# Research Overview

Status: active. Authoritative project description and scope.

## Research area

IFPM is an exploratory **comparative flood-risk modelling workspace** for two
semi-arid, mining-influenced mountain catchments:

- **Upper Mzingwane Catchment, Zimbabwe** (primary)
- **Arequipa Region, Peru** — mainly the Vitor-La Joya-Santa Rita de Siguas
  catchment west of Arequipa city (provisional comparison catchment)

The method is **AHP-MCDA weighted-overlay prioritization**, not hydrodynamic
inundation modelling. Outputs are susceptibility / prioritization products.

## Background and motivation

The mentor's 2026-06-16 methodology slide (Version B, see `DECISION_LOG.md`
D-VERSION-B) defines the Priority Intervention Map index:

`PIM = wF(FH) + wS(SR) + wL(LU) + wE(ES) + wSE(SV)`

with five scored criteria: Flood (FH), Sediment (SR), Land Use / ASM (LU),
Environmental (ES), Socioeconomic (SV). A pairwise matrix was supplied (CR 0.022,
consistent) but labelled "example" — recorded as `sensitivity_scenario`, not
final weights.

Motivation: identify and prioritize flood-and-mining-influenced areas for
intervention in two comparable catchments, using public data and a defensible
MCDA scaffold that the mentor can later authorize for thesis-level claims.

## Research scope

In scope (Version B):

- Five AHP main criteria; rainfall is included only as a Flood-side sensitivity
  implementation layer, not as a sixth AHP main criterion.
- Bilateral Zimbabwe-Peru prototype comparison (established requirement from the
  dataset inventory / research review, 2026-06-02).
- AHP-MCDA weighted overlay producing a priority intervention map.
- Sensitivity analysis over weights.
- Data-request preparation and evidence hardening for the weakest criteria.

Not required unless the mentor re-requests (Version A legacy, de-scoped):

- Citizen-science input module — dropped from Version B. Do not build it.
- Stakeholder feedback iteration loop — dropped from Version B. Do not build it.
- Post-mining opportunities as a full third module — reduced in Version B to an
  unconfirmed single layer (Rehabilitation Potential, see IFPM-D05).

Avoid unless explicitly re-scoped:

- Full hydrodynamic modelling.
- Broad RUSLE / R-factor rework beyond the named experiment.
- Full AHP expert-survey design.
- WebGIS / dashboard work.
- Long literature-review writing.

## Workspace split

The workspace has a clean split between private context and deliverable code:

- **Root repository** — private context and document repository. All files in
  `context/` are `INTERNAL_CONTEXT`.
- **`ifpm-flood-pipeline/`** — independent deliverable code repository with a
  minimal synthetic-tested pipeline. Real-data use remains gated.

The deliverable pipeline must not depend on `../context`, `../data`, or
`../outputs`. Public release packages come from `ifpm-flood-pipeline/` only.

## Current status (2026-07-05)

- [x] Idea exploration and project framing
- [x] Minimal AHP-overlay pipeline built and synthetic-tested
- [x] Boundary discovery (Zimbabwe V1 + Peru PE1 southern comparison catchment)
- [x] Terrain chain end-to-end on both sites (SRTM DEM, slope, hydrology, LS)
- [x] USLE factor chain (K, LS, C) verified; R-factor quarantined out of critical path
- [x] Five-main-criterion / implementation-layer prototype priority maps on both sites
- [x] July 18 mentor/boss comparison pack generated
- [ ] Sediment criterion on K×LS×C shown to mentor (R-factor quarantined; default taken)
- [ ] AHP slide-matrix sensitivity-scenario priority maps shown to mentor (default taken)
- [ ] Rehabilitation Potential: default not built (not in PIM formula); revisit if a use appears
- [ ] Final boundary acceptance (V1 = Upper Mzingwane, ~3689 km², accepted with waiver for prototype)
- [ ] Harmonised Zimbabwe-Peru comparison claim
- [ ] Validation / final flood-risk claim

Most current outputs are `diagnostic_only`, `provisional`, or
`sensitivity_scenario`. No output is `final_claim`.

## Operating mode (2026-07-06)

This project runs on **autonomous default decisions**, not on questions to the
mentor. The HiWi makes the methodological call with a documented default, builds
the artifact, labels it with the appropriate claim level, and shows the result.
If the mentor wants something different, he says so when he sees the artifact.
Open questions in `RESEARCH_QUESTIONS.md` are recorded as defaults-taken or
next-experiment prompts, not as gates that block forward progress. The project
does not maintain a queue of "questions to ask the mentor".

## Current evidence gaps (these are realities to label, not problems to solve by asking)

1. **AHP weights** — the slide matrix (CR 0.022) is used as a
   `sensitivity_scenario` input; multiple weight scenarios are run and hotspot
   stability is reported. Default: no single weight set is called final.
2. **Mining/ASM evidence (Zimbabwe)** — only OSM quarry/industrial indicator;
   official ASM data does not exist publicly and the mentor may be able to ask
   Zimbabwe contacts. Default: label as indicator, keep building.
3. **Socioeconomic exposure evidence** — only road/access proximity; no observed
   flood-impact / damaged-infrastructure / affected-settlement data. Default:
   label as access indicator, keep building.
4. **Peru boundary** — PE1 is HydroBASINS L7 `6070641200`, a provisional
   southern Peru comparison catchment in Arequipa Region, mainly the
   Vitor-La Joya-Santa Rita de Siguas area west of Arequipa city. It is chosen
   by a selection rule, not a final research-selected site. Default: keep PE1,
   do not extend further.
5. **Validation data** — effectively zero for both sites. Default: outputs stay
   at priority/susceptibility level, never labelled as validated risk.
6. **Sediment criterion** — uses K×LS×C erosion-source structure (R-factor
   quarantined out of the critical path, see `DECISION_LOG.md`
   D-RFACTOR-QUARANTINE).

## R-factor status (no longer a critical-path uncertainty)

R-factor was previously the highest-priority open question. As of 2026-07-06 it
is **quarantined out of the critical path** (see `DECISION_LOG.md`
D-RFACTOR-QUARANTINE):

- The sediment criterion is served by the K×LS×C erosion-source structure layer
  (`a_structure_K_LS_C_30m.tif`), which is independent of the rainfall-
  erosivity factor R and is already built and grid-compatible.
- Priority hotspots are independent of the rainfall-erosivity factor R
  (H-HOTSPOT-R-INVARIANT, supported), so the PIM output does not depend on the
  R-method choice.
- USLE A absolute values (ton/ha/yr) are **no longer required** for the
  prototype priority map. They become a thesis-stage optional refinement,
  reopened only if a quantitative soil-loss rate is needed.
- The R-factor investigation history and ERA5 lower-bound evidence stay in
  `RESULTS.md` §R-factor as a deferred-record, not an active blocker.

## Optional conventions noted but not adopted as policy

The research-governance framework this folder follows suggests a weekly cadence
(Monday questions, Tue-Thu experiments, Friday results, Sunday cleanup) and an
explicit evidence-type enumeration (quantitative, qualitative, logs, comparison,
human evaluation, failure cases, ablation). These are noted as useful discipline
but are not adopted as binding IFPM policy — IFPM's `EXPERIMENT_WORKER` mode
already requires concrete artifacts per non-trivial task, which is stricter.

## Lineage

Absorbs content from:
- root `README.md` (project description and workspace split)
- `project_objective_calibration_2026-07-02.md` (Version A vs B decision)
- `task_progress_board.md` §Current Position (status narrative)
- `AGENTS.md` §Active Prototype Scope (scope limits)
- `execution_status_policy.md` (status-level language)
