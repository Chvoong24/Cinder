import os
import time
import requests
import logging
import pygrib
import pathlib
import utils
from pathlib import Path
from datetime import datetime, timezone
from logging.handlers import TimedRotatingFileHandler
from concurrent.futures import ThreadPoolExecutor, as_completed

# -----------------------------------------
# ------------ Constants ------------------
# -----------------------------------------

# Output locations

SCRIPT_DIR = Path(__file__).resolve().parent

PARENT_DIR = SCRIPT_DIR.parent

HREF_DATA_DIR = PARENT_DIR / "href_data"

OUTDIR = HREF_DATA_DIR / "href_download"
LOGDIR = HREF_DATA_DIR / "./href_logs"

OUTDIR.mkdir(parents=True, exist_ok=True)
LOGDIR.mkdir(parents=True, exist_ok=True)


# Multi Threading
MAX_THREADS = 10    # Parallel download threads
MAX_RETRIES = 5     # Retry attempts allowed before fail
RETRY_DELAY = 10    # Delay (secs) between retry attempts
MIN_FILE_SIZE = 1 * 1024    # Min file size check

# -----------------------------------------
# ------- Logging Configuration -----------
# -----------------------------------------
if ( == True):
	LOGFILE = LOGDIR / "href_pull.log"
	LOG_LEVEL = logging.INFO

	logger = logging.getLogger("href_manual")
	logger.setLevel(LOG_LEVEL)
	logger.handlers.clear()

	ch = logging.StreamHandler()
	ch.setLevel(LOG_LEVEL)
	ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
	logger.addHandler(ch)

	fh = TimedRotatingFileHandler(
		filename=str(LOGFILE), when="midnight", backupCount=7, encoding="utf-8"
	)
	fh.setLevel(LOG_LEVEL)
	fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
	logger.addHandler(fh)

# ----------------------------------------------
# --- Manual Override Settings (for Testing) ---
# ----------------------------------------------

manual_mode = False  # ⚡ Set to True for manual download and adjust date/time at bottom of script.

# -----------------------------------------
# --- Determine Model Run (00/06/12/18) ----
# -----------------------------------------

def determine_model_run():
	"""Determines what Cycle and Date depending on the most recent time available."""
	now = datetime.now(timezone.utc)
	
	if now.hour >= 19:
		run_hour = 18
		
	elif now.hour >= 12:
		run_hour = 12
		
	elif now.hour >= 6:
		run_hour = 6
		
	else:
		run_hour = 0
		
	pull_date = now.strftime('%Y%m%d')
	run_hour_str = f"{run_hour:02d}"
	
	return pull_date, run_hour_str

# -------------------------
# ----- URL Generator -----
# -------------------------

def generate_href_urls(pull_date, run_hour_str, forecast_hours, field_type = 'mean'):

	"""
	field_type: 'prob'
	returns a list of HREF URLs for f01-f48
	"""
	
	base = (
		f'https://nomads.ncep.noaa.gov/cgi-bin/filter_hrefconus.pl'
		f'?dir=%2Fhref.{pull_date}%2Fensprod'
	)
	if field_type == 'prob':
		var_params = "&".join(["all_var=on"])
		lev_params = "&".join([
		    "lev_10_m_above_ground=on",
			"lev_5000-2000_m_above_ground=on",
			"lev_90-0_mb_above_ground=on",
			"lev_surface=on",
			"lev_entire_atmosphere_(considered_as_a_single_layer)=on",
		])
		
	bbox = "&subregion=&toplat=38&leftlon=-107.5&rightlon=-91.5&bottomlat=24.5"
	
	urls = []
	for fhr in forecast_hours:
		fh = f'{fhr:02d}'
		filename = f"href.t{run_hour_str}z.conus.{field_type}.f{fh}.grib2"
		url = f"{base}&file={filename}&{var_params}&{lev_params}{bbox}"
		urls.append(url)
		
	return urls


# -------------------------
# --- Download Function ---
# -------------------------

def download_file(url, output_dir):
	filename = url.split("file=")[1].split("&")[0]
	filepath = os.path.join(output_dir, filename)
	print(f"⬇️  Requesting: {filename}", flush = True)
    
	for attempt in range(1, MAX_RETRIES + 1):

		try:
			if(utils.Logging):
				logger.info(f'[{attempt}/{MAX_RETRIES}] Downloading {filename}')
				response = requests.get(url, stream = True, timeout = 20)
				response.raise_for_status()

			with open(filepath, "wb") as f:
				for chunk in response.iter_content(chunk_size = 65536):
					f.write(chunk)
					
			size = os.path.getsize(filepath)
			if size < MIN_FILE_SIZE:
				raise ValueError(f'File too small ({size} bytes)')
			if(utils.Logging):
				logger.info(f'Downloaded {filename} successfully ({size} bytes)')
				print(f'✅ Downloaded: {filename}', flush = True)
			return True

		except Exception as e:
			err_msg = str(e)

			if " for url" in err_msg:
				err_msg = err_msg.split(" for url")[0]
				if(utils.Logging):
					logger.warning(f'Attempt {attempt} failed for {filename}: {err_msg}')
			if attempt < MAX_RETRIES:
				if(utils.Logging):
					logger.info(f'Retrying in {RETRY_DELAY} seconds...')
				time.sleep(RETRY_DELAY)
			else:
				if(utils.Logging):
					logger.error(f'All retries failed for {filename}')
				print(f'❌ Failed: {filename} → check log!', flush = True)
			return False


# -------------------------
# ------ Main Script ------
# -------------------------

def main():

	prob_urls = generate_href_urls(pull_date, run_hour_str, forecast_hours, 'prob')
	urls = prob_urls
	
	print(f"\n📅 Fetching HREF Run: {pull_date} at {run_hour_str}Z")
	print(f"\n🛠️  Forecast Hours: 1-48 (total {len(urls)} files)\n")
	if(utils.Logging):
		logger.info(f'Fetching HREF Run: {pull_date} at {run_hour_str}Z')
		logger.info(f'Forecast Hours: 1-48 (total {len(urls)} files)')
	
	success_list, fail_list = [], []
	
	print(f"🚀 Starting parallel downloads with {MAX_THREADS} threads...\n")
	if(utils.Logging):
		logger.info(f'Starting downloads with {MAX_THREADS} threads...')
	
	with ThreadPoolExecutor(max_workers = MAX_THREADS) as executor:
		future_to_url = {executor.submit(download_file, url, OUTDIR): url for url in urls}
		for future in as_completed(future_to_url):
			url = future_to_url[future]
			if future.result():
				success_list.append(url)
			else:
				fail_list.append(url)
	if(utils.Logging):			
		logger.info(f'Downloads finished: {len(success_list)}/{len(urls)} succeeded.')
	
	if fail_list:
		if(utils.Logging):
			logger.warning('The following files failed after retries:')
		for url in fail_list:
			fn = url.split('file=')[1].split('&')[0]
			if(utils.Logging):
				logger.error(f' - {fn}')
			
	else:
		if(utils.Logging):
			logger.info('All files downloaded successfully!')
		
	print("\n✅ 📂 All downloads complete!\n")
	

def view_grib():
	'''
	Function grabs the first of the downloaded forecast hours and prints
	the header values contained within.
	'''
	folder = Path(__file__).resolve().parent.parent / "href_data/href_download"

	if not folder.exists():
		raise FileNotFoundError(f"Folder not found: {folder}")

	file_path = next(folder.iterdir())
	print(f"Opening GRIB file: {file_path}")

	with pygrib.open(str(file_path)) as grbs:
		grbs.seek(0)
		for grb in grbs:
			print(grb)


# -------------------------
# ------ Run Script -------
# -------------------------

if manual_mode:
	pull_date = '20251023'  # YYYYMMDD format
	run_hour_str = '00'     # '00', '06', '12', '18', etc.
	forecast_hours = list(range(1, 49))  # Example: f00 to f18 or 19, 49 for f19 to f48
	
else:
	pull_date, run_hour_str = determine_model_run()
	forecast_hours = list(range(1, 49))

if __name__ == "__main__":
	main()
	try: 
		view_grib()
	except Exception as e:
		print(f'Failed to view grib contents with exception: {e}')
		





