import os
import time
import requests
import logging
import pygrib
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from concurrent.futures import ThreadPoolExecutor, as_completed

# -----------------------------------------
# ------------ Constants ------------------
# -----------------------------------------

LOG_DIR = 'hrefDownloads'
LOG_FILENAME = 'hrefDownloader.log'
MAX_THREADS = 10    # Parallel download threads
MAX_RETRIES = 10     # Retry attempts allowed before fail
RETRY_DELAY = 10    # Delay (secs) between retry attempts
MIN_FILE_SIZE = 1 * 1024    # Min file size check

def ensure_log_dir():
	os.makedirs(LOG_DIR, exist_ok = True)

# -----------------------------------------
# ------- Logging Configuration -----------
# -----------------------------------------

def setup_logger():
	ensure_log_dir()
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.INFO)
	
	log_path = os.path.join(LOG_DIR, LOG_FILENAME)
	file_handler = TimedRotatingFileHandler(log_path, when = 'midnight', interval = 1, backupCount = 7)
	file_handler.setLevel(logging.INFO)
	fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt = '%Y-%m-%d %H:%M:%S')
	file_handler.setFormatter(fmt)
	logger.addHandler(file_handler)
	
	return logger
	
logger = setup_logger()

# ----------------------------------------------
# --- Manual Override Settings (for Testing) ---
# ----------------------------------------------

manual_mode = False  # ⚡ Set to True for manual download and adjust date/time at bottom of script.

# -----------------------------------------
# --- Determine HREF Run (00/06/12/18) ----
# -----------------------------------------

def determine_href_run():
	now = datetime.utcnow()
	
	if now.hour >= 20:
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
			logger.info(f'[{attempt}/{MAX_RETRIES}] Downloading {filename}')
			response = requests.get(url, stream = True, timeout = 20)
			response.raise_for_status()

			with open(filepath, "wb") as f:
				for chunk in response.iter_content(chunk_size = 65536):
					f.write(chunk)
					
			size = os.path.getsize(filepath)
			if size < MIN_FILE_SIZE:
				raise ValueError(f'File too small ({size} bytes)')
			logger.info(f'Downloaded {filename} successfully ({size} bytes)')
			print(f'✅ Downloaded: {filename}', flush = True)
			return True

		except Exception as e:
			err_msg = str(e)

			if " for url" in err_msg:
				err_msg = err_msg.split(" for url")[0]

				logger.warning(f'Attempt {attempt} failed for {filename}: {err_msg}')
			if attempt < MAX_RETRIES:
				logger.info(f'Retrying in {RETRY_DELAY} seconds...')
				time.sleep(RETRY_DELAY)
			else:
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
	
	logger.info(f'Fetching HREF Run: {pull_date} at {run_hour_str}Z')
	logger.info(f'Forecast Hours: 1-48 (total {len(urls)} files)')
	
	success_list, fail_list = [], []
	
	output_dir = os.path.join(LOG_DIR, f't_{run_hour_str}_z')
	os.makedirs(output_dir, exist_ok = True)
	
	print(f"🚀 Starting parallel downloads with {MAX_THREADS} threads...\n")
	
	logger.info(f'Starting downloads with {MAX_THREADS} threads...')
	
	with ThreadPoolExecutor(max_workers = MAX_THREADS) as executor:
		future_to_url = {executor.submit(download_file, url, output_dir): url for url in urls}
		for future in as_completed(future_to_url):
			url = future_to_url[future]
			if future.result():
				success_list.append(url)
			else:
				fail_list.append(url)
				
	logger.info(f'Downloads finished: {len(success_list)}/{len(urls)} succeeded.')
	
	if fail_list:
		logger.warning('The following files failed after retries:')
		for url in fail_list:
			fn = url.split('file=')[1].split('&')[0]
			logger.error(f' - {fn}')
			
	else:
		logger.info('All files downloaded successfully!')
		
	print("\n✅ 📂 All downloads complete!\n")
	

def viewGrib():
	'''
	Function grabs one of the downloaded forecast hours and prints the header values contained within.
	Manaually edit to make sure it is pulling the right file.
	'''
	grbs = pygrib.open(r'hrefDownloads\t_12_z\href.t12z.conus.prob.f01.grib2')
	grbs.seek(0)
	for grb in grbs:
		print(grb)
	return None


# -------------------------
# ------ Run Script -------
# -------------------------

if manual_mode:
	pull_date = '20250624'  # YYYYMMDD format
	run_hour_str = '06'     # '00', '06', '12', '18', etc.
	forecast_hours = list(range(1, 49))  # Example: f00 to f18 or 19, 49 for f19 to f48
	
else:
	pull_date, run_hour_str = determine_href_run()
	forecast_hours = list(range(1, 49))

if __name__ == "__main__":
	main()
	viewGrib()




