"""
GRIB to MongoDB Bridge Script
This script reads downloaded GRIB2 files, parses weather data, and inserts into MongoDB
"""

import os
import sys
import pygrib
import logging
from pathlib import Path
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# =========================
# Configuration
# =========================

# load MongoDB connection from backend .env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / "backend" / ".env")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/cinder_weather")

# GRIB file directories
SCRIPT_DIR = Path(__file__).resolve().parent
NBM_DIR = SCRIPT_DIR / "nbm_data" / "nbm_download"
HREF_DIR = SCRIPT_DIR / "href_data" / "href_download"
REFS_DIR = SCRIPT_DIR / "refs_data" / "refs_download"

# Logging
LOG_DIR = SCRIPT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOGFILE = LOG_DIR / "grib_to_mongodb.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOGFILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =========================
# MongoDB Connection
# =========================

def connect_mongodb():
    try:
        client = MongoClient(MONGODB_URI)
        db = client["cinder_weather"]
        collection = db["weatherdatas"]
        client.admin.command('ping')
        logger.info(f"Connected to MongoDB: {db.name}")
        return collection
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        sys.exit(1)

# =========================
# GRIB Parsing Functions
# =========================

def kelvin_to_celsius(kelvin):
    if kelvin is None:
        return None
    return round(kelvin - 273.15, 2)

def extract_location_from_filename(filename):
    locations = [
        {"type": "Point", "coordinates": [-72.6506, 41.5623], "name": "Hartford"},
        {"type": "Point", "coordinates": [-72.6508, 41.5623], "name": "Middletown"},
        {"type": "Point", "coordinates": [-73.2048, 41.2677], "name": "Bridgeport"},
        {"type": "Point", "coordinates": [-72.9279, 41.3083], "name": "New Haven"},
    ]
    return locations

def get_value_at_location(grb, lat, lon):
    try:
        lats, lons = grb.latlons()
        import numpy as np
        # find nearest grid point to our location
        lat_diff = np.abs(lats - lat)
        lon_diff = np.abs(lons - lon)
        distance = np.sqrt(lat_diff**2 + lon_diff**2)
        min_idx = np.unravel_index(distance.argmin(), distance.shape)
        value = grb.values[min_idx]
        return float(value) if not np.isnan(value) else None
    except Exception as e:
        logger.warning(f"Error extracting location-specific value: {e}")
        return None

def parse_grib_file(grib_path, model_source="NBM"):
    weather_records = []
    
    try:
        logger.info(f"Parsing GRIB file: {grib_path}")
        grbs = pygrib.open(str(grib_path))
        
        filename = grib_path.name
        forecast_hour = 0
        # pull forecast hour from filename
        import re
        fh_match = re.search(r'f(\d{2,3})', filename)
        if fh_match:
            forecast_hour = int(fh_match.group(1))
        
        locations = extract_location_from_filename(filename)
        # set up data storage for each city
        location_data = {}
        for loc in locations:
            location_data[loc['name']] = {
                'location': loc,
                'temp': {},
                'precip': {},
                'wind': {},
                'humidity': {},
                'pressure': {}
            }
        
        # iterate through GRIB messages and extract data for each location
        for grb in grbs:
            param_name = grb.name
            for loc_name, data in location_data.items():
                lat = data['location']['coordinates'][1]
                lon = data['location']['coordinates'][0]
                
                if "2 metre temperature" in param_name or "2-metre temperature" in param_name:
                    temp_k = get_value_at_location(grb, lat, lon)
                    if temp_k:
                        data['temp']['current'] = kelvin_to_celsius(temp_k)
                    
                elif "Total Precipitation" in param_name or "precipitation" in param_name.lower():
                    precip_val = get_value_at_location(grb, lat, lon)
                    if precip_val is not None:
                        data['precip']['amount'] = precip_val
                        data['precip']['type'] = "rain"
                    
                elif "10 metre U wind component" in param_name or "u-component of wind" in param_name.lower():
                    u_val = get_value_at_location(grb, lat, lon)
                    if u_val is not None:
                        data['wind']['u'] = u_val
                    
                elif "10 metre V wind component" in param_name or "v-component of wind" in param_name.lower():
                    v_val = get_value_at_location(grb, lat, lon)
                    if v_val is not None:
                        data['wind']['v'] = v_val
                    
                elif "Relative humidity" in param_name or "relative humidity" in param_name.lower():
                    humid_val = get_value_at_location(grb, lat, lon)
                    if humid_val is not None:
                        data['humidity']['value'] = humid_val
                    
                elif "Pressure" in param_name or "Mean sea level pressure" in param_name:
                    press_val = get_value_at_location(grb, lat, lon)
                    if press_val is not None:
                        data['pressure']['value'] = press_val / 100  # Pa to hPa
        
        # calculate wind speed/direction from u and v components
        for loc_name, data in location_data.items():
            if 'u' in data['wind'] and 'v' in data['wind']:
                import math
                wind_speed = math.sqrt(data['wind']['u']**2 + data['wind']['v']**2) * 3.6  # m/s to km/h
                wind_direction = (math.degrees(math.atan2(data['wind']['u'], data['wind']['v'])) + 180) % 360
                data['wind']['speed'] = round(wind_speed, 2)
                data['wind']['direction'] = round(wind_direction, 2)
        
        grbs.close()
        timestamp = datetime.now(timezone.utc)
        # build final weather documents
        for loc_name, data in location_data.items():
            weather_doc = {
                "location": data['location'],
                "timestamp": timestamp,
                "forecastHour": forecast_hour,
                "temperature": {
                    "current": data['temp'].get('current'),
                    "min": data['temp'].get('min'),
                    "max": data['temp'].get('max'),
                    "unit": "celsius"
                },
                "precipitation": {
                    "amount": data['precip'].get('amount'),
                    "type": data['precip'].get('type', "rain"),
                    "unit": "mm"
                },
                "wind": {
                    "speed": data['wind'].get('speed'),
                    "direction": data['wind'].get('direction'),
                    "unit": "km/h"
                },
                "humidity": data['humidity'].get('value'),
                "pressure": {
                    "value": data['pressure'].get('value'),
                    "unit": "hPa"
                },
                "modelSource": model_source,
                "rawData": {
                    "filename": filename,
                    "parsedAt": datetime.now(timezone.utc).isoformat()
                }
            }
            weather_records.append(weather_doc)
        
        logger.info(f"Successfully parsed {filename}: {len(weather_records)} records for {len(location_data)} locations")
        
    except Exception as e:
        logger.error(f"Error parsing GRIB file {grib_path}: {e}")
    
    return weather_records

# =========================
# Main Processing
# =========================

def process_grib_directory(directory, model_source, collection):
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return 0
    
    grib_files = list(directory.glob("*.grib2"))
    
    if not grib_files:
        logger.info(f"No GRIB files found in {directory}")
        return 0
    
    logger.info(f"Found {len(grib_files)} GRIB files in {directory}")
    
    inserted_count = 0
    
    for grib_file in grib_files:
        weather_records = parse_grib_file(grib_file, model_source)
        
        for record in weather_records:
            try:
                result = collection.insert_one(record)
                inserted_count += 1
                logger.info(f"✅ Inserted record: {result.inserted_id}")
            except DuplicateKeyError:
                logger.warning(f"⚠️  Duplicate record, skipping...")
            except Exception as e:
                logger.error(f"❌ Error inserting record: {e}")
    
    return inserted_count

def main():
    logger.info("=" * 60)
    logger.info("Starting GRIB to MongoDB sync")
    logger.info("=" * 60)
    
    collection = connect_mongodb()
    total_inserted = 0
    
    logger.info("\n📊 Processing NBM data...")
    total_inserted += process_grib_directory(NBM_DIR, "NBM", collection)
    
    logger.info("\n📊 Processing HREF data...")
    total_inserted += process_grib_directory(HREF_DIR, "HREF", collection)
    
    logger.info("\n📊 Processing REFS data...")
    total_inserted += process_grib_directory(REFS_DIR, "REFS", collection)
    
    logger.info("=" * 60)
    logger.info(f"✅ Sync complete! Total records inserted: {total_inserted}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()

