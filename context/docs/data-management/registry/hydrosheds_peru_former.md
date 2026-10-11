# Dataset Registry: HydroBASINS South America Peru Prototype

Status: downloaded 2026-06-30 for Peru boundary discovery; source of the former Peru study area
boundary `peru_former` (frozen).

## Dataset Identity

- Dataset id: `hydrosheds_peru_former`
- Short name: HydroBASINS standard South America
- Project role: hydrological boundary discovery for the Peru analogue catchment (IFPM-D02)
- Study area: Arequipa-Moquegua-Tacna three-department envelope, Peru
- Spatial unit or mask: HydroBASINS level-7 candidate basins
- Temporal coverage: static hydrographic baseline derived from HydroSHEDS products

## Source And Access

- Source organization: HydroSHEDS
- Source URL or portal: `https://www.hydrosheds.org/products/hydrobasins`
- Source artifact: `https://data.hydrosheds.org/file/hydrobasins/standard/hybas_sa_lev01-12_v1c.zip`
- Product/version: HydroBASINS standard South America, all levels 1-12, version 1c
- Access date: 2026-06-30
- Access method: direct product-page HTTPS download; no login required
- Licence or terms: HydroSHEDS core product licence in the HydroSHEDS Technical Documentation
- Citation requirement: cite HydroSHEDS and Lehner & Grill (2013) where applicable

## Acquisition

- Source artifact name: `hybas_sa_lev01-12_v1c.zip`
- Download command: `curl -L --fail` of the source artifact URL above

## Download Record

- Attempt date: 2026-06-30
- Archive state: downloaded and verified
- Extraction state: complete (all levels 1-12 extracted under `extracted/`)

## Files

- Checksum (SHA-256): `fb012e48419bda0a7f4d0ebc56efcd906ad0e3bde324b9c70fac9693e2d21a72`
- File size: 334,160,720 bytes
- File-count evidence: 12 levels (lev01-lev12) extracted, each with shp/shx/dbf/prj/sbx/sbn/xml
- CRS or georeferencing checked: yes, shapefiles report EPSG:4326
- Geometry/raster integrity checked: candidate L7 basins inspected as valid

## Processing And Use

- Raw data path: `data/raw/hydrosheds_peru_former/`
- Derived output path: `outputs/peru_former_boundary_discovery/`
- Scripts or commands used: `bin/acquire/discover_peru_former_candidate_basins.py`
- Known limitations: the three-department envelope mixes Pacific-slope and highland drainage
