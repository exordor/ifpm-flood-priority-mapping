# Dataset Registry: WDPCA Zimbabwe V1 Methodology Evidence

Status: downloaded and processed for controlled V1 methodology evidence review. This does not
authorize AHP overlay, flood-risk interpretation, or final thesis boundary claims.

## Dataset Identity

- Dataset id: `wdpca_zimbabwe_v1_methodology`
- Short name: Protected and Conserved Areas (WDPCA) in Zimbabwe
- Data class: `LOCAL_DATA`
- Reusable download: yes, for environmental-sensitivity evidence review
- Project role: official protected/conserved-area candidate evidence
- Study area: Zimbabwe / V1 working catchment
- Spatial unit or mask: Zimbabwe protected/conserved-area polygons and points screened against V1
- Temporal coverage: HDX dataset date range as recorded by provider; monthly-updated WDPCA
  source

## Source And Access

- Source organization: UNEP-WCMC and IUCN, through HDX dataset record
- Source URL or portal:
  `https://data.humdata.org/api/3/action/package_show?id=unep_wdpca_zwe`
- Direct source artifact:
  `https://data.humdata.org/dataset/ef375df9-81d3-4cd9-9461-2aa6cda6ae45/resource/a15eef56-23bf-4969-a07c-6d98911c2825/download/protected_conserved_areas_wdpca.gpkg`
- Product/version: Protected and Conserved Areas (WDPCA) in Zimbabwe, HDX record updated
  2026-06-10
- Access date: 2026-06-13
- Access method: HDX CKAN API and direct GeoPackage URL
- Licence or terms: HDX record links to UNEP-WCMC WDPCA licence; cite UNEP-WCMC and IUCN before
  public release
- Account, registration, or approval needed: none identified for the HDX direct resource URL

## Download Plan

- Intended destination: `data/raw/wdpca_zimbabwe_v1_methodology/`
- Expected file types: GeoPackage
- Expected file count: 1
- Download command or manual steps:
  1. Run `.venv/bin/python bin/acquire/download_v1_methodology_inputs.py`.
  2. Run `.venv/bin/python bin/package/prepare_v1_full_methodology_evidence.py`.
- Temporary path, if any: `data/tmp/wdpca_zimbabwe_v1_methodology/`

## Verification

- Download completed: yes
- Verification date: 2026-06-13
- Checksum scope: downloaded GeoPackage
- Checksum algorithm: SHA-256
- Checksum value: `5ea5be5ce3bf5efb741157eaa927d54afdac89d6293e9a9b02e893b6d64d65b3`
- Expected and actual manifest:
  `outputs/v1_full_methodology_evidence_sweep/source_manifest.csv`
- Actual file size: 733,184 bytes
- Readability checked: yes; GeoPackage opens as `points` and `polygons` layers, `EPSG:3857`

## Processing And Use

- Raw data path: `data/raw/wdpca_zimbabwe_v1_methodology/`
- Derived output path: `outputs/v1_full_methodology_evidence_sweep/`
- Planned/actual use: V1 protected-area overlap and context evidence in
  `outputs/v1_full_methodology_evidence_sweep/v1_wdpca_protected_area_summary.csv`
- Known limitations: WDPCA must be cited and licensing reviewed before public release. The V1
  summary records geometry overlap area, which may differ from source-reported area fields.

## Release Boundary

- May be committed: no raw data
- May be used in public examples: no unless replaced by synthetic or approved sample data
- Public-safe summary available: this registry note only
