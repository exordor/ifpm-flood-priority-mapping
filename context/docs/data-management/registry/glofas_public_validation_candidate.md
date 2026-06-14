# Dataset Registry: GloFAS Public Validation Candidate

Status: DRAFT candidate registry. Not authorized for download. Created as P1 R1.1 preflight
scaffolding so a scoped download can be authorized quickly once the mentor confirms Tier A
outlet-scale discharge context use. No real data has been downloaded for this dataset id.

## Dataset Identity

- Dataset id: `glofas_public_validation_candidate`
- Short name: Copernicus Global Flood Awareness System (GloFAS)
- Data class: `LOCAL_DATA`
- Reusable download: yes, for outlet-scale discharge context
- Project role: modelled river-discharge reanalysis context for the V1 outlet and downstream
  Mzingwane channel; candidate timeline of return-period exceedance events for cross-check
  against CHIRPS rainfall anomalies and EM-DAT/DFO events
- Study area: V1 outlet region and Mzingwane channel downstream toward Gwanda
- Spatial unit or mask: GloFAS river-network cells (about 0.1 degree) intersecting or nearest to
  the V1 outlet; explicit acknowledgement that GloFAS resolution cannot resolve V1 internal
  catchment detail
- Temporal coverage: reanalysis 1979-present; focus window 1985-2024

## Source And Access

- Source organization: Copernicus Emergency Management Service (CEMS) / European Centre for
  Medium-Range Weather Forecasts (ECMWF)
- Source URL or portal: Copernicus Climate Data Store (CDS)
  `https://cds.climate.copernicus.eu/` (GloFAS reanalysis dataset record)
- Product/version: GloFAS historical reanalysis, latest public version at access date
- Access date: not yet accessed; intended access date to be recorded at authorization
- Access method: CDS API (requires free CDS account and API key placed in local config only, not
  committed) or CDS web interface
- Licence or terms: Copernicus data licence, free with attribution; confirm exact licence text at
  access
- Citation requirement: cite Copernicus CEMS GloFAS and access date
- Account, registration, or approval needed: free CDS account; API key must remain local-only and
  never committed
- Redistribution allowed: generally yes with attribution; confirm at access

## Download Plan

- Intended destination: `data/raw/glofas_public_validation_candidate/`
- Expected file types: NetCDF (.nc) discharge grids or time series
- Source artifact name: GloFAS reanalysis subset for the V1 outlet bounding box and time window
- Expected file count: 1-5 files (subset, not global)
- Expected byte size: order of tens to low hundreds of MB depending on subset and time window
- Download command or manual steps: CDS API request specifying bounding box around V1 outlet,
  1979-2024, daily discharge; to be specified precisely at authorization
- Rate limits or quotas: CDS queues requests; typical turnaround minutes to hours
- Authentication handling: CDS API key in local `~/.cdsapirc` only; never copy into the workspace
- Temporary path, if any: `data/tmp/glofas_public_validation_candidate/`
- Cleanup needed after extraction: remove any global NetCDF if accidentally downloaded; keep only
  the scoped subset

## Download Attempt State

- Attempt status: planned (draft, not authorized)
- Archive state: not downloaded
- Retry or resume safe: yes (CDS API request can be re-submitted)

## Verification

- Download completed: no
- Verification date: not applicable
- Checksum scope: downloaded NetCDF files
- Checksum algorithm: SHA-256 (to be recorded post-download)
- Expected files or manifest: to be confirmed at access
- CRS or georeferencing checked: to be checked post-download (expect global lat/lon grid)
- Geometry/raster integrity checked: to be checked post-download

## Processing And Use

- Raw data path: `data/raw/glofas_public_validation_candidate/` (planned)
- Derived output path: `outputs/glofas_public_validation_candidate/` (planned)
- Planned use: extract discharge time series at the GloFAS cell nearest the V1 outlet; compute
  return-period exceedance events; cross-check event dates against CHIRPS rainfall anomalies and
  EM-DAT/DFO timelines. Output is outlet-scale discharge context, not overland flood extent.
- Known limitations: 0.1 degree modelled discharge cannot resolve V1 internal overland flooding;
  GloFAS is reanalysis (modelled), not gauge observation; requires the V1 outlet to be accepted
  or provisionally fixed before extraction is meaningful.
- Validation role: Tier A outlet-scale context per
  `p1_validation_data_decision_package_2026-06-15.md`. Not a spatial inundation validation layer.

## Release Boundary

- May be committed: no raw data
- May be used in public examples: no unless replaced by synthetic or approved sample data
- May be included in release archives: no unless licence and mentor approval confirmed
- Public-safe summary available: this registry note only
