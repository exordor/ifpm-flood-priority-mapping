# IFPM Flood Risk Modelling Workspace

> New to this project? Start with [HANDOVER.md](HANDOVER.md) (handover
> note, 2026-10-08). It summarises the current state, directory map and next steps.

The root repository is the research workspace (report-figure scripts in `bin/visualize/`, docs in `context/`, local `data/` and `outputs/`); the chain itself is the config-driven package `ifpm/` with settings in `configs/`.

Active cases: Secocha (Peru) and Goslar (Germany). Zimbabwe is a background case.

- **Secocha, Arequipa, Peru** (`secocha_reference_extent`): a provisional 30 km² reference window, not a catchment; see `context/docs/research-map/EXPERIMENTS.md` for detail.
- **Goslar, Germany** (Abzucht and the multi-river comparison under `outputs/goslar_multiriver_full_extent/`): compares the priority index with official flood zones.

The former Peru area `peru_former` is a frozen baseline. Its outputs are kept under `outputs/peru_former_pim_chain/` and must not receive new runs.

## How to run

Set up the environment with `uv sync --extra hydrology` (see [HANDOVER.md](HANDOVER.md) §4). The config-driven chain (`ifpm/`, settings in `configs/`) is the new way to run both study areas:

```sh
.venv/bin/python -m ifpm list                                  # areas, extents and stages
.venv/bin/python -m ifpm run secocha                           # writes to outputs/_rerun/secocha/
.venv/bin/python -m ifpm run goslar --extent basin --step rainfall
.venv/bin/python -m ifpm verify secocha                        # compare a rerun with the current outputs
.venv/bin/python -m ifpm run peru_former                       # frozen area: re-score and check the pins
.venv/bin/python -m ifpm qgis secocha                          # QGIS packages (needs QGIS)
```

`run` never writes over the current outputs: it writes under `--out` (default `outputs/_rerun/<area>/`) with the same relative paths.

## Directory Structure

See the directory map in [HANDOVER.md](HANDOVER.md) §3.

## Document Navigation

- [Experiments](context/docs/research-map/EXPERIMENTS.md): current experiments, commands and results.
- [Decision log](context/docs/research-map/DECISION_LOG.md): decisions in force, including weights.
- [Dataset registry](context/docs/data-management/registry/): source and licence per dataset.
- [Terminology](context/docs/glossary.md).
- [Internal context](context/README.md): what is kept under `context/`.
- [Figure scripts](bin/README.md): the report-figure scripts kept in `bin/visualize/`.
