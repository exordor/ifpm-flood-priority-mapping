# Dataset Registry: SoilGrids 250m Sediment Candidate

Status: DRAFT candidate registry. Not authorized for download. Created as P2 R2.1 preflight
scaffolding so a scoped download can be authorized quickly once the mentor confirms a
SoilGrids-based K-factor and the R-factor formula decision. No real data has been downloaded for
this dataset id.

## Dataset Identity

- Dataset id: `soilgrids_250m_sediment_candidate`
- Short name: SoilGrids 250m (ISRIC)
- Data class: `LOCAL_DATA`
- Reusable download: yes, for soil-erodibility (K-factor) and soil-property context
- Project role: soil erodibility input for the USLE/RUSLE sediment-risk factor K; soil texture
  and organic carbon context for infiltration-capacity and environmental-sensitivity evidence
- Study area: V1 working catchment and Zimbabwe context
- Spatial unit or mask: SoilGrids global 250 m grid, clipped to V1 and reported as 250 m
  diagnostics or V1/sub-basin zonal summary; explicitly NOT resampled to the V1 30 m terrain
  grid as pixel-level truth
- Temporal coverage: SoilGrids contemporary soil properties (2017/2020 release as available)

## Source And Access

- Source organization: ISRIC - World Soil Information
- Source URL or portal:
  - SoilGrids page: `https://www.isric.org/explore/soilgrids`
  - SoilData access: `https://soilgrids.org/` (WCS / COG / download)
- Product/version: SoilGrids 250m, latest public release at access date (soil properties:
  clay, silt, sand, organic carbon, bulk density at standard depths)
- Access date: not yet accessed; intended access date to be recorded at authorization
- Access method: WCS request, COG read, or direct download of the scoped V1 bounding box
- Licence or terms: CC BY 4.0; attribution to ISRIC required
- Citation requirement: cite ISRIC SoilGrids and the access date
- Account, registration, or approval needed: none identified for public WCS/COG access
- Redistribution allowed: yes under CC BY 4.0 with attribution

## Download Plan

- Intended destination: `data/raw/soilgrids_250m_sediment_candidate/`
- Expected file types: GeoTIFF (COG) per soil property per depth
- Source artifact name: SoilGrids layers for clay, silt, sand, organic carbon at mean-depth
  slices, scoped to the V1 bounding box
- Expected file count: order of 10-30 GeoTIFFs depending on properties and depths selected
- Expected byte size: tens to low hundreds of MB for a scoped V1 subset
- Download command or manual steps: WCS GetCoverage or COG windowed read for the V1 bounding box;
  to be specified precisely at authorization
- Rate limits or quotas: ISRIC may throttle heavy WCS use; scoped subset should be modest
- Authentication handling: none for public access; no credentials to store
- Temporary path, if any: `data/tmp/soilgrids_250m_sediment_candidate/`
- Cleanup needed after extraction: keep only V1-scoped layers; remove any global layer if
  accidentally downloaded

## Download Attempt State

- Attempt status: planned (draft, not authorized)
- Archive state: not downloaded
- Retry or resume safe: yes (WCS/COG request can be re-submitted)

## Verification

- Download completed: no
- Verification date: not applicable
- Checksum scope: downloaded GeoTIFF files
- Checksum algorithm: SHA-256 (to be recorded post-download)
- Expected files or manifest: to be confirmed at access
- CRS or georeferencing checked: to be checked post-download (expect EPSG:4326 or equal-area)
- Geometry/raster integrity checked: to be checked post-download

## Processing And Use

- Raw data path: `data/raw/soilgrids_250m_sediment_candidate/` (planned)
- Derived output path: `outputs/soilgrids_250m_sediment_candidate/` (planned)
- Planned use: compute soil erodibility K-factor via a chosen pedotransfer function (e.g.
  Williams 1995 / Sharply-Williams) from clay/silt/sand/organic-carbon layers; produce V1 250 m
  K-factor diagnostics and V1/sub-basin zonal summary. Output is soil-erodibility context at
  250 m, NOT a 30 m raster.
- Known limitations: 250 m resolution is much coarser than the V1 30 m terrain grid; must not be
  resampled to 30 m as pixel-level truth; pedotransfer function choice changes absolute K values;
  SoilGrids uncertainty bands exist and should be reported.
- Validation role: sediment-risk factor K per `p2_sediment_risk_decision_package_2026-06-15.md`;
  also supports infiltration-capacity and environmental-sensitivity context.

## Release Boundary

- May be committed: no raw data
- May be used in public examples: no unless replaced by synthetic or approved sample data
- May be included in release archives: no unless licence and mentor approval confirmed
- Public-safe summary available: this registry note only
