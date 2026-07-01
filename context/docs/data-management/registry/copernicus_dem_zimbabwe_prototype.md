# Dataset Registry: Copernicus DEM Zimbabwe Prototype

Status: planned; not downloaded.

## Dataset Identity

- Dataset id: `copernicus_dem_zimbabwe_prototype`
- Short name: Copernicus DEM GLO-30 / GLO-90
- Data class: `LOCAL_DATA`
- Reusable download: yes, if used for DEM-based catchment delineation
- Project role: alternate DEM for outlet snapping and independent catchment delineation
- Study area: Zimbabwe / Upper Mzingwane candidate outlet discovery
- Spatial unit or mask: minimum bounding box around the accepted or provisional outlet search
  envelope
- Temporal coverage: static DEM product

## Source And Access

- Source organization: Copernicus / ESA
- Source URL or portal:
  `https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM`
- Product/version: GLO-30 or GLO-90, exact access route not selected
- Access date: checked 2026-06-11
- Access method: Copernicus Data Space, OpenTopography, or another documented official route
- Licence or terms: Copernicus DEM page reports worldwide free licence for GLO-30 and GLO-90
- Citation requirement: cite Copernicus DEM DOI `https://doi.org/10.5270/ESA-c5d3d65`
- Account, registration, or approval needed: depends on selected access route
- Redistribution allowed: not cleared for this project; review before release

## Download Plan

- Intended destination: `data/raw/copernicus_dem_zimbabwe_prototype/`
- Expected file types: GeoTIFF tiles or access-route-specific raster artifacts
- Source artifact name: not selected
- Expected file count: unknown until bounding box and route are selected
- Expected byte size: unknown until tile list is selected
- Download command or manual steps: select minimum bbox, record exact tile/artifact list, verify
  licence and size, download with overwrite guards, record checksums and manifest
- Rate limits or quotas: depends on selected access route
- Authentication handling: do not record tokens, cookies, or private links
- Temporary path, if any: `data/tmp/copernicus_dem_zimbabwe_prototype/`
- Cleanup needed after extraction: remove failed partials and record manifest

## Download Attempt State

- Attempt status: planned
- Attempt date:
- Failure reason, if any:
- Partial path, if any:
- Archive state: not downloaded
- Extraction state: not started
- Retry or resume safe: unknown until route is selected
- Cleanup/disposition:
- Cleanup date:

## Verification

- Download completed: no
- Verification date:
- Checksum scope: source raster artifacts
- Checksum algorithm: SHA-256
- Checksum command:
- Checksum value:
- Expected files or manifest:
- Actual files or manifest:
- Expected byte size:
- Actual byte size:
- File-count evidence:
- File-size evidence:
- CRS or georeferencing checked: no
- Geometry/raster integrity checked: no
- Licence/terms accepted: no

## Processing And Use

- Raw data path: `data/raw/copernicus_dem_zimbabwe_prototype/`
- Derived output path: `outputs/_archive/superseded_outlet_exploration_2026-06/candidate_outlet_discovery/` or a DEM-specific output directory
- Scripts or commands used:
- Standardization/preprocessing notes: Copernicus DEM is a DSM; document hydrological
  conditioning before using it for flow direction or outlet snapping
- Known limitations: DSM can include surface objects; DEM conditioning may be required
- Replacement or update rule: use SRTM as baseline if Copernicus DEM route is too complex
- Validation role: hydrological delineation support only

## Release Boundary

- May be committed: no
- May be used in public examples: no unless replaced by synthetic data
- May be included in release archives: no unless explicitly approved
- Public-safe summary available: yes
