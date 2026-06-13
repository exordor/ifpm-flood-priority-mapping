# Dataset Registry: WorldPop Zimbabwe 2020 V1 Methodology Evidence

Status: downloaded and processed for controlled V1 methodology evidence review. This does not
authorize AHP overlay, flood-risk interpretation, or final thesis boundary claims.

## Dataset Identity

- Dataset id: `worldpop_zwe_2020_v1_methodology`
- Short name: WorldPop Zimbabwe 2020 population
- Data class: `LOCAL_DATA`
- Reusable download: yes, for V1 prototype evidence review
- Project role: socioeconomic vulnerability and exposure candidate evidence
- Study area: Zimbabwe / V1 working catchment
- Spatial unit or mask: native WorldPop grid summarized to V1
- Temporal coverage: 2020

## Source And Access

- Source organization: WorldPop
- Source URL or portal: `https://hub.worldpop.org/`
- Direct source artifact:
  `https://data.worldpop.org/GIS/Population/Global_2000_2020/2020/ZWE/zwe_ppp_2020_UNadj.tif`
- Product/version: Zimbabwe 2020 unconstrained population count, UN adjusted
- Access date: 2026-06-13
- Access method: direct public GeoTIFF URL
- Licence or terms: WorldPop terms and citation requirements must be cited before public release
- Account, registration, or approval needed: none identified for this direct file URL

## Download Plan

- Intended destination: `data/raw/worldpop_zwe_2020_v1_methodology/`
- Expected file types: GeoTIFF
- Expected file count: 1 raster
- Expected byte size: about 192 MB
- Download command or manual steps:
  1. Run `.venv/bin/python bin/download_v1_methodology_inputs.py`.
  2. Record file size and SHA-256 in the full methodology source manifest.
- Temporary path, if any: `data/tmp/worldpop_zwe_2020_v1_methodology/`

## Verification

- Download completed: yes
- Verification date: 2026-06-13
- Checksum scope: downloaded raster
- Checksum algorithm: SHA-256
- Checksum value: `80f5a25269c85f5a4901beb6557936342c8eb90fae8f793fa47bbf3ddccf91c6`
- Expected and actual manifest:
  `outputs/v1_full_methodology_evidence_sweep/source_manifest.csv`
- Actual file size: 192,412,178 bytes
- CRS or georeferencing checked: yes; `EPSG:4326`, Zimbabwe bounds, native resolution
  approximately 100 m

## Processing And Use

- Raw data path: `data/raw/worldpop_zwe_2020_v1_methodology/`
- Derived output path: `outputs/v1_full_methodology_evidence_sweep/`
- Scripts or commands used:
  - `.venv/bin/python bin/download_v1_methodology_inputs.py`
  - `.venv/bin/python bin/prepare_v1_full_methodology_evidence.py`
- Planned/actual use: V1 population count and exposure summaries
- Known limitations: 2020 population count is an exposure proxy, not direct flood vulnerability
  or poverty evidence

## Release Boundary

- May be committed: no
- May be used in public examples: no unless replaced by synthetic or approved sample data
- Public-safe summary available: this registry note only
