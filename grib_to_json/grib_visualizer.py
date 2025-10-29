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



readable_data = []



desired_href_forecast_types = [
    "Total Precipitation",
    "10 metre wind speed",
]

def get_all_readable_data(filename, lat, lon):
    grbs = pygrib.open(filename)
    print(f"Parsing {filename}")
    for grb in grbs:
        if grb.name in desired_href_forecast_types:
            limit = ""
            if grb.upperLimit > grb.lowerLimit:
                limit = f">{grb.upperLimit}"
                
            elif grb.upperLimit < grb.lowerLimit:
                limit = f"<{grb.lowerLimit}"
            else:
                pass


            data, lats, lons = grb.data()
            value = get_value_from_latlon(lat, lon, lats, lons, data)

            this_data = (limit, grb.name, grb.forecastTime, value)

            readable_data.append(this_data)


        else:
            pass

        # print(f"Probability of {limit} {val} {grb.units} {grb.name} at {grb.forecastTime} hours from {grb.analDate} is {value} at {LAT},{LON}")

        


FILE_NAME = 'href_download/href.t12z.conus.prob.f12.grib2'
LAT = 24.02619
LON = -107.421197






def make_json_file(folder_path, data, lat, lon, forecast_time, sitrep):
    """
    Args:
        folder_path: The path to the folder with all the grib2 files
        data: The list that contains all desired data for the grib2 files
        lat: lattitude part of coordinate
        lon: longitude part of coordinate
        forecast_time: the time that the grib2 files were made for in zulu time (for naming the json)
        sitrep: the model name (for naming the json)

    Returns nothing. Creates a json file in current directory.
    
    """
    for file_path in folder_path.iterdir():
        get_all_readable_data(file_path, lat, lon)

    print("Making JSON")
    headers = ["threshold", "name", "forecastTime", "probability"]
    records = [dict(zip(headers, row)) for row in data]
    with open(f"{sitrep}{forecast_time}_for_{lat},{lon}.json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print("JSON Made")




FOLDER = Path("href_download/")
make_json_file(FOLDER, readable_data, LAT, LON, "12z", "HREF")



# grbs = pygrib.open(FILE_NAME)
# # grb = grbs.message(1)
# for grb in grbs:
#     print(grb)
# for key in grb.keys():
#     try:
#         print(f"{key}: {getattr(grb, key)}")
#     except Exception as e:
#         print(f"{key}: <unavailable> ({e})")




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
# print("Probability type", grb.probabilityType)
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