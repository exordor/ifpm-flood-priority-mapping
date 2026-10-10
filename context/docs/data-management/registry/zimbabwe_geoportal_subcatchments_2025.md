# Dataset Registry: Zimbabwe Geoportal Sub-Catchments 2025

Status: downloaded and verified for boundary comparison (Zimbabwe background only).

## Dataset Identity

- Dataset id: `zimbabwe_geoportal_subcatchments_2025`
- Short name: Zimbabwe Geoportal Sub-Catchments
- Project role: local or management-style boundary candidate for Upper Mzingwane comparison
- Study area: Zimbabwe / Upper Mzingwane Catchment prototype slice
- Spatial unit or mask: Zimbabwe sub-catchment polygon layer
- Temporal coverage: static boundary layer; portal update date 2025-10-22

## Source And Access

- Source organization: Zimbabwe Geoportal
- Source URL or portal: `https://zimgeoportal.org.zw/datasets/sub-catchments/`
- Product/version: Sub-Catchments, version `v1.0`
- Access date: 2026-06-10
- Access method: Shapefile resource link on the dataset page (portal login required)
- Licence or terms: ODC-BY 1.0 as stated on the dataset page
- Citation requirement: cite Zimbabwe Geoportal dataset page and licence

## Acquisition

- Source artifact name: portal resource `sub-catchment_shp` or `sub-catchment_geojson`
- Download: Shapefile resource from the dataset page, saved as
  `data/raw/zimbabwe_geoportal_subcatchments_2025/sub_catchments-1761163234.zip`
  (`curl -L --fail --retry 3`, then `unzip`)

## Download Record

- Attempt date: 2026-06-10
- Archive state: downloaded
- Extraction state: extracted under `data/raw/zimbabwe_geoportal_subcatchments_2025/extracted/`

## Files

- Checksum (SHA-256):
  `fb5a3528ca677f420e5030f146a7699027e93c765fcebe7ef45a59611b6f0cd2`
- Actual files or manifest:
  - `sub_catchments-1761163234.zip`
  - `extracted/sub_catchments.cpg`
  - `extracted/sub_catchments.dbf`
  - `extracted/sub_catchments.prj`
  - `extracted/sub_catchments.qmd`
  - `extracted/sub_catchments.shp`
  - `extracted/sub_catchments.shx`
- File size: 629,658 bytes
- File-count evidence: one archive plus six extracted Shapefile sidecar files
- CRS or georeferencing checked: yes; extracted Shapefile CRS is `EPSG:4326`
- Geometry/raster integrity checked: yes; 47 polygon features, 47 valid, 0 empty

## Processing And Use

- Raw data path: `data/raw/zimbabwe_geoportal_subcatchments_2025/`
- Derived output path: `outputs/zimbabwe_geoportal_subcatchments_2025/`
- Standardization/preprocessing notes: compared sub-catchment names, area, geometry, and anchor
  containment against HydroBASINS candidate `HYBAS_ID=1071528840`
- Known limitations: portal lists organisation/source as unspecified; login is required to access
  the dataset page; the Geoportal `Upper Mzingwane` feature is about `7321.5 km2`, so it is a
  broader named sub-catchment unit than the reported but source/geometry-unresolved
  `~2138 km2` Upper Mzingwane reference
- Use: boundary comparison for the Zimbabwe prototype
