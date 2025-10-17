import os
import re
import time
import logging
import pathlib
import requests
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

# =========================
# User settings
# =========================

# ---- Manual single-file mode (OFF by default) ---------------------------------------------------------
MANUAL_SINGLE = False   # set True to use MANUAL_URL branch below (or use CLI --url)
MANUAL_URL    = "https://noaa-rrfs-pds.s3.amazonaws.com/rrfs_a/refs.20250921/12/enspost_timelag/refs.t12z.conus.pmmn.f13.grib2"      # e.g. "https://noaa-rrfs-pds.s3.amazonaws.com/rrfs_a/refs.20250921/12/enspost_timelag/refs.t12z.conus.pmmn.f10.grib2"
MANUAL_OUTDIR = pathlib.Path("./refs_download")  # where to save the compact file
MANUAL_FIELDS = ["REFC"]  # which fields to keep from manual file; supports: REFC, U10, V10
# -------------------------------------------------------------------------------------------------------

DATE  = "20250923"      # UTC YYYYMMDD
CYCLE = "00"            # '00'..'23'
F_START = 0            # inclusive
F_END   = 36            # inclusive

# Members to pull
MEMBERS = [f"m{n:03d}" for n in range(1, 6)]  # m001..m005

# Fields to fetch (regex against .idx "desc" column)
FIELD_PATTERNS = [
    r":REFC:",                       # composite reflectivity (entire atmosphere)
    r":UGRD:10 m above ground:",     # U @ 10 m AGL
    r":VGRD:10 m above ground:",     # V @ 10 m AGL
]

# RRFS products to try (first match wins for each field)
PRODUCTS = ["prslev"]

# One combined GRIB per f-hour? (True)  OR one compact GRIB per member? (False)
COMBINE_ONE_FILE = True

BUCKET = "https://noaa-rrfs-pds.s3.amazonaws.com"

# Output locations
OUTDIR = pathlib.Path("./rrfs_download")
LOGDIR = pathlib.Path("./rrfs_logs")
OUTDIR.mkdir(parents=True, exist_ok=True)
LOGDIR.mkdir(parents=True, exist_ok=True)

# Logging
LOGFILE = LOGDIR / "rrfs_pull.log"
LOG_LEVEL = logging.INFO
MAX_RETRIES = 5
TIMEOUT = 60
BACKOFF = 1.6

# Regex to parse .idx lines: "msg#:offset:desc..."
IDX_RE = re.compile(r"^\s*(\d+):(\d+):(.*)$")

# =========================
# Logging setup
# =========================
logger = logging.getLogger("refs")
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

    # Output filename
    # Try to infer date/cycle/fhr from the URL; fall back to a safe stem.
    m = re.search(r"(refs|rrfs)\.t(\d{2})z.*?\.f(\d{2,3})", grib_url)
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
def candidate_urls(product: str, date: str, cycle: str, fxx: int, member: str):
    """
    member: 'm001'..'m005'
    """
    fff = f"{fxx:03d}"
    if product == "prslev":
        return [
            f"{BUCKET}/rrfs_a/refs.{date}/{cycle}/{member}/rrfs.t{cycle}z.{member}.prslev.3km.f{fff}.conus.grib2"
        ]
    return []

def pick_grib_url(product: str, date: str, cycle: str, fxx: int, member: str):
    for url in candidate_urls(product, date, cycle, fxx, member):
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
    return OUTDIR / f"refs_{date}t{cycle}z_f{fxx:03d}_ens5.grib2"

def out_member_path(date: str, cycle: str, fxx: int, member: str) -> pathlib.Path:
    return OUTDIR / f"refs_{date}t{cycle}z_f{fxx:03d}_{member}.grib2"

def fetch_hour(date: str, cycle: str, fxx: int):
    """
    Pull requested fields from each ensemble member; either:
    - write ONE combined file with all members' messages (COMBINE_ONE_FILE=True), or
    - write one compact file per member (COMBINE_ONE_FILE=False).
    """
    if COMBINE_ONE_FILE:
        outfile = out_combined_path(date, cycle, fxx)
        if outfile.exists() and outfile.stat().st_size > 0:
            logger.info(f"{date} t{cycle}z f{fxx:03d} already exists -> {outfile} (skip)")
            return outfile
        tmp = outfile.with_suffix(outfile.suffix + ".part")
        # open once; append member slices into same file
        with open(tmp, "wb") as out:
            total_written = 0
            members_ok = 0

            for member in MEMBERS:
                downloads = []
                got_any = False

                # Find a viable product/URL for this member
                grib_url = idx_url = None
                entries = None
                total_size = None
                for product in PRODUCTS:
                    grib_url, idx_url = pick_grib_url(product, date, cycle, fxx, member)
                    if not grib_url:
                        continue
                    logger.info(f"{date} t{cycle}z f{fxx:03d} {member} using index -> {idx_url}")
                    idx_lines = http_get(idx_url).text.splitlines()
                    entries = parse_idx(idx_lines)
                    if not entries:
                        logger.info(f"{date} t{cycle}z f{fxx:03d} {member} empty/invalid index.")
                        continue
                    head = http_head(grib_url)
                    total_size = int(head.headers.get("Content-Length", "0"))
                    if total_size <= 0:
                        logger.warning(f"{date} t{cycle}z f{fxx:03d} {member} missing Content-Length.")
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
                    logger.info(f"{date} t{cycle}z f{fxx:03d} {member}: no matching fields yet (skip member).")
                    continue

                # keep in ascending byte order per member
                downloads.sort(key=lambda t: t[1])

                # fetch ranges
                for grib_url, start, end, desc in downloads:
                    logger.info(f"  {member} GET {grib_url} bytes={start}-{end} :: {desc}")
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
                            f"{member} range size mismatch [{start}-{end}] expected {expected}, got {got}"
                        )
                    got_any = True

                if got_any:
                    members_ok += 1

        if outfile.exists():
            outfile.unlink(missing_ok=True)
        tmp.replace(outfile)
        sz_mb = outfile.stat().st_size / (1024*1024)
        logger.info(f"{date} t{cycle}z f{fxx:03d} combined ENS file ({members_ok}/{len(MEMBERS)} members) Size={sz_mb:.1f} MB")
        return outfile

    else:
        # One compact file per member
        made = 0
        for member in MEMBERS:
            outfile = out_member_path(date, cycle, fxx, member)
            if outfile.exists() and outfile.stat().st_size > 0:
                logger.info(f"{date} t{cycle}z f{fxx:03d} {member} exists -> {outfile} (skip)")
                made += 1
                continue

            downloads = []
            grib_url = idx_url = None
            total_size = None
            for product in PRODUCTS:
                grib_url, idx_url = pick_grib_url(product, date, cycle, fxx, member)
                if not grib_url:
                    continue
                logger.info(f"{date} t{cycle}z f{fxx:03d} {member} using index -> {idx_url}")
                idx_lines = http_get(idx_url).text.splitlines()
                entries = parse_idx(idx_lines)
                if not entries:
                    logger.info(f"{date} t{cycle}z f{fxx:03d} {member} empty/invalid index.")
                    continue
                head = http_head(grib_url)
                total_size = int(head.headers.get("Content-Length", "0"))
                if total_size <= 0:
                    logger.warning(f"{date} t{cycle}z f{fxx:03d} {member} missing Content-Length.")
                    continue
                for pat in FIELD_PATTERNS:
                    rx = re.compile(pat)
                    filtered = [e for e in entries if rx.search(e["desc"])]
                    if not filtered:
                        continue
                    ranges = build_ranges(filtered, entries, total_size)
                    for (start, end, desc) in ranges:
                        downloads.append((grib_url, start, end, desc))
                break

            if not downloads:
                logger.info(f"{date} t{cycle}z f{fxx:03d} {member}: no matching fields yet (skip).")
                continue

            downloads.sort(key=lambda t: t[1])
            tmp = outfile.with_suffix(outfile.suffix + ".part")
            with open(tmp, "wb") as out:
                for grib_url, start, end, desc in downloads:
                    logger.info(f"  {member} GET {grib_url} bytes={start}-{end} :: {desc}")
                    r = http_get_range(grib_url, start, end)
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk:
                            out.write(chunk)
            if outfile.exists():
                outfile.unlink(missing_ok=True)
            tmp.replace(outfile)
            sz_mb = outfile.stat().st_size / (1024*1024)
            logger.info(f"{date} t{cycle}z f{fxx:03d} {member} done. Size = {sz_mb:.1f} MB")
            made += 1
        return made

# =========================
# Main
# =========================
def main():
    # Manual single-file branch
    if MANUAL_SINGLE and MANUAL_URL:
        try:
            fetch_single_url(MANUAL_URL, MANUAL_OUTDIR, MANUAL_FIELDS)
        except Exception as e:
            logger.exception(f"Manual fetch failed: {e}")
        return

    # Normal bulk ensemble pulling
    logger.info(f"==== REFS ENS pull start :: {DATE} t{CYCLE}z f{F_START:03d}-{F_END:03d} (combine={COMBINE_ONE_FILE}) ====")
    started = time.time()
    success = 0
    for fxx in range(F_START, F_END + 1):
        try:
            out = fetch_hour(DATE, CYCLE, fxx)
            if out:
                success += 1
        except Exception as e:
            logger.exception(f"f{fxx:03d} failed: {e}")
    elapsed = time.time() - started
    logger.info(f"==== Finished: {success}/{F_END - F_START + 1} ok in {elapsed:.1f}s ====")

if __name__ == "__main__":
    main()
