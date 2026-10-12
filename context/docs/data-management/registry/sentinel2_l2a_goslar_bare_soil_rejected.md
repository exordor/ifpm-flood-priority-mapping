# Sentinel-2 L2A Goslar bare-soil candidate

- Dataset id: `sentinel2_l2a_goslar_bare_soil_rejected`
- Status: rejected 2026-08-14 (failed the land-cover specificity check) and superseded by
  `clms_hrl_bare_soil_tcd_goslar`; not part of the PIM score.
- Source: ESA Copernicus Sentinel-2 Level-2A, Element 84 Earth Search
  `https://earth-search.aws.element84.com/v1`, collection `sentinel-2-c1-l2a`
  (Collection 1, processing baseline 5.x)
- Method reference: Copernicus Data Space soil-erosion notebook (modified bareness index),
  `https://documentation.dataspace.copernicus.eu/notebook-samples/sentinelhub/soil_erosion_risk.html`
- Access date: 2026-08-14
- Licence: Copernicus Sentinel data terms; attribution `Contains modified Copernicus Sentinel data`
- Study area: `goslar_harz_2024_focus_extent` (about 22.9 km²)
- Temporal scope: March-November 2021, 2023, 2024 and 2025; 24 scene windows (2022 missing from
  Collection 1)
- Command: `.venv/bin/python bin/acquire/pull_goslar_sentinel_bare_soil.py`
  (Script removed 2026-10-11; recover with `git show cc4f247:bin/acquire/pull_goslar_sentinel_bare_soil.py`.)
- Local path: `data/raw/sentinel2_l2a_goslar_bare_soil_rejected/` (`scene_windows_c1_10m/`, about 80.4 MB;
  `scene_windows_10m/` is an earlier legacy-collection read with mixed radiometric revisions,
  about 100.6 MB, not used); source asset URLs frozen in `earth_search_catalog.json`
- Derived outputs: `outputs/goslar_sentinel2_bare_soil_rejected/`

## Reason for rejection

Stratified against ESA WorldCover, the bare-frequency layer responded strongly over built and
water classes (median frequency about 0.59 for built surfaces and 1.0 for water with an SCL-only
rule) and about 59% of tree-class pixels received at least one bare observation.
