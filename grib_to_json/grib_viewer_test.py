import pygrib

# ========= Testing =============

FILE_NAME = "href_download/href.t12z.conus.prob.f06.grib2"

nbm_names = []
grbs = pygrib.open(FILE_NAME)


for grb in grbs:
    # print(grb)
    nbm_names.append(grb.name)


# for key in grb.keys():
#     try:
#         print(f"{key}: {getattr(grb, key)}")
#     except Exception as e:
#         print(f"{key}: <unavailable> ({e})")


# nbm_names = set(nbm_names)
# for name in nbm_names:
#     print(name)


grb = grbs.message(32)
print(grb)
# print("Short name:", grb.shortName)
# print("Name:", grb.name)
# print("Units:", grb.units)
# print("Type of level:", grb.typeOfLevel)
# print("Level:", grb.level)
print("Forecast time:", grb.forecastTime)
print("Anal date:", grb.analDate)
print("Start time:", grb.validDate)
print("Step units:", grb.stepUnits)
# print("Probability type:", grb.parameterCategory, grb.parameterNumber)
# print("Description:", grb.parameterName)
# print("Probability type", grb.probabilityType)
# print("Lower limit", grb.lowerLimit)
# print("Upper limit", grb.upperLimit)
grb = grbs.message(36)
print(grb)
# print("Short name:", grb.shortName)
# print("Name:", grb.name)
# print("Units:", grb.units)
# print("Type of level:", grb.typeOfLevel)
# print("Level:", grb.level)
print("Forecast time:", grb.forecastTime)
print("Anal date:", grb.analDate)
print("Start time:", grb.validDate)
print("Step units:", grb.stepUnits)
# print("Probability type:", grb.parameterCategory, grb.parameterNumber)
# print("Description:", grb.parameterName)
grb = grbs.message(41)
print(grb)
# print("Short name:", grb.shortName)
# print("Name:", grb.name)
# print("Units:", grb.units)
# print("Type of level:", grb.typeOfLevel)
# print("Level:", grb.level)
print("Forecast time:", grb.forecastTime)
print("Anal date:", grb.analDate)
print("Start time:", grb.validDate)
print("Step units:", grb.stepUnits)
# print("Probability type:", grb.parameterCategory, grb.parameterNumber)
# print("Description:", grb.parameterName)


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