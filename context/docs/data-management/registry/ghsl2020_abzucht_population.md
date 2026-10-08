# GHSL 2020 population replacement scenario

- Classification: LOCAL_DATA. Dataset id: `ghsl2020_abzucht_population`.
- Product: JRC GHS-POP R2023A, epoch 2020, V1-0, 100 m Mollweide tile R3_C19.
- Metadata: https://data.jrc.ec.europa.eu/dataset/2ff68a52-5b5b-4a22-8f40-c41da8332cfe
- Source: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/GHS_POP_E2020_GLOBE_R2023A_54009_100/V1-0/tiles/GHS_POP_E2020_GLOBE_R2023A_54009_100_V1_0_R3_C19.zip
- Access date: 2026-09-14. Public, no account. CC BY 4.0; attribute European Commission/JRC and document clipping/reprojection.
- Download scope verified by HEAD: 41,019,822 bytes, one tile. Available disk >300 GB. Local archive plus clipped window expected <45 MB; full uncompressed tile will not be extracted.
- Destination: `data/raw/ghsl2020_abzucht_population/`. Partials: `data/tmp/ghsl2020_abzucht_population/`.
- Study area: full `goslar_abzucht_display_rectangle_v1` reference grid with native-window padding; not a new scientific boundary.
- Command: `.venv/bin/python bin/acquire/pull_abzucht_ghsl_population.py`.
- SHA-256, file sizes, actual NoData and native bounds: output `source_manifest.json` in the dataset directory after acquisition.
- Reusable: yes, as an attributed model-derived population scenario. Counts are per native 100 m cell, not observed residents at 30 m.
- Intended use: replace the whole population component in a separate sensitivity scenario; do not blend 2020 estimates into unpublished Zensus2022 cells or interpret unpublished census cells as zero.
- Retain Zensus2022 baseline and frozen normalization anchors. Any source-model/year effects belong to this scenario; it does not complete missing census observations.
