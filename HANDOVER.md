# IFPM handover note

Date: 2026-10-08. This note is for whoever takes over this workspace. After reading it you should know what the project does, where things are, how to run it and what to do next.

## 1. What the project is

IFPM is a multi-criteria flood prioritisation prototype. It normalizes the five main PIM criteria (flood FH, sediment/soil erosion SE, land use LU, environmental ES, socioeconomic SV) to 0–1 and combines them with weights into a composite priority map. All results are prototype or diagnostic level (`diagnostic_only` / `provisional`). They are not a validated flood prediction model.

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
| `bin/` | About 190 processing scripts, grouped into folders by stage; entry points and descriptions are in `bin/README.md` | Yes |
| `tests/` | 60 test files | Yes |
| `context/docs/research-map/` | Main project record: `EXPERIMENTS.md` (commands, outputs and conclusions of current experiments) and `DECISION_LOG.md` (decisions that are still in force, including the weights) | Yes |
| `context/docs/data-management/registry/` | Source, licence and download record for each dataset | Yes |
| `context/docs/glossary.md`, `context/docs/methodology/` | Glossary; PIM method note (English) | Yes |
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
- Some older field names are broader than the actual evidence. For example, tree canopy cover loss is only a proxy for vegetation loss. The September notes on semantics are in `goslar_abzucht_display_rectangle_v1/component_semantics_v1/` and `input_semantics_followup_v1/`.
- Some raw data were left out of the handover package because of licence restrictions (see `EXCLUSIONS.json` in the handover package). Rerunning historical results may require requesting access again.
- The scripts that download CLMS and Sentinel pixels need an access credentials file on the local machine. The credentials are not in the repository.

## 7. Suggested next steps

1. Decide how the composite priority index should be evaluated against the flood evidence. If you want to tune the weights, first set aside an independent evaluation dataset; do not use the same data both to tune the weights and to validate them.
2. Check the coverage and proxy meaning of each criterion. Places with missing data must be visible on the map and must not be treated as low risk.
3. Connect the Secocha and Goslar runners to `pipeline.yaml`, or simply make `pipeline.yaml` serve only these two chains and remove the default former Peru area chain.
4. Rebuild the environment on the new person's machine, run the tests and the main commands above, and confirm that the results can be reproduced.
5. Confirm that the person taking over can open the QGIS review projects in `outputs/`.

## 8. What this cleanup did (2026-10-08)

- Deleted about 17 GB of duplicate and temporary files: three extracted folders in `exports/` that were identical to their zips (the zips were checked file by file), `tmp/` (intermediate versions of the August PPT, including a website cookies file), `data/tmp/`, 12 automatic backup folders named `*_previous_<timestamp>`, `IFPM_for_ChatGPT_QA.zip` in the root folder, and caches and `.DS_Store` files.
- Deleted 22 obsolete scripts and two unused generated images in `bin/_archive/` (they can be recovered from the Git history).
- Rewrote `outputs/README.md` and deleted the outdated `outputs/OUTPUTS_INDEX.csv`; updated `README.md`, `bin/README.md` and `context/README.md`.
- Moved the reference papers to `context/references/`.

On 2026-10-09 `context/` was cleaned up further. Only the research records, data registry, glossary, method notes and the Supervisor handover draft were kept, plus `context/configs/`, because scripts in `bin/` read it. The mentor communication drafts, early verification reports, old plans and archives, pre-download checks, reference grid rules, screenshots of the mentor's method framework and the original data inventory were deleted (they can be recovered from the Git history). The reference paper PDFs were also deleted; they are not in Git. A few paths in the remaining research records still point to deleted files. These are historical references; look them up in the Git history when needed.

On 2026-10-10 outdated and defensive content was removed from the documentation and code. The research records were merged from 9 files into two, `EXPERIMENTS.md` and `DECISION_LOG.md`, which only describe current experiments and decisions that are still in force. `AGENTS.md` was changed from 467 lines of AI management rules into a one-page set of working conventions. The glossary now only keeps the current criteria and field meanings. Four scripts that only checked wording (`check_*terminology*`, `check_glossary_sources`, `check_top20_priority_wording`) and their tests were deleted.

On 2026-10-10 `exports/IFPM_Supervisor_Handover_2026-10-08.zip` (14 GB, the full snapshot taken before the cleanup) and its checksum file were deleted, together with two zips: the August sharing package and the June mentor report package. The root PPT template `pre/summary01.potx` and the unused QGIS style library `symbology-style.db` were also deleted. In addition, the packaging script `bin/package/build_supervisor_handover.py`, two English handover letter drafts for Supervisor, the old Zimbabwe configuration `context/configs/boundary_v1_criteria_stack_v0_2.csv` and the script that read it, `bin/criteria/build_boundary_v1_criteria_stack.py`, were deleted.

On 2026-10-10 24 plotting and packaging scripts used only for reports, slides and mentor presentations were deleted along with their configuration tables (report figures, briefing boards, PPT figures and old QGIS project packaging for the former Peru area and Zimbabwe), together with 6 tests that only tested them. References to them in `pipeline.yaml`, `bin/README.md` and the remaining tests were cleaned up at the same time. `export_peru_raw_input_factor_maps`, `export_peru_pim_criteria_maps`, `export_paper_style_single_maps` and `build_ifpm_qgis_project_package` are kept for now, because Zimbabwe plotting scripts or tests still call them.

2026-10-10: translated all remaining Chinese text in the workspace to English: this note, the PIM method note, the strings and comments in 17 scripts under `bin/`, and the READING_NOTE.md files and inventory tables under `outputs/`. Checksums in the affected output manifests were updated to match. Text inside existing figures (PNG/PDF) was not changed.
