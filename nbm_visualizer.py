# %%
import xarray as xr
import numpy as np
import pprint

# Path to GRIB file
grib_path = "nbm_data/nbm_download/blend.t18z.qmd.f051.co.grib2"

# Load the dataset

# Example: open only data at 2 meters above ground
ds = xr.open_dataset(
    grib_path,
    engine="cfgrib",
    backend_kwargs={"filter_by_keys": {"typeOfLevel": "heightAboveGround", "level": 2}}
)


lat = ds['latitude']
lon = ds['longitude']

# Target location (example: Denver)
target_lat = 39.7392
target_lon = -104.9903

# Compute distance on the sphere (approximation)
dist = np.sqrt((lat - target_lat)**2 + (lon - target_lon)**2)

# Find the indices of the nearest grid point
iy, ix = np.unravel_index(np.argmin(dist.values), dist.shape)
nearest_lat = lat.values[iy, ix]
nearest_lon = lon.values[iy, ix]

print(f"\nNearest grid point found at:")
print(f"  Latitude:  {nearest_lat}")
print(f"  Longitude: {nearest_lon}")
print(f"  Indices:   (y={iy}, x={ix})")

# Print global dataset info
print("\n--- DATASET SUMMARY ---")
print(ds)

print("\n--- GLOBAL ATTRIBUTES ---")
pprint.pprint(ds.attrs)

# Print coordinate metadata
print("\n--- COORDINATES ---")
for coord in ds.coords:
    print(f"\nCoordinate: {coord}")
    pprint.pprint(ds[coord].attrs)

# Print variable-level metadata and value at the nearest point
print("\n--- VARIABLES AND METADATA ---")
for var in ds.data_vars:
    print(f"\nVariable: {var}")
    pprint.pprint(ds[var].attrs)
    print("Value at nearest grid point:")
    val = ds[var].isel(y=iy, x=ix).values
    print(val)

print("\n--- SELECTED POINT DATA (summary) ---")
point_data = {var: ds[var].isel(y=iy, x=ix).values for var in ds.data_vars}
pprint.pprint(point_data)