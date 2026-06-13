# Dataset Registry: HydroBASINS And HydroRIVERS Zimbabwe Prototype

Status: downloaded for boundary discovery; boundary not accepted.

## Dataset Identity

- Dataset id: `hydrosheds_zimbabwe_prototype`
- Short name: HydroBASINS Africa and HydroRIVERS Africa
- Data class: `LOCAL_DATA`
- Reusable download: yes, if the prototype proceeds
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
- Product/version: HydroBASINS standard Africa version 1c for the first boundary-discovery
  artifact; HydroBASINS pour points version 1.0 and HydroRIVERS version 1.0 remain deferred
- Access date: 2026-06-10
- Access method: direct product-page download
- Licence or terms: HydroSHEDS core product licence in the HydroSHEDS Technical Documentation;
  the downloaded ZIP did not include a separate licence text file
- Citation requirement: cite HydroSHEDS and Lehner & Grill (2013) where applicable
- Account, registration, or approval needed: none identified on product pages; recheck before use
- Redistribution allowed: not yet confirmed; governed by HydroSHEDS licence agreement. Record
  redistribution restrictions before any release.

## Download Plan

- Intended destination: `data/raw/hydrosheds_zimbabwe_prototype/`
- Expected file types: compressed archives with vector layers and sidecar files
- Source artifact name:
  - first authorized boundary-discovery artifact: `hybas_af_lev01-12_v1c.zip`
  - deferred HydroBASINS pour points: exact Africa or all-level artifact not yet selected; use
    the HydroBASINS product page and pour-point technical documentation before download
  - deferred HydroRIVERS options: `HydroRIVERS_v10_af.gdb.zip` and
    `HydroRIVERS_v10_af_shp.zip`
- Expected file count: one source archive for the first boundary-discovery attempt
- Expected byte size: `549296874` bytes for `hybas_af_lev01-12_v1c.zip`
- Download command or manual steps:
  1. Re-open the HydroBASINS product page.
  2. Confirm the Standard Africa all-levels artifact still resolves to
     `hybas_af_lev01-12_v1c.zip`.
  3. Confirm source size, licence pointer, and no-authentication state.
  4. Use the guarded command in the boundary-discovery authorization note only after explicit
     approval.
  5. Defer HydroRIVERS unless river-network plausibility checking is required.
- Rate limits or quotas: unknown; check HydroSHEDS site behavior before batch download
- Authentication handling: no credentials expected
- Temporary path, if any: `data/tmp/hydrosheds_zimbabwe_prototype/`
- Cleanup needed after extraction: retain archive manifest or checksums, remove failed partials

## Download Attempt State

- Attempt status: complete for boundary discovery
- Attempt date: 2026-06-10
- Failure reason, if any: not applicable
- Partial path, if any: none
- Archive state: downloaded and verified
- Extraction state: complete
- Retry or resume safe: use a temporary `.part` file and do not overwrite existing files
- Cleanup/disposition: source archive, checksum, manifest, and extracted shapefiles retained
  under ignored `data/raw/`
- Cleanup date: not applicable

## Verification

- Download completed: yes
- Verification date: 2026-06-10
- Checksum scope: source archives and extracted vector sidecar manifests
- Checksum algorithm: SHA-256 preferred for archives
- Checksum command: `shasum -a 256 <archive>`
- Checksum value:
  `6b331a6e89d56c3a542dcee39a7e6e8700d0cf7c94083c5946c7db0d262a48d6`
- Expected files or manifest: `hybas_af_lev01-12_v1c.zip` before extraction
- Actual files or manifest: local manifest retained under
  `data/raw/hydrosheds_zimbabwe_prototype/hybas_af_lev01-12_v1c_manifest.txt`
- Expected byte size: `549296874` bytes before extraction
- Actual byte size: `549296874`
- File-count evidence: 85 extracted files
- File-size evidence: archive size matched expected `549296874` bytes
- CRS or georeferencing checked: yes, inspected shapefiles reported EPSG:4326
- Geometry/raster integrity checked: candidate geometries inspected as valid
- Licence/terms accepted: yes for internal boundary-discovery use by downloading; redistribution
  and release remain unapproved

## Processing And Use

- Raw data path: `data/raw/hydrosheds_zimbabwe_prototype/`
- Derived output path: `outputs/hydrosheds_zimbabwe_prototype/`
- Scripts or commands used: guarded `curl`, `shasum -a 256`, `unzip`, and temporary Python
  GeoPandas inspection
- Standardization/preprocessing notes: candidate HydroBASINS levels and ids were discovered; do
  not use boundaries for aggregation until accepted or waived
- Known limitations: product scale may not match local official catchment boundaries; river
  reaches are generalized and should not be treated as field-survey data
- Replacement or update rule: replace or supplement if mentor supplies an authoritative local
  catchment boundary or river network
- Validation role: hydrological framework and aggregation units, not validation evidence

## Candidate Outlet Follow-Up Sources

These sources were reviewed as likely next evidence layers for candidate outlet discovery but
were not downloaded during the 2026-06-11 first pass:

- HydroBASINS pour points: official sub-basin outlet point layer. Use only after recording exact
  artifact name, byte size, licence pointer, and checksum plan.
- HydroRIVERS Africa: river-network plausibility layer. The HydroSHEDS product page reports an
  Africa Shapefile option of about 108 MB; download only if river-exit checks are needed.

Any future download remains subject to the same `data/raw/<dataset_id>/` destination, checksum,
and release-boundary rules recorded above.

## Release Boundary

- May be committed: no
- May be used in public examples: no unless replaced by synthetic or approved sample data
- May be included in release archives: no unless explicitly approved
- Public-safe summary available: yes, this registry note without downloaded files
