# Dataset Registry: DFO Global Flood Archive V1 Methodology Evidence

Status: downloaded and processed for Zimbabwe-level historical-flood context. This does not
authorize AHP overlay, flood-risk interpretation, or local flood validation claims.

## Dataset Identity

- Dataset id: `dfo_global_flood_archive_v1_methodology`
- Short name: Dartmouth Flood Observatory Global Active Archive
- Data class: `LOCAL_DATA`
- Reusable download: yes, for historical context review
- Project role: historical flood-event context and global flood-database evidence
- Study area: V1 working catchment / Zimbabwe context
- Spatial unit or mask: global event centroids or affected-area outlines, intersected or screened
  against V1/context extent
- Temporal coverage: 1985-present archive described by DFO

## Source And Access

- Source organization: Dartmouth Flood Observatory / University of Colorado, redistributed
  through HDX/WFP dataset record
- Source URL or portal:
  - DFO archive page: `https://floodobservatory.colorado.edu/Archives/`
  - HDX API dataset record:
    `https://data.humdata.org/api/3/action/package_show?id=global-active-archive-of-large-flood-events-dfo`
- Direct source artifact:
  `https://data.humdata.org/dataset/1fd855de-57c6-42b3-83e1-9cf989b0f70d/resource/984cc240-b2b7-4266-9f61-5715a9e10ff5/download/wlf_nhr_fl_dfomasterlist_20190418.zip`
- Archive description: the page describes an online table, Excel/XML files, and GIS MapInfo/SHP
  files with flood catalog numbers, centroids, and affected-area outlines
- Access date: 2026-06-13
- Access method tested: HDX CKAN API and direct SHP zip download
- Licence or terms: HDX record reports Creative Commons Attribution International; cite DFO/HDX
  before public release
- Account, registration, or approval needed: none identified on the archive page

## Download Plan

- Intended destination: `data/raw/dfo_global_flood_archive_v1_methodology/`
- Expected file types: ZIP containing shapefile components
- Download command or manual steps:
  1. Run `.venv/bin/python bin/acquire/download_v1_methodology_inputs.py`.
  2. Run `.venv/bin/python bin/package/prepare_v1_full_methodology_evidence.py`.
- Temporary path, if any: `data/tmp/dfo_global_flood_archive_v1_methodology/`

## Verification

- Download completed: yes
- Verification date: 2026-06-13
- Checksum algorithm: SHA-256
- Checksum value: `976f0904c603ba31e8aa62f6d1b55cec4c153be783495593ed247d01629ffe09`
- Actual file size: 610,578 bytes
- Readability checked: yes; ZIP shapefile opens with GeoPandas as 4,029 global point records,
  `EPSG:4326`

## Processing And Use

- Raw data path: `data/raw/dfo_global_flood_archive_v1_methodology/`
- Derived output path: `outputs/v1_full_methodology_evidence_sweep/`
- Planned/actual use: Zimbabwe-related historical flood records were screened and summarized in
  `outputs/v1_full_methodology_evidence_sweep/v1_dfo_zimbabwe_flood_events.csv`
- Known limitations: the downloaded HDX resource contains event points/centroids rather than
  inundation polygons. Nine Zimbabwe-related records were found, but zero valid event points
  fall within V1 plus one degree. Several Zimbabwe-related records contain invalid sentinel
  coordinates. Treat this as historical context only, not local flood depth, local validation, or
  official hazard zoning.

## Release Boundary

- May be committed: no raw data
- May be used in public examples: no unless replaced by synthetic or approved sample data
- Public-safe summary available: this registry note only
