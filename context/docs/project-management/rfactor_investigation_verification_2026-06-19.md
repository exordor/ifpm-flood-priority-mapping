# Independent verification of the R-factor investigation results (2026-06-19)

A first-principles re-check of every formula, coefficient, and headline number in the R-factor
investigation (IFPM-079..084), done by hand-calculating each method from the original sources and
comparing to the script output. This exists so the briefing to the mentor is backed by verified
numbers, not by "the script ran".

## Method

For each item: re-extract the exact equation from the primary source (RF1994 PDF for the
Renard-Freimund and Elwell equations; USDA-ARS GISus-M for LS; Foster 1981 for K), hand-calculate
at the V1 inputs (P_annual = 583.5 mm, MFI = 92.92), and compare to the diagnostics JSON / raster
values. Where the hand-calc and script differ, determine whether it is a real error or an expected
property of non-linear functions (function-of-mean != mean-of-function).

## Results

### 1. Renard-Freimund (1994) equations — CORRECT
Re-extracted from the original PDF:
- Eq 11: `R = 0.04830*P^1.610` (P < 850 mm)
- Eq 12: `R = 587.8 - 1.219*P + 0.004105*P^2` (P >= 850 mm)
- Eq 13: `R = 0.07397*F^1.847` (F < 55 mm)
- Eq 14: `R = 95.77 - 6.081*F + 0.4770*F^2` (F >= 55 mm)
- Break points 850 mm (P-form, line 775) and 55 mm (F-form, line 1228) both confirmed in the
  original text. The "invented break at MFI=80" in V1 is indeed neither. VERIFIED.

### 2. Six R methods — hand-calc vs script
Hand-calc at V1 scalars vs script zonal-mean, with % difference:

| method | hand-calc | script | diff | verdict |
|---|---:|---:|---:|---|
| A corrected Arnoldus | 2314 | 2329 | 0.7% | OK (non-linear mean effect) |
| B RF F-form (Eq 14) | 3649 | 3719 | 1.9% | OK |
| C RF P-form (Eq 11) | 1372 | 1380 | 0.6% | OK |
| D OLD V1 (wrong) | 510 | 408 | 25% | OK — see below |
| E Hurni | 320 | 320 | 0.1% | OK |
| F Epworth/Merritt | 243 | 243 | 0.1% | OK |

Method D's 25% "difference" is NOT an error. The hand-calc used a single MFI=92.92 (all in the high
branch). The actual 132 cells split 29 low-branch (MFI~70, R~45) + 103 high-branch (MFI~100, R~507),
giving a weighted mean of 405.5, matching the script's 408. Verified by reading the rf_v1_bimodal
raster directly (mean=408.0, 29 cells<100, 103 cells>400).

### 3. ERA5 EI30 algorithm — CORRECT
- Wischmeier-Smith unit energy `e = 0.119 + 0.0873*log10(i)` (cap 76) and Brown-Foster
  `e = 0.29*(1-0.72*exp(-0.05*i))` both implemented correctly.
- Unit-energy magnitudes at i=1..50 mm/h range 0.09-0.27 MJ/ha/mm, within the literature-typical
  0.1-0.3. CORRECT.
- Storm segmentation (6h gap, >=12mm erosive threshold) verified on a real 37h storm.
- Annual R at one test point reproduced: 6-yr mean R = 508 (I30 est) / 462 (I60 lb), matching the
  script. The year-to-year spread (240-1150) and Pareto effect (top-5 storms = 49% of R) are
  physically plausible for semi-arid convective rainfall.

### 4. Elwell/Stocking table — CORRECT
RF1994 reproduces the Stocking & Elwell (1976a) R-values: 400-500mm=1630, 500-600mm=2000,
600-700mm=2400, 700-800mm=2800. Slope ~400/100mm. V1 P=583.5 falls in 500-600 -> R~2000. VERIFIED.

### 5. Epworth equation — CORRECT
R = 38.5 + 0.35*M. R=329 back-solves to M=830mm, within the Harare range (Airport 804, Belvedere
880). VERIFIED. (The circularity caveat - 329 was computed with this equation, not measured -
stands, and is recorded separately.)

### 6. LS exponents 0.4/1.2 and K conversion 0.1317 — CORRECT
LS lower bound of the GISus-M m[0.4-0.56]/n[1.2-1.3] range (verified earlier against USDA-ARS).
K: 0.1695 US * 0.1317 = 0.02232, matches the K diagnostics. VERIFIED.

### 7. Hydrology standardization (TWI, distance) — CORRECT
TWI raw p2/p98 = 5.234/14.208, matching the standardization clip range [5.23, 14.21]. Standardized
output in [0,1], 0 out-of-range values, monotonicity correct (TWI +0.985, distance -0.996), grid
gate passes on all 7 fields, valid-fraction (43.6%) matches the terrain candidates (43.7%) and
a_structure (42.5%). VERIFIED.

## Issue found — Arnoldus coefficient sourcing for Method A (FLAGGED, not yet corrected)

Method A uses the Nakil & Khire (2023) form `R = 17.02*10^(1.50*log10(MFI) - 0.8188)`. This
implies a prefactor `17.02*10^(-0.8188) = 2.583`, i.e. `2.583*MFI^1.5`. But the Arnoldus (1977)
original coefficient (RF1994 Eq 8) is `0.264*F^1.50`, which after the 17.02 unit conversion would
be `0.264*17.02 = 4.493`, i.e. `4.493*F^1.5`.

These disagree by a factor of 1.74 (2.583 vs 4.493). So the Nakil & Khire "corrected Arnoldus" is
NOT simply "Arnoldus coefficients x 17.02 unit conversion" - its intercept (-0.8188) implies a
different base coefficient (0.1519) than Arnoldus's 0.264. Either Nakil & Khire re-fitted the
coefficients (so it is not "the Arnoldus equation with a conversion"), or my reading of the 2023
review's form is incomplete.

Impact: Method A's value (2329) is still a valid data point for the family comparison (it lands in
the HIGH family with the others), but describing it in the briefing as "Arnoldus WITH the 17.02
conversion" overstates the lineage. The briefing text should be softened to "a 17.02-corrected
MFI power law attributed to the Arnoldus family (Nakil & Khire 2023), noting the base coefficient
differs from Arnoldus 1977's 0.264". The safer conclusion is that high-family values are much
larger than the ERA5 hourly lower-bound check; this does not by itself settle the final R method.

## Items NOT independently re-verified here (already covered)
- rf_lo removal: the coefficient had no traceable source; removal stands. Not re-derived.
- Epworth circularity: confirmed (329 back-solves to the F equation). Not a numerical error.
- V1 R-factor error: confirmed (wrong coefficients on MFI, invented break). Deprecated products stay
  deprecated.

## Overall verdict

The investigation's headline numbers are verified by independent hand-calculation:
- the six R-method values match (within expected non-linear-mean effects);
- the ERA5 empirical R (~460-508) is computed correctly from a verified EI30 algorithm;
- the family split (HIGH ~1380-3719 vs LOW ~240-320, empirical ~460-508 near the lower range)
  holds as method-decision evidence.
- LS, K, hydrology standardization all verified.

One sourcing inaccuracy is flagged: Method A's "corrected Arnoldus" coefficient (0.1519 base) is
not the Arnoldus 1977 coefficient (0.264); the briefing must not claim it is. This affects the
description of Method A, not the conclusion.
