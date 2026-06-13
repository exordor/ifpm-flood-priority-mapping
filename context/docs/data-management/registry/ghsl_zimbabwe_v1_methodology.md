# Dataset Registry: GHSL Zimbabwe V1 Methodology Evidence

Status: downloaded and processed for V1 full methodology evidence review. This does not authorize AHP overlay,
flood-risk interpretation, or final thesis boundary claims.

## Dataset Identity

- Dataset id: `ghsl_zimbabwe_v1_methodology`
- Short name: Copernicus Global Human Settlement Layer, Zimbabwe
- Data class: `LOCAL_DATA`
- Reusable download: yes, for V1 prototype evidence review
- Project role: socioeconomic exposure and built-up settlement cross-check
- Study area: Zimbabwe / V1 working catchment
- Spatial unit or mask: native GHSL grids summarized to V1
- Temporal coverage: 2025 epoch, release R2023A

## Source And Access

- Source organization: European Commission Joint Research Centre, distributed through HDX
- Source URL or portal: `https://data.humdata.org/dataset/zwe-ghsl`
- Direct source artifacts:
  - `https://data.humdata.org/dataset/9befff21-f81d-43f1-9fcb-15b09a5f9103/resource/ca0feb6a-149d-4dd0-afb1-a681bf37a8ee/download/ghs_built_s_e2025_r2023a_54009_100_v1_0_zwe.tif`
  - `https://data.humdata.org/dataset/9befff21-f81d-43f1-9fcb-15b09a5f9103/resource/a712437c-f0ce-46ea-a4c8-ec01a8041ee4/download/ghs_pop_e2025_r2023a_54009_100_v1_0_zwe.tif`
- Product/version: GHS Built-up Surface and GHS Population Grid, epoch 2025, R2023A, 100 m
- Access date: 2026-06-13
- Access method: direct public GeoTIFF URLs
- Licence or terms: CC BY via HDX package metadata; cite JRC/GHSL before public release
- Account, registration, or approval needed: none identified for these direct file URLs

## Download Plan

- Intended destination: `data/raw/ghsl_zimbabwe_v1_methodology/`
- Expected file types: GeoTIFF
- Expected file count: 2 rasters
- Download command or manual steps:
  1. Run `.venv/bin/python bin/download_v1_methodology_inputs.py`.
  2. Record file size and SHA-256 in the full methodology source manifest.
- Temporary path, if any: `data/tmp/ghsl_zimbabwe_v1_methodology/`

## Verification

- Download completed: yes
- Verification date: 2026-06-13
- Checksum scope: downloaded rasters
- Checksum algorithm: SHA-256
- Checksum values:
  - Built-up surface:
    `5f604c4992beb27df14f9f447caddef71540d8c17bbecce1a78d10c0b82820d1`
  - Population:
    `21ccdb3e2300cae9c739d0bbf2226f82c2bb738be6215f573554cf7318f7055e`
- File sizes:
  - Built-up surface: 12,958,740 bytes
  - Population: 37,893,059 bytes
- Expected and actual manifest:
  `outputs/v1_full_methodology_evidence_sweep/source_manifest.csv`
- CRS or georeferencing checked: yes; `ESRI:54009`, 100 m native resolution

## Processing And Use

- Raw data path: `data/raw/ghsl_zimbabwe_v1_methodology/`
- Derived output path: `outputs/v1_full_methodology_evidence_sweep/`
- Scripts or commands used:
  - `.venv/bin/python bin/download_v1_methodology_inputs.py`
  - `.venv/bin/python bin/prepare_v1_full_methodology_evidence.py`
- Planned/actual use: built-up surface and population exposure cross-check
- Known limitations: GHSL is exposure context only; it does not encode poverty, coping capacity,
  damage, or observed flood vulnerability.

## Release Boundary

- May be committed: no
- May be used in public examples: no unless replaced by synthetic or approved sample data
- Public-safe summary available: this registry note only
