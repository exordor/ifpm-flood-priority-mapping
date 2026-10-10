# Dataset Registry: JRC Global Surface Water V1 Methodology Evidence

Status: downloaded and processed for V1 methodology evidence review (Zimbabwe background).

## Dataset Identity

- Dataset id: `jrc_global_surface_water_v1_methodology`
- Short name: JRC Global Surface Water
- Project role: remote-sensing surface-water, wetland/water proximity, and flood-hazard context
  candidate evidence
- Study area: V1 working catchment within `20E_20S` tile
- Spatial unit or mask: native GSW tile clipped or summarized to V1
- Temporal coverage: source product tile generation as provided by JRC/Google storage artifact

## Source And Access

- Source organization: European Commission Joint Research Centre
- Source URL or portal: `https://global-surface-water.appspot.com/download`
- Direct source artifacts:
  - `https://storage.googleapis.com/global-surface-water/downloads/occurrence/occurrence_20E_20S.tif`
  - `https://storage.googleapis.com/global-surface-water/downloads/seasonality/seasonality_20E_20S.tif`
  - `https://storage.googleapis.com/global-surface-water/downloads/recurrence/recurrence_20E_20S.tif`
  - `https://storage.googleapis.com/global-surface-water/downloads/change/change_20E_20S.tif`
  - `https://storage.googleapis.com/global-surface-water/downloads/transitions/transitions_20E_20S.tif`
- Product/version: Global Surface Water tile artifacts available from public download storage
- Access date: 2026-06-13
- Access method: direct public GeoTIFF URLs
- Licence or terms: JRC GSW terms; cite JRC Global Surface Water

## Acquisition

- Download command or manual steps:
  1. Run `.venv/bin/python bin/acquire/download_v1_methodology_inputs.py`.

## Files

- File count: 5 GeoTIFF layers, 81,504,552 bytes in total
- Checksums (SHA-256, computed 2026-10-10 from the local files):
  - `change_20E_20S.tif` (19,058,378 bytes): `6aa950cec88395c144a61576c62cf5da273c91f5624532aa6f9a05e64e4e34ce`
  - `occurrence_20E_20S.tif` (18,192,530 bytes): `f6ef8941ac345315d647f61e1b9ccaa8d4e37c008e5c3b57e670ca52425ff522`
  - `recurrence_20E_20S.tif` (17,283,404 bytes): `5ceed324fa0ecfea658c14b9c006cc593832f3f8bdafe03c968407b3e8e17dd0`
  - `seasonality_20E_20S.tif` (13,239,208 bytes): `2b77a3975570f500a7bfaf79098b2fe87378e2a2f663396e435cf89b7c20d054`
  - `transitions_20E_20S.tif` (13,731,032 bytes): `83fb3eb19fa84b063e9e26e237b39181cd8c7fac049ce35c2769d10e6b15a64c`
- CRS or georeferencing checked: yes; `EPSG:4326`, tile bounds `20E,-30S,30E,-20S`,
  native resolution `0.00025` degrees

## Processing And Use

- Raw data path: `data/raw/jrc_global_surface_water_v1_methodology/`
- Use: V1 water occurrence, seasonality, recurrence, change, and transition
  summaries
- Known limitations: surface-water history is not event flood depth or hazard frequency; it is
  remote-sensing context for flood/wetland evidence review
