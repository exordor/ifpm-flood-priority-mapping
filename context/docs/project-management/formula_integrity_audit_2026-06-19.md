# Formula and Citation Integrity Audit (2026-06-19)

Status: internal record of the post-implementation literature-integrity audit of every USLE/RUSLE
formula, coefficient, unit, and citation used in the V1 and V2 USLE tooling. Triggered after the
V2 R-factor implementation, when a spot-check on the candidate R-formulas surfaced an unverified
coefficient. This audit is a defensive sweep, not a validation of model outputs.

It does NOT authorise any download, AHP overlay, flood-risk interpretation, sediment-risk
interpretation, or intervention-priority claim.

**Revision 2026-06-19 (same day, deeper pass):** after extracting the exact equations from the
Renard & Freimund (1994) original PDF, the P/MFI finding was reclassified from "variable
confusion" to a more serious compound error (P-based coefficients applied to MFI AND an invented
break point), and the Arnoldus finding was corrected (the coefficients ARE Arnoldus 1977's
original values, but use metric units inconsistent with the USLE R-factor unit). The severity of
these two findings was upgraded; see Findings 2 and 3 below. The V2 mentor communication is
PAUSED pending mentor guidance on the correct R-factor method for the study area (see Impact and
Open Items).

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
| R: Renard-Freimund on MFI | P-based coeffs `0.0483*MFI^1.61` / `587.8-1.219*MFI+0.004105*MFI^2` applied to MFI with INVENTED break at MFI=80 | COMPOUND ERROR: wrong coefficients for MFI variable AND fabricated break point. The V1 bimodality is an artifact of the wrong break (should be F=55mm for the MFI form). | flagged; V1/V2 R absolute values NOT trustworthy; needs mentor decision on the correct R method before any re-run |
| R: Arnoldus coeffs | `0.2647 * MFI^1.5` | COEFFICIENTS ARE ORIGINAL (Arnoldus 1977 Eq 8: `R=0.264*F^1.50`) BUT UNIT MISMATCH (Arnoldus used metric t-m-cm-ha-h units, not USLE MJ-mm-ha-h) | kept as a smoothing test function only; absolute values unit-inconsistent |
| K: US->SI conversion | `K_US * 0.1317` | CORRECT | no change |
| LS: normalising constants | `22.13`, `0.0896` | CORRECT | no change |
| LS: exponents | `0.4`, `1.2` | CORRECT (lower bound of documented range) | no change |

Three real findings (rf_lo removal; the Renard-Freimund compound error; the Arnoldus unit
mismatch). The Renard-Freimund error is the most serious because it manufactured the V1
bimodality that motivated the V2 exercise. K, LS constants, and LS exponents are verified correct.

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

### Finding 2 - COMPOUND ERROR: Renard-Freimund P-based coefficients applied to MFI with an invented break point (inherited from V1)

- Location: `bin/derive_v1_chirps_rfactor.py` (V1) and `bin/derive_v2_rfactor_candidates.py` (V2),
  candidates `rf_v1_bimodal` and `rf_rf_low_branch`. The function is named `renard_freimund_r(mfi)`.
- Problem (verified against the original PDF, `outputs/literature_verification/renard_freimund_1994_fulltext.txt`).
  Renard & Freimund (1994) published TWO independent equation composites:
  - P-based form (Eq 11/12), variable = mean annual precipitation P (mm), break at **P = 850 mm**:
    `R = 0.04830*P^1.610` (P<850) and `R = 587.8 - 1.219*P + 0.004105*P^2` (P>=850).
  - F-based form (Eq 13/14), variable = modified Fournier index F = sum(pi^2)/P (mm) = the
    project's MFI, break at **F = 55 mm**:
    `R = 0.07397*F^1.847` (F<55) and `R = 95.77 - 6.081*F + 0.4770*F^2` (F>=55).
  The project applies the **P-based coefficients** (0.0483/1.61/587.8/1.219/0.004105) to MFI AND
  sets the break at **MFI=80**. MFI=80 is NEITHER the P-form break (850) NOR the F-form break (55);
  it is invented.
- Severity: HIGH. This is a compound error with two consequences:
  1. The break at MFI=80 is fabricated, and V1's MFI range (70-117) straddles it. Under the
     CORRECT F-form (break at 55) EVERY V1 cell falls in the upper branch (F>=55), so there is NO
     discontinuity and NO bimodality. **The V1 bimodality (29 low / 103 high cells) is an artifact
     of the wrong break point, not a real erosivity structure.**
  2. The absolute R values are wrong on both scale and structure. At MFI=92.9 the project reports
     R~510 (upper branch of the wrong form); the correct F-form gives R~3650 at the same MFI.
- Impact on V2: the V2 smoother-R exercise was framed as "resolve the V1 bimodality and test
  hotspot survival". Because the bimodality was an artifact, the "resolve the bimodality" half of
  that premise does not hold up (there is nothing real to resolve once the correct break is used).
  The hotspot-survival half remains valid, because it tests the LS x C structure, which is
  R-invariant and independent of the R formula. The V2 comparison outputs and board therefore
  remain useful as a STRUCTURE test but must NOT be presented as "V2 fixed a real V1 problem".
- Resolution: FLAGGED. Not silently re-derived, because the correct re-derivation needs a mentor
  decision on which method suits semi-arid Zimbabwe (the F-form gives very high R for this MFI
  range, which may itself indicate the Renard-Freimund US-calibrated relations are not transferable
  here). **V1/V2 R-factor absolute values are NOT trustworthy until this is resolved.** This is the
  highest-priority open item for the mentor.
- Re-run needed: YES, for the R-factor and USLE A-factor, once the correct method is chosen. No
  re-run needed for LS/C/K or the non-R parts of the pipeline.

### Finding 3 - UNIT MISMATCH: Arnoldus (1977) coefficients are original but use metric units

- Location: `bin/derive_v2_rfactor_candidates.py`, candidate `rf_arnoldus`.
- Problem (verified against the original PDF). The earlier "non-universal / regionally-fitted"
  assessment was INCORRECT and is corrected here. Renard & Freimund (1994, Eq 8, citing Arnoldus
  1977) state the Arnoldus relation as `R = 0.264*F^1.50`. So the coefficients ARE Arnoldus's
  original published values (the project's 0.2647 vs the paper's 0.264 is a rounding difference
  from secondary citations). HOWEVER the paper explicitly notes Arnoldus's R units are metric
  (t-m cm ha-1 h-1 year-1), NOT the USLE-standard MJ mm ha-1 h-1 year-1, and that "units ... were
  identified as metric units but not specified" by Arnoldus.
- Severity: medium. The coefficient values are correctly attributed, but mixing Arnoldus's metric
  R units with the USLE-standard R units used by the rest of the pipeline is a unit inconsistency.
  As a smoothing test function this is tolerable; as an absolute R value it is not.
- Resolution: kept as a candidate smoothing function. The earlier "non-universal" label in the
  processing note and task board is superseded: the coefficients are Arnoldus 1977 original values,
  and the caveat is a UNIT MISMATCH, not non-universality.

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

## Impact summary (what is and is not affected)

- V1 R-factor (RF and bimodal) and V2 rf_v1_bimodal / rf_rf_low_branch candidates: absolute values
  NOT trustworthy (Finding 2). Re-run needed once the correct method is chosen.
- V2 rf_arnoldus candidate: coefficient values correct, but R units inconsistent (Finding 3). Keep
  as a structural test only.
- V2 "resolve the bimodality" framing: does NOT hold (the bimodality was an artifact of the wrong
  break point). Do not present V2 to the mentor as fixing a real V1 problem.
- V2 hotspot-survival test: STILL VALID as a structure test, because it uses the R-invariant
  a_structure = K x LS x C reference and is independent of the R formula. The survival rates and
  Spearman agreement reported are about the LS x C structure, not about R.
- LS, C, K factors, hydrology derivatives, terrain preprocessing, CHIRPS rainfall comparison, and
  all non-R pipeline parts: unaffected.
- AHP, flood-risk, intervention-priority: remain blocked (no change).

## What this audit does NOT cover

- It does not validate the MFI computation itself (the 5-month Nov-Mar sum vs full 12 months);
  that is a documented data-availability limitation, not a formula-integrity issue.
- It does not validate Saaty random-index values (standard reference values, unchanged).
- It does not re-verify the AHP eigenvector math (covered by the pipeline's regression tests).
- It does not authorise any interpretable soil-loss or risk claim; all V1/V2 USLE outputs remain
  DIAGNOSTIC.

## Open items handed to the mentor (HIGHEST PRIORITY first)

1. R-factor method for semi-arid Zimbabwe (Finding 2): the V1 R used P-based Renard-Freimund
   coefficients on MFI with an invented break at MFI=80, which manufactured the bimodality. The
   correct F-form (break at 55) gives no bimodality over V1's MFI range but yields very high R
   values, suggesting the US-calibrated Renard-Freimund relations may not transfer here. Which R
   method is appropriate (correct F-form; P-form on annual precipitation; a region-calibrated
   method; or another)? This blocks all R/A absolute values.
2. Once the R method is chosen: re-derive the V1 R-factor and USLE A, then re-evaluate the V2
   smoother-R exercise (which may be moot if the correct method is already smooth).
3. Arnoldus unit consistency (Finding 3): if Arnoldus is retained as a candidate, confirm whether a
   unit conversion to USLE-standard MJ mm ha-1 h-1 is required.

## Mentor communication status

PAUSED. The V2 R-factor comparison board and the "V2 resolves the bimodality" framing must NOT be
sent to the mentor until Finding 2 is resolved, because the bimodality was an artifact. The V2
hotspot-structure results may be shared later as a structural finding only, clearly separated from
any R-absolute-value claim.

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
