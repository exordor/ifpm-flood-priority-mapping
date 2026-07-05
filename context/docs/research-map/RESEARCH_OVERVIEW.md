# Research Overview

Status: active. Authoritative project description and scope.

## Research area

IFPM is an exploratory **comparative flood-risk modelling workspace** for two
semi-arid, mining-influenced mountain catchments:

- **Upper Mzingwane Catchment, Zimbabwe** (primary)
- **Arequipa-Moquegua-Tacna Region, Peru** (parallel engineering pilot)

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

- Five AHP-scored criteria plus the rainfall sensitivity criterion already added.
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
- [x] Boundary discovery (Zimbabwe V1 + Peru PE1 engineering pilot)
- [x] Terrain chain end-to-end on both sites (SRTM DEM, slope, hydrology, LS)
- [x] USLE factor chain (K, LS, C) verified; R-factor under investigation
- [x] Five-criteria + rainfall prototype priority maps on both sites
- [x] July 18 mentor/boss comparison pack generated
- [ ] Mentor confirmation on R-factor method (highest-priority open question)
- [ ] Mentor confirmation on AHP matrix authorisation
- [ ] Mentor confirmation on Rehabilitation Potential role
- [ ] Final boundary acceptance (V1 is `accepted_with_waiver_for_controlled_prototype`)
- [ ] Harmonised Zimbabwe-Peru comparison claim
- [ ] Validation / final flood-risk claim

Most current outputs are `diagnostic_only`, `provisional`, `sensitivity_scenario`,
or `engineering_pilot`. No output is `final_claim`.

## Biggest current uncertainties

1. **R-factor method for semi-arid Zimbabwe** — two incompatible literature
   families ~6× apart; ERA5 empirical lower-bound sits in the lower range; needs
   mentor ruling or primary EI30 data. See `RESULTS.md` §R-factor.
2. **AHP weight authorisation** — the slide matrix is `sensitivity_scenario`
   only. See IFPM-D04 in `RESEARCH_QUESTIONS.md`.
3. **Mining/ASM evidence (Zimbabwe)** — only OSM quarry/industrial proxy;
   official ASM data waits on the mentor's 2026-07-18 conference ask. See A-013.
4. **Socioeconomic exposure evidence** — only road/access proximity; no observed
   flood-impact / damaged-infrastructure / affected-settlement data.
5. **Peru boundary** — PE1 is an engineering pilot chosen by a selection rule,
   not a research-selected site. See IFPM-D02.
6. **Validation data** — effectively zero for both sites. See IFPM-D03.

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
