import pygrib
import numpy as np
from pathlib import Path
import json
import re
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed







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





import os
import re
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pygrib

logger = logging.getLogger(__name__)

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
        max_workers: number of threads for parallel execution.
    """

    prob_re = re.compile(r'Probability.*\(([^)]*)\)', re.IGNORECASE)

    def get_all_readable_data(filename):
        readable_data = []

        try:
            with pygrib.open(filename.path) as grbs:  # <-- use filename.path
                logger.info(f"Parsing {filename.name}")

                match = re.search(r'f(\d{2})', filename.name)
                if match:
                    forecast_end = int(match.group(1))
                    
                    

                for grb in grbs:
                    if grb.name not in desired_forecast_types: 
                        continue

                    # Extract probability threshold if available
                    match = prob_re.search(str(grb))
                    limit = match.group(1) if match else "none"

                    # Get nearest value to requested lat/lon
                    data, lats, lons = grb.data()
                    value = get_value_from_latlon(lat, lon, lats, lons, data)

                    
                    step_length = forecast_end - grb.forecastTime
                    

                    readable_data.append((limit, grb.name, step_length, grb.forecastTime, value))

        except Exception as e:
            logger.error(f"Error processing {filename.name}: {e}")

        return readable_data

    # --- Parallel execution ---
    readable_data = []

    folder_path = os.fspath(folder_path) if not isinstance(folder_path, (str, os.PathLike)) else folder_path

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(get_all_readable_data, file_path): file_path
            for file_path in os.scandir(folder_path) if file_path.is_file()
        }

        for future in as_completed(futures):
            file_path = futures[future]
            try:
                rd = future.result()
                readable_data.extend(rd)
            except Exception as e:
                logger.error(f"Failed on {file_path}: {e}")

    # --- Metadata from first file ---
    files = [f.name for f in os.scandir(folder_path) if f.is_file()]
    model, cycle = "unknown", "unknown"
    if files:
        match = re.search(r"([a-zA-Z]+)[._]t?(\d{2}z)", files[0], re.IGNORECASE)
        if match:
            model, cycle = match.groups()

    # --- Prepare JSON output ---

    forecast_types = [tup[:2] for tup in readable_data]
    forecast_types = sorted(set(forecast_types))


    hour_and_step_list = [tup[2:4] for tup in readable_data]
    hour_and_step_list = sorted(set(hour_and_step_list))
    print(hour_and_step_list)
    

    headers = ["threshold", "name", "step_length", "forecast_time", "probability"]


    output_data = {
        "metadata": {
            "sitrep": model,
            "forecast_time": cycle,
            "location": {"lat": lat, "lon": lon},
            "folder": str(folder_path),
            "forecast_types": forecast_types,
            "hour_list": hour_and_step_list
            
        },
        "data": [dict(zip(headers, row)) for row in readable_data],
    }

    output_name = f"{model}{cycle}_for_{lat},{lon}.json"
    with open(output_name, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"JSON saved as {output_name}")





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

