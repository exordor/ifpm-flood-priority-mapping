# bin/ — IFPM Pipeline Scripts

This directory holds the local exploration and processing scripts for the IFPM
flood-risk modelling workspace. Scripts are organised into a **7-stage pipeline**
and orchestrated by `pipeline.py`.

Scripts here work on real local data under `data/` and `outputs/`.

## Current entry points (September 2026 state)

The active work (Secocha and Goslar) is run by standalone runners, not by the
`pipeline.yaml` default chain. The default chain still targets the
frozen former Peru area (`outputs/srtm_1arcsec_peru_pilot/`) and must not be
used for new runs.

```bash
# Secocha five-criterion chain (Supervisor weights) and its validation report
.venv/bin/python bin/factors/run_peru_secocha_chain.py
.venv/bin/python bin/validate/validate_peru_secocha_chain.py

# Goslar expanded multi-river comparison and report
.venv/bin/python bin/analysis/run_goslar_multiriver_full.py
.venv/bin/python bin/analysis/report_goslar_multiriver_full.py
```

Other Goslar/Abzucht commands are listed per experiment in
`context/docs/research-map/EXPERIMENTS.md`.

## Legacy pipeline

`bin/pipeline.py` only drives the frozen former-Peru chain; do not use it for new runs.

## Weights

Supervisor complete weight specification: FH/SE/LU/ES/SV =
0.34 / 0.25 / 0.17 / 0.10 / 0.14. The weights used in each run are recorded in
its `run_manifest.json`.

## The 7 pipeline stages

Scripts are classified by filename prefix. Each stage consumes the previous
stage's outputs.

| Stage | Prefixes | What it does |
|---|---|---|
| **acquire** | `download_` `plan_` `inventory_` `intake_` `check_data` `discover_` `extract_` | Download, plan, and inventory raw data |
| **factors** | `preprocess_` `derive_` | Derive terrain/hydrology/USLE factors from raw data |
| **criteria** | `build_` | Assemble MCDA scoreable criteria (0–1 standardised) |
| **scenarios** | `run_` | Weighted overlay + sensitivity/stability analysis |
| **visualize** | `plot_` | Figures |
| **package** | `prepare_` `standardize_` `export_` `diagnose_` `check_v1_raster_grid` | Boundary export, evidence packaging, grid checks |
| **investigate** | `explore_` `compute_` `compare_` `verify_` `summarize_` | One-off diagnostics, comparisons, and summaries |

## Shared helpers (`_lib/`)

`bin/_lib/ifpm_tools.py` provides common functions that were previously
duplicated across dozens of scripts:

- `load_boundary(gpkg, layer, crs)` — load a single-feature boundary geometry
- `write_raster(path, data, profile)` — unified float32/deflate/tiled GeoTIFF writer
- `raster_stats(data, mask)` — summary statistics (two modes: with/without mask)
- `standardize(data, nodata, invert, p_low, p_high)` — percentile-clip min-max to [0,1]
- `run_grid_gate(reference, rasters, output)` — invoke the V1 grid-compatibility check
- `ROOT`, `NODATA` — canonical constants

## Declaring dependencies for the DAG

A script participates in the DAG once it declares module-level `INPUTS` and
`OUTPUTS` lists:

```python
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

INPUTS = [
    ROOT / "outputs" / "srtm_1arcsec_zimbabwe_prototype" / "terrain_preprocessing" / "v1_dem_utm35s_30m.tif",
]
OUTPUTS = [
    ROOT / "outputs" / "srtm_1arcsec_zimbabwe_prototype" / "terrain_preprocessing" / "v1_slope_30m.tif",
]
```

The orchestrator parses these statically (no execution needed) to build the DAG,
so `pipeline.py run --target X` runs X and its full transitive upstream in the
correct order. Until a script declares I/O it is treated as a standalone node.
