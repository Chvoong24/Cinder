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
ds = xr.load_dataset("nbm_download/nbm_t18z_f051_custom.grib2", engine="cfgrib")
def main():
    # ds = xr.load_dataset("nbm_data/nbm_download/nbm_t00z_f001_custom.grib2", engine="cfgrib")
    plt.figure()

# if __name__ == "__main__":
#     # main()
# plt.pcolormesh(lon, lat, temp[0, :, :]);

# print(ds.coords["longitude"])\


lat = ds.latitude.data
lon = ds.longitude.data
# temp = ds.data_vars["aptmp"].data

ds.attrs
ds.data_vars
ds.coords
# plt.figure()
# plt.pcolormesh(lon, lat, temp[:, :]);




