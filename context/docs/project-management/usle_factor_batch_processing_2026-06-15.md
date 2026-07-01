# V1 USLE Factor Batch Processing Note (R, Hydrology, C)

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
