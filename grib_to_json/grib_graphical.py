import pygrib





filename = "href_download/href.t12z.conus.prob.f01.grib2"
grbs = pygrib.open(filename)
for grb in grbs:
    print(grb)
grb = grbs.message(42)






import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# --- Extract from GRIB message ---
lats = grb.latitudes
lons = grb.longitudes
values = grb.values

# Reshape lat/lon to match the 2D grid
lats_2d = lats.reshape(values.shape)
lons_2d = lons.reshape(values.shape)

# --- Create DataArray with 2D lat/lon coords ---
da = xr.DataArray(
    data=values,
    dims=("y", "x"),
    coords={
        "lat": (("y", "x"), lats_2d),
        "lon": (("y", "x"), lons_2d),
    },
    name="value"
)

# --- Use the full dataset (no subsetting) ---
da_full = da

# --- Determine geographic extent (min/max of full data) ---
lon_min = float(da_full.lon.min())
lon_max = float(da_full.lon.max())
lat_min = float(da_full.lat.min())
lat_max = float(da_full.lat.max())

# --- Plot on correct coordinates ---
fig = plt.figure(figsize=(10, 6))
ax = plt.axes(projection=ccrs.PlateCarree())

# Set map extent to your data bounds
ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())

# Plot data using pcolormesh
pcm = ax.pcolormesh(
    da_full.lon,
    da_full.lat,
    da_full,
    cmap="viridis",
    vmin=0,
    vmax=100,
    shading="auto",
    transform=ccrs.PlateCarree()
)

# --- Add map features ---
ax.add_feature(cfeature.LAND, facecolor="lightgray")
ax.add_feature(cfeature.OCEAN, facecolor="lightblue")
ax.add_feature(cfeature.BORDERS, linestyle=":")
ax.add_feature(cfeature.COASTLINE)


# Add major populated places (major world cities)

# --- Final map polish ---
ax.gridlines(draw_labels=True)
# plt.colorbar(pcm, ax=ax, orientation="vertical", label="Value (0–100)")

plt.show()






# for key in grb.keys():
#     try:
#         print(f"{key}: {getattr(grb, key)}")
#     except Exception as e:
#         print(f"{key}: <unavailable> ({e})")


