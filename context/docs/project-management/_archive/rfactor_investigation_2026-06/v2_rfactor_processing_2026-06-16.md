# V2 smoother R-factor candidates and hotspot survival test (2026-06-16)

> **PREMISE CORRECTION (2026-06-19, READ FIRST):** A deeper pass against the Renard & Freimund
> (1994) original PDF showed that the V1 bimodality this package was built to "resolve" was an
> ARTIFACT. V1 applied the P-based Renard-Freimund coefficients to MFI with an INVENTED break at
> MFI=80; the paper's F-based form (the MFI form) breaks at F=55 mm, and V1's MFI range (70-117)
> lies entirely in that upper branch, so there is no discontinuity and no bimodality under the
> correct formula. Therefore:
> - The "V2 resolves the V1 bimodality" framing does NOT hold and must NOT be presented to the
>   mentor as a real fix.
> - The V2 hotspot-survival test remains VALID as a structure test (it uses the R-invariant
>   K x LS x C reference and is independent of the R formula).
> - All V1/V2 R-factor ABSOLUTE values are NOT trustworthy until the mentor chooses the correct
>   R method for semi-arid Zimbabwe.
> - V2 mentor communication is PAUSED. See `formula_integrity_audit_2026-06-19.md` Finding 2.
>
> The rest of this document records the V2 work as executed; read it with the correction above in
> mind. The numerical results (bimodality bands, survival rates, Spearman) are correctly computed
> from the inputs as defined, but the inputs encode the V1 error, so the "smoother R resolves
> bimodality" conclusion is about an artifact, not a real property of the catchment's erosivity.

## Literature-integrity correction (2026-06-19, post-implementation review)

A post-implementation literature-integrity review found two issues that affect the formulas cited
in this package. Both are recorded here for the mentor before any of these results are presented:

1. **A "Lo et al. (1985)" candidate (R = 0.0737 * MFI^1.81) was removed.** A literature check
   showed Lo et al. 1985 used mean annual precipitation (not MFI) as the R predictor, and the
   0.0737/1.81 coefficients had no traceable source. They were an unverified/fabricated formula.
   The V2 candidate set is now V1-bimodal, Arnoldus, and RF-low-branch only (3 candidates).

2. **Renard & Freimund (1994) variable-confusion risk (inherited from V1, FLAGGED not silently
   fixed).** Renard & Freimund published BOTH a P-based form (R = 0.0483*P^1.61, P = mean annual
   precipitation, break at P=850 mm) AND an F-based form (F = Modified Fournier Index, DIFFERENT
   coefficients). The coefficients 0.0483/1.61/587.8/1.219/0.004105 applied to MFI in V1 and V2 are
   the P-based coefficients. This is an inherited V1 ambiguity. V2 preserves the V1 convention so
   the two remain comparable, but this is an open methodological risk for the mentor to resolve
   before any USLE result is used for a claim.

3. **Arnoldus (1980) coefficients are non-universal.** Arnoldus provided only the R = a*Fm^b
   framework; the 0.2647/1.5 values are regionally-fitted coefficients reported in some
   applications, not Arnoldus's original universal values (see Catena 2023 systematic review on the
   misuse of this equation). Treat Arnoldus here as a candidate smoothing function, not an
   authoritative formula.

Verified as correct (no change): K-factor conversion 0.1317 (Foster et al. 1981); LS formula
constants 22.13/0.0896 (Moore & Nieber 1989). The LS exponents 0.4/1.2 were additionally
verified: per USDA-ARS GISus-M (Oliveira et al. 2015, eq 13) the UCA LS form
`LS = (As/22.13)^m * (sin(theta)/0.0896)^n` uses m in [0.4-0.56] and n in [1.2-1.3]; the project's
0.4/1.2 are the lower-bound starting combination of that documented range (a standard, valid
choice within the Moore & Nieber 1989 / Moore & Wilson 1992 framework). Capture record:
`outputs/literature_verification/usda_ars_gisus_m.txt`.

## Trigger

Mentor decision 2026-06-16 (IFPM-074): keep the V1 bimodal R-factor as a diagnostic baseline,
switch V2 to a smoother R, and re-test whether the soil-loss hotspot pattern survives. Verbatim:
*"switch to a smoother R for V2, while preserving this V1 as a diagnostic baseline. If the spatial
hotspot pattern survives the smoother R test the evidence board becomes much stronger."*

This is a HiWi data-processing action (data production is GO); it does not authorise interpretable
soil-loss or intervention claims, and it does not commit a final V2 R formula.

## Why the V1 R-factor is bimodal

V1 uses the Renard & Freimund (1994) piecewise R(MFI):

- `R = 0.0483 * MFI^1.61` when `MFI < 80`
- `R = 587.8 - 1.219*MFI + 0.004105*MFI^2` when `MFI >= 80`

The V1 catchment MFI spans [69.9, 117.4] (mean 94.5), straddling the MFI=80 break. At the break R
jumps from ~105 to ~507, so cells cluster at a low mode (~50) and a high mode (~510) with ~0 cells
in between (29 / 0 / 103 in the <100 / 100-400 / >400 bands). This is the artifact the smoother
candidates are designed to resolve.

## Method

1. **Identical MFI** to V1 (Arnoldus 1980: `MFI = sum_i(Pi^2) / P_annual` over the 5 available
   rainy-season months, Nov-Mar; full-year P_annual in the denominator). Only the MFI->R conversion
   differs across candidates.

2. **Three candidates** (all share MFI, differ in MFI->R):

   | id | formula | role |
   |---|---|---|
   | `rf_v1_bimodal` | Renard-Freimund 1994 piecewise | V1 baseline (MFI=80 break) |
   | `rf_arnoldus` | `0.2647 * MFI^1.5` | V2 main candidate (non-universal regional coeffs) |
   | `rf_rf_low_branch` | `0.0483 * MFI^1.61` (full range) | minimal-change same-source |

   (A fourth "Lo et al. 1985" candidate was removed after the literature-integrity check above.)

3. **Hotspot survival test.** V1 R is a global zonal scalar, so the spatial pattern of A is
   mathematically fixed by `LS x C x K` and is invariant to R (R is only a multiplier). A pure
   scalar swap is therefore a weak test. To make the test meaningful, the smoother R is allowed to
   vary spatially on the native CHIRPS 0.05 deg grid, then recombined at 30 m FOR DIAGNOSTIC
   PURPOSES ONLY:

   - Path 1 (zonal-scalar A): `A_v2_zonal = a_structure * R_zonal_scalar`, where
     `a_structure = K x LS x C x P` (the V1 R-invariant raster).
   - Path 2 (spatially-varying A, diagnostic): `A_v2_spatial = K x LS x C x R_pixelwise`, with the
     0.05 deg R raster bilinearly resampled to the 30 m grid. This resample is labelled
     diagnostic-only and is **not** a pixel-level 30 m evidence product (per the V1 terrain
     reference grid rule).
   - Reference hotspots: the top p95 cells of `a_structure` (R-invariant; defined by LS x C x K
     only). Survival rate = fraction of these reference cells that remain in the top p95 of
     `A_v2_spatial`.

4. **Agreement metrics.** Pearson and Spearman of `A_v2_zonal` vs `A_v2_spatial` quantify how much
   R's spatial heterogeneity perturbs the pattern; Spearman is the key rank-agreement indicator for
   hotspots.

## Results

### Bimodality resolution (both smoother candidates resolve it)

| candidate | R mean | cells <100 / 100-400 / >400 | abs jump at MFI=80 |
|---|---:|---|---:|
| rf_v1_bimodal (baseline) | 408.0 | 29 / 0 / 103 | 460.6 |
| rf_arnoldus | 238.6 | 0 / 132 / 0 | 0.7 |
| rf_rf_low_branch | 71.8 | 127 / 5 / 0 | 0.2 |

The smoother candidates drop the MFI=80 jump from ~461 to <1 and populate the middle band. Arnoldus
is the cleanest (all 132 cells in the middle band). Note `rf_rf_low_branch` is continuous but low in
absolute R (it is the low branch extended), so it underestimates erosivity relative to Arnoldus.

### Hotspot survival (the answer to the mentor's question)

| candidate | A zonal mean (t/ha/yr) | survival rate | Spearman (zonal vs spatial) |
|---|---:|---:|---:|
| rf_v1_bimodal | 0.500 | 0.840 | 0.883 |
| rf_arnoldus | 0.293 | **0.869** | **0.990** |
| rf_rf_low_branch | 0.088 | 0.863 | 0.989 |

**Headline: the hotspot pattern survives under all candidates, including the V1 bimodal baseline.**
84-87% of the R-invariant (LS x C x K) hotspots remain in the top p95 of the spatially-varying A.

**Important caveat on the test's discriminating power (adversarial-review finding).** This test is
structurally biased toward high survival: the LS factor spans ~4 orders of magnitude across the
catchment while the bilinearly-resampled R field varies only ~3x, so the top-p95 tail is dominated
by LS x C and R can only modulate the fringe of the hotspot set. The fact that the *broken V1
bimodal baseline also scores 0.840* shows the test cannot distinguish a good R formula from a bad
one on this metric alone. Survival rates should therefore be read as a weak confirmatory signal
("terrain/land-cover governs hotspots, as expected"), not as a quality ranking between candidates.

**The stronger signal is the zonal-vs-spatial Spearman agreement.** The smoother candidates reach
0.99 while the V1 bimodal baseline reaches only 0.88: under a smoother R the cell-level soil loss is
far more internally consistent (the spatially-varying R barely perturbs the zonal-R pattern),
whereas the bimodal R injects a large discontinuous perturbation. This is consistent with the
bimodality being a methodological artifact rather than a real erosivity structure.

**Net interpretation for the evidence board:** the erosion-hotspot *locations* are robust to the
R-factor method (a terrain/land-cover signal), and the smoother R candidates additionally remove
the bimodal discontinuity. This supports the mentor's criterion that a surviving hotspot pattern
strengthens the evidence board, but the survival-rate metric itself is not the discriminating
evidence; the discontinuity resolution and the Spearman gain are.

## Outputs

Under `outputs/v1_usle_soil_loss/v2_rfactor/`:
- `a_v2_<candidate>_zonal_30m.tif`, `a_v2_<candidate>_spatial_DIAGNOSTIC_30m.tif` (per candidate;
  the `_DIAGNOSTIC` product embeds the 0.05 deg->30 m R resample and is not pixel-level evidence)
- `a_v2_<candidate>_zonal_classes_30m.tif`
- `v2_hotspot_survival_diagnostics.json`
- `v2_rfactor_candidate_summary.csv`, `v2_rfactor_candidate_correlation.csv`,
  `v2_rfactor_hotspot_survival.csv`
- `mentor_v2_rfactor_comparison_board.{png,pdf}`, `mentor_v2_rfactor_caption.md`

Under `outputs/chirps_v3_zimbabwe_prototype/r_factor_v2/`:
- `rasters/rf_<candidate>_0p05deg.tif` (per candidate)
- `v2_rfactor_diagnostics.json`, `v2_rfactor_processing_note.md`

Tooling scripts (TOOLING, local `bin/`): `derive_v2_rfactor_candidates.py`,
`derive_v2_usle_soil_loss.py`, `plot_v2_rfactor_comparison_board.py`,
`compare_v2_rfactor_candidates.py`.

## Claim boundaries (strict)

- All outputs are DIAGNOSTIC data products, not interpretable validated soil-loss maps.
- The 0.05 deg R raster resampled to 30 m for path 2 is diagnostic-only and is not a pixel-level
  30 m evidence product. This resample is a documented, narrowly-scoped waiver of the V1 terrain
  reference grid rule, recorded in `context/docs/data-management/v1_terrain_reference_grid_rule.md`
  ("Documented Diagnostic Waiver" section); the waiver does not extend to any other CHIRPS use.
- The hotspot survival rate is structurally biased toward high values (LS dynamic range >> R) and
  has low discriminating power (the V1 baseline also scores 0.84). It is reported as a weak
  confirmatory signal, not a candidate-quality ranking.
- Absolute A values remain R-method-dependent (Arnoldus A-mean 0.29 vs V1 0.50 vs RF-low-branch
  0.09). Absolute magnitudes are not comparable across candidates and are not interpretable.
- The final V2 R formula is still a mentor methodological decision. This package supplies
  candidates and evidence; it does not commit a choice.
- This work does not trigger AHP overlay, flood-risk interpretation, or intervention-priority
  interpretation.

## Recommendation for the mentor

- `rf_arnoldus` is the strongest V2 candidate: continuous, fills the middle band cleanly, and
  delivers the highest survival rate (0.869) and Spearman agreement (0.990). Its coefficients are
  regionally-fitted (not Arnoldus's universal values) - acceptable as a smoothing function, but the
  mentor should confirm the formula is suitable for the study area.
- `rf_rf_low_branch` is continuous but systematically low; useful only as a same-source lower bound.
- (A "Lo et al. 1985" candidate was removed during the literature-integrity check; its coefficients
  had no traceable source.)
- The Renard-Freimund P-vs-MFI variable-confusion risk (inherited from V1) is an open methodological
  item for the mentor to resolve before any USLE result supports a claim.
- Pending mentor confirmation of the V2 formula, the V1 bimodal R remains the documented baseline.
