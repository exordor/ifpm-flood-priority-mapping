# Dataset Registry: WorldPop Peru population exposure input

Status: downloaded on 2026-07-08; subset refreshed on 2026-07-10 for the former Peru study area (frozen, `peru_former`).

## Dataset Identity

- Dataset id: `worldpop_peru_population`
- Short name: WorldPop Peru 2020 population count
- Project role: population component of the Peru exposure indicators and
  endogenous population accounting by PIM class
- Study area: former Peru study area (frozen, `peru_former`) and a small surrounding bbox
- Spatial unit or mask: gridded population count
- Temporal coverage: 2020

## Source And Access

- Source organization: WorldPop
- Source URL:
  `https://data.worldpop.org/GIS/Population/Global_2000_2020/2020/PER/per_ppp_2020_UNadj.tif`
- Product/version: Peru 2020 population count, unconstrained, UN-adjusted
- Access date: 2026-07-08 (full file); subset made 2026-07-10
- Access method: public GeoTIFF URL; full file downloaded and clipped locally (the server does not support range reads)
- Licence or terms: WorldPop terms (CC BY 4.0); cite WorldPop

## Acquisition

- Destination: `data/raw/worldpop_peru_population/`
- Script:
  `.venv/bin/python bin/acquire/download_peru_former_worldpop_population_subset.py`

## Files

- Full source size: 625,103,891 bytes
- Full source SHA-256:
  `2fb071f6afda320242ce7e361635e9032ecb645afbf1d3cbee646dc9cc5f2be3`
- Local subset: `per_ppp_2020_UNadj_peru_former_bbox.tif`, 3,385,219 bytes
- Local subset SHA-256:
  `10c3ab7855e4c9c030301ea863b5a43e17926c7f86a05b0ea8e415615a4f7e3c`
- Local subset bbox (EPSG:4326):
  `[-72.358333, -16.904734, -71.5375, -16.091099]`
- Bbox population sum from source-grid subset: 641,138.25 people
- Manifest:
  `outputs/peru_former_worldpop_population/worldpop_peru_population_subset_manifest.json`
- CRS: EPSG:4326 (source and subset); aligned to the PIM grid in the exposure step

## Processing And Use

- Raw data path: `data/raw/worldpop_peru_population/`
- Derived output path: `outputs/peru_former_worldpop_population/`
- Use:
  - people potentially exposed in high / very-high PIM cells;
  - people potentially exposed in top-priority cells;
  - population context near high-priority mining/access intersections.
- Known limitations:
  - population count is exposure context, not observed affected population;
  - the population input is sum-aggregated to the native PIM grid for class
    accounting;
  - WorldPop also feeds the PIM exposure criterion, so population by PIM class is
    endogenous accounting.
