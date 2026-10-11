# IFPM handover note

Date: 2026-10-08.

## 1. What the project is

IFPM is a multi-criteria flood prioritisation prototype. It normalizes the five main PIM criteria (flood FH, sediment/soil erosion SE, land use LU, environmental ES, socioeconomic SV) to 0–1 and combines them with weights into a composite priority map. All results are provisional; the index has not been validated against observed floods.

Current weights (Supervisor full specification): FH 0.34 / SE 0.25 / LU 0.17 / ES 0.10 / SV 0.14. The weights actually used in each run are the ones recorded in `run_manifest.json` in the output folder. Mining is no longer a criterion; it is only kept as a separate comparison layer.

## 2. Study areas and current status

| Study area | Status | Main outputs |
|---|---|---|
| Goslar, Germany (multi-river extension covering Abzucht and 8 regulatory flood zones, about 739 km²) | Most recent work (September), active | `outputs/goslar_multiriver_full_extent_v1/frozen_scale_v1/`, `outputs/goslar_abzucht_display_rectangle_v1/` |
| Secocha, Peru (a 30 km² reference window from A7367 Map 7, not a catchment) | Active, provisional | `outputs/peru_secocha_a7367_reference_extent_v1/`, `outputs/secocha_2023_validation/` |
| Former Peru area `peru_hybas_l7_6070641200` | Frozen baseline, read-only; do not write new results here | `outputs/srtm_1arcsec_peru_pilot/` (contains 7 weight versions) |
| Upper Mzingwane, Zimbabwe (`boundary_v1`) | Background case, no longer being developed | `outputs/boundary_v1/` and others |

The most important open problem: in the Goslar extension comparison, the flood criterion is higher inside all 8 regulatory flood zones than in their surrounding 1 km rings, but the composite priority is higher in only 3 of them. In other words, the relationship between the composite index and the flood evidence has not yet been sorted out.

## 3. Directory map

| Location | Contents | In Git? |
|---|---|---|
| `README.md`, `AGENTS.md` | General workspace description; `AGENTS.md` is a one-page set of working conventions (folders, data registration, modelling rules) | Yes |
| `bin/` | About 160 processing scripts, grouped into folders by stage; entry points and descriptions are in `bin/README.md` | Yes |
| `tests/` | 53 test files | Yes |
| `context/docs/research-map/` | Main project record: `EXPERIMENTS.md` (commands, outputs and conclusions of current experiments) and `DECISION_LOG.md` (decisions that are still in force, including the weights) | Yes |
| `context/docs/data-management/registry/` | Source, licence and download record for each dataset | Yes |
| `context/docs/glossary.md`, `context/docs/methodology/` | Glossary; PIM method note | Yes |
| `data/raw/`, `data/validation/` | Raw data, about 17 GB | No |
| `outputs/` | All results; the index is in `outputs/README.md` | No |
| `exports/` | Portable QGIS packages | No |
| `ifpm-flood-pipeline/` | Separate delivery code repository (with its own `.git`); it only has tests on synthetic data | Separate repository |

Note: `data/`, `outputs/` and `exports/` are all ignored by `.gitignore`. Cloning the repository alone does not give you the data or the results; you need to copy the whole folder.

## 4. How to run it

Environment (in the workspace root):

```sh
# Install uv first (on a Mac you can use brew install uv), then run in the workspace root:
uv sync --extra hydrology    # installs Python 3.11+ and all dependencies from uv.lock and creates .venv
```

`--extra hydrology` installs WhiteboxTools, which both main chains need for the hydrology steps. On first run it automatically downloads a program file, so it needs an internet connection. rasterio and geopandas ship with their own GDAL, so you do not need to install it separately. The existing `.venv` was built on macOS and must be rebuilt on a different machine. QGIS is only used to open the review projects and is installed separately.

Main commands:

```sh
# Secocha
.venv/bin/python bin/factors/run_peru_secocha_chain.py
.venv/bin/python bin/validate/validate_peru_secocha_chain.py

# Goslar extension comparison
.venv/bin/python bin/analysis/run_goslar_multiriver_full.py
.venv/bin/python bin/analysis/report_goslar_multiriver_full.py

# Tests
.venv/bin/python -m unittest discover -s tests
```

The remaining Goslar/Abzucht commands are listed one by one under the corresponding experiments in `context/docs/research-map/EXPERIMENTS.md`.

Do not use the default chain of `python bin/pipeline.py run`: it still points to the frozen former Peru area.

To look at results quickly, open `outputs/peru_secocha_qgis_project_package_compact/IFPM_Peru_Secocha_ReviewMap.qgz` and `outputs/goslar_qgis_project_package_compact/IFPM_Goslar_ReviewMap.qgz` in QGIS. The explanation of the latest Goslar conclusions is in `outputs/goslar_multiriver_full_extent_v1/frozen_scale_v1/READING_NOTE.md`.

## 5. Git status

- The branch `codex/goslar-validation-2024` is the reference. On 2026-10-08 all uncommitted work from September was committed to this branch (locally, not pushed).
- `main` is behind the current branch and has one commit that duplicates a commit on the current branch ("Centralize numeric standardization"). Do not keep working on `main`; when needed, merge or reset the current branch onto it.
- The `weights/supervisor-full-spec` branch has been merged into the current branch and deleted.
- The repository has no configured push remote. Whether and where to push is up to the person taking over.

## 6. Known issues

- The default include chain in `pipeline.yaml` still uses the former Peru area scripts. Secocha and Goslar use standalone runners that are not connected to the DAG.
- Some Zimbabwe scripts in `bin/` reference `outputs/_archive/...` files that were cleaned up in August, so they no longer run (`export_v1_working_boundary.py`, `prepare_v1_multicriteria_evidence.py`, `plot_v1_boundary_paper.py`). Zimbabwe is now a background case, so the impact is small.
- Some older field names are broader than the actual evidence. For example, tree canopy cover loss is only a proxy for vegetation loss. The September notes on semantics are in `outputs/goslar_abzucht_display_rectangle_v1/component_semantics_v1/` and `outputs/goslar_abzucht_display_rectangle_v1/input_semantics_followup_v1/`.
- Some raw data are licence-restricted (see the per-dataset notes in `context/docs/data-management/registry/`). Rerunning historical results may require requesting access again.
- The scripts that download CLMS and Sentinel pixels need an access credentials file on the local machine. The credentials are not in the repository.

## 7. Suggested next steps

1. Decide how the composite priority index should be evaluated against the flood evidence. If you want to tune the weights, first set aside an independent evaluation dataset; do not use the same data both to tune the weights and to validate them.
2. Check the coverage and proxy meaning of each criterion. Places with missing data must be visible on the map and must not be treated as low risk.
3. Connect the Secocha and Goslar runners to `pipeline.yaml`, or simply make `pipeline.yaml` serve only these two chains and remove the default former Peru area chain.
4. Rebuild the environment on the new person's machine, run the tests and the main commands above, and confirm that the results can be reproduced.
5. Confirm that the person taking over can open the QGIS review projects in `outputs/`.

## 8. Removed material

Obsolete scripts, documents and duplicate exports were removed in October 2026; they can be recovered from Git history.
