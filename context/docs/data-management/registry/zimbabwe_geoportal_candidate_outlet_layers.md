# Dataset Registry: Zimbabwe Geoportal Candidate Outlet Layers

Status: downloaded and verified for visual review.

## Dataset Identity

- Dataset id: `zimbabwe_geoportal_candidate_outlet_layers`
- Short name: Zimbabwe Geoportal Rivers, Flood Prone Zones, and related outlet evidence
- Data class: `LOCAL_DATA`
- Reusable download: yes, if source terms allow
- Project role: local river, flood-prone-zone, and possible impact-context evidence for
  candidate outlet discovery
- Study area: Zimbabwe / Upper Mzingwane candidate outlet discovery
- Spatial unit or mask: clip to candidate outlet search envelope after download
- Temporal coverage: static or portal-reported update date for each layer

## Source And Access

- Source organization: Zimbabwe Geoportal / contributing organisations
- Source URL or portal:
  - Rivers: `https://zimgeoportal.org.zw/datasets/rivers/`
  - Flood Prone Zones: `https://zimgeoportal.org.zw/datasets/flood-prone-zones/`
  - Dataset search: `https://zimgeoportal.org.zw/datasets/`
- Product/version:
  - Rivers: v1.0, updated 2026-02-10, Shapefile resource `zwe-water`
  - Flood Prone Zones: v1.0, updated 2025-10-22
  - Mining-specific Geoportal layer: not identified as a reusable download in this pass
- Access date: checked 2026-06-12
- Access method: authenticated portal download
- Licence or terms:
  - Rivers: page reports PDDL 1.0
  - Flood Prone Zones: page reports PDDL 1.0
  - Mining evidence: unresolved
- Citation requirement: cite Zimbabwe Geoportal page and dataset title/version
- Account, registration, or approval needed: login required for listed resources
- Redistribution allowed: not cleared; do not release raw or derived layers without review

## Download Plan

- Intended destination: `data/raw/zimbabwe_geoportal_candidate_outlet_layers/`
- Expected file types: Shapefile or GeoJSON archives
- Source artifact name:
  - Rivers: `zwe_wat-1770728773.zip`
  - Flood Prone Zones Shapefile: `flood_prone_zones-1761163533.zip`
  - Flood Prone Zones GeoJSON: `flood_prone_zones-1761163533.geojson`
- Expected file count: one archive per selected layer
- Expected byte size:
  - Rivers Shapefile: page reports about 551 KB
  - Flood Prone Zones Shapefile: page reports about 10 KB
- Download command or manual steps: reused temporary authenticated browser session material from
  ignored `tmp/` only to reveal authenticated resource URLs, then downloaded static resource
  artifacts; session values were not written to committed files
- Rate limits or quotas: unknown
- Authentication handling: do not record cookies, tokens, or private object URLs in committed
  files
- Temporary path, if any: `data/tmp/zimbabwe_geoportal_candidate_outlet_layers/`
- Cleanup needed after extraction: remove failed partials and record manifest

## Download Attempt State

- Attempt status: complete
- Attempt date: 2026-06-12
- Failure reason, if any:
- Partial path, if any:
- Archive state: downloaded and verified
- Extraction state: complete for Shapefile archives
- Retry or resume safe: yes, with overwrite guards
- Cleanup/disposition:
- Cleanup date:

## Verification

- Download completed: yes
- Verification date: 2026-06-12
- Checksum scope: source archive
- Checksum algorithm: SHA-256
- Checksum command: `shasum -a 256 data/raw/zimbabwe_geoportal_candidate_outlet_layers/*`
- Checksum value:
  - `f4a841b4e82e839eccc4ec9875a95ec414f01281a82aa25eb8b87bc53c05d495`
    `rivers_zwe_wat-1770728773.zip`
  - `d78d0528e08fa9184c1f2ce81c1c5a72873b3bffd0befd72edb70dd8d258940b`
    `flood_prone_zones-1761163533.zip`
  - `f6d65e684e06a177dfa03ccedf2cf4c8e809cb395f1d9d4648a2e7b665872912`
    `flood_prone_zones-1761163533.geojson`
- Expected files or manifest: Rivers water lines/areas shapefile sidecars and Flood Prone Zones
  shapefile sidecars
- Actual files or manifest:
  `data/raw/zimbabwe_geoportal_candidate_outlet_layers/extraction_manifest.txt`
- Expected byte size:
- Actual byte size:
  - Rivers ZIP: 551 KB
  - Flood Prone Zones ZIP: 10 KB
  - Flood Prone Zones GeoJSON: 24 KB
- File-count evidence: 14 extracted files listed in manifest
- File-size evidence: local `ls -lh` evidence recorded during download handoff
- CRS or georeferencing checked: yes, EPSG:4326
- Geometry/raster integrity checked: yes; clipped review layers have 83 river lines, 8 water
  areas, and 0 flood-prone-zone features intersecting the review envelope
- Licence/terms accepted: yes for internal review use by authenticated download; redistribution
  remains unapproved

## Processing And Use

- Raw data path: `data/raw/zimbabwe_geoportal_candidate_outlet_layers/`
- Derived output path: `outputs/_archive/superseded_outlet_exploration_2026-06/professional_outlet_review/`
- Scripts or commands used: authenticated page inspection via temporary browser session material,
  guarded `curl`, `shasum -a 256`, `unzip`, `bin/_archive/superseded_outlet_exploration_2026-06/prepare_outlet_review_sources.py`
- Standardization/preprocessing notes: use as outlet plausibility evidence, not model scoring
- Known limitations: portal pages report missing/unknown source metadata for some layers; Flood
  Prone Zones page explicitly asks users to verify before use; the downloaded flood-prone layer
  has no overlap with the Upper Mzingwane review envelope
- Replacement or update rule: recheck page update dates before use
- Validation role: supporting evidence only

## Release Boundary

- May be committed: no
- May be used in public examples: no unless source permission is explicit
- May be included in release archives: no unless explicitly approved
- Public-safe summary available: yes
