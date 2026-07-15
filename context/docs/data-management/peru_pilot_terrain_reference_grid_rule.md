# Southern Peru Arequipa Region Terrain Reference Grid Rule

Status: active internal rule; the Peru analogue of `v1_terrain_reference_grid_rule.md`.

Last updated: 2026-06-30

Scope: Arequipa Region controlled raster preprocessing and grid compatibility for the
southern Peru comparison catchment in Arequipa Region, mainly the
Vitor-La Joya-Santa Rita de Siguas area west of Arequipa city. This rule does
NOT accept Arequipa Region as a final research-selected Peru study area and does NOT
authorize final flood-risk interpretation, intervention-priority
interpretation, or Zimbabwe-Peru comparison.

## Purpose

Use the current Arequipa Region DEM as the single reference raster for all Arequipa Region terrain-derived raster layers.
Any Peru terrain raster that does not exactly match this reference grid is not eligible for
standardization, weighted overlay, or scoring. This is independent of the Zimbabwe V1 reference
grid (different CRS, different transform, different boundary).

## Reference Raster

Reference raster:

`outputs/srtm_1arcsec_peru_pilot/terrain_preprocessing/peru_hybas_l7_6070641200_dem_utm18s_30m.tif`

The reference raster defines the Peru prototype terrain grid:

- CRS: `EPSG:32718` (UTM 18S, NOT Zimbabwe's EPSG:32735)
- resolution: `30 m`
- transform: `30.0, 0, 787128.312, 0, -30.0, 8213045.897` (must be inherited exactly)
- bounds: left 787128.31, bottom 8134175.90, right 864258.31, top 8213045.90
- width: `2571`, height: `2629`
- band count: `1`
- dtype: `float32`
- NoData: `-9999.0`

Future Arequipa Region terrain derivatives (slope, hydrology, TWI, LS, etc.) must match this reference raster's
CRS, transform, resolution, width, height, band count, dtype, NoData, and Arequipa Region valid-cell coverage
before standardization, scoring, or weighted overlay.

Incompatible rasters must be recorded as `grid_compatible=false` and blocked from overlay.

## Scale-Mismatch Rule (Same Principle As Zimbabwe)

CHIRPS and other coarse rainfall products must not be described as native 30 m information and
must not be resampled to the Arequipa Region 30 m grid as pixel-level evidence. Use native-resolution
diagnostics or catchment/sub-basin zonal summaries until a separate modelling-unit decision is
accepted. This is the same binding data-quality rule as the Zimbabwe V1 rule.

## What This Rule Does NOT Do

- It does not accept Arequipa Region as the final Peru study boundary.
- It does not authorize CHIRPS, AHP overlay, flood-risk interpretation, or
  intervention-priority interpretation.
- It does not merge the Peru and Zimbabwe reference grids; each country keeps its own.
- It does not accept a Zimbabwe-Peru comparison (requires harmonized criteria, still blocked).

## Reproducibility

Rebuild the reference DEM with:

```bash
.venv/bin/python bin/factors/preprocess_srtm_peru_pilot_dem.py
```

Source tiles: `S17W073`, `S17W072` under `data/raw/srtm_1arcsec_peru_pilot/`.
