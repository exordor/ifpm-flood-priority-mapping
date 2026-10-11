# Dataset Registry: ESA WorldCover 2021 V1 Methodology Evidence

Status: downloaded and processed for V1 methodology evidence review (Zimbabwe background).

## Dataset Identity

- Dataset id: `esa_worldcover_2021_zimbabwe`
- Short name: ESA WorldCover 2021 v200
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
- Licence or terms: ESA WorldCover terms (CC BY 4.0); cite ESA WorldCover

## Acquisition

- Download command or manual steps:
  1. Run `.venv/bin/python bin/acquire/download_zimbabwe_methodology_inputs.py`.

## Files

- Checksum (SHA-256): `9bc24ff959920471b288814b0cf2c1cb4b554a75b033730241caec9033e8aab7`
- File size: 156,602,407 bytes
- CRS or georeferencing checked: yes; `EPSG:4326`, bounds `27E,-21S,30E,-18S`,
  native resolution approximately 10 m

## Processing And Use

- Raw data path: `data/raw/esa_worldcover_2021_zimbabwe/`
- Use: V1 class-area summaries and candidate evidence rows only
- Known limitations: land-cover class is not active mining truth; bare/sparse and quarry/industrial
  interpretations must be labelled as proxies
