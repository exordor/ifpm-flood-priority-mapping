"""Re-score an area from its existing criterion rasters (method ``rescore``).

Used for the background and frozen areas whose upstream chains are no longer run:

- zimbabwe (ported from bin/scenarios/run_zimbabwe_rainfall_exposure.py);
- peru_former (ported from bin/scenarios/run_peru_former_priority_scenarios.py). This area is
  frozen: the rerun goes under --out only, and ``check_pins`` compares the rescored priority
  raster and the frozen files with the sha256 pins in FROZEN_BASELINE.json.

The arithmetic is copied unchanged: float32 accumulation in config order, a criterion is
valid only where all its components are valid, the PIM only where all five criteria are
valid (no weight renormalization). Only the computed outputs are rebuilt; the static
tables (sub-criterion weights, screening summary), figures and run manifests are not. The rasters are written with the reference DEM profile
as the old scripts did, so an unchanged input gives a byte-identical output.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import geometry_mask

from . import io
from .config import Config
from .normalize import percentile_minmax


def ensure_unit_interval(data: np.ndarray) -> np.ndarray:
    """Keep a 0-1 layer as is (clipped); max-scale a positive absolute layer."""
    values = data[np.isfinite(data)]
    if values.size == 0:
        raise ValueError("empty criterion")
    if float(values.max()) <= 1.000001 and float(values.min()) >= -0.000001:
        return np.clip(data, 0.0, 1.0).astype("float32")
    if float(values.max()) <= 0.0:
        raise ValueError("non-positive criterion range")
    return np.clip(data / float(values.max()), 0.0, 1.0).astype("float32")


def write_profile_raster(path: Path, data: np.ndarray, profile: dict) -> None:
    """Float32 with the reference profile, NaN -> -9999 (bin/_lib/ifpm_tools.write_raster)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    out = dict(profile)
    out.update(driver="GTiff", dtype="float32", nodata=io.NODATA, compress="deflate",
               tiled=True, blockxsize=256, blockysize=256)
    with rasterio.open(path, "w", **out) as dst:
        dst.write(np.where(np.isfinite(data), data, io.NODATA).astype("float32"), 1)


def combine(components: dict, weights: dict, divide_by_total: bool) -> np.ndarray:
    """Weighted sum where every component is valid, clipped to 0-1."""
    first = next(iter(components.values()))
    numerator = np.zeros(first.shape, dtype="float32")
    common = np.ones(first.shape, dtype=bool)
    for name, weight in weights.items():
        layer = components[name]
        valid = np.isfinite(layer)
        numerator[valid] += layer[valid] * weight
        common &= valid
    out = np.full(first.shape, np.nan, dtype="float32")
    out[common] = numerator[common] / float(sum(weights.values())) if divide_by_total else numerator[common]
    return np.clip(out, 0.0, 1.0).astype("float32")


def score_common_support(criteria: dict, weights: dict):
    """PIM where all criteria are valid, plus available main weight and evidence count."""
    first = next(iter(criteria.values()))
    numerator = np.zeros(first.shape, dtype="float32")
    available = np.zeros(first.shape, dtype="float32")
    count = np.zeros(first.shape, dtype="uint8")
    common = np.ones(first.shape, dtype=bool)
    for name, weight in weights.items():
        valid = np.isfinite(criteria[name])
        numerator[valid] += criteria[name][valid] * weight
        available[valid] += weight
        count[valid] += 1
        common &= valid
    score = np.full(first.shape, np.nan, dtype="float32")
    score[common] = numerator[common]
    return score, available, count


def evidence_support_class(components: dict, criteria: dict, mask: np.ndarray) -> np.ndarray:
    """1 scored, 2 LS missing (channel mask), 3 K missing, 4 other gap; outside NaN."""
    support = np.zeros(mask.shape, dtype="uint8")
    support[mask] = 4
    k, ls, c = (np.isfinite(components[n]) for n in ("soil_k_factor", "ls_factor", "c_factor"))
    support[mask & ~k] = 3
    support[mask & k & c & ~ls] = 2
    common = mask.copy()
    for layer in criteria.values():
        common &= np.isfinite(layer)
    support[common] = 1
    return support


def write_csv(path: Path, rows: list[dict]) -> None:
    fields: list[str] = []
    for row in rows:
        fields += [key for key in row if key not in fields]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def stats(data: np.ndarray, keys=("min", "mean", "p50", "p80", "p95", "max")) -> dict:
    values = data[np.isfinite(data)]
    funcs = {"min": np.min, "mean": np.mean, "max": np.max,
             "p50": lambda v: np.percentile(v, 50), "p80": lambda v: np.percentile(v, 80),
             "p95": lambda v: np.percentile(v, 95)}
    return {"valid_cells": int(values.size), **{k: round(float(funcs[k](values)), 6) for k in keys}}


def grid_check(profile: dict, layers: dict, mask: np.ndarray | None) -> list[dict]:
    rows = []
    for name, data in layers.items():
        values = data[np.isfinite(data)]
        row = {"criterion": name, "grid_compatible": True, "crs": str(profile["crs"]),
               "width": profile["width"], "height": profile["height"], "valid_cells": int(values.size)}
        if mask is not None:  # zimbabwe: share of the boundary
            row["valid_fraction_of_boundary"] = round(float((mask & np.isfinite(data)).sum() / mask.sum()), 6)
            row["coverage_denominator"] = "boundary cells"
        else:
            row["valid_fraction"] = round(float(values.size / data.size), 6)
        row.update(min=round(float(values.min()), 6), mean=round(float(values.mean()), 6),
                   max=round(float(values.max()), 6))
        rows.append(row)
    return rows


def run_rescore(cfg: Config, name: str, out: Path, steps=None) -> None:
    ext = cfg.extent(name)
    root = cfg.root
    with rasterio.open(root / ext["reference"]) as ref:
        profile = ref.profile.copy()
    boundary = __import__("geopandas").read_file(root / ext["boundary"], layer=ext["boundary_layer"])
    mask = geometry_mask(boundary.to_crs(profile["crs"]).geometry,
                         out_shape=(profile["height"], profile["width"]),
                         transform=profile["transform"], invert=True)

    components = {}
    for comp, spec in ext["components"].items():
        data = io.read_band(root / spec["path"], profile)
        prep = spec.get("prepare")
        if prep == "unit":
            data = ensure_unit_interval(data)
        elif prep == "percentile":
            data = percentile_minmax(data, mask)[0]
        components[comp] = data

    out_dir = out / ext["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    rules = ext["rules"]
    for comp in rules.get("write_components", []):
        write_profile_raster(out_dir / "sediment_components" / f"{comp}_0_1.tif", components[comp], profile)
    criteria = {crit: combine(components, w, rules["divide_by_total"])
                for crit, w in cfg["weights"]["components"].items()}
    for crit, data in criteria.items():
        write_profile_raster(out_dir / "pim_criteria" / f"{crit}_0_1.tif", data, profile)

    weights = cfg["weights"]["main"]
    if round(sum(weights.values()), 10) != 1.0:
        raise ValueError(f"main weights sum to {sum(weights.values())}")
    common = mask.copy()
    for layer in criteria.values():
        common &= np.isfinite(layer)
    common_fraction = float(common.sum() / mask.sum())
    if common_fraction < rules.get("min_common_fraction", 0.0):
        raise RuntimeError(f"common support {common_fraction:.6f} below {rules['min_common_fraction']}")

    scenario = cfg["scenario_id"]
    score, available, count = score_common_support(criteria, weights)
    if rules["clip_score"]:
        score = np.clip(score, 0.0, 1.0)
    score[~mask] = np.nan
    write_profile_raster(out_dir / "scenarios" / f"priority_{scenario}.tif", score, profile)

    sediment_count = sum(np.isfinite(components[n]).astype("uint8")
                         for n in ("soil_k_factor", "ls_factor", "c_factor")).astype("float32")
    sediment_count[~mask] = np.nan
    write_profile_raster(out_dir / "sediment_component_count.tif", sediment_count, profile)

    weight_rows = [{"boundary_id": cfg["boundary_id"], "experiment_id": cfg["experiment_id"],
                    "scenario": scenario, "criterion": crit, "weight": round(w, 8),
                    "weight_source": cfg["weight_source"], "claim_level": "sensitivity_scenario"}
                   for crit, w in weights.items()]
    write_csv(out_dir / "scenario_weights.csv", weight_rows)

    summary = {"boundary_id": cfg["boundary_id"], "experiment_id": cfg["experiment_id"], "scenario": scenario}
    if rules.get("evidence_rasters"):  # peru_former
        for fname, data in (("available_main_weight", available.astype("float32")),
                            ("criteria_evidence_count", count.astype("float32"))):
            data[~mask] = np.nan
            write_profile_raster(out_dir / f"{fname}.tif", data, profile)
        support = evidence_support_class(components, criteria, mask)
        support_out = support.astype("float32")
        support_out[~mask] = np.nan
        write_profile_raster(out_dir / "evidence_support_class.tif", support_out, profile)
        scoreable = mask & np.isfinite(score)
        threshold = float(np.nanpercentile(score, 80))
        top20 = np.where(scoreable, score >= threshold, np.nan).astype("float32")
        write_profile_raster(out_dir / "scenarios" / f"top20_{scenario}.tif", top20, profile)
        fractions = {
            "scoreable_valid_fraction": round(common_fraction, 6),
            "full_five_criterion_fraction": round(common_fraction, 6),
            "incomplete_evidence_fraction": round(float((mask & ~scoreable).sum() / mask.sum()), 6),
            "ls_missing_fraction": round(float(np.sum(support == 2) / mask.sum()), 6),
            "k_missing_fraction": round(float(np.sum(support == 3) / mask.sum()), 6),
            "other_missing_fraction": round(float(np.sum(support == 4) / mask.sum()), 6),
        }
        summary.update(top20_threshold=threshold, **fractions, common_valid_fraction=round(common_fraction, 6),
                       **stats(score, ("min", "mean", "p50", "p95", "max")))
        write_csv(out_dir / "component_grid_check.csv", grid_check(profile, components, None))
        write_csv(out_dir / "pim_criteria_grid_check.csv", grid_check(profile, criteria, None))
    else:  # zimbabwe
        summary.update(common_valid_fraction=round(common_fraction, 6), **stats(score))
        write_csv(out_dir / "component_grid_check.csv", grid_check(profile, components, mask))
        write_csv(out_dir / "pim_criteria_grid_check.csv", grid_check(profile, criteria, mask))
    write_csv(out_dir / "scenario_priority_summary.csv", [summary])
    print(f"{cfg.area}/{name}: common support {common_fraction:.6f}; wrote {out_dir}", flush=True)
    if ext.get("frozen_baseline"):
        check_pins(cfg, name, out)


def check_pins(cfg: Config, name: str, out: Path) -> None:
    """Compare the rescored priority raster and the frozen files with FROZEN_BASELINE.json."""
    ext = cfg.extent(name)
    pins = json.loads((cfg.root / ext["frozen_baseline"]).read_text(encoding="utf-8"))["key_artifacts"]
    failures = []
    for key, pin in pins.items():
        current = cfg.root / pin["path"]
        if io.sha256_file(current) != pin["sha256"]:
            failures.append(f"frozen {key} changed: {pin['path']}")
    rescored = out / pins["priority"]["path"]
    status = "matches" if io.sha256_file(rescored) == pins["priority"]["sha256"] else "differs from"
    print(f"rescored priority {status} the frozen pin {pins['priority']['sha256'][:8]}", flush=True)
    if status != "matches":
        failures.append("rescored priority is not byte-identical to the pin")
    if failures:
        raise SystemExit("frozen-baseline pin check failed: " + "; ".join(failures))
