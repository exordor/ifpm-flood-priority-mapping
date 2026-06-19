# USLE R-Factor for V1 (Upper Mzingwane): method and recommendation

Date: 2026-06-19

I have been working on the rainfall-erosivity (R) factor for the V1 catchment and have hit a
method choice I need you to decide. This note states the problem, what I found, and the one
decision I need from you. All R and soil-loss (A) figures here are exploratory until you decide.

## The problem

The V1 R-factor I had been using (CHIRPS Modified Fournier → Renard & Freimund) is wrong. I was
applying the paper's precipitation-based coefficients to the Modified Fournier Index, with a break
at MFI=80 that does not exist in the original paper. The original has two separate forms: a
precipitation form (break at P=850 mm) and an MFI form (break at F=55 mm, different coefficients).
Because V1's MFI sits between 70 and 117, the MFI=80 break I invented split the catchment into two
artificial clusters - the bimodality was an artifact of my error, not a real feature. I have
deprecated all V1 and V2 R and A products built on it (`outputs/.../DEPRECATED_DUE_TO_R_FACTOR_ERROR.md`).

That left the question: which R-factor method is correct for semi-arid Zimbabwe?

## What I found

I compared the standard literature formulas and then computed an R directly from ERA5 hourly
rainfall as an independent check (IMERG half-hourly would be better but needs a NASA account I
don't have).

The literature methods fall into two groups that disagree by about 4-6x. I have hand-checked each
one against its primary source and against the script output (verification note:
`context/docs/project-management/rfactor_investigation_verification_2026-06-19.md`); the numbers
below are confirmed.

| group | methods | R for V1 |
|---|---|---:|
| High | Renard-Freimund (US), an Arnoldus-family power law (Morocco), Elwell/Stocking 1976 (Zimbabwe) | 1380-3719 |
| Low | Hurni 1985 (Ethiopia), Epworth/Merritt (Harare RUSLE) | 240-320 |

One sourcing note on the Arnoldus-family entry: it uses the Nakil & Khire (2023) form
`R = 17.02·10^(1.5·log10(MFI)−0.8188)`. Its implied base coefficient (0.152) is not Arnoldus 1977's
0.264, so I am describing it as "Arnoldus-family" rather than "the Arnoldus equation with a unit
fix". It still lands squarely in the High group and does not change the conclusion.

One thing worth flagging: the "measured" Epworth value of 329 that is often cited is not actually a
measurement - that same paper computed it from its own Low-group equation (R = 38.5 + 0.35·M). So it
cannot be used to validate either group.

My independent ERA5 computation (45 points across V1, 2018-2023, standard EI30 algorithm with
Wischmeier-Smith and Brown-Foster kinetic energy) gives:

- V1 catchment-mean R ≈ 500 (range 360-510 across forms and points).

This matches the Low group and is about 4x below the High group. Since ERA5 hourly rainfall
under-represents short convective bursts, the true R is probably a bit higher than 500 but still
well below the High group.

My reading: the High formulas, including the Zimbabwe-native Elwell relation as it reaches me,
over-estimate R for our semi-arid convective regime by roughly 4x.

## What it means for soil loss

With the clean K·LS·C structure I already have (verified, R-invariant), R ≈ 500 gives an annual
soil loss A ≈ 0.6 t/ha/yr. The High group would give A ≈ 2-4 t/ha/yr. The spatial pattern of
erosion (where it is relatively worse) is set by slope and land cover and is the same under any R,
because R only scales the magnitude.

## The decision I need from you

Which R-factor should I use for V1? This is your call - it sets the magnitude of every soil-loss
result in the thesis. My recommendation is the ERA5-based value (≈ 500) or one of the Low-group
regional equations (Hurni or Epworth, ≈ 240-320). The one caveat is that ERA5 hourly data is a
lower bound on the true 30-minute R, so if you want a stricter figure, the route is a local rain
gauge or GPM IMERG data. Either way, I'm blocked on the R magnitude until you decide.

## Figures

- R vs the two groups: `outputs/v1_usle_soil_loss/rfactor_empirical_era5/mentor_era5_empirical_rfactor_board.png`
- Empirical R raster and soil loss A: `outputs/v1_usle_soil_loss/rfactor_empirical_era5/mentor_era5_rfactor_raster_board.png`
- Six-method literature comparison: `outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/mentor_rfactor_exploration_board.png`

## What this does not affect

The K, LS, and C factors are unchanged (I checked them against their sources). The soil-loss
hotspot pattern is robust. This is only about the R magnitude, and it does not by itself unlock any
flood-risk or intervention-priority interpretation.
