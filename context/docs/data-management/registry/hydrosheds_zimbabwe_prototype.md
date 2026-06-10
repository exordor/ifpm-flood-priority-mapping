# Dataset Registry: HydroBASINS And HydroRIVERS Zimbabwe Prototype

Status: planned; no data downloaded.

## Dataset Identity

- Dataset id: `hydrosheds_zimbabwe_prototype`
- Short name: HydroBASINS Africa and HydroRIVERS Africa
- Data class: `LOCAL_DATA`
- Reusable download: yes, if the prototype proceeds
- Project role: hydrological boundary, river network, and possible sub-basin aggregation
- Study area: Zimbabwe / Upper Mzingwane Catchment prototype slice
- Spatial unit or mask: HydroBASINS-compatible catchment or sub-basin units, pending
- Temporal coverage: static hydrographic baseline derived from HydroSHEDS products

## Source And Access

- Source organization: HydroSHEDS
- Source URL or portal:
  - HydroBASINS: `https://www.hydrosheds.org/products/hydrobasins`
  - HydroRIVERS: `https://www.hydrosheds.org/products/hydrorivers`
  - Product overview: `https://www.hydrosheds.org/products`
- Product/version: HydroBASINS Africa and HydroRIVERS Africa, exact version to record at download
- Access date: 2026-06-10
- Access method: direct product-page download
- Licence or terms: HydroSHEDS product licence; exact agreement text/version to record
- Citation requirement: cite HydroSHEDS and Lehner & Grill (2013) where applicable
- Account, registration, or approval needed: none identified on product pages; recheck before use
- Redistribution allowed: not yet confirmed; governed by HydroSHEDS licence agreement. Record
  redistribution restrictions before any release.

## Download Plan

- Intended destination: `data/raw/hydrosheds_zimbabwe_prototype/`
- Expected file types: compressed archives with vector layers and sidecar files
- Source artifact name:
  - HydroBASINS Standard Africa archive, exact filename pending
  - HydroRIVERS Africa archive, exact filename pending
- Expected file count: pending product-page download details
- Expected byte size: pending product-page download details
- Download command or manual steps:
  1. Open the HydroBASINS product page and select the Standard Africa download.
  2. Open the HydroRIVERS product page and select the Africa download.
  3. Record exact filenames, versions, terms, and archive sizes before downloading.
  4. Download only the Africa archives needed for the Zimbabwe prototype.
- Rate limits or quotas: unknown; check HydroSHEDS site behavior before batch download
- Authentication handling: no credentials expected
- Temporary path, if any: `data/tmp/hydrosheds_zimbabwe_prototype/`
- Cleanup needed after extraction: retain archive manifest or checksums, remove failed partials

## Download Attempt State

- Attempt status: planned
- Attempt date: not started
- Failure reason, if any: not applicable
- Partial path, if any: none
- Archive state: not downloaded
- Extraction state: not started
- Retry or resume safe: unknown until download behavior is observed
- Cleanup/disposition: not applicable
- Cleanup date: not applicable

## Verification

- Download completed: no
- Verification date: not applicable
- Checksum scope: source archives and extracted vector sidecar manifests
- Checksum algorithm: SHA-256 preferred for archives
- Checksum command: `shasum -a 256 <archive>`
- Checksum value: not available
- Expected files or manifest: not available
- Actual files or manifest: not available
- Expected byte size: not available
- Actual byte size: not available
- File-count evidence: not available
- File-size evidence: not available
- CRS or georeferencing checked: no
- Geometry/raster integrity checked: no
- Licence/terms accepted: no

## Processing And Use

- Raw data path: `data/raw/hydrosheds_zimbabwe_prototype/`
- Derived output path: `outputs/hydrosheds_zimbabwe_prototype/`
- Scripts or commands used: none yet
- Standardization/preprocessing notes: identify HydroBASINS level and candidate basin ids for
  Upper Mzingwane before using boundaries for aggregation
- Known limitations: product scale may not match local official catchment boundaries; river
  reaches are generalized and should not be treated as field-survey data
- Replacement or update rule: replace or supplement if mentor supplies an authoritative local
  catchment boundary or river network
- Validation role: hydrological framework and aggregation units, not validation evidence

## Release Boundary

- May be committed: no
- May be used in public examples: no unless replaced by synthetic or approved sample data
- May be included in release archives: no unless explicitly approved
- Public-safe summary available: yes, this registry note without downloaded files
