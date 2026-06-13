# SRTM V1 Terrain Preprocessing Note

Updated: 2026-06-12

Status: DEM, QA hillshade, and slope diagnostics produced for controlled V1 terrain preprocessing.

## Scope

This step preprocesses the already-downloaded SRTMGL1 tiles for the V1 working boundary. V1
remains `accepted_with_waiver_for_controlled_prototype`; this step does not make V1 a final thesis
boundary and does not produce a flood-risk or intervention map.

## Inputs

- Raw SRTM source archives:
  `data/raw/srtm_1arcsec_zimbabwe_prototype/*.SRTMGL1.hgt.zip`
- V1 working boundary:
  `outputs/v1_working_boundary/v1_working_boundary.gpkg`
- Raw inventory:
  `outputs/srtm_1arcsec_zimbabwe_prototype/srtm_tile_inventory.csv`

No new data was downloaded for this step.

## Processing Rules

- Working CRS: `EPSG:32735` / WGS 84 UTM zone 35S.
- Output resolution: `30 m`.
- Output data type: `float32`.
- Output NoData: `-9999.0`.
- SRTM source NoData: `-32768`.
- Continuous elevation reprojection: bilinear resampling.
- Buffered DEM: V1 boundary plus `1 km` buffer, used to reduce edge effects when deriving slope.
- Slope: derived from the buffered DEM and then masked to the exact V1 grid, units in degrees.
- Hillshade: QA visualization only, not saved as an analysis raster.

## Outputs

- `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif`
- `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_buffered_utm35s_30m.tif`
- `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_slope_degrees_utm35s_30m.tif`
- `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_terrain_preprocessing_diagnostics.csv`
- `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_terrain_qa_map.png`
- `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_terrain_qa_map.pdf`
- `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_terrain_preprocessing_handoff.md`

## Diagnostics

Both final rasters are single-band `float32` GeoTIFFs in `EPSG:32735`, with `30 m` resolution and
NoData `-9999.0`. The DEM and slope rasters share the same shape, transform, CRS, and NoData
semantics.

| Raster | Valid inside V1 | Min | Max | Mean |
|---|---:|---:|---:|---:|
| DEM elevation, m | `1.0` | `863.04718` | `1531.481812` | `1136.947266` |
| Slope, degrees | `1.0` | `0.0` | `55.609856` | `3.852057` |

## Raster Grid Gate

Implemented gate script:

`bin/check_v1_raster_grid.py`

Latest manifest:

`outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_raster_grid_check.csv`

Gate result: the final V1 DEM and final V1 slope rasters are `grid_compatible=true` against the
V1 reference DEM. A failure probe with the buffered DEM correctly failed because the buffered
raster has a different transform, width, height, and bounds. The buffered DEM remains a processing
intermediate, not an overlay-ready terrain layer.

## Limits

This step does not include CHIRPS, flow direction, flow accumulation, drainage-distance proxy,
stream burning, hydrological conditioning, AHP-MCDA overlay, flood-risk interpretation, or
intervention-priority interpretation.

Before using slope in any scoring workflow, select the modelling-unit branch and define the
standardization rule for terrain indicators.
