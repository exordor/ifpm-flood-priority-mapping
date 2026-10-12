# Abzucht ATKIS watercourse and DOP visual context v1

- Dataset id: `goslar_abzucht_atkis_dop_context`.
- Access date: 2026-09-14. Study area: Goslar/Abzucht display rectangle plus about 300 m for vector completeness; three small orthophoto windows around case A, case C, and the longest >30 m network-gap run.
- Used by: `atkis_dop_check`, checking whether model t500 drainage and red high-PIM cells follow mapped watercourses; visually inspect selected ambiguous locations. Neither source records 2017 inundation.

## Sources and request scope

1. LGLN ATKIS Basis-DLM, model-based WFS 2.0.0, feature type `adv:AX_Gewaesserachse`, EPSG:25832, bounded `GetFeature` request. Official [product page](https://lgln-geodaten.niedersachsen.de/startseite/verwaltungen_und_fachkundige/produkte/digitale_landschaftsmodelle/digitales-landschaftsmodell-basis-dlm-144141.html) and [WFS catalogue](https://numis.niedersachsen.de/trefferanzeige?docuuid=e26aebd6-cc4c-4af2-8be3-8719b808df5d). Service: `https://opendata.lgln.niedersachsen.de/doorman/noauth/atkisbdlm_wfs_sf`.
2. LGLN DOP20 orthophoto display WMS 1.3.0, layer `ni_dop20`, EPSG:25832. [WMS catalogue](https://numis.niedersachsen.de/trefferanzeige?currentSelectorPage=1&docuuid=ae78fcce-b07a-4f0e-ab70-9095285e0de7&f=&rstart=7190), service `https://opendata.lgln.niedersachsen.de/doorman/noauth/dop_wms`. Three bounded PNG map images, each at most 1600 × 1200 pixels.

The Basis-DLM [product page](https://lgln-geodaten.niedersachsen.de/startseite/verwaltungen_und_fachkundige/produkte/digitale_landschaftsmodelle/digitales-landschaftsmodell-basis-dlm-144141.html) says open LGLN data are CC BY 4.0 and describes approximately ±3 m positional accuracy for linear objects. Use attribution `LGLN (2026), CC BY 4.0` for this local retrieval. No account required.

- Reproduce: `.venv/bin/python bin/acquire/pull_abzucht_atkis_dop_context.py`.
  (Script removed 2026-10-11; recover with `git show cc4f247:bin/acquire/pull_abzucht_atkis_dop_context.py`.)
- Files: `atkis_gewaesserachse.gml`, `dop_case_a.png`, `dop_case_c.png`, `dop_longest_gap.png`, and `source_manifest.json` under `data/validation/goslar_abzucht_atkis_dop_context/`.
- ATKIS: the bounded WFS query returned 169/169 features, 206,308 bytes, SHA-256 `2ca0ee55409e8d3bd1a94e2dacdf70b48d626584230a7a8a9c257775efb8a015`. GeoPandas reopened 169 LineString features in EPSG:25832. The exact bbox and HTTP response metadata are in `data/validation/goslar_abzucht_atkis_dop_context/source_manifest.json`.
- DOP PNG checksums and bytes: case A 4,050,779 bytes / `0365362c69f039ea602bdcc7fb8fcaabf37c46b3d54f11f3089029ab67d3f30b`; case C 4,099,267 / `d7c234872be4518f971eeffc093c0d20142d32e8a74c6cafe3b107059b62ca78`; longest gap 4,079,627 / `a197c25f933038a764f041ef62465cd18058032fcd811094932c21309eb08f08`. Map pixels are about 0.6 m for cases A/C and 0.875 m for the longest run. The WMS `ni_dop20_info` GetFeatureInfo at each image **center point** reports aerial capture date **2025-04-02**; other parts of the image mosaic may have different dates. The center-point date is eight years after the 2017 event.
