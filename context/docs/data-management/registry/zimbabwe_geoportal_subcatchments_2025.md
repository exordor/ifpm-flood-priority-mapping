# Dataset Registry: Zimbabwe Geoportal Sub-Catchments 2025

Status: downloaded and verified for controlled boundary comparison.

## Dataset Identity

- Dataset id: `zimbabwe_geoportal_subcatchments_2025`
- Short name: Zimbabwe Geoportal Sub-Catchments
- Data class: `LOCAL_DATA`
- Reusable download: yes, as boundary-comparison evidence; not yet as an accepted model boundary
- Project role: local or management-style boundary candidate for Upper Mzingwane comparison
- Study area: Zimbabwe / Upper Mzingwane Catchment prototype slice
- Spatial unit or mask: Zimbabwe sub-catchment polygon layer
- Temporal coverage: static boundary layer; portal update date 2025-10-22

## Source And Access

- Source organization: Zimbabwe Geoportal
- Source URL or portal: `https://zimgeoportal.org.zw/datasets/sub-catchments/`
- Product/version: Sub-Catchments, version `v1.0`
- Access date: 2026-06-10
- Access method: authenticated portal page inspected in the in-app browser; Shapefile resource
  link downloaded after page verification
- Licence or terms: ODC-BY 1.0 as stated on the dataset page
- Citation requirement: cite Zimbabwe Geoportal dataset page and licence
- Account, registration, or approval needed: login required to download
- Redistribution allowed: unknown for project release; review before public packaging

## Download Plan

- Intended destination: `data/raw/zimbabwe_geoportal_subcatchments_2025/`
- Expected file types: GeoJSON or zipped Shapefile
- Source artifact name: portal resource `sub-catchment_shp` or `sub-catchment_geojson`
- Expected file count: one downloaded resource archive or file
- Expected byte size: Shapefile resource about `614.9 KB`; GeoJSON resource about `2.2 MB`
- Download command or manual steps:
  1. Open `https://zimgeoportal.org.zw/datasets/sub-catchments/` in the in-app browser.
  2. Confirm that the page is the Sub-Catchments dataset page and lists Shapefile and GeoJSON
     resources.
  3. Use the Shapefile resource link exposed on that page.
  4. Download the resource directly to
     `data/raw/zimbabwe_geoportal_subcatchments_2025/sub_catchments-1761163234.zip`.
  5. Record actual file name, byte size, checksum, extraction state, CRS, and geometry check.
- Direct resource URL handling: exact object URL is intentionally not recorded in committed files;
  use portal page, resource name, checksum, and file-size evidence for reproducibility
- Rate limits or quotas: unknown; one small manual download only
- Authentication handling: do not store cookies, tokens, passwords, or private links in files
- Temporary path, if any: none used for the completed download
- Cleanup needed after extraction: remove failed partials and keep source archive plus extracted
  Shapefile components

## Download Attempt State

- Attempt status: completed
- Attempt date: 2026-06-10
- Failure reason, if any: not applicable
- Partial path, if any: none
- Archive state: downloaded
- Extraction state: extracted under `data/raw/zimbabwe_geoportal_subcatchments_2025/extracted/`
- Retry or resume safe: manual inspection required before overwrite
- Cleanup/disposition: no failed partials found
- Cleanup date: 2026-06-10

## Verification

- Download completed: yes
- Verification date: 2026-06-10
- Checksum scope: source archive or downloaded file
- Checksum algorithm: SHA-256
- Checksum command:
  `shasum -a 256 data/raw/zimbabwe_geoportal_subcatchments_2025/sub_catchments-1761163234.zip`
- Checksum value:
  `fb5a3528ca677f420e5030f146a7699027e93c765fcebe7ef45a59611b6f0cd2`
- Expected files or manifest: zipped Shapefile resource
- Actual files or manifest:
  - `sub_catchments-1761163234.zip`
  - `extracted/sub_catchments.cpg`
  - `extracted/sub_catchments.dbf`
  - `extracted/sub_catchments.prj`
  - `extracted/sub_catchments.qmd`
  - `extracted/sub_catchments.shp`
  - `extracted/sub_catchments.shx`
- Expected byte size: about `614.9 KB` for Shapefile or `2.2 MB` for GeoJSON
- Actual byte size: `629658` bytes
- File-count evidence: one archive plus six extracted Shapefile sidecar files
- File-size evidence: `stat -f '%z bytes %Sm'` returned `629658 bytes`
- CRS or georeferencing checked: yes; extracted Shapefile CRS is `EPSG:4326`
- Geometry/raster integrity checked: yes; 47 polygon features, 47 valid, 0 empty
- Licence/terms accepted: page-level licence recorded as ODC-BY 1.0; no separate download terms
  prompt was observed

## Processing And Use

- Raw data path: `data/raw/zimbabwe_geoportal_subcatchments_2025/`
- Derived output path: `outputs/zimbabwe_geoportal_subcatchments_2025/`
- Scripts or commands used:
  - `curl -L --fail --retry 3`
  - `unzip`
  - one-off `uv run --with geopandas --with pyogrio --with shapely --with pyproj --with pandas`
    inspection commands
- Standardization/preprocessing notes: compared sub-catchment names, area, geometry, and anchor
  containment against HydroBASINS candidate `HYBAS_ID=1071528840`
- Known limitations: portal lists organisation/source as unspecified; login is required to access
  the dataset page; the Geoportal `Upper Mzingwane` feature is about `7321.5 km2`, so it is a
  broader named sub-catchment unit than the reported but source/geometry-unresolved
  `~2138 km2` Upper Mzingwane reference
- Replacement or update rule: replace if mentor supplies a more authoritative local boundary
- Validation role: boundary decision evidence, not flood-risk validation evidence

## Release Boundary

- May be committed: no
- May be used in public examples: no unless replaced by synthetic or approved sample data
- May be included in release archives: no unless explicitly approved
- Public-safe summary available: yes, this registry note without downloaded files
