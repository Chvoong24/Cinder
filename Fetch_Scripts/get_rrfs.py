import os
import re
import time
import logging
import pathlib
import requests
from logging.handlers import TimedRotatingFileHandler
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta

# =========================
# User settings
# =========================

# ---- Manual single-file mode (OFF by default) ---------------------------------------------------------
MANUAL_SINGLE = False   # set True to use MANUAL_URL branch below (or use CLI --url)
MANUAL_URL    = "https://noaa-rrfs-pds.s3.amazonaws.com/rrfs_a/refs.20250921/12/enspost_timelag/refs.t12z.conus.pmmn.f13.grib2"      # e.g. "https://noaa-rrfs-pds.s3.amazonaws.com/rrfs_a/refs.20250921/12/enspost_timelag/refs.t12z.conus.pmmn.f10.grib2"
MANUAL_OUTDIR = pathlib.Path("./refs_download")  # where to save the compact file
MANUAL_FIELDS = ["REFC"]  # which fields to keep from manual file; supports: REFC, U10, V10
# -------------------------------------------------------------------------------------------------------

F_START = 0            # inclusive
F_END   = 36            # inclusive

# ---- Manual Date/Cycle Selection (manually change pull_date and cycle_run to DATE and CYCLE in MAIN) --

DATE  = "20251030"      # UTC YYYYMMDD
CYCLE = "00"            # '00'..'23'

# -------------------------------------------------------------------------------------------------------

# =========================
# Determine Model Run
# =========================

def determine_model_run():
    """Determine most recent NBM cycle based on current UTC time."""
    now = datetime.now(timezone.utc)

    hour = now.hour
    if hour >= 0 and hour < 6:
        cycle = 0

    elif hour >= 6 and hour < 12:
        cycle = 6

    elif hour >= 12 and hour < 18:
        cycle = 12

    else:
        cycle = 18

    ## Modify to include logic for rollback day if needed: NOT DONE YET!!!

    pull_date = now.strftime('%Y%m%d')
    cycle_str = f"{cycle:02d}"

    return pull_date, cycle_str

def rollback_day():
    """Fetch data from previous day in case of current day unavailability."""
    curr_day = datetime.now(timezone.utc)
    prev_day = curr_day - timedelta(days=1)
    pull_date = prev_day.strftime('%Y%m%d')

    return pull_date

def rollback_cycle(date_str, cycle_str):
    """Adjust cycle to previous cycle in case of unavailability."""
    cycle = int(cycle_str)

    if cycle == 0:
        # Roll back to previous day’s 18z
        new_date = rollback_day()
        new_cycle = "18"
    elif cycle == 6:
        new_date = date_str
        new_cycle = "00"
    elif cycle == 12:
        new_date = date_str
        new_cycle = "06"
    elif cycle == 18:
        new_date = date_str
        new_cycle = "12"
    else:
        new_date = date_str
        new_cycle = "18"

    return new_date, new_cycle


# Members to pull
#MEMBERS = [f"m{n:03d}" for n in range(1, 6)]  # m001..m005

# Fields to fetch (regex against .idx "desc" column)
FIELD_PATTERNS = [
    r":REFC:",                       # composite reflectivity (entire atmosphere)
    r":UGRD:10 m above ground:",     # U @ 10 m AGL
    r":VGRD:10 m above ground:",     # V @ 10 m AGL
]

# RRFS products to try (first match wins for each field)
PRODUCTS = ["prslev"]

BUCKET = "https://noaa-rrfs-pds.s3.amazonaws.com"

# Output locations
OUTDIR = pathlib.Path("./rrfs_download")
LOGDIR = pathlib.Path("./rrfs_logs")
OUTDIR.mkdir(parents=True, exist_ok=True)
LOGDIR.mkdir(parents=True, exist_ok=True)

# Logging
LOGFILE = LOGDIR / "rrfs_pull.log"
LOG_LEVEL = logging.INFO
MAX_RETRIES = 1
TIMEOUT = 60
BACKOFF = 1.6

# Regex to parse .idx lines: "msg#:offset:desc..."
IDX_RE = re.compile(r"^\s*(\d+):(\d+):(.*)$")

# =========================
# Logging setup
# =========================
logger = logging.getLogger("rrfs")
logger.setLevel(LOG_LEVEL)
logger.handlers.clear()

ch = logging.StreamHandler()
ch.setLevel(LOG_LEVEL)
ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(ch)

fh = TimedRotatingFileHandler(
    filename=str(LOGFILE),
    when="midnight",
    backupCount=7,
    encoding="utf-8",
)
fh.setLevel(LOG_LEVEL)
fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(fh)

# =========================
# HTTP helpers with retry
# =========================
def http_get(url, headers=None, stream=False):
    for a in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(url, headers=headers or {}, stream=stream, timeout=TIMEOUT)
            if r.status_code in (200, 206):
                return r
            logger.warning(f"GET {url} -> HTTP {r.status_code}")
        except Exception as e:
            logger.warning(f"GET {url} attempt {a} failed: {e}")
        time.sleep(BACKOFF ** a)
    raise RuntimeError(f"Failed GET {url}")

def http_head(url):
    for a in range(1, MAX_RETRIES + 1):
        try:
            r = requests.head(url, headers={"Accept-Encoding": "identity"}, timeout=TIMEOUT)
            if r.status_code == 200:
                return r
            logger.warning(f"HEAD {url} -> HTTP {r.status_code}")
        except Exception as e:
            logger.warning(f"HEAD {url} attempt {a} failed: {e}")
        time.sleep(BACKOFF ** a)
    raise RuntimeError(f"Failed HEAD {url}")

def http_get_range(url, start: int, end: int):
    """
    Ranged GET that forces identity (no gzip) and validates 206 + Content-Range.
    Returns a streaming response.
    """
    hdrs = {
        "Range": f"bytes={start}-{end}",
        "Accept-Encoding": "identity",
        "Connection": "close",
        "User-Agent": "rrfs-puller/1.0",
    }
    for a in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(url, headers=hdrs, stream=True, timeout=TIMEOUT)
            if r.status_code == 206 and r.headers.get("Content-Range"):
                return r
            logger.warning(
                f"RANGE GET {url} [{start}-{end}] -> HTTP {r.status_code} "
                f"(Content-Range={r.headers.get('Content-Range')!r}); retrying"
            )
        except Exception as e:
            logger.warning(f"RANGE GET {url} attempt {a} failed: {e}")
        time.sleep(BACKOFF ** a)
    raise RuntimeError(f"Failed RANGE GET {url} bytes={start}-{end}")

# ==================================
# Helper for Manual Request Only
# ==================================

def patterns_for(names: list[str]) -> list[str]:
    """
    Map simple names to the regex patterns you already use.
    Supported keys: 'REFC', 'U10', 'V10'
    """
    mapping = {
        "REFC": r":REFC:",
        "U10":  r":UGRD:10 m above ground:",
        "V10":  r":VGRD:10 m above ground:",
    }
    pats = []
    for n in names:
        key = n.strip().upper()
        if key in mapping:
            pats.append(mapping[key])
        else:
            raise ValueError(f"Unknown field name: {n} (choose from REFC, U10, V10)")
    return pats

# ==================================
# HTTP Request for Manual Mode Only
# ==================================

def fetch_single_url(grib_url: str, outdir: pathlib.Path, field_names: list[str]) -> pathlib.Path:
    """
    Download ONLY the requested fields from an arbitrary GRIB2 URL that has a .idx file.
    Example grib_url: https://.../rrfs.t12z.conus.pmmn.f10.grib2
    """
    outdir.mkdir(parents=True, exist_ok=True)
    idx_url = grib_url + ".idx"

    # Probe index + size
    logger.info(f"Manual: using index -> {idx_url}")
    idx_lines = http_get(idx_url).text.splitlines()
    entries = parse_idx(idx_lines)
    if not entries:
        raise RuntimeError("Manual: empty/invalid .idx")

    head = http_head(grib_url)
    total_size = int(head.headers.get("Content-Length", "0"))
    if total_size <= 0:
        raise RuntimeError("Manual: missing Content-Length on GRIB")

    # Select fields
    pats = patterns_for(field_names)
    downloads = []
    for pat in pats:
        rx = re.compile(pat)
        filtered = [e for e in entries if rx.search(e["desc"])]
        if not filtered:
            logger.warning(f"Manual: no matches for {pat} in index (skipping)")
            continue
        ranges = build_ranges(filtered, entries, total_size)
        downloads.extend((grib_url, start, end, desc) for (start, end, desc) in ranges)

    if not downloads:
        raise RuntimeError("Manual: no matching fields found in index")

    downloads.sort(key=lambda t: t[1])  # by start byte

    # Output filename
    # Try to infer date/cycle/fhr from the URL; fall back to a safe stem.
    m = re.search(r"(rrfs)\.t(\d{2})z.*?\.f(\d{2,3})", grib_url)
    if m:
        cy, fff = m.group(2), m.group(3)
        stem = f"manual_t{cy}z_f{int(fff):03d}_{'_'.join(field_names).lower()}"
    else:
        stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", pathlib.Path(grib_url).name) + f"_{'_'.join(field_names).lower()}"

    outfile = outdir / (stem + ".grib2")
    tmp = outfile.with_suffix(outfile.suffix + ".part")

    # Write compact GRIB
    logger.info(f"Manual: writing -> {outfile}")
    with open(tmp, "wb") as out:
        for _, start, end, desc in downloads:
            logger.info(f"  GET bytes={start}-{end} :: {desc}")
            r = http_get_range(grib_url, start, end)
            expected = end - start + 1
            got = 0
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    out.write(chunk)
                    got += len(chunk)
            if got != expected:
                raise RuntimeError(f"Manual: range mismatch [{start}-{end}] expected {expected}, got {got}")

    if outfile.exists():
        outfile.unlink(missing_ok=True)
    tmp.replace(outfile)
    sz_mb = outfile.stat().st_size / (1024*1024)
    logger.info(f"Manual: done. Size = {sz_mb:.1f} MB")
    return outfile


# =========================
# .idx parsing & ranges
# =========================
def parse_idx(text_lines):
    out = []
    for line in text_lines:
        m = IDX_RE.match(line)
        if m:
            out.append({"msg": int(m.group(1)), "offset": int(m.group(2)), "desc": m.group(3)})
    out.sort(key=lambda d: d["msg"])
    return out

def build_ranges(filtered_entries, full_entries, total_size):
    off = {e["msg"]: e["offset"] for e in full_entries}
    all_msgs = [e["msg"] for e in full_entries]
    ranges = []
    for e in filtered_entries:
        i = all_msgs.index(e["msg"])
        start = off[e["msg"]]
        end = (off[all_msgs[i + 1]] - 1) if i < len(all_msgs) - 1 else (total_size - 1)
        ranges.append((start, end, e["desc"]))
    return ranges

# =========================
# URL candidates (ENSEMBLE)
# =========================
def candidate_urls(product: str, date: str, cycle: str, fxx: int):
    """
    member: 'm001'..'m005'
    """
    fff = f"{fxx:03d}"
    if product == "prslev":
        return [
            f"{BUCKET}/rrfs_a/rrfs.{date}/{cycle}/rrfs.t{cycle}z.prslev.3km.f{fff}.conus.grib2"
        ]
    return []

def pick_grib_url(product: str, date: str, cycle: str, fxx: int):
    for url in candidate_urls(product, date, cycle, fxx):
        idx_url = f"{url}.idx"
        try:
            r = http_head(idx_url)
            if r.status_code == 200:
                return url, idx_url
        except Exception:
            continue
    return None, None

# =========================
# Writers
# =========================
def out_combined_path(date: str, cycle: str, fxx: int) -> pathlib.Path:
    return OUTDIR / f"refs.{date}t{cycle}z.f{fxx:03d}.conus.grib2"

"""
    RRFS doesn't probide members anymore so out_member_path is likely out of date.
"""
def out_member_path(date: str, cycle: str, fxx: int, member: str) -> pathlib.Path:
    return OUTDIR / f"rrfs.{date}t{cycle}z.f{fxx:03d}.{member}.grib2"

def fetch_hour(date: str, cycle: str, fxx: int):
    """
    Pull requested fields
    - write ONE combined file with all messages 
    """
    
    outfile = out_combined_path(date, cycle, fxx)
    if outfile.exists() and outfile.stat().st_size > 0:
        logger.info(f"{date} t{cycle}z f{fxx:03d} already exists -> {outfile} (skip)")
        return outfile
    tmp = outfile.with_suffix(outfile.suffix + ".part")
    # open once; append member slices into same file
    with open(tmp, "wb") as out:
        total_written = 0

        downloads = []

        # Find a viable product/URL for this member
        grib_url = idx_url = None
        entries = None
        total_size = None
        for product in PRODUCTS:
            grib_url, idx_url = pick_grib_url(product, date, cycle, fxx)
            if not grib_url:
                continue
            logger.info(f"{date} t{cycle}z f{fxx:03d} using index -> {idx_url}")
            idx_lines = http_get(idx_url).text.splitlines()
            entries = parse_idx(idx_lines)
            if not entries:
                logger.info(f"{date} t{cycle}z f{fxx:03d} empty/invalid index.")
                continue
            head = http_head(grib_url)
            total_size = int(head.headers.get("Content-Length", "0"))
            if total_size <= 0:
                logger.warning(f"{date} t{cycle}z f{fxx:03d} missing Content-Length.")
                continue
            # select fields for this member
            for pat in FIELD_PATTERNS:
                rx = re.compile(pat)
                filtered = [e for e in entries if rx.search(e["desc"])]
                if not filtered:
                    continue
                ranges = build_ranges(filtered, entries, total_size)
                for (start, end, desc) in ranges:
                    downloads.append((grib_url, start, end, desc))
            break  # we found a viable product for this member (or not)

        if not downloads:
            logger.info(f"{date} t{cycle}z f{fxx:03d} : no matching fields")

        # keep in ascending byte order
        downloads.sort(key=lambda t: t[1])

        # fetch ranges
        for grib_url, start, end, desc in downloads:
            logger.info(f" GET {grib_url} bytes={start}-{end} :: {desc}")
            r = http_get_range(grib_url, start, end)
            expected = end - start + 1
            got = 0
            for chunk in r.iter_content(chunk_size=1024*1024):
                if not chunk:
                    continue
                out.write(chunk)
                got += len(chunk)
                total_written += len(chunk)
            if got != expected:
                raise RuntimeError(
                    f"range size mismatch [{start}-{end}] expected {expected}, got {got}"
                )

    if outfile.exists():
        outfile.unlink(missing_ok=True)
    tmp.replace(outfile)
    sz_mb = outfile.stat().st_size / (1024*1024)
    logger.info(f"{date} t{cycle}z f{fxx:03d} combined ENS file Size={sz_mb:.1f} MB")
    return outfile

# =========================
# Main
# =========================
def main():
    # Manual single-file branch
    # if MANUAL_SINGLE and MANUAL_URL:
    #     try:
    #         fetch_single_url(MANUAL_URL, MANUAL_OUTDIR, MANUAL_FIELDS)
    #     except Exception as e:
    #         logger.exception(f"Manual fetch failed: {e}")
    #     return

    pull_date, cycle_str = determine_model_run()
    logger.info(f"==== RRFS ENS pull start :: {pull_date} t{cycle_str}z ====")

    # --- Check if current cycle is available ---
    test_url, test_idx = pick_grib_url(PRODUCTS[0], pull_date, cycle_str, 0)
    if not test_url:
        logger.warning(f"No data for {pull_date} t{cycle_str}z — rolling back")
        pull_date, cycle_str = rollback_cycle(pull_date, cycle_str)
        logger.info(f"Rolled back to {pull_date} t{cycle_str}z")

    # --- Download loop ---
    logger.info(f"==== RRFS pull start :: {pull_date} t{cycle_str}z f{F_START:03d}-{F_END:03d} ====")
    started = time.time()
    success = 0
    for fxx in range(F_START, F_END + 1):
        try:
            out = fetch_hour(pull_date, cycle_str, fxx)
            if out:
                success += 1
        except Exception as e:
            logger.exception(f"f{fxx:03d} failed: {e}")
    elapsed = time.time() - started
    logger.info(f"==== Finished: {success}/{F_END - F_START + 1} ok in {elapsed:.1f}s ====")
if __name__ == "__main__":
    main()
