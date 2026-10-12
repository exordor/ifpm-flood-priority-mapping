# Dataset Registry: HydroBASINS And HydroRIVERS Zimbabwe Prototype

Status: downloaded for boundary discovery; boundary not accepted. Zimbabwe is background only.

## Dataset Identity

- Dataset id: `hydrosheds_zimbabwe`
- Short name: HydroBASINS Africa and HydroRIVERS Africa
- Project role: hydrological boundary, river network, and possible sub-basin aggregation
- Study area: Zimbabwe / Upper Mzingwane Catchment prototype slice
- Spatial unit or mask: HydroBASINS-compatible catchment or sub-basin units, to be identified by
  boundary discovery
- Temporal coverage: static hydrographic baseline derived from HydroSHEDS products

## Source And Access

- Source organization: HydroSHEDS
- Source URL or portal:
  - HydroBASINS: `https://www.hydrosheds.org/products/hydrobasins`
  - HydroRIVERS: `https://www.hydrosheds.org/products/hydrorivers`
  - Product overview: `https://www.hydrosheds.org/products`
- Product/version: HydroBASINS standard Africa version 1c
- Access date: 2026-06-10
- Access method: direct product-page download
- Licence or terms: HydroSHEDS core product licence in the HydroSHEDS Technical Documentation;
  the downloaded ZIP did not include a separate licence text file
- Citation requirement: cite HydroSHEDS and Lehner & Grill (2013) where applicable

## Acquisition

- Source artifact name: `hybas_af_lev01-12_v1c.zip` (HydroBASINS Standard Africa, all levels)
- Download method: `curl` from the HydroBASINS product page; HydroRIVERS and pour points were not downloaded

## Download Record

- Attempt date: 2026-06-10
- Archive state: downloaded and verified
- Extraction state: complete

## Files

- Checksum (SHA-256):
  `6b331a6e89d56c3a542dcee39a7e6e8700d0cf7c94083c5946c7db0d262a48d6`
- Actual files or manifest: local manifest retained under
  `data/raw/hydrosheds_zimbabwe/hybas_af_lev01-12_v1c_manifest.txt`
- File size: 549,296,874 bytes
- File-count evidence: 85 extracted files. The unpacked copy under `extracted/` was removed on 2026-10-12 (byte-identical to the zip, which is kept).
- CRS or georeferencing checked: yes, inspected shapefiles reported EPSG:4326
- Geometry/raster integrity checked: candidate geometries inspected as valid

## Processing And Use

- Raw data path: `data/raw/hydrosheds_zimbabwe/`
- Scripts or commands used: `curl`, `shasum -a 256`, `unzip`, GeoPandas inspection
- Standardization/preprocessing notes: candidate HydroBASINS levels and ids were discovered; do
  not use boundaries for aggregation until accepted or waived
- Known limitations: product scale may not match local official catchment boundaries; river
  reaches are generalized and should not be treated as field-survey data
- Use: hydrological framework and candidate aggregation units for the Zimbabwe background prototype

