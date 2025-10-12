import re
import time
import logging
import pathlib
import requests
from logging.handlers import TimedRotatingFileHandler

MANUAL_SINGLE = False
MANUAL_URL = "https://noaa-nbm-para-pds.s3.amazonaws.com/blend.20251009/18/qmd/blend.t18z.qmd.f051.co.grib2"
MANUAL_OUTDIR = pathlib.Path("./nbm_download")

MANUAL_FIELDS = ["REFC"] # Not entirely sure what it means

DATE  = "20251011"      # UTC YYYYMMDD
CYCLE = "00"
F_START = 0
F_END = 48

MEMBERS = [f"m{n:03d}" for n in range(1, 6)]

FIELD_PATTERNS = [
    r":REFC:",                       # composite reflectivity (entire atmosphere)
    r":UGRD:10 m above ground:",     # U @ 10 m AGL
    r":VGRD:10 m above ground:",     # V @ 10 m AGL
]

# List of REGEX patterns to match .idx "desc" column (case-sensitive by default)
# Examples:
#   r":TMP:2 m above ground:"                  -> any 2 m temperature messages
#   r":TMP:2 m above ground:.*72 hour fcst"    -> 2 m temp with 72h fcst
#   r":TMP:2 m above ground:.*prob >305\.372:" -> specific probability threshold (escape dot)
#   r":APCP:surface:.*:6 hour acc"             -> 6-hr precip accumulation

MANUAL_PATTERNS = [
    # r":TMP:2 m above ground:51 hour fcst:prob >305\.372:",
    r":APTMP:2 m above ground:51 hour fcst:prob >310\.928:",
]

PRODUCTS = ["prslev"]

COMBINE_ONE_FILE = True

BUCKET = "https://nomads.ncep.noaa.gov"

OUTDIR = pathlib.Path("./NBM_download")
LOGDIR = pathlib.Path("./NBM_logs")
OUTDIR.mkdir(parents=True, exist_ok=True)
LOGDIR.mkdir(parents=True, exist_ok=True)

LOGFILE = LOGDIR / "NBM_pull.log"
LOG_LEVEL = logging.INFO
MAX_RETRIES = 5
TIMEOUT = 60
BACKOFF = 1.6

IDX_RE = re.compile(r"^\s*(\d+):(\d+):(.*)$")

logger = logging.getLogger("NBM")
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
        "User-Agent": "refs-puller/1.0",
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
    Example grib_url: https://.../refs.t12z.conus.pmmn.f10.grib2
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

    #output filename
    m = re.search(r"(NBM|)")