#!/usr/bin/env python3
"""Compute an empirical USLE/RUSLE R-factor (EI30) from ERA5 hourly precipitation via open-meteo,
to arbitrate the two incompatible literature R-families for the V1 catchment.

Local TOOLING script. After the exploratory method comparison (IFPM-081) split the R-factor
literature into a HIGH-R family (~1400-3700, incl. the Zimbabwe-native Elwell relation) and a
LOW-R family (~240-320, Hurni/Epworth), this script computes an EMPIRICAL R from hourly rainfall
to see which family the data supports. ERA5 hourly (open-meteo, no auth) is used because GPM IMERG
(half-hourly) requires a NASA Earthdata account that is unavailable; CHIRPS daily is not
storm-resolved and cannot yield EI30.

ALGORITHM (Wischmeier-Smith / RUSLE, verified from standard references):
  1. Split the hourly series into storms: a storm is a run of wet hours separated from the next by
     >= STORM_GAP_HOURS of dry weather. Only storms with total depth >= EROSIVE_DEPTH_MM are
     erosive (USLE threshold ~12.7 mm; also accepted: >=6mm if intensity high).
  2. Unit kinetic energy per storm (two forms, both reported):
       Wischmeier-Smith SI:  e = 0.119 + 0.0873 * log10(i)   [MJ ha-1 mm-1], capped at i=76 mm/h
       Brown-Foster (RUSLE): e = 0.29 * (1 - 0.72*exp(-0.05*i)) [MJ ha-1 mm-1]
     where i = hourly intensity (mm/h). e is set to 0 where i == 0.
  3. Storm energy E = sum over hours of (e_i * depth_i)  [MJ/ha].
  4. I30 (max 30-min intensity). ERA5 is hourly, so the true I30 is unobservable; approximate it as
     the max single-hour intensity (I60, a LOWER BOUND on I30). Report both the I60-based R and,
     for reference, an I30 estimate = I60 * 1.1 (a rough convective-storm upscaling, clearly
     labelled as an assumption).
  5. Storm EI30 = E * I30_est.
  6. Annual R = sum of erosive-storm EI30 over a year; report the multi-year mean.

CAVEAT: hourly resolution makes the computed R a LOWER BOUND on the true 30-min EI30 R. This is
acceptable for arbitrating a 6x family gap (300 vs 2000); it is NOT a validated quantitative R.

Usage (from workspace root):
    .venv/bin/python bin/compute_era5_empirical_rfactor.py
"""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/raw/era5_hourly_precip_v1_rfactor"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DIAG_OUT = ROOT / "outputs/v1_usle_soil_loss/rfactor_empirical_era5"
DIAG_OUT.mkdir(parents=True, exist_ok=True)

# V1 catchment: a small grid of points across the catchment to get a spatial mean.
V1_POINTS = [
    ("NW", 28.70, -20.85),
    ("N",  28.95, -20.85),
    ("NE", 29.20, -20.85),
    ("C",  28.95, -20.50),
    ("SW", 28.70, -20.20),
    ("SE", 29.20, -20.20),
    ("S",  28.95, -20.20),
]
YEAR_RANGE = (2018, 2023)  # 6 years for a multi-year mean R

# Algorithm parameters (USLE/RUSLE standard, verified from literature)
STORM_GAP_HOURS = 6          # dry hours that separate storms (USLE convention)
EROSIVE_DEPTH_MM = 12.0      # a storm is erosive if total depth >= this (USLE ~12.7mm)
KE_INTENSITY_CAP = 76.0      # cap unit KE above this intensity (mm/h, Wischmeier-Smith)
I30_UPSCALE = 1.1            # rough I30 = I60 * factor, to bracket the hourly-resolution gap


def unit_ke_wischmeier(i_mmh: np.ndarray) -> np.ndarray:
    """Wischmeier-Smith SI unit kinetic energy: e = 0.119 + 0.0873*log10(i), capped, 0 where i=0."""
    i = np.where(i_mmh <= 0, np.nan, np.minimum(i_mmh, KE_INTENSITY_CAP))
    e = 0.119 + 0.0873 * np.log10(i)
    return np.where(i_mmh <= 0, 0.0, e)


def unit_ke_brown_foster(i_mmh: np.ndarray) -> np.ndarray:
    """Brown-Foster (RUSLE) unit kinetic energy: e = 0.29*(1 - 0.72*exp(-0.05*i)), 0 where i=0."""
    e = 0.29 * (1.0 - 0.72 * np.exp(-0.05 * i_mmh))
    return np.where(i_mmh <= 0, 0.0, e)


def fetch_era5_hourly(lon: float, lat: float, y0: int, y1: int) -> tuple[list[str], np.ndarray]:
    """Fetch ERA5 hourly precipitation for one point via open-meteo (no auth)."""
    url = (
        f"https://archive-api.open-meteo.com/v1/era5?"
        f"latitude={lat}&longitude={lon}"
        f"&start_date={y0}-01-01&end_date={y1}-12-31"
        f"&hourly=precipitation"
    )
    with urllib.request.urlopen(url, timeout=120) as r:
        d = json.load(r)
    times = d["hourly"]["time"]
    precip = np.array(d["hourly"]["precipitation"], dtype=float)
    precip[~np.isfinite(precip)] = 0.0
    return times, precip


def compute_r_for_series(precip: np.ndarray, times: list[str], ke_fn) -> dict:
    """Split into storms, compute erosive-storm EI30, sum per year, return annual R stats."""
    n = len(precip)
    # --- 1. storm segmentation ---
    is_wet = precip > 0
    storms: list[tuple[int, int]] = []
    i = 0
    while i < n:
        if is_wet[i]:
            j = i
            gap = 0
            while j < n:
                if is_wet[j]:
                    j += 1
                    gap = 0
                else:
                    gap += 1
                    j += 1
                    if gap >= STORM_GAP_HOURS:
                        break
            end = j - gap  # last wet hour
            storms.append((i, end + 1))
            i = j
        else:
            i += 1

    # --- 2-5. per-storm E, I30(≈I60), EI30 ---
    year_r: dict[int, float] = {}
    year_r_i30est: dict[int, float] = {}
    n_erosive = 0
    for (s, e) in storms:
        seg = precip[s:e]
        depth = float(seg.sum())
        if depth < EROSIVE_DEPTH_MM:
            continue
        n_erosive += 1
        i_mmh = seg  # hourly intensity = hourly depth (mm/h over 1h)
        unit_e = ke_fn(i_mmh)
        storm_E = float(np.sum(unit_e * seg))  # MJ/ha
        i60 = float(seg.max())                  # mm/h, lower bound on I30
        i30_est = i60 * I30_UPSCALE
        ei30_i60 = storm_E * i60
        ei30_i30est = storm_E * i30_est
        # assign storm to its year (by start hour)
        yr = int(times[s][:4])
        year_r[yr] = year_r.get(yr, 0.0) + ei30_i60
        year_r_i30est[yr] = year_r_i30est.get(yr, 0.0) + ei30_i30est

    rs = list(year_r.values())
    rs_est = list(year_r_i30est.values())
    return {
        "n_storms_total": len(storms),
        "n_erosive_storms": n_erosive,
        "annual_R_I60lowerbound": year_r,
        "annual_R_I30est": year_r_i30est,
        "mean_annual_R_I60lowerbound": float(np.mean(rs)) if rs else 0.0,
        "mean_annual_R_I30est": float(np.mean(rs_est)) if rs_est else 0.0,
    }


def main() -> None:
    print(f"Fetching ERA5 hourly precipitation {YEAR_RANGE[0]}-{YEAR_RANGE[1]} for {len(V1_POINTS)} V1 points ...")
    all_results = []
    for pid, lon, lat in V1_POINTS:
        times, precip = fetch_era5_hourly(lon, lat, *YEAR_RANGE)
        total = float(np.nansum(precip))
        # two KE forms
        r_ws = compute_r_for_series(precip, times, unit_ke_wischmeier)
        r_bf = compute_r_for_series(precip, times, unit_ke_brown_foster)
        rec = {
            "point_id": pid, "lon": lon, "lat": lat,
            "total_precip_mm": round(total, 1),
            "wischmeier": r_ws,
            "brown_foster": r_bf,
        }
        all_results.append(rec)
        print(f"  {pid} ({lon:.2f},{lat:.2f}): P={total:.0f}mm; "
              f"R(Wisch,I60)={r_ws['mean_annual_R_I60lowerbound']:.0f} "
              f"R(BF,I60)={r_bf['mean_annual_R_I60lowerbound']:.0f}")
        # save raw series
        (OUT_DIR / f"era5_hourly_{pid}_{YEAR_RANGE[0]}-{YEAR_RANGE[1]}.json").write_text(
            json.dumps({"point_id": pid, "lon": lon, "lat": lat, "times": times,
                        "precipitation": precip.tolist()}),
            encoding="utf-8",
        )

    # spatial mean R across points
    mean_r_ws_i60 = float(np.mean([r["wischmeier"]["mean_annual_R_I60lowerbound"] for r in all_results]))
    mean_r_bf_i60 = float(np.mean([r["brown_foster"]["mean_annual_R_I60lowerbound"] for r in all_results]))
    mean_r_ws_i30 = float(np.mean([r["wischmeier"]["mean_annual_R_I30est"] for r in all_results]))
    mean_r_bf_i30 = float(np.mean([r["brown_foster"]["mean_annual_R_I30est"] for r in all_results]))

    print(f"\n=== Empirical R (spatial mean over {len(V1_POINTS)} points, {YEAR_RANGE[0]}-{YEAR_RANGE[1]}) ===")
    print(f"  Wischmeier-Smith KE, I60 lower bound : R = {mean_r_ws_i60:.0f}")
    print(f"  Brown-Foster KE,      I60 lower bound : R = {mean_r_bf_i60:.0f}")
    print(f"  Wischmeier-Smith KE, I30 est (x{I30_UPSCALE})   : R = {mean_r_ws_i30:.0f}")
    print(f"  Brown-Foster KE,      I30 est (x{I30_UPSCALE})   : R = {mean_r_bf_i30:.0f}")
    print(f"\n  Literature HIGH family: ~1380-3719; LOW family: ~240-320")

    diag = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": "bin/compute_era5_empirical_rfactor.py",
        "purpose": "Empirical EI30 R from ERA5 hourly to arbitrate the HIGH vs LOW R-families.",
        "data_source": "ERA5 hourly precipitation via open-meteo (no auth)",
        "year_range": list(YEAR_RANGE),
        "parameters": {
            "storm_gap_hours": STORM_GAP_HOURS,
            "erosive_depth_mm": EROSIVE_DEPTH_MM,
            "ke_intensity_cap_mmh": KE_INTENSITY_CAP,
            "i30_upscale_from_i60": I30_UPSCALE,
        },
        "caveats": [
            "ERA5 is hourly, not 30-min breakpoint, so I60 is a lower bound on I30 and R is a LOWER BOUND.",
            "ERA5 reanalysis can under-estimate convective storm intensity in semi-arid tropics.",
            f"I30 estimate = I60 * {I30_UPSCALE} is a rough convective upscaling assumption, labelled separately.",
        ],
        "points": all_results,
        "spatial_mean_R": {
            "wischmeier_I60lowerbound": round(mean_r_ws_i60, 1),
            "brown_foster_I60lowerbound": round(mean_r_bf_i60, 1),
            "wischmeier_I30est": round(mean_r_ws_i30, 1),
            "brown_foster_I30est": round(mean_r_bf_i30, 1),
        },
        "literature_families_for_comparison": {
            "HIGH": "RF/Arnoldus/Elwell-Zimbabwe ~1380-3719",
            "LOW": "Hurni/Epworth ~240-320",
        },
    }
    (DIAG_OUT / "era5_empirical_rfactor_diagnostics.json").write_text(
        json.dumps(diag, indent=2), encoding="utf-8"
    )
    print(f"\nwrote {DIAG_OUT / 'era5_empirical_rfactor_diagnostics.json'}")


if __name__ == "__main__":
    main()
