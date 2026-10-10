# bin/ — IFPM Pipeline Scripts

This directory holds the local exploration and processing scripts for the IFPM
flood-risk modelling workspace. Scripts are organised into a **7-stage pipeline**
and orchestrated by `pipeline.py`.

> **Scope**: these are `TOOLING` scripts (AGENTS.md), not the public-safe
> deliverable. The reusable pipeline scaffold lives in `ifpm-flood-pipeline/`
> (separate repo). Scripts here work with real local data under `data/` and
> `outputs/`; they are not part of any release package.

## Current entry points (September 2026 state)

The active work (Secocha and Goslar) is run by standalone runners, not by the
`pipeline.yaml` default chain. The default chain below still targets the
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

## Legacy pipeline quick start (frozen former Peru area)

```bash
# List all scripts grouped by pipeline stage
.venv/bin/python bin/pipeline.py list

# Visualise the dependency DAG (pipe to Graphviz if installed)
.venv/bin/python bin/pipeline.py dot | dot -Tpng -o pipeline.png

# Run a whole stage in dependency order
.venv/bin/python bin/pipeline.py run factors

# Run one script and everything it depends on
.venv/bin/python bin/pipeline.py run --target run_peru_hybas_l7_6070641200_priority_scenarios

# Run one script only (no upstream)
.venv/bin/python bin/pipeline.py run --target run_peru_hybas_l7_6070641200_priority_scenarios --no-deps

# Rebuild the Peru exposure indicators directly before a scenario rerun.
.venv/bin/python bin/criteria/build_peru_exposure_indicators.py

# Refresh Peru population accounting and SINPAD co-location tables from the current mentor PIM.
.venv/bin/python bin/pipeline.py run --target summarize_peru_population_by_pim_class
.venv/bin/python bin/pipeline.py run --target compare_peru_pim_sinpad_colocation
.venv/bin/python bin/pipeline.py run --target summarize_peru_criterion_data_strength

# Refresh remote source data only when network access is intentional.
.venv/bin/python bin/pipeline.py run --target download_peru_worldpop_population_subset --allow-network
.venv/bin/python bin/pipeline.py run --target query_peru_sinpad_flood_events --allow-network

# Without --allow-network, remote producers are omitted from dependency chains.
# A downstream step fails clearly if its required local input is absent.

# Force re-run even if outputs are up-to-date
.venv/bin/python bin/pipeline.py run --target <name> --force
```

## Weights

The Supervisor complete weight specification (FH/SE/LU/ES/SV =
0.34 / 0.25 / 0.17 / 0.10 / 0.14) is applied in the canonical runner
`bin/scenarios/run_peru_hybas_l7_6070641200_priority_scenarios.py` on the
current branch `codex/goslar-validation-2024` and recorded in each run's
`run_manifest.json`. The former `weights/supervisor-full-spec` branch has been
merged and removed. The older test weights (0.35 / 0.25 / 0.20 / 0.12 / 0.08)
survive only as frozen outputs under
`outputs/srtm_1arcsec_peru_pilot/pim_versions/`; the side-by-side comparison
is in `pim_versions/comparison_v02_v07/`.

## The 7 pipeline stages

Scripts are classified by filename prefix. Each stage consumes the previous
stage's outputs.

| Stage | Prefixes | What it does |
|---|---|---|
| **acquire** | `download_` `plan_` `inventory_` `intake_` `check_data` `discover_` `extract_` | Download, plan, and inventory raw data |
| **factors** | `preprocess_` `derive_` | Derive terrain/hydrology/USLE factors from raw data |
| **criteria** | `build_` | Assemble MCDA scoreable criteria (0–1 standardised) |
| **scenarios** | `run_` | Weighted overlay + sensitivity/stability analysis |
| **visualize** | `plot_` | Generate mentor/boss-facing figures and boards |
| **package** | `prepare_` `standardize_` `export_` `diagnose_` `check_v1_raster_grid` | Boundary export, evidence packaging, grid checks |
| **investigate** | `explore_` `compute_` `compare_` `verify_` `summarize_` | One-off diagnostics, comparisons, and summaries |

## Two parallel country chains

Most stages have a Zimbabwe (V1) and a Peru (Arequipa Region) variant that mirror each other:

```
                    acquire → factors → criteria → scenarios → visualize
Zimbabwe V1:   ...   v1_dem  →  slope   →  criteria_stack_v0_2  →  rainfall_exposure_v0_4  →  comparison
Peru Arequipa Region:      ...   peru_hybas_l7_6070641200_dem →  slope   →  peru_hybas_l7_6070641200_criteria_stack   →  peru_hybas_l7_6070641200_priority_scenarios  →  comparison
```

The two chains now follow the mentor five-main-criterion framework (Flood,
Sediment, Land Use / ASM, Environmental, Socioeconomic). The executable overlay
uses those five PIM main criteria as top-level weights (see "Weights" above;
the exact top-level and sub-weights of each run are in its `run_manifest.json`).
Mining is no longer a PIM criterion; it is shown as a separate context overlay.
This diagram describes the legacy chains; Secocha and Goslar use the runners
listed under "Current entry points".

## Shared helpers (`_lib/`)

`bin/_lib/ifpm_tools.py` provides common functions that were previously
duplicated across dozens of scripts:

- `load_boundary(gpkg, layer, crs)` — load a single-feature boundary geometry
- `write_raster(path, data, profile)` — unified float32/deflate/tiled GeoTIFF writer
- `raster_stats(data, mask)` — summary statistics (two modes: with/without mask)
- `standardize(data, nodata, invert, p_low, p_high)` — percentile-clip min-max to [0,1]
- `run_grid_gate(reference, rasters, output)` — invoke the V1 grid-compatibility check
- `ROOT`, `NODATA` — canonical constants

Scripts can adopt these incrementally (see the stage-3 migration plan).

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

## Removed legacy scripts

The abandoned V1/V2 R-factor chain, the early outlet-exploration scripts and the
v0.1 autonomous prototype (formerly `bin/_archive/`) were deleted in the
2026-10-08 handover cleanup. Retrieve them from Git history if needed
(`git log --diff-filter=D -- bin/_archive`).
