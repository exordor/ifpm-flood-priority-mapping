# USLE R-Factor for V1 (Upper Mzingwane): method and recommendation

Date: 2026-06-19

I have been working on the rainfall-erosivity (R) factor for the V1 catchment and have run into a
method problem I'd like your decision on. This note states the problem, what I found, and the one
question I need answered. All R and soil-loss (A) figures here are exploratory until you decide.

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

The literature methods fall into two groups that disagree by about 4-6x:

| group | methods | R for V1 |
|---|---|---:|
| High | Renard-Freimund (US), Arnoldus (Morocco), Elwell/Stocking 1976 (Zimbabwe) | 1380-3719 |
| Low | Hurni 1985 (Ethiopia), Epworth/Merritt (Harare RUSLE) | 240-320 |

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

## The question

Which R-factor do you want me to use? My recommendation is the ERA5-based value (≈ 500) or one of
the Low-group regional equations (Hurni or Epworth, ≈ 240-320). The one caveat is that ERA5 hourly
data is a lower bound on the true 30-minute R, so if you need a stricter figure, the route is a
local rain gauge or GPM IMERG data.

## Figures

- R vs the two groups: `outputs/v1_usle_soil_loss/rfactor_empirical_era5/mentor_era5_empirical_rfactor_board.png`
- Empirical R raster and soil loss A: `outputs/v1_usle_soil_loss/rfactor_empirical_era5/mentor_era5_rfactor_raster_board.png`
- Six-method literature comparison: `outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/mentor_rfactor_exploration_board.png`

## What this does not affect

The K, LS, and C factors are unchanged (I checked them against their sources). The soil-loss
hotspot pattern is robust. This is only about the R magnitude, and it does not by itself unlock any
flood-risk or intervention-priority interpretation.
