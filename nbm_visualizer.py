import xarray as xr
import numpy as np
import pprint
import pygrib

grib_path = "nbm_data/nbm_download/blend.t00z.qmd.f001.co.grib2"


# open only data at 2 meters above ground, can adjust field make a variable
ds = xr.open_dataset(
    grib_path,
    engine="cfgrib"
    # backend_kwargs={"filter_by_keys": {"typeOfLevel": "heightAboveGround", "level": 2}}
)

ds 
lat = ds['latitude']
lon = ds['longitude']

# Target location
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
# print(f"  Indices:   (y={iy}, x={ix})")

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
#     print(val)

# print("\n--- SELECTED POINT DATA (summary) ---")
# point_data = {var: ds[var].isel(y=iy, x=ix).values for var in ds.data_vars}
# pprint.pprint(point_data)# --- Identify probabilistic variables ---
prob_vars = [
    var for var in ds.data_vars
    if "prob" in var.lower() or "probability" in ds[var].attrs.get("long_name", "").lower()
]

if not prob_vars:
    print("\nNo probabilistic variables found in this dataset.")
else:
    print("\n--- PROBABILISTIC VARIABLES ---")
    for var in prob_vars:
        print(f"\nVariable: {var}")
        pprint.pprint(ds[var].attrs)
        value = ds[var].isel(y=iy, x=ix).values
        print(f"Value at nearest grid point: {value}")



# grbs = pygrib.open("nbm_data/nbm_download/blend.t00z.qmd.f001.co.grib2")
# grbs.seek(0)
# for grb in grbs:
#     print(grb)