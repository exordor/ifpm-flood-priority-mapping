# Decision Log

Status: active. Why each major choice was made. Each entry: id, date, context,
decision, reason, alternatives, consequences.

## D-VERSION-B — 2026-06-16 slide is the authoritative methodology

- **Date:** 2026-07-02 (recorded), 2026-06-16 (slide received).
- **Context:** Two methodology versions existed: Version A (original broad
  picture, 2026-05/2026-06-02) and Version B (2026-06-16 slide). They are not
  identical.
- **Decision:** Version B (2026-06-16 slide) is authoritative.
- **Reason:** most recent, most specific, the version the mentor actively sent.
  Version B narrows scope: five scored criteria, example weights, an explicit
  open question on Rehabilitation Potential rather than treating it as a full
  third module.
- **Alternatives:** Version A (broad picture with citizen-science + stakeholder
  iteration + post-mining module). Rejected — de-scoped by Version B.
- **Consequences:**
  - In scope: five AHP main criteria; rainfall only as a Flood-side sensitivity
    implementation layer; AHP-MCDA weighted overlay; sensitivity analysis.
    Bilateral Zimbabwe-Peru prototype comparison was the June/early-July
    working route, but the current mainline is superseded by D-PERU-FIRST.
  - Not required unless mentor re-requests: citizen-science module; stakeholder
    feedback iteration; post-mining opportunities as a full module.
  - Open, mentor-gated: Rehabilitation Potential role (D-REHAB).

## D-V1-WAIVER — V1 (Upper Mzingwane catchment, ~3689 km²) accepted with waiver for prototype

- **Date:** 2026-06-12 (decision), 2026-06-16 (mentor thumbs-up).
- **Context:** Boundary discovery produced multiple candidates (HydroBASINS L7
  ~3700 km², Geoportal `Upper Mzingwane` ~7321.5 km², ~2138 km² literature
  reference). No source supplied reusable geometry for the literature reference.
- **Decision:** V1 — the Upper Mzingwane catchment (~3689 km², HydroBASINS
  level-8, semi-arid; contains Mzingwane Dam and Esigodini, excludes Gwanda) —
  is accepted with waiver for prototype. C1 (the next-nearest HydroBASINS
  candidate) is demoted to machine prior only.
- **Reason:** V1 better matches the mentor's Level-8 downstream-to-Gwanda cue;
  mentor gave thumbs-up to the V1 evidence board.
- **Alternatives:** Geoportal named sub-catchment; HydroBASINS L7 union; ~2138
  km² literature boundary (geometry-unresolved).
- **Consequences:** V1 — the Upper Mzingwane catchment (~3689 km², semi-arid;
  contains Mzingwane Dam and Esigodini, excludes Gwanda) — is the prototype
  boundary. Final thesis boundary remains open (IFPM-D06). Waiver does not
  authorize final flood-risk
  interpretation, intervention-priority interpretation, or treating CHIRPS as
  native 30 m rainfall evidence.

## D-PE1-CATCHMENT — PE1 selected as southern Peru comparison catchment

- **Date:** 2026-06-30.
- **Context:** Peru side was entirely blank. The mentor had not named a final
  Peru study site. A boundary was needed to run the terrain chain end-to-end and
  prove comparability.
- **Decision:** PE1 = HydroBASINS L7 `HYBAS_ID=6070641200`, 2745.4 km²,
  Pacific-slope catchment in Arequipa Region, mainly the
  Vitor-La Joya-Santa Rita de Siguas area west of Arequipa city. It was chosen
  by explicit selection rule (pacific-slope, fully inside the
  Arequipa-Moquegua-Tacna discovery envelope, area comparable to V1,
  non-terminal).
- **Reason:** no mentor-named Peru outlet exists; selection rule makes the
  choice auditable rather than arbitrary.
- **Alternatives:** wait for mentor to name a site (blocked progress); pick
  arbitrary largest basin (not defensible).
- **Consequences:** PE1 — the Pacific-slope Vitor-La Joya-Santa Rita de Siguas
  catchment in Arequipa Region (~2745 km², arid) — is a provisional comparison
  catchment, NOT a final research-selected Peru study area. It will be replaced
  if the mentor names a specific Peru site. No flood-risk/comparison claim from
  PE1. Superseded for the current working mainline by D-PERU-FIRST: PE1 remains
  provisional, but it is now the active Peru-first case to complete.

## D-PERU-FIRST — Peru becomes the current mainline case

- **Date:** 2026-07-06.
- **Context:** During the 2026-07-06 mentor discussion, the mentor directed:
  "Let's keep Peru and work with Peru first till the end." The immediate
  methodological point was that the end product should be a flood
  prioritisation map based on all weighted criteria, with mining data overlaid
  afterwards to see whether mining areas coincide with high-priority areas.
  Peru also has stronger current mining evidence through INGEMMET small-mining
  points, while Zimbabwe mining remains OSM-only / weak.
- **Decision:** Shift the active project mainline to a Peru-first case study.
  Complete PE1 first: five-criterion input maps, AHP-weighted prototype
  prioritisation map, top-priority classes, mining overlay, and a data-strength
  table. Keep Zimbabwe as a secondary / background comparison and method
  development baseline, not the result to finish first.
- **Reason:** Peru currently has the more complete and defensible data stack
  for the research story, especially mining. Completing one coherent Peru case
  is stronger than maintaining a symmetric Zimbabwe-Peru comparison while one
  side has weaker mining evidence.
- **Alternatives:**
  - Continue bilateral Zimbabwe-Peru comparison as the mainline (rejected for
    now: splits attention and over-emphasises weak Zimbabwe evidence).
  - Switch to Zimbabwe only (rejected: current mining evidence is weaker).
  - Wait for a final Peru site or final AHP weights (rejected: uncertainty
    lowers claim level; it does not stop the Peru prototype).
- **Consequences:**
  - New outputs and PPT structure should lead with Peru.
  - Zimbabwe outputs remain usable for background, contrast, or later
    comparison, but not as the active endpoint.
  - PE1 is still provisional and not a final research-selected Peru boundary.
  - Equal weights remain baseline/sensitivity only; the current Peru main
    weight scenario is superseded by D-PERU-MENTOR-WEIGHTS.
  - The final map label should be "prototype flood prioritisation map", not
    "validated flood-risk map" or "rescue-decision map".
  - Mining overlay is an interpretation layer over the Peru prioritisation map;
    it is not validation by itself.

## D-PERU-MENTOR-WEIGHTS — Peru direct AHP weights become the current PIM scenario

- **Date:** 2026-07-06.
- **Context:** After the Peru-first switch, the mentor supplied a Peru-specific
  recommended weight table for the Arequipa mining-region case:
  `FH=0.35`, `SE=0.25`, `LM=0.20`, `ES=0.12`, `SV=0.08`, plus local
  sub-criteria weights.
- **Decision:** Use those direct Peru weights as the current main PIM scenario
  (`mentor_peru_direct_pim`) and keep equal weights as a neutral baseline. Do
  not use the older slide pairwise matrix as the current Peru mainline scenario.
- **Reason:** The new table is site-specific and newer than the generic
  example matrix. It matches the mentor's current Peru-first direction.
- **Alternatives:** keep the old slide matrix (rejected for the current Peru
  run because it is generic/older); keep flood-sediment-heavy as a third
  scenario (rejected for the current PPT/mainline because the mentor asked for
  the weighted prioritisation model, not extra scenario storytelling).
- **Consequences:**
  - Current Peru scenario outputs contain two scenarios: `equal_active_pim`
    and `mentor_peru_direct_pim`.
  - The direct weights have no supplied pairwise matrix or consistency ratio,
    so the current run must not report a CR for them.
  - Flood, Land Use / ASM, and Environmental subweights are implemented where
    the current data support them.
  - Sediment still uses the current `K x LS x C` erosion-source structure as a
    single executable criterion; the new K/LS/C local subweights are recorded
    as a gap until a grid-compatible independent K-factor layer is rebuilt.
  - Socioeconomic still uses road/access proximity only; independent
    infrastructure exposure is recorded as missing.

## D-ZIMBABWE-MENTOR-WEIGHTS — Zimbabwe direct AHP weights recorded as secondary scenario

- **Date:** 2026-07-06.
- **Context:** After the Peru-first switch, a Zimbabwe-specific recommended
  weight table was supplied for the Upper Mzingwane catchment:
  `FH=0.32`, `SE=0.23`, `LM=0.18`, `ES=0.12`, `SV=0.15`, plus local
  sub-criteria weights.
- **Decision:** Use those direct Zimbabwe weights in the secondary
  `boundary_v1 / rainfall_exposure_v0_4` run as
  `mentor_zimbabwe_direct_pim`, with equal weights retained as baseline.
  Do not use the older generic slide matrix or the former flood/sediment-heavy
  scenario in the current Zimbabwe output directory.
- **Reason:** The new table is site-specific and aligns the secondary
  Zimbabwe prototype with the same five-main-criterion framework used by
  Peru, while keeping Peru as the active mainline.
- **Alternatives:** keep the old slide matrix in the current Zimbabwe run
  (rejected for current outputs because a newer site-specific table exists);
  promote Zimbabwe back to mainline (rejected because D-PERU-FIRST still
  applies).
- **Consequences:**
  - Current Zimbabwe scenario outputs contain two scenarios:
    `equal_active_pim` and `mentor_zimbabwe_direct_pim`.
  - The direct weights have no supplied pairwise matrix or consistency ratio,
    so the current run must not report a CR for them.
  - Flood subweights are implemented as rainfall 0.35, TWI 0.30, and drainage
    proximity 0.35.
  - Land Use / ASM subweights are implemented as land-cover pressure 0.40 and
    mining pressure 0.60, but Zimbabwe mining evidence remains OSM-only and
    weak.
  - Environmental is implemented as water/wetland context 0.55 plus protected /
    ecological context 0.45.
  - Sediment still uses the current `K x LS x C` erosion-source structure as a
    single executable criterion; the new K/LS/C subweights are recorded as a
    gap until a grid-compatible independent K-factor layer is rebuilt.
  - Socioeconomic still uses road/access proximity only; independent
    infrastructure exposure is recorded as missing.

## D-CRITERIA-V0-2 — honest-label criteria stack repair

- **Date:** 2026-06-29.
- **Context:** `criteria_stack_v0_1` worked technically but two semantic/data-
  policy problems: `K×LS×C` was mislabelled as sediment risk, and NoData was
  filled as low pressure. Mining and exposure criteria were the weakest.
- **Decision:** `criteria_stack_v0_2` splits the hidden averages, renames to
  honest labels (`land_cover_pressure`, `mining_pressure`,
  `soil_erosion_factors`), and preserves NoData instead of filling.
- **Reason:** AGENTS.md §Criteria Design Rules requires criterion names that
  describe what the data actually measure, and NoData must remain NoData unless
  a documented method justifies imputation.
- **Alternatives:** keep v0.1 labelling (violates criteria-design rules);
  over-broaden to sediment risk (no accepted R-factor).
- **Replacement rules** (a v0.2 update may replace a v0.1 criterion only if
  stronger by at least one of):
  - official source instead of public proxy;
  - observed flood/mining impact instead of generic proximity;
  - better temporal match;
  - clear V1 overlap;
  - documented licence and reproducibility;
  - no false precision from resampling.
- **Consequences:** v0.1 remains the frozen baseline; v0.2 outputs do not
  overwrite v0.1. If evidence is not stronger, v0.2 keeps the baseline criterion
  and marks the missing dataset in the mentor trip request list.

## D-EXECUTION-POLICY — uncertainty reduces claim level, not pauses execution

- **Date:** 2026-06-29 (IFPM-090).
- **Context:** Multiple "defensive gates" treated uncertainty as a reason to
  pause. This blocked legitimate data-processing work behind thesis-level
  decisions that are the mentor's responsibility.
- **Decision:** Convert defensive gates into execution-status rules.
  Uncertainty reduces claim level; it does not automatically pause execution.
- **Reason:** separates HiWi data-processing scope from mentor/thesis claim
  scope. Data production (downloads, preprocessing, indicator derivation,
  standardization, diagnostic overlays with documented weights) is GO and
  self-authorizing via documented defaults. Interpretable claims (validated
  flood-risk map, intervention priority, Zimbabwe-Peru comparison, publication)
  remain NO-GO and are the mentor's calls.
- **Alternatives:** keep global pauses (blocked progress); remove all gates
  (loses claim discipline).
- **Consequences:** the five claim levels
  (`diagnostic_only`/`provisional`/`sensitivity_scenario`/`mentor_review_ready`/
  `final_claim`) become the standard status vocabulary. Pause only when required
  inputs are missing and no provisional substitute exists, code cannot run with
  the exact error documented, continuing would overwrite valid outputs, or the
  user explicitly asks to pause. See `REPRODUCIBILITY.md` §Execution status.

## D-JULY18-SCOPE — locked deliverable scope for 18 July mentor trip

- **Date:** 2026-07-02 (revised 2026-07-03).
- **Context:** The bilateral comparison the mentor wants already existed at
  ~80% completion but was buried in `outputs/`. Work drifted to engineering
  refactoring because the real scientific direction was invisible. Three
  mentor/boss-facing artifacts existed but were scattered and each lacked one
  piece.
- **Decision:** Lock scope for two deliverables, built entirely from existing
  data and scripts. No new criteria, no new downloads, no final claims.
  - Deliverable 1: integrated main figure with bilateral comparison + per-pixel
    priority-criterion colouring + clear "why" (4 panels, takeaway, claim level
    on figure face).
  - Deliverable 2: boss short process figure with goal header and bilateral
    label.
- **Reason:** the mentor independently asked (2026-07-02 Teams) for exactly what
  was half-built.
- **Alternatives:** broad new modelling (blocked by gates); broad `bin/`
  refactoring as primary activity (no scientific value).
- **Consequences:** the integrated comparison pack is generated under
  `outputs/zimbabwe_peru_prototype_comparison/`. Out of scope for 7/18: new
  Zimbabwe mining work; Voi site switch; final flood-risk claim; final
  Zimbabwe-Peru comparison; weight authorisation; broad `bin/` refactoring.
- **QA criteria:** non-participant identifies study area, main result, key
  driver within 30 seconds; claim level on figure face in plain language;
  takeaway is a statement not a question; legends/colourbars/captions do not
  hide evidence; criterion names are plain.

## D-RFACTOR-DEPRECATE — all V1/V2 R and USLE A products deprecated

- **Date:** 2026-06-19 (audit), 2026-07-01 (products removed).
- **Context:** A spot-check found an unverified R-factor coefficient. A full
  audit revealed the V1 R applies P-based Renard-Freimund coefficients to MFI
  with an invented break, manufacturing the bimodality.
- **Decision:** all V1/V2 R-factor rasters and all USLE A rasters derived from
  them are deprecated and removed. The "V2 resolves the bimodality" framing is
  invalid.
- **Reason:** wrong coefficients AND wrong break; absolute values untrustworthy.
- **What stays safe:** `a_structure_K_LS_C_30m.tif` (K×LS×C erosion-source
  structure, no rainfall-erosivity factor); K, LS, C factors (all verified);
  hydrology and terrain preprocessing; CHIRPS
  rainfall-comparison products; ERA5 empirical R diagnostics; top-20%
  selection-survival structure test (with caveats).
- **Consequences:** USLE A absolute values blocked until R-method decision
  (RQ1). New R-factor products may be generated as `provisional` or
  `sensitivity_scenario` if method, source, value range, uncertainty, and
  lineage are documented. (Superseded for the critical path by
  D-RFACTOR-QUARANTINE below.)

## D-RFACTOR-QUARANTINE — R-factor removed from the critical path

- **Date:** 2026-07-06.
- **Context:** R-factor had been the highest-priority open question (RQ1) since
  the 2026-06-19 formula audit (D-RFACTOR-DEPRECATE). It recurrently consumed
  attention through three mechanisms: (a) the original error opened a rabbit
  hole with no exit sign; (b) the project's own execution-status policy
  ("uncertainty reduces claim level, does not automatically pause") was not
  applied to R-factor, which was treated as a blocker; (c) the technical work
  (six literature methods, two incompatible families ~6× apart, ERA5 lower-
  bound) was interesting enough to keep pulling focus. Meanwhile R-factor is
  one sub-component of one criterion (sediment) out of five, not the project
  mainline.
- **Decision:** Quarantine R-factor out of the critical path. The sediment
  criterion is served by the K×LS×C erosion-source structure layer
  (`a_structure_K_LS_C_30m.tif`), which is independent of R, already built, and
  grid-compatible. USLE A absolute values (ton/ha/yr) are no longer required
  for the prototype priority map. RQ1, H-RF-FAMILIES, and the R-factor
  experiments move to `deferred` status. The R-factor record stays in
  `RESULTS.md` §R-factor as a deferred technical record, not an active blocker.
- **Reason:** Top-20% priority areas are independent of the rainfall-erosivity
  factor R (H-TOP20-R-INVARIANT,
  supported): R only scales absolute magnitude (ton/ha/yr), it does not change
  which area ranks first. For the PIM priority-map output, the R-method choice
  is irrelevant. The v0.2 honest-label repair already renamed this criterion
  `soil_erosion_factors` (not "sediment risk") — the quarantine completes what
  that rename started. This decision operationalises the existing
  D-EXECUTION-POLICY rule that the project was not applying to R-factor.
- **Alternatives considered:**
  - Keep R-factor as the highest-priority open question (rejected: no stop
    condition; recursion loop continues).
  - Delete the R-factor history entirely (rejected: the audit/verification
    work is sound and may be needed if the mentor requires USLE A; deletion
    loses traceable evidence).
  - Demote the entire sediment criterion to weight 0 (rejected for now: the
    slide matrix gives sediment weight 0.226, second highest; unilateral
    demotion may diverge from mentor expectation. K×LS×C keeps the criterion
    live with honest evidence.)
- **Consequences:**
  - The PIM prototype priority map no longer waits on R-factor.
  - One-sentence mentor question drafted (see TODO + mentor-explanation draft)
    asking whether the K×LS×C sediment-criterion approach is acceptable.
  - Reversible: if the mentor rejects K×LS×C and requires USLE A (ton/ha/yr),
    R-factor is reopened and the deferred record in `RESULTS.md` becomes the
    active starting point.
  - IFPM-074 (V2 R-factor) and the dead V2 set stay deferred; no rework now.

## D-TERMINOLOGY — active terminology gate

- **Date:** 2026-07-02 (audit), 2026-07-03 (execution).
- **Context:** Human-facing terms needed to be checked against mainstream
  literature; broad `*_proxy` names were leaking into active workflow.
- **Decision:** stop using broad `*_proxy` names in the active workflow. Active
  criteria now use `flood_conditioning_factors`, `soil_erosion_factors`,
  `land_cover_pressure`, `mining_pressure`, `exposure_indicators`,
  `rainfall_climatology`. Active gate is `bin/check_active_terminology.py`.
- **Reason:** P1 findings: the deprecated `flood_hazard_proxy` name misused the
  standard word "hazard" (no inundation evidence); the deprecated coined internal
  shorthand `R-invariant` is not a mainstream USLE/RUSLE term.
- **Consequences:** active terminology gate must pass before sending any
  mentor/boss-facing package. 5 v0.1 + 6-13 files archived 2026-07-03; 3 live
  files rewritten; `violation` count stayed at 0. Remaining hits of the coined
  shorthand are all in the dead V2 set or living docs to fix opportunistically.

## IFPM-DNN decision register (mentor-gated)

These decisions are recorded in `RESEARCH_QUESTIONS.md` and block final claims.
They are not project decisions; they are mentor decisions awaiting input.

| id | decision needed | current state |
|---|---|---|
| IFPM-D01 | Final modelling unit (pixel / sub-basin / mixed) | blocked |
| IFPM-D02 | Peru boundary rule (admin / hydrographic / clipped) | concrete candidates exist; mentor-gated |
| IFPM-D03 | Validation evidence hierarchy | blocked (validation data ~zero) |
| IFPM-D04 | AHP weighting protocol + matrix authorisation | candidate matrix exists as `sensitivity_scenario`; auth open |
| IFPM-D05 | Mining-data interpretation rule + Rehabilitation Potential role | open |
| IFPM-D06 | Upper Mzingwane boundary acceptance (final thesis) | V1 waiver only |

## Lineage

Absorbs content from:
- `project_objective_calibration_2026-07-02.md` (D-VERSION-B)
- `task_progress_board.md` §Blocked Or Needs Decision (IFPM-D01..D06)
- `boundary_v1_criteria_stack_v0_2_2026-06-29.md` (D-CRITERIA-V0-2)
- `july18_deliverable_scope_2026-07-02.md` (D-JULY18-SCOPE)
- `real_data_execution_preflight_gate.md` (D-EXECUTION-POLICY scope split)
- `rfactor_investigation_consolidated.md` §1, §6 (D-RFACTOR-DEPRECATE)
- `terminology_audit_2026-07-02.md` (D-TERMINOLOGY)
- `assumptions_log.md` (decision-style assumptions)
- `real_data_preprocessing_design.md` (boundary acceptance rules → D-V1-WAIVER)
- `_archive/superseded_boundary_exploration_2026-06/v1_working_boundary_decision_2026-06-12.md` (D-V1-WAIVER)
- `_archive/superseded_process_notes_2026-06/peru_pilot_boundary_decision_2026-06-30.md` (historical PE1 boundary-selection note)
