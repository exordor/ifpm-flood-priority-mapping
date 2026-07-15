# Research Questions

Status: active. Open scientific and methodological questions.

> **Operating mode (2026-07-06):** this project runs on autonomous default
> decisions. The HiWi makes the call, documents it, builds the artifact, and
> shows the result. Open questions below are tracked as defaults-taken or
> next-experiment-prompts, not as "questions for the mentor". If the mentor
> wants a different choice after seeing an artifact, the project adapts then.

> **Current mainline (2026-07-06):** per D-PERU-FIRST, finish Peru first. Arequipa Region is
> the active Peru-first working case for maps and PPT structure, while Zimbabwe
> is secondary/background until stronger Zimbabwe evidence or a later comparison
> need reopens it.

## RQ1: What is the appropriate R-factor method for semi-arid Zimbabwe? (DEFERRED — out of critical path as of 2026-07-06)

**Status: deferred.** R-factor is quarantined out of the critical path (see
`DECISION_LOG.md` D-RFACTOR-QUARANTINE). The active Peru Sediment criterion
combines normalized K, LS, and C with local AHP weights and does not calculate
USLE A. The older Zimbabwe K×LS×C structure remains diagnostic lineage. USLE A
absolute values (ton/ha/yr) are not required for the prototype priority map.

The technical record stays for transparency: six literature methods run on the
same V1 CHIRPS inputs split into two incompatible families ~6× apart. The only
independent check (ERA5 hourly EI30 lower-bound) sits in the lower range. There
is no independent measured EI30 R for the V1 catchment.

**Default taken:** use normalized K/LS/C subcriteria for current Peru Sediment.
Revisit R-factor only if a quantitative soil-loss rate (ton/ha/yr) becomes needed for the thesis —
that would require a primary EI30 dataset (sub-daily gauge or GPM IMERG) or an
explicit method choice.

- **Decision id:** D-RFACTOR-QUARANTINE (active); was surfaced via IFPM-080/081/082
- **Related:** `EXPERIMENTS.md` §R-factor exploration, §ERA5 empirical (deferred);
  `RESULTS.md` §R-factor (deferred-record); `HYPOTHESES.md` H-RF-FAMILIES (deferred),
  H-BIMODALITY-ARTIFACT (supported), H-TOP20-R-INVARIANT (supported, justifies quarantine)
- **Claim level:** `deferred` (was `sensitivity_scenario`); all V1/V2 R and
  USLE A absolute values remain deprecated and are no longer needed.

## RQ2: AHP weight set — default: Peru direct mentor weights for reporting

The 2026-06-16 slide matrix (CR 0.022) is internally consistent and remains a
historical / generic sensitivity record. After the 2026-07-06 Peru-first
discussion, the current Peru mainline uses the newer Peru-specific direct
mentor weights: `FH=0.35`, `SE=0.25`, `LM=0.20`, `ES=0.12`, `SV=0.08`.
Zimbabwe has a newer site-specific direct table for the secondary Upper
Mzingwane run: `FH=0.32`, `SE=0.23`, `LM=0.18`, `ES=0.12`, `SV=0.15`.

**Default taken:** use the Peru direct weights as the current main
`sensitivity_scenario` and as the only active or reported Peru weight set. Do
not generate an equal-versus-direct comparison. Use the Zimbabwe direct weights only
in the secondary Zimbabwe run. Do not report a consistency ratio for either
direct table because no pairwise matrix was supplied with the new tables. Do
not call the result final; it remains a prototype priority map.

- **Decision id:** D-PERU-MENTOR-WEIGHTS; D-ZIMBABWE-MENTOR-WEIGHTS
- **Related:** `HYPOTHESES.md` H-PERU-DIRECT-WEIGHTS,
  H-ZIMBABWE-DIRECT-WEIGHTS; H-AHP-SLIDE-TRANSFERS remains
  historical/background.
- **Claim level:** `sensitivity_scenario`

## RQ3: Rehabilitation Potential — default: not built until a use is needed

The slide lists it as an input layer but omits it from the PIM formula and
matrix.

**Default taken:** do not build a Rehabilitation Potential criterion for the
prototype. It is not in the 5-criteria PIM formula, so it is not needed for the
priority map. If a rehabilitation-priority comparison becomes a thesis goal
later, revisit then. Meanwhile do not block on it.

- **Decision id:** IFPM-D05 (default taken)
- **Related:** none built
- **Claim level:** not applicable yet

## RQ4: Modelling unit — default: pixel-raster on the 30 m reference grid

Controls normalization, aggregation, and Zimbabwe-Peru comparability.

**Default taken:** pixel-raster on the 30 m reference grid (EPSG:32735 for V1,
EPSG:32718 for Arequipa Region), with zonal summaries (catchment / sub-basin) reported
alongside when needed. The grid gate enforces compatibility before any overlay.
This avoids blocking on a sub-basin-aggregation redesign.

- **Decision id:** IFPM-D01 (default taken)
- **Related:** `REPRODUCIBILITY.md` §Preprocessing design (model-unit branches)
- **Claim level:** `provisional` for pixel-raster outputs

## RQ5: Zimbabwe (Upper Mzingwane) boundary — default: V1 with waiver

V1 — the Upper Mzingwane catchment (~3689 km², semi-arid; contains Mzingwane
Dam and Esigodini, excludes Gwanda) — is accepted with waiver for prototype.
Comparison layers: Geoportal `Upper Mzingwane` (~7321.5 km²), HydroBASINS L7
(~3700 km²), the source/geometry-unresolved ~2138 km² literature reference.

**Default taken:** keep V1 as the prototype boundary for all current work. Do
not promote it to "final thesis boundary" in any output label. The ~2138 km²
public-source hunt is exhausted; if the mentor supplies an authoritative
polygon later, swap it in then. Meanwhile do not redo work on a different
boundary.

- **Decision id:** IFPM-D06 (default taken)
- **Related:** `EXPERIMENTS.md` §boundary discovery; `DECISION_LOG.md` D-V1-WAIVER
- **Claim level:** `provisional` (prototype)

## RQ6: Peru boundary — working HydroBASINS catchment within Arequipa Region

The current working boundary, displayed externally as **Arequipa Region**, is
HydroBASINS L7 `6070641200`: a provisional comparison catchment mainly covering
the Vitor-La Joya-Santa Rita de Siguas area west of
Arequipa city. It was chosen by a selection rule (pacific-slope, inside the
Arequipa-Moquegua-Tacna discovery envelope, area comparable to V1,
non-terminal), not as a final research-selected site.

**Default taken:** keep Arequipa Region as the active Peru-first working case and complete
the Peru workflow first. The input-criteria maps, direct-weight prototype PIM,
priority classes, mining/population overlay, contribution map, and SINPAD
diagnostic are complete; the integrated briefing board and data-strength table
remain. If the mentor names a different Peru site later, rebuild there. See
`DECISION_LOG.md` D-AREQUIPA-REGION-CATCHMENT and D-PERU-FIRST.

- **Decision id:** IFPM-D02 (default taken)
- **Related:** `EXPERIMENTS.md` §Peru Arequipa Region chain; `DECISION_LOG.md`
  D-AREQUIPA-REGION-CATCHMENT, D-PERU-FIRST
- **Claim level:** `provisional`

## RQ7: Validation evidence — SINPAD point context available; independent validation remains unavailable

Determines whether outputs are susceptibility maps, risk maps, or intervention
maps. Peru now has 25 in-boundary SINPAD hydrometeorological records at 11
unique coordinates. Only 4 records at 2 unique coordinates are explicitly
flood-labelled, and the geometries are event reference points rather than
observed flood extents. This supports a co-location diagnostic, not validation.

**Default taken:** label all outputs as priority/susceptibility prototypes,
never as validated risk maps. Report SINPAD by all records, unique coordinates,
flood-specific records, and unique flood coordinates. If observed flood extent
or impact evidence becomes available, add a separate independent validation
layer then.

- **Decision id:** IFPM-D03 (default taken)
- **Related:** `RESULTS.md` §exposure diagnostic
- **Claim level:** `diagnostic_only` for any validation-dependent claim

## RQ8: Mining evidence — default: OSM indicator (Zimbabwe) / INGEMMET official points (Peru)

Avoids treating mining rights as active mining footprints. Zimbabwe ASM is
structurally artisanal and scattered; no official footprint exists (A-013).
Peru has the public INGEMMET/GEOCATMIN Pequeña Minería cadastre (strictly
stronger than Zimbabwe's OSM-only indicator).

**Default taken:** use OSM quarry/industrial proximity as the Zimbabwe mining
indicator (label as indicator, not truth), and INGEMMET official ASM point
proximity as the Peru mining layer (stronger, `provisional`). If the mentor
returns with official Zimbabwe ASM data, swap it in.

- **Decision id:** IFPM-D05 (default taken; overlaps RQ3 role)
- **Related:** `EXPERIMENTS.md` §Arequipa Region mining upgrade; `RESULTS.md` §mining
- **Claim level:** Zimbabwe mining = `diagnostic_only`; Peru mining = `provisional`

## RQ9: Are the V1 prototype top-20% priority areas robust to weighting assumptions?

Earlier multi-scenario top-20% tests remain historical structure diagnostics;
they are not part of the active Peru reporting chain.

- **Decision id:** none
- **Related:** `EXPERIMENTS.md` §priority scenarios; `RESULTS.md` §top-20% priority-area stability
- **Claim level:** `sensitivity_scenario`

## RQ10: Are the Zimbabwe and Peru sites structurally comparable?

Arequipa Region is now operationally comparable to V1 under the mentor five-main-criterion
framework. Both runs use the same five active PIM main criteria as top-level
overlay terms: Flood, Sediment, Land Use / ASM, Environmental, and
Socioeconomic. Flood and Land Use / ASM have internal component rasters, while
Environmental is a provisional water/wetland and protected-area sensitivity
indicator rather than ecological valuation. Physical
contrast is real: Arequipa Region is arid Andean Pacific slope (C=0.61, bare; soil loss
8.74 t/ha/yr) vs V1 semi-humid savanna (C=0.04, shrub/grass; soil loss 0.50).
Final comparison claim remains blocked until harmonized. After D-PERU-FIRST,
this is a secondary/background question rather than the active mainline; the
current priority is to complete the Peru case first.

- **Decision id:** part of IFPM-D03 / Peru gate
- **Related:** `EXPERIMENTS.md` §Zimbabwe-Peru comparison; `RESULTS.md` §comparison
- **Claim level:** `provisional` / `sensitivity_scenario`; final claim blocked

## Other recurring open modelling questions

From the project's open-modelling-questions list (AGENTS.md §Modelling Context),
most are subsumed by the IFPM-DNN decisions above. The ones without a dedicated
decision id:

- **GIS preprocessing readiness** — closed for terrain; open for rainfall and
  exposure resampling.
- **Time period and validation windows** — partly closed for rainfall
  comparison, open for validation (RQ7).
- **Final dataset selection and replacement rules** — tracked per-criterion in
  `boundary_v1_criteria_stack_v0_2` decision rules (see `DECISION_LOG.md`
  D-CRITERIA-V0-2).

## Active assumptions register (was `assumptions_log.md`)

| id | assumption | status | applies to |
|---|---|---|---|
| A-001 | V1 (Upper Mzingwane, ~3689 km², semi-arid; contains Mzingwane Dam and Esigodini, excludes Gwanda) remains the prototype boundary, not the final thesis boundary. | provisional | V1 outputs |
| A-002 | Coarse rainfall may be used through zonal aggregation or labelled coarse-to-reference-grid resampling. | sensitivity_scenario | CHIRPS/rainfall criteria |
| A-003 | The 2026-06-16 mentor-slide AHP matrix may be used as a historical/generic sensitivity scenario, but it is no longer the current Peru mainline weight set. | sensitivity_scenario | AHP weights |
| A-004 | Deprecated R/A products remain invalid, but new R-factor families may be generated with fresh lineage. | provisional | R-factor/RUSLE work |
| A-005 | OSM quarry/industrial evidence is a mining activity indicator, not official ASM truth. | diagnostic_only | mining/ASM criterion |
| A-006 | Road proximity is an exposure/access indicator, not socioeconomic vulnerability. | diagnostic_only | exposure criterion |
| A-007 | Peru can run data-readiness and terrain diagnostics in parallel. | diagnostic_only | Peru side |
| A-008 | The Peru Arequipa-Moquegua-Tacna discovery envelope is a discovery aid, not an authoritative boundary. | diagnostic_only | Peru boundary discovery |
| A-009 | The working boundary displayed externally as **Arequipa Region** is HydroBASINS L7 `6070641200`, mainly covering the Vitor-La Joya-Santa Rita de Siguas area west of Arequipa city. It is chosen by a selection rule, NOT a final research-selected site. | provisional | Peru terrain chain |
| A-010 | The `rainfall_climatology` criterion (rainfall_sensitivity_v0_3) is a 0.05° CHIRPS rainy-season mean bilinear-resampled to the V1 30 m grid; resampling-edge NoData slivers inside V1 are nearest-EDT filled. Effective resolution ~5 km, NOT native 30 m. | sensitivity_scenario | rainfall criterion |
| A-011 | The top-20% priority-area exposure diagnostic measures spatial co-location of v0.2 repeatedly selected top-20% priority areas with exposure indicators; weak co-location means selected priority areas reflect natural-pressure overlap, not observed exposure. | diagnostic_only | exposure diagnostic |
| A-012 | The Arequipa Region `rainfall_climatology` criterion uses CHIRPS latam Dec-Mar mean, bilinear-resampled to the 30 m reference grid and normalized from Arequipa Region boundary values only. Effective resolution remains ~5 km. | sensitivity_scenario | Arequipa Region rainfall criterion |
| A-013 | Zimbabwe ASM is structurally artisanal and scattered; no verified active footprint exists. The current mining layer uses USGS Africa GIS mineral facilities and deposits as a proximity-based reference, not an active ASM footprint. | diagnostic_only | Zimbabwe mining criterion |
| A-014 | If Zimbabwe ASM data is not obtainable, the mentor may switch the Zimbabwe site to Voi (Kenya). Voi rainfall is already in managed storage. NOT a current action — strategic fallback only. | contingency | Zimbabwe site / boundary |
| A-015 | Peru is the active mainline case after the 2026-07-06 mentor direction to work with Peru first until the end. Arequipa Region remains provisional, but new maps and PPT structure should lead with Peru. | provisional | Peru-first workflow |
| A-016 | Current Peru PIM main weights are the mentor direct table: FH 0.35, SE 0.25, LM 0.20, ES 0.12, SV 0.08. This is the only active Peru scenario. No CR is reported because no pairwise matrix was supplied for this direct table. | sensitivity_scenario | Peru AHP weights |
| A-017 | Peru Sediment independently applies normalized K 0.30 / LS 0.45 / C 0.25. SoilGrids K is aligned to the reference grid but remains 250 m effective evidence. The final PIM is scored only on 95.0998% five-criterion common support; 4.9002% remains unscored and is classified by missing LS, K, or other evidence. | provisional | Peru sediment criterion |
| A-018 | Peru exposure indicators implement the supplied socioeconomic split: 0.45 road/access + 0.55 infrastructure. Infrastructure exposure is a provisional 0.50 WorldPop population + 0.50 OSM mapped-building implementation indicator. | provisional | Peru socioeconomic criterion |
| A-019 | Current secondary Zimbabwe PIM main weights are the direct table: FH 0.32, SE 0.23, LM 0.18, ES 0.12, SV 0.15. Zimbabwe remains background and no equal-weight comparison enters the current Peru report. No CR is reported because no pairwise matrix was supplied for this table. | sensitivity_scenario | Zimbabwe AHP weights |
| A-020 | Zimbabwe Sediment independently applies boundary-standardized spatial K 0.35 / LS 0.35 / C 0.30. SoilGrids K is aligned to the 30 m reference grid but remains 250 m effective evidence; NoData in any component remains unscored. | provisional | Zimbabwe sediment criterion |
| A-021 | Zimbabwe socioeconomic exposure uses road/access proximity only; independent infrastructure exposure is not available in the current run. | diagnostic_only | Zimbabwe socioeconomic criterion |
| A-022 | INEI district poverty and OSM health-service remoteness are response-capacity context layers and are excluded from the current Peru AHP overlay because no mentor subweights were supplied for them. | diagnostic_only | Peru response-capacity context |
| A-023 | SERNANP national definitive protected-area MapServer layer 0 was checked for Arequipa Region plus a 5 km context zone. No layer-0 geometry occurs in that zone; regional, private, and transitional layers were not queried. The current Environmental score is therefore driven by water/wetland evidence rather than a missing layer-0 download. | provisional | Peru environmental criterion |
| A-024 | Peru Land Use pressure uses a WorldCover human-intensity value function distinct from the RUSLE C-factor used inside Sediment. | provisional | Peru land-use criterion |

## Lineage

Absorbs content from:
- `AGENTS.md` §Modelling Context (recurring open questions)
- `mentor_methodology_slide_interpretation_2026-06-16.md` (Rehab-Potential role, AHP)
- `task_progress_board.md` §Blocked Or Needs Decision (IFPM-D01..D06)
- `rfactor_investigation_consolidated.md` §7 (R-factor open question)
- `assumptions_log.md` (original A-001..A-014 register; A-015..A-022 added in research-map)
