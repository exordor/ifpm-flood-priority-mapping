# USLE Factor Batch Processing History (2026-06-15)

Merged 2026-07-05 from three notes of the same 2026-06-15 USLE factor batch:
K-factor (SoilGrids), LS-factor + USLE A diagnostic, and the consolidated
batch note (R/hydrology/C). Original content preserved verbatim below.

## Part 1 — K-factor (SoilGrids)


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

## Part 2 — LS-factor And USLE Soil Loss


Date: 2026-06-15

Status: data-processing record for the LS-factor and the first USLE Annual Soil Loss (A)
diagnostic. Diagnostic data products, not interpretable validated soil-loss claims. The
absolute A values are NOT trustworthy until the R-factor bimodality is resolved; the spatial
structure (where erosion is relatively higher) is trustworthy.

## LS-Factor

- Script: `bin/factors/derive_v1_ls_factor.py`. Formula: Moore & Nieber (1989) raster LS:
  `LS = (As / 22.13)^0.4 * (sin(theta) / 0.0896)^1.2`, As = specific contributing area (m),
  theta = slope angle. Both inputs on the V1 30 m grid.
- Outputs in `outputs/srtm_1arcsec_zimbabwe_prototype/ls_factor/`:
  - `v1_ls_factor_uncapped_30m.tif` - raw formula (nonsensical on high-SCA channel cells).
  - `v1_ls_factor_hillslope_30m.tif` - channel cells (>500 contributing cells) masked.
  - `v1_ls_factor_capped50_hillslope_30m.tif` - hillslope LS capped at 50 for USLE combination.
- Hillslope LS: mean 1.563, p50 0.864, p95 5.511, max 63.2 (sensible for moderate plateau terrain).

## USLE Annual Soil Loss Diagnostic (A = R x K x LS x C x P)

- Script: `bin/factors/derive_v1_usle_soil_loss.py`. Outputs in `outputs/v1_usle_soil_loss/`.
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

- `bin/factors/derive_v1_ls_factor.py`
- `bin/factors/derive_v1_usle_soil_loss.py`

## Part 3 — Consolidated Batch Note (R/Hydrology/C)


Date: 2026-06-15

Status: data-processing record for three USLE/RUSLE factor outputs produced in parallel.
Diagnostic data products, not interpretable sediment-risk claims. Produced under the
data-processor scope (data production GO; claims remain mentor-gated). Detailed per-factor
processing notes live alongside the data under `outputs/`; this note consolidates and flags
methodological items needing mentor awareness.

## USLE Progress (5 factors)

| Factor | Status | Output location | Key value |
|---|---|---|---|
| K (soil erodibility) | done (earlier) | `outputs/soilgrids_250m_sediment_candidate/` | mean 0.1695 US @ 250m |
| **R (rainfall erosivity)** | **done (this batch)** | `outputs/chirps_v3_zimbabwe_prototype/r_factor/` | mean 408 @ 0.05 deg (see flag) |
| LS (slope length/steepness) | unblocked now (needs hydrology) | pending | needs flow accumulation (now ready) + slope |
| **C (cover management)** | **done (this batch)** | `outputs/esa_worldcover_2021_v1_methodology/c_factor/` | mean 0.0429 @ 30m |
| P (support practice) | documented default P=1 | - | assumption recorded |

## R-Factor (CHIRPS Modified Fournier)

- Script: `bin/factors/derive_v1_chirps_rfactor.py`. Native CHIRPS 0.05 deg grid, V1 window, 132 cells.
- P_annual mean 583 mm/yr (1981-2024 climatology, matches expected).
- Modified Fournier Index (Nov-Mar 5 months) mean 92.9, range 70-117.
- R-factor: mean 408, range 45-517 MJ mm ha-1 h-1 yr-1.

### METHODOLOGICAL FLAG: Bimodal R-factor (needs mentor review)

The Renard-Freimund (1994) piecewise conversion has a discontinuity at MFI=80: the low branch
gives R~56 at the crossover and the high branch gives R~517 at the crossover (a ~9x jump). V1's
MFI range (70-117) straddles 80, so the output is strongly bimodal: 29 cells R<100, 103 cells
R>400, and 0 cells in between. This is a property of the exact piecewise formula implemented
verbatim, not a coding bug.

This needs a methodological decision before R is used in any USLE overlay. Options the mentor
should consider:
- accept the bimodality (it separates lower- and higher-MFI zones sharply);
- use a single smooth R-MFI relationship;
- verify the coefficient set against the original Renard-Freimund (1994) paper (the modified
  vs original Fournier index use different coefficients).

Until then, the R-factor is a diagnostic only. The limitation is also recorded in
`outputs/chirps_v3_zimbabwe_prototype/r_factor/r_factor_processing_note.md` and the diagnostics
JSON. CHIRPS was NOT resampled to 30 m.

## Hydrology Derivatives (whitebox on V1 DEM)

- Script: `bin/factors/derive_v1_hydrology.py`. All 10 outputs on the V1 30 m grid (EPSG:32735), all
  grid_compatible=true per `bin/package/check_v1_raster_grid.py`.
- Outputs: filled DEM, D8 flow direction, flow accumulation (cells + SCA), streams at thresholds
  100/500/1000/5000, distance-to-drainage (t500 primary), TWI.
- Max flow accumulation: 4,036,878 cells = 3633 km2 (~98.5% of V1 reaches the main outlet, sane).
- Chosen channel threshold: t500 = 0.45 km2 per initiating cell; drainage density 0.951 km/km2.
- TWI range 3.13-27.23, mean 7.81.

### Engineering note

The subagent found and fixed a float32-vs-float64 routing bug: Wang-Liu fill writes a sub-mm
plateau gradient that float32 epsilon destroys, causing pit cells. Routing runs on the raw
float64 filled DEM; only final products are cast to float32. The delivered `v1_dem_filled.tif`
is a float32 product, not a routing input.

### Domain caveat

V1 boundary is an administrative/ HydroBASINS basin boundary, not a surveyed watershed divide,
so edge flow accumulation underestimates true upslope area. Recorded in the hydrology processing
note.

## C-Factor (WorldCover lookup)

- Script: `bin/factors/derive_v1_worldcover_cfactor.py`. Native 10m + V1 30m outputs, grid-compatible.
- Lookup applied AFTER mode (majority-class) resampling from 10m to 30m; C-values are discrete
  lookup values, not cross-class averages.
- V1 class fractions match the methodology sweep: shrubland 55%, tree 23%, grassland 15%,
  cropland 6%.
- Area-weighted mean C: 0.0429 (30m), within the expected 0.03-0.06 band.
- 10m->30m aggregation is legitimate (fine->coarse, preserves categorical class); this is the
  opposite of the CHIRPS/SoilGrids coarse->fine prohibition.

## venv Dependencies Used

- `whitebox` (new): hydrology toolchain. Local tooling only; not a public pipeline dependency.
- `playwright` (earlier): CDP portal check only, not used in factor derivation.
- Existing: rasterio, geopandas, pyproj, numpy, scipy.

## Next Step

LS-factor is now unblocked: it needs flow accumulation (done) + slope (done) via the standard
RUSLE LS equation (e.g. Moore & Nieber 1989 / Desmet & Govers 1996). This would complete 4 of 5
USLE factors, leaving only the P=1 documented assumption.
