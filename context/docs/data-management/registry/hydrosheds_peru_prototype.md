# Dataset Registry: HydroBASINS South America Peru Prototype

Status: downloaded for Peru boundary discovery; no Peru boundary accepted.

## Dataset Identity

- Dataset id: `hydrosheds_peru_prototype`
- Short name: HydroBASINS standard South America
- Data class: `LOCAL_DATA`
- Reusable download: yes, if the Peru side proceeds
- Project role: hydrological boundary discovery for the Peru analogue catchment (IFPM-D02)
- Study area: Arequipa-Moquegua-Tacna three-department envelope, Peru
- Spatial unit or mask: HydroBASINS-compatible candidate basins, to be identified by boundary
  discovery (not yet accepted)
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
- Account, registration, or approval needed: none
- Redistribution allowed: not yet confirmed; governed by HydroSHEDS licence agreement

## Download Plan

- Intended destination: `data/raw/hydrosheds_peru_prototype/`
- Expected file types: compressed archive with vector layers and sidecar files
- Source artifact name: `hybas_sa_lev01-12_v1c.zip`
- Expected byte size: `334160720` bytes
- Download command or manual steps: guarded `curl` under the boundary-discovery authorization
  `context/docs/data-management/preflight/peru_hydrobasins_boundary_discovery_authorization_2026-06-30.md`
- Rate limits or quotas: none encountered
- Authentication handling: no credentials expected

## Download Attempt State

- Attempt status: complete for boundary discovery
- Attempt date: 2026-06-30
- Archive state: downloaded and verified
- Extraction state: complete (all levels 1-12 extracted under `extracted/`)
- Cleanup/disposition: source archive, checksum, and extracted shapefiles retained under ignored
  `data/raw/`

## Verification

- Download completed: yes
- Verification date: 2026-06-30
- Checksum algorithm: SHA-256
- Checksum value: `fb012e48419bda0a7f4d0ebc56efcd906ad0e3bde324b9c70fac9693e2d21a72`
- Actual byte size: `334160720` bytes
- File-count evidence: 12 levels (lev01-lev12) extracted, each with shp/shx/dbf/prj/sbx/sbn/xml
- CRS or georeferencing checked: yes, shapefiles report EPSG:4326
- Geometry/raster integrity checked: candidate L7 basins inspected as valid

## Processing And Use

- Raw data path: `data/raw/hydrosheds_peru_prototype/`
- Derived output path: `outputs/peru_boundary_discovery/`
- Scripts or commands used: `bin/acquire/discover_peru_candidate_basins.py`
- Authorization: `context/docs/data-management/preflight/peru_hydrobasins_boundary_discovery_authorization_2026-06-30.md`
- Known limitations: the three-department envelope mixes Pacific-slope and highland drainage;
  candidate basins need catchment-vs-region bias review before acceptance
- Replacement or update rule: replace if mentor names a specific Peru site or supplies an
  authoritative administrative polygon
- Validation role: hydrological framework for boundary discovery, not validation evidence

## Release Boundary

- May be committed: no
- May be used in public examples: no unless replaced by synthetic or approved sample data
- May be included in release archives: no unless explicitly approved
- Public-safe summary available: yes, this registry note without downloaded files
