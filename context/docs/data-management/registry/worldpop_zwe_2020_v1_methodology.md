# Dataset Registry: WorldPop Zimbabwe 2020 V1 Methodology Evidence

Status: downloaded and processed for V1 methodology evidence review (Zimbabwe background).

## Dataset Identity

- Dataset id: `worldpop_zwe_2020_v1_methodology`
- Short name: WorldPop Zimbabwe 2020 population
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
- Licence or terms: WorldPop terms; cite WorldPop

## Acquisition

- Download command or manual steps:
  1. Run `.venv/bin/python bin/acquire/download_v1_methodology_inputs.py`.

## Files

- Checksum (SHA-256): `80f5a25269c85f5a4901beb6557936342c8eb90fae8f793fa47bbf3ddccf91c6`
- File size: 192,412,178 bytes
- CRS or georeferencing checked: yes; `EPSG:4326`, Zimbabwe bounds, native resolution
  approximately 100 m

## Processing And Use

- Raw data path: `data/raw/worldpop_zwe_2020_v1_methodology/`
- Use: V1 population count and exposure summaries
- Known limitations: 2020 population count is an exposure proxy, not direct flood vulnerability
  or poverty evidence
