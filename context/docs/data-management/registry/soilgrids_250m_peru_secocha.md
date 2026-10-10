# SoilGrids 250 m snapshot — Peru Secocha

- Dataset id: `soilgrids_250m_peru_secocha`
- Source: ISRIC SoilGrids 250 m property VRTs, clay/silt/sand/SOC mean layers
- Source portal: `https://files.isric.org/soilgrids/latest/data/`
- Product slices: 0–5, 5–15, and 15–30 cm
- Licence: CC BY 4.0
- Access date: 2026-08-14
- Study area: `peru_secocha_a7367_reference_extent_v1` plus a 0.02° read halo
- Used by: soil K in the Secocha five-criterion PIM chain
- Destination: `data/raw/soilgrids_250m_peru_secocha/`
- Acquisition command: `.venv/bin/python bin/acquire/pull_secocha_soilgrids_window.py`
- Processing: Williams (1995) EPIC/RUSLE K function, depth-weighted to 0–30 cm
- K snapshot SHA-256: `bece595cfd4fc0ddd4d9294e59816c3cdd18f2ae484b4e9f2a8dad0b79d453a6`
- Snapshot evidence: 42 × 40 cells, 1,671 valid cells, US-unit K range
  0.151118–0.228283

The downloader writes per-file and final K-snapshot SHA-256 values, access date,
source window, native CRS, cell counts, and value diagnostics to
`soilgrids_peru_secocha_diagnostics.json`. The chain reads only this local
snapshot and fails explicitly if it is absent; it does not fall back to the
Goslar window or to a live remote layer.
