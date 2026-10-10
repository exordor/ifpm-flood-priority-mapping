# Dataset Registry: Goslar chain input sources

Status: downloaded 2026-08-07 to 2026-08-17; inputs of the Goslar five-criterion PIM chain
(`bin/factors/run_goslar_peru_style_chain.py`). Chain stages, weights and repairs are in
`context/docs/research-map/EXPERIMENTS.md` ("Goslar input chain notes").

## Sources

- **DEM**: Copernicus DEM GLO-30 tile `N51E010` (EPSG:4326, ~30 m) from the public AWS bucket
  `copernicus-dem-30m`. Access date 2026-08-07; Copernicus DEM licence. 29.8 MB, SHA-256
  `ba72875033a3f201a6de462ced430bc19f8de771fd4cc493a52acecb19bbcd7f`.
  Local path: `data/raw/copernicus_dem_30m_goslar/`.
- **Land cover**: ESA WorldCover 10 m 2021 v200, tile `N51E009`.
  Local path: `data/raw/esa_worldcover_2021_goslar/`.
- **Protected areas**: EEA Natura 2000, 2024 release (FFH + SPA layers), queried by bbox from the
  EEA ArcGIS REST service (`bio.discomap.eea.europa.eu`); 30 polygons including Oberharzer
  Teichgebiet, Nationalpark Harz, Okertal and Hochharz. Access date 2026-08-07; EEA re-use policy.
  File `goslar_natura2000_2024.gpkg`, SHA-256
  `02bb8f574485e368e7cbff022058d75d038c00b86bd2a76ae4eb4cfe75d8d687`.
  Local path: `data/raw/eea_natura2000_goslar/`.
- **Population**: Destatis Zensus 2022 100 m grid
  (`Zensus2022_Bevoelkerungszahl_100m-Gitter.csv`, EPSG:3035, 153 MB national CSV), filtered to
  the Goslar bbox and rasterized to 100 m EPSG:3035. Access date 2026-08-07; DL-DE-BY-2.0.
  Derived raster SHA-256 `bf0369c88b8e718fb57adb01161a1d976f234295ac9b5ee2ea3c7de47f88c0c6`.
  Local path: `data/raw/zensus2022_goslar/`.
- **Rainfall**: DWD REGNIE monthly grid (`opendata.dwd.de`, 1 km, EPSG:31467); 99 monthly files
  1991-2023, of which the 90 June-August files of 1991-2020 are used.
  Command: `.venv/bin/python bin/acquire/pull_goslar_regnie_1991_2020.py`.
  Local path: `data/raw/dwd_regnie_germany/`.
- **Soil K**: SoilGrids 250 m clay/silt/sand/SOC (0-5/5-15/15-30 cm), pinned local windows with
  SHA-256 in `soilgrids_goslar_diagnostics.json`.
  Command: `.venv/bin/python bin/acquire/pull_goslar_soilgrids_window.py`.
  Local paths: `data/raw/soilgrids_250m_goslar/` (focus window) and
  `data/raw/soilgrids_250m_goslar_official_basin/` (official-basin window, used since 2026-08-17).
  BGR's official K-factor layer exists only as a rendered 1:1,000,000 WMS/ArcGIS service and is
  not used.
- **Roads**: OSM via Overpass (kumi.systems mirror); ODbL. Local paths:
  `data/raw/geofabrik_osm_goslar/` and, for the official-basin window,
  `data/raw/goslar_official_hydrology_and_flood_data/osm_goslar_official_basin_roads.gpkg`.
- **Critical infrastructure, boundary, bare soil, mining overlay**: see
  `goslar_official_hydrology_flood_infrastructure`, `clms_hrl_bare_soil_tcd_goslar` and
  `goslar_mining_context_overlay_v1`.

## Known limitations

- SoilGrids (250 m), WorldCover (10 m) and REGNIE (1 km) are resampled to the 30 m grid; their
  effective resolution is unchanged.
- Natura 2000 covers EU-designated FFH/SPA sites only; national designations (NSG etc.) are not
  included.
- Zensus 2022 counts residents at 100 m; workplace and visitor populations are not represented.
