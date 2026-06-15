# V1 LS-Factor And USLE Annual Soil Loss Diagnostic

Date: 2026-06-15

Status: data-processing record for the LS-factor and the first USLE Annual Soil Loss (A)
diagnostic. Diagnostic data products, not interpretable validated soil-loss claims. The
absolute A values are NOT trustworthy until the R-factor bimodality is resolved; the spatial
structure (where erosion is relatively higher) is trustworthy.

## LS-Factor

- Script: `bin/derive_v1_ls_factor.py`. Formula: Moore & Nieber (1989) raster LS:
  `LS = (As / 22.13)^0.4 * (sin(theta) / 0.0896)^1.2`, As = specific contributing area (m),
  theta = slope angle. Both inputs on the V1 30 m grid.
- Outputs in `outputs/srtm_1arcsec_zimbabwe_prototype/ls_factor/`:
  - `v1_ls_factor_uncapped_30m.tif` - raw formula (nonsensical on high-SCA channel cells).
  - `v1_ls_factor_hillslope_30m.tif` - channel cells (>500 contributing cells) masked.
  - `v1_ls_factor_capped50_hillslope_30m.tif` - hillslope LS capped at 50 for USLE combination.
- Hillslope LS: mean 1.563, p50 0.864, p95 5.511, max 63.2 (sensible for moderate plateau terrain).

## USLE Annual Soil Loss Diagnostic (A = R x K x LS x C x P)

- Script: `bin/derive_v1_usle_soil_loss.py`. Outputs in `outputs/v1_usle_soil_loss/`.
- Scalars (V1 zonal means): K_SI = 0.02232, R_mean = 408 (bimodal), P = 1.
- Spatially varying at 30 m: LS (capped50 hillslope) and C.
- A is reported in three R scenarios because the V1 R-factor is bimodal:
  - `a_mean_30m.tif` (R=408): mean 0.50, p50 0.22, p95 1.96 t/ha/yr.
  - `a_low_R50_30m.tif` (R=50): mean 0.061 t/ha/yr.
  - `a_high_R510_30m.tif` (R=510): mean 0.625 t/ha/yr.
- `a_structure_K_LS_C_30m.tif` - the trustworthy spatial part (per-unit-R), isolating LS/C/K from
  the rainfall multiplier.
- `a_mean_classes_30m.tif` - severity classes on the mean case.

### Severity class distribution (A-mean, t/ha/yr)

| Class | Range | Cells | Share |
|---|---|---:|---:|
| 1 very low | 0-1 | 3,484,289 | ~87% |
| 2 low | 1-5 | 474,913 | ~12% |
| 3 moderate | 5-10 | 20,022 | ~0.5% |
| 4 high | 10-50 | 4,220 | ~0.1% |
| 5 very high | >50 | 167 | <0.01% |

Most of V1 is very-low erosion (<1 t/ha/yr), consistent with well-vegetated semi-arid shrubland on
moderate slopes. Erosion hotspots (high/very-high) cluster where steep slopes (high LS) coincide
with cropland or bare ground (high C).

## Methodological Caveats (flagged for mentor awareness)

1. **R bimodality**: the absolute A values depend on the Renard-Freimund piecewise R-factor,
   which is bimodal in V1 (discontinuity at MFI=80). The a_low/a_mean/a_high trio shows the
   sensitivity; absolute A is NOT trustworthy until R is methodologically reviewed.
2. **K and R as zonal scalars**: spatial variation of soil erodibility (250 m) and rainfall
   erosivity (5 km) is masked in this 30 m A raster (coarse->fine resampling is forbidden). The
   spatial structure comes from LS and C only. A future sub-basin aggregation (Branch 2) could
   carry K and R variation per zone.
3. **P=1**: no support-practice data; default assumption documented.
4. **Channel masking**: the hillslope LS formula is not meaningful on main-channel cells; these
   are masked, so the A raster reports sheet/rill erosion potential, not channel erosion.
5. **V1 boundary caveat**: V1 is an administrative basin boundary, not a surveyed watershed
   divide, so edge flow accumulation (and thus LS near the edge) underestimates true upslope area.

## USLE Factor Status

| Factor | Status | Notes |
|---|---|---|
| K | done | SoilGrids 250 m, Williams 1995; mean 0.1695 US / 0.0223 SI |
| R | done, FLAGGED | CHIRPS modified Fournier; bimodal, needs method review |
| LS | done | Moore-Nieber, hillslope-masked, capped50; mean 1.563 |
| C | done | WorldCover lookup; mean 0.0429 |
| P | documented default | P=1 |
| **A** | **done (diagnostic)** | **mean 0.50 t/ha/yr; spatial structure trustworthy, absolute R-dependent** |

## Scripts

- `bin/derive_v1_ls_factor.py`
- `bin/derive_v1_usle_soil_loss.py`
