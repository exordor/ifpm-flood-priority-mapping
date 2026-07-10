# Dataset Registry: WorldPop Peru population exposure input

Status: downloaded on 2026-07-08 and subset refreshed on 2026-07-10. The full Peru WorldPop file was required
because the server did not support HTTP range reads; the workflow then created a
current-study-area bbox subset.

## Dataset Identity

- Dataset id: `worldpop_peru_population`
- Short name: WorldPop Peru 2020 population count
- Data class: `LOCAL_DATA`
- Reusable download: yes
- Project role: population component of the Peru exposure indicators and
  endogenous population accounting by PIM class
- Study area: current Peru study boundary and small surrounding bbox
- Spatial unit or mask: gridded population count
- Temporal coverage: 2020

## Source And Access

- Source organization: WorldPop
- Source URL:
  `https://data.worldpop.org/GIS/Population/Global_2000_2020/2020/PER/per_ppp_2020_UNadj.tif`
- Product/version: Peru 2020 population count, unconstrained, UN-adjusted
- Access date: 2026-07-10 refresh from the existing verified full source
- Access method: public GeoTIFF URL; local script reads a spatial window
- Account, registration, or approval needed: none identified
- Licence or terms: WorldPop terms and citation requirements must be checked
  before public release

## Download Plan

- Destination: `data/raw/worldpop_peru_population/`
- Expected file types: clipped GeoTIFF subset
- Full-source size from HEAD probe: about 625 MB
- Download strategy: attempted remote spatial window read for the Peru study-area
  bbox. The server rejected range reads, so the full Peru raster was downloaded
  and then clipped locally.
- Script:
  `.venv/bin/python bin/acquire/download_peru_worldpop_population_subset.py`
- Temporary path: none

## Verification

- Download completed: yes
- Download verification date: 2026-07-10
- Checksum scope: local clipped GeoTIFF subset
- Full source size: 625,103,891 bytes
- Full source SHA-256:
  `2fb071f6afda320242ce7e361635e9032ecb645afbf1d3cbee646dc9cc5f2be3`
- Local subset size: 3,385,219 bytes
- Local subset SHA-256:
  `10c3ab7855e4c9c030301ea863b5a43e17926c7f86a05b0ea8e415615a4f7e3c`
- Local subset bbox (EPSG:4326):
  `[-72.358333, -16.904734, -71.5375, -16.091099]`
- Bbox population sum from source-grid subset: 641,138.25 people
- Expected output manifest:
  `outputs/worldpop_peru_population/worldpop_peru_population_subset_manifest.json`
- CRS or georeferencing check: source is expected in EPSG:4326; subset is in
  source CRS and should be reprojected/aligned in a separate exposure step

## Processing And Use

- Raw data path: `data/raw/worldpop_peru_population/`
- Derived output path: `outputs/worldpop_peru_population/`
- Planned use:
  - people potentially exposed in high / very-high PIM cells;
  - people potentially exposed in top-priority cells;
  - population context near high-priority mining/access intersections.
- Known limitations:
  - population count is exposure context, not observed affected population;
  - the population input is sum-aggregated to the native PIM grid for class
    accounting;
  - because WorldPop also contributes to the PIM exposure criterion, population
    by PIM class is endogenous accounting rather than independent validation.

## Release Boundary

- May be committed: no raw raster
- May be used in public examples: no unless replaced by synthetic or approved
  sample data
- Public-safe summary available: aggregate exposure statistics only
