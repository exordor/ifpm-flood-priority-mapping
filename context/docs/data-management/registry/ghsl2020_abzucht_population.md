# GHSL 2020 population replacement scenario

- Dataset id: `ghsl2020_abzucht_population`
- Product: JRC GHS-POP R2023A, epoch 2020, V1-0, 100 m Mollweide tile R3_C19.
- Metadata: https://data.jrc.ec.europa.eu/dataset/2ff68a52-5b5b-4a22-8f40-c41da8332cfe
- Source: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/GHS_POP_E2020_GLOBE_R2023A_54009_100/V1-0/tiles/GHS_POP_E2020_GLOBE_R2023A_54009_100_V1_0_R3_C19.zip
- Access date: 2026-09-14. Public, no account. CC BY 4.0; attribute European Commission/JRC.
- Study area: `goslar_abzucht_display_rectangle` reference grid with native-window padding.
- Command: `.venv/bin/python bin/acquire/pull_abzucht_ghsl_population.py`.
  (Script removed 2026-10-11; recover with `git show 6e2ed8b:bin/acquire/pull_abzucht_ghsl_population.py`.)
- Local path: `data/raw/ghsl2020_abzucht_population/`
- Files: `GHS_POP_E2020_GLOBE_R2023A_54009_100_V1_0_R3_C19.zip` (41,019,822 bytes, SHA-256
  `736d07c99453834235d62c2c9eab9f37450809d6621b9ea8d6255e4ae7f44dd1`); clipped
  `ghsl2020_population_native_100m.tif` (36,427 bytes, SHA-256
  `574dd418d1aaec026f68496e0f0e83a3bfaa4b1bf6069c46d5c0c700a68cc473`). Native CRS ESRI:54009,
  100 m, NoData -200; details in `source_manifest.json`.
- Used by: the Abzucht population-replacement scenario (`gap_repair`, `input_completion`),
  which replaces the whole population component; Zensus 2022 stays the baseline and 2020
  estimates are not blended into unpublished Zensus cells.
