# Dataset Registry: ohsome Peru Road History Pilot

## Dataset Identity

- Dataset id: `ohsome_peru_road_history_pilot`
- Short name: OSM highway snapshots through ohsome API
- Data class: `LOCAL_DATA`
- Reusable download: yes, subject to OSM/ohsome attribution and completeness checks
- Project role: evaluate whether historical road geometry can support the road-expansion part of BE
- Study area: bounding box of `peru_hybas_l7_6070641200`
- Spatial unit or mask: API bounding box, clipped to the scientific boundary during processing
- Temporal coverage: snapshots at 2015-01-01 and 2024-01-01

## Source And Access

- Source organization: Heidelberg Institute for Geoinformation Technology / OpenStreetMap contributors
- Source URL or portal: `https://api.ohsome.org/v1/elements/geometry`
- Product/version: ohsome API v1; API reported version 1.10.4 during preflight
- Access date: 2026-08-05
- Access method: public API
- Licence or terms: OSM history data after 2012 is ODbL 1.0; ohsome and OpenStreetMap attribution required
- Citation requirement: `© OpenStreetMap contributors`, with `https://ohsome.org/copyrights`
- Account, registration, or approval needed: none
- Redistribution allowed: subject to ODbL requirements; keep raw snapshots local by default

## Download Plan

- Intended destination: `data/raw/ohsome_peru_road_history_pilot/`
- Expected file types: GeoJSON plus SHA-256 sidecars
- Source artifact name: highway way geometry snapshots for 2015-01-01 and 2024-01-01
- Expected file count: 2 GeoJSON files
- Expected byte size: unknown, expected below 100 MB combined from preflight feature counts
- Download command or manual steps: `bin/data/download_ohsome_peru_road_snapshots.sh`
- Rate limits or quotas: public API timeout is 600 seconds; sequential requests only
- Authentication handling: not applicable
- Temporary path, if any: none
- Cleanup needed after extraction: none

## Download Attempt State

- Attempt status: failed
- Attempt date: 2026-08-05
- Failure reason, if any: the documented `/v1/elements/geometry` endpoint returned HTTP 403 for both the Peru request and the official small example request; aggregate count and length endpoints remained available
- Partial path, if any: none; the failed response was not retained as data
- Archive state: not downloaded
- Extraction state: not applicable
- Retry or resume safe: API requests can be repeated; partial GeoJSON must not be used

## Verification

- Download completed: no
- Verification date: 2026-08-05
- Checksum scope: individual GeoJSON files
- Checksum algorithm: SHA-256
- Checksum command: `shasum -a 256 data/raw/ohsome_peru_road_history_pilot/*.geojson`
- Expected files or manifest: two valid GeoJSON FeatureCollections
- Expected feature-count evidence: 3,719 ways in 2015 and 16,801 ways in 2024 from ohsome count preflight
- Expected length evidence: 965.711 km in 2015 and 6,666.008 km in 2024 from ohsome length preflight
- CRS or georeferencing checked: not applicable because geometry extraction failed
- Geometry/raster integrity checked: not applicable because geometry extraction failed
- Licence/terms accepted: yes

## Processing And Use

- Raw data path: `data/raw/ohsome_peru_road_history_pilot/`
- Derived output path: `outputs/ohsome_peru_road_history_pilot/`
- Known limitations: OSM history records when features were mapped, not necessarily when roads were physically built. The large 2015-2024 increase is therefore mapping-completeness evidence until independently checked.
- Replacement or update rule: use road history as BE scoring evidence only after completeness/stability checks; otherwise retain it as context or a sensitivity scenario
- Validation role: data-completeness and temporal road evidence, not direct validation of physical road construction

## Release Boundary

- May be committed: no
- May be used in public examples: no unless ODbL obligations and release approval are satisfied
- May be included in release archives: no unless explicitly approved
- Public-safe summary available: this registry note
