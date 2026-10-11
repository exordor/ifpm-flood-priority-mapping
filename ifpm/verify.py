"""Regression check: compare a rerun's outputs with the current outputs in the workspace.

For every file matched by the extent's ``verify`` globs (configs/<area>.yaml) under the
workspace root, the file at the same relative path under the rerun root is compared:

- any file: pass when the sha256 is equal;
- GeoTIFF: else pass when CRS, transform, shape and NoData mask are identical and the
  cell-wise difference is at most TOL (same rule as tools/verify_baseline.py);
- CSV: else pass when the rows match in any order (some row orders follow file-system
  glob order) with numbers equal within TOL;
- JSON: else pass when the parsed content matches with numbers equal within TOL.

Files listed under the extent's ``known_differences`` that fail only on a raster value
difference no larger than its ``max_diff`` get the status KNOWN and count as pass.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

from .config import ROOT, Config
from .io import sha256_file

TOL = 1e-6


def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _cells_equal(a: str, b: str) -> bool:
    if a == b:
        return True
    x, y = _number(a), _number(b)
    if x is None or y is None:
        return False
    if math.isnan(x) and math.isnan(y):
        return True
    return abs(x - y) <= TOL


def _json_equal(a, b) -> bool:
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_json_equal(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_json_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return _cells_equal(str(a), str(b))
    return a == b


def compare_tif(old: Path, new: Path, tol: float = TOL) -> tuple[bool, str]:
    import rasterio
    with rasterio.open(old) as o, rasterio.open(new) as n:
        if (o.crs, o.transform, o.shape) != (n.crs, n.transform, n.shape):
            return False, "grid differs"
        x = o.read(1, masked=True).astype("float64").filled(np.nan)
        y = n.read(1, masked=True).astype("float64").filled(np.nan)
    if not np.array_equal(np.isnan(x), np.isnan(y)):
        return False, f"NoData mask differs ({int((np.isnan(x) != np.isnan(y)).sum())} cells)"
    if np.isnan(x).all():
        return True, "all NoData"
    diff = float(np.nanmax(np.abs(x - y)))
    return diff <= tol, f"max diff {diff:.2e}"


def compare_csv(old: Path, new: Path) -> tuple[bool, str]:
    def rows(path):
        with path.open(newline="", encoding="utf-8") as f:
            return list(csv.reader(f))
    a, b = rows(old), rows(new)
    if not a or not b or a[0] != b[0]:
        return False, "header differs"
    if len(a) != len(b):
        return False, f"{len(a) - 1} vs {len(b) - 1} rows"
    remaining = sorted(b[1:])
    for row in sorted(a[1:]):
        match = next((i for i, other in enumerate(remaining) if len(other) == len(row)
                      and all(_cells_equal(p, q) for p, q in zip(row, other))), None)
        if match is None:
            return False, "row not found: " + ",".join(row)[:80]
        remaining.pop(match)
    return True, "rows equal (order-insensitive)"


def compare_json(old: Path, new: Path) -> tuple[bool, str]:
    a = json.loads(old.read_text(encoding="utf-8"))
    b = json.loads(new.read_text(encoding="utf-8"))
    equal = _json_equal(a, b)
    return equal, "content equal" if equal else "content differs"


def compare_file(old: Path, new: Path, known: dict | None = None) -> tuple[str, str]:
    """('PASS'|'TOL'|'KNOWN'|'FAIL'|'MISSING', detail) for one file pair.

    ``known`` ({reason, max_diff}) marks an accepted raster difference for this file.
    """
    if not new.exists():
        return "MISSING", "not in rerun"
    if sha256_file(old) == sha256_file(new):
        return "PASS", "identical"
    compare = {".tif": compare_tif, ".csv": compare_csv, ".json": compare_json}.get(old.suffix)
    if compare is None:
        return "FAIL", "bytes differ"
    ok, detail = compare(old, new)
    if ok:
        return "TOL", detail
    if known and old.suffix == ".tif" and detail.startswith("max diff"):
        if compare_tif(old, new, float(known["max_diff"]))[0]:
            return "KNOWN", f"{detail}; {known['reason']}"
    return "FAIL", detail


def verify(area: str, out: Path, extents: list[str] | None = None, root: Path = ROOT) -> bool:
    """Print a pass/fail table for the area's verify globs; True when everything passes."""
    cfg = Config(area)
    rows = []
    for name in extents or cfg.extents:
        extent = cfg.extent(name)
        accepted = extent.get("known_differences") or {}
        known_files = set(accepted.get("files", []))
        for pattern in extent.get("verify", []):
            matches = sorted(root.glob(pattern))
            if not matches:
                rows.append((name, pattern, "MISSING", "no current file matches"))
            for old in matches:
                rel = old.relative_to(root)
                known = accepted if str(rel) in known_files else None
                status, detail = compare_file(old, out / rel, known)
                rows.append((name, str(rel), status, detail))
    width = max(len(r[1]) for r in rows) if rows else 10
    for extent, rel, status, detail in rows:
        print(f"{status:<8} {extent:<14} {rel:<{width}}  {detail}")
    failed = [r for r in rows if r[2] in ("FAIL", "MISSING")]
    known = sum(r[2] == "KNOWN" for r in rows)
    print(f"\n{len(rows) - len(failed)}/{len(rows)} files pass "
          f"(identical or within {TOL:g}; {known} known differences); "
          f"{len(failed)} fail. Rerun root: {out}")
    return not failed
