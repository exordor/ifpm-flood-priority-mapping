# Research Overview

Status: active. Authoritative project description and scope.

## Research area

IFPM is now an exploratory **Peru-first flood-prioritisation modelling
workspace** for semi-arid, mining-influenced catchments. The active main case
is:

- **Arequipa Region, Peru** — mainly the Vitor-La Joya-Santa Rita de Siguas
  catchment west of Arequipa city (Arequipa Region, provisional Peru main case)

**Upper Mzingwane Catchment, Zimbabwe** remains a secondary / background
comparison case and a reusable method-development baseline, but it is no longer
the current mainline result to finish first.

The method is **AHP-MCDA weighted-overlay prioritization**, not hydrodynamic
inundation modelling. Outputs are susceptibility / prioritization products.

## Background and motivation

The mentor's 2026-06-16 methodology slide (Version B, see `DECISION_LOG.md`
D-VERSION-B) defines the Priority Intervention Map index:

`PIM = wF(FH) + wS(SR) + wL(LU) + wE(ES) + wSE(SV)`

with five scored criteria: Flood (FH), Sediment (SR), Land Use / ASM (LU),
Environmental (ES), Socioeconomic (SV). A pairwise matrix was supplied (CR 0.022,
consistent) but labelled "example" — recorded as `sensitivity_scenario`, not
final weights. After the 2026-07-06 Peru-first discussion, the current Peru
mainline uses newer direct Peru weights: `FH=0.35`, `SE=0.25`, `LM=0.20`,
`ES=0.12`, `SV=0.08`. This is the only active Peru weight set; no equal-weight
comparison is generated or reported.

Motivation: first complete a Peru flood-prioritisation prototype that uses the
stronger Peru data stack, especially the INGEMMET small-mining evidence, then
use Zimbabwe or Voi/Kenya only as secondary comparison cases if the research
story needs them. The end product is a prototype screening map indicating where
further flood-impact assessment and intervention planning should focus,
followed by a mining overlay to test whether mapped mining evidence coincides
with higher-priority screening zones.

## Research scope

In scope (Version B):

- Five AHP/PIM main criteria. Rainfall is included inside Flood hazard, and
  Environmental is a provisional water/wetland plus protected-area sensitivity
  indicator; neither is a sixth top-level criterion.
- Peru-first prototype completion. Zimbabwe-Peru comparison remains useful
  background, but it is no longer the active mainline deliverable.
- AHP-MCDA weighted overlay producing a priority intervention map.
- One direct Peru weight scenario, plus component-dependence and component-
  removal diagnostics; no equal-weight comparison.
- Mining overlay on the Peru priority map, with the mining layer interpreted as
  evidence of mining-pressure coincidence, not as independent flood validation.
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

## Current status (2026-07-13)

- [x] Idea exploration and project framing
- [x] Minimal AHP-overlay pipeline built and synthetic-tested
- [x] Boundary discovery (Zimbabwe V1 + Peru Arequipa Region southern comparison catchment)
- [x] Terrain chain end-to-end on both sites (SRTM DEM, slope, hydrology, LS)
- [x] USLE factor chain (K, LS, C) verified; R-factor quarantined out of critical path
- [x] Five-main-criterion PIM prototype priority maps on both sites
- [x] July 18 mentor/boss comparison pack generated and later moved to the
  historical figure-governance archive after the Peru-first switch
- [x] Peru-first mainline switch recorded after mentor direction to work with
  Peru first until the end
- [x] Current Peru direct mentor weights implemented in `peru_hybas_l7_6070641200_priority_scenarios`;
  obsolete equal-weight rasters removed from the active output directory
- [x] Peru socioeconomic criterion upgraded from road-only to the supplied
  0.45 road/access + 0.55 infrastructure split using WorldPop and OSM mapped
  buildings; INEI poverty and health remoteness exported as diagnostic context
- [x] Peru WorldPop exposure accounting and SINPAD co-location rerun against the refreshed
  mentor PIM with checksum lineage
- [x] Peru authoritative report figure chain generated with one current entry:
  raw inputs → five criteria → direct-weight PIM → mining/population context →
  weighted contribution → SINPAD co-location diagnostic
- [x] Peru Sediment rebuilt as independently normalized K / LS / C subcriteria
  with local weights 0.30 / 0.45 / 0.25; the previously mislocated Peru K
  extraction was corrected and aligned with an explicit 250 m effective-resolution warning
- [x] Land Use pressure separated from the RUSLE C value function
- [x] Peru rainfall normalized within the Arequipa Region boundary; SERNANP national
  definitive protected-area layer 0 checked and recorded
- [x] Five-row criterion data-strength table generated from current outputs
- [x] Criterion-dependence diagnostics generated for shared WorldCover use,
  road-led socioeconomic ordering, and water-led Environmental context
- [x] Secondary Zimbabwe direct weights retained as historical/background work;
  no equal-weight comparison enters either active reporting chain; Zimbabwe
  Sediment now uses independent K / LS / C subcriteria at 0.35 / 0.35 / 0.30
- [ ] Peru-only final prototype briefing board: governed source figures are
  ready; the data-strength table and final one-board composition remain
- [ ] Current K/LS/C Sediment criterion and per-cell evidence-support hatching shown to mentor
- [ ] Peru direct mentor-weight priority map shown with the data-gap table
- [ ] Rehabilitation Potential: default not built (not in PIM formula); revisit if a use appears
- [ ] Final boundary acceptance (V1 = Upper Mzingwane, ~3689 km², accepted with waiver for prototype)
- [ ] Harmonised Zimbabwe-Peru comparison claim (secondary; not current mainline)
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

1. **AHP weights** — current Peru direct weights are implemented as the main
   `sensitivity_scenario` (`FH=0.35`, `SE=0.25`, `LM=0.20`, `ES=0.12`,
   `SV=0.08`). No equal-weight result enters the current reporting chain. The
   secondary Zimbabwe direct table (`FH=0.32`, `SE=0.23`, `LM=0.18`, `ES=0.12`,
   `SV=0.15`) remains background only. The older slide matrix
   (CR 0.022) remains a historical/generic sensitivity record. Default: no
   single weight set is called final.
2. **Mining/ASM evidence (Zimbabwe)** — USGS Africa GIS mineral facilities and
   deposits are used as a proximity-based reference; a verified active ASM
   footprint does not exist publicly and the mentor may be able to ask
   Zimbabwe contacts. Default after the Peru-first switch: do not spend the
   current mainline on Zimbabwe mining repair; keep Zimbabwe as secondary /
   background unless stronger data arrives.
3. **Socioeconomic exposure evidence** — Peru now combines road/access,
   WorldPop population, and OSM mapped-building evidence. The 0.50/0.50
   population/building split inside infrastructure exposure is still an
   implementation placeholder. INEI poverty and OSM health remoteness are
   diagnostic context outside the PIM; Zimbabwe remains road/access-only. Default: label Peru as a
   provisional socioeconomic exposure indicator, not observed vulnerability.
   Roads account for 94.4% of the weighted spatial mean but 66.6% of the
   marginal weighted SD share. These are covariance-blind diagnostics, not
   ranking attribution or replacement weights;
   they do not by themselves justify forcing component means to match.
4. **Peru boundary** — the active working boundary displayed externally as
   **Arequipa Region** is HydroBASINS L7 `6070641200`. It remains a provisional
   southern Peru comparison catchment, mainly covering the
   Vitor-La Joya-Santa Rita de Siguas area west of Arequipa city. It is chosen
   by a selection rule, not a final research-selected site. Default: keep Arequipa Region
   and complete the Peru workflow first; replace only if the mentor names a
   different Peru site.
5. **Validation data** — Peru has 25 in-boundary SINPAD flood-relevant emergency
   records for point comparison. Twelve fall on the complete five-criterion
   support domain and two of those twelve are in the selected quintile. Only one
   of four flood-specific records is scoreable and none is selected. The other
   records mainly coincide with K-factor gaps. This is sparse point co-location
   evidence, not observed flood extent or independent validation. Default:
   outputs stay at priority/susceptibility level, never labelled as validated risk.
6. **Sediment criterion** — Peru now uses an additive AHP combination of
   independently normalized SoilGrids K (0.30), SRTM LS (0.45), and WorldCover
   C (0.25). Sediment coverage is 95.1101%. The final PIM is scoreable over
   95.0998% of Arequipa Region on the five-criterion common-support domain. The remaining
   4.9002% is unscored: 3.7573% lacks LS, 1.1326% lacks K, and 0.0103% lacks
   other required evidence. Support-class rasters and hatching expose those
   cells without imputation or weight renormalization. This is an erosion-source priority
   indicator, not measured sediment transport.
7. **Criterion proxies and source dependence** — Flood uses rainy-season CHIRPS
   climatology rather than an event-extreme rainfall metric. Sediment C and Land
   Use pressure have different value functions but share WorldCover
   (`Spearman rho=0.498`). The Socioeconomic score remains strongly rank-aligned
   with road/access (`rho=0.970`). The Environmental score is water/wetland-led
   because the checked SERNANP national definitive layer contributes no local
   geometry. Removing or replacing those components changes the selected
   highest-priority quintile, so these are explicit evidence limitations rather
   than reasons to silently retune the supplied AHP weights.

## R-factor status (no longer a critical-path uncertainty)

R-factor was previously the highest-priority open question. As of 2026-07-06 it
is **quarantined out of the critical path** (see `DECISION_LOG.md`
D-RFACTOR-QUARANTINE):

- The active Peru Sediment criterion uses normalized K, LS, and C subcriteria;
  it does not calculate USLE A and therefore does not require R.
- The older K×LS×C structure remains diagnostic lineage and is not the current
  Peru PIM Sediment input.
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
