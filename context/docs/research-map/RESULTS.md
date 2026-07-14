# Results

Status: active. Per-experiment observation / evidence / interpretation, with
IFPM claim level. Confidence uses the IFPM `claim_level` ladder defined in
`REPRODUCIBILITY.md` (diagnostic_only → provisional → sensitivity_scenario →
mentor_review_ready → final_claim), not the framework's low/medium/high — IFPM's
ladder is stricter.

> **R-factor quarantine notice (2026-07-06):** R-factor is removed from the
> critical path. The active Peru Sediment criterion now combines normalized K,
> LS, and C with local AHP weights and does not calculate USLE A. The older
> K×LS×C structure is diagnostic lineage only. The R-factor section below is kept as
> a deferred technical record, not an active blocker. USLE A absolute values
> (ton/ha/yr) are no longer required for the prototype. See
> `DECISION_LOG.md` D-RFACTOR-QUARANTINE.

> **Peru-first notice (updated 2026-07-13):** after D-PERU-FIRST, PE1 is the active
> mainline working case. Existing Zimbabwe results remain useful as background
> and method-development evidence. Peru input-factor maps, five criterion maps,
> the direct-weight prototype PIM, mining/population overlay, contribution map,
> and SINPAD diagnostic are complete. The next result artifact is the integrated
> Peru briefing board with its data-strength table.

## R-factor investigation (RQ1) — DEFERRED RECORD

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
- The two R-families are real but no longer on the critical path
  (H-RF-FAMILIES, deferred per D-RFACTOR-QUARANTINE).
- The "US formulas don't transfer" hypothesis is rejected — the Zimbabwe-native
  Elwell relation lands in the HIGH family (H-US-FORMULAS-TRANSFER, rejected).
- ERA5 supports the lower range as an independent lower-bound check
  (H-ERA5-LOWER-BOUND, supported as lower bound; kept as deferred record).

### Claim level: `deferred` (was `sensitivity_scenario`). All V1/V2 R and USLE A
absolute values deprecated and no longer required for the prototype.

## V1 terrain and USLE factor chain

### Observation

Five USLE factors derived on the V1 reference grid; R-factor quarantined out of
the critical path (D-RFACTOR-QUARANTINE) — the sediment criterion is served by
the K×LS×C erosion-source structure layer, which is independent of R.

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

K, LS, C are correct. The top-20% erosion-source pattern is governed by LS×C and is
independent of the rainfall-erosivity factor R (H-TOP20-R-INVARIANT, supported
as a structure test). Re-deriving
A waits on the R-method decision (RQ1).

### Claim level: factors `diagnostic_only`; `a_structure` `provisional`; A
`deprecated`.

## V1 prototype priority (criteria_stack_v0_2 / priority_scenarios_v0_2)

### Observation

Five PIM main criteria were built on the V1 reference grid in an archived
secondary Zimbabwe experiment. That experiment compared equal and direct
weights, but it is excluded from the current default pipeline and current
reporting chain. Flood and Land Use / ASM were derived from internal component
rasters, and Environmental was a provisional water/wetland plus protected-area
sensitivity indicator.

### Evidence

- Active PIM criteria: flood_hazard, sediment, landuse_asm, environmental,
  socioeconomic.
- Component rasters: rainfall_climatology, TWI wetness, drainage proximity,
  spatial SoilGrids K, SRTM LS, WorldCover C, land_cover_pressure, mining_pressure,
  environmental_sensitivity, exposure_indicators.
- Area selected in the top 20% across all four scenarios: **436.907 km²** (v0.1) /
  **431.907 km²** (v0.2).
- Current PIM 5-criterion run (`rainfall_exposure_v0_4`): Zimbabwe direct
  weights only; **96.609%** five-criterion common-support coverage and
  **3.391%** remains unscored.
- All criteria and checked priority rasters passed the V1 raster grid gate.
- Archived secondary Zimbabwe direct weights: `FH=0.32`, `SE=0.23`, `LM=0.18`,
  `ES=0.12`, `SV=0.15`. The historical equal-weight comparison is not used in
  the current Peru-first reporting chain. No CR is reported because no
  pairwise matrix was supplied with this direct table.
- Flood subweights are implemented as rainfall 0.35, TWI 0.30, drainage
  proximity 0.35.
- Land Use / ASM subweights are implemented as land-cover pressure 0.40 and
  mining pressure 0.60.
- Environmental is provisional: water/wetland context 0.55 plus protected /
  ecological context 0.45, not ecological valuation.
- Sediment independently combines boundary-standardized spatial K / LS / C at
  0.35 / 0.35 / 0.30. The spatial K layer is grid-compatible for overlay but
  retains a 250 m effective-resolution warning; the result is an erosion-source
  indicator, not measured sediment transport.
- Socioeconomic still uses road/access proximity only; independent
  infrastructure exposure is not available in the current run.

### Interpretation

The project now has a secondary Zimbabwe prototype aligned to the same
five-criterion PIM structure as Peru. It is useful as background and method
development evidence, but it does not override the Peru-first mainline and it
does not revive deprecated R/A products.

### Claim level: `provisional` (criteria stack) / `sensitivity_scenario` (priority).

## PE1 (Peru) prototype

### Observation

PE1 is now the active Peru-first prototype case. It is operationally comparable
with V1 under the mentor five-main-criterion framework, but after D-PERU-FIRST
the immediate interpretation focus is Peru completion rather than bilateral
symmetry.

### Evidence

- PE1 boundary: HYBAS 6070641200, 2745.4 km² (ratio 0.74 vs V1), pacific-slope,
  ~17 km west of Arequipa city.
- PE1 DEM: EPSG:32718, 30 m, elevation 144.9-3188.3 m, valid fraction 0.4506.
- LS hillslope mean 3.70 (vs V1 1.563).
- K (0-5 cm US, native/effective 250 m) mean 0.2084, range 0.100-0.266;
  C mean 0.6096 (bare/sparse dominant).
- USLE A (LOW R=238.6) mean 8.74 t/ha/yr (vs V1 0.50).
- Active PIM criteria: flood_hazard, sediment, landuse_asm, environmental,
  socioeconomic.
- Current main weights: `FH=0.35`, `SE=0.25`, `LM=0.20`, `ES=0.12`,
  `SV=0.08` from the Peru mentor-weight table; this is the only active Peru scenario.
- Component rasters: rainfall_climatology, twi_wetness, drainage_proximity,
  soil_k_factor, ls_factor, c_factor, land_cover_pressure, mining_pressure (INGEMMET
  11 official ASM points), environmental_sensitivity, and exposure_indicators.
  The socioeconomic exposure indicator combines road/access proximity (0.45) with
  infrastructure exposure (0.55); infrastructure exposure is an explicit
  provisional 0.50/0.50 blend of WorldPop population and OSM mapped-building
  exposure.
- The nominal 0.45/0.55 split is implemented. Road/access contributes 94.4%
  of the weighted spatial mean and 66.6% of the marginal weighted SD share;
  infrastructure contributes 5.6% and 33.4%. These covariance-blind diagnostics
  are not effective weights, ranking attribution, or a calibration target.
- Flood subweights are implemented as rainfall 0.40, TWI 0.30, drainage
  proximity 0.30.
- Land Use / ASM subweights are implemented as land-cover pressure 0.35 and
  mining pressure 0.65.
- Environmental is provisional: water/wetland context 0.60 plus SERNANP national
  definitive protected-area layer 0 context 0.40, not ecological valuation.
  Layer 0 was checked; no geometry occurs within PE1 + 5 km, and regional,
  private, or transitional protected-area layers were not queried. The current
  criterion is therefore driven by water/wetland evidence.
- Sediment applies normalized SoilGrids K 0.30, SRTM LS 0.45, and WorldCover C
  0.25. A cell missing any one component remains NoData; neither component nor
  main-criterion weights are renormalized around missing evidence.
- INEI district poverty and OSM health-service remoteness are exported as
  response-capacity context only and are not hidden AHP inputs.
- The direct highest-priority quintile covers **521.356 km²**.
- Scoreable coverage is **95.0998%**, exactly the five-criterion common-support
  domain. **4.9002%** remains unscored: **3.7573%** lacks LS, **1.1326%** lacks
  K, and **0.0103%** lacks other required evidence. These cells are hatched by
  cause on the reporting maps.
- WorldPop accounting is recorded in the checksum-bound
  `outputs/peru_gap_closure_analysis/peru_population_by_pim_class.csv`. WorldPop
  is itself a PIM exposure input, so this is endogenous exposure accounting, not
  validation or an observed affected-population count.
- SINPAD co-location: **12 of 25** hydrometeorological records are scoreable and
  **2 of those 12** fall in the highest-priority quintile. For flood-specific
  records, **1 of 4** is scoreable and **0** is selected. Thirteen records fall
  outside complete support, all at K-factor gaps. This is a point co-location
  diagnostic and not independent validation.
- Criterion-dependence diagnostics show that distinct Sediment C and Land Use
  pressure functions still share WorldCover (`Spearman rho=0.498`). Replacing
  the Land Use / Mining criterion with mining pressure only gives a selected-
  quintile Jaccard of **0.778** against the current PIM.
- The combined Socioeconomic proxy is strongly rank-aligned with road/access
  (`rho=0.970`). Road-only and infrastructure-only alternatives give selected-
  quintile Jaccard values of **0.880** and **0.895**. This diagnoses source
  influence; it does not justify changing the supplied 0.45/0.55 subweights.
- Environmental versus water/wetland context has effectively identical rank
  ordering because SERNANP national definitive layer 0 contributes no nonzero
  local cells. A water-only rescaling alternative gives a selected-quintile
  Jaccard of **0.847**. The current layer is therefore an Environmental context
  proxy, not complete ecological sensitivity valuation.

### Interpretation

PE1 is the best current mainline case because it has the stronger mining
evidence (INGEMMET points) and a coherent five-criterion PIM stack. Physical
regimes differ fundamentally from Zimbabwe: arid Andean Pacific slopes and
bare-ground cover versus semi-humid savanna and shrub/grass cover. That contrast
remains useful background, but the
next result claim should be Peru-only unless a comparison is explicitly needed.
The current Peru reporting map is a prototype prioritisation product under the
direct Peru weights. Flood is a conditioning proxy based partly on rainy-season
climatology, not an event-extreme rainfall product. The map is not validated flood risk
and not a rescue-decision product.

### Claim level: `provisional` / `sensitivity_scenario`. PE1 remains a
provisional working boundary; no validated flood-risk or rescue-decision claim.

## Mining evidence

### Observation

Zimbabwe mining evidence is OSM-only and weak; Peru mining is upgraded to
official INGEMMET point evidence.

### Evidence

- V1: 2 quarry/industrial polygons in V1+5km (OSM indicator only).
- PE1: 32 quarry/industrial polygons (OSM) upgraded to 11 official INGEMMET
  Pequeña Minería ASM points (ArcGIS REST, no login).
- PE1 mining upgrade shifted the area selected in the top 20% under all scenarios from 368 km² (OSM) to
  **307.356 km²** in the earlier three-scenario run; the current Peru direct
  weights select **521.356 km²** in the highest-priority quintile on the strict
  five-criterion common support. Official
  ASM locations produce a more precise mining-pressure pattern than the old OSM
  mining indicator.

### Interpretation

PE1's mining criterion is `provisional` official-source evidence; V1's is
`diagnostic_only` indicator only. This is the one criterion where Peru is
strictly better evidenced than Zimbabwe, and it is the main reason Peru is now
the active mainline case. The governed Peru overlay now shows the INGEMMET
reference locations with the priority classes and distinguishes 2 unique
locations inside the PE1 boundary from 4 nearby locations. These are point
references and model-input context, not mining footprints or validation.

### Claim level: V1 `diagnostic_only` / PE1 `provisional`.

## Exposure diagnostic

### Observation

V1 repeatedly selected top-20% priority areas show weak co-location with
exposure indicators.

### Evidence

`hotspot_exposure_diagnostic_v0_3` measures spatial co-location; weak co-location
means repeatedly selected top-20% priority areas reflect natural-pressure overlap,
not observed exposure.

### Interpretation

This does NOT validate the selected priority areas as flood risk; it supports
the data-request argument for real exposure / flood-observation data rather
than claiming current top-20% priority areas are validated (A-011).

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
diagnostics; top-20% selection-survival structure test (with caveats).

## Send decisions

**R-factor figures (deferred):** Figure 1 (R-method comparison) and Figure 2
(ERA5 lower-bound) are no longer active send items as of D-RFACTOR-QUARANTINE.
They remain available in
`context/docs/mentor-explanation/Mentor_RFactor_Figure_Send_Packet_2026-06-19.md`
if a quantitative USLE A product later requires reopening the R-factor record.

Blocked: Figure 3 (V1/V2 comparison board); any soil-loss A magnitude as a final
result; any flood-risk / sediment-risk / intervention-priority claim.

If R-factor figures are sent later, the required wording corrections still apply:
- "Corrected Arnoldus" → "Arnoldus-family / Nakil-Khire MFI law"
- "high formulas ~4× too high" → "high-family formulas much larger than ERA5 lower-bound"
- "ERA5 proves the low family" → "ERA5 supports the lower range as independent lower-bound check"

## Lineage

Absorbs content from:
- `task_progress_board.md` per-IFPM-NNN "Key result" blocks
- `rfactor_investigation_consolidated.md` §1-8 (full R-factor synthesis)
- `boundary_v1_criteria_stack_v0_2_2026-06-29.md` (v0.2 results)
- IFPM-087/093/094/095/096 result blocks
