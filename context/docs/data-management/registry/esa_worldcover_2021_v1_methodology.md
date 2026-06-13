# Dataset Registry: ESA WorldCover 2021 V1 Methodology Evidence

Status: downloaded and processed for controlled V1 methodology evidence review. This does not
authorize AHP overlay, flood-risk interpretation, or final thesis boundary claims.

## Dataset Identity

- Dataset id: `esa_worldcover_2021_v1_methodology`
- Short name: ESA WorldCover 2021 v200
- Data class: `LOCAL_DATA`
- Reusable download: yes, for V1 prototype evidence review
- Project role: land-use, bare/sparse-ground, vegetation, water/wetland, and rehabilitation
  candidate evidence
- Study area: V1 working catchment and surrounding tile coverage
- Spatial unit or mask: native WorldCover tile clipped or summarized to V1
- Temporal coverage: 2021 land-cover map

## Source And Access

- Source organization: ESA WorldCover consortium
- Source URL or portal: `https://esa-worldcover.org/en/data-access`
- Direct source artifact:
  `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_S21E027_Map.tif`
- Product/version: ESA WorldCover 10 m 2021 v200
- Access date: 2026-06-13
- Access method: direct public S3 GeoTIFF URL
- Licence or terms: ESA WorldCover terms must be cited before public release
- Account, registration, or approval needed: none identified for this direct tile URL

## Download Plan

- Intended destination: `data/raw/esa_worldcover_2021_v1_methodology/`
- Expected file types: GeoTIFF
- Expected file count: 1 tile
- Expected byte size: about 157 MB
- Download command or manual steps:
  1. Run `.venv/bin/python bin/download_v1_methodology_inputs.py`.
  2. Record file size and SHA-256 in the full methodology source manifest.
- Temporary path, if any: `data/tmp/esa_worldcover_2021_v1_methodology/`

## Verification

- Download completed: yes
- Verification date: 2026-06-13
- Checksum scope: downloaded tile
- Checksum algorithm: SHA-256
- Checksum value: `9bc24ff959920471b288814b0cf2c1cb4b554a75b033730241caec9033e8aab7`
- Expected and actual manifest:
  `outputs/v1_full_methodology_evidence_sweep/source_manifest.csv`
- Actual file size: 156,602,407 bytes
- CRS or georeferencing checked: yes; `EPSG:4326`, bounds `27E,-21S,30E,-18S`,
  native resolution approximately 10 m

## Processing And Use

- Raw data path: `data/raw/esa_worldcover_2021_v1_methodology/`
- Derived output path: `outputs/v1_full_methodology_evidence_sweep/`
- Scripts or commands used:
  - `.venv/bin/python bin/download_v1_methodology_inputs.py`
  - `.venv/bin/python bin/prepare_v1_full_methodology_evidence.py`
- Planned/actual use: V1 class-area summaries and candidate evidence rows only
- Known limitations: land-cover class is not active mining truth; bare/sparse and quarry/industrial
  interpretations must be labelled as proxies

## Release Boundary

- May be committed: no
- May be used in public examples: no unless replaced by synthetic or approved sample data
- Public-safe summary available: this registry note only
