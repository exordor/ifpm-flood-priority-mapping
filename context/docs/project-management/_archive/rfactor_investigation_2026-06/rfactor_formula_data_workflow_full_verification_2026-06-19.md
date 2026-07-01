# R-factor formula, data, and workflow verification

Date: 2026-06-19

Status: unsafe Teams send paused until this verification is used to replace the draft. This does
not pause new R-factor work with fresh lineage.

2026-06-29 execution-status update: known-invalid R/A products remain deprecated, but new
R-factor products may be generated as `provisional` or `sensitivity_scenario` outputs if method,
source, value range, uncertainty, and lineage are documented. Waiting for mentor confirmation
should downgrade claim level, not stop all R-factor experiments.

Verdict:

- Figure 1 is conditionally usable as a method-comparison figure.
- Figure 2 is conditionally usable as an ERA5 lower-bound check.
- Figure 3 is blocked because it repeats the invalid "V2 resolves bimodality" framing.
- All V1/V2 R-factor and A-factor outputs based on the old Renard-Freimund mistake remain
  deprecated.
- `a_structure_K_LS_C_30m.tif` remains usable as an R-invariant structure layer, but not as a
  flood-risk or intervention-priority result.

Every verification row below lists source IDs. If a row has no source, it is not allowed to support
a mentor-facing claim.

## Source register

| id | source | type | what it supports | current use |
|---|---|---|---|---|
| S1 | Renard & Freimund 1994, official USDA/ARS PDF, https://www.tucson.ars.ag.gov/unit/publications/PDFfiles/942.pdf | primary paper copy | USLE equation, R-factor meaning, Brown-Foster kinetic-energy equation, RF P-form and F-form equations | formula audit and R-method comparison |
| S2 | Wischmeier & Smith 1978, USDA Agriculture Handbook 537, https://www.ars.usda.gov/ARSUserFiles/60600505/RUSLE/AH_537%20Predicting%20Rainfall%20Soil%20Losses.pdf | primary handbook copy | Wischmeier-Smith kinetic-energy equation and USLE rainfall erosivity background | ERA5 EI calculation check |
| S3 | Brown & Foster 1987 ASABE abstract, https://elibrary.asabe.org/abstract.asp?aid=31957&t=1 | bibliographic source | revised storm-energy method provenance | ERA5 EI calculation source trail |
| S4 | Foster, McCool, Renard & Moldenhauer 1981 SI conversion PDF, https://www.engr.colostate.edu/~pierre/ce_old/Projects/linkfiles/USLE%20Unit%20conversions.pdf | primary/hosted copy | K conversion factor 0.1317 and R SI conversion factor 17.02 | K and unit checks |
| S5 | CHIRPS v3 official product page, https://www.chc.ucsb.edu/data/chirps3 | official data documentation | CHIRPS v3 coverage, 0.05 degree gridded rainfall, 1981 to near-present | CHIRPS data provenance |
| S6 | Open-Meteo Historical Weather API docs, https://open-meteo.com/en/docs/historical-weather-api | official API documentation | historical/reanalysis data source and ERA5/ERA5-Land consistency note | ERA5/Open-Meteo provenance caveat |
| S7 | Marondedze & Schutt 2020 Epworth RUSLE paper, https://www.mdpi.com/2071-1050/12/20/8531 | peer-reviewed Zimbabwe case study | Epworth/Harare RUSLE context and equation-based local reference | lower Zimbabwe reference, not direct EI30 validation |
| S8 | Hurni R-P equation secondary trace, e.g. Ghana RUSLE article snippets and later African RUSLE papers | secondary trace only | `R = -8.12 + 0.562P` regional R-P proxy | exploratory low-family comparison only |
| S9 | Oliveira et al. 2015 GISus-M / USDA-ARS PDF, https://www.tucson.ars.ag.gov/unit/publications/PDFfiles/2279.pdf | USDA-hosted paper | LS equation constants and exponent ranges | LS factor check |
| L1 | `context/docs/project-management/formula_integrity_audit_2026-06-19.md` | local audit | deprecated R/A finding and exact error explanation | authoritative local formula audit |
| L2 | `context/docs/project-management/rfactor_investigation_verification_2026-06-19.md` | local audit | hand-calculated six-method values and ERA5 logic check | headline number verification |
| L3 | `outputs/v1_usle_soil_loss/DEPRECATED_DUE_TO_R_FACTOR_ERROR.md` | local output marker | product-level do-not-use list | output gating |
| L4 | `outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/rfactor_method_exploration_diagnostics.json` | local diagnostic | six method zonal means, CHIRPS inputs, valid cells | Figure 1 values |
| L5 | `outputs/v1_usle_soil_loss/rfactor_empirical_era5/era5_empirical_rfactor_diagnostics.json` | local diagnostic | 7-point ERA5 EI check | Figure 2 point panel |
| L6 | `outputs/v1_usle_soil_loss/rfactor_empirical_era5/era5_rfactor_raster_diagnostics.json` | local diagnostic | 45-point ERA5 rasterized check and A scalar diagnostic | Figure 2 summary panel |
| L7 | `outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/chirps_v1_raw_file_manifest.csv` | local manifest | CHIRPS download inventory, URLs, size, SHA-256 | data governance |

## Formula verification matrix

| item | implemented / discussed formula | source annotation | verification result | decision |
|---|---|---|---|---|
| USLE/RUSLE product form | `A = R x K x L x S x C x P` | S1 | Source confirms the product form and that R and K carry units. | Use only after R is accepted; do not call current A final. |
| RF P-form | `R = 0.04830*P^1.610` for `P < 850`; quadratic form for `P >= 850` | S1, L1, L2 | Hand check confirms P is annual precipitation and the break is P=850 mm. | Valid formula, but it must be applied to P, not MFI. |
| RF F/MFI-form | `R = 0.07397*F^1.847` for `F < 55`; quadratic form for `F >= 55` | S1, L1, L2 | Hand check confirms F is Modified Fournier Index and the break is F=55 mm. | Valid formula, but gives very high V1 values; mentor method decision needed. |
| Old V1 R | P-form coefficients applied to MFI with invented `MFI=80` break | S1, L1, L3 | This is a compound error: wrong predictor and invented break point. | Deprecated; may appear only as labelled wrong reference. |
| Method A | `17.02*10^(1.50*log10(MFI)-0.8188)` | S4, L2, plus secondary method trace | Value is traceable as a Nakil-Khire / Arnoldus-family MFI law, but the coefficient is not a clean Arnoldus-1977 conversion. | Keep only as high-family comparison; fix wording. |
| Hurni regional R-P | `R = -8.12 + 0.562P` | S8, L2 | Secondary trace supports equation, but primary Hurni source is not yet captured. | Exploratory proxy only; do not treat as final Zimbabwe calibration. |
| Epworth/Harare R-P | `R = 38.5 + 0.35M` | S7, L2 | Zimbabwe case-study page confirms Equation 2 context; search snippet/PDF confirms formula text. | Useful local lower reference; not a direct measured EI30 value. |
| Wischmeier-Smith kinetic energy | `e = 0.119 + 0.0873 log10(i)` with high-intensity cap | S2, L2 | Local ERA5 implementation was hand-checked against source form and one storm example. | OK as one ERA5 sensitivity route. |
| Brown-Foster kinetic energy | `e = 0.29*(1 - 0.72 exp(-0.05i))` | S1, S3, L2 | RF1994 reproduces the Brown-Foster equation and ASABE page confirms source identity. | OK as second ERA5 sensitivity route. |
| K conversion | `K_SI = K_US * 0.1317` | S4, L1, L2 | Conversion factor and local K mean were checked. | OK. |
| LS factor | `(As/22.13)^m * (sin(theta)/0.0896)^n`, current `m=0.4`, `n=1.2` | S9, L1, L2 | Constants and exponent range are source-backed; current exponents are conservative lower-end values. | OK, but state as a chosen parameter set. |

## Data verification matrix

| data item | local evidence | source annotation | checks completed | decision |
|---|---|---|---|---|
| CHIRPS v3 rainfall | `data/raw/chirps_v3_zimbabwe_prototype/`; manifest has 561 records plus header | S5, L7 | Manifest records source URL, file size, SHA-256, and checked timestamp. | Data inventory OK. |
| CHIRPS temporal coverage used for method comparison | annual 1981-2024; rainy months Nov-Mar; 132 valid V1 cells | S5, L4 | Diagnostics confirm `n_annual_files=44`, MFI mean 92.92, annual P mean 583.45 mm. | OK for exploratory method comparison. |
| ERA5/Open-Meteo hourly | `data/raw/era5_hourly_precip_v1_rfactor/`, 52 local JSON files | S6, L5, L6 | 7-point empirical board and 45-point raster check exist; caveat says hourly is lower bound for true 30-min EI30. | OK as independent lower-bound check, not final R. |
| V1 old R/A outputs | deprecated markers under `outputs/.../DEPRECATED_DUE_TO_R_FACTOR_ERROR.md` | S1, L1, L3 | Deprecated file lists affected products and unaffected products. | Do not use or send as model result. |
| `a_structure_K_LS_C_30m.tif` | listed as safe in deprecation marker | S4, S9, L1, L3 | It contains no R-factor, so the old R error does not affect it. | Keep as structure-only input for future rerun. |
| Figure 1 image | `outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/mentor_rfactor_exploration_board.png` | S1, S4, S7, S8, L2, L4 | Regenerated and visually checked; Method A now uses cautious Arnoldus-family wording. | Conditionally sendable. |
| Figure 2 image | `outputs/v1_usle_soil_loss/rfactor_empirical_era5/mentor_era5_empirical_rfactor_board.png` | S1, S2, S3, S6, L5, L6 | Regenerated and visually checked; title now says ERA5 is a lower-bound check. | Conditionally sendable. |
| Figure 3 image | `outputs/teams_handoff/rfactor_first_round/03_v1_v2_rfactor_comparison_captioned.png` | S1, L1, L3 | Visual review finds invalid title/framing; source audit blocks the claim. | Do not send. |

## Experimental workflow verification

| step | current workflow | source annotation | check result | gate |
|---|---|---|---|---|
| 1. Boundary | V1 controlled prototype boundary only | local V1 decision docs, L1 | Boundary status remains prototype-only with waiver. | OK for diagnostics, not final thesis boundary. |
| 2. Rainfall input | CHIRPS used for monthly/annual rainfall and MFI; ERA5 used as independent hourly check | S5, S6, L4, L5, L6 | CHIRPS and ERA5 are separate data products; ERA5 is not used to pretend CHIRPS has 30-min intensity. | OK. |
| 3. R methods | Multiple formulas compared from same V1 rainfall inputs | S1, S4, S7, S8, L2, L4 | Numeric means match hand calculations except expected non-linear mean effects. | OK for method comparison only. |
| 4. Old V1/V2 outputs | Old R/A products remain deprecated | S1, L1, L3 | Figure 3 violates the new deprecation logic. | Block. |
| 5. A-factor magnitude | Current valid statement is only `A = a_structure x provisional/sensitivity R` until final R is accepted | S1, S4, S9, L1, L3 | No accepted final R exists yet. | Allow provisional/sensitivity A; block final A. |
| 6. Flood risk / intervention | No final flood-risk map or intervention-priority map is authorized by this R check | AGENTS rules, L1, L3 | No current figure should be called final flood risk. | Block final interpretation. |

## Corrected send decision

I should not send the current Teams draft as-is.

Sendable after caption replacement:

- Figure 1 with the method-choice caption.
- Figure 2 with the ERA5 lower-bound caption.

Blocked:

- Figure 3 and any text saying V2 fixed a real R bimodality.
- Any soil-loss A magnitude as a final result.
- Any final flood-risk, sediment-risk, AHP, overlay, or intervention-priority claim.

## Required wording corrections

- Replace "Corrected Arnoldus" with "Arnoldus-family / Nakil-Khire MFI law" unless the text
  explicitly states the coefficient caveat.
- Replace "high formulas are about 4x too high" with "high-family formulas are much larger than
  the ERA5 lower-bound and lower Zimbabwe references".
- Replace "ERA5 proves the low family" with "ERA5 supports the lower range as an independent
  lower-bound check".
- Replace "V2 resolves bimodality" with "the old bimodality was an artifact; do not use the V2
  comparison board".

## Adversarial review

Domain/correctness findings:

- P1: Figure 3 is unsafe because it repeats an invalid causal story. Fixed by blocking the figure
  in the send packet and disabling the regeneration script.
- P2: Method A wording could overclaim Arnoldus provenance. Fixed in the script label and caption
  language.
- P2: ERA5 can be misread as final R. Fixed by requiring "hourly lower-bound check" in the caption.

Engineering/data-governance findings:

- P2: Deprecated output could be regenerated by mistake. Fixed by adding a hard stop to
  `bin/plot_v2_rfactor_comparison_board.py`.
- P3: Images and raw data are ignored outputs/data. Confirm with `git check-ignore` before any
  commit; do not stage them.

## Next safe action

Use `context/docs/mentor-explanation/Mentor_RFactor_Figure_Send_Packet_2026-06-19.md` as the only
send source. Remove Figure 3 from the Teams draft before sending anything.
