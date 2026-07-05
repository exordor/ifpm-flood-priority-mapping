# R-factor investigation — consolidated record

Date span: 2026-06-16 to 2026-06-19. Status: investigation complete; **R-method decision
BLOCKED on mentor input**. All V1/V2 R-factor and USLE A-factor absolute values remain
deprecated (see `outputs/v1_usle_soil_loss/DEPRECATED_DUE_TO_R_FACTOR_ERROR.md`).

This single note replaces and consolidates six earlier process notes (listed under Lineage
below). It keeps every verified conclusion, formula, headline number, source, and claim
boundary; the process narration is compressed.

## 1. The V1 R-factor error (the trigger)

V1 applied the **P-based** Renard & Freimund (1994) coefficients
(`0.0483*X^1.61` and `587.8 - 1.219*X + 0.004105*X^2`) to the Modified Fournier Index (MFI),
with an **invented break at MFI=80**. Verified against the original PDF (S1):

- the P-based form (Eq 11/12) takes mean annual precipitation P (mm) and breaks at **P = 850 mm**;
- the F-based form (Eq 13/14) takes F = MFI (mm) and breaks at **F = 55 mm**, with DIFFERENT
  coefficients (`0.07397*F^1.847` / `95.77 - 6.081*F + 0.4770*F^2`).

V1's MFI range is 70-117, which under the CORRECT F-based form lies entirely in the upper
branch (F >= 55). There is therefore **no discontinuity and no bimodality** under the correct
formula. The V1 bimodality (29 low / 103 high cells) is an **artifact of the wrong break point**.

Consequences: all V1 and V2 R-factor absolute values are wrong (wrong coefficients AND wrong
break); all USLE A-factor values derived from them are wrong; the "V2 resolves the V1
bimodality" framing does NOT hold (there was nothing real to resolve).

A separate Arnoldus finding: `0.264*F^1.50` ARE Arnoldus 1977's original coefficients (S1, Eq 8),
but Arnoldus's R units are metric (t-m cm ha-1 h-1 year-1), not USLE-standard
(MJ mm ha-1 h-1 year-1). This is a **unit mismatch**, not non-universality (corrects an earlier
label). Kept as a smoothing test function only.

A "Lo et al. 1985" candidate (`0.0737*MFI^1.81`) was REMOVED — its coefficients had no
traceable source and Lo et al. used P, not MFI, as the predictor.

## 2. Verified CORRECT (no change, no open item)

| item | value / formula | source |
|---|---|---|
| K-factor US->SI conversion | `K_SI = K_US * 0.1317` | Foster et al. 1981 (S4) |
| LS normalising constants | `22.13`, `0.0896` | Moore & Nieber 1989 |
| LS exponents | `0.4`, `1.2` (lower bound of GISus-M range m∈[0.4-0.56], n∈[1.2-1.3]) | Oliveira et al. 2015 / USDA-ARS (S9) |
| Hydrology standardization (TWI, distance) | clip ranges, monotonicity, valid-fraction | local diagnostics |

`a_structure_K_LS_C_30m.tif` (K x LS x C, no R-factor) is the verified-correct R-invariant
base for any future `A = structure x R` re-derivation. It is **safe to keep** (see deprecation
marker).

## 3. The method comparison — two incompatible R-families

Six literature methods run on identical V1 inputs (P_annual mean 583.5 mm; MFI mean 92.92),
hand-verified against script output (all within expected non-linear-mean effects):

| method | formula | R zonal mean | family |
|---|---|---:|---|
| A: Arnoldus-family / Nakil-Khire | `17.02*10^(1.50*log10(MFI)-0.8188)` | 2329 | HIGH |
| B: RF F-based correct (Eq 14) | `95.77-6.081*F+0.4770*F^2` | 3719 | HIGH |
| C: RF P-based correct (Eq 11) | `0.04830*P^1.61` | 1380 | HIGH |
| (Elwell/Stocking 1976 ref) | Zimbabwe-native R-vs-P table | ~2000 | HIGH |
| empirical ERA5 (I30 est) | hourly EI30 algorithm | ~506 | (lower range) |
| E: Hurni 1985 | `R = -8.12 + 0.562*P` | 320 | LOW |
| F: Epworth/Merritt | `R = 38.5 + 0.35*M` | 243 | LOW |
| D: OLD V1 (WRONG) | P-coeffs on MFI, break@80 | 408 | (invalid) |

**Key finding: the methods split into two mutually incompatible families ~6x apart.**

- **HIGH family (~1380-3719):** US-calibrated Renard-Freimund forms (A/B/C) AND the
  Zimbabwe-native Elwell/Stocking (1976) relation (~2000 at P~583) AGREE. This is significant:
  Elwell/Stocking used Rhodesian rainfall data independent of the US calibration, yet lands in
  the same range. The "US formulas don't transfer" hypothesis is NOT supported once the
  Zimbabwe-native relation is included.
- **LOW family (~240-320):** Hurni (1985, Ethiopia) and the Epworth/Merritt equation.

**Circularity caveat:** the often-cited "measured Epworth 329" is NOT independent evidence.
It was computed using `R = 38.5 + 0.35*M` (the LOW-family equation), so citing it to validate
the low-R family is circular. There is NO independent measured EI30 R for the V1 catchment in
any source found.

Method A sourcing caveat: its coefficient (0.1519 base) is NOT a clean Arnoldus-1977
conversion (Arnoldus's 0.264). Describe it as "a 17.02-corrected MFI power law attributed to
the Arnoldus family (Nakil & Khire 2023)", not "Arnoldus with unit conversion".

## 4. Empirical ERA5 lower-bound check

An INDEPENDENT empirical R computed directly from ERA5 hourly precipitation (7+45 V1 points,
2018-2023, via open-meteo, no auth) using a verified EI30 algorithm (Wischmeier-Smith and
Brown-Foster kinetic-energy forms; storm segmentation 6h gap / >=12mm threshold):

- Spatial-mean empirical R: **358-506** (depending on KE form and I60-lower-bound vs I30-estimate)
- 45-point rasterized R zonal mean (WS I30 est) = **507**, matching the 7-point 506 (spatially stable)
- Per-point range 256-532; spatial pattern plausible (higher in wetter north/centre)

| | R value | relation to empirical (~358-506) |
|---|---:|---|
| LOW family (Hurni/Epworth) | 240-320 | empirical ~1.1-1.6x (close, slightly above) |
| **Empirical ERA5** | **358-506** | (this experiment) |
| HIGH family (RF/Arnoldus/Elwell) | 1380-3719 | empirical ~3-7x BELOW |

This is the first non-circular check. It makes the lower range plausible and raises a serious
transferability question for the high-family formulas — but because ERA5 is hourly rather than
true 30-min breakpoint rainfall, this is a **lower bound** supporting the method decision, not a
final R validation.

Algorithm verification (hand-checked): unit-energy magnitudes 0.09-0.27 MJ/ha/mm (literature
0.1-0.3); annual R at one test point reproduced (6-yr mean 508 I30 / 462 I60); year-to-year
spread 240-1150 and Pareto (top-5 storms = 49% of R) physically plausible.

USLE A using empirical R: A_zonal (R=507 scalar) mean = **0.621 t/ha/yr**; A_spatial
(DIAGNOSTIC, R resampled to 30m) mean = **0.619**. Agreement <1% confirms the soil-loss hotspot
pattern is governed by LS x C (R-invariant a_structure), not by R spatial variation. These A
outputs are **sensitivity diagnostics only**, not accepted soil-loss evidence.

## 5. V2 hotspot-survival test (valid only as a structure test)

The V2 smoother-R exercise tested whether the LS x C hotspot pattern survives different R
candidates. Headline: hotspot survival is 84-87% under all candidates including the V1 bimodal
baseline, and Spearman agreement reaches 0.99 under smoother R vs 0.88 under bimodal R.

**Two strict caveats** (from adversarial review):
1. The survival metric is structurally biased toward high values (LS spans ~4 orders of
   magnitude vs R's ~3x), so it has **low discriminating power** — a broken V1 baseline also
   scores 0.84. Read it as a weak confirmatory signal ("terrain/land-cover governs hotspots"),
   not a candidate-quality ranking.
2. The "V2 resolves bimodality" framing is invalid (the bimodality was an artifact). The V2
   results are correctly computed but the premise was wrong.

The hotspot-survival NUMBERS were computed from the (now-removed) V2 outputs and are recorded
in this section; they remain valid as a STRUCTURE test only and must not be read as a statement
about R. The V2 A-factor rasters that encoded the wrong R were deleted 2026-07-01.

## 6. What is deprecated vs safe to keep

DEPRECATED (do not use): all V1/V2 R-factor rasters, all USLE A rasters derived from them, the
V2 comparison board and caption. Full list in
`outputs/v1_usle_soil_loss/DEPRECATED_DUE_TO_R_FACTOR_ERROR.md`.

SAFE TO KEEP: `a_structure_K_LS_C_30m.tif`; all LS, C, K, hydrology, terrain preprocessing, and
CHIRPS rainfall-comparison products (none depend on the R formula); the empirical ERA5 R
diagnostics and the hotspot-survival structure test (with their caveats).

## 7. The open question for the mentor (HIGHEST PRIORITY)

Which R-factor method is appropriate for semi-arid Zimbabwe? The evidence package presents:

- two incompatible literature families ~6x apart;
- the Zimbabwe-native Elwell relation supports the HIGH family;
- the LOW family's only "validation" (Epworth 329) is circular;
- the only independent check (ERA5 hourly) sits in the lower range, questioning the high
  family's transferability — but is itself a lower bound.

To settle R the project needs ONE of: a primary EI30 dataset (sub-daily gauge or GPM IMERG) in
or near V1; a mentor ruling on which R convention the thesis adopts (with the family choice
documented); or a traceable original source for the low-R family to resolve its units.

Until R is settled, USLE A absolute values are blocked. New R-factor products may be generated
as `provisional` or `sensitivity_scenario` outputs if method, source, value range, uncertainty,
and lineage are documented (execution-status policy, 2026-06-29 update).

## 8. Send decision

Sendable (after caption wording): Figure 1 (method-comparison) and Figure 2 (ERA5 lower-bound).
Blocked: Figure 3 (V1/V2 comparison board, repeats invalid "V2 resolves bimodality" framing);
any soil-loss A magnitude as a final result; any flood-risk/sediment-risk/intervention claim.

Send source: `context/docs/mentor-explanation/Mentor_RFactor_Figure_Send_Packet_2026-06-19.md`.

Required wording corrections: "Corrected Arnoldus" -> "Arnoldus-family / Nakil-Khire MFI law";
"high formulas ~4x too high" -> "high-family formulas much larger than ERA5 lower-bound";
"ERA5 proves the low family" -> "ERA5 supports the lower range as independent lower-bound check".

## Source register

| id | source | supports |
|---|---|---|
| S1 | Renard & Freimund 1994 (USDA/ARS PDF) | USLE form, RF P/F equations, Brown-Foster KE, Arnoldus Eq 8 |
| S2 | Wischmeier & Smith 1978, USDA AH-537 | Wischmeier-Smith KE, USLE R background |
| S3 | Brown & Foster 1987 ASABE | revised storm-energy provenance |
| S4 | Foster et al. 1981 (SI conversion PDF) | K factor 0.1317, R SI factor 17.02 |
| S5 | CHIRPS v3 product page | CHIRPS coverage/resolution |
| S6 | Open-Meteo Historical Weather API docs | ERA5/reanalysis provenance |
| S7 | Marondedze & Schutt 2020 (Epworth RUSLE, MDPI Sustainability 12:8531) | Epworth/Harare equation and context |
| S8 | Hurni 1985 (secondary trace) | `R = -8.12 + 0.562*P` regional proxy |
| S9 | Oliveira et al. 2015 GISus-M / USDA-ARS | LS constants and exponent ranges |

Additional: Nakil & Khire 2023 (Catena/Earth-Science Reviews, systematic review of R-factor
equation misuse); Elwell & Stocking 1973/1976 (Zimbabwe erosivity, SLEMSA); Moore & Nieber 1989
/ Moore & Wilson 1992 (UCA LS framework).

## Outputs and tooling

Method comparison: `outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/` (diagnostics,
rasters, board, caption); `bin/investigate/explore_rfactor_methods.py`, `bin/visualize/plot_rfactor_exploration_board.py`.

ERA5 empirical: `outputs/v1_usle_soil_loss/rfactor_empirical_era5/` (point diagnostics, R
rasters, A diagnostics, boards, captions); `bin/investigate/compute_era5_empirical_rfactor.py`,
`bin/criteria/build_era5_rfactor_raster.py`, `bin/visualize/plot_era5_empirical_rfactor_board.py`,
`bin/visualize/plot_era5_rfactor_raster_board.py`.

V2 hotspot-survival (V2 A-factor outputs removed 2026-07-01 as deprecated; survival numbers
retained as recorded values in §5, not as re-runnable files):
`bin/factors/derive_v2_rfactor_candidates.py`,
`bin/factors/derive_v2_usle_soil_loss.py`, `bin/investigate/compare_v2_rfactor_candidates.py`.

Verification tooling: `bin/investigate/verify_ls_factor_exponents.py`; literature captures under
`outputs/literature_verification/`.

## Lineage

This note consolidates and replaces these earlier process notes (moved to `_archive/`):
- `rfactor_method_exploration_2026-06-19.md`
- `rfactor_investigation_verification_2026-06-19.md`
- `rfactor_empirical_era5_2026-06-19.md`
- `rfactor_formula_data_workflow_full_verification_2026-06-19.md`
- `formula_integrity_audit_2026-06-19.md`
- `v2_rfactor_processing_2026-06-16.md`
