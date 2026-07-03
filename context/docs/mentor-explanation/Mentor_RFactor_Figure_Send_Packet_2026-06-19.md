# R-factor figure send packet

I should not send the current three-image packet as-is. I can send Figure 1 and Figure 2 after
using the safer captions below. I should not send Figure 3.

My one question for Supervisor is:

> Which R-factor route should I use for the next V1 rerun: an ERA5-based provisional R, or should I
> first look for rain-gauge / GPM data for a stricter erosivity estimate?

## Figure 1 - can send with this caption

![Figure 1](/Users/jlw/code/IFPM/outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/mentor_rfactor_exploration_board.png)

Caption to paste:

> Fig. 1: I checked several R-factor methods. They split into low and high value groups. This is
> only for choosing the R method, not a final result. The old V1 method is shown only as a wrong
> reference.

Why I can send it:

- The old V1 method is clearly labelled as wrong.
- The figure is framed as exploratory.
- The values come from the current diagnostics file:
  `outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/rfactor_method_exploration_diagnostics.json`.
- The image was regenerated after the wording fix, so Method A now appears as
  "Arnoldus-family / Nakil-Khire MFI law".

Limits I need to keep with the figure:

- Method A must be described as "Arnoldus-family / Nakil-Khire MFI law", not as a clean Arnoldus
  unit conversion.
- The figure does not prove which R family is correct.
- The Epworth value is an equation-based local reference, not a direct EI30 measurement.

Source anchors: [S1], [S4], [S7], [S8], [L1], [L2], [L4].

## Figure 2 - can send with this caption

![Figure 2](/Users/jlw/code/IFPM/outputs/v1_usle_soil_loss/rfactor_empirical_era5/mentor_era5_empirical_rfactor_board.png)

Caption to paste:

> Fig. 2: I used ERA5 hourly rainfall as an independent check. It gives R around 500, so it supports
> the lower range, but it is still a lower-bound check because ERA5 is hourly and not true 30-minute
> rainfall intensity.

Why I can send it:

- It says ERA5 is a lower bound.
- It is useful as an independent check against CHIRPS-only formulas.
- The values come from local downloaded ERA5/Open-Meteo JSON files and diagnostics:
  `outputs/v1_usle_soil_loss/rfactor_empirical_era5/era5_empirical_rfactor_diagnostics.json` and
  `outputs/v1_usle_soil_loss/rfactor_empirical_era5/era5_rfactor_raster_diagnostics.json`.
- The image was regenerated after the wording fix, so the title says ERA5 is a lower-bound check,
  not final proof.

Limits I need to keep with the figure:

- It does not validate a final R-factor.
- It does not unlock final soil-loss, flood-risk, or intervention maps.
- If Supervisor wants stricter erosivity, the next step is rain-gauge or GPM/IMERG-style sub-hourly
  data, not another CHIRPS-only shortcut.

Source anchors: [S1], [S2], [S3], [S6], [L2], [L5], [L6].

## Figure 3 - do not send

![Figure 3](/Users/jlw/code/IFPM/outputs/teams_handoff/rfactor_first_round/03_v1_v2_rfactor_comparison_captioned.png)

I should not send this figure.

Reason:

- It says "smoother R resolves bimodality".
- The formula audit found that the bimodality was not a real data feature. It was created by the
  old wrong Renard-Freimund break point.
- The R and A values behind this figure are deprecated.

What remains usable:

- The K x LS x C structure check is still useful internally.
- I should only share that later as a separate structure-only figure, not as "V2 fixed R".

Source anchors: [S1], [L1], [L3].

## Short message after the figures

> I found that my old R formula had an error, so I paused the old R/A outputs.
>
> The two checks above show the method choice problem: some formulas give very high R, while ERA5
> and the simpler regional equations give a lower range.
>
> My question is simple: should I use an ERA5-based provisional R for the next V1 rerun, or should
> I first look for rain-gauge / GPM data?

## Source anchors

- [S1] Renard, K.G. & Freimund, J.R. (1994). Using monthly precipitation data to estimate the
  R-factor in the revised USLE. Journal of Hydrology 157. Official USDA/ARS PDF:
  https://www.tucson.ars.ag.gov/unit/publications/PDFfiles/942.pdf
- [S2] Wischmeier, W.H. & Smith, D.D. (1978). Predicting rainfall erosion losses. USDA Agriculture
  Handbook 537. Official USDA/ARS PDF:
  https://www.ars.usda.gov/ARSUserFiles/60600505/RUSLE/AH_537%20Predicting%20Rainfall%20Soil%20Losses.pdf
- [S3] Brown, L.C. & Foster, G.R. (1987). Storm erosivity using idealized intensity distributions.
  Transactions of the ASAE 30(2):379-386:
  https://elibrary.asabe.org/abstract.asp?aid=31957&t=1
- [S4] Foster, G.R., McCool, D.K., Renard, K.G. & Moldenhauer, W.C. (1981). Conversion of the USLE
  to SI metric units:
  https://www.engr.colostate.edu/~pierre/ce_old/Projects/linkfiles/USLE%20Unit%20conversions.pdf
- [S5] CHIRPS v3 official product page:
  https://www.chc.ucsb.edu/data/chirps3
- [S6] Open-Meteo Historical Weather API data-source note:
  https://open-meteo.com/en/docs/historical-weather-api
- [S7] Marondedze, A.K. & Schutt, B. (2020). Assessment of Soil Erosion Using the RUSLE Model for
  the Epworth District, Harare Metropolitan Province, Zimbabwe. Sustainability 12(20):8531:
  https://www.mdpi.com/2071-1050/12/20/8531
- [S8] Hurni equation source status: secondary trace only in the current audit; use as a regional
  sanity check, not as a primary Zimbabwe calibration.
- [L1] `context/docs/project-management/rfactor_investigation_consolidated.md`
- [L2] `context/docs/project-management/rfactor_investigation_consolidated.md`
- [L3] `outputs/v1_usle_soil_loss/DEPRECATED_DUE_TO_R_FACTOR_ERROR.md`
- [L4] `outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/rfactor_method_exploration_diagnostics.json`
- [L5] `outputs/v1_usle_soil_loss/rfactor_empirical_era5/era5_empirical_rfactor_diagnostics.json`
- [L6] `outputs/v1_usle_soil_loss/rfactor_empirical_era5/era5_rfactor_raster_diagnostics.json`
