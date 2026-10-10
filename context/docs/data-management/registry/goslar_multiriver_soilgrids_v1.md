# Goslar multi-river SoilGrids window

Source: https://files.isric.org/soilgrids/latest/data (SoilGrids 250 m mean clay/silt/sand/SOC, 0–5/5–15/15–30 cm). Access 2026-09-14; same source and Williams K method as the original Goslar chain. Public ISRIC data, CC-BY 4.0. Area 9.79,51.76,10.70,52.31 (extended flood comparison extent). Cropped 250 m windows; the `latest` version is pinned by per-file hash.

Destination: `data/raw/soilgrids_250m_goslar_multiriver_v1/`. Command: `.venv/bin/python bin/acquire/pull_goslar_soilgrids_window.py --extent 9.79 51.76 10.70 52.31 --out-dir data/raw/soilgrids_250m_goslar_multiriver_v1`. Used by: soil K in the Goslar multi-river full-extent chain.

Files: 12 property/depth windows and derived 0–30 cm K, shape 243×330; 72,621 valid native cells. Derived K SHA-256 `f4df49add7a8cebd23131df8daddf3db06d83d257108db8b560b8f258eb04e08`. Per-window hashes and diagnostics are in `soilgrids_goslar_diagnostics.json`.
