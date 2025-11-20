import pygrib
import numpy as np
from pathlib import Path
import json
import re
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import Pool, cpu_count
import sys
from functools import partial

SCRIPT_DIR = Path(__file__).resolve().parent
PARENT_DIR = SCRIPT_DIR.parent

class SafeMemoryFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, "memory"):
            try:
                import psutil, os
                mem = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
                record.memory = f"{mem:,.1f}"
            except Exception:
                record.memory = "?"
        return super().format(record)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d | %(levelname)-8s | [MEM %(memory)s MB] | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)
for handler in logging.getLogger().handlers:
    handler.setFormatter(SafeMemoryFormatter(handler.formatter._fmt, handler.formatter.datefmt))

def compute_nearest_index(lat, lon, lats, lons):
    dist = (lats - lat) ** 2 + (lons - lon) ** 2
    return np.unravel_index(np.argmin(dist), dist.shape)

def is_interesting_message(grb, keywords_lower):
    """
    Fast checks:
      - check grb.name / grb.shortName / grb.parameterName (if available)
      - keywords_lower is a list of substrings to match (already lowercase)
    """
    try:
        candidates = []
        if hasattr(grb, "name") and grb.name:
            candidates.append(str(grb.name).lower())
        if hasattr(grb, "shortName") and grb.shortName:
            candidates.append(str(grb.shortName).lower())
        if hasattr(grb, "parameterName") and grb.parameterName:
            candidates.append(str(grb.parameterName).lower())
    except Exception:
        candidates = [str(grb).lower()]

    for kw in keywords_lower:
        for c in candidates:
            if kw in c:
                return True
    return False
def process_single_file(file_path_str, lat, lon, keywords_lower):
    """
    Opens the grib file, computes index once (using first message latlons) and
    extracts values from messages that match keywords_lower.
    Returns: (list_of_rows, anal_date_or_None, model_cycle_hint)
    list_of_rows: list of tuples -> (threshold_text, grb.name, step_length, forecastTime, value)
    model_cycle_hint: tuple (lowercase filename) to help determine model/cycle upstream
    """
    file_path = Path(file_path_str)
    readable_rows = []
    anal_date = None
    try:
        with pygrib.open(str(file_path)) as grbs:
            try:
                first = grbs.message(1)
                anal_date = first.analDate
                try:
                    lats, lons = first.latlons()
                except Exception:
                    _, lats, lons = first.data()
            
                row, col = compute_nearest_index(lat, lon, lats, lons)
            except Exception:
                row, col = None, None

            paren_re = re.compile(r'\(([^)]*?)\)')

            forecast_end = None
            m = re.search(r'f(\d{2,3})', file_path.name)
            if m:
                try:
                    forecast_end = int(m.group(1))
                except Exception:
                    forecast_end = None

            for grb in grbs:
                try:
                    if not is_interesting_message(grb, keywords_lower):
                        continue
                except Exception:
                    continue

                try:
                    anal_date = grb.analDate or anal_date
                except Exception:
                    pass

                try:
                    txt = str(grb)
                    pm = paren_re.findall(txt)
                    threshold_text = pm[-1].strip() if pm else "none"
                except Exception:
                    threshold_text = "none"

                units = getattr(grb, "units", "") or ""
                limit = f"{threshold_text} {units}".strip()
                if not (">" in limit or "<" in limit):
                        continue
                try:
                    if row is not None and col is not None:
                        values = getattr(grb, "values", None)
                        if values is None:
                            values, _, _ = grb.data()
                        value = float(values[row, col])
                    else:
                        data, lats2, lons2 = grb.data()
                        r, c = compute_nearest_index(lat, lon, lats2, lons2)
                        value = float(data[r, c])
                except Exception as e:
                    continue

                try:
                    step_length = (forecast_end - grb.forecastTime) if (forecast_end is not None) else None
                except Exception:
                    step_length = None

                readable_rows.append((limit, grb.name, step_length, grb.forecastTime, value))
    except Exception as e:
        logger.error(f"Error processing {file_path.name}: {e}")

    return readable_rows, anal_date, file_path.name.lower()


def make_json_file(folder_path, lat, lon, desired_forecast_types, max_workers=8):
    """
    folder_path: path to directory with grib files
    lat, lon: target point
    desired_forecast_types: list of substring keywords (case-insensitive)
    max_workers: used only for multiprocessing pool size hint (ignored by Pool's own defaults)
    """

    keywords_lower = [k.lower() for k in desired_forecast_types]

    folder_path = os.fspath(folder_path) if not isinstance(folder_path, (str, os.PathLike)) else folder_path
    logger.info(f"make_json_file: scanning folder {folder_path}")


    file_list = [str(p) for p in Path(folder_path).iterdir() if p.is_file()]
    if not file_list:
        logger.warning(f"No files found in {folder_path}")
        return


    pool_size = min(len(file_list), max(1, cpu_count() - 1))
    results = []
    try:
        with Pool(processes=pool_size) as pool:
            fn = partial(process_single_file, lat=lat, lon=lon, keywords_lower=keywords_lower)
            results = pool.map(fn, file_list)
    except Exception as e:
        logger.error(f"Multiprocessing error: {e}")

        results = [process_single_file(fp, lat, lon, keywords_lower) for fp in file_list]


    readable_data = []
    anal_date = None
    lower_first_fname = None
    for rows, ad, fname_lower in results:
        if rows:
            readable_data.extend(rows)
        if anal_date is None and ad:
            anal_date = ad
        if lower_first_fname is None and fname_lower:
            lower_first_fname = fname_lower


    model, cycle = "unknown", "unknown"
    fname = (lower_first_fname or "").lower()

    m = re.search(r"^(rrfs)\.(\d{8})t(\d{2})z", fname)
    if m:
        model = "RRFS"
        cycle = f"{m.group(3)}z"
    elif re.search(r"^href", fname):
        model = "HREF"
        cyc = re.search(r"t(\d{2})z", fname)
        if cyc:
            cycle = f"{cyc.group(1)}z"
    elif re.search(r"^refs", fname):
        model = "REFS"
        cyc = re.search(r"t(\d{2})z", fname)
        if cyc:
            cycle = f"{cyc.group(1)}z"
    elif re.search(r"^nbm", fname):
        model = "NBM"
        cyc = re.search(r"t(\d{2})z", fname)
        if cyc:
            cycle = f"{cyc.group(1)}z"

    headers = ["threshold", "name", "step_length", "forecast_time", "value"]

    output_data = {
        "metadata": {
            "sitrep": model,
            "anal_date": anal_date.strftime("%Y-%m-%d %H:%M:%S") if anal_date else "unknown",
            "location": {"lat": lat, "lon": lon},
            "folder": str(folder_path)
        },
        "data": [dict(zip(headers, row)) for row in readable_data],
    }

    DATA_DIR = PARENT_DIR / "cinder-app" / "backend" / "models"
    OUTDIR = DATA_DIR / "data"

    if not OUTDIR.exists():
        raise FileNotFoundError(f"Hardcoded output directory does not exist: {OUTDIR}")


    safe_lat = float(lat)
    safe_lon = float(lon)
    output_name = f"{model}{cycle}_for_{safe_lat},{safe_lon}.json"
    output_path = OUTDIR / output_name

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    logger.info(f"JSON saved to {output_path}")


def run_all_models(lat, lon):
    logger.info("Running ALL GRIB -> JSON conversions in parallel...")

    model_folders = {
        "HREF": PARENT_DIR / "href_data" / "href_download",
        "NBM": PARENT_DIR / "nbm_data" / "nbm_download",
        "REFS": PARENT_DIR / "refs_data" / "refs_download"
    }


    with ThreadPoolExecutor(max_workers=min(len(model_folders), cpu_count())) as execd:
        futures = []
        for _, folder in model_folders.items():
            futures.append(
                execd.submit(
                    make_json_file,
                    folder,
                    lat,
                    lon,
                    ["precip", "wind", "apparent", "2 metre", "relative humidity"],
                    max(1, cpu_count() // 2)
                )
            )
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                logger.error(f"Model conversion failed: {e}")

    logger.info("All GRIB -> JSON files have been generated.")



if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python grib_data_to_json.py <lat> <lon>")
        sys.exit(1)

    LAT = float(sys.argv[1])
    LON = float(sys.argv[2])
    run_all_models(LAT, LON)