# Results

Status: active. Per-experiment observation / evidence / interpretation, with
IFPM claim level. Confidence uses the IFPM `claim_level` ladder defined in
`REPRODUCIBILITY.md` (diagnostic_only → provisional → sensitivity_scenario →
mentor_review_ready → final_claim), not the framework's low/medium/high — IFPM's
ladder is stricter.

## R-factor investigation (RQ1)

### Observation

Six literature R-factor methods run on identical V1 CHIRPS inputs split into two
incompatible families ~6× apart. The V1 bimodality (29 low / 103 high cells) was
triggered by a wrong formula application.

### Evidence

| method | R zonal mean | family |
|---|---:|---|
| A: Arnoldus-family / Nakil-Khire | 2329 | HIGH |
| B: RF F-based correct (Eq 14) | 3719 | HIGH |
| C: RF P-based correct (Eq 11) | 1380 | HIGH |
| Elwell/Stocking 1976 (Zimbabwe-native ref) | ~2000 | HIGH |
| empirical ERA5 (I30 est, 7+45 points) | ~506 | (lower range) |
| E: Hurni 1985 | 320 | LOW |
| F: Epworth/Merritt | 243 | LOW |
| D: OLD V1 (WRONG) | 408 | (invalid) |

The "measured Epworth 329" is circular (computed with the LOW-family equation).
The only independent check (ERA5 hourly EI30) sits in/near the LOW family and
~3-7× below the HIGH family.

### Interpretation

- The V1 bimodality is an artifact of applying P-based Renard-Freimund
  coefficients to MFI with an invented break at MFI=80 (H-BIMODALITY-ARTIFACT,
  supported).
- The "V2 resolves the bimodality" framing is invalid (H-V2-RESOLVES-BIMODALITY,
  rejected).
- The two R-families are real and unresolved (H-RF-FAMILIES, unresolved).
- The "US formulas don't transfer" hypothesis is rejected — the Zimbabwe-native
  Elwell relation lands in the HIGH family (H-US-FORMULAS-TRANSFER, rejected).
- ERA5 supports the lower range as an independent lower-bound check
  (H-ERA5-LOWER-BOUND, supported as lower bound).

### Claim level: `sensitivity_scenario`. All V1/V2 R and USLE A absolute values
deprecated.

## V1 terrain and USLE factor chain

### Observation

Five USLE factors derived on the V1 reference grid; only the R-factor is blocked.

### Evidence (verified correct, IFPM-080/085)

| factor | value / formula | source | status |
|---|---|---|---|
| K-factor US→SI | `K_SI = K_US * 0.1317` | Foster et al. 1981 | verified |
| K-factor V1 (0-5 cm, US) | mean 0.1695, range [0.082, 0.251] | SoilGrids 250m | verified; native 250 m, not resampled |
| LS constants | 22.13, 0.0896 | Moore & Nieber 1989 | verified |
| LS exponents | 0.4, 1.2 (lower bound of GISus-M m∈[0.4-0.56], n∈[1.2-1.3]) | Oliveira et al. 2015 | verified |
| LS hillslope V1 | mean 1.563, p95 5.511 | local | diagnostic_only |
| C-factor V1 | area-weighted mean 0.0429 | ESA WorldCover lookup | verified |
| R-factor V1 | bimodal, artifact | deprecated | deprecated |
| USLE A V1 | mean 0.50 t/ha/yr | deprecated (R-dependent) | deprecated |

`a_structure_K_LS_C_30m.tif` (K×LS×C, no rainfall-erosivity factor) is the
verified erosion-source-structure base for any future `A = structure × R`
re-derivation. **Safe to keep.**

### Interpretation

K, LS, C are correct. The hotspot pattern is governed by LS×C and is
independent of the rainfall-erosivity factor R (H-HOTSPOT-R-INVARIANT, supported
as a structure test). Re-deriving
A waits on the R-method decision (RQ1).

### Claim level: factors `diagnostic_only`; `a_structure` `provisional`; A
`deprecated`.

## V1 prototype priority (criteria_stack_v0_2 / priority_scenarios_v0_2)

### Observation

Five honest-label criteria built on the V1 reference grid; tested under four
weight scenarios. v0.3 adds the rainfall criterion (CHIRPS coarse-to-grid).

### Evidence

- Criteria: flood_conditioning_factors, soil_erosion_factors, land_cover_pressure,
  mining_pressure, exposure_indicators (v0.1 used the legacy `socioeconomic_exposure`
  name; renamed under D-CRITERIA-V0-2). v0.3 adds rainfall_climatology.
- Top-20% stable hotspot across all four scenarios: **436.907 km²** (v0.1) /
  **431.907 km²** (v0.2).
- Top-20% hotspot in at least one scenario: 1066.03 km².
- Mean priority standard deviation across scenarios: 0.04697.
- All criteria and checked priority rasters passed the V1 raster grid gate.
- Methodology-slide candidate matrix: CR 0.022046 (consistent), still
  `sensitivity_scenario`.

### Interpretation

The project now has a defensible autonomous baseline for asking whether hotspot
patterns survive weight changes. It does not rely on Voi rainfall and does not
revive deprecated R/A products.

### Claim level: `provisional` (criteria stack) / `sensitivity_scenario` (priority).

## PE1 (Peru) prototype

### Observation

PE1 reaches full 6-criteria symmetry with V1 v0.3.

### Evidence

- PE1 boundary: HYBAS 6070641200, 2745.4 km² (ratio 0.74 vs V1), pacific-slope,
  ~17 km west of Arequipa city.
- PE1 DEM: EPSG:32718, 30 m, elevation 144.9-3188.3 m, valid fraction 0.4506.
- LS hillslope mean 3.70 (vs V1 1.563).
- K (0-1815 US, native 250m); C mean 0.6096 (bare/sparse dominant).
- USLE A (LOW R=238.6) mean 8.74 t/ha/yr (vs V1 0.50).
- 6 criteria: flood, erosion, land cover, mining (INGEMMET 11 official ASM
  points), exposure (OSM 6210 roads), rainfall (CHIRPS latam Dec-Mar 37.6-292.9
  mm/season, mean ~78).
- Stable top-20% hotspot across 3 scenarios: **299.57 km²**.

### Interpretation

PE1 is methodologically symmetric to V1 v0.3 (H-PE1-SYMMETRIC, supported at
`engineering_pilot`). Physical regimes differ fundamentally: arid Andean
Pacific slope (C=0.61, bare; soil loss 8.74) vs semi-humid savanna (C=0.04,
shrub/grass; soil loss 0.50). This is a real defensible contrast, not noise.

### Claim level: `engineering_pilot` / `sensitivity_scenario`. Final harmonised
comparison claim blocked (IFPM-D03).

## Mining evidence

### Observation

Zimbabwe mining evidence is OSM-only and weak; Peru mining is upgraded to
official INGEMMET point evidence.

### Evidence

- V1: 2 quarry/industrial polygons in V1+5km (OSM proxy only).
- PE1: 32 quarry/industrial polygons (OSM) upgraded to 11 official INGEMMET
  Pequeña Minería ASM points (ArcGIS REST, no login).
- PE1 mining upgrade shifted stable top-20% hotspot from 368 km² (OSM) to
  **307.356 km²** (INGEMMET) — official ASM locations produce a more precise
  pattern.

### Interpretation

PE1's mining criterion is `provisional` official-source evidence; V1's is
`diagnostic_only` indicator only. This is the one criterion where Peru is
strictly better evidenced than Zimbabwe. Zimbabwe ASM data waits on the mentor's
2026-07-18 conference ask (A-013).

### Claim level: V1 `diagnostic_only` / PE1 `provisional`.

## Exposure diagnostic

### Observation

V1 stable hotspots show weak co-location with exposure proxies.

### Evidence

`hotspot_exposure_diagnostic_v0_3` measures spatial co-location; weak co-location
means hotspots reflect natural-pressure overlap, not observed exposure.

### Interpretation

This does NOT validate hotspots as flood risk; it supports the data-request
argument for real exposure / flood-observation data rather than claiming current
hotspots are validated (A-011).

### Claim level: `diagnostic_only`.

## Rainfall comparison (CHIRPS V1)

### Observation

561 scoped CHIRPS inputs processed for the V1 catchment; multiple temporal
windows and timesteps compared.

### Evidence

- All readable at EPSG:4326, ~0.05°.
- V1 recent annual and rainy-season anomaly: both ~17.5%.
- Pentad peak has a much different spatial pattern from long-term annual
  rainfall.

### Interpretation

Rainfall can serve as `sensitivity_scenario` coarse-to-grid criterion (A-010,
H-RAINFALL-COARSE-TO-GRID). Final rainfall criterion selection and overlay role
remain mentor-gated (RQ1).

### Claim level: `sensitivity_scenario`.

## Deprecated outputs (do not use)

| product | reason | marker |
|---|---|---|
| All V1/V2 R-factor rasters | wrong coefficients + wrong break; bimodality artifact | `outputs/v1_usle_soil_loss/DEPRECATED_DUE_TO_R_FACTOR_ERROR.md` |
| All USLE A rasters derived from them | R-dependent | same |
| V2 comparison board and caption | repeats invalid "V2 resolves bimodality" framing | removed 2026-07-01 |

Safe to keep: `a_structure_K_LS_C_30m.tif`; all LS, C, K, hydrology, terrain
preprocessing, and CHIRPS rainfall-comparison products; empirical ERA5 R
diagnostics; hotspot-survival structure test (with caveats).

## Send decisions

Sendable (with caption wording): Figure 1 (R-method comparison) and Figure 2
(ERA5 lower-bound). Source: `context/docs/mentor-explanation/Mentor_RFactor_Figure_Send_Packet_2026-06-19.md`.

Blocked: Figure 3 (V1/V2 comparison board); any soil-loss A magnitude as a final
result; any flood-risk / sediment-risk / intervention-priority claim.

Required wording corrections:
- "Corrected Arnoldus" → "Arnoldus-family / Nakil-Khire MFI law"
- "high formulas ~4× too high" → "high-family formulas much larger than ERA5 lower-bound"
- "ERA5 proves the low family" → "ERA5 supports the lower range as independent lower-bound check"

## Lineage

Absorbs content from:
- `task_progress_board.md` per-IFPM-NNN "Key result" blocks
- `rfactor_investigation_consolidated.md` §1-8 (full R-factor synthesis)
- `boundary_v1_criteria_stack_v0_2_2026-06-29.md` (v0.2 results)
- IFPM-087/093/094/095/096 result blocks
