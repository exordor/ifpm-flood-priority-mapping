# P2 Risk R2.4 Modelling Unit Decision Package

Date: 2026-06-15

Status: internal decision package for IFPM-D01 (Modelling Unit). This document does not authorize
any download, AHP overlay, flood-risk interpretation, or intervention-priority interpretation. It
records the three modelling-unit branches, their trade-offs, a recommendation tied to current
evidence, and the IFPM-D01 closure criteria.

## Risk Statement

R2.4 (P2): the modelling unit is not selected (IFPM-D01 blocked).

The real-data execution preflight gate requires a modelling-unit branch to be chosen before
terrain and rainfall are combined. The three branches defined in
`context/docs/research-map/REPRODUCIBILITY.md` §3 IFPM-D01 are:

1. Terrain-only raster screening with CHIRPS reported as context or a separate summary.
2. Sub-basin aggregation with terrain and CHIRPS summarized to the same accepted units.
3. Mixed product with terrain rasters and rainfall tables reported separately.

The blocker matters because it controls how every criterion is normalized, aggregated, and
compared. It also controls whether CHIRPS (~0.05 degree, about 5 km) can ever enter the same
score as the V1 30 m terrain grid without producing false precision.

## Why This Is A Decision, Not An Engineering Task

The deliverable pipeline already supports both same-grid raster overlay and zonal/tabular
scoring (IFPM-060 closed Step S5 engineering readiness, including the `zonal-score` CLI). So the
engineering is ready for any of the three branches. What is missing is a domain decision on which
branch the V1 prototype should use, because that decision determines:

- whether rainfall enters the scored criteria or stays as context;
- whether outputs are rasters, sub-basin tables, or both;
- how multi-resolution evidence (30 m terrain, 0.05 degree rainfall, 10 m WorldCover, 250 m
  SoilGrids if added) is reconciled;
- what the deliverable's effective spatial resolution claim is.

The HiWi should not make this call alone; it is a mentor/domain decision (IFPM-D01).

## Trade-Off Matrix

| Branch | What enters the score | Rainfall role | Output form | Pros | Cons | Dependency |
|---|---|---|---|---|---|---|
| 1. Terrain-only raster screening | 30 m terrain-derived rasters (slope, eventual flow accum / TWI / drainage distance) | Native 0.05 degree diagnostics and V1 zonal summaries, NOT in the score | 30 m raster priority classes | Matches existing pipeline and V1 DEM; no scale mixing; no CHIRPS-30m trap; fastest to a first interpretable run | Rainfall does not drive priority; misses rainfall-driven hazard differentiation | V1 DEM ready; needs IFPM-D01 selection only |
| 2. Sub-basin aggregation | Per-unit summaries of every criterion (terrain stats, CHIRPS stats, land-use fractions, population sums) | Aggregated to the same units, enters the score | Sub-basin/tabular priority + optional zone-coloured map | Coherent scale for CHIRPS + terrain; honest handling of multi-resolution evidence; matches how flood/sediment prioritization is usually reported for intervention planning | Loses intra-basin spatial detail; depends on accepted boundary AND accepted sub-basin unit layer; more aggregation-rule decisions | Needs accepted final boundary (IFPM-D06), accepted sub-basin layer (HydroBASINS level), and chosen rainfall criterion (Step S1) |
| 3. Mixed | 30 m terrain rasters scored; rainfall reported as a separate parallel summary | Separate rainfall table, not in the terrain score | Two parallel outputs | Safest when scale mismatch is unresolved; no false precision | Two outputs harder to communicate; no single priority map; rainfall effectively context | Needs IFPM-D06 + Step S1 rainfall criterion |

## CHIRPS Scale Mismatch (The Core Constraint)

CHIRPS native resolution is about 0.05 degree (roughly 5.5 km at this latitude). The V1 terrain
grid is 30 m. The ratio is about 180x per side, or about 34,000x by area. Resampling CHIRPS to
30 m would fabricate about 34,000 cells of identical value per real CHIRPS cell, implying false
spatial detail that does not exist.

The V1 terrain reference grid rule (`context/docs/data-management/v1_terrain_reference_grid_rule.md`)
and AGENTS.md explicitly forbid treating CHIRPS as 30 m pixel-level evidence. This rule is
binding for any branch chosen here. The modelling-unit decision cannot override it; it can only
choose how rainfall is legitimately included (context, zonal summary, or separate table).

## Recommendation

**Branch 1 (terrain-only raster screening) for the first V1 prototype.**

Rationale tied to current evidence:

- The V1 DEM and slope are ready and grid-gated (IFPM-052, IFPM-054).
- The pipeline's raster overlay path is the most mature (IFPM-004, IFPM-024, Step S5).
- CHIRPS sensitivity is already documented as native-grid/V1-summary context
  (`chirps_v1_rainfall_comparison_2026-06-13.md`), which fits Branch 1 exactly.
- It avoids the CHIRPS-30m trap with no workaround needed.
- It produces the fastest defensible first interpretable run, as long as the P1 blockers
  (validation R1.1, mining R1.2, AHP weights R1.3) are also addressed.

**Branch 2 (sub-basin aggregation) as the natural upgrade** once the final boundary is accepted
(IFPM-D06), a sub-basin unit layer is chosen, and a rainfall criterion is selected (Step S1). The
`zonal-score` CLI path is already implemented for this.

Branch 3 (mixed) is the fallback if Branch 1 is rejected and Branch 2 prerequisites are not met
in time.

## IFPM-D01 Closure Criteria

To close IFPM-D01, record:

- [ ] selected branch (recommended: Branch 1 for V1);
- [ ] rationale tied to current evidence;
- [ ] explicit statement of whether any pixel-level rainfall overlay is allowed (must be NO under
      the current CHIRPS-30m rule);
- [ ] statement that CHIRPS will not be treated as 30 m information;
- [ ] if Branch 2: the accepted sub-basin unit layer and aggregation rule;
- [ ] if Branch 3: the two output forms and how they will be communicated together.

## Decision Questions For Mentor

1. Is Branch 1 (terrain-only raster screening, rainfall as context) acceptable for the first V1
   prototype?
2. If not, which branch is preferred, and are its prerequisites (final boundary, sub-basin layer,
   rainfall criterion) closeable in time?
3. Is rainfall intended to drive priority in the first prototype, or is context/sensitivity
   enough?
4. If Branch 2 is chosen later, which sub-basin unit layer should be used (HydroBASINS level 7/8,
   Geoportal sub-catchments, or outlet-delineated units)?

## Boundaries And Blockers

- No real-data overlay is authorized by this document.
- Selecting a branch does not close IFPM-D06 (boundary), Step S1 (rainfall criterion), or Step S5
  (engineering readiness for the chosen branch). Branch 2 additionally needs an accepted
  sub-basin layer.
- The CHIRPS-30m rule is binding regardless of branch.

## Cross-References

- Risk overview: `p2_risk_overview_2026-06-15.md`.
- Preflight gate: `context/docs/research-map/REPRODUCIBILITY.md` §3 (IFPM-D01).
- Reference grid rule: `context/docs/data-management/v1_terrain_reference_grid_rule.md`.
- CHIRPS comparison: `chirps_v1_rainfall_comparison_2026-06-13.md`.
- Pipeline zonal path: `ifpm-flood-pipeline/src/ifpm_flood_pipeline/zonal.py`.
- Decision tasks: IFPM-D01 (final modelling unit), IFPM-066 (this package).
