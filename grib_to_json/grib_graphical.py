import pygrib





filename = "blend.t00z.qmd.f001.co.grib2"
grbs = pygrib.open(filename)
for grb in grbs:
    print(grb)
grb = grbs.message(42)






import xarray
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

lats = grb.latitudes
lons = grb.longitudes
values = grb.values

lats_two_dimensional = lats.reshape(values.shape)
lons_two_dimensional = lons.reshape(values.shape)

da = xarray.DataArray(
    data=values,
    dims=("y", "x"),
    coords={
        "lat": (("y", "x"), lats_two_dimensional),
        "lon": (("y", "x"), lons_two_dimensional),
    },
    name="value"
)



lon_min = float(da.lon.min())
lon_max = float(da.lon.max())
lat_min = float(da.lat.min())
lat_max = float(da.lat.max())

figure = plt.figure(figsize=(10, 6))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())

pcm = ax.pcolormesh(
    da.lon,
    da.lat,
    da,
    cmap="viridis",
    vmin=0,
    vmax=100,
    shading="auto",
    transform=ccrs.PlateCarree()
)

ax.add_feature(cfeature.LAND, facecolor="lightgray")
ax.add_feature(cfeature.OCEAN, facecolor="lightblue")
ax.add_feature(cfeature.BORDERS, linestyle=":")
ax.add_feature(cfeature.COASTLINE)


ax.gridlines(draw_labels=True)
# plt.colorbar(pcm, ax=ax, orientation="vertical", label="Value (0–100)")

plt.show()






# for key in grb.keys():
#     try:
#         print(f"{key}: {getattr(grb, key)}")
#     except Exception as e:
#         print(f"{key}: <unavailable> ({e})")


