import pygrib
import numpy as np
from pathlib import Path
import json
import re
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Logger

class SafeMemoryFormatter(logging.Formatter):
    def format(self, record):
        # add default if missing
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



# Code workflow

def get_value_from_latlon(lat, lon, lats, lons, data):
    """
    Return the value in `data` closest to the given lat/lon.
    """
    distance_squared = (lats - lat) ** 2 + (lons - lon) ** 2
    row, col = np.unravel_index(np.argmin(distance_squared), distance_squared.shape)
    return float(data[row, col])


def make_json_file(folder_path, lat, lon, desired_forecast_types, max_workers=8):
    """
    Args:
        folder_path: Path to folder with grib2 files.
        lat, lon: desired latitude/longitude point for forecast.
        desired_forecast_types: list of grib2 forecast types that you want in the json.
        max_workers: number of threads for parallel execution.
    
    Outputs a JSON file to the current directory
    """

    prob_re = re.compile(r'Probability.*\(([^)]*)\)', re.IGNORECASE)

    def get_all_readable_data(filename):

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
                    if grb.name not in desired_forecast_types: 
                        continue
                    anal_date = grb.analDate
                    # Extract probability threshold if available

                    match = prob_re.search(str(grb))
                    if match:
                        pass
                    else:
                        continue
                    
                    limit = f"{match.group(1) if match else "none"} {grb.units}"

                    # Get nearest value to requested lat/lon
                    data, lats, lons = grb.data()
                    value = get_value_from_latlon(lat, lon, lats, lons, data)

                    
                    step_length = forecast_end - grb.forecastTime
                    # print(grb)
                    # print(grb.analDate)
                    # print("Forecast end: ", forecast_end)
                    # print("Forecast time: ", grb.forecastTime)
                    # print("Step length: ", step_length)
                    
                    readable_data.append((limit, grb.name, step_length, grb.forecastTime, value))
                logger.info(f"Parsed {filename.name}")
        except Exception as e:
            logger.error(f"Error processing {filename.name}: {e}")

        return readable_data, anal_date

    # --- Parallelization ---
    readable_data = []

    folder_path = os.fspath(folder_path) if not isinstance(folder_path, (str, os.PathLike)) else folder_path

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(get_all_readable_data, file_path): file_path
            for file_path in os.scandir(folder_path) if file_path.is_file()
        }

        anal_date = None  # initialize before loop
        for future in as_completed(futures):
            file_path = futures[future]
            try:
                rd, ad = future.result()
                readable_data.extend(rd)
                if anal_date is None and ad:  # capture the first non-empty analysis date
                    anal_date = ad
            except Exception as e:
                logger.error(f"Failed on {file_path}: {e}")

    # --- Prepare JSON output ---
    files = [f.name for f in os.scandir(folder_path) if f.is_file()]
    model, cycle = "unknown", "unknown"
    if files:
        match = re.search(r"([a-zA-Z]+)[._]t?(\d{2}z)", files[0], re.IGNORECASE)
        if match:
            model, cycle = match.groups()


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

    output_name = f"{model}{cycle}_for_{lat},{lon}.json"
    with open(output_name, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"JSON saved as {output_name}")



if __name__ == "__main__":
    LAT = 24.02619
    LON = -107.421197

    DESIRED_FORECAST_TYPES = [
        "Total Precipitation",
        "10 metre wind speed",
        "Apparent temperature",
        "2 metre temperature",
        "2 metre relative humidity"
    ]

    FOLDER = Path("href_download")
    make_json_file(FOLDER, LAT, LON, DESIRED_FORECAST_TYPES)
