# Mentor Briefing: USLE R-Factor Method Investigation (V1, semi-arid Zimbabwe)

Date: 2026-06-19

Status: internal mentor-facing briefing on a multi-round investigation of the rainfall-erosivity
(R) factor for the V1 catchment. It started from a discovered formula error, ran through a
literature comparison, exposed a circular "measured" anchor, and ended with an independent
empirical R-factor computed from ERA5 hourly data. The briefing asks one mentor decision: which
R-factor method/convention the thesis will adopt. It does NOT authorise any AHP overlay,
flood-risk interpretation, or intervention-priority interpretation. All R/A numbers here are
EXPLORATORY until the mentor decides.

## Why this investigation

The V1 R-factor (the CHIRPS Modified-Fournier -> Renard-Freimund product, IFPM-074) turned out to
use the wrong formula: it applied the **P-based** Renard & Freimund (1994) coefficients to the
Modified Fournier Index (MFI) with an **invented break at MFI=80**. Verified against the original
paper, the P-based form takes mean annual precipitation (break at P=850 mm) and the MFI-based form
breaks at F=55 mm with different coefficients. So the V1 bimodality (the thing the V2 smoother-R
exercise was built to "fix") was an artifact of the wrong break point. All V1/V2 R and USLE A
products are now marked DEPRECATED (see `formula_integrity_audit_2026-06-19.md`).

This triggered the question: what is the right R-factor method for semi-arid Zimbabwe? The
investigation below is the answer, with evidence.

## Headline (TL;DR)

- The literature splits into **two incompatible R-families ~4-6x apart**.
- An **independent empirical R computed from ERA5 hourly rainfall** (= 358-506, V1 zonal ~507 over
  a 45-point grid) supports the **LOW family** and contradicts the **HIGH family** (which includes
  the Zimbabwe-native Elwell/Stocking relation).
- The HIGH family over-estimates R for this semi-arid convective regime by ~4x.
- The one decision needed: adopt a **LOW-family regional R method** (Hurni 1985, the Epworth
  equation, a Zimbabwe-specific calibration, or the ERA5 empirical R) for the thesis, OR obtain a
  primary 30-min EI30 dataset (gauge / GPM IMERG) to refine it.

## The two R-families (literature comparison, 6 methods)

All on the same V1 CHIRPS inputs (P_annual mean 583.5 mm; MFI mean 92.92):

| method | formula | R zonal mean | family |
|---|---|---:|---|
| A: Corrected Arnoldus (Nakil & Khire 2023) | `R = 17.02*10^(1.5*log10(MFI)-0.8188)` | 2329 | HIGH |
| B: RF F-based correct (Eq 13/14) | `0.07397*F^1.847` / `95.77-6.081F+0.4770F^2` (F=MFI) | 3719 | HIGH |
| C: RF P-based correct (Eq 11/12) | `0.04830*P^1.61` / `587.8-1.219P+0.004105P^2` (P=P_annual) | 1380 | HIGH |
| (Elwell/Stocking 1976 Zimbabwe-native) | table: ~400 per 100mm, via RF1994 | ~2000 | HIGH |
| D: OLD V1 (WRONG, reference) | P-coeffs on MFI, invented break | 408 | (mixed) |
| E: Hurni (1985) regional R-P | `R = -8.12 + 0.562*P` | 320 | LOW |
| F: Epworth/Merritt (Harare RUSLE) | `R = 38.5 + 0.35*M` | 243 | LOW |

Two mutually incompatible families: HIGH ~1380-3719 (US + Morocco + Zimbabwe-native Elwell all
agree), LOW ~240-320 (Hurni + Epworth agree). The ~6x gap cannot be a coefficient nuance; it is a
definition/unit question that the literature alone cannot resolve.

## The circular-anchor problem

The obvious "measured" validation point - the Epworth (Harare) RUSLE value of 329 - is NOT
independent. That same paper computed 329 using its own Equation (2) `R = 38.5 + 0.35*M` (a LOW
family equation). So citing 329 to validate the LOW family is circular: it confirms the equation,
not the true R. There is no independent 30-min EI30 measurement for the V1 catchment in the
sources found. This is why the literature comparison alone could not settle the family.

## The empirical resolution (independent data)

To break the circularity, an empirical R was computed directly from **ERA5 hourly precipitation**
(open-meteo, no account needed; GPM IMERG half-hourly would be better but needs a NASA Earthdata
account that is unavailable). Method: standard USLE EI30 algorithm (Wischmeier-Smith and
Brown-Foster kinetic energy), storm segmentation, per-storm E x I30, annual sum; 7 sample points
then extended to a 45-point V1 grid (2018-2023).

| estimate | R (MJ mm ha-1 h-1 yr-1) |
|---|---:|
| Wischmeier-Smith, I60 lower bound | 460 |
| Brown-Foster, I60 lower bound | 358 |
| Wischmeier-Smith, I30 estimate (I60*1.1) | **506-507** |
| Brown-Foster, I30 estimate | 394 |

**The empirical R (~360-506, V1 zonal ~507 over 45 points) sits in/near the LOW family and is
~4x below the HIGH family.** Because ERA5 hourly is a lower bound on true 30-min EI30 (and ERA5
under-estimates convective intensity), the real R is likely somewhat above these values but still
well below the HIGH family.

**Conclusion: the independent empirical evidence supports the LOW family and contradicts the HIGH
family - including the Zimbabwe-native Elwell relation as currently available.** The HIGH family
appears to over-estimate R for this semi-arid convective regime by ~4x.

## What this implies for the USLE A (soil loss)

Using the verified-clean, R-invariant `a_structure = K*LS*C*P` (mean 0.0012 t/ha/yr per unit R),
the empirical R gives an indicative A:
- with empirical R = 507: **A ~ 0.62 t/ha/yr** (zonal; spatial variant agrees to <1%).
- with HIGH-family R ~2000: A ~ 2-4 t/ha/yr (4x higher).

The close agreement between zonal-R A and spatial-R A (0.621 vs 0.619) independently confirms that
the soil-loss hotspot pattern is governed by terrain and land cover (LS x C), not by rainfall
variation - a robustness result that holds regardless of the R choice.

## Figures available for the meeting

- `outputs/v1_usle_soil_loss/rfactor_empirical_era5/mentor_era5_empirical_rfactor_board.png` -
  empirical R vs the two families (bar chart with family bands).
- `outputs/v1_usle_soil_loss/rfactor_empirical_era5/mentor_era5_rfactor_raster_board.png` -
  empirical R raster + USLE A (4 panels).
- `outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/mentor_rfactor_exploration_board.png`
  - the 6-method + Elwell comparison board.

## The decision needed (one)

Which R-factor method/convention does the thesis adopt? Options, with the evidence weight:

| option | R for V1 | evidence | note |
|---|---:|---|---|
| **ERA5 empirical (Wisch, I30 est)** | ~507 | strongest: independent, spatial, physically computed | lower bound; needs ERA5 accepted as R source |
| Hurni (1985) | 320 | LOW family, widely used in data-scarce Africa | unit caveat (pre-SI calibration) |
| Epworth/Merritt | 243 | LOW family, used in Harare RUSLE | same circularity caveat, but matches Hurni |
| RF/Arnoldus (HIGH family) | 1380-3719 | contradicted by empirical data | over-estimates ~4x |
| Obtain primary 30-min EI30 (gauge / GPM IMERG) | TBD | would settle definitively | needs data access |

**HiWi recommendation (recommended):** adopt the **ERA5 empirical R (~507)** as the V1 R, OR a
LOW-family regional R (Hurni/Epworth, ~240-320), pending the mentor's view on whether ERA5 is an
acceptable R source and whether the lower-bound caveat is acceptable for the thesis claim level.
If a validated R is required, the path is a primary 30-min EI30 dataset (mentor-mediated gauge
access or a NASA Earthdata account for GPM IMERG).

## What this does NOT change

- The LS, C, K factors are unaffected (verified correct in the integrity audit).
- The spatial soil-loss structure (where erosion is relatively higher) is robust regardless of R.
- This does NOT unblock flood-risk, AHP overlay, or intervention-priority interpretation.
- The deprecated V1/V2 R and USLE A products stay deprecated until the mentor decides.

## Open caveat to carry to the mentor

The empirical R from ERA5 is a LOWER BOUND (hourly != 30-min; ERA5 under-estimates convective
storms). It is strong enough to decide the family, but for a quantitative A claim the mentor may
want either (a) to accept ERA5 with a documented uncertainty band, or (b) to obtain sub-daily
gauge / IMERG data to refine it. This is the one honest limitation of the recommendation.
