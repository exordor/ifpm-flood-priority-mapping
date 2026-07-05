# Research Questions

Status: active. Open scientific and methodological questions, plus the
mentor-gated decisions that block final claims.

Each open question is tagged with the IFPM-DNN decision id (where applicable),
related experiment_ids, related hypotheses, and current claim level.

## RQ1: What is the appropriate R-factor method for semi-arid Zimbabwe?

The deepest open methodological question. Six literature methods run on the same
V1 CHIRPS inputs split into two incompatible families ~6× apart. The only
independent check (ERA5 hourly EI30 lower-bound) sits in the lower range,
questioning the transferability of the high-family formulas. There is no
independent measured EI30 R for the V1 catchment.

To settle: a primary EI30 dataset (sub-daily gauge or GPM IMERG) in or near V1;
or a mentor ruling on which R convention the thesis adopts; or a traceable
original source for the low-R family to resolve its units.

- **Decision id:** (highest-priority open question, no IFPM-D id; surfaced
  via IFPM-080/081/082)
- **Related:** `EXPERIMENTS.md` §R-factor exploration, §ERA5 empirical;
  `RESULTS.md` §R-factor; `HYPOTHESES.md` H-RF-FAMILIES, H-BIMODALITY-ARTIFACT
- **Claim level:** `sensitivity_scenario`; all V1/V2 R and USLE A absolute
  values remain deprecated.

## RQ2: Is the mentor-supplied AHP pairwise matrix the intended project weight set?

The 2026-06-16 slide matrix (CR 0.022) is internally consistent and structurally
aligns with the deliverable pipeline, but the slide labels it "example". It is
recorded as `sensitivity_scenario`, not final weights.

- **Decision id:** IFPM-D04
- **Related:** `HYPOTHESES.md` H-AHP-SLIDE-TRANSFERS
- **Claim level:** `sensitivity_scenario`

## RQ3: Should Rehabilitation Potential be a sixth scored criterion, a post-score
scenario filter, or an output?

The slide lists it as an input layer but omits it from the PIM formula and
matrix. Three options: (A) post-score scenario comparison; (B) sixth criterion
with simplified formula; (C) output/filter rather than AHP criterion.

- **Decision id:** IFPM-D05
- **Related:** none yet built; blocks any rehabilitation-priority output
- **Claim level:** not yet applicable

## RQ4: What is the final modelling unit?

Pixel, HydroBASINS/sub-basin, ANA hydrographic unit, or mixed mask. Controls
normalization, aggregation, and Zimbabwe-Peru comparability.

- **Decision id:** IFPM-D01
- **Related:** `REPRODUCIBILITY.md` §Preprocessing design (model-unit branches)
- **Claim level:** blocks final terrain-rainfall claim

## RQ5: What is the final Zimbabwe (Upper Mzingwane) thesis boundary?

V1 (`HB_L8_1081528840_full_l7_chain`) is `accepted_with_waiver_for_controlled_prototype`.
Final thesis boundary remains open. Comparison layers: Geoportal `Upper Mzingwane`
(~7321.5 km²), HydroBASINS L7 (~3700 km²), the source/geometry-unresolved
~2138 km² literature reference.

- **Decision id:** IFPM-D06
- **Related:** `EXPERIMENTS.md` §boundary discovery; `DECISION_LOG.md` D-V1-WAIVER
- **Claim level:** controlled prototype only

## RQ6: What is the Peru boundary rule?

Administrative regions, hydrographic units, or clipped hydrological units. PE1
is an engineering pilot, not a research-selected site. Avoids catchment-vs-
region bias.

- **Decision id:** IFPM-D02
- **Related:** `EXPERIMENTS.md` §Peru PE1 chain; `DECISION_LOG.md` D-PE1-PILOT
- **Claim level:** `engineering_pilot`

## RQ7: What evidence hierarchy supports validation or calibration?

Determines whether outputs are susceptibility maps, risk maps, or intervention
maps. Current validation data is effectively zero (EM-DAT country profile only;
GloFAS downgraded as not publicly accessible; no in-situ flood-impact data).

- **Decision id:** IFPM-D03
- **Related:** `RESULTS.md` §exposure diagnostic
- **Claim level:** blocks any validated-claim output

## RQ8: How should mining concessions, cadastre records, and active disturbance be separated?

Avoids treating mining rights as active mining footprints. Zimbabwe ASM is
structurally artisanal and scattered; no official footprint exists (A-013).
Peru has the public INGEMMET/GEOCATMIN Pequeña Minería cadastre (strictly
stronger than Zimbabwe's OSM-only proxy).

- **Decision id:** IFPM-D05 (overlaps RQ3 role)
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
