import re
import time
import logging
import pathlib
import requests
from logging.handlers import TimedRotatingFileHandler

# =========================
# User settings (MANUAL ONLY)
# =========================
MANUAL_URL = "https://noaa-nbm-para-pds.s3.amazonaws.com/blend.20250929/18/qmd/blend.t18z.qmd.f051.co.grib2"
OUTDIR     = pathlib.Path("./nbm_mulit_download")

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

# =========================
# Logging
# =========================
LOGDIR = pathlib.Path("./nbm_logs")
LOGDIR.mkdir(parents=True, exist_ok=True)
LOGFILE = LOGDIR / "nbm_manual_slice.log"
LOG_LEVEL = logging.INFO

logger = logging.getLogger("nbm_manual")
logger.setLevel(LOG_LEVEL)
logger.handlers.clear()

ch = logging.StreamHandler()
ch.setLevel(LOG_LEVEL)
ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(ch)

fh = TimedRotatingFileHandler(
    filename=str(LOGFILE), when="midnight", backupCount=7, encoding="utf-8"
)
fh.setLevel(LOG_LEVEL)
fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(fh)

# =========================
# HTTP (retry) helpers
# =========================
MAX_RETRIES = 5
TIMEOUT = 60
BACKOFF = 1.6

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
    hdrs = {
        "Range": f"bytes={start}-{end}",
        "Accept-Encoding": "identity",
        "Connection": "close",
        "User-Agent": "nbm-manual-slicer/1.0",
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

# =========================
# .idx parsing & range builder
# =========================
IDX_RE = re.compile(r"^\s*(\d+):(\d+):(.*)$")

def parse_idx(text_lines):
    """
    Return list of dicts: {'msg':int, 'offset':int, 'desc':str}, sorted by msg#
    """
    out = []
    for line in text_lines:
        m = IDX_RE.match(line)
        if m:
            out.append({"msg": int(m.group(1)), "offset": int(m.group(2)), "desc": m.group(3)})
    out.sort(key=lambda d: d["msg"])
    return out

def build_ranges(filtered_entries, full_entries, total_size):
    """
    For each selected message, compute [start,end] byte range to slice that message.
    """
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
# Core manual slicer
# =========================
def fetch_single_url(grib_url: str, outdir: pathlib.Path, idx_patterns: list[str]) -> pathlib.Path:
    """
    Slice a single NBM GRIB into a compact GRIB containing only messages whose
    .idx 'desc' matches ANY of the provided regex patterns.
    """
    if not idx_patterns:
        raise ValueError("No MANUAL_PATTERNS specified.")

    outdir.mkdir(parents=True, exist_ok=True)
    idx_url = grib_url + ".idx"

    logger.info(f"Using index -> {idx_url}")
    idx_lines = http_get(idx_url).text.splitlines()
    entries = parse_idx(idx_lines)
    if not entries:
        raise RuntimeError("Empty/invalid .idx")

    head = http_head(grib_url)
    total_size = int(head.headers.get("Content-Length", "0"))
    if total_size <= 0:
        raise RuntimeError("Missing Content-Length on GRIB")

    # Compile regexes
    regexes = [re.compile(p) for p in idx_patterns]

    # Find matches
    matched = []
    for e in entries:
        if any(rx.search(e["desc"]) for rx in regexes):
            matched.append(e)

    if not matched:
        logger.info("No index lines matched your MANUAL_PATTERNS. Nothing to do.")
        return None

    # Log which lines matched for transparency
    logger.info("Matched .idx lines:")
    for e in matched:
        logger.info(f"  msg={e['msg']:>4} off={e['offset']:>10} :: {e['desc']}")

    # Build byte ranges
    downloads = build_ranges(matched, entries, total_size)
    downloads.sort(key=lambda t: t[0])  # by start offset

    # Output filename (derive from URL and a hash of patterns)
    m = re.search(r"\.t(\d{2})z.*?\.f(\d{2,3})", grib_url)
    if m:
        cy, fff = m.group(1), int(m.group(2))
        stem = f"nbm_t{cy}z_f{fff:03d}_custom"
    else:
        # fallback to URL basename
        stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", pathlib.Path(grib_url).name) + "_custom"

    outfile = outdir / (stem + ".grib2")
    tmp = outfile.with_suffix(outfile.suffix + ".part")

    # Fetch & write compact GRIB
    logger.info(f"Writing -> {outfile}")
    with open(tmp, "wb") as out:
        for (start, end, desc) in downloads:
            logger.info(f"  GET bytes={start}-{end} :: {desc}")
            r = http_get_range(grib_url, start, end)
            expected = end - start + 1
            got = 0
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    out.write(chunk)
                    got += len(chunk)
            if got != expected:
                raise RuntimeError(
                    f"Range size mismatch [{start}-{end}] expected {expected}, got {got}"
                )

    if outfile.exists():
        outfile.unlink(missing_ok=True)
    tmp.replace(outfile)
    sz_mb = outfile.stat().st_size / (1024 * 1024)
    logger.info(f"Done. Size = {sz_mb:.1f} MB")
    return outfile

# =========================
# Main
# =========================
def main():
    try:
        t0 = time.time()
        out = fetch_single_url(MANUAL_URL, OUTDIR, MANUAL_PATTERNS)
        dt = time.time() - t0
        if out:
            logger.info(f"? Finished manual slice -> {out} in {dt:.1f}s")
        else:
            logger.info(f"? Nothing matched; finished in {dt:.1f}s")
    except Exception as e:
        logger.exception(f"Manual fetch failed: {e}")

if __name__ == "__main__":
    main()
