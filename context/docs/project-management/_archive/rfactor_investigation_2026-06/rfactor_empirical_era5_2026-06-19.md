# Empirical ERA5 EI30 R-factor: arbitrating the two literature R-families (2026-06-19)

Status: EXPLORATORY experiment. Computes an empirical USLE/RUSLE R-factor from ERA5 hourly
precipitation to compare against the HIGH vs LOW R-families identified in
`rfactor_method_exploration_2026-06-19.md`. The ERA5 R is a lower bound (hourly != 30-min), so this
is supporting evidence for the method decision, not a validated R.

## Why this experiment

The literature comparison split R-factor methods into two incompatible families ~6x apart:
- HIGH (~1380-3719): Renard-Freimund, Arnoldus, AND the Zimbabwe-native Elwell/Stocking 1976.
- LOW (~240-320): Hurni 1985, Epworth/Merritt.

Pure literature reasoning could not decide between them, and the only "measured" anchor (Epworth
329) turned out to be circular (computed from the LOW-family equation). This experiment adds an
INDEPENDENT empirical R computed directly from hourly rainfall (ERA5 via open-meteo, no auth
required), to see where the hourly lower-bound estimate sits relative to the two families.

GPM IMERG (half-hourly, ideal) requires a NASA Earthdata account that is unavailable; ERA5 hourly
via open-meteo is the best no-authentication high-temporal-resolution source. CHIRPS daily cannot
yield EI30.

## Method (standard EI30 algorithm, verified from literature)

1. ERA5 hourly precipitation for 7 points across V1 (lon 28.56-29.35, lat -20.96 to -20.03),
   2018-2023 (6 years), via open-meteo.
2. Storm segmentation: runs of wet hours separated by >= 6 dry hours; erosive if total depth
   >= 12.0 mm (USLE ~12.7 mm threshold).
3. Unit kinetic energy, two forms:
   - Wischmeier-Smith SI: `e = 0.119 + 0.0873*log10(i)` MJ ha-1 mm-1, capped at i=76 mm/h.
   - Brown-Foster (RUSLE): `e = 0.29*(1 - 0.72*exp(-0.05*i))` MJ ha-1 mm-1.
4. Storm energy E = sum(e_i * depth_i) [MJ/ha].
5. I30: ERA5 is hourly, so the true 30-min I30 is unobservable. Report I60 (max hourly intensity)
   as a LOWER BOUND, and an I30 estimate = I60 * 1.1 (rough convective upscaling, labelled).
6. Annual R = sum of erosive-storm (E * I30) over each year; report the 6-year mean.

## Results

Spatial-mean empirical R over 7 V1 points, 2018-2023:
- Wischmeier-Smith KE, I60 lower bound: **R = 460**
- Brown-Foster KE, I60 lower bound: **R = 358**
- Wischmeier-Smith KE, I30 estimate (x1.1): **R = 506**
- Brown-Foster KE, I30 estimate (x1.1): **R = 394**

Per-point empirical R ranges 256-532 (I60 lower bound) across the catchment; spatial pattern is
plausible (higher in the wetter north/centre).

Comparison:
| | R value | relation to empirical (~360-506) |
|---|---:|---|
| LOW family (Hurni/Epworth) | 240-320 | empirical is ~1.1-1.6x (close, slightly above) |
| **Empirical ERA5** | **358-506** | (this experiment) |
| HIGH family (RF/Arnoldus/Elwell) | 1380-3719 | empirical is ~3-7x BELOW |

## Key finding

**The empirical ERA5 lower-bound R sits near the lower range and well below the high-family values.
Because ERA5 is hourly rather than true 30-minute breakpoint rainfall, this is supporting evidence
for the mentor method decision, not a final R validation.**

This is the first non-circular check in the family comparison. It raises a serious transferability
question for the high-family formulas, including the Elwell/Stocking relation as it currently
reaches this project, but it does not by itself settle the correct R method.

### Reconciliation
- The high-family values are much larger than the ERA5 hourly lower-bound check. The Elwell
  relation reaching us via Renard-Freimund 1994 may itself carry a unit or definition issue.
- The lower-family values are closer to the ERA5 check, but Hurni/Epworth remain proxy equations
  and are not final Zimbabwe/V1 calibrations.

## Implications for the project

1. The empirical evidence makes the lower range plausible and makes the high-family transfer
   questionable, but the R method still needs a mentor decision.
2. The strongest candidate remains a region-appropriate R. Hurni (1985) and the Epworth equation
   are both in the right magnitude; a Zimbabwe-specific calibration (if Elwell's original can be
   obtained and its units clarified) could refine it.
3. Absolute A values remain blocked. The ERA5-derived A outputs are diagnostic sensitivity outputs
   only and should not be sent as accepted soil-loss evidence.
4. This does NOT validate the deprecated V1 R; it only shows why the R method has to be chosen
   carefully before any A re-run.

## Caveats (strict)

- ERA5 is hourly, not 30-min breakpoint, so the computed R is a LOWER BOUND. I30 estimate via
  I60*1.1 is a rough assumption, reported separately.
- ERA5 reanalysis can under-estimate convective storm intensity in semi-arid tropical regions;
  gauge or IMERG data would be more reliable but require auth/unavailable.
- 7 sample points, not a full grid; spatial mean is indicative.
- This is supporting evidence for a method decision, NOT a validated quantitative R for V1.
- This does NOT re-derive the V1 R or replace the deprecated products.

## Outputs

- `outputs/v1_usle_soil_loss/rfactor_empirical_era5/era5_empirical_rfactor_diagnostics.json` (7-point family arbitration)
- `outputs/v1_usle_soil_loss/rfactor_empirical_era5/mentor_era5_empirical_rfactor_board.{png,pdf}`
- `outputs/v1_usle_soil_loss/rfactor_empirical_era5/mentor_era5_empirical_rfactor_caption.md`
- Raw series: `data/raw/era5_hourly_precip_v1_rfactor/era5_hourly_<pt>_2018-2023.json`
- Tooling: `bin/compute_era5_empirical_rfactor.py`, `bin/plot_era5_empirical_rfactor_board.py`

## Extension: spatial R raster and USLE A (2026-06-19)

The 7-point experiment was extended to a denser V1 grid (45 points at ~0.12 deg, ERA5 hourly
2018-2023), interpolated to a 0.05 deg R raster, and used to recompute USLE A with the clean
R-invariant a_structure.

- Headline empirical R (Wischmeier-Smith I30 est) V1 zonal mean over 45 points = **507** (matches
  the 7-point 506, confirming spatial stability).
- USLE A_zonal (R=507 as catchment scalar): mean = **0.621 t/ha/yr**.
- USLE A_spatial (DIAGNOSTIC, R resampled to 30m): mean = **0.619 t/ha/yr**.
- A_zonal and A_spatial agree to <1%, confirming the soil-loss hotspot pattern is governed by
  LS x C (R-invariant a_structure), not by R spatial variation.

Additional outputs:
- `outputs/v1_usle_soil_loss/rfactor_empirical_era5/r_empirical_era5_<form>_0p05deg.tif` (4 R rasters: WS/BF x I60/I30)
- `outputs/v1_usle_soil_loss/rfactor_empirical_era5/a_empirical_era5_zonal_30m.tif`
- `outputs/v1_usle_soil_loss/rfactor_empirical_era5/a_empirical_era5_spatial_DIAGNOSTIC_30m.tif`
- `outputs/v1_usle_soil_loss/rfactor_empirical_era5/era5_rfactor_raster_diagnostics.json`
- `outputs/v1_usle_soil_loss/rfactor_empirical_era5/mentor_era5_rfactor_raster_board.{png,pdf}`
- Raw grid series: `data/raw/era5_hourly_precip_v1_rfactor/grid_<lon>_<lat>_2018-2023.json`
- Tooling: `bin/build_era5_rfactor_raster.py`, `bin/plot_era5_rfactor_raster_board.py`

This moves the empirical R from a point check to a spatially-explicit diagnostic layer. The A
outputs are retained only as sensitivity diagnostics. They do not replace the deprecated V1
products and should not be used as accepted soil-loss evidence unless the mentor accepts the R
source and the workflow is re-run under a documented decision.

## Sources

- Wischmeier, W.H. & Smith, D.D. (1978). Predicting rainfall erosion losses. USDA AH-537.
- Brown, L.C. & Foster, G.R. (1987). Storm erosivity using idealized intensity distributions.
  Trans. ASAE 30, 379-386.
- ERA5 (Hersbach et al. 2020) via open-meteo archive API.
- Renard, K.G. & Freimund, J.R. (1994). J. Hydrology 157. (for the Elwell table reproduction.)
