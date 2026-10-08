#!/usr/bin/env python3
"""Acquire Copernicus HRL raster windows for the Goslar focus extent via the CLMS API.

Downloads bbox-cropped GeoTIFFs of:
  - HRL VLCC Bare Soil After 2017-present (10 m, yearly)  -> data/raw/clms_hrl_bare_soil_goslar/
  - HRL VLCC Tree Cover Density 2018-present (10 m, yearly) -> data/raw/clms_hrl_tcd_goslar/

The CLMS portal prepares each request in a background job (queue cap 5); this
script submits, polls and downloads with a local state file so it can resume.
The private CLMS service key is read from the token file and never printed.

Usage:
  .venv/bin/python bin/acquire/pull_goslar_clms_hrl.py --submit
  .venv/bin/python bin/acquire/pull_goslar_clms_hrl.py --status
  .venv/bin/python bin/acquire/pull_goslar_clms_hrl.py --fetch
  .venv/bin/python bin/acquire/pull_goslar_clms_hrl.py --all --timeout-min 240
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import statistics
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TOKEN = ROOT / "data/tmp/clms_token_ifpm.json"
STATE = ROOT / "data/tmp/clms_hrl_tasks.json"
API = "https://land.copernicus.eu/api"

BBOX = [51.95, 10.5, 51.8, 10.3]  # [max.lat, max.lon, min.lat, min.lon], padded focus extent
FOCUS_EXTENT = [51.9089, 10.4194, 51.8544, 10.3646]  # [max.lat, max.lon, min.lat, min.lon]

# (label, DatasetID, DatasetDownloadInformationID, output dir, years)
PRODUCTS = [
    (
        "bare_soil",
        "bb6a2f6a0eca45b1b46ce83364fd6b6b",
        "c8f6d613-6e80-43ef-a361-12e660004939",
        ROOT / "data/raw/clms_hrl_bare_soil_goslar",
        [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
    ),
    (
        "tcd",
        "f954d06dfb5442b4910f0ccea9070917",
        "b119df47-079d-4d28-bda5-0748477a1053",
        ROOT / "data/raw/clms_hrl_tcd_goslar",
        [2018, 2024],
    ),
]


def ms(year: int) -> tuple[int, int]:
    start = dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc)
    end = dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def access_token(token_path: Path) -> str:
    d = json.load(open(token_path))

    def b64url(b: bytes) -> str:
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

    header = b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    now = int(time.time())
    payload = b64url(
        json.dumps(
            {
                "iss": d["client_id"],
                "sub": d["user_id"],
                "aud": d["token_uri"],
                "iat": now,
                "exp": now + 3600,
            }
        ).encode()
    )
    key = Path("/tmp/clms_hrl_sig_key.pem")
    key.write_text(d["private_key"])
    key.chmod(0o600)
    sig = subprocess.run(
        ["openssl", "dgst", "-sha256", "-sign", str(key)],
        input=f"{header}.{payload}".encode(),
        capture_output=True,
        check=True,
    ).stdout
    assertion = f"{header}.{payload}.{b64url(sig)}"
    body = urllib.parse.urlencode(
        {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        }
    ).encode()
    req = urllib.request.Request(d["token_uri"], data=body, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["access_token"]


def api_get(path: str, tok: str, params: dict | None = None) -> dict:
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "Authorization": f"Bearer {tok}"}
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def submit(token_path: Path, state_path: Path) -> None:
    state = json.load(open(state_path)) if state_path.exists() else {}
    tok = access_token(token_path)
    jobs = []
    for label, uid, dl_id, _dir, years in PRODUCTS:
        for year in years:
            if f"{label}_{year}" in state:
                continue
            s, e = ms(year)
            jobs.append(
                {
                    "label": f"{label}_{year}",
                    "DatasetID": uid,
                    "DatasetDownloadInformationID": dl_id,
                    "BoundingBox": BBOX,
                    "TemporalFilter": {"StartDate": s, "EndDate": e},
                    "OutputFormat": "Geotiff",
                    "OutputGCS": "EPSG:3035",
                }
            )
    for i in range(0, len(jobs), 4):
        batch = jobs[i : i + 4]
        payload = {"Datasets": [{k: v for k, v in x.items() if k != "label"} for x in batch]}
        req = urllib.request.Request(
            API + "/@datarequest_post",
            data=json.dumps(payload).encode(),
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {tok}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.load(r)
        except urllib.error.HTTPError as e:
            print(f"batch failed {[x['label'] for x in batch]}: {e.code} {e.read().decode()[:200]}")
            continue
        if resp.get("ErrorTaskIds"):
            print("error tasks:", resp["ErrorTaskIds"])
        for task in resp.get("TaskIds", []):
            tid = task["TaskID"]
            labels = [x["label"] for x in batch]
            state[tid] = {"label": labels, "status": "queued"}
            print("submitted", tid, labels)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=1))


def fetch(token_path: Path, state_path: Path) -> None:
    state = json.load(open(state_path)) if state_path.exists() else {}
    tok = access_token(token_path)
    ok = api_get("/@datarequest_search", tok, {"status": "Finished_ok"})
    for tid, info in ok.items():
        if tid not in state or state[tid].get("status") == "downloaded":
            continue
        labels = state[tid]["label"]

        def walk(o):
            found = []

            def rec(x):
                if isinstance(x, dict):
                    for v in x.values():
                        rec(v)
                elif isinstance(x, list):
                    for e in x:
                        rec(e)
                elif isinstance(x, str) and x.startswith("http"):
                    found.append(x)

            rec(o)
            return found

        datasets = info.get("Datasets") or []
        urls = [walk(ds) for ds in datasets]
        if not urls or not any(urls):
            print("no download url in finished task", tid)
            continue
        for i, label in enumerate(labels):
            entry_urls = urls[i] if i < len(urls) else []
            url = entry_urls[0] if entry_urls else urls[0][0]
            for _label, _uid, _dl, out_dir, years in PRODUCTS:
                if label.startswith(_label):
                    year = int(label.split("_")[-1])
                    dest = out_dir / str(year)
                    dest.mkdir(parents=True, exist_ok=True)
                    fname = f"{label}.zip"
                    target = dest / fname
                    if target.exists() and target.stat().st_size > 0:
                        print("exists, skip", target)
                        continue
                    print("downloading", url, "->", target)
                    req = urllib.request.Request(
                        url, headers={"Authorization": f"Bearer {tok}"}
                    )
                    with urllib.request.urlopen(req, timeout=1800) as r, open(target, "wb") as fh:
                        while True:
                            chunk = r.read(1 << 20)
                            if not chunk:
                                break
                            fh.write(chunk)
                    state[tid]["status"] = "downloaded"
                    state_path.write_text(json.dumps(state, indent=1))
                    print("saved", target, target.stat().st_size, "bytes")


def status(token_path: Path) -> None:
    tok = access_token(token_path)
    for st in ["In_progress", "Finished_ok"]:
        res = api_get("/@datarequest_search", tok, {"status": st})
        print(st, list(res.keys()))


def qa(out_dir: Path, product_label: str) -> dict:
    """Unzip downloaded windows and write coverage/range diagnostics."""
    try:
        import rasterio
        from rasterio.warp import transform_bounds
    except ImportError:
        print("rasterio not available; skip qa")
        return {}
    summary = {}
    for year_dir in sorted(out_dir.iterdir()):
        if not year_dir.is_dir():
            continue
        for zp in sorted(year_dir.glob("*.zip")):
            with zipfile.ZipFile(zp) as zf:
                tifs = [n for n in zf.namelist() if n.lower().endswith((".tif", ".tiff"))]
                zf.extractall(year_dir)
                tif = year_dir / tifs[0]
                with rasterio.open(tif) as src:
                    bbox_4326 = transform_bounds(src.crs, "EPSG:4326", *src.bounds)
                    inside = (
                        bbox_4326[0] <= FOCUS_EXTENT[3]
                        and bbox_4326[2] >= FOCUS_EXTENT[1]
                        and bbox_4326[1] <= FOCUS_EXTENT[0]
                        and bbox_4326[3] >= FOCUS_EXTENT[2]
                    )
                    arr = src.read(1)
                    nd = src.nodata
                    valid = arr[arr != nd] if nd is not None else arr
                    frac_nodata = float((arr == nd).mean()) if nd is not None else 0.0
                    summary[str(year_dir.name)] = {
                        "file": str(tif.relative_to(out_dir)),
                        "crs": str(src.crs),
                        "size": [src.width, src.height],
                        "res": list(src.res),
                        "bbox_4326": [round(v, 5) for v in bbox_4326],
                        "covers_focus_extent": inside,
                        "nodata_fraction": round(frac_nodata, 4),
                        "valid_min": float(valid.min()) if valid.size else None,
                        "valid_max": float(valid.max()) if valid.size else None,
                        "valid_mean": round(float(valid.mean()), 3) if valid.size else None,
                    }
    diag = out_dir / "hrl_diagnostics.json"
    diag.write_text(json.dumps({"product": product_label, "summary": summary}, indent=1))
    print(json.dumps(summary, indent=1))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default=str(DEFAULT_TOKEN))
    ap.add_argument("--state", default=str(STATE))
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--timeout-min", type=int, default=240)
    args = ap.parse_args()
    tokp = Path(args.token)
    if not tokp.exists():
        raise SystemExit(f"token file not found: {tokp}")
    if args.status:
        status(tokp)
        return
    if args.submit or args.all:
        submit(tokp, Path(args.state))
    if args.fetch or args.all:
        fetch(tokp, Path(args.state))
    if args.qa:
        for label, _uid, _dl, out_dir, _years in PRODUCTS:
            qa(out_dir, label)


if __name__ == "__main__":
    main()
