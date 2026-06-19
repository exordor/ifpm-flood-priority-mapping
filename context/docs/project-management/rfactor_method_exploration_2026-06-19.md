# Exploratory R-factor method comparison for semi-arid Zimbabwe (2026-06-19)

Status: EXPLORATORY experiment to inform the mentor R-method decision after the V1 formula error
(formula_integrity_audit_2026-06-19.md, Finding 2). Not a validated result. This document records
what was tested, what was found, and what it implies.

## Why this experiment

The integrity audit established that V1 applied the wrong Renard-Freimund coefficients to MFI with
an invented break at MFI=80. The natural follow-up question is: which R-factor method is correct
for semi-arid Zimbabwe? Rather than leave this as an abstract choice for the mentor, this
experiment runs four literature-based methods on the same V1 CHIRPS inputs and compares them to
MEASURED Zimbabwe R-factor values. The goal is to turn "which method?" into a question with
concrete evidence behind it.

## Methods tested (all literature-sourced, no fabricated coefficients)

| id | method | formula | source |
|---|---|---|---|
| A | Corrected Arnoldus | `R = 17.02 * 10^(1.50*log10(MFI) - 0.8188)` | Nakil & Khire 2023 (Catena systematic review) - Arnoldus form WITH the 17.02 imperial->metric unit conversion |
| B | RF F-based correct | `R = 0.07397*F^1.847` if F<55 else `95.77-6.081*F+0.4770*F^2`, F=MFI | Renard & Freimund 1994, Eq 13/14 |
| C | RF P-based correct | `R = 0.04830*P^1.61` if P<850 else `587.8-1.219*P+0.004105*P^2`, P=P_annual | Renard & Freimund 1994, Eq 11/12 |
| D | OLD V1 (WRONG) | P-based coeffs on MFI, break at 80 | V1 error (kept as reference baseline only) |
| E | Hurni regional R-P | `R = -8.12 + 0.562*P` | Hurni 1985 (Erosion-Productivity-Conservation Systems in Ethiopia); data-scarce regional proxy. Unit caveat: pre-SI calibration. |

Methods A/B/D/E share the same MFI input (`sum_i(Pi^2)/P_annual`, Nov-Mar, full-year P_annual)
computed from the V1 CHIRPS climatology; methods C and E use P_annual directly. V1 inputs:
P_annual mean 583.5 mm; MFI mean 92.92.

## Measured Zimbabwe R-factor anchor (for sanity-checking)

- Epworth (Harare area), RUSLE: R ~ 329 (1984-2000), ~ 315 (2000-2018) MJ mm ha-1 h-1 yr-1
- Southern Africa semi-arid lowlands: ~ 150-400
- Source: MDPI Sustainability 12(20):8531 (Epworth); Lesotho RUSLE assessments (lowlands)

A defensible R for the V1 catchment is therefore expected in the low hundreds, NOT thousands.

## Results

| method | R zonal mean (MJ mm ha-1 h-1 yr-1) | ratio to measured (~330) | verdict |
|---|---:|---:|---|
| A: Corrected Arnoldus | 2329 | 7.1x | far above measured |
| B: RF F-based correct | 3719 | 11.3x | far above measured |
| C: RF P-based correct | 1380 | 4.2x | far above measured |
| D: OLD V1 (WRONG) | 408 | 1.2x | near measured (but wrong, errors cancelled) |
| E: Hurni 1985 regional R-P | 320 | 1.0x | **within measured range, ~Epworth 329** |

Indicative USLE A estimates (A = a_structure_mean * R_zonal, with the verified-clean R-invariant
a_structure): A ~ 2.8 t/ha/yr (A), 4.5 (B), 1.7 (C), 0.5 (D), 0.39 (E). These vary ~11x across
methods, underscoring that the R choice dominates the A magnitude.

## Key finding

**The three standard transfer formulas (A/B/C) over-estimate the measured Zimbabwe R-factor by
3-11x. The OLD WRONG V1 method (D) falls near the range only because its errors cancelled. Method E
(Hurni 1985 regional R-P regression) gives R ~ 320, within the measured semi-arid range and almost
exactly the Epworth/Harare measured value of 329.**

This is strong evidence that:
1. The **Renard-Freimund (US-calibrated, 132 stations) and Arnoldus (Morocco-calibrated) relations
   are NOT transferable to semi-arid Zimbabwe.** The catchment's rainfall regime (concentrated
   convective storms, MFI ~93, P ~583 mm) produces an erosivity structure these temperate/US
   regressions do not capture. The 2023 Catena systematic review flags exactly this class of
   transferability problem.
2. A **regional R-P method is the promising direction.** Hurni (1985), calibrated for the Ethiopian
   Highlands, matches the measured southern-African R magnitude despite being from a different
   (though also semi-arid tropical) region. A Zimbabwe-specific calibration (Elwell & Stocking's
   work, see below) would be even better.

### Note on Hurni units
Hurni's original (1985) calibration predates the strict RUSLE SI standardization, so its output
units are ambiguous (older USLE English vs MJ mm ha-1 h-1). Despite this, its magnitude matches the
measured Zimbabwe R, so it is a strong candidate. The unit caveat must be resolved (or the result
accepted as an order-of-magnitude match) before Hurni is used for any quantitative A claim.

## Implications for the project

1. The R-factor method is not a "fix the coefficient" problem; it is a "the standard US/Morocco
   formulas do not fit this region" problem. This reframes the mentor question.
2. Candidate paths forward (for the mentor to weigh), now with concrete evidence:
   - **Hurni (1985) `R = -8.12 + 0.562*P`** - the only tested method matching measured R; strong
     candidate, with a unit caveat to resolve.
   - a Zimbabwe-specific R-P/R-MFI calibration - Elwell & Stocking (1973) and Elwell (1976,
     "Rainfall Erosivity over Rhodesia") are the foundational Zimbabwe references; their SLEMSA
     model uses kinetic energy directly (E = 29.82 - 127.51/I) rather than a USLE R, so adopting
     them needs a conversion or a move to SLEMSA. Worth checking whether Elwell published an R-P
     regression directly usable in USLE.
   - direct EI30 / R computation from sub-daily rainfall if a higher-temporal-resolution source is
     available (CHIRPS-daily is not storm-resolved, but a regional gauge or GPM IMERG might be);
   - adoption of a published regional R value (e.g. the Epworth ~329) as a documented scalar.
3. The USLE A absolute values cannot be settled until R is settled. The spatial structure (LS x C,
   via the clean a_structure) remains valid and ready to multiply by whichever R is chosen.

## What this experiment does NOT do

- It does not pick the R method; it provides the evidence for the mentor to pick.
- It does not validate any A value; the A estimates are indicative (zonal-scalar R).
- It does not re-derive the V1 R or replace the deprecated V1/V2 products; those stay deprecated.
- The measured Zimbabwe anchor is from a different sub-catchment (Epworth/Harare) - it is a
  regional sanity check, not a V1-specific calibration. A V1-specific R would need local gauge data.

## Outputs

- `outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/rfactor_method_exploration_diagnostics.json`
- `outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/rasters/<method>_0p05deg.tif` (4 files)
- `outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/mentor_rfactor_exploration_board.{png,pdf}`
- `outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/mentor_rfactor_exploration_caption.md`
- Tooling: `bin/explore_rfactor_methods.py`, `bin/plot_rfactor_exploration_board.py`

## Sources

- Renard, K.G. & Freimund, J.R. (1994). Using monthly precipitation data to estimate the R-factor
  in the revised USLE. J. Hydrology 157, 287-306. (Eq 11-14 verified against the original PDF.)
- Nakil, M. & Khire, M. (2023). A systematic review of the incorrect use of an empirical equation
  for the R-factor. Catena / Earth-Science Reviews. (Corrected Arnoldus form with 17.02 conversion.)
- Hurni, H. (1985). Erosion-Productivity-Conservation Systems in Ethiopia. Proc. 4th ISCO,
  Maracay, pp. 654-674. (Method E: R = -8.12 + 0.562*P; verified via multiple secondary citations
  and the University of Pretoria thesis (Bobe 2004) which reproduces the equation.)
- Elwell, H.A. & Stocking, M.A. (1973); Elwell, H.A. (1976), Rainfall Erosivity over Rhodesia.
  Foundational Zimbabwe erosivity work; SLEMSA model uses kinetic energy E = 29.82 - 127.51/I
  directly, not a USLE R. Not yet incorporated as a method; noted as the route to a
  Zimbabwe-specific calibration if the mentor prefers it.
- Epworth (Harare) Zimbabwe RUSLE: MDPI Sustainability 12(20):8531.
- Foster et al. (1981). Conversion of the USLE to SI metric units. JSWC 36. (17.02 / 0.1317.)
