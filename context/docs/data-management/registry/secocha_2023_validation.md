# Dataset Registry: Secocha 2023 historical hazard event

Status: downloaded and processed (2026-08-07 to 2026-08-18). Event-comparison evidence for the
Secocha case; not a PIM input and not used to set weights.

## Dataset Identity

- Dataset id: `secocha_2023_validation`
- Event: Secocha 2023 debris-flow and flood-related disaster
- Event time: 2023-02-05, approximately 14:00-14:17 local time (19:00-19:17 UTC) according to
  the later INDECI report
- Study area: Secocha, San Martin, Miski/Posco Misky, Pampa Blanca/Pampaylima and nearby
  localities in Mariano Nicolas Valcarcel district, Camana province, Arequipa department
- Used by: the 2023 event comparison for `peru_secocha_a7367_reference_extent_v1`
  (see `context/docs/research-map/EXPERIMENTS.md`)

## Official Reports

1. INGEMMET, *Informe Tecnico N A7367: Evaluacion de peligros geologicos en el centro
   poblado Secocha y las localidades La Poderosa, San Martin, Posco Misky y Pampaylima*
   (2023-03). Public PDF served by SIGRID/CENEPRED. Fieldwork 2023-02-14 to 2023-02-18, with
   GPS control points, photographs and hazard mapping.
   File: `ingemmet_a7367_secocha_hazard_assessment.pdf`, 24,402,598 bytes, SHA-256
   `a0e667c8c20bb4e6e4f620cc447ad141060d50d3ef42efe15bb7b18fcc97b083`.
2. INDECI/COEN, *Informe de Emergencia N 1733*, 2023-05-20 (Informe N 13), *Lluvias intensas
   en el distrito de Mariano Nicolas Valcarcel - Arequipa*. Report-dated chronology and impact
   updates.
   File: `indeci_emergency_report_1733_2023-05-20.pdf`, 2,582,796 bytes, SHA-256
   `dc229300ff3bd4d18bcbef6e5ad2a9a7c5b7d469c3df0ab02b0749b4d13ae289`.

- Access date: 2026-08-07 (from the manifest)
- Access method: public HTTPS downloads; no account
- Source URLs and checksums: `outputs/secocha_2023_validation/official_reports_manifest.json`
- Download command: `.venv/bin/python bin/acquire/pull_secocha_2023_validation_reports.py`
- Local path: `data/validation/secocha_2023_validation/official_reports/`
- Derived outputs: `outputs/secocha_2023_validation/` (event facts with report date and page,
  affected locations, INGEMMET field anchors, INDECI response locations)

## Model-window sources (2026-08-09)

- Acquisition command: `.venv/bin/python bin/acquire/pull_peru_secocha_model_sources.py`
- Manifest with URLs, byte sizes and SHA-256:
  `outputs/peru_secocha_a7367_reference_extent_v1/source_acquisition/source_manifest.json`
- New local sources: SRTMGL1 v3 tile `S16W074`; INGEMMET small-mining layer-0 subset (26 records,
  external overlay only); SERNANP national definitive protected-area layer-0 query (zero records
  within 25 km).
- Reused sources: ESA WorldCover 2021 v200, WorldPop Peru 2020 UN-adjusted, Geofabrik Peru OSM.
- Runtime sources: CHIRPS v3 monthly Latin America windows for December-March 2014/15-2023/24 and
  ISRIC SoilGrids top-30-cm windows (`soilgrids_250m_peru_secocha`). Native resolutions are kept
  in the output manifests; 30 m is only the common grid.

## Map 7 event digitization (2026-08-09)

- Command: `.venv/bin/python bin/analysis/digitize_secocha_a7367_map7_event.py`
- Source: INGEMMET A7367, Map 7, PDF page 75, 1:25,000, WGS 84 / UTM zone 18S grid.
- Classes digitized: `Huaico del 5 de febrero` and `Flujo de lodo del 5 de febrero`. Rockfall,
  debris avalanche, generic debris flow and gully erosion are excluded.
- Method: legend-colour segmentation of a 300 dpi rendering, component cleanup, georeferencing on
  the printed grid; estimated registration uncertainty 10 m. The polygons have not been
  independently reviewed.
- Outputs: `outputs/secocha_2023_validation/observed_hazard/` (georeferenced Map 7 raster, class
  layers, combined footprint, comparison metrics, review figure).
- Result: footprint 0.211 km²; 66.2% of its 30 m cells have valid PIM values; of those, 19.1% are
  High versus 15.6% study-wide (1.22x); mean PIM 0.565 versus 0.528. No mining record intersects
  the footprint; 5 records are within 250 m and 9 within 500 m.

## Original INGEMMET GIS (2026-08-11)

- Command: `.venv/bin/python bin/acquire/pull_ingemmet_secocha_original_gis.py`
- Service: `SERV_PELIGROS_GEOLOGICOS`, MapServer layer 6, `Cartografia de Peligros`. Result:
  3 polygons with `CODIGO=A7367`, `FECHA_EVAL=febrero 2023` (`Avalancha de detritos`,
  `Flujo de detritos`, `Caída de rocas`). Layer 7 (`Cartografia Peligros Fotointerpretado`)
  returned no A7367 features.
- Local path:
  `data/raw/ingemmet_a7367_cartografia_peligros_secocha/ingemmet_a7367_cartografia_peligros_layer6_secocha.geojson`
- Manifest:
  `outputs/peru_secocha_a7367_reference_extent_v1/source_acquisition/ingemmet_original_gis_manifest.json`
- Result: the three polygons cover 6.364 km² (4.637 km² inside the reference window) and 93.8% of
  the digitized 5 February footprint (`Flujo de detritos` alone 84.3%). They are general A7367
  hazard cartography, not a dated 2023-02-05 footprint. Comparison:
  `outputs/secocha_2023_validation/observed_hazard/ingemmet_original_gis_comparison.json`

## Event-window CHIRPS daily rainfall (2026-08-12)

- Commands: `.venv/bin/python bin/acquire/pull_secocha_2023_event_rainfall.py` and
  `.venv/bin/python bin/acquire/pull_secocha_2023_event_rainfall_rnl.py`
- Product: CHC UCSB CHIRPS v3.0 daily final, `sat` and `rnl` GeoTIFFs, native 0.05 degree
  (`https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/`). Per-file HTTP size/ETag/Last-Modified
  in `outputs/secocha_2023_validation/rainfall/event_rainfall_manifest.json` and
  `outputs/secocha_2023_validation/rainfall_rnl/event_rainfall_rnl_manifest.json`.
- Window: reference extent plus 5 km, 2023-01-07 to 2023-02-10, native grid.
- Local paths: `data/validation/secocha_2023_validation/rainfall/chirps_v3_daily_event_window/`,
  `data/validation/secocha_2023_validation/rainfall/chirps_v3_rnl_daily_event_window/`
- Result: 2023-02-05 mean about 6.91 mm (`sat`) and 2.74 mm (`rnl`); 30-day means both about
  44.57 mm. Gridded daily values, not gauge data; `sat`/`rnl` are alternative temporal
  allocations of the same product. Comparison:
  `outputs/secocha_2023_validation/rainfall/rainfall_sat_vs_rnl_comparison.json`.
- SENAMHI station data: the nearest public legacy daily file (Caravelí 000746, about 30 km) ends
  2014-04-30; 2023 station data require a request via `https://www.senamhi.gob.pe/?p=solicitud-servicio`.

## Sentinel-1/2 before/after (2026-08-12 to 2026-08-18)

- Catalogue command: `.venv/bin/python bin/acquire/pull_secocha_sentinel_catalog.py`
  (`POST https://stac.dataspace.copernicus.eu/v1/search`, reference-window bbox,
  2023-01-20/2023-02-20). Request, response, footprints and SHA-256 in
  `outputs/secocha_2023_validation/satellite_before_after/sentinel_catalog_manifest.json`.
- Pixel commands (CDSE S3 account required):
  `.venv/bin/python bin/acquire/pull_secocha_sentinel_pixels.py --batch core_s2 --manifest outputs/secocha_2023_validation/satellite_before_after/sentinel_pixel_download_core_s2_manifest.json`
  and the same with `--batch s1_pair` and `sentinel_pixel_download_s1_pair_manifest.json`.
- Files: S2 L2A 2023-02-03 and 2023-02-08 (B02/B03/B04/B08, SCL, metadata; 14 files, about
  122.4 MiB); S1 GRD COG 2023-01-29 and 2023-02-10 (VV/VH, calibration/noise XML; 14 files, about
  2.41 GiB); quicklooks and footprint GeoJSON. All sizes match the STAC assets; per-file bytes and
  SHA-256 in the batch manifests.
- Local path: `data/validation/secocha_2023_validation/satellite_before_after/` (pixels under `pixels/`)
- Licence: Copernicus Data Space terms (`https://dataspace.copernicus.eu/data-access`).
- S2 processing: `.venv/bin/python bin/analysis/process_secocha_sentinel_validation.py`;
  NDWI=(B03-B08)/(B03+B08), water if NDWI > 0.15, SCL 4-7 valid. Outputs under
  `outputs/secocha_2023_validation/satellite_before_after/processed/` with
  `s2_optical_change_qa.json`. Result: 161,416 common valid 10 m pixels; no pixel meets the water
  threshold on either date (expected for a debris flow; not a footprint).
- S1 pixels are downloaded but not processed.

## Known limitations

- The Secocha reference extent is the coordinate frame of A7367 Map 7, not a catchment or event
  footprint. It lies about 117.7 km from the former Peru study area (`peru_hybas_l7_6070641200`).
- A hazard-assessment map is not automatically an observed footprint; map semantics were checked
  page by page.
- Affected localities and administrative event points do not give pixel-level extent.
- Early and later INDECI totals differ; extracted values keep report date and page.
