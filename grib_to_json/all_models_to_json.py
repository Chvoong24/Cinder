#!/usr/bin/env python3
# all_models_to_json.py (orchestrator)
from concurrent.futures import ThreadPoolExecutor
import subprocess
from pathlib import Path
import sys
import os
from multiprocessing import cpu_count

SCRIPT_DIR = Path(__file__).resolve().parent
GRIB_SCRIPT = SCRIPT_DIR / "grib_data_to_json.py"

def run_script(lat, lon):
    # call the optimized grib_data_to_json directly with lat/lon (it runs all models internally)
    subprocess.run(["python3", str(GRIB_SCRIPT), str(lat), str(lon)], check=True)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Error: Missing LAT LON arguments")
        print("Usage: python all_models_to_json.py <lat> <lon>")
        sys.exit(1)

    lat = sys.argv[1]
    lon = sys.argv[2]

    # use a small threadpool to invoke the script once (grib_data_to_json already parallelizes per-model)
    with ThreadPoolExecutor(max_workers=1) as exe:
        futures = [exe.submit(run_script, lat, lon)]
        for f in futures:
            f.result()