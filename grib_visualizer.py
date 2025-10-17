import pygrib
import numpy as np



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









def get_all_readable_data(filename, lat, lon):
    grbs = pygrib.open(filename)

    for grb in grbs:
        limit = ""
        if grb.upperLimit > grb.lowerLimit:
            limit = "more than"
            val = grb.upperLimit
        else:
            limit = "less than"
            val = grb.lowerLimit

        if grb.forecastTime == grb.endStep:
            time = grb.forecastTime
        else:
            time = f"{grb.forecastTime} to {grb.endStep}"

        data, lats, lons = grb.data()

        
        value = get_value_from_latlon(lat, lon, lats, lons, data)

        print(f"Probability of {limit} {val} {grb.units} {grb.name} at {time} hours from {grb.analDate} is {value} at {LAT},{LON}")


FILE_NAME = 'href.t12z.conus.prob.f42.grib2'
LAT = 24.02619
LON = -107.421197
get_all_readable_data(FILE_NAME, LAT, LON)


grbs = pygrib.open(FILE_NAME)
for grb in grbs:
    print(grb)

print("Short name:", grb.shortName)
print("Name:", grb.name)
print("Units:", grb.units)
print("Type of level:", grb.typeOfLevel)
print("Level:", grb.level)
print("Forecast time:", grb.forecastTime)
print("Start time:", grb.analDate)
print("End time:", grb.validDate)
print("Probability type:", grb.parameterCategory, grb.parameterNumber)
print("Description:", grb.parameterName)
print("Probability type", grb.probabilityType)
print("Lower limit", grb.lowerLimit)
print("Upper limit", grb.upperLimit)