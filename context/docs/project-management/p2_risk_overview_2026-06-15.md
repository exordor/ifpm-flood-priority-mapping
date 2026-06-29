# P2 Risk Overview And Dependency Sequencing

Date: 2026-06-15

Status: internal index and sequencing note for the five P2 (serious) risks identified in the
2026-06-15 project risk analysis. This document does not authorize any download, AHP overlay,
flood-risk interpretation, or intervention-priority interpretation. It links the five P2 decision
packages, records the dependency chain between them, and gives the recommended mentor-question
sequencing.

## Purpose

The 2026-06-15 risk analysis identified five P2 serious risks that affect methodology
completeness. Unlike the P1 risks (which were all decision-blocked and largely unsolvable without
mentor/external input), several P2 risks are engineering-actionable once a documented decision is
made. The dependency chain between them matters: closing them in the wrong order wastes effort.
This overview exists so a reviewer can see the five risks, their packages, their dependencies,
and the recommended order in one place.

## P2 Risk Register

### R2.1 Sediment Risk Layer Entirely Missing

- Risk: zero of five USLE/RUSLE factors (R, K, LS, C, P) are computed; "Sediment Risk Map"
  promised by methodology cannot be produced.
- Decision package: `p2_sediment_risk_decision_package_2026-06-15.md`.
- Preflight scaffolding (public source, NOT authorized):
  - `context/docs/data-management/registry/soilgrids_250m_sediment_candidate.md`
  - `context/docs/data-management/preflight/soilgrids_250m_sediment_candidate.md`
- Dependencies: LS-factor needs R2.2 hydro-conditioning acceptance; multi-resolution
  reconciliation needs R2.4 modelling-unit branch.
- Self-resolvable: R and LS are engineering-actionable from existing data (CHIRPS, DEM) once
  formula/assumption decisions are made; K needs SoilGrids download (public); C is partially
  derivable from existing WorldCover; P is a documented assumption.
- Default fallback: demote Sediment Risk to qualitative/context evidence.

### R2.2 Hydrology Derivatives Incomplete

- Risk: only DEM and slope exist; flow direction, flow accumulation, TWI, drainage density,
  stream order, distance-to-drainage all missing. Two core flood-hazard indicators absent.
- Decision package: `p2_hydrology_derivatives_decision_package_2026-06-15.md`.
- Dependencies: none (this is the upstream assumption-provider for R2.1 LS-factor and for the
  flood-hazard terrain derivatives).
- Self-resolvable: fully engineering-actionable from existing V1 DEM once the hydrological-
  conditioning assumptions A1-A5 (sink fill, flow algorithm, channel threshold, grid/mask,
  boundary handling) are accepted by the mentor. No new download needed.
- Default fallback: keep flood-hazard on slope/elevation only; document flow accumulation and
  drainage distance as future work.

### R2.3 Peru Side Entirely Blank

- Risk: zero Peru data; no Peru boundary; comparative dimension of the project is zero.
- Decision package: `p2_peru_side_decision_package_2026-06-15.md`.
- Dependencies: final Zimbabwe-Peru comparison should not start until criteria hierarchy,
  standardization rules, modelling-unit branch, validation protocol, and thresholds are harmonized.
  Peru data inventory, terrain indicators, and diagnostic readiness checks may run in parallel.
- Self-resolvable: public global sources (SRTM, CHIRPS, WorldCover, etc.) apply to Peru; INGEMMET
  GEOCATMIN is publicly accessible for Peru mining data. Sequencing gate applies to final
  comparison claims, not to Peru readiness diagnostics.
- Default fallback: reframe as single-site Zimbabwe study with Peru as documented future work.

### R2.4 Modelling Unit Undecided (Gate G2)

- Risk: pixel vs sub-basin vs mixed not chosen; controls normalization, aggregation,
  comparability, and how multi-resolution evidence is reconciled.
- Decision package: `p2_modelling_unit_decision_package_2026-06-15.md`.
- Dependencies: none upstream; Branch 2 (sub-basin) downstream needs accepted final boundary
  (R2.5) and accepted sub-basin layer.
- Self-resolvable: decision-only. Engineering ready for all three branches (Gate G7 closed).
- Recommendation: Branch 1 (terrain-only raster screening, rainfall as context) for first V1
  prototype; Branch 2 as natural upgrade once boundary and sub-basin layer accepted.
- Default fallback: Branch 1 by default; Branch 3 (mixed) if Branch 1 rejected.

### R2.5 Final Boundary Not Accepted

- Risk: V1 is waiver-only; literature `~2138 km2` has no reusable geometry; Geoportal
  7321.5 km2; candidates differ by 3.4x; area-dependent reporting unstable.
- Decision package: `p2_boundary_acceptance_decision_package_2026-06-15.md`.
- Dependencies: public-source hunt is exhausted (IFPM-043); remaining levers are human request
  (mentor, ZINWA, authors) or accept V1 / Geoportal.
- Self-resolvable: no further automated search will help; needs mentor escalation.
- Default fallback: promote V1 to accepted with documented discrepancy, or accept Geoportal.

## Dependency Chain And Recommended Sequencing

Unlike P1 (where the three risks were largely independent mentor asks), the P2 risks have a clear
dependency chain. Closing them in this order avoids rework:

```
R2.4 modelling unit  ──┐
                       ├──> R2.1 sediment (needs modelling-unit branch + LS factor)
R2.2 hydrology        ──┤
   assumptions          ├──> R2.3 Peru final comparison (waits for harmonized rules)
                       │
R2.5 boundary         ──┘ (unlocks sub-basin branch R2.4-B2 + area-dependent reporting)
```

Recommended mentor-question order:

1. **R2.4 modelling unit** first (unblocks rainfall role and aggregation approach). Recommend
   Branch 1 acceptance. Lowest cost, highest leverage.
2. **R2.5 boundary** in parallel (mentor escalation; human request, not analysis). Unlocks
   area-dependent reporting and the sub-basin upgrade path.
3. **R2.2 hydrology assumptions** once modelling unit is chosen (unblocks terrain derivatives and
   LS-factor engineering; no new download).
4. **R2.1 sediment** once R2.2 (LS factor) and R2.4 (modelling unit) are closed. SoilGrids
   preflight can be authorized in parallel.
5. **R2.3 Peru final comparison** last, after harmonized rules are locked. Peru data inventory
   and terrain/readiness diagnostics may run earlier as `diagnostic_only`.

## Engineering Track (What Becomes Actionable Without New Downloads)

Once the relevant decisions are accepted, the following engineering work is unblocked using
existing downloaded data only (no new download, no gate violation):

| After accepting | Engineering unblocked | Uses existing |
|---|---|---|
| R2.2 assumptions A1-A5 | V1 flow direction, flow accumulation, drainage network, stream order, TWI, distance-to-drainage | V1 DEM (SRTM) |
| R2.1 R-factor formula | V1 R-factor diagnostics from CHIRPS | CHIRPS v3 inputs |
| R2.1 LS-factor (needs R2.2) | V1 LS-factor raster | V1 DEM |
| R2.1 C-factor mapping | V1 C-factor proxy | ESA WorldCover 2021 |

These would be implemented as `bin/` scripts with root `.venv` local tooling dependencies (e.g.
`richdem`/`pysheds`/`whitebox` for hydrology), never as public pipeline dependencies, matching
the scipy precedent. Outputs stay under `outputs/`, never in `ifpm-flood-pipeline/` or `context/`.

## Consolidated Mentor Asks (P2 Bundle)

Present these after the P1 bundle, in the dependency order above:

1. R2.4-Q1 to Q4: is Branch 1 (terrain-only, rainfall as context) acceptable for the first V1
   prototype?
2. R2.5-Q1 to Q4: do you hold the boundary polygon, or should V1 be promoted to accepted?
3. R2.2-Q1 to Q4: are the hydro-conditioning defaults (fill-to-spill, D8, edge-as-outlet)
   acceptable, and which channel-initiation threshold matches the Mzingwane network?
4. R2.1-Q1 to Q5: which R-factor formula, K-factor source, C-factor mapping, and P-factor
   default? Is SoilGrids 250m acceptable? Is demoting sediment to context acceptable if the
   chain cannot complete?
5. R2.3-Q1 to Q4: is Peru a hard requirement, and on what timeline and boundary option?

## New Tracking Tasks

- IFPM-064: P2 R2.1 sediment risk decision package + SoilGrids scaffolding. Status: decision
  package complete; awaits R-factor formula, K-factor source, C-factor mapping decisions; LS
  factor blocked on R2.2.
- IFPM-065: P2 R2.2 hydrology derivatives decision package (hydro-conditioning assumptions
  A1-A5). Status: assumptions drafted; awaits mentor confirmation; engineering unblocked after
  acceptance.
- IFPM-066: P2 R2.4 modelling-unit decision package (Gate G2). Status: trade-off matrix and
  Branch-1 recommendation complete; awaits mentor selection.
- IFPM-067: P2 R2.3 Peru side decision package. Status: scope and data-holder inventory
  complete; awaits mentor confirmation of comparative requirement and timeline.
- IFPM-068: P2 R2.5 final boundary acceptance mentor escalation. Status: hunt consolidated as
  exhausted; awaits mentor polygon or V1 promotion decision.

## What This Package Does NOT Do

- It does not authorize any real download. SoilGrids preflight is a draft requiring Gate G5
  authorization.
- It does not authorize any hydrology-derivative production. That requires accepted R2.2
  assumptions A1-A5.
- It does not authorize AHP overlay on real data. That remains blocked by Gates G1/G2/G7 and the
  P1 decision gates.
- It does not accept any boundary or start Peru work.
- It does not promote any V1 terrain standardization or CHIRPS summary into overlay.

## Cross-References

- Source risk analysis: 2026-06-15 in-session project risk and data-gap analysis.
- P1 overview (preceding package): `p1_risk_overview_2026-06-15.md`.
- Preflight gate: `real_data_execution_preflight_gate.md`.
- Task board: `task_progress_board.md`.
- Packages: `p2_modelling_unit_decision_package_2026-06-15.md`,
  `p2_hydrology_derivatives_decision_package_2026-06-15.md`,
  `p2_sediment_risk_decision_package_2026-06-15.md`,
  `p2_peru_side_decision_package_2026-06-15.md`,
  `p2_boundary_acceptance_decision_package_2026-06-15.md`.
