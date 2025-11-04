# GRIB to JSON Converter

This folder contains scripts to convert GRIB2 weather data files to JSON format.

## Files

1. **grib_data_to_json.py** - Main converter script

   - Converts GRIB2 files to JSON for a specific lat/lon location
   - Uses multithreading (8 workers) for fast processing
   - Monitors memory usage during conversion

2. **forecast_json_parser.py** - JSON reader

   - Simple script to read and display the generated JSON files
   - Uses `orjson` for fast parsing

3. **grib_graphical.py** - Visualization tool
   - Creates map visualizations using matplotlib + cartopy
   - Shows weather data on geographic maps

## Usage

### Basic Usage

Edit `grib_data_to_json.py` and configure:

```python
LAT = 41.5623  # Your latitude
LON = -72.6506  # Your longitude

DESIRED_FORECAST_TYPES = [
    "Total Precipitation",
    "10 metre wind speed",
    "Apparent temperature",
    "2 metre temperature",
    "2 metre relative humidity"
]

FOLDER = Path("href_download")  # Path to GRIB files
```

Then run:

```bash
python grib_data_to_json.py
```

### Output

Generates JSON files named like:

```
HREF12z_for_41.5623,-72.6506.json
```

### JSON Structure

```json
{
  "metadata": {
    "sitrep": "HREF",
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

Install with:

```bash
pip install -r ../requirements.txt
```

Required packages:

- pygrib
- numpy
- psutil
- orjson
- matplotlib
- cartopy

## Connecticut Cities Coordinates

For reference, here are the 4 Connecticut cities:

- **Hartford**: 41.5623, -72.6506
- **Middletown**: 41.5623, -72.6508
- **Bridgeport**: 41.2677, -73.2048
- **New Haven**: 41.3083, -72.9279
