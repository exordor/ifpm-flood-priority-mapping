# Formula and Citation Integrity Audit (2026-06-19)

Status: internal record of the post-implementation literature-integrity audit of every USLE/RUSLE
formula, coefficient, unit, and citation used in the V1 and V2 USLE tooling. Triggered after the
V2 R-factor implementation, when a spot-check on the candidate R-formulas surfaced an unverified
coefficient. This audit is a defensive sweep, not a validation of model outputs.

It does NOT authorise any download, AHP overlay, flood-risk interpretation, sediment-risk
interpretation, or intervention-priority claim.

## Why this audit exists

The V2 smoother-R package introduced candidate MFI->R formulas. A check on one candidate ("Lo et
al. 1985") found that its coefficients had no traceable source. Because USLE factors multiply
together, a single fabricated coefficient corrupts every downstream A-factor value. This document
audits every formula in the USLE chain so the mentor (and any reviewer) can see which numbers are
literature-backed and which carry open methodological risk.

## Summary verdict

| Item | Formula / value | Verdict | Action taken |
|---|---|---|---|
| R: rf_lo candidate | `0.0737 * MFI^1.81` ("Lo et al. 1985") | FABRICATED (no traceable source) | removed from V2 candidates |
| R: Renard-Freimund coeffs on MFI | `0.0483*MFI^1.61` / `587.8-1.219*MFI+0.004105*MFI^2` | VARIABLE CONFUSION (P-based coeffs applied to MFI; inherited from V1) | flagged, NOT silently fixed (preserved for V1-V2 comparability) |
| R: Arnoldus coeffs | `0.2647 * MFI^1.5` | NON-UNIVERSAL (regionally-fitted; Arnoldus gave only R=a*Fm^b framework) | kept, labelled as non-authoritative candidate |
| K: US->SI conversion | `K_US * 0.1317` | CORRECT | no change |
| LS: normalising constants | `22.13`, `0.0896` | CORRECT | no change |
| LS: exponents | `0.4`, `1.2` | CORRECT (lower bound of documented range) | no change |

Two real findings (rf_lo removal; P/MFI ambiguity); the rest verified against primary sources.

## Detailed findings

### Finding 1 - FABRICATED: rf_lo candidate R = 0.0737 * MFI^1.81

- Location (before removal): `bin/derive_v2_rfactor_candidates.py`, candidate `rf_lo`, attributed
  to "Lo et al. (1985)".
- Problem: a literature check showed "Lo et al. 1985" refers to Lo, El-Swaify, Dangler & Shinsiro
  (1985, Hawaii) or Lo, K.S. et al. (1985, Korea), BOTH of which use mean annual precipitation (P)
  as the R predictor, NOT the Modified Fournier Index (MFI). The coefficient pair 0.0737 / 1.81
  has no traceable source in either study; it was introduced without a verified citation.
- Severity: high. A fabricated coefficient in the R-factor propagates into every USLE A-factor
  derived from it.
- Resolution: the `rf_lo` candidate was REMOVED from `R_CANDIDATES` in
  `bin/derive_v2_rfactor_candidates.py`, from the `CANDIDATES` lists in
  `bin/derive_v2_usle_soil_loss.py` and `bin/compare_v2_rfactor_candidates.py`, and from the plot
  board in `bin/plot_v2_rfactor_comparison_board.py`. A comment in each script records the removal
  and the reason. The V2 candidate set is now 3 (V1-bimodal, Arnoldus, RF-low-branch).
- Why not "fixed": there is no verified Lo-et-al MFI coefficient to substitute. Any reintroduction
  must come with a verified citation and the correct predictor variable.

### Finding 2 - VARIABLE CONFUSION: Renard-Freimund coefficients applied to MFI (inherited from V1)

- Location: `bin/derive_v1_chirps_rfactor.py` (V1) and `bin/derive_v2_rfactor_candidates.py` (V2),
  candidate `rf_v1_bimodal` and `rf_rf_low_branch`. The function is named `renard_freimund_r(mfi)`.
- Problem: Renard & Freimund (1994) published TWO related forms:
  - a P-based form: `R = 0.0483*P^1.61` if P < 850 mm else `587.8 - 1.219*P + 0.004105*P^2`,
    where P = mean annual precipitation;
  - an F-based form (F = Modified Fournier Index), with DIFFERENT coefficients.
  The coefficient values 0.0483 / 1.61 / 587.8 / 1.219 / 0.004105 used here are the P-based
  coefficients, but they are applied to MFI. The MFI=80 break used in the code is also the P=850mm
  threshold rescaled by convention.
- Severity: medium-high. This affects the ABSOLUTE value of every V1 and V2 R-factor and therefore
  every A-factor magnitude. It does NOT affect the V1-vs-V2 comparison (both use the same
  convention) or the bimodality / hotspot-structure conclusions (those are about the discontinuity,
  not the absolute scale).
- Resolution: FLAGGED, not silently fixed. Changing the convention now would break V1-vs-V2
  comparability and would require re-deriving the entire V1 R-factor. This is recorded as an open
  methodological risk for the mentor to resolve before any USLE result supports a claim. The V2
  script docstring and the V2 processing note both document the convention and the risk.

### Finding 3 - NON-UNIVERSAL: Arnoldus (1980) coefficients 0.2647 / 1.5

- Location: `bin/derive_v2_rfactor_candidates.py`, candidate `rf_arnoldus`.
- Problem: Arnoldus (1980) presented only the FRAMEWORK `R = a * Fm^b`; the a/b values are
  regionally-fitted regression coefficients, NOT universal constants Arnoldus published. The
  0.2647 / 1.5 pair appears in some applied papers but is region-specific. A 2023 Catena systematic
  review documents widespread mis-citation/misuse of this equation family.
- Severity: low-medium. The candidate is used as a smoothing function to test hotspot survival, not
  as an authoritative R value. The absolute Arnoldus A values are already flagged as
  non-interpretable.
- Resolution: kept as a candidate, but its display name and the processing note now label the
  coefficients as "regionally-fitted / non-universal" so the mentor does not read them as Arnoldus's
  original values.

### Finding 4 - VERIFIED CORRECT: K-factor US->SI conversion 0.1317

- Location: `bin/derive_v1_soilgrids_kfactor.py`, `bin/derive_v1_usle_soil_loss.py`,
  `bin/derive_v2_usle_soil_loss.py` (`k_si_mean = k_us_mean * 0.1317`).
- Source: Foster, McCool, Renard & Moldenhauer (1981), "Conversion of the Universal Soil Loss
  Equation to SI Metric Units", J. Soil & Water Conservation 36, 355-359.
- Verification: the 0.1317 factor is widely and consistently cited across USLE/RUSLE literature
  (e.g. Colorado State reproduction of the original; RUSLE handbook; applied papers). Typical SI K
  range 0.013-0.059 matches the V1 K_SI mean of 0.02232 (= 0.1695 US * 0.1317).
- Verdict: correct, no change.

### Finding 5 - VERIFIED CORRECT: LS normalising constants 22.13 / 0.0896

- Location: `bin/derive_v1_ls_factor.py` (`(As/22.13)^0.4 * (sin(theta)/0.0896)^1.2`).
- Source: Moore & Nieber (1989) raster LS based on specific contributing area.
- Verification: 22.13 m is the standard USLE plot length constant and 0.0896 = sin(5.14 deg) the
  standard 9% plot slope; both are consistent across the Moore-Nieber / Moore-Wilson literature
  and across GIS implementations (SAGA, GRASS).
- Verdict: correct, no change.

### Finding 6 - VERIFIED CORRECT: LS exponents 0.4 / 1.2

- Location: `bin/derive_v1_ls_factor.py`.
- Source: Moore & Nieber (1989) / Moore & Wilson (1992) UCA LS framework.
- Verification: per USDA-ARS GISus-M (Oliveira et al. 2015, eq 13), the UCA LS form
  `LS = (As/22.13)^m * (sin(theta)/0.0896)^n` uses m in [0.4-0.56] and n in [1.2-1.3]. The
  project's 0.4 / 1.2 are the lower-bound starting combination of that documented range - a
  standard, valid choice. SAGA GIS labels this as the "Moore & Nieber 1989" method.
- Capture record: `outputs/literature_verification/usda_ars_gisus_m.txt`.
- Note: m and n are a tunable range; 0.4/1.2 is the conservative lower bound. This is acceptable
  but worth stating if the LS magnitude is ever challenged.
- Verdict: correct, no change.

## What this audit does NOT cover

- It does not validate the MFI computation itself (the 5-month Nov-Mar sum vs full 12 months);
  that is a documented data-availability limitation, not a formula-integrity issue.
- It does not validate Saaty random-index values (standard reference values, unchanged).
- It does not re-verify the AHP eigenvector math (covered by the pipeline's regression tests).
- It does not authorise any interpretable soil-loss or risk claim; all V1/V2 USLE outputs remain
  DIAGNOSTIC.

## Open items handed to the mentor

1. P-vs-MFI variable confusion in the Renard-Freimund R-factor (Finding 2): which convention is
   correct for the study area, and does V1 need re-derivation before any USLE claim?
2. Confirm the V2 R formula choice (Arnoldus, with its non-universal coefficients; or RF-low-branch;
   or another) and whether the P/MFI convention must be resolved first.

## Cross-references

- V2 R-factor processing note (includes the literature-integrity correction section):
  `context/docs/project-management/v2_rfactor_processing_2026-06-16.md`.
- V1 LS and USLE processing note: `context/docs/project-management/ls_factor_and_usle_soil_loss_processing_2026-06-15.md`.
- V2 R-factor scripts: `bin/derive_v2_rfactor_candidates.py`, `bin/derive_v2_usle_soil_loss.py`,
  `bin/plot_v2_rfactor_comparison_board.py`, `bin/compare_v2_rfactor_candidates.py`.
- Verification tooling and capture: `bin/verify_ls_factor_exponents.py`,
  `outputs/literature_verification/`.
- Task board: IFPM-079 (V2 R-factor) records the literature-integrity review block.

## Sources

- Arnoldus, H.M.J. (1980). An approximation of the rainfall factor in the Universal Soil Loss
  Equation. In De Boodt & Gabriels (Eds.), Assessment of Erosion, pp. 127-132. Wiley.
- Foster, McCool, Renard & Moldenhauer (1981). Conversion of the USLE to SI Metric Units. JSWC 36.
- Moore, I.D. & Nieber, J.L. (1989). Landscape assessment of soil erosion and nonpoint source
  pollution. J. Minnesota Acad. Sci. 55, 18-25.
- Moore, I.D. & Wilson, J.P. (1992). Length-slope factors for the RUSLE.
- Oliveira et al. (2015). GISus-M: a GIS-based procedure for automatically calculating soil loss
  from the USLE. USDA-ARS.
- Renard, K.G. & Freimund, J.R. (1994). Using monthly precipitation data to estimate the R-factor.
  J. Hydrology 157.
- (2023) A systematic review of the incorrect use of an empirical equation for rainfall erosivity.
  Catena / Earth-Science Reviews.
