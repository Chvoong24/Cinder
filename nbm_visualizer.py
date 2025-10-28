import xarray as xr
import matplotlib.pyplot as plt 
import os
import pathlib
from pathlib import Path
import cartopy.crs as ccrs
import numpy as np
import pandas as pd


# lat = ds.air.lat.data
# lon = ds.air.lon.data
# temp = ds.air.data
ds = xr.load_dataset("nbm_data/nbm_download/nbm_t00z_f001_custom.grib2.part", engine="cfgrib")
# ds.sel(lat = 52, long = 251.8998, method = "nearest").plot()

# if __name__ == "__main__":
#     # main()
# plt.pcolormesh(lon, lat, temp[0, :, :]);

# print(ds.coords["longitude"])\
# lat = ds.latitude.data
# lon = ds.longitude.data
ds
# ds.sel(time="2025-10-28")



# # temp = ds.data_vars["aptmp"].data

# ds.attrs
# ds.data_vars
# ds.coords
# plt.figure()
# plt.pcolormesh(lon, lat, temp[:, :]);
