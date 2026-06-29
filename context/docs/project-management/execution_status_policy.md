# IFPM Execution Status Policy

Date: 2026-06-29

Status: active internal execution policy.

## Core Rule

Uncertainty reduces claim level; it does not automatically pause execution.

If a scientific choice is uncertain, continue with a labelled diagnostic, provisional, or
sensitivity scenario. Record the assumption, method lineage, source data, and output status. Do
not present the result as a final scientific claim.

## Output Status Levels

Every generated output should declare or inherit one status level:

| status | meaning | allowed use |
|---|---|---|
| `diagnostic_only` | tests code, data readiness, or processing logic | internal QA, debugging, method development |
| `provisional` | defensible for controlled prototype work but not fully validated | internal prototype and mentor discussion |
| `sensitivity_scenario` | compares assumptions, weights, thresholds, formulas, or data families | robustness and method-choice review |
| `mentor_review_ready` | concrete figure/table/map suitable for mentor feedback | mentor review; not final thesis claim |
| `final_claim` | validated and explicitly approved scientific result | thesis/public claim only |

Only `final_claim` requires full validation and explicit approval. Most current IFPM outputs should
be `diagnostic_only`, `provisional`, or `sensitivity_scenario`.

## No-Pause Rule

Do not pause work merely because mentor confirmation would improve scientific confidence.

Pause only when:

- required inputs are missing and no diagnostic/provisional substitute is possible;
- code cannot run and the exact error has been documented;
- continuing would overwrite or corrupt existing valid outputs;
- credentials, licences, or storage rules prevent safe execution;
- the user explicitly asks to pause.

Mentor confirmation is a reason to downgrade status, not a reason to stop execution.

## Rainfall / CHIRPS Rule

CHIRPS and other coarse rainfall products must not be described as native 30 m information.

Rainfall-derived metrics may enter diagnostic, provisional, or sensitivity MCDA experiments through:

- catchment or sub-basin zonal aggregation; or
- explicit coarse-to-reference-grid resampling for overlay compatibility.

Required metadata:

- native resolution;
- target grid or aggregation unit;
- resampling or aggregation method;
- effective-resolution warning;
- source lineage;
- status / claim level.

Do not block rainfall criteria only because CHIRPS is coarse. Block only unsupported claims that
treat coarse rainfall as true 30 m rainfall evidence.

## AHP Rule

AHP matrices from mentor slides, meetings, or documented project material may be used as
`sensitivity_scenario` inputs.

They must not be named or described as final approved weights unless explicitly confirmed.

Required metadata:

- source;
- date;
- criteria order;
- pairwise matrix or derived weights;
- consistency ratio;
- status / claim level.

## R-Factor Rule

Known-invalid R/A products remain deprecated.

New R-factor products may be generated as provisional or sensitivity scenarios if method, source,
value range, uncertainty, and lineage are documented. Waiting for mentor confirmation should not
pause all R-factor work.

## Peru Rule

Peru work may run in parallel for:

- data inventory;
- terrain indicators;
- rainfall/land-cover availability checks;
- diagnostic readiness reports.

Final Zimbabwe-Peru comparison remains blocked until both countries share harmonized criteria,
normalization, thresholds, and claim rules.

## Global Scope Statement

This repository produces AHP-MCDA-based flood, sediment, and intervention-priority prototype
outputs. These are susceptibility/prioritization products, not hydrodynamic inundation
simulations. Diagnostic and provisional outputs are intended for internal review and method
development only.
