# AGENTS.md

Working conventions for this workspace.

## Where things go

| Content | Location | In Git |
|---|---|---|
| Processing chain and settings | `ifpm/`, `configs/` | yes |
| Report-figure scripts | `bin/visualize/` | yes |
| Tests | `tests/` | yes |
| One-time scripts | `tools/` | yes |
| Research records, dataset registry | `context/docs/` | yes |
| Raw downloaded data | `data/raw/<dataset_id>/`, `data/validation/<dataset_id>/` | no |
| Model outputs, maps, tables | `outputs/<boundary_id>/<experiment_id>/` | no |
| Packaged handovers | `exports/` | no |

- Every new real dataset gets a note in `context/docs/data-management/registry/`:
  source, version, access date, licence, download command, file size or checksum.
- Never commit credentials, cookies, API keys or absolute local paths.

## Study areas

- Active: Secocha, Peru (`secocha_reference_extent`) and Goslar, Germany.
- Frozen: former Peru area `peru_former` in
  `outputs/peru_former_pim_chain/`. Read only; never write new runs there.
- Background only: Zimbabwe `zimbabwe_upper_mzingwane`.

## Modelling rules

- Criteria are normalized to 0–1 and combined with the weights in
  `context/docs/research-map/DECISION_LOG.md`. Each run writes its weights to
  `run_manifest.json`.
- NoData stays NoData. Do not fill it with 0 or treat it as low risk.
- Rasters entering an overlay must share CRS, transform, resolution and extent with
  the reference grid.
- Coarse inputs (CHIRPS rainfall, SoilGrids) keep their native resolution as a
  stated limitation after resampling.
- Name criteria after what the data measure (for example road proximity is access,
  not socioeconomic vulnerability).
- Mining is an overlay, not a scored criterion.

## Workflow

- Run commands from the workspace root with `.venv/bin/python`; check a rerun with
  `python -m ifpm verify <area>` before replacing current outputs.
- Record new experiments in `context/docs/research-map/EXPERIMENTS.md` with the
  command, output folder and main result.
- Run the relevant tests in `tests/` after changing code.
