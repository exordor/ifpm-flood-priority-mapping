# Hypotheses

Status: active. Testable claims with verdicts.

Verdict vocabulary (per research-governance framework, mapped onto IFPM
claim levels):

| verdict | meaning |
|---|---|
| `supported` | evidence backs the claim at the listed claim level |
| `rejected` | evidence contradicts the claim |
| `partially_supported` | evidence backs a restricted form of the claim |
| `unresolved` | evidence is insufficient or inconsistent; needs more data |
| `needs_replication` | one observation; needs repeat |
| `abandoned` | dropped; no longer pursued |

## H-BIMODALITY-ARTIFACT

**Statement:** The V1 R-factor bimodality (29 low / 103 high cells) is an
artifact of applying P-based Renard-Freimund coefficients to MFI with an
invented break at MFI=80, not a real erosivity structure.

- **Related RQ:** RQ1
- **Evidence:** Renard-Freimund PDF re-extracted; the correct F-based form breaks
  at F=55 mm; V1's MFI range (70-117) lies entirely in its upper branch, so
  there is no discontinuity under the correct formula.
- **Verdict:** **supported** (`provisional`, hand-verified against primary source)
- **Status:** closed. The V2 "resolve the bimodality" premise is invalid.

## H-V2-RESOLVES-BIMODALITY

**Statement:** V2 smoother-R candidates resolve a real V1 bimodality.

- **Related RQ:** RQ1
- **Evidence:** the premise is invalid (see H-BIMODALITY-ARTIFACT). There was
  nothing real to resolve.
- **Verdict:** **rejected** (premise does not hold)
- **Status:** closed. Do not present V2 to the mentor as fixing a real V1
  problem.

## H-RF-FAMILIES

**Statement:** The six literature R-factor methods split into two mutually
incompatible families ~6× apart, and the correct family must be determined
before any USLE A absolute value can be trusted.

- **Related RQ:** RQ1
- **Evidence:** HIGH family (Arnoldus-family 2329 / RF-F 3719 / RF-P 1380 /
  Elwell-Stocking-1976 Zimbabwe-native ~2000) all agree, including the
  Zimbabwe-native relation. LOW family (Hurni 320 / Epworth 243) agree with
  each other. The "measured Epworth 329" is circular (computed with the
  low-family equation).
- **Verdict:** **deferred** (families identified, but which is correct is no
  longer on the critical path — see D-RFACTOR-QUARANTINE)
- **Status:** deferred as of 2026-07-06. Reopened only if the mentor requires a
  quantitative USLE A (ton/ha/yr) or rejects the K×LS×C sediment criterion.
- **Claim level:** `deferred` (was `sensitivity_scenario`)

## H-ERA5-LOWER-BOUND

**Statement:** The empirical ERA5 hourly EI30 R (~358-506) sits in/near the LOW
family and ~3-7× below the HIGH family, supporting the lower range as an
independent lower-bound check.

- **Related RQ:** RQ1
- **Evidence:** standard EI30 algorithm on ERA5 hourly (2018-2023, 7+45 V1
  points, open-meteo, no auth); Wischmeier-Smith and Brown-Foster KE forms;
  spatial-mean 358-506; 45-point rasterized R mean = 507 matches 7-point 506.
- **Verdict:** **supported** as a lower bound only
- **Caveat:** ERA5 hourly ≠ true 30-min breakpoint rainfall, so this is a
  lower bound, not a final R validation.
- **Status:** active. Supports asking the mentor for an R-method decision.
- **Claim level:** `provisional` (lower-bound supporting evidence)

## H-US-FORMULAS-TRANSFER

**Statement:** US-calibrated R-factor formulas do not transfer to semi-arid
Zimbabwe.

- **Related RQ:** RQ1
- **Evidence:** **rejected** once the Zimbabwe-native Elwell/Stocking (1976)
  relation is included — it lands in the same range as the HIGH family
  despite being calibrated on Rhodesian rainfall independent of the US work.
- **Verdict:** **rejected**
- **Status:** closed. The "US formulas don't transfer" framing was wrong; the
  real open question is the family-level R definition/units (H-RF-FAMILIES).

## H-AHP-SLIDE-TRANSFERS

**Statement:** The 2026-06-16 mentor-slide AHP matrix is internally consistent
and structurally aligns with the deliverable pipeline, so it can serve as a
sensitivity-scenario weight set.

- **Related RQ:** RQ2
- **Evidence:** eigenvector weights Flood 0.490 / Sediment 0.226 /
  Environmental 0.141 / Land use 0.087 / Socioeconomic 0.056; λmax 5.099;
  CI 0.0247; CR 0.022 (below 0.10 threshold). PIM formula matches the
  pipeline's already-implemented overlay.
- **Verdict:** **supported** as a sensitivity scenario
- **Caveat:** the slide labels it "example", so it is `sensitivity_scenario`,
  not final authorised weights. Promotion to `final_claim` happens only if the
  mentor explicitly adopts the matrix after seeing results
  (IFPM-D04).
- **Status:** active.
- **Claim level:** `sensitivity_scenario`

## H-HOTSPOT-R-INVARIANT

**Statement:** The LS×C hotspot pattern is independent of the rainfall-
erosivity factor R — it is governed by LS×C, not by R spatial variation, so it
survives any choice of R-factor.

- **Related RQ:** RQ1, RQ9
- **Evidence:** hotspot survival 84-87% under all R candidates including the
  bimodal baseline; Spearman agreement 0.99 under smoother R vs 0.88 under
  bimodal R. USLE A using empirical R=507: A_zonal mean 0.621 vs A_spatial
  mean 0.619 (<1% agreement) confirms hotspot pattern is governed by LS×C.
- **Caveat:** the survival metric is structurally biased toward high values
  (LS spans ~4 orders of magnitude vs R's ~3×), so it has low discriminating
  power — read as a weak confirmatory signal, not a candidate-quality ranking.
- **Verdict:** **supported** as a structure test only
- **Status:** closed as a structure-test claim; must not be read as a
  statement about R correctness. **This hypothesis is the justification for
  D-RFACTOR-QUARANTINE (2026-07-06)**: since hotspots are independent of the
  rainfall-erosivity factor R, the PIM priority map does not require an
  R-method choice, and R-factor is
  removed from the critical path.
- **Claim level:** `sensitivity_scenario`

## H-PE1-SYMMETRIC

**Statement:** PE1 is methodologically symmetric to V1 — same 5/6-criteria
structure, same slide-matrix scenario, comparable hotspot-stability output —
so the two prototypes can be structurally compared with identical weighting.

- **Related RQ:** RQ10
- **Evidence:** PE1 5-criteria stack (flood, erosion, land cover, mining,
  exposure) reaches full 6-criteria symmetry with the +rainfall criterion;
  stable top-20% hotspot 299.57 km² (V1 v0.3 ref 431.907 km²); PE1 mining
  upgraded to official INGEMMET point evidence (strictly stronger than V1).
- **Verdict:** **supported** at `engineering_pilot` level
- **Caveat:** PE1 is not research-selected; physical regimes differ (arid
  Andean Pacific slope vs semi-humid savanna). Final harmonised comparison
  claim blocked (IFPM-D03).
- **Status:** active.
- **Claim level:** `engineering_pilot`

## H-MINING-OSM-INDICATOR

**Statement:** OSM quarry/industrial polygons are a mining activity indicator,
not official ASM truth.

- **Related RQ:** RQ8
- **Evidence:** only 2 quarry/industrial polygons in V1+5km vs 32 in PE1+5km
  and 11 official INGEMMET ASM points in PE1. Zimbabwe has no public ASM
  cadastre.
- **Verdict:** **supported** as an indicator; weak as truth
- **Status:** active. A-005 / A-013. Replacement waits on the mentor's
  2026-07-18 conference ask.
- **Claim level:** `diagnostic_only`

## H-EXPOSURE-ROAD-INDICATOR

**Statement:** Road/access proximity is an exposure/access indicator, not
observed socioeconomic vulnerability.

- **Related RQ:** RQ7, RQ8
- **Evidence:** V1 hotspot-exposure diagnostic shows weak co-location of
  stable hotspots with exposure proxies; hotspots reflect natural-pressure
  overlap, not observed exposure.
- **Verdict:** **supported** as an indicator
- **Status:** active. A-006 / A-011. Needs observed flood-impact data to
  upgrade.
- **Claim level:** `diagnostic_only`

## H-RAINFALL-COARSE-TO-GRID

**Statement:** A 0.05° CHIRPS rainy-season mean bilinear-resampled to a 30 m
reference grid is a usable `sensitivity_scenario` rainfall criterion, provided
its effective resolution (~5 km) is documented and it is never claimed as
native 30 m rainfall.

- **Related RQ:** RQ1 (rainfall sub-question)
- **Evidence:** built for both V1 (A-010) and PE1 (A-012); enters priority
  scenarios with explicit coarse-to-grid governance.
- **Verdict:** **supported** as sensitivity scenario
- **Caveat:** effective resolution ~5 km; never pixel-level 30 m rainfall
  evidence or final flood-risk claim.
- **Status:** active.
- **Claim level:** `sensitivity_scenario`

## Lineage

Absorbs hypothesis-style content from:
- `rfactor_investigation_consolidated.md` §1-5 (H-BIMODALITY-ARTIFACT,
  H-V2-RESOLVES-BIMODALITY, H-RF-FAMILIES, H-ERA5-LOWER-BOUND, H-US-FORMULAS-TRANSFER,
  H-HOTSPOT-R-INVARIANT)
- `task_progress_board.md` IFPM-079/080/081/082/094/095 (R-factor + Peru symmetry)
- `assumptions_log.md` A-005/A-006/A-010/A-011/A-012/A-013 (indicator and
  rainfall-coarse-to-grid statuses)
- `mentor_methodology_slide_interpretation_2026-06-16.md` (H-AHP-SLIDE-TRANSFERS)
