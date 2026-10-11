#!/usr/bin/env python3
"""Record and check a regression baseline of the key outputs per study area.

Used to verify the config-driven chain (refactor phase 2-3) against the current outputs.
Run from the workspace root with the project environment:

    .venv/bin/python tools/verify_baseline.py snapshot > baseline.json
    .venv/bin/python tools/verify_baseline.py compare baseline.json <new_root>

`snapshot` records sha256 for each key file and, for GeoTIFFs, CRS, transform, shape,
NaN count and min/max/mean. `compare` checks files under <new_root> (where the new chain
wrote its outputs; never the current outputs). A file passes when its sha256 is equal,
or for GeoTIFFs when grid and NaN mask are identical and the cell-wise difference to the
current file is at most TOL. Exit code 1 if anything fails.
"""
import hashlib, json, sys
from pathlib import Path
import numpy as np, rasterio

KEY = {
 "secocha": ["outputs/secocha_pim_chain/criteria_stack/criteria/*.tif",
             "outputs/secocha_pim_chain/priority_scenarios/pim_criteria/*.tif",
             "outputs/secocha_pim_chain/priority_scenarios/scenarios/*.tif",
             "outputs/secocha_pim_chain/priority_scenarios/*.tif",
             "outputs/secocha_pim_chain/quality_assurance/*.json"],
 "goslar": ["outputs/goslar_pim_chain/criteria_stack/criteria/*.tif",
            "outputs/goslar_pim_chain/priority_scenarios/**/*.tif",
            "outputs/goslar_abzucht_diagnostics/fixed_scale/chain/priority_scenarios/**/*.tif",
            "outputs/goslar_abzucht_diagnostics/fixed_scale/frozen_normalization.json",
            "outputs/goslar_multiriver_full_extent/fixed_scale/chain/priority_scenarios/**/*.tif",
            "outputs/goslar_multiriver_full_extent/fixed_scale/pim_flood_*.tif",
            "outputs/goslar_multiriver_full_extent/fixed_scale/*.csv"],
 "peru_former": ["outputs/peru_former_pim_chain/criteria_stack/criteria/*.tif",
                 "outputs/peru_former_pim_chain/priority_scenarios/**/*.tif"],
 "zimbabwe": ["outputs/zimbabwe_pim_scenarios/rainfall_exposure/**/*.tif",
              "outputs/zimbabwe_pim_scenarios/rainfall_exposure/*.csv"],
}
TOL = 1e-6  # 0-1 criteria / PIM

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def describe(p):
    d = {"sha256": sha(p)}
    if p.suffix == ".tif":
        with rasterio.open(p) as ds:
            a = ds.read(1, masked=True).astype("float64").filled(np.nan)
            d.update(crs=str(ds.crs), transform=list(ds.transform)[:6], shape=list(a.shape),
                     nan=int(np.isnan(a).sum()), min=float(np.nanmin(a)), max=float(np.nanmax(a)),
                     mean=float(np.nanmean(a)))
    return d

def snapshot(root):
    out = {}
    for area, pats in KEY.items():
        for pat in pats:
            for p in sorted(root.glob(pat)):
                out[str(p.relative_to(root))] = dict(area=area, **describe(p))
    return out

def compare(base, root):
    bad = 0
    for rel, b in base.items():
        p = root / rel
        if not p.exists(): print("MISSING", rel); bad += 1; continue
        if sha(p) == b["sha256"]: continue
        if p.suffix != ".tif": print("DIFF", rel); bad += 1; continue
        n = describe(p)
        same_grid = all(n[k] == b[k] for k in ("crs", "transform", "shape", "nan"))
        close = all(abs(n[k] - b[k]) <= TOL for k in ("min", "max", "mean"))
        if same_grid and Path(rel).exists():  # cell-wise against the untouched old file
            with rasterio.open(rel) as o, rasterio.open(p) as q:
                x = o.read(1, masked=True).astype("float64").filled(np.nan)
                y = q.read(1, masked=True).astype("float64").filled(np.nan)
            close = bool(np.array_equal(np.isnan(x), np.isnan(y)) and np.nanmax(np.abs(x - y)) <= TOL)
        print(("TOL-OK " if same_grid and close else "FAIL   ") + rel)
        bad += not (same_grid and close)
    return bad

if __name__ == "__main__":
    if sys.argv[1] == "snapshot":
        json.dump(snapshot(Path(".")), sys.stdout, indent=1)
    else:
        sys.exit(1 if compare(json.load(open(sys.argv[2])), Path(sys.argv[3])) else 0)
