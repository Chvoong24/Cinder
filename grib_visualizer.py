import pygrib
import numpy as np
from datetime import timedelta, datetime
import os


def get_value_from_latlon(lat, lon, lats, lons, data):
    """Return value at grid point closest to the input lat/lon."""
    # Compute squared distance for all grid points
    distance_squared = (lats - lat) ** 2 + (lons - lon) ** 2

    # Find indices of the minimum distance
    row, col = np.unravel_index(np.argmin(distance_squared), distance_squared.shape)
    return data[row, col]


def parse_grib_message(grb, lat, lon, filename):
    """Extract human-readable info and value for one GRIB message."""
    limit = "more than" if grb.upperLimit > grb.lowerLimit else "less than"
    val = grb.upperLimit if grb.upperLimit > grb.lowerLimit else grb.lowerLimit

    # Compute forecast start and end
    forecast_start_hour = grb.forecastTime
    forecast_end_hour = grb.endStep
    forecast_start_time = grb.analDate + timedelta(hours=forecast_start_hour)
    forecast_end_time = grb.analDate + timedelta(hours=forecast_end_hour)

    # Build readable time string
    if forecast_start_hour == forecast_end_hour:
        time_label = f"at {forecast_start_time}"
    else:
        time_label = f"from {forecast_start_time} to {forecast_end_time}"

    # Extract data and nearest grid value
    data, lats, lons = grb.data()
    value = get_value_from_latlon(lat, lon, lats, lons, data)

    return limit, val, grb.units, grb.name, forecast_start_time, forecast_end_time, value, time_label





def get_one_forecast(folder_name, upper_limit, short_name, start_time, requested_forecast_length, lat, lon):
    """Find matching GRIB files and extract the requested forecast data."""
    href_files = sorted([entry.path for entry in os.scandir(folder_name) if entry.is_file()])

    # Print analysis date from first file
    with pygrib.open(href_files[0]) as meta_grbs:
        meta_grb = meta_grbs.message(1)
        print(f"HREF analysis date: {meta_grb.analDate}")

    for file_path in href_files:
        # Extract forecast hour number (e.g., 'f42')
        parts = file_path.split(".")
        number = next((p[1:] for p in parts if p.startswith("f")), None)

        with pygrib.open(file_path) as grbs:
            for grb in grbs:
                forecast_length = grb.endStep - grb.startStep

                if grb.cfVarName == short_name and grb.upperLimit == upper_limit and forecast_length == requested_forecast_length:
                    limit, val, units, name, forecast_start, forecast_end, value, time_label = parse_grib_message(grb, lat, lon, file_path)

                    if forecast_start == start_time:
                        print(
                            f"Hour {number}. Message {grb.messagenumber}: "
                            f"Probability of {limit} {val} {units} {name} "
                            f"{time_label} is {value:.1f}% at ({lat:.4f}, {lon:.4f})"
                        )


# --- Configuration ---
FOLDER_NAME = "href_data/href_download"
LAT = 24.02619
LON = -107.421197
dt = datetime(year=2025, month=10, day=17, hour=14)

# --- Run ---
get_one_forecast(FOLDER_NAME, 12.7, "tp", dt, 1, LAT, LON)





# print("Short name:", grb.shortName)
# print("Name:", grb.name)
# print("Units:", grb.units)
# print("Type of level:", grb.typeOfLevel)
# print("Level:", grb.level)
# print("Forecast time:", grb.forecastTime)
# print("Forecast end time:", grb.endStep)
# print("Start time:", grb.analDate)
# print("End time:", grb.validDate)
# print("Probability type:", grb.parameterCategory, grb.parameterNumber)
# print("Description:", grb.parameterName)
# print("Probability type", grb.probabilityType)
# print("Lower limit", grb.lowerLimit)
# print("Upper limit", grb.upperLimit)




# MESSAGE = 65

# i = 1
# while i <= 84:

#     limit, val, units, name, time, value = get_all_readable_data(FILE_NAME, LAT, LON, i)

#     # print(f"Probability of {limit} {val} {units} {name} {time} is {value}% at {LAT},{LON}")
#     i +=1

# grbs = pygrib.open(FILE_NAME)
# for grb in grbs:
#     print(grb)

# grbs = pygrib.open(FILE_NAME)
# for grb in grbs:
#     print(grb)
# grb = grbs.message(40)  # pick the first message as an example
# print(grb)

# # Loop over all attributes that don't start with "__"
# for attr in dir(grb):
#     if not attr.startswith("__"):
#         try:
#             value = getattr(grb, attr)
#             # Skip methods, just print values
#             if not callable(value):
#                 print(f"{attr}: {value}")
#         except Exception as e:
#             print(f"{attr}: <Could not read ({e})>")