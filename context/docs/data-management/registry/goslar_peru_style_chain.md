# Dataset Registry: Goslar Peru-style PIM chain

Status: prototype chain complete; diagnostic-only outputs; not final flood risk.

## 2026-08-12 data-model repair

The chain was repaired to fix confirmed technical defects found in audit: (1) OSM
roads were rasterized in EPSG:4326 onto the EPSG:32632 grid, placing 0 road
pixels inside the focus box; roads are now projected to the metric CRS first
(5,931 rasterized pixels after fix). (2) WorldCover and SoilGrids NoData was
converted to 0; NoData is now preserved (soil_k keeps 2,661 NaN cells, not
filled). (3) hydrology was computed on the focus-clipped DEM, truncating upstream flow
accumulation; fill/D8/accumulation/streams/TWI now run on the +1 km buffered
DEM and are aligned back to the reference grid. The SoilGrids K source is now a
pinned local snapshot (no /latest/ drift). Outputs were regenerated.

On 2026-08-14, the temporary Goslar-specific LU/SV reweighting was withdrawn.
Goslar now retains the complete Secocha Supervisor v07 weight contract so the two
cases remain directly comparable. The all-zero Goslar bare-soil component and
the built-up critical-infrastructure proxy remain explicit local evidence
limitations; they do not trigger site-specific weight changes.

Also on 2026-08-14, a separate mining context overlay was added from official
LBEG/NIBIS mining-right polygons and OpenStreetMap mining features within a
12 km context radius. It is packaged for visual comparison only, has
`claim_level=context_evidence`, and is explicitly excluded from PIM scoring.

## Data Source Upgrade (2026-08-07)

The Goslar chain now uses more suitable official data than the first prototype:

- **DEM**: Copernicus DEM GLO-30 (`N51E010`, EPSG:4326, ~30 m) replaces SRTM
  1-arcsec. Downloaded from the public AWS Copernicus bucket
  (`copernicus-dem-30m`), 29.8 MB, SHA-256 verified at download. Better suited
  to the mountainous Harz terrain than SRTM. Access date 2026-08-07, licence
  Copernicus DEM open (ESA/Copernicus). SHA-256
  `ba72875033a3f201a6de462ced430bc19f8de771fd4cc493a52acecb19bbcd7f`.
- **Protected areas**: EEA official Natura 2000 2024 release (FFH layer + SPA
  layer) replaces the OSM protected-area proxy. Queried from the EEA ArcGIS
  REST service (`bio.discomap.eea.europa.eu`, MapServer query by bbox), 30
  polygons within the query box incl. Oberharzer Teichgebiet, Nationalpark
  Harz, Okertal, Hochharz. Stored as `goslar_natura2000_2024.gpkg`
  (SHA-256 `02bb8f574485e368e7cbff022058d75d038c00b86bd2a76ae4eb4cfe75d8d687`).
  Access date 2026-08-07, EEA re-use policy.
- **Population / exposure**: Destatis Zensus 2022 official 100 m grid
  (`Zensus2022_Bevoelkerungszahl_100m-Gitter.csv`, EPSG:3035) replaces WorldPop
  DEU 2020. Full national CSV (153 MB) filtered to the Goslar bbox and
  rasterised to a 100 m EPSG:3035 grid under `data/raw/zensus2022_goslar/`.
  Access date 2026-08-07, Destatis open data (DL-DE-BY-2.0). Derived raster
  SHA-256 `bf0369c88b8e718fb57adb01161a1d976f234295ac9b5ee2ea3c7de47f88c0c6`.
- **Rainfall**: DWD REGNIE JJA climatology extended from the 2014-2023 window
  to the official DWD 1991-2020 climate normal (30 years, 90 JJA monthly files
  used by the chain). 99 REGNIE files are present locally (1991-2023); the
  chain consumes the 1991-2020 JJA subset. REGNIE remains 1 km native,
  resampled to 30 m as a documented provisional coarse-to-reference step.
- **Soil K (pinned)**: SoilGrids 250 m clay/silt/sand/soc (0-5/5-15/15-30 cm)
  are now downloaded once to `data/raw/soilgrids_250m_goslar/` by
  `bin/acquire/pull_goslar_soilgrids_window.py` with SHA-256 provenance in
  `soilgrids_goslar_diagnostics.json`. K-factor uses the canonical Williams
  (1995) four-factor form (US units, 0-30 cm depth-weighted); the chain
  converts to SI with x0.1317. This replaces the un-versioned /latest/ remote
  read. K snapshot SHA-256 `86191741d2d15421...`.
- **Soil K**: BGR publishes an official K-factor layer, but only as a 1:1,000,000
  rendered ArcGIS/WMS service (no raw value export). SoilGrids K (250 m) is
  kept and documented as the working source; not a silent substitution.

## Experiment Identity

- Focus area id (2026-08-17 onward): `goslar_wrrl_water_bodies_reference_v1`,
  a 153.779 km2 union of official Lower Saxony WRRL water bodies intersecting
  the earlier ZLW layout extent. It is a provisional hydrologic reference,
  not an observed 2017 flood footprint.
- Boundary:
  `outputs/goslar_official_hydrology_and_flood_data/goslar_official_hydrologic_reference_boundary.gpkg`
- Minimum study-area anchor:
  `outputs/goslar_focus_boundary/goslar_focus_boundary.gpkg` (22.882 km2,
  original ZLW QGIS print-layout extent). The active WRRL reference fully
  contains this anchor. The anchor is visible in both Goslar QGIS packages,
  has weight 0, and must be contained by any future adopted Goslar study
  boundary. It is not a catchment, municipal boundary, or observed inundation
  footprint.
- Metric reference grid: EPSG:32632 (UTM 32N), 30 m, 635 x 611 cells
- Claim level: `provisional` / controlled prototype
- Enters Peru PIM score: no

## Chain Stages And Inputs

Runs via `.venv/bin/python bin/factors/run_goslar_peru_style_chain.py`:

1. register inputs - Copernicus DEM GLO-30 N51E010, ESA WorldCover N51E009,
   Zensus 2022 100 m grid (derived by acquire step)
2. boundary - active raster mask from the official WRRL union; the original
   ZLW focus extent is retained separately as the mandatory minimum study-area
   anchor and visible QGIS overlay
3. DEM - Copernicus DEM GLO-30, 30 m UTM 32N clipped to the active WRRL
   reference boundary; hydrology is derived on its configured buffer first
4. slope - central-difference degrees
5. hydrology - WhiteboxTools fill -> D8 -> flow accumulation -> streams (t500)
   -> distance to drainage -> TWI
6. LS factor - Moore & Nieber, capped 50, channel-masked
7. WorldCover C-factor - RUSLE C and land-use pressure LUTs (10 m -> 30 m)
8. SoilGrids K - Williams (1995) from clay/silt/sand/soc windows (250 m -> 30 m)
9. OSM roads - Overpass highway query within focus buffer, proximity score
10. rainfall - DWD REGNIE monthly grid, JJA (Jun-Aug) 1991-2020 mean (official
    30-y climate normal), 1 km native, provisional 30 m resample
11. protected areas - EEA Natura 2000 2024 (FFH + SPA, 30 polygons), proximity
    score
12. criteria stack - 2-98 percentile min-max standardization
13. exposure indicators - Zensus 2022 population + built + road proxies
14. environmental sensitivity - WorldCover water/wetland + EEA protected-area proximity
15. priority scenarios - Supervisor main weights

## Weights

- Main: FH 0.34 / SE 0.25 / LU 0.17 / ES 0.10 / SV 0.14
- FH components: rainfall 0.35 + TWI 0.25 + drainage 0.40
- SE: K 0.25 / LS 0.50 / C 0.25; LU: LC 0.40 / BV 0.35 / BE 0.25
- ES: water/wetland 0.65 + protected 0.35; SV: road 0.35 / settlement 0.35 / CI 0.30
- Weight contract: identical to Secocha Supervisor v07; no Goslar-specific
  reweighting. Candidate weights, not final.
- Current Goslar land-change component uses CLMS TCD decline 2018-2024 as a
  provisional vegetation-loss proxy. Critical infrastructure uses proximity
  to filtered OSM facility candidates; it is not an official facility inventory.
- NoData is preserved, not imputed; hydrology runs on the +1 km buffer.

## Data Sources (current)

- Rainfall: DWD REGNIE monthly grid (`opendata.dwd.de`, 1 km, EPSG:31467),
  JJA 1991-2020 mean (official 30-y climate normal). Files under
  `data/raw/dwd_regnie_germany/`. Acquire:
  `.venv/bin/python bin/acquire/pull_goslar_regnie_1991_2020.py`.
- Protected areas: EEA Natura 2000 2024 (FFH + SPA), queried by bbox from the
  EEA ArcGIS REST service, stored under `data/raw/eea_natura2000_goslar/`.
- DEM: Copernicus DEM GLO-30 N51E010 (AWS `copernicus-dem-30m` bucket),
  stored under `data/raw/copernicus_dem_30m_goslar/`.
- Population: Destatis Zensus 2022 100 m grid, filtered to bbox and rasterised
  to EPSG:3035, under `data/raw/zensus2022_goslar/`.
- Soil K: SoilGrids K (250 m); BGR official K-factor only exposed as a rendered
  1:1,000,000 WMS/ArcGIS service, kept out.
- OSM roads: Overpass API (kumi.systems mirror), `data/raw/geofabrik_osm_goslar/`.
- Mining context overlay: LBEG/NIBIS `Bergwerkseigentum` WFS (CC BY 4.0) plus
  OSM mine/adit/mineshaft/quarry features (ODbL), acquired by
  `bin/acquire/pull_goslar_mining_overlay.py`. The overlay does not enter the
  five-criterion score.

No current data gaps; all five criteria are scored.

## Outputs

- Priority map:
  `outputs/srtm_1arcsec_goslar/priority_scenarios/scenarios/priority_goslar_direct_pim.tif`
- Five criteria: `outputs/srtm_1arcsec_goslar/priority_scenarios/pim_criteria/`
- Criteria stack: `outputs/srtm_1arcsec_goslar/criteria_stack/criteria/`
- Run manifest: `outputs/srtm_1arcsec_goslar/priority_scenarios/run_manifest.json`
- Overview figure: `outputs/srtm_1arcsec_goslar/priority_scenarios/goslar_pim_overview.png`
- External mining overlay:
  `outputs/goslar_mining_context_overlay/goslar_mining_context_overlay.gpkg`
- QGIS project packages:
  `outputs/goslar_qgis_project_package/IFPM_Goslar_FullAudit.qgz` (workspace-linked),
  `exports/qgis_packages/goslar/FullAudit/IFPM_Goslar_FullAudit.qgz`
  (portable audit package), and
  `exports/qgis_packages/goslar/ReviewMap/IFPM_Goslar_ReviewMap.qgz`
  (portable scoring-focused review package).
  Build: `.venv/bin/python bin/package/build_goslar_qgis_project_package.py`;
  layer QA: `.venv/bin/python bin/validate/validate_goslar_qgis_layer_rendering.py`.
  FullAudit contains 36 governed layers and ReviewMap contains 24, in 7 groups
  following the processing chain. Both include the original ZLW focus extent
  as a visible, weight-0 minimum study-area anchor
  (priority result -> five criteria -> terrain/hydrology intermediates ->
  erosion factors -> rainfall -> exposure/environment -> context).
  The priority result and five top-level criteria use the same discrete
  equal-interval contract as the original Peru/Goslar figures: class upper
  bounds `0.2/0.4/0.6/0.8/1.0`, numeric class labels, and the criterion-specific
  ColorBrewer hex codes. Continuous interpolation is not used for these six layers.

## Known Limits And Release Boundary

- Hydrology uses a +1 km buffer so upstream flow accumulation is preserved;
  larger upstream basins would need a real catchment boundary (not available).
- NoData is preserved for WorldCover and SoilGrids; coarse-source coverage
  (soil_k ~94% within boundary) is documented, not imputed to 0.
- Focus box is a layout reference, not a validated catchment.
- SoilGrids and WorldCover are resampled to the 30 m grid; effective resolution
  remains 250 m / 10 m respectively.
- REGNIE is 1 km native rainfall evidence, not 30 m pixel truth; the FH rainfall
  component remains provisional and coarse-source.
- EEA Natura 2000 covers EU-designated FFH/SPA sites only; national designations
  (NSG etc.) outside Natura 2000 are not included, which may lower the
  protected-context score where purely national sites matter.
- Zensus 2022 counts residents at 100 m; institutional/business populations and
  non-resident exposure are not represented.
- Raw inputs and outputs stay local; public release requires explicit approval.
