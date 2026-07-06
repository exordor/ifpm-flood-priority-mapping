# Research Questions

Status: active. Open scientific and methodological questions.

> **Operating mode (2026-07-06):** this project runs on autonomous default
> decisions. The HiWi makes the call, documents it, builds the artifact, and
> shows the result. Open questions below are tracked as defaults-taken or
> next-experiment-prompts, not as "questions for the mentor". If the mentor
> wants a different choice after seeing an artifact, the project adapts then.

## RQ1: What is the appropriate R-factor method for semi-arid Zimbabwe? (DEFERRED — out of critical path as of 2026-07-06)

**Status: deferred.** R-factor is quarantined out of the critical path (see
`DECISION_LOG.md` D-RFACTOR-QUARANTINE). The sediment criterion is served by
the K×LS×C erosion-source structure layer, which is independent of R; priority
hotspots are independent of the rainfall-erosivity factor R
(H-HOTSPOT-R-INVARIANT). USLE A absolute values (ton/ha/yr) are no longer
required for the prototype priority map.

The technical record stays for transparency: six literature methods run on the
same V1 CHIRPS inputs split into two incompatible families ~6× apart. The only
independent check (ERA5 hourly EI30 lower-bound) sits in the lower range. There
is no independent measured EI30 R for the V1 catchment.

**Default taken:** use K×LS×C for the sediment criterion. Revisit R-factor only
if a quantitative soil-loss rate (ton/ha/yr) becomes needed for the thesis —
that would require a primary EI30 dataset (sub-daily gauge or GPM IMERG) or an
explicit method choice.

- **Decision id:** D-RFACTOR-QUARANTINE (active); was surfaced via IFPM-080/081/082
- **Related:** `EXPERIMENTS.md` §R-factor exploration, §ERA5 empirical (deferred);
  `RESULTS.md` §R-factor (deferred-record); `HYPOTHESES.md` H-RF-FAMILIES (deferred),
  H-BIMODALITY-ARTIFACT (supported), H-HOTSPOT-R-INVARIANT (supported, justifies quarantine)
- **Claim level:** `deferred` (was `sensitivity_scenario`); all V1/V2 R and
  USLE A absolute values remain deprecated and are no longer needed.

## RQ2: AHP weight set — default: slide matrix as sensitivity scenario

The 2026-06-16 slide matrix (CR 0.022) is internally consistent and structurally
aligns with the deliverable pipeline. The slide labels it "example".

**Default taken:** use the slide matrix as a `sensitivity_scenario` input, run
multiple weight scenarios (equal + slide + flood/erosion-heavy), and report
hotspot stability across them. Do not call any single weight set "final". The
priority map shown to the mentor is the multi-scenario comparison, not a single
weighted overlay.

- **Decision id:** IFPM-D04 (default taken)
- **Related:** `HYPOTHESES.md` H-AHP-SLIDE-TRANSFERS
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
EPSG:32718 for PE1), with zonal summaries (catchment / sub-basin) reported
alongside when needed. The grid gate enforces compatibility before any overlay.
This avoids blocking on a sub-basin-aggregation redesign.

- **Decision id:** IFPM-D01 (default taken)
- **Related:** `REPRODUCIBILITY.md` §Preprocessing design (model-unit branches)
- **Claim level:** `provisional` for pixel-raster outputs

## RQ5: Zimbabwe (Upper Mzingwane) boundary — default: V1 with waiver

V1 (`HB_L8_1081528840_full_l7_chain`) is `accepted_with_waiver_for_controlled_prototype`.
Comparison layers: Geoportal `Upper Mzingwane` (~7321.5 km²), HydroBASINS L7
(~3700 km²), the source/geometry-unresolved ~2138 km² literature reference.

**Default taken:** keep V1 as the working boundary for all prototype work. Do
not promote it to "final thesis boundary" in any output label. The ~2138 km²
public-source hunt is exhausted; if the mentor supplies an authoritative
polygon later, swap it in then. Meanwhile do not redo work on a different
boundary.

- **Decision id:** IFPM-D06 (default taken)
- **Related:** `EXPERIMENTS.md` §boundary discovery; `DECISION_LOG.md` D-V1-WAIVER
- **Claim level:** `provisional` (prototype)

## RQ6: Peru boundary — default: PE1 engineering pilot

PE1 is an engineering pilot chosen by a selection rule (pacific-slope, inside
the three-department envelope, area comparable to V1, non-terminal), not a
research-selected site.

**Default taken:** keep PE1 as the Peru-side prototype. Do not extend it
further (no additional criteria refinement, no further sensitivity sub-runs)
until either (a) the mentor names a specific Peru site, or (b) the bilateral
comparison is promoted. If the mentor names a different site, rebuild there.
See `DECISION_LOG.md` D-PE1-PILOT.

- **Decision id:** IFPM-D02 (default taken)
- **Related:** `EXPERIMENTS.md` §Peru PE1 chain; `DECISION_LOG.md` D-PE1-PILOT
- **Claim level:** `engineering_pilot`

## RQ7: Validation evidence — default: none available; outputs stay at priority/susceptibility level

Determines whether outputs are susceptibility maps, risk maps, or intervention
maps. Current validation data is effectively zero (EM-DAT country profile only;
GloFAS downgraded as not publicly accessible; no in-situ flood-impact data).

**Default taken:** label all outputs as priority/susceptibility prototypes,
never as validated risk maps. Do not block progress waiting for validation
data that does not exist. If the mentor can supply flood-impact observations
or a validation dataset, the project will add a validation layer then.

- **Decision id:** IFPM-D03 (default taken)
- **Related:** `RESULTS.md` §exposure diagnostic
- **Claim level:** `diagnostic_only` for any validation-dependent claim

## RQ8: Mining evidence — default: OSM indicator (Zimbabwe) / INGEMMET official points (Peru)

Avoids treating mining rights as active mining footprints. Zimbabwe ASM is
structurally artisanal and scattered; no official footprint exists (A-013).
Peru has the public INGEMMET/GEOCATMIN Pequeña Minería cadastre (strictly
stronger than Zimbabwe's OSM-only proxy).

**Default taken:** use OSM quarry/industrial proximity as the Zimbabwe mining
indicator (label as indicator, not truth), and INGEMMET official ASM point
proximity as the Peru mining layer (stronger, `provisional`). If the mentor
returns with official Zimbabwe ASM data, swap it in.

- **Decision id:** IFPM-D05 (default taken; overlaps RQ3 role)
- **Related:** `EXPERIMENTS.md` §PE1 mining upgrade; `RESULTS.md` §mining
- **Claim level:** Zimbabwe mining = `diagnostic_only`; Peru mining = `provisional`

## RQ9: Are the V1 prototype hotspots robust to weighting assumptions?

Tested via hotspot-stability across multiple weight scenarios. The
hotspot-survival test is valid only as a structure test (LS×C governs hotspots,
independent of R), not as a candidate-quality ranking.

- **Decision id:** none
- **Related:** `EXPERIMENTS.md` §priority scenarios; `RESULTS.md` §hotspot stability
- **Claim level:** `sensitivity_scenario`

## RQ10: Are the Zimbabwe and Peru sites structurally comparable?

PE1 is now methodologically symmetric to V1 v0.3 — same 6-criteria structure,
same slide-matrix scenario, comparable hotspot-stability output. Physical
contrast is real: PE1 is arid Andean Pacific slope (C=0.61, bare; soil loss
8.74 t/ha/yr) vs V1 semi-humid savanna (C=0.04, shrub/grass; soil loss 0.50).
Final comparison claim remains blocked until harmonized.

- **Decision id:** part of IFPM-D03 / Peru gate
- **Related:** `EXPERIMENTS.md` §Zimbabwe-Peru comparison; `RESULTS.md` §comparison
- **Claim level:** `engineering_pilot` / `sensitivity_scenario`; final claim blocked

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
| A-001 | V1 remains the controlled prototype boundary, not the final thesis boundary. | provisional | V1 outputs |
| A-002 | Coarse rainfall may be used through zonal aggregation or labelled coarse-to-reference-grid resampling. | sensitivity_scenario | CHIRPS/rainfall criteria |
| A-003 | The 2026-06-16 mentor-slide AHP matrix may be used as a sensitivity scenario. | sensitivity_scenario | AHP weights |
| A-004 | Deprecated R/A products remain invalid, but new R-factor families may be generated with fresh lineage. | provisional | R-factor/RUSLE work |
| A-005 | OSM quarry/industrial evidence is a mining activity indicator, not official ASM truth. | diagnostic_only | mining/ASM criterion |
| A-006 | Road proximity is an exposure/access indicator, not socioeconomic vulnerability. | diagnostic_only | exposure criterion |
| A-007 | Peru can run data-readiness and terrain diagnostics in parallel. | diagnostic_only | Peru side |
| A-008 | The Peru Arequipa-Moquegua-Tacna discovery envelope is a discovery aid, not an authoritative boundary. | diagnostic_only | Peru boundary discovery |
| A-009 | PE1 is an engineering-pilot Peru boundary, chosen by a selection rule, NOT a research-value-selected site. | engineering_pilot | Peru terrain chain |
| A-010 | The `rainfall_climatology` criterion (rainfall_sensitivity_v0_3) is a 0.05° CHIRPS rainy-season mean bilinear-resampled to the V1 30 m grid; resampling-edge NoData slivers inside V1 are nearest-EDT filled. Effective resolution ~5 km, NOT native 30 m. | sensitivity_scenario | rainfall criterion |
| A-011 | The hotspot-exposure diagnostic measures spatial co-location of v0.2 stable hotspots with exposure proxies; weak co-location means hotspots reflect natural-pressure overlap, not observed exposure. | diagnostic_only | exposure diagnostic |
| A-012 | The PE1 `rainfall_climatology` criterion mirrors Zimbabwe A-010 (CHIRPS latam Dec-Mar mean, bilinear-resampled to PE1 30 m grid). Effective resolution ~5 km. | sensitivity_scenario | PE1 rainfall criterion |
| A-013 | Zimbabwe ASM is structurally artisanal and scattered; no official footprint exists and none is expected before the mentor's 2026-07-18 conference ask. The OSM quarry/industrial indicator (A-005) remains the current mining layer. | diagnostic_only | Zimbabwe mining criterion |
| A-014 | If Zimbabwe ASM data is not obtainable, the mentor may switch the Zimbabwe site to Voi (Kenya). Voi rainfall is already in managed storage. NOT a current action — strategic fallback only. | contingency | Zimbabwe site / boundary |

## Lineage

Absorbs content from:
- `AGENTS.md` §Modelling Context (recurring open questions)
- `mentor_methodology_slide_interpretation_2026-06-16.md` (Rehab-Potential role, AHP)
- `task_progress_board.md` §Blocked Or Needs Decision (IFPM-D01..D06)
- `rfactor_investigation_consolidated.md` §7 (R-factor open question)
- `assumptions_log.md` (full A-001..A-014 register)
