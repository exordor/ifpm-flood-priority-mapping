# Dataset Registry: HydroRIVERS Africa Visual Review

Status: downloaded and verified for visual review.

## Dataset Identity

- Dataset id: `hydrorivers_africa_visual_review`
- Short name: HydroRIVERS Africa Shapefile
- Data class: `LOCAL_DATA`
- Reusable download: yes, for river-network plausibility review
- Project role: independent river-line evidence for professional outlet visual review
- Study area: Zimbabwe / Upper Mzingwane outlet review
- Spatial unit or mask: clip to the professional outlet review envelope after download
- Temporal coverage: static HydroRIVERS v1.0 product

## Source And Access

- Source organization: HydroSHEDS
- Source URL or portal: `https://www.hydrosheds.org/products/hydrorivers`
- Product/version: `HydroRIVERS_v10_af_shp.zip`, Africa Shapefile, HydroRIVERS v1.0
- Access date: 2026-06-12
- Access method: direct product-page download
- Licence or terms: HydroSHEDS core product licence; by downloading and using the data the user
  agrees to the HydroSHEDS licence terms
- Citation requirement: cite HydroSHEDS and Lehner & Grill (2013)
- Account, registration, or approval needed: none identified on the product page
- Redistribution allowed: not cleared for this project; do not release raw data without review

## Download Plan

- Intended destination: `data/raw/hydrorivers_africa_visual_review/`
- Temporary path: `data/tmp/hydrorivers_africa_visual_review/`
- Source artifact URL:
  `https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_af_shp.zip`
- Expected source artifact: `HydroRIVERS_v10_af_shp.zip`
- Expected byte size: `107873468` bytes from HTTP header on 2026-06-12
- Download command: guarded `curl -L --fail --continue-at -`
- Cleanup needed after extraction: keep archive, checksum, and extracted manifest under ignored
  `data/raw/`

## Download Attempt State

- Attempt status: complete
- Attempt date: 2026-06-12
- Failure reason, if any:
- Partial path, if any:
- Archive state: downloaded and verified
- Extraction state: complete
- Retry or resume safe: yes, with temporary `.part` file and no overwrite of verified archive

## Verification

- Download completed: yes
- Verification date: 2026-06-12
- Checksum scope: source archive
- Checksum algorithm: SHA-256
- Checksum command: `shasum -a 256 data/raw/hydrorivers_africa_visual_review/HydroRIVERS_v10_af_shp.zip`
- Checksum value:
  `63cc615134d8812b73f27ee9dfd9d790c520af96bc609dfc97bcd47811fec125`
- Expected files or manifest: source ZIP plus HydroRIVERS shapefile sidecars
- Actual files or manifest:
  `data/raw/hydrorivers_africa_visual_review/extraction_manifest.txt`
- Expected byte size: `107873468`
- Actual byte size: `107873468`
- File-count evidence: 7 extracted files listed in manifest
- File-size evidence: archive size matched expected byte size
- CRS or georeferencing checked: yes, EPSG:4326
- Geometry integrity checked: yes, 589 features intersect the review envelope after clipping
- Licence/terms accepted: yes for internal review use by downloading; redistribution remains
  unapproved

## Processing And Use

- Raw data path: `data/raw/hydrorivers_africa_visual_review/`
- Derived output path: `outputs/professional_outlet_review/`
- Scripts or commands used: guarded `curl`, `shasum -a 256`, `unzip`,
  `bin/prepare_outlet_review_sources.py`
- Standardization/preprocessing notes: clip to review envelope and use as river-line evidence;
  do not treat generalized river lines as field-survey river positions
- Known limitations: generalized product; not local survey data
- Validation role: supporting map evidence only

## Release Boundary

- May be committed: no
- May be used in public examples: no unless replaced by synthetic data
- May be included in release archives: no unless explicitly approved
- Public-safe summary available: yes
