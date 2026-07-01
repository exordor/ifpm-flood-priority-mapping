# V1 SoilGrids K-Factor Processing Note

Date: 2026-06-15

Status: data-processing note for the first V1 soil-erodibility (K-factor) output. Diagnostic data
product, not an interpretable sediment-risk claim. Produced under the data-processor scope
(data production GO; claims remain mentor-gated).

## Output

- `k_factor_0_5cm_250m.tif` - USLE K-factor at 0-5 cm (surface topsoil).
- `k_factor_0_30cm_avg_250m.tif` - depth-weighted average over 0-30 cm.
- `k_factor_diagnostics.json` - per-depth ranges and V1 zonal summary.
- Grid: 341 x 490 px at 250 m, Interrupted Goode Homolosine (ESRI:54017), float32, NoData -9999.
- NOT resampled to the V1 30 m terrain grid (per the V1 terrain reference grid rule).

## Source And Method

- SoilGrids 250m VRT collection at `https://files.isric.org/soilgrids/latest/data/`, read via
  rasterio HTTP windowed read for the V1 bounding box only. No global raster downloaded; only the
  V1 window (~85 x 123 km) was read for clay / silt / sand / soil-organic-carbon at the six
  standard SoilGrids depth slices.
- Access verified 2026-06-15 via CDP: directory listing, no login required.
- K-factor formula: Williams (1995) EPIC/RUSLE pedotransfer function (see
  `bin/factors/derive_v1_soilgrids_kfactor.py` docstring for the full equation).
- Units: K in US units; multiply by 0.1317 for SI (t ha h / ha MJ mm).
- SoilGrids storage convention applied: texture raw / 10 = percent; soc raw / 100 = percent C.

## V1 Zonal Results

- V1 valid cells: 58969 (250 m pixels inside the V1 boundary).
- K (0-5 cm, US units): mean 0.1695, range [0.082, 0.251].
- K (0-5 cm, SI units): mean 0.0223, range [0.011, 0.033].
- K (0-30 cm, US units): mean 0.1674, range [0.077, 0.253].
- K is stable across depth slices (0.166-0.170), consistent with a relatively uniform soil.

## Sanity Check

- Typical USLE K-factor (US units) for mineral soils: 0.10-0.40. V1 mean 0.17 is moderate-low,
  consistent with semi-arid sandy-loam soils in Matabeleland South.
- SI range 0.022 is within the typical 0.01-0.06 SI band.
- Depth stability indicates the result is not an artefact of a single noisy depth slice.

## Known Limitations

- K-factor is one of five USLE factors (R x K x LS x C x P). R, LS, C, P are still missing; a
  full sediment-risk map cannot be produced yet.
- SoilGrids is 250 m; it is deliberately kept at native resolution and must not be treated as
  30 m pixel-level truth.
- The Williams formula is one of several K pedotransfer functions; a mentor may prefer an
  alternative. The choice is documented here for review, not fixed.
- 22 V1 cells had no SoilGrids coverage (excluded from K).

## Methodological Note For Mentor

The depth choice (0-5 cm surface + 0-30 cm average) and the Williams formula are standard but
not the only options. If the mentor prefers a different depth convention (e.g. a single
representative depth) or a different pedotransfer function, the script can be re-run; the choice
is recorded here, not locked.

## Script

`bin/factors/derive_v1_soilgrids_kfactor.py` (root `.venv`; uses rasterio, geopandas, pyproj; playwright
was used only for the upstream portal check, not for this derivation).
