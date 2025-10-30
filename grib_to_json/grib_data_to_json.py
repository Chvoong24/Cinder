import pygrib
import numpy as np
from pathlib import Path
import json







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



def make_json_file(folder_path, lat, lon, desired_forecast_types, forecast_time, sitrep):
    """
    Args:
        folder_path: Path to folder with grib2 files.
        lat: desired latitude point for forecast
        lon: desired longitude point for forecast
        forecast_time: the time the forecast was created in zulu time
        sitrep: the model that the collection of grib_files was run for
    """
    readable_data = [] 
    forecast_types = []

    def get_all_readable_data(filename):
        grbs = pygrib.open(filename)
        print(f"Parsing {filename}")
        for grb in grbs:

            if grb.name in desired_forecast_types:
                limit = ""
                if grb.upperLimit > grb.lowerLimit:
                    limit = f">{grb.upperLimit}"
                elif grb.upperLimit < grb.lowerLimit:
                    limit = f"<{grb.lowerLimit}"

                data, lats, lons = grb.data()
                value = get_value_from_latlon(lat, lon, lats, lons, data)
                readable_data.append((limit, grb.name, grb.forecastTime, value))
                forecast_types.append((grb.name, limit))
            
    
    for file_path in folder_path.iterdir():
        get_all_readable_data(file_path)

    forecast_types = sorted(list(set(forecast_types)))
    headers = ["threshold", "name", "forecastTime", "probability"]
    

    output_data = {
        "metadata": {
            "sitrep": sitrep,
            "forecast_time": forecast_time,
            "location": {"lat": lat, "lon": lon},
            "folder": str(folder_path),
            "forecast_types": forecast_types,
        },
        "data": [dict(zip(headers, row)) for row in readable_data],
    }


    output_name = f"{sitrep}{forecast_time}_for_{lat},{lon}.json"
    with open(output_name, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)



    print(f"JSON saved as {output_name}")




LAT = 24.02619
LON = -107.421197
SITREP = "NBM"
DESIRED_FORECAST_TYPES = [
    "Total Precipitation",
    "10 metre wind speed",
    "Apparent temperature",
    "2 metre temperature",
    "2 metre relative humidity"
]

FOLDER = Path("href_download/")
# make_json_file(FOLDER, LAT, LON, DESIRED_FORECAST_TYPES, "12z", SITREP)


# ========= Testing =============

FILE_NAME = 'nbm_download/blend.t00z.qmd.f003.co.grib2'

nbm_names = []
grbs = pygrib.open(FILE_NAME)
grb = grbs.message(67)
print(grb)
for grb in grbs:
    print(grb)
    nbm_names.append(grb.name)


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


href_forecast_types = [
    "Total Precipitation",
    "Convective available potential energy",
    "Convective inhibition",
    "Categorical freezing rain",
    "Categorical rain",
    "10 metre wind speed",
    "Haines Index",
    "Lightning",
    "Water equivalent of accumulated snow depth (deprecated)",
    "unknown",
    "Precipitable water",
    "Vertical speed shear",
    "Categorical ice pellets",
    "Flight Category",
    "Maximum/Composite radar reflectivity",
    "Visibility",
    "Categorical snow"
]