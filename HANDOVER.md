# IFPM handover note

Date: 2026-10-08; layout updated 2026-10-12 after the move to the config-driven `ifpm` package.

## 1. What the project is

IFPM is a multi-criteria flood prioritisation prototype. It normalizes the five main PIM criteria (flood FH, sediment/soil erosion SE, land use LU, environmental ES, socioeconomic SV) to 0–1 and combines them with weights into a composite priority map. All results are provisional; the index has not been validated against observed floods.

Current weights (Supervisor full specification): FH 0.34 / SE 0.25 / LU 0.17 / ES 0.10 / SV 0.14. The weights actually used in each run are the ones recorded in `run_manifest.json` in the output folder. Mining is no longer a criterion; it is only kept as a separate comparison layer.

## 2. Study areas and current status

| Study area | Status | Main outputs |
|---|---|---|
| Goslar, Germany (multi-river extension covering Abzucht and 8 regulatory flood zones, about 739 km²) | Most recent work (September), active | `outputs/goslar_multiriver_full_extent/fixed_scale/`, `outputs/goslar_abzucht_diagnostics/` |
| Secocha, Peru (a 30 km² reference window from A7367 Map 7, not a catchment) | Active, provisional | `outputs/secocha_pim_chain/`, `outputs/secocha_2023_validation/` |
| Former Peru area `peru_former` | Frozen baseline, read-only; do not write new results here | `outputs/peru_former_pim_chain/` (contains 7 weight versions) |
| Upper Mzingwane, Zimbabwe (`zimbabwe_upper_mzingwane`) | Background case, no longer being developed | `outputs/zimbabwe_pim_scenarios/` and others |

The most important open problem: in the Goslar extension comparison, the flood criterion is higher inside all 8 regulatory flood zones than in their surrounding 1 km rings, but the composite priority is higher in only 3 of them. In other words, the relationship between the composite index and the flood evidence has not yet been sorted out.

## 3. Directory map

| Location | Contents | In Git? |
|---|---|---|
| `README.md`, `AGENTS.md` | General workspace description; `AGENTS.md` is a one-page set of working conventions (folders, data registration, modelling rules) | Yes |
| `ifpm/`, `configs/` | The config-driven chain for all four areas and the QGIS packages (`python -m ifpm`); settings per area in `configs/<area>.yaml`, dataset paths in `configs/datasets.yaml` | Yes |
| `bin/visualize/` | 11 report-figure scripts (location maps, overviews, Peru/Zimbabwe report maps); see `bin/README.md` | Yes |
| `tests/` | 14 test files (54 tests, about 10 s); tests that would regenerate files under `outputs/` run only with `IFPM_WRITE_OUTPUTS=1` | Yes |
| `tools/` | `digitize_secocha_a7367_map7_event.py`: the one-time Map 7 event digitization | Yes |
| `context/docs/research-map/` | Main project record: `EXPERIMENTS.md` (commands, outputs and conclusions of current experiments) and `DECISION_LOG.md` (decisions that are still in force, including the weights) | Yes |
| `context/docs/data-management/registry/` | Source, licence and download record for each dataset | Yes |
| `context/docs/glossary.md`, `context/docs/methodology/` | Glossary; PIM method note | Yes |
| `data/raw/`, `data/validation/` | Raw data, about 12 GB | No |
| `outputs/` | All results, about 1.3 GB plus `outputs/_rerun/` (reruns for `verify`, can be rebuilt); the index is in `outputs/README.md` | No |
| `exports/` | Portable QGIS packages (`exports/qgis_packages/`, folder plus zip per package) | No |

Note: `data/`, `outputs/` and `exports/` are all ignored by `.gitignore`. Cloning the repository alone does not give you the data or the results; you need to copy the whole folder.

## 4. How to run it

Environment (in the workspace root):

```sh
# Install uv first (on a Mac you can use brew install uv), then run in the workspace root:
uv sync --extra hydrology    # installs Python 3.11+ and all dependencies from uv.lock and creates .venv
```

`--extra hydrology` installs WhiteboxTools, which both main chains need for the hydrology steps. On first run it automatically downloads a program file, so it needs an internet connection. rasterio and geopandas ship with their own GDAL, so you do not need to install it separately. The existing `.venv` was built on macOS and must be rebuilt on a different machine. QGIS is only used to open the review projects and is installed separately.

Config-driven package `ifpm/` (settings in `configs/<area>.yaml` and `configs/datasets.yaml`):

```sh
.venv/bin/python -m ifpm list                         # areas, extents and their stages
.venv/bin/python -m ifpm run secocha                  # all stages incl. validation
.venv/bin/python -m ifpm run goslar                   # extents basin, abzucht_hq100, abzucht, multiriver in order
.venv/bin/python -m ifpm run goslar --extent multiriver --step comparison,report
.venv/bin/python -m ifpm verify goslar                # pass/fail table against the current outputs
.venv/bin/python -m ifpm run zimbabwe                 # re-score from the existing criteria (background case)
.venv/bin/python -m ifpm run peru_former              # frozen: re-score into _rerun and check the FROZEN_BASELINE pins
.venv/bin/python -m ifpm qgis goslar --qa             # QGIS FullAudit and ReviewMap packages (needs QGIS); --in-place rebuilds the live ones
```

`run` writes under `--out` (default `outputs/_rerun/<area>/`, same relative paths as `outputs/`) and never over the current outputs; `verify` compares that folder with the current outputs (identical, or within 1e-6 for rasters; differences accepted in the config show as KNOWN).

Tests:

```sh
.venv/bin/python -m unittest discover -s tests
```

The per-experiment Goslar/Abzucht commands are listed in `context/docs/research-map/EXPERIMENTS.md`.

To look at results quickly, open `outputs/secocha_qgis_review/IFPM_Peru_Secocha_ReviewMap.qgz` and `outputs/goslar_qgis_review/IFPM_Goslar_ReviewMap.qgz` in QGIS. The explanation of the latest Goslar conclusions is in `outputs/goslar_multiriver_full_extent/fixed_scale/READING_NOTE.md`.

## 5. Git status

- `main` is the reference branch. On 2026-10-12 the work branch `codex/goslar-validation-2024` (all September work plus the October refactor) was merged into `main` (merge commit 1d5460d); the one commit that only `main` had ("Centralize numeric standardization", 9c780c5) was already contained in the branch (43fc9dc). The branch is kept and points at the same commit.
- The `weights/supervisor-full-spec` branch has been merged earlier and deleted.
- Everything is committed locally; the repository has no configured push remote. Whether and where to push is up to the person taking over.

## 6. Known issues

- Zimbabwe and the former Peru area are only re-scored from their existing criterion rasters (`ifpm run zimbabwe|peru_former`); their upstream chains are not part of `ifpm`. The Zimbabwe criteria-stack builder was removed in commit 4fbd10c and its environmental input folder no longer exists.
- The Goslar full-extent run reads Zensus 2022 population from `data/raw/zensus2022_goslar_multiriver/` (the 100 m clip derived from the national archive, which is no longer present); see the registry note `zensus2022_goslar_multiriver`.
- Some older field names are broader than the actual evidence. For example, tree canopy cover loss is only a proxy for vegetation loss. The September notes on semantics are in `outputs/goslar_abzucht_diagnostics/component_semantics/` and `outputs/goslar_abzucht_diagnostics/input_semantics_followup/`.
- Some raw data are licence-restricted (see the per-dataset notes in `context/docs/data-management/registry/`). Rerunning historical results may require requesting access again.
- Downloading CLMS and Sentinel pixels again needs an access credentials file on the local machine (not in the repository); the download scripts are in Git history (`git show 206214e:bin/acquire/<script>.py`).
- The Secocha road-access rerun differs from the stored outputs by 3 edge cells (floating-point clipping at x=696500); `ifpm verify secocha` reports the 5 affected files as KNOWN.

## 7. Suggested next steps

1. Decide how the composite priority index should be evaluated against the flood evidence. If you want to tune the weights, first set aside an independent evaluation dataset; do not use the same data both to tune the weights and to validate them.
2. Check the coverage and proxy meaning of each criterion. Places with missing data must be visible on the map and must not be treated as low risk.
3. Rebuild the environment on the new person's machine, run the tests and the main commands above, and confirm that the results can be reproduced.
4. Confirm that the person taking over can open the QGIS review projects in `outputs/`.

## 8. Removed material

Obsolete scripts, documents and duplicate exports were removed in October 2026; they can be recovered from Git history. Files under `data/` and `outputs/` are not in Git: the removed SVG twins, scratch rasters, diagnostic rasters, duplicate figure copies, unpacked copies of zips and four unused public datasets are gone for good (each registry note says where to download a dataset again; `identical_files.csv` in `outputs/peru_former_pim_chain/pim_versions/<version>/` says where a removed byte-identical copy still lives). The bin/ processing scripts replaced by `ifpm` (Peru, Zimbabwe, Goslar, Secocha chains, data acquisition, QGIS packaging) are in commit 206214e: `git show 206214e:<path>`. The separate delivery repository `ifpm-flood-pipeline` (own `.git`, tests on synthetic data only) now lives outside this workspace at `~/code/ifpm-flood-pipeline`.
