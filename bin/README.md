# bin/ — IFPM Pipeline Scripts

This directory holds the local exploration and processing scripts for the IFPM
flood-risk modelling workspace. Scripts are organised into a **7-stage pipeline**
and orchestrated by `pipeline.py`.

> **Scope**: these are `TOOLING` scripts (AGENTS.md), not the public-safe
> deliverable. The reusable pipeline scaffold lives in `ifpm-flood-pipeline/`
> (separate repo). Scripts here work with real local data under `data/` and
> `outputs/`; they are not part of any release package.

## Quick start

```bash
# List all scripts grouped by pipeline stage
.venv/bin/python bin/pipeline.py list

# Visualise the dependency DAG (pipe to Graphviz if installed)
.venv/bin/python bin/pipeline.py dot | dot -Tpng -o pipeline.png

# Run a whole stage in dependency order
.venv/bin/python bin/pipeline.py run factors

# Run one script and everything it depends on
.venv/bin/python bin/pipeline.py run --target run_pe1_priority_scenarios

# Run one script only (no upstream)
.venv/bin/python bin/pipeline.py run --target run_pe1_priority_scenarios --no-deps

# Force re-run even if outputs are up-to-date
.venv/bin/python bin/pipeline.py run --target <name> --force
```

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
| **investigate** | `explore_` `compute_` `compare_` `verify_` | One-off R-factor investigation and literature checks |

## Two parallel country chains

Most stages have a Zimbabwe (V1) and a Peru (PE1) variant that mirror each other:

```
                    acquire → factors → criteria → scenarios → visualize
Zimbabwe V1:   ...   v1_dem  →  slope   →  criteria_stack_v0_2  →  rainfall_exposure_v0_4  →  comparison
Peru PE1:      ...   pe1_dem →  slope   →  pe1_criteria_stack   →  pe1_priority_scenarios  →  comparison
                                                              ↘                ↙
                                                    plot_zimbabwe_peru_prototype_comparison
                                                    plot_mentor_boss_priority_explanation_package
```

The two chains now follow the mentor five-main-criterion framework (Flood,
Sediment, Land Use / ASM, Environmental, Socioeconomic). The executable overlay
currently uses six scored implementation layers because Land Use / ASM is split
into land-cover and mining, rainfall is a sensitivity layer, and Environmental
is not yet an independent scored raster.

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

## Deprecated scripts (`_deprecated/`)

Six scripts from the abandoned V1/V2 R-factor chain are kept under
`_deprecated/` with `raise SystemExit` guards — running them prints a clear
DEPRECATED message and exits. They are excluded from the pipeline DAG.

## Archived scripts (`_archive/`)

Six early outlet-exploration scripts (superseded by `boundary_v1`) are under
`_archive/`. They are also excluded from the DAG.
