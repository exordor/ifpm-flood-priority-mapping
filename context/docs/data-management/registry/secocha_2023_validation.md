# Dataset Registry: Secocha 2023 historical hazard event

Status: active Peru research-area evidence package; historical validation candidate, not a scored PIM input.

## Dataset Identity

- Dataset id: `secocha_2023_validation`
- Data class: `LOCAL_DATA`
- Event: Secocha 2023 debris-flow and flood-related disaster
- Event time: 2023-02-05, approximately 14:00 local time according to the later INDECI report
- Study area: Secocha, San Martin, Miski/Posco Misky, Pampa Blanca/Pampaylima and nearby
  localities in Mariano Nicolas Valcarcel district, Camana province, Arequipa department
- Project role: official evidence and historical-event comparison for the active
  Secocha Peru model window
- Claim level: `validation_candidate`
- PIM role: does not enter the PIM score and does not change criterion weights
- Reusable download: yes for internal analysis; redistribution terms must be checked before release

## Official Sources And Access

1. INGEMMET, *Informe Tecnico N A7367: Evaluacion de peligros geologicos en el centro
   poblado Secocha y las localidades La Poderosa, San Martin, Posco Misky y Pampaylima*.
   Public PDF served by SIGRID/CENEPRED. The report describes fieldwork conducted on
   2023-02-14 to 2023-02-18 and includes GPS control points, photographs and hazard mapping.
2. INDECI/COEN, *Informe de Emergencia N 1733*, dated 2023-05-20 (Informe N 13),
   *Lluvias intensas en el distrito de Mariano Nicolas Valcarcel - Arequipa*.
   This later report preserves report-dated chronology and impact updates.

- Access method: public HTTPS downloads; no account identified
- Access date: recorded by the generated manifest
- Source URLs and checksums: `outputs/secocha_2023_validation/official_reports_manifest.json`
- Download command:
  `.venv/bin/python bin/acquire/pull_secocha_2023_validation_reports.py`

## Active Model-Window Sources (2026-08-09)

- Acquisition command: `.venv/bin/python bin/acquire/pull_peru_secocha_model_sources.py`
- Source manifest with URLs, byte sizes and SHA-256 checksums:
  `outputs/peru_secocha_a7367_reference_extent_v1/source_acquisition/source_manifest.json`
- New local sources: SRTMGL1 v3 tile `S16W074`; INGEMMET small-mining layer-0
  subset (26 records, external overlay only); SERNANP national definitive
  protected-area layer-0 query (zero records within 25 km).
- Reused sources after coverage checks: ESA WorldCover 2021 v200, WorldPop Peru
  2020 UN-adjusted population, and the Geofabrik Peru OSM extract.
- Runtime sources: CHIRPS v3 monthly Latin America windows for December-March
  2014/15-2023/24 and ISRIC SoilGrids top-30-cm property windows. Their coarse
  native resolution is retained in the output manifests; 30 m is only the
  common overlay grid.

## Storage And Verification

- Raw destination: `data/validation/secocha_2023_validation/official_reports/`
- Partial-download destination: `data/tmp/secocha_2023_validation/`
- Derived outputs: `outputs/secocha_2023_validation/`
- Verification: require PDF signature, byte size and SHA-256 per source
- Expected first-stage footprint: approximately 25-35 MB for the two official PDFs

## Planned Processing

- Extract report-dated event facts without merging conflicting updates across publication dates.
- Separate official mapped/observed geometry from analyst-digitized geometry.
- Create affected-location and observed-hazard validation layers with source page anchors.
- Compare the event evidence with High/Very High cells in the current no-mining PIM.
- Add mining locations only as a separate co-location overlay, not causal or scored evidence.

## Map 7 Event Digitization Candidate (2026-08-09)

- Reproducible command:
  `.venv/bin/python bin/analysis/digitize_secocha_a7367_map7_event.py`
- Source anchor: INGEMMET A7367, Map 7, PDF page 75, printed scale
  1:25,000 and WGS 84 / UTM zone 18S coordinate grid.
- Extracted event-only classes: `Huaico del 5 de febrero` and
  `Flujo de lodo del 5 de febrero`. Rockfall, debris avalanche, generic debris
  flow and gully erosion remain excluded from the observed-event union.
- Outputs:
  `outputs/secocha_2023_validation/observed_hazard/` contains the approximately
  georeferenced Map 7 raster, separate class layers, their combined footprint
  candidate, comparison metrics and a review figure.
- Method boundary: legend-colour segmentation from a 300 dpi PDF rendering,
  component cleanup and printed-grid georeferencing. Estimated registration
  uncertainty is 10 m. This is a `validation_candidate`, not an official vector
  release or survey-grade event footprint.
- Current diagnostic result: candidate footprint area 0.211 km²; 66.2% of its
  30 m event cells have valid strict-common-support PIM values. Of that valid
  overlap, 19.1% is High versus 15.6% for the study area (1.22x enrichment),
  and mean PIM is 0.565 versus 0.528 for the study area. These are descriptive
  spatial comparisons, not accuracy or causal evidence.
- Mining remains external: no mining record intersects the candidate polygon;
  5 records are within 250 m, 9 within 500 m. Exact intersection and proximity
  do not establish mining causation.

## Original INGEMMET GIS Source (2026-08-11)

- Acquisition command:
  `.venv/bin/python bin/acquire/pull_ingemmet_secocha_original_gis.py`
- Official service: `SERV_PELIGROS_GEOLOGICOS`, MapServer layer 6,
  `Cartografia de Peligros`.
- Query result: 3 polygons, all with `CODIGO=A7367`, Secocha title metadata and
  `FECHA_EVAL=febrero 2023`: `Avalancha de detritos`, `Flujo de detritos`, and
  `Caída de rocas`.
- Raw destination:
  `data/raw/ingemmet_a7367_cartografia_peligros_secocha/ingemmet_a7367_cartografia_peligros_layer6_secocha.geojson`
- Source manifest:
  `outputs/peru_secocha_a7367_reference_extent_v1/source_acquisition/ingemmet_original_gis_manifest.json`
- The three original polygons cover 6.364 km² in total and overlap 4.637 km²
  of the active reference window. They cover 93.8% of the PDF-derived
  5 February candidate; the `Flujo de detritos` polygon alone covers 84.3%.
  The original service is stronger geometry evidence, but its layer semantics
  are general A7367 geological-hazard cartography, not an automatically
  confirmed 2023-02-05 observed footprint.
- The separate `Cartografia Peligros Fotointerpretado` layer 7 returned zero
  matching A7367 features. This is recorded as a negative source check, not as
  evidence that no other hazard data exist.
- Comparison output:
  `outputs/secocha_2023_validation/observed_hazard/ingemmet_original_gis_comparison.json`

## Current Spatial-Scope Check

- Checked on 2026-08-07 against
  `outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg`.
- Secocha anchor used: 695121 E, 8232667 N (WGS84 / UTM zone 18S), from A7367
  Figure 59, PDF page 51.
- Result: outside `peru_hybas_l7_6070641200`; nearest boundary distance is approximately
  117.7 km in EPSG:32718.
- The checked active PIM raster footprint also does not contain the Secocha anchor.
- On 2026-08-09, `peru_secocha_a7367_reference_extent_v1` replaced the former
  area as the active Peru boundary. The former `peru_hybas_l7_6070641200`
  model is frozen and retained only as the previous-area baseline.
- The active Secocha boundary is the 30 km² coordinate-frame reference extent
  of A7367 Map 7 (EPSG:32718); it contains the Secocha anchor but is not a
  digitized event footprint or hydrologic catchment.
- Consequence: the same criteria/normalization/weight contract has been rerun
  and the two explicit 5 February Map 7 classes now have a reproducible
  digitization candidate. Analyst polygon review and an independent observed
  footprint/source are still needed before calling this completed validation.

## Known Limits And Release Boundary

- A hazard-assessment map is not automatically an observed debris-flow footprint; map semantics
  must be checked page by page before digitization.
- Affected localities and administrative event points do not establish pixel-level inundation or
  debris-flow extent.
- Early and later INDECI totals may differ; every extracted value must retain report date and page.
- Raw reports, extracted images and analyst digitization stay local unless redistribution and
  public-safe release are explicitly approved.

## Event-window CHIRPS daily rainfall (2026-08-12)

- Acquisition commands:
  - `.venv/bin/python bin/acquire/pull_secocha_2023_event_rainfall.py`
  - `.venv/bin/python bin/acquire/pull_secocha_2023_event_rainfall_rnl.py`
- Official publisher/product: Climate Hazards Center, UCSB, CHIRPS v3.0 daily final
  `sat` and `rnl` GeoTIFF products, native 0.05 degree (approximately 5.5 km).
  Source URL templates and per-file HTTP size/ETag/Last-Modified evidence are in
  `outputs/secocha_2023_validation/rainfall/event_rainfall_manifest.json` and
  `outputs/secocha_2023_validation/rainfall_rnl/event_rainfall_rnl_manifest.json`.
- Window: active Secocha reference extent plus a 5 km buffer, 2023-01-07 through
  2023-02-10. The local stacks retain the native CHIRPS grid; no 30 m resampling is
  used for this event context.
- Local outputs:
  - `data/validation/secocha_2023_validation/rainfall/chirps_v3_daily_event_window/`
  - `data/validation/secocha_2023_validation/rainfall/chirps_v3_rnl_daily_event_window/`
  - `outputs/secocha_2023_validation/rainfall/`
  - `outputs/secocha_2023_validation/rainfall_rnl/`
- Diagnostic result: the `sat` crop has a 2023-02-05 mean of approximately 6.91 mm
  and the `rnl` crop approximately 2.74 mm; 30-day means are both approximately
  44.57 mm in this small window. These are gridded daily context values, not gauge
  observations and not a measurement of the INDECI-reported 14:00-14:17 peak.
- Claim/use boundary: `validation_candidate`, separate from the long-term rainfall
  criterion and excluded from the PIM score. `sat`/`rnl` are retained as alternative
  CHIRPS daily temporal allocations/sensitivity products, not independent observations
  and not merged into a single asserted measurement. The paired comparison is in
  `outputs/secocha_2023_validation/rainfall/rainfall_sat_vs_rnl_comparison.json` and
  `.csv`.
- Official documentation: `https://www.chc.ucsb.edu/data/chirps3` and the repository
  directory `https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/`.

## Copernicus Sentinel before/after catalogue (2026-08-12)

- Acquisition command: `.venv/bin/python bin/acquire/pull_secocha_sentinel_catalog.py`
- Official endpoint: `POST https://stac.dataspace.copernicus.eu/v1/search`, with the
  active Secocha boundary bbox and `2023-01-20/2023-02-20` datetime window. The complete
  request and response JSON, selected footprints and SHA-256 values are recorded in
  `outputs/secocha_2023_validation/satellite_before_after/sentinel_catalog_manifest.json`.
- Selected scene context: same-orbit Sentinel-1 GRD VV/VH scenes on 2023-01-29 and
  2023-02-10 (full active-window overlap); low-cloud Sentinel-2 L2A scenes on
  2023-02-03, 2023-02-08 and 2023-02-13 (partial T18LXH overlap); and full-overlap
  R082 scenes on 2023-01-22 and 2023-02-11. Seven public quicklooks and a selected
  footprint GeoJSON were saved for review.
- Local metadata and quicklooks:
  `data/validation/secocha_2023_validation/satellite_before_after/`.
- Access boundary: STAC metadata, footprint, asset links and thumbnails were available
  without credentials. Quantitative S1/S2 pixel assets point to CDSE S3 and require a
  registered account/token; no credentialed pixel download is claimed. Quicklooks are
  visual context only. The event chronology is 2023-02-05 14:00-14:17 PET
  (19:00-19:17 UTC); sensing datetimes remain in UTC in the STAC records.
- Terms: metadata/quicklook reuse remains subject to current Copernicus Data Space
  access and attribution terms; quantitative assets are account/token-gated. See
  `https://dataspace.copernicus.eu/data-access` and the OData/S3 documentation links
  above before redistribution.
- Claim/use boundary: `validation_candidate`; no Sentinel layer enters the PIM score.
  If credentials become available, the next step is radiometric/terrain-corrected S1
  log-ratio and cloud-masked S2 native-resolution change analysis.
- Official documentation: `https://documentation.dataspace.copernicus.eu/APIs/STAC.html`,
  `https://documentation.dataspace.copernicus.eu/APIs/OData.html`, and
  `https://documentation.dataspace.copernicus.eu/APIs/S3.html`.

## Copernicus Sentinel quantitative raw pixels (2026-08-18)

- Acquisition commands, using the ignored local CDSE S3 credential file:
  - `.venv/bin/python bin/acquire/pull_secocha_sentinel_pixels.py --batch core_s2 --manifest outputs/secocha_2023_validation/satellite_before_after/sentinel_pixel_download_core_s2_manifest.json`
  - `.venv/bin/python bin/acquire/pull_secocha_sentinel_pixels.py --batch s1_pair --manifest outputs/secocha_2023_validation/satellite_before_after/sentinel_pixel_download_s1_pair_manifest.json`
- Credential file: `data/tmp/cdse_s3_credentials.json` (ignored, local only). Outputs record
  its SHA-256 and credential source but never copy access keys, secret keys, endpoints or
  tokens into the repository.
- Core S2 batch: the selected 2023-02-03 pre-event and 2023-02-08 post-event L2A scenes,
  10 m B02/B03/B04/B08, 20 m SCL, manifest.safe and product metadata. Fourteen files,
  approximately 122.4 MiB, all matching the STAC asset sizes.
- S1 batch: the same-orbit 2023-01-29 pre-event and 2023-02-10 post-event GRD COG scenes,
  VV/VH measurement TIFFs plus calibration/noise annotation XML and manifest.safe. Fourteen
  files, approximately 2.41 GiB, all matching the STAC asset sizes.
- Local destination:
  `data/validation/secocha_2023_validation/satellite_before_after/pixels/`.
  Batch manifests with per-file byte size and SHA-256 are under
  `outputs/secocha_2023_validation/satellite_before_after/`.
- Claim/use boundary: these are raw quantitative assets, not analysis-ready validation.
  S1 still requires radiometric calibration/noise removal, terrain correction and
  co-registration. S2 requires native-resolution cloud masking using SCL and consistent
  band co-registration. No Sentinel layer enters the PIM score. The event chronology is
  2023-02-05 14:00-14:17 PET; sensing datetimes remain UTC in source metadata.

## SENAMHI station-data limitation (2026-08-12)

- The nearest publicly exposed legacy daily station file checked was Caravelí station
  000746 (about 30 km away), but it ends on 2014-04-30. Camaná's historical file is
  unavailable in the public endpoint. Recent 2023 station data require SENAMHI's
  authenticated portal or a formal historical-data request, so they are not silently
  represented as acquired data here.
- Official request route: `https://www.senamhi.gob.pe/?p=solicitud-servicio`.
- This is an access/data-availability blocker for sub-daily gauge validation, not a
  reason to treat CHIRPS daily values as local observations.

## Processed Sentinel-2 optical change candidate (2026-08-18)

- Processing command:
  `.venv/bin/python bin/analysis/process_secocha_sentinel_validation.py`
- Input pair: Sentinel-2 L2A 2023-02-03 (pre-event) and 2023-02-08 (post-event),
  from the hash-verified core-pixel batch.
- Method: NDWI=(B03-B08)/(B03+B08), water candidate NDWI > 0.15. Valid SCL classes
  are 4-7; the 20 m SCL mask is applied to the 10 m optical grid and outputs are
  clipped to the active Secocha reference window with a small review margin.
- Outputs under
  `outputs/secocha_2023_validation/satellite_before_after/processed/`:
  before/after NDWI, before/after surface-water candidates, persistent/new/lost
  surface-water candidates, and `s2_optical_change_qa.json`.
- Result: 300,000 10 m pixels fall inside the reference window; 240,644 are valid
  before and 165,024 after. The common valid support is 161,416 pixels. No pixels
  meet the NDWI water threshold in either date, so all persistent/new/lost water
  candidate counts are zero. This is a negative NDWI diagnostic, not evidence that
  no debris flow occurred.
- Interpretation boundary: the event was a debris-flow/mudflow disaster rather than
  an open-water flood. Post-event sediment/deposition can increase bare surface
  reflectance without satisfying a positive NDWI water threshold. The result cannot
  be used as an event footprint, accuracy measure, or causal evidence.
