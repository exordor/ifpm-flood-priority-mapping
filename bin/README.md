# bin/visualize: report-figure scripts

The processing chain is the config-driven package `ifpm/` (`python -m ifpm`, settings in
`configs/`). This folder keeps only the scripts that draw report figures from existing
outputs:

| Script | Figure |
|---|---|
| `plot_goslar_2024_location_map.py`, `plot_secocha_location_map.py` | Study-area location maps |
| `plot_goslar_pim_overview.py`, `plot_secocha_pim_overview.py` | Priority and five-criteria overview panels |
| `plot_secocha_standardization_detail.py` | Secocha standardization detail figure and xlsx table (needs `openpyxl`) |
| `export_peru_former_pim_criteria_maps.py`, `export_peru_former_raw_input_factor_maps.py`, `export_paper_style_single_maps.py` | Former Peru area report maps (shared map helpers) |
| `export_zimbabwe_reporting_maps.py`, `export_zimbabwe_input_evidence_maps.py`, `export_zimbabwe_mining_population_overlay.py` | Zimbabwe report maps |

Run from the workspace root, e.g. `.venv/bin/python bin/visualize/plot_secocha_pim_overview.py`.
Most of them write into `outputs/` (often `outputs/slide_ready_figures/`).

The processing, acquisition and packaging scripts that used to live here were replaced by
`ifpm` on 2026-10-12; recover one with `git show 206214e:bin/<folder>/<script>.py`.
