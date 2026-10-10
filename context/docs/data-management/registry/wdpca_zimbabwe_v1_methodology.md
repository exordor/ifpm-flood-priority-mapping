# Dataset Registry: WDPCA Zimbabwe V1 Methodology Evidence

Status: downloaded and processed for V1 methodology evidence review (Zimbabwe background).

## Dataset Identity

- Dataset id: `wdpca_zimbabwe_v1_methodology`
- Short name: Protected and Conserved Areas (WDPCA) in Zimbabwe
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
- Licence or terms: HDX record links to UNEP-WCMC WDPCA licence; cite UNEP-WCMC and IUCN

## Acquisition

- Download command or manual steps:
  1. Run `.venv/bin/python bin/acquire/download_v1_methodology_inputs.py`.

## Files

- Checksum (SHA-256): `5ea5be5ce3bf5efb741157eaa927d54afdac89d6293e9a9b02e893b6d64d65b3`
- File size: 733,184 bytes
- Readability checked: yes; GeoPackage opens as `points` and `polygons` layers, `EPSG:3857`

## Processing And Use

- Raw data path: `data/raw/wdpca_zimbabwe_v1_methodology/`
- Use: V1 protected-area overlap and context summary
- Known limitations: The V1
  summary records geometry overlap area, which may differ from source-reported area fields.
