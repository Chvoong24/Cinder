import pygrib
import numpy as np
import os
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv('cinder-app/backend/.env')

ATLAS_URI = os.getenv('MONGODB_URI')
NBM_DIR = Path('nbm_download')

CITIES = {
    "Hartford": (41.7627, -72.6743),
    "Middletown": (41.5623, -72.6506),
    "Bridgeport": (41.1792, -73.1894),
    "New Haven": (41.3083, -72.9279),
}

def find_ensemble_mean(grbs, param_name):
    for grb in grbs:
        if grb.name == param_name:
            try:
                if hasattr(grb, 'percentileValue') and grb.percentileValue is None:
                    product_type = grb.productDefinitionTemplateNumber
                    if product_type == 11 or 'mean' in str(grb).lower():
                        return grb
            except:
                try:
                    product_type = grb.productDefinitionTemplateNumber
                    if product_type == 11:
                        return grb
                except:
                    continue
    return None

def get_value_at_location(grb, city_name, lat, lon):
    try:
        data = grb.values
        lats, lons = grb.latlons()
        dist = np.sqrt((lats - lat)**2 + (lons - lon)**2)
        min_idx = np.unravel_index(np.argmin(dist), dist.shape)
        return data[min_idx]
    except:
        return None

def find_ensemble_mean_message(grbs, param_name_pattern):
    for grb in grbs:
        if param_name_pattern in grb.name.lower():
            try:
                product_type = grb.productDefinitionTemplateNumber
                if product_type == 11:
                    return grb
                percentile = getattr(grb, 'percentileValue', None)
                if percentile is None and 'mean' in str(grb).lower():
                    return grb
            except:
                if 'mean' in str(grb).lower() or 'ENSEMBLE MEAN' in str(grb):
                    return grb
    return None

def process_nbm_file(filepath, client):
    db = client["cinder_weather"]
    collection = db["points"]

    try:
        filename = Path(filepath).stem
        import re
        f_match = re.search(r'_f(\d+)_', filename)
        if f_match:
            forecast_hour = int(f_match.group(1))
        else:
            print(f"Warning: {filepath.name} - Could not extract forecast hour")
            return 0

        grbs = pygrib.open(str(filepath))
        all_messages = list(grbs)
        
        points_to_insert = []

        for city_name, (lat, lon) in CITIES.items():
            temp_grb = find_ensemble_mean_message(all_messages, '2 metre temperature')
            if temp_grb:
                temp_value = get_value_at_location(temp_grb, city_name, lat, lon)
                if temp_value is not None and not np.isnan(temp_value) and temp_value != 0:
                    temp_celsius = temp_value - 273.15
                    points_to_insert.append({
                        'threshold': 'temperature',
                        'lat': lat,
                        'lon': lon,
                        'name': city_name,
                        'step_length': forecast_hour,
                        'forecast_time': forecast_hour,
                        'value': float(temp_celsius),
                    })

            precip_grb = find_ensemble_mean_message(all_messages, 'total precipitation')
            if precip_grb:
                precip_value = get_value_at_location(precip_grb, city_name, lat, lon)
                if precip_value is not None and not np.isnan(precip_value):
                    points_to_insert.append({
                        'threshold': 'precipitation',
                        'lat': lat,
                        'lon': lon,
                        'name': city_name,
                        'step_length': forecast_hour,
                        'forecast_time': forecast_hour,
                        'value': float(precip_value),
                    })

            u_grb = None
            v_grb = None
            for grb in all_messages:
                if '10 m' in grb.name.lower():
                    try:
                        product_type = grb.productDefinitionTemplateNumber
                        if product_type == 11:
                            if 'u-component' in grb.name.lower() or ':ugrd:' in str(grb).lower():
                                u_grb = grb
                            elif 'v-component' in grb.name.lower() or ':vgrd:' in str(grb).lower():
                                v_grb = grb
                    except:
                        pass

            if u_grb and v_grb:
                u_value = get_value_at_location(u_grb, city_name, lat, lon)
                v_value = get_value_at_location(v_grb, city_name, lat, lon)
                if u_value is not None and v_value is not None and not np.isnan(u_value) and not np.isnan(v_value):
                    wind_speed = np.sqrt(u_value**2 + v_value**2)
                    wind_dir = np.degrees(np.arctan2(-u_value, -v_value)) % 360
                    
                    points_to_insert.append({
                        'threshold': 'wind_speed',
                        'lat': lat,
                        'lon': lon,
                        'name': city_name,
                        'step_length': forecast_hour,
                        'forecast_time': forecast_hour,
                        'value': float(wind_speed * 3.6),
                    })
                    points_to_insert.append({
                        'threshold': 'wind_direction',
                        'lat': lat,
                        'lon': lon,
                        'name': city_name,
                        'step_length': forecast_hour,
                        'forecast_time': forecast_hour,
                        'value': float(wind_dir),
                    })

            rh_grb = find_ensemble_mean_message(all_messages, 'relative humidity')
            if rh_grb:
                rh_value = get_value_at_location(rh_grb, city_name, lat, lon)
                if rh_value is not None and not np.isnan(rh_value):
                    points_to_insert.append({
                        'threshold': 'humidity',
                        'lat': lat,
                        'lon': lon,
                        'name': city_name,
                        'step_length': forecast_hour,
                        'forecast_time': forecast_hour,
                        'value': float(rh_value),
                    })

            pres_grb = find_ensemble_mean_message(all_messages, 'surface pressure')
            if pres_grb:
                pres_value = get_value_at_location(pres_grb, city_name, lat, lon)
                if pres_value is not None and not np.isnan(pres_value):
                    points_to_insert.append({
                        'threshold': 'pressure',
                        'lat': lat,
                        'lon': lon,
                        'name': city_name,
                        'step_length': forecast_hour,
                        'forecast_time': forecast_hour,
                        'value': float(pres_value / 100),
                    })

        grbs.close()

        if points_to_insert:
            collection.insert_many(points_to_insert)
            print(f"{filepath.name}: Inserted {len(points_to_insert)} points")
            return len(points_to_insert)
        else:
            print(f"⚠ {filepath.name}: No data extracted")
            return 0

    except Exception as e:
        print(f"✗ {filepath.name}: Error - {e}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    if not ATLAS_URI:
        print("Error: MONGODB_URI not found in .env")
        return

    client = MongoClient(ATLAS_URI)
    
    all_files = sorted(NBM_DIR.glob('nbm_*.grib2'))
    new_files = [f for f in all_files if 't00z' in f.name or 't12z' in f.name]
    
    if new_files:
        nbm_files = sorted(new_files)[-48:]
        print(f"Processing newest {len(nbm_files)} files (from {len(all_files)} total)\n")
    else:
        nbm_files = sorted(all_files)
        print(f"Found {len(nbm_files)} NBM files to process\n")

    total_points = 0
    processed = 0
    for filepath in nbm_files:
        processed += 1
        print(f"[{processed}/{len(nbm_files)}] Processing {filepath.name}...")
        count = process_nbm_file(filepath, client)
        total_points += count

    print(f"\nComplete. Inserted {total_points} total points into MongoDB Atlas")
    client.close()

if __name__ == "__main__":
    main()

