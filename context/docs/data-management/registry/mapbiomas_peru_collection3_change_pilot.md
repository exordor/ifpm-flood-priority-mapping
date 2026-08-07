# Dataset Registry: MapBiomas Peru Collection 3 Change Pilot

## Dataset Identity

- Dataset id: `mapbiomas_peru_collection3_change_pilot`
- Short name: MapBiomas Peru Collection 3 annual LULC
- Data class: `LOCAL_DATA`
- Reusable download: yes, for controlled Peru land-cover change experiments
- Project role: replace single-date BV and BE state proxies with observed annual land-cover transitions
- Study area: Arequipa Region prototype boundary `peru_hybas_l7_6070641200`
- Spatial unit or mask: current 30 m Peru reference grid after clipping and reprojection
- Temporal coverage: stable-window pilot years 2014-2016 and 2022-2024; source series is available annually from 1985 to 2024

## Source And Access

- Source organization: MapBiomas Peru
- Source URL or portal: `https://peru.mapbiomas.org/en/colecciones-de-mapbiomas-peru/`
- Product/version: Collection 3, integration v1, annual land-cover and land-use classification
- Access date: 2026-08-05
- Access method: direct public GeoTIFF download
- Licence or terms: Creative Commons CC-BY; source attribution required
- Citation requirement: `MapBiomas Peru Project - Collection 3 of the Annual Land Cover and Land Use Series for Peru, acquired 2026-08-05 through https://peru.mapbiomas.org/`
- Account, registration, or approval needed: none for direct GeoTIFF URLs
- Redistribution allowed: yes with CC-BY attribution; raw data remains local under the workspace release boundary

## Download Plan

- Intended destination: `data/raw/mapbiomas_peru_collection3_change_pilot/`
- Expected file types: LZW-compressed GeoTIFF plus SHA-256 sidecars
- Source artifact names:
  - `peru_collection3_integration_v1-classification_2014.tif`
  - `peru_collection3_integration_v1-classification_2015.tif`
  - `peru_collection3_integration_v1-classification_2016.tif`
  - `peru_collection3_integration_v1-classification_2022.tif`
  - `peru_collection3_integration_v1-classification_2023.tif`
  - `peru_collection3_integration_v1-classification_2024.tif`
- Expected file count: 6 GeoTIFFs
- Expected byte size: 634,310,355 bytes
- Download command or manual steps: `bin/data/download_mapbiomas_peru_change_pilot.sh`
- Rate limits or quotas: none identified; use resumable sequential downloads
- Authentication handling: not applicable
- Temporary path, if any: none; `curl --continue-at -` resumes an interrupted destination file
- Cleanup needed after extraction: none; GeoTIFFs are directly usable

## Download Attempt State

- Attempt status: complete
- Attempt date: 2026-08-05
- Failure reason, if any: none
- Partial path, if any: none
- Archive state: six of six downloaded and verified
- Extraction state: not applicable
- Retry or resume safe: yes
- Cleanup/disposition: retain verified raw GeoTIFFs and checksum sidecars

## Verification

- Download completed: yes
- Verification date: 2026-08-05
- Checksum scope: individual files
- Checksum algorithm: SHA-256
- Checksum command: `shasum -a 256 data/raw/mapbiomas_peru_collection3_change_pilot/*.tif`
- Checksum values:
  - 2014: `90449fcc0c53dfccfdbec17bf577410580509287bfbb990d3ae53aaf9707fd47`
  - 2015: `adf8760ff08f05de5aa1189d0bcdc25ab821def20876e4e2ec36d72d8c698c4c`
  - 2016: `2fb25a794c8af2827a2d7424c72220bedff6cb9b7eddd401b65a15c66f8c9b19`
  - 2022: `00fae2cc33f1dadf65adc821b4764eb07c1e69952a6329a9c91fcb16fed881cf`
  - 2023: `6694fead757601a8ec8532ec73f057b7155326966e7b2c68fb29bdb99c5816cc`
  - 2024: `307b17670cdd441f3457da6a47c48277b40d4e33ced3a4843daa509b53db4a21`
- Expected files or manifest: six annual GeoTIFFs and six `.sha256` sidecars
- Actual files or manifest: six GeoTIFFs and six `.sha256` sidecars
- Expected byte size: 634,310,355 bytes
- Actual byte size: 634,310,355 bytes
- File-count evidence: six readable single-band GeoTIFFs
- File-size evidence: exact source `Content-Length` matched for all six files
- CRS or georeferencing checked: yes; all six rasters are EPSG:4326 with identical extent and approximately 30 m angular resolution
- Geometry/raster integrity checked: yes; all six opened successfully and were aligned to the active EPSG:32718 reference grid with 100% study-area coverage
- Licence/terms accepted: yes

## Processing And Use

- Raw data path: `data/raw/mapbiomas_peru_collection3_change_pilot/`
- Derived output path: `outputs/mapbiomas_peru_collection3_change_pilot/`
- Scripts or commands used: download script above and `bin/factors/derive_mapbiomas_peru_change.py`
- Standardization/preprocessing notes: categorical classes are aligned to the active 30 m reference grid with nearest-neighbour resampling; 2014-2016 and 2022-2024 are each reduced by pixel majority before change detection
- Known limitations: 30 m thematic classifications are recommended by MapBiomas for use up to approximately 1:100,000; class changes can include classification uncertainty and require a transition-stability rule
- Replacement or update rule: use the latest internally consistent MapBiomas collection; do not mix collections in one change calculation
- Validation role: temporal evidence for BV and the built-up/agricultural parts of BE; not flood-model validation

## Release Boundary

- May be committed: no
- May be used in public examples: no unless explicitly approved
- May be included in release archives: no unless explicitly approved
- Public-safe summary available: this registry note
