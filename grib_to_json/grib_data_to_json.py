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





def get_value_from_latlon(lat, lon, lats, lons, data):
    """
    input is the lat, lon you want, as well as the data, list of lats, and list of lons
    output is the value closest to the input lat, lon
    """
    # Calculate how far each grid point is from the target lat,lon
    lat_diff = lats - lat
    lon_diff = lons - lon
    distance_squared = lat_diff**2 + lon_diff**2
    
    # Find the row and col of the closest point
    flat_index = np.argmin(distance_squared)
    row, col = np.unravel_index(flat_index, distance_squared.shape)

    # Return the value at that grid point
    return data[row, col]





logger = logging.getLogger(__name__)

def make_json_file(folder_path, lat, lon, desired_forecast_types, max_workers=8):
    """
    Args:
        folder_path: Path to folder with grib2 files.
        lat: desired latitude point for forecast
        lon: desired longitude point for forecast
        desired_forecast_types: list of GRIB variable names to include
        forecast_time: the time the forecast was created (Zulu)
        sitrep: model name for the collection
        max_workers: number of threads (default 8)
    """

    prob_re = re.compile(r'Probability.*\(([^)]*)\)', re.IGNORECASE)

    def get_all_readable_data(filename):
        readable_data = []
        forecast_types = []
        try:
            with pygrib.open(str(filename)) as grbs:
                logger.info(f"Parsing {filename}")
                for grb in grbs:
                    if grb.name not in desired_forecast_types:
                        continue

                    # Extract probability threshold
                    match = prob_re.search(str(grb))
                    limit = match.group(1) if match else "none"

                    # Get data & nearest value
                    data, lats, lons = grb.data()
                    d2 = (lats - lat)**2 + (lons - lon)**2
                    r, c = np.unravel_index(np.argmin(d2), d2.shape)
                    value = float(data[r, c])

                    readable_data.append((limit, grb.name, grb.forecastTime, value))
                    forecast_types.append((grb.name, limit))

        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")

        return readable_data, forecast_types

    # --- Parallel execution ---
    readable_data = []
    forecast_types = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(get_all_readable_data, file_path): file_path for file_path in folder_path.iterdir() if file_path.is_file()}

        for future in as_completed(futures):
            file_path = futures[future]
            try:
                rd, ft = future.result()
                readable_data.extend(rd)
                forecast_types.extend(ft)
            except Exception as e:
                logger.error(f"Failed on {file_path}: {e}")

    # --- Post-processing ---
    
    

    

    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    if files:
        first_file = files[0]  # name only (not full path)
        match = re.search(r"([a-zA-Z]+)[._]t?(\d{2}z)", first_file, re.IGNORECASE)
        if match:
            model, cycle = match.groups()



    forecast_types = sorted(set(forecast_types))
    headers = ["threshold", "name", "forecastTime", "probability"]


    output_data = {
        "metadata": {
            "sitrep": model,
            "forecast_time": cycle,
            "location": {"lat": lat, "lon": lon},
            "folder": str(folder_path),
            "forecast_types": forecast_types,
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

FOLDER = Path("nbm_download")

make_json_file(FOLDER, LAT, LON, DESIRED_FORECAST_TYPES)


# ========= Testing =============

# FILE_NAME = "nbm_download/nbm_t18z_f024_custom.grib2"

# nbm_names = []
# grbs = pygrib.open(FILE_NAME)
# grb = grbs.message(1)
# print(grb)
# for grb in grbs:
#     # print(grb)
#     nbm_names.append(grb.name)


# for key in grb.keys():
#     try:
#         print(f"{key}: {getattr(grb, key)}")
#     except Exception as e:
#         print(f"{key}: <unavailable> ({e})")


# nbm_names = set(nbm_names)
# for name in nbm_names:
#     print(name)



# print("Short name:", grb.shortName)
# print("Name:", grb.name)
# print("Units:", grb.units)
# print("Type of level:", grb.typeOfLevel)
# print("Level:", grb.level)
# print("Forecast time:", grb.forecastTime)
# print("Start time:", grb.analDate)
# print("End time:", grb.validDate)
# print("Probability type:", grb.parameterCategory, grb.parameterNumber)
# print("Description:", grb.parameterName)
# # print("Probability type", grb.probabilityType)
# print("Lower limit", grb.lowerLimit)
# print("Upper limit", grb.upperLimit)


# href_forecast_types = [
#     "Total Precipitation",
#     "Convective available potential energy",
#     "Convective inhibition",
#     "Categorical freezing rain",
#     "Categorical rain",
#     "10 metre wind speed",
#     "Haines Index",
#     "Lightning",
#     "Water equivalent of accumulated snow depth (deprecated)",
#     "unknown",
#     "Precipitable water",
#     "Vertical speed shear",
#     "Categorical ice pellets",
#     "Flight Category",
#     "Maximum/Composite radar reflectivity",
#     "Visibility",
#     "Categorical snow"
# ]