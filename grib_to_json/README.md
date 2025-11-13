# GRIB to JSON Converter

Scripts for converting GRIB2 weather files to JSON.

## Files

grib_data_to_json.py - Main converter

- Converts GRIB2 files to JSON for a specific lat/lon
- Uses multithreading (8 workers)
- Monitors memory usage

forecast_json_parser.py - JSON reader

- Reads and displays the generated JSON files
- Uses orjson for fast parsing

grib_graphical.py - Visualization

- Creates map visualizations with matplotlib + cartopy

## How to Use

Edit grib_data_to_json.py and set your coordinates:

```python
LAT = 41.5623  # Hartford
LON = -72.6506

DESIRED_FORECAST_TYPES = [
    "Total Precipitation",
    "10 metre wind speed",
    "Apparent temperature",
    "2 metre temperature",
    "2 metre relative humidity"
]

FOLDER = Path("href_download")
```

Run it:

```bash
python grib_data_to_json.py
```

## Output

Generates JSON files like: `href12z_for_41.5623,-72.6506.json`

Format:

```json
{
  "metadata": {
    "model": "href",
    "forecast_time": "12z",
    "location": {"lat": 41.5623, "lon": -72.6506},
    "forecast_types": [...]
  },
  "data": [
    {
      "threshold": "none",
      "name": "2 metre temperature",
      "forecastTime": 1,
      "probability": 285.5
    }
  ]
}
```

## Dependencies

Install with: `pip install -r ../requirements.txt`

Needs:

- pygrib
- numpy
- psutil
- orjson
- matplotlib
- cartopy

## Connecticut Cities

Hartford: 41.5623, -72.6506
Middletown: 41.5623, -72.6508
Bridgeport: 41.2677, -73.2048
New Haven: 41.3083, -72.9279
