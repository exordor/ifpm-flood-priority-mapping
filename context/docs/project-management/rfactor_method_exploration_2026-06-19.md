# Exploratory R-factor method comparison for semi-arid Zimbabwe (2026-06-19)

Revision note 2026-06-19: this note is kept as the historical exploration log. For current
send/no-send decisions and source-checked wording, use
`context/docs/project-management/rfactor_formula_data_workflow_full_verification_2026-06-19.md`
and `context/docs/mentor-explanation/Mentor_RFactor_Figure_Send_Packet_2026-06-19.md`.
Do not use this note alone to brief the mentor.

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
| A | Arnoldus-family / Nakil-Khire MFI law | `R = 17.02 * 10^(1.50*log10(MFI) - 0.8188)` | Source-traced MFI power law; do not describe as a clean Arnoldus-1977 coefficient conversion |
| B | RF F-based correct | `R = 0.07397*F^1.847` if F<55 else `95.77-6.081*F+0.4770*F^2`, F=MFI | Renard & Freimund 1994, Eq 13/14 |
| C | RF P-based correct | `R = 0.04830*P^1.61` if P<850 else `587.8-1.219*P+0.004105*P^2`, P=P_annual | Renard & Freimund 1994, Eq 11/12 |
| D | OLD V1 (WRONG) | P-based coeffs on MFI, break at 80 | V1 error (kept as reference baseline only) |
| E | Hurni regional R-P | `R = -8.12 + 0.562*P` | Hurni 1985 (Erosion-Productivity-Conservation Systems in Ethiopia); data-scarce regional proxy. Unit caveat: pre-SI calibration. |
| F | Epworth/Merritt R-P | `R = 38.5 + 0.35*M` | Ndlovu et al. 2020 (MDPI Sustainability 12:8531) Eq 2, citing Merritt 2003 / Tundu 2018. This is the equation used to compute the "measured" Epworth 329 anchor. |

Methods A/B/D use MFI; C/E/F use P_annual. V1 inputs: P_annual mean 583.5 mm; MFI mean 92.92.

A further Zimbabwe-native reference (not a raster method, shown as a reference line): Stocking &
Elwell (1976), "Rainfall Erosivity over Rhodesia", whose R-vs-annual-rainfall table is reproduced in
Renard & Freimund (1994). At V1 P~583 the table gives R~2000 (slope ~400 MJ mm ha-1 h-1 yr-1 per
100 mm). Source is secondary reproduction (via RF1994), so treated as a reference point only.

## Measured Zimbabwe R-factor anchor (for sanity-checking) - WITH A CRITICAL CAVEAT

- Epworth (Harare area), RUSLE: R ~ 329 (1984-2000), ~ 315 (2000-2018) MJ mm ha-1 h-1 yr-1
- Southern Africa semi-arid lowlands: ~ 150-400
- Source: MDPI Sustainability 12(20):8531 (Epworth); Lesotho RUSLE assessments (lowlands)

**CRITICAL CAVEAT (added 2026-06-19): the Epworth 329 is NOT an independent measurement.** It was
computed in that same paper using Equation (2) `R = 38.5 + 0.35*M` (Merritt 2003 / Tundu 2018).
So 329 is a model output from the low-R family, not a primary EI30 observation. Citing it to
validate the low-R family (Hurni/Epworth) is circular. It is retained here only to expose that
circularity. There is NO independent measured EI30 R for the V1 catchment in the sources found.

## Results

| method | R zonal mean (MJ mm ha-1 h-1 yr-1) | family | notes |
|---|---:|---|---|
| A: Arnoldus-family / Nakil-Khire | 2329 | HIGH | source-traced MFI power law with coefficient caveat |
| B: RF F-based correct | 3719 | HIGH | US transfer formula |
| C: RF P-based correct | 1380 | HIGH | US transfer formula |
| (Elwell/Stocking 1976 ref) | ~2000 | HIGH | Zimbabwe-native, via RF1994 table |
| D: OLD V1 (WRONG) | 408 | (mixed) | errors happened to land mid-range |
| E: Hurni 1985 | 320 | LOW | Ethiopia regional R-P |
| F: Epworth/Merritt | 243 | LOW | Harare RUSLE Eq 2 |

Indicative USLE A estimates (A = a_structure_mean * R_zonal, R-invariant a_structure verified
clean): A ~ 2.8 (A), 4.5 (B), 1.7 (C), 0.5 (D), 0.39 (E), 0.30 (F) t/ha/yr. The ~15x spread across
methods shows the R choice dominates the A magnitude.

## Key finding (REVISED 2026-06-19 - this overturns the earlier single-family conclusion)

**The methods split into two mutually incompatible R-families that differ by ~6x, and the
"measured Zimbabwe 329" anchor is NOT independent evidence - it is a self-confirmation of the
low-R family.**

- **HIGH-R family** (~1400-3700): the US-calibrated Renard-Freimund forms (A/B/C) AND the
  Zimbabwe-native Elwell/Stocking (1976) relation (~2000 at V1 P~583) AGREE with each other.
  This is significant: Elwell/Stocking used Rhodesian (Zimbabwe) rainfall data, independent of the
  US calibration, yet lands in the same range. So the "US formulas don't transfer" hypothesis from
  the earlier draft is NOT supported once the Zimbabwe-native relation is included.
- **LOW-R family** (~240-320): Hurni (1985, Ethiopia) and the Epworth/Merritt equation (R=38.5+
  0.35*M, used in Harare RUSLE). These two agree with each other but are ~6x below the high family.
- **The "measured" Epworth 329 is circular.** It was computed using the F equation (R=38.5+0.35*M),
  so citing it as validation for the low-R family is circular reasoning - it confirms F, not the
  true R. The 329 is a model output, not an independent EI30 measurement.

**The earlier draft's conclusion ("US/Morocco formulas not transferable; Hurni matches measured") was
wrong** because it treated the Epworth 329 as an independent anchor. With the Elwell/Stocking
Zimbabwe-native relation added, the high-R family has independent Zimbabwe support, and the
low-R family's only "validation" is its own equation.

### The real open question

Which family uses the correct R definition/units? Both cannot be right for the same physical
quantity. Candidate explanations:
1. The low-R family may use a different R convention (e.g. Roose's West-Africa R, a per-storm
   rather than annual index, or unconverted units) that is ~6x smaller than USLE-standard R.
2. The high-R family may over-predict convective-storm erosivity in this regime.
3. Only a primary EI30 dataset (sub-daily rainfall from a local gauge) can settle this. Neither
   family has been validated against true EI30 in the V1 catchment.

This is precisely the question to put to the mentor - with the evidence that the two families
exist, that the Zimbabwe-native Elwell relation supports the high family, and that the low family's
"measured" anchor is circular.

## Implications for the project

1. The R-factor problem is a "two incompatible literature families, unresolved by available data"
   problem - NOT simply "wrong coefficients" or "non-transferable US formulas".
2. To settle R, the project needs ONE of:
   - a primary EI30 dataset (sub-daily gauge or GPM IMERG) in or near V1, to compute R directly and
     see which family it matches;
   - a mentor ruling on which R convention the thesis will adopt, with the family choice documented;
   - a traceable original source for the low-R family's equation (Hurni 1985 / the Merritt-Tundu
     chain) to resolve its units.
3. The USLE A absolute values cannot be settled until R is settled. The spatial structure (LS x C,
   via the clean a_structure) remains valid and ready to multiply by whichever R is chosen. The A
   estimate would be ~0.3 t/ha/yr (low family) or ~2-4 t/ha/yr (high family) - a >10x difference.

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
  for the R-factor. Catena / Earth-Science Reviews. Treat the MFI law here as Arnoldus-family with
  a coefficient-provenance caveat, not as a clean Arnoldus-1977 conversion.
- Hurni, H. (1985). Erosion-Productivity-Conservation Systems in Ethiopia. Proc. 4th ISCO,
  Maracay, pp. 654-674. (Method E: R = -8.12 + 0.562*P; verified via multiple secondary citations
  and the University of Pretoria thesis (Bobe 2004) which reproduces the equation.)
- Elwell, H.A. & Stocking, M.A. (1973); Elwell, H.A. (1976), Rainfall Erosivity over Rhodesia.
  Foundational Zimbabwe erosivity work; SLEMSA model uses kinetic energy E = 29.82 - 127.51/I
  directly, not a USLE R. Not yet incorporated as a method; noted as the route to a
  Zimbabwe-specific calibration if the mentor prefers it.
- Epworth (Harare) Zimbabwe RUSLE: MDPI Sustainability 12(20):8531.
- Foster et al. (1981). Conversion of the USLE to SI metric units. JSWC 36. (17.02 / 0.1317.)
