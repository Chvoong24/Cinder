import pygrib
import numpy as np
from pathlib import Path
import json
import re
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

class SafeMemoryFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, "memory"):
            try:
                import psutil, os
                mem = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
                record.memory = f"{mem:,.1f}"
            except Exception:
                record.memory = "?"
        return super().format(record)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d | %(levelname)-8s | [MEM %(memory)s MB] | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

for handler in logging.getLogger().handlers:
    handler.setFormatter(SafeMemoryFormatter(handler.formatter._fmt, handler.formatter.datefmt))


def get_value_from_latlon(lat, lon, lats, lons, data):
    """returns the data associated at a lat lon coordinate, uses distance formula on a plane"""
    distance_squared = (lats - lat) ** 2 + (lons - lon) ** 2
    row, col = np.unravel_index(np.argmin(distance_squared), distance_squared.shape)
    return float(data[row, col])


def make_json_file(folder_path, lat, lon, desired_forecast_types, max_workers=8):
    """Args: Folder_path -> path of where grib data is located
             lat and lon are float values of lat and lon
             desired_forecast_types -> fitlered thresholds (vague for now)
             max_workers -> hardcoded to 8, is for multithreaded processing
    """
    prob_re = re.compile(r'\(([^)]*?)\)')

    def get_all_readable_data(filename):
        """Parses all data in the inputed grib file"""
        readable_data = []
        anal_date = ""
        try:
            with pygrib.open(filename.path) as grbs:
                logger.info(f"Parsing {filename.name}")
                first_grib = grbs.message(1)
                anal_date = first_grib.analDate

                match = re.search(r'f(\d{2,3})', filename.name)
                if match:
                    forecast_end = int(match.group(1))

                for grb in grbs:
                    if not any(kw in grb.name.lower() for kw in desired_forecast_types):
                        continue
                    


                    anal_date = grb.analDate
                    text = str(grb)
                    paren_matches = prob_re.findall(text)
                    threshold_text = paren_matches[-1].strip() if paren_matches else "none"

                    units = getattr(grb, "units", "") or ""
                    limit = f"{threshold_text} {units}".strip()

                    if not (">" in limit or "<" in limit):
                        continue
                    try:
                        data, lats, lons = grb.data()
                        value = get_value_from_latlon(lat, lon, lats, lons, data)
                    except Exception as e:
                        logger.error(f"Error getting data for {filename.name} / {grb.name}: {e}")
                        continue

                    step_length = forecast_end - grb.forecastTime
                    readable_data.append((limit, grb.name, step_length, grb.forecastTime, value))

                logger.info(f"Parsed {filename.name}")

        except Exception as e:
            logger.error(f"Error processing {filename.name}: {e}")

        return readable_data, anal_date


    readable_data = []

    folder_path = os.fspath(folder_path)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(get_all_readable_data, file_path): file_path
            for file_path in os.scandir(folder_path)
            if file_path.is_file()
        }

        anal_date = None
        for future in as_completed(futures):
            file_path = futures[future]
            try:
                rd, ad = future.result()
                readable_data.extend(rd)
                if anal_date is None and ad:
                    anal_date = ad
            except Exception as e:
                logger.error(f"Failed on {file_path}: {e}")

    files = [f.name for f in os.scandir(folder_path) if f.is_file()]
    model, cycle = "unknown", "unknown"

    if files:
        fname = files[0].lower()

        m = re.search(r"^(rrfs)\.(\d{8})t(\d{2})z", fname)
        if m:
            model = "RRFS"
            cycle = f"{m.group(3)}z"
        elif re.search(r"^href", fname):
            model = "HREF"
            cyc = re.search(r"t(\d{2})z", fname)
            if cyc: cycle = f"{cyc.group(1)}z"
        elif re.search(r"^refs", fname):
            model = "REFS"
            cyc = re.search(r"t(\d{2})z", fname)
            if cyc: cycle = f"{cyc.group(1)}z"
        elif re.search(r"^nbm", fname):
            model = "NBM"
            cyc = re.search(r"t(\d{2})z", fname)
            if cyc: cycle = f"{cyc.group(1)}z"

    headers = ["threshold", "name", "step_length", "forecast_time", "value"]

    output_data = {
        "metadata": {
            "sitrep": model,
            "anal_date": anal_date.strftime("%Y-%m-%d %H:%M:%S") if anal_date else "unknown",
            "location": {"lat": lat, "lon": lon},
            "folder": str(folder_path)
        },
        "data": [dict(zip(headers, row)) for row in readable_data],
    }

    PARENT_DIR = SCRIPT_DIR.parent
    DATA_DIR = PARENT_DIR / "cinder-app" / "backend" / "models"
    OUTDIR = DATA_DIR / "data"

    if not OUTDIR.exists():
        raise FileNotFoundError(f"Hardcoded output directory does not exist: {OUTDIR}")

    output_name = f"{model}{cycle}_for_{lat},{lon}.json"
    output_path = OUTDIR / output_name

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"JSON saved to {output_path}")


def run_all_models(lat, lon):
    logger.info("Running ALL GRIB -> JSON conversions in parallel...")

    model_folders = {
        "HREF": DATA_DIR / "href_data" / "href_download",
        "NBM": DATA_DIR / "nbm_data" / "nbm_download",
        "REFS": DATA_DIR / "refs_data" / "refs_download"
    }

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []

        for name, folder in model_folders.items():
            futures.append(
                executor.submit(
                    make_json_file,
                    folder,
                    lat,
                    lon,
                    ["precip", "wind", "apparent", "2 metre", "relative humidity"]
                )
            )

        for future in as_completed(futures):
            future.result()

    logger.info("All GRIB -> JSON files have been generated.")



if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <lat> <lon>")
        sys.exit(1)

    LAT = float(sys.argv[1])
    LON = float(sys.argv[2])

    SCRIPT_DIR = Path(__file__).resolve().parent
    DATA_DIR = SCRIPT_DIR.parent

    run_all_models(LAT, LON)