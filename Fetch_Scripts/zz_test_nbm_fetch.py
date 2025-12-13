"""
NBM QMD subset downloader using .idx + HTTP Range

Features:
- Supports all NBM cycles: 00Z, 06Z, 12Z, 18Z
- Auto-detects most recent run based on current UTC time
- Optional manual override of run date and cycle via CLI
- Optional single-forecast-hour mode (e.g., --hour 156)
- Uses .idx files and HTTP Range requests to download ONLY needed GRIB messages
- Uses ThreadPoolExecutor for parallel forecast-hour processing
- For full runs: wipes existing subset files in the cycle folder before writing new ones

Usage:
- python zz_test_nbm_fetch.py Picks most recent cycle by UTC time.
- python zz_test_nbm_fetch.py --date 20251123 --cycle 12 Downloads the cycle and date for manual download
- python zz_test_nbm_fetch.py --date 20251123 --cycle 12 --hour 156 Downloads only the f-hour requested. Leaves all other files intact.
"""

import re
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

# ----------------- Constants / thresholds ----------------- #

BASE_URL = "https://noaa-nbm-para-pds.s3.amazonaws.com"

# Temperature thresholds (K)
APTMP_ABOVE = [310.928, 313.706, 316.483]  # warm thresholds
APTMP_BELOW = [273.14, 270.928, 255.372]

TMP_MIN_THRESH = [273.15, 270.928, 260.928]
TMP_MAX_THRESH = [273.15, 305.372, 310.928]

# Precip thresholds (mm)
APCP_24_48_THRESH = [76.2, 127.0, 152.4, 203.2]
APCP_72_THRESH = [76.2, 127.0, 203.2, 254.0]

# Percentiles we want
PERCENTILES = [10, 25, 50, 75, 90, 95, 100]

# Float comparison tolerance
TOL = 0.01

# Globals that get initialized per run
RUN_DATE = None   # "YYYYMMDD"
CYCLE = None      # "00","06","12","18"
DOMAIN = None     # e.g. "co"
OUT_DIR = None    # Path

APTMP_HOURS   = set()
TMP_MIN_HOURS = set()
TMP_MAX_HOURS = set()
GUST_HOURS    = set()
APCP24_HOURS  = set()
APCP48_HOURS  = set()
APCP72_HOURS  = set()
ALL_HOURS     = []


# ----------------- Hour configuration per cycle ----------------- #

def build_aptemp_hours_common():
    """APTMP hours are the same for all cycles."""
    h1 = list(range(1, 48, 1))     # 1–60 every hour
    return sorted(set(h1))


HOUR_CONFIG = {
    "00": {
        "tmp_min": [18, 42],
        "tmp_max": [30],
        "gust":    [30],

        "apcp24": list(range(24, 48, 6)),   # [24, 30, 36, 42]
        "apcp48": [48],
        "apcp72": [],
    },

    "06": {
        "tmp_min": [36],
        "tmp_max": [24, 48],
        "gust": list(range(24, 48, 24)),    # [24]

        "apcp24": list(range(24, 48, 6)),
        "apcp48": [],
        "apcp72": [],
    },

    "12": {
        "tmp_min": [30],
        "tmp_max": [18, 42],
        "gust": [42],

        "apcp24": list(range(24, 48, 6)),
        "apcp48": [48],
        "apcp72": [],
    },

    "18": {
        "tmp_min": [24, 48],
        "tmp_max": [36],
        "gust": [36],

        "apcp24": list(range(24, 48, 6)),
        "apcp48": [],
        "apcp72": [],
    },
}


def init_hour_sets(cycle: str):
    """Initialize the global hour sets based on the NBM cycle ("00","06","12","18")."""
    global APTMP_HOURS, TMP_MIN_HOURS, TMP_MAX_HOURS
    global GUST_HOURS, APCP24_HOURS, APCP48_HOURS, APCP72_HOURS, ALL_HOURS

    if cycle not in HOUR_CONFIG:
        raise ValueError(f"Unsupported cycle '{cycle}', expected one of {list(HOUR_CONFIG.keys())}")

    cfg = HOUR_CONFIG[cycle]

    APTMP_HOURS   = set(build_aptemp_hours_common())
    TMP_MIN_HOURS = set(cfg["tmp_min"])
    TMP_MAX_HOURS = set(cfg["tmp_max"])
    GUST_HOURS    = set(cfg["gust"])

    apcp24_h1 = cfg["apcp24"]
    apcp48_h1 = cfg["apcp48"]
    apcp72_h1 = cfg["apcp72"]

    APCP24_HOURS = set(apcp24_h1)
    APCP48_HOURS = set(apcp48_h1)
    APCP72_HOURS = set(apcp72_h1)

    print(apcp24_h1)

    ALL_HOURS = sorted(
        APTMP_HOURS
        | TMP_MIN_HOURS
        | TMP_MAX_HOURS
        | GUST_HOURS
        | APCP24_HOURS
        | APCP48_HOURS
        | APCP72_HOURS
    )


# ----------------- Run / path setup ----------------- #

def auto_detect_run():
    """
    Returns (RUN_DATE, CYCLE) based on current UTC time.
    Rule: use the most recent 00/06/12/18Z cycle at current UTC.
    """
    now = datetime.now(timezone.utc)
    hour = now.hour

    if hour >= 18:
        cycle = "18"
    elif hour >= 12:
        cycle = "12"
    elif hour >= 6:
        cycle = "06"
    else:
        cycle = "00"

    run_date = now.strftime("%Y%m%d")
    return run_date, cycle


def setup_run_paths(run_date: str, cycle: str, domain: str):
    """
    Set up globals RUN_DATE, CYCLE, DOMAIN, OUT_DIR based on user/auto settings.
    Output folder structure: nbm_{cycle}z_qmd_subset_idx/
    (all dates share the same cycle folder; cleaned before full runs)
    """
    global RUN_DATE, CYCLE, DOMAIN, OUT_DIR

    RUN_DATE = run_date
    CYCLE = cycle
    DOMAIN = domain

    base_dir = Path(f"nbm_data")
    OUT_DIR = Path(f"{base_dir}/nbm_downloads")
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def clean_output_dir_full():
    """Delete all subset GRIB2 files in OUT_DIR (for full-cycle runs)."""
    removed = 0
    for f in OUT_DIR.glob("*.subset.grib2"):
        f.unlink()
        removed += 1
    print(f"[INFO] Cleaned {removed} existing subset file(s) in {OUT_DIR}")


def clean_single_hour(hour: int):
    """Delete only the target hour's subset file (for single-hour repair runs)."""
    target = OUT_DIR / f"blend.t{CYCLE}z.qmd.f{hour:03d}.{DOMAIN}.subset.grib2"
    if target.exists():
        target.unlink()
        print(f"[INFO] Removed existing file for f{hour:03d}: {target.name}")


# ----------------- Parsing helpers ----------------- #

def parse_trange(trange):
    """
    Parse a wgrib2-style time range into (start_hr, end_hr, kind).

    Examples:
      "6 hour fcst"           -> (0, 6, "fcst")
      "0-18 hour min fcst"    -> (0, 18, "min")
      "24-48 hour acc fcst"   -> (24, 48, "acc")
      "0-1 day acc fcst"      -> (0, 24, "acc")
      "1-3 day acc fcst"      -> (24, 72, "acc")
    """
    kind = "fcst"
    if "min fcst" in trange:
        kind = "min"
    elif "max fcst" in trange:
        kind = "max"
    elif "acc fcst" in trange:
        kind = "acc"

    # Day-based
    if "day" in trange:
        m = re.search(r"(\d+)-(\d+) day", trange)
        if m:
            a = int(m.group(1))
            b = int(m.group(2))
            return 24 * a, 24 * b, kind
        m = re.search(r"(\d+) day", trange)
        if m:
            b = int(m.group(1))
            return 0, 24 * b, kind

    # Hour-based
    m = re.search(r"(\d+)-(\d+) hour", trange)
    if m:
        a = int(m.group(1))
        b = int(m.group(2))
        return a, b, kind

    m = re.search(r"(\d+) hour", trange)
    if m:
        b = int(m.group(1))
        return 0, b, kind

    return 0, 0, kind


def parse_probability(details):
    """Parse 'prob >310.928' or 'prob <273.15' from inventory details."""
    m = re.search(r"prob\s*([<>])\s*([0-9.]+)", details)
    if not m:
        return None, None
    sign = m.group(1)
    val = float(m.group(2))
    return sign, val


def parse_percentile(details):
    """Parse '50% level' etc. from inventory details."""
    m = re.search(r"(\d+)% level", details)
    if not m:
        return None
    return int(m.group(1))


def accumulate_hours_for_acc(acc_hours):
    """Map accumulation length to the hour set we want (24, 48, 72)."""
    if acc_hours == 24:
        return APCP24_HOURS
    elif acc_hours == 48:
        return APCP48_HOURS
    elif acc_hours == 72:
        return APCP72_HOURS
    else:
        return set()


# ----------------- Matchers ----------------- #

def is_aptemp_prob(var, level, trange, details, fhr):
    if var != "APTMP" or level != "2 m above ground":
        return False
    start_hr, end_hr, kind = parse_trange(trange)
    if end_hr != fhr or kind != "fcst":
        return False
    sign, val = parse_probability(details)
    if sign is None:
        return False

    # To temporarily disable warm thresholds in winter, you can do:
    # if sign == ">": return False
    if sign == ">":
        # return any(abs(val - t) < TOL for t in APTMP_ABOVE)
        return False
    else:
        return any(abs(val - t) < TOL for t in APTMP_BELOW)


def is_tmp_min_prob(var, level, trange, details, fhr):
    if var != "TMP" or level != "2 m above ground":
        return False
    start_hr, end_hr, kind = parse_trange(trange)
    if end_hr != fhr or kind != "min":
        return False
    if fhr not in TMP_MIN_HOURS:
        return False
    sign, val = parse_probability(details)
    if sign != "<":
        return False
    return any(abs(val - t) < TOL for t in TMP_MIN_THRESH)


def is_tmp_max_prob(var, level, trange, details, fhr):
    if var != "TMP" or level != "2 m above ground":
        return False
    start_hr, end_hr, kind = parse_trange(trange)
    if end_hr != fhr or kind != "max":
        return False
    if fhr not in TMP_MAX_HOURS:
        return False
    sign, val = parse_probability(details)
    if sign is None:
        return False
    # You specified prob <273.15, >305.372, >310.928
    return any(abs(val - t) < TOL for t in TMP_MAX_THRESH)


def is_gust_50pct(var, level, trange, details, fhr):
    if var != "GUST" or level != "10 m above ground":
        return False
    start_hr, end_hr, kind = parse_trange(trange)
    if end_hr != fhr or kind != "max":
        return False
    if fhr not in GUST_HOURS:
        return False
    pct = parse_percentile(details)
    return pct == 50


def is_apcp_prob(var, level, trange, details, fhr, acc_hours, thresholds):
    if var != "APCP" or level != "surface":
        return False
    start_hr, end_hr, kind = parse_trange(trange)
    if end_hr != fhr or kind != "acc":
        return False
    if (end_hr - start_hr) != acc_hours:
        return False
    if fhr not in accumulate_hours_for_acc(acc_hours):
        return False
    sign, val = parse_probability(details)
    if sign != ">":
        return False
    return any(abs(val - t) < TOL for t in thresholds)


def is_apcp_percentile(var, level, trange, details, fhr, acc_hours):
    if var != "APCP" or level != "surface":
        return False
    start_hr, end_hr, kind = parse_trange(trange)
    if end_hr != fhr or kind != "acc":
        return False
    if (end_hr - start_hr) != acc_hours:
        return False
    if fhr not in accumulate_hours_for_acc(acc_hours):
        return False
    pct = parse_percentile(details)
    if pct is None:
        return False
    return pct in PERCENTILES


def match_record(var, level, trange, details, fhr):
    """Return True if this inventory line matches any of the requested products."""
    # APTMP probs
    if fhr in APTMP_HOURS and is_aptemp_prob(var, level, trange, details, fhr):
        return True

    # TMP min/max probs
    if fhr in TMP_MIN_HOURS and is_tmp_min_prob(var, level, trange, details, fhr):
        return True

    if fhr in TMP_MAX_HOURS and is_tmp_max_prob(var, level, trange, details, fhr):
        return True

    # GUST 50%
    if fhr in GUST_HOURS and is_gust_50pct(var, level, trange, details, fhr):
        return True

    # APCP 24h
    if fhr in APCP24_HOURS:
        if is_apcp_prob(var, level, trange, details, fhr, 24, APCP_24_48_THRESH):
            return True
        if is_apcp_percentile(var, level, trange, details, fhr, 24):
            return True

    # APCP 48h
    if fhr in APCP48_HOURS:
        if is_apcp_prob(var, level, trange, details, fhr, 48, APCP_24_48_THRESH):
            return True
        if is_apcp_percentile(var, level, trange, details, fhr, 48):
            return True

    # APCP 72h
    if fhr in APCP72_HOURS:
        if is_apcp_prob(var, level, trange, details, fhr, 72, APCP_72_THRESH):
            return True
        if is_apcp_percentile(var, level, trange, details, fhr, 72):
            return True

    return False


# ----------------- HTTP / idx helpers ----------------- #

def build_nbm_paths(fhr: int):
    base = f"blend.{RUN_DATE}/{CYCLE}/qmd/blend.t{CYCLE}z.qmd.f{fhr:03d}.{DOMAIN}.grib2"
    grib_url = f"{BASE_URL}/{base}"
    idx_url = f"{grib_url}.idx"
    return grib_url, idx_url


def fetch_idx(idx_url: str):
    try:
        r = requests.get(idx_url, timeout=15)
    except requests.exceptions.RequestException as e:
        print(f"[WARN] idx request error for {idx_url}: {e}")
        return None

    if r.status_code != 200:
        print(f"[WARN] idx HTTP {r.status_code} for {idx_url}")
        return None
    return r.text.splitlines()


def download_range_append(grib_url: str, start: int, end: int | None,
                          out_path: Path, retries: int = 3):
    """
    Download a byte range [start, end] (inclusive) from grib_url and append to out_path.
    If end is None, requests from start to EOF.
    Retries on transient network errors.
    """
    if end is None:
        range_header = f"bytes={start}-"
    else:
        range_header = f"bytes={start}-{end}"

    headers = {"Range": range_header}

    for attempt in range(1, retries + 1):
        try:
            with requests.get(grib_url, headers=headers, stream=True, timeout=30) as r:
                if r.status_code in (200, 206):
                    with open(out_path, "ab") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    return
                else:
                    print(f"[WARN] {r.status_code} on attempt {attempt} for {grib_url} {range_header}")
        except requests.exceptions.RequestException as e:
            print(f"[WARN] network error on attempt {attempt} for {range_header}: {e}")
        time.sleep(1)

    print(f"[ERROR] failed to download {range_header} after {retries} attempts")


# ----------------- Core per-forecast-hour processing ----------------- #

def process_forecast_hour(fhr: int):
    grib_url, idx_url = build_nbm_paths(fhr)
    print(f"\n[INFO] === f{fhr:03d} ===")
    print(f"[INFO] GRIB: {grib_url}")
    print(f"[INFO] IDX : {idx_url}")

    idx_lines = fetch_idx(idx_url)
    if idx_lines is None:
        print(f"[INFO] No idx for f{fhr:03d}; skipping.")
        return

    records = []
    for line in idx_lines:
        # Example: 1:0:d=2025112100:APTMP:2 m above ground:6 hour fcst:prob >310.928:...
        parts = line.split(":")
        if len(parts) < 6:
            continue
        try:
            rec_no = int(parts[0])
            start_byte = int(parts[1])
        except ValueError:
            continue
        var = parts[3]
        level = parts[4]
        trange = parts[5]
        details = ":".join(parts[6:]) if len(parts) > 6 else ""
        records.append(
            {
                "rec_no": rec_no,
                "start": start_byte,
                "var": var,
                "level": level,
                "trange": trange,
                "details": details,
            }
        )

    if not records:
        print(f"[INFO] No records parsed from idx for f{fhr:03d}; skipping.")
        return

    records.sort(key=lambda r: r["start"])

    kept = []
    for r in records:
        if match_record(r["var"], r["level"], r["trange"], r["details"], fhr):
            kept.append(r)

    if not kept:
        print(f"[INFO] No matching messages for f{fhr:03d}.")
        return

    out_path = OUT_DIR / f"nbm_t{CYCLE}z_qmd_f{fhr:03d}_{DOMAIN}_subset_grib2"
    if out_path.exists():
        out_path.unlink()

    print(f"[INFO] Downloading {len(kept)} messages into {out_path.name}")

    rec_index_by_no = {r["rec_no"]: i for i, r in enumerate(records)}

    for r in kept:
        i = rec_index_by_no[r["rec_no"]]
        start = r["start"]

        if i < len(records) - 1:
            next_start = records[i + 1]["start"]
            end = next_start - 1
        else:
            end = None  # to EOF

        print(f"  - rec {r['rec_no']}: {r['var']}:{r['level']}:{r['trange']}:{r['details'][:60]}...")
        download_range_append(grib_url, start, end, out_path)

    # Remove empty file if something went wrong
    if out_path.exists() and out_path.stat().st_size == 0:
        print(f"[INFO] {out_path.name} is empty; removing.")
        out_path.unlink()


# ----------------- CLI / main ----------------- #

def parse_args():
    parser = argparse.ArgumentParser(
        description="NBM QMD subset downloader via .idx + HTTP Range"
    )
    parser.add_argument(
        "--date",
        help="Run date in YYYYMMDD (default: auto-detect from current UTC)",
    )
    parser.add_argument(
        "--cycle",
        choices=["00", "06", "12", "18"],
        help="Cycle hour (00,06,12,18). Default: auto-detect.",
    )
    parser.add_argument(
        "--domain",
        default="co",
        help="NBM domain (default: co)",
    )
    parser.add_argument(
        "--hour",
        type=int,
        help="Optional single forecast hour to process (e.g., 156). If omitted, processes all needed hours.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Number of parallel workers for forecast hours (default: 4)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Decide run date & cycle
    if args.date and args.cycle:
        run_date = args.date
        cycle = args.cycle
        print(f"[INFO] Using manual run: {run_date} {cycle}Z")
    elif args.date or args.cycle:
        print("[ERROR] If you specify --date or --cycle, you must specify both.")
        sys.exit(1)
    else:
        run_date, cycle = auto_detect_run()
        print(f"[INFO] Auto-detected run: {run_date} {cycle}Z")

    setup_run_paths(run_date, cycle, args.domain)
    init_hour_sets(cycle)

    print(f"[INFO] Output directory: {OUT_DIR}")

    # Determine which hours to process
    if args.hour is not None:
        hours_to_process = [args.hour]
        print(f"[INFO] Single-hour mode: f{args.hour:03d}")
        clean_single_hour(args.hour)
        if args.hour not in ALL_HOURS:
            print(f"[WARN] f{args.hour:03d} is not in configured ALL_HOURS; "
                  f"matchers may find no records depending on field availability.")
    else:
        hours_to_process = ALL_HOURS
        print(f"[INFO] Total forecast hours to consider: {len(ALL_HOURS)}")
        # Full run: clean all existing subset files first
        clean_output_dir_full()

    # Threaded processing over forecast hours
    max_workers = max(1, args.max_workers)
    print(f"[INFO] Using {max_workers} worker(s)")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_forecast_hour, fhr): fhr
            for fhr in hours_to_process
        }

        for future in as_completed(futures):
            fhr = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"[ERROR] f{fhr:03d} raised exception (continuing): {e}")


if __name__ == "__main__":
    main()
