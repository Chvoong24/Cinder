import xarray as xr
import matplotlib.pyplot as plt 
import os
import pathlib
from pathlib import Path
import cartopy.crs as ccrs
import numpy as np
import pandas as pd

ds = xr.load_dataset("nbm_data/nbm_download/nbm_t00z_f001_custom.grib2", engine="cfgrib")



print(ds)
