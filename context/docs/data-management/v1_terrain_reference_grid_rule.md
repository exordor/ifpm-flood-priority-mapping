# V1 Terrain Reference Grid Rule

Status: active internal rule; executable gate implemented

Last updated: 2026-06-13

Scope: V1 controlled prototype terrain preprocessing only. This rule does not accept V1 as the
final thesis boundary and does not authorize CHIRPS, AHP overlay, flood-risk interpretation, or
intervention-priority interpretation.

## Purpose

Use the current V1 DEM as the single reference raster for all V1 terrain-derived raster layers.
Any terrain raster that does not exactly match this reference grid is not eligible for
standardization, weighted overlay, or scoring.

## Reference Raster

Reference raster:

`outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif`

The reference raster defines the prototype terrain grid:

- CRS: `EPSG:32735`
- resolution: `30 m`
- transform: must be inherited exactly
- bounds: must match the reference raster bounds
- width and height: must match the reference raster shape
- band count: `1`
- dtype: `float32`
- NoData: `-9999.0`
- validity mask: V1 working boundary mask
- minimum valid-cell fraction inside V1: `>= 0.98`

## Applies To

This rule applies to V1 terrain-derived rasters, including:

- clipped or reprojected DEM analysis copies;
- slope;
- hillshade if it is ever promoted beyond QA visualization;
- future terrain-only indicators such as curvature, topographic wetness proxies, or
  drainage-distance proxies.

This rule does not apply directly to:

- raw source data under `data/raw/`;
- vector layers such as boundaries, rivers, roads, settlements, or mining evidence;
- CHIRPS rainfall rasters;
- sub-basin or catchment-level summary tables.

## Required Script Enforcement

Every script that writes a V1 terrain raster intended for later standardization, overlay, or
scoring must read the reference DEM and assert grid compatibility before the output is treated as
usable.

Minimum compatibility check:

```python
with rasterio.open(reference_dem) as ref, rasterio.open(candidate_raster) as src:
    assert src.crs == ref.crs
    assert src.transform == ref.transform
    assert src.width == ref.width
    assert src.height == ref.height
    assert src.count == 1
    assert src.nodata == -9999.0
    assert src.dtypes[0] == "float32"
```

If a raster fails any required check, the script must not mark it as an overlay-ready output.
The failure must be recorded as `grid_compatible=false` in diagnostics or handoff notes.

## Diagnostics Manifest Requirement

Every processed V1 terrain raster must be recorded in a diagnostics CSV or equivalent internal
handoff with these fields:

- path
- source
- CRS
- transform
- width
- height
- resolution
- band count
- dtype
- NoData
- min
- max
- mean
- valid-cell fraction inside V1
- grid-compatible: `true` or `false`

Only rasters with `grid-compatible=true` may enter a later standardization or scoring step.

## Overlay Gate

Before any V1 terrain standardization, scoring, or weighted overlay, run the dedicated grid gate:

`bin/check_v1_raster_grid.py`

The gate must do one job only: compare every candidate terrain raster against the reference DEM.
If any raster differs in CRS, transform, width, height, band count, dtype, NoData, or V1 valid-cell
coverage, the downstream step is blocked.

Current gate manifest:

`outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_raster_grid_check.csv`

Current default checked rasters:

- `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_dem_utm35s_30m.tif`
- `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_slope_degrees_utm35s_30m.tif`

Both default rasters must be `grid_compatible=true` before any terrain standardization step.

## CHIRPS Scale Constraint

CHIRPS must not be forced onto the V1 30 m terrain grid for pixel-level overlay. Its source
resolution is much coarser than SRTM-derived terrain layers.

Allowed CHIRPS handling before a separate modelling-unit decision:

- native-resolution rainfall diagnostics;
- catchment-level zonal summaries;
- sub-basin-level zonal summaries.

Blocked CHIRPS handling:

- resampling CHIRPS to the V1 30 m grid and treating the result as 30 m evidence;
- mixing CHIRPS pixels with terrain rasters in a cell-by-cell weighted overlay before a separate
  modelling-unit decision. If a future coarse rainfall visualization is approved, it must be
  labelled as a zonal or coarse-summary product, not as 30 m rainfall evidence.

## Data Governance

- Raw SRTM archives remain unchanged under `data/raw/srtm_1arcsec_zimbabwe_prototype/`.
- Processed terrain rasters and diagnostics remain under
  `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/`.
- This rule is internal context and must not make public pipeline examples depend on root
  `context/`, `data/`, or `outputs/`.
- V1 remains `accepted_with_waiver_for_controlled_prototype`, not a final thesis boundary.
