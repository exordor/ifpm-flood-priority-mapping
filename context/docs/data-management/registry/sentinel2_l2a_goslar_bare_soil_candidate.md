# Sentinel-2 L2A Goslar bare-soil candidate

- Dataset id: `sentinel2_l2a_goslar_bare_soil_candidate`
- Status / claim level: `diagnostic_only`; does not enter the PIM score
- Source mission: ESA Copernicus Sentinel-2 Level-2A surface reflectance
- Catalogue and public COG access: Element 84 Earth Search,
  `https://earth-search.aws.element84.com/v1`, collection
  `sentinel-2-c1-l2a` (Collection 1, processing baseline 5.x)
- Method reference: Copernicus Data Space soil-erosion notebook,
  `https://documentation.dataspace.copernicus.eu/notebook-samples/sentinelhub/soil_erosion_risk.html`
- Access date: 2026-08-14
- Licence / attribution: Copernicus Sentinel data terms; retain
  `Contains modified Copernicus Sentinel data` and the frozen source URLs
- Study area: `goslar_harz_2024_focus_extent`, approximately 22.9 km2; layout
  reference rather than a validated catchment
- Temporal scope: March-November in 2021, 2023, 2024 and 2025; two
  low-catalog-cloud scenes per spring, summer and autumn period (24 scene
  windows). The incomplete 2022 Collection-1 archive is an explicit gap and is
  not filled from the legacy collection.
- Spatial scope: only the Goslar focus window; 10 m analysis grid aligned to the
  existing EPSG:32632 reference and an additional 30 m candidate output
- Expected local footprint: less than approximately 200 MB for cropped,
  analysis-ready scene windows; no full Sentinel tile download
- Raw/local snapshot destination:
  `data/raw/sentinel2_l2a_goslar_bare_soil/`
- Derived output destination:
  `outputs/goslar_sentinel_bare_soil_candidate/`
- Reproducible command:
  `.venv/bin/python bin/acquire/pull_goslar_sentinel_bare_soil.py`
- Reuse: internal research use; external redistribution requires checking the
  current Copernicus terms and preserving attribution

## Processing and evidence boundary

The bare-soil candidate follows the modified bareness index used by the
Copernicus Data Space soil-erosion example. Cloud, shadow, cirrus, snow,
invalid and NoData observations remain NoData. A pixel requires at least five
clear observations before a frequency is reported. The script also produces a
2021-to-2025 median-NDVI decline candidate, but this is not a validated forest
loss product.

The Earth Search catalogue and every selected source asset URL are frozen in
`earth_search_catalog.json`; cropped local scene windows and outputs receive
SHA-256 checksums. These products must pass coverage and non-constant checks
before any model-integration proposal. They do not replace the active
WorldCover component automatically.

An initial read from the legacy `sentinel-2-l2a` collection exposed mixed
radiometric processing revisions and was rejected by QA. Its local
`scene_windows_10m/` folder is retained only as superseded diagnostic evidence;
the accepted rerun must use `scene_windows_c1_10m/` and processing baseline
5.x throughout.

## Acquisition and QA result (2026-08-14)

- Accepted Collection-1 snapshot: 24 scenes, all processing baseline 5.x;
  approximately 80.4 MB in `scene_windows_c1_10m/`.
- Superseded legacy diagnostic snapshot: approximately 100.6 MB; it must not be
  used for modelling because radiometric revisions were mixed.
- Accepted engineering coverage: bare-frequency candidate covers 100% of the
  focus mask at 10 m; clear-observation count is 7-24 per pixel (median 21).
- Physical-range check: 2021 and 2025 median NDVI remain within [-1, 1], with
  approximately 97% focus coverage in each endpoint year.
- Candidate bare-frequency distribution at 10 m: median 0.227, 98th percentile
  0.727; the layer is spatially variable rather than all-zero.

The scientific specificity check did **not** pass. Stratification against ESA
WorldCover showed high MBI response over built and water classes and frequent
non-zero responses in forest. A stricter SCL-only rule still produced median
frequency about 0.59 for built surfaces and 1.0 for water, while about 59% of
tree-class pixels received at least one bare observation. These are material
false-positive risks, not merely visual noise.

Decision: retain the rasters as `diagnostic_only` evidence and keep
`enters_pim_score=false`. They do not replace the current model component. The
preferred next source is the validated Copernicus HRL Croplands `Bare Soil
After` 10 m product for agricultural areas, combined with the Copernicus Tree
Cover Density/change product for forest vegetation loss. Quantitative access
to those products requires Copernicus Data Space/WEkEO access in the current
environment.
