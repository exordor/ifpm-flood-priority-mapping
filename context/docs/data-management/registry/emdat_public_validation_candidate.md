# Dataset Registry: EM-DAT Public Validation Candidate

Status: DRAFT candidate registry. Not authorized for download. Created as P1 R1.1 preflight
scaffolding so a scoped download can be authorized quickly once the mentor confirms Tier A
context use. No real data has been downloaded for this dataset id.

## Dataset Identity

- Dataset id: `emdat_public_validation_candidate`
- Short name: EM-DAT International Disaster Database (CRED)
- Data class: `LOCAL_DATA`
- Reusable download: yes, for temporal/event-magnitude context
- Project role: historical flood-disaster event context for Zimbabwe; candidate validation
  timeline cross-check against CHIRPS rainfall anomalies and GloFAS discharge events
- Study area: Zimbabwe national and admin-1; screened against V1 where admin-1 allows
- Spatial unit or mask: country / admin-1 only; cannot resolve to V1 catchment geometry
- Temporal coverage: 1900-present; focus window 1985-2024 to overlap DFO and CHIRPS

## Source And Access

- Source organization: Centre for Research on the Epidemiology of Disasters (CRED), Universite
  catholique de Louvain
- Source URL or portal:
  - Public site: `https://www.emdat.be/`
  - HDX redistribution: `https://data.humdata.org/dataset/emdat-international-disaster-database`
- Product/version: EM-DAT public disaster records (current public release at access date)
- Access date: not yet accessed; intended access date to be recorded at authorization
- Access method: direct download from HDX CSV resource, or EM-DAT site export after free
  registration
- Licence or terms: HDX record reports CC BY-NC-SA 4.0 (non-commercial, attribution required);
  EM-DAT site terms require registration and citation. Confirm exact licence field at access.
- Citation requirement: cite CRED / EM-DAT and the access date
- Account, registration, or approval needed: HDX direct download likely none; EM-DAT site export
  requires free academic registration
- Redistribution allowed: limited by NC clause; derived summaries only, no raw redistribution in
  release archives

## Download Plan

- Intended destination: `data/raw/emdat_public_validation_candidate/`
- Expected file types: CSV (event records), possibly XLSX
- Source artifact name: HDX CSV resource (exact resource id to be confirmed at access time)
- Expected file count: 1-3 files
- Expected byte size: order of tens of MB (full global disaster history)
- Download command or manual steps: to be specified at authorization; candidate HDX resource URL
  to be re-verified at access because HDX resource ids rotate
- Rate limits or quotas: none expected for HDX direct
- Authentication handling: none for HDX direct; do not store EM-DAT site credentials in any
  committed file
- Temporary path, if any: `data/tmp/emdat_public_validation_candidate/`
- Cleanup needed after extraction: remove raw XLSX lock files if opened locally

## Download Attempt State

- Attempt status: planned (draft, not authorized)
- Archive state: not downloaded
- Retry or resume safe: yes (HDX direct)

## Verification

- Download completed: no
- Verification date: not applicable
- Checksum scope: source archive
- Checksum algorithm: SHA-256 (to be recorded post-download)
- Expected files or manifest: to be confirmed at access
- CRS or georeferencing checked: not applicable (tabular)
- Licence/terms accepted: to be confirmed at access

## Processing And Use

- Raw data path: `data/raw/emdat_public_validation_candidate/` (planned)
- Derived output path: `outputs/emdat_public_validation_candidate/` (planned)
- Planned use: filter to Zimbabwe flood/disaster events 1985-2024; produce a timeline of event
  dates and magnitudes for cross-check against CHIRPS rainfall anomalies and (future) GloFAS
  discharge events. Output is temporal/magnitude context only, not spatial validation.
- Known limitations: country-level / admin-1 spatial precision; cannot validate V1 catchment
  flood extent; entry criteria changed over EM-DAT history (older entries have higher thresholds).
- Validation role: Tier A temporal context per
  `p1_validation_data_decision_package_2026-06-15.md`. Not a spatial validation layer.

## Release Boundary

- May be committed: no raw data
- May be used in public examples: no unless replaced by synthetic or approved sample data
- May be included in release archives: no unless licence and mentor approval confirmed
- Public-safe summary available: this registry note only
