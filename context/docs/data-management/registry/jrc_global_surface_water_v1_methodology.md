# Dataset Registry: JRC Global Surface Water V1 Methodology Evidence

Status: downloaded and processed for controlled V1 methodology evidence review. This does not
authorize AHP overlay, flood-risk interpretation, or final thesis boundary claims.

## Dataset Identity

- Dataset id: `jrc_global_surface_water_v1_methodology`
- Short name: JRC Global Surface Water
- Data class: `LOCAL_DATA`
- Reusable download: yes, for V1 prototype evidence review
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
- Licence or terms: JRC GSW terms and citation requirements must be cited before public release
- Account, registration, or approval needed: none identified for these direct tile URLs

## Download Plan

- Intended destination: `data/raw/jrc_global_surface_water_v1_methodology/`
- Expected file types: GeoTIFF
- Expected file count: 5 tile layers
- Expected byte size: about 80 MB total from checked tile sizes
- Download command or manual steps:
  1. Run `.venv/bin/python bin/acquire/download_v1_methodology_inputs.py`.
  2. Record file size and SHA-256 in the full methodology source manifest.
- Temporary path, if any: `data/tmp/jrc_global_surface_water_v1_methodology/`

## Verification

- Download completed: yes
- Verification date: 2026-06-13
- Checksum scope: downloaded GSW layers
- Checksum algorithm: SHA-256
- Expected and actual manifest:
  `outputs/v1_full_methodology_evidence_sweep/source_manifest.csv`
- Actual file count: 5 GeoTIFF layers
- Actual total file size: 81,504,552 bytes
- CRS or georeferencing checked: yes; `EPSG:4326`, tile bounds `20E,-30S,30E,-20S`,
  native resolution `0.00025` degrees

## Processing And Use

- Raw data path: `data/raw/jrc_global_surface_water_v1_methodology/`
- Derived output path: `outputs/v1_full_methodology_evidence_sweep/`
- Scripts or commands used:
  - `.venv/bin/python bin/acquire/download_v1_methodology_inputs.py`
  - `.venv/bin/python bin/package/prepare_v1_full_methodology_evidence.py`
- Planned/actual use: V1 water occurrence, seasonality, recurrence, change, and transition
  summaries
- Known limitations: surface-water history is not event flood depth or hazard frequency; it is
  remote-sensing context for flood/wetland evidence review

## Release Boundary

- May be committed: no
- May be used in public examples: no unless replaced by synthetic or approved sample data
- Public-safe summary available: this registry note only
