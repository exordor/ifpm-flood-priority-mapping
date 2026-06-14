# P1 Risk R1.3 AHP Weighting Decision Package

Date: 2026-06-15

Status: internal decision package. This document does not authorize any AHP overlay,
flood-risk interpretation, or intervention-priority interpretation on real data. It proposes a
structured expert-elicitation protocol, a blank comparison template, and an explicitly
non-authoritative illustrative prior. No weights in this package may be used to generate
interpretable project outputs.

## Risk Statement

R1.3 (P1): AHP weights have no expert source.

Current evidence baseline:

- The only weight matrix in the deliverable code is
  `ifpm-flood-pipeline/configs/example_pairwise_matrix.csv`, a synthetic test fixture.
- No expert pairwise comparisons have been collected.
- No documented weighting protocol exists.
- No sensitivity-analysis scenario has been defined (IFPM-038 in backlog).
- Multi-level progress review P2-2 explicitly warned: "the synthetic sample matrix becomes de
  facto expert judgment" if no first-slice AHP protocol exists before any real output is
  interpreted.

Consequence: any real-data overlay run with current weights would produce a plausible-looking
but scientifically unjustified priority map. Per the project analysis note, the HiWi must not
independently decide criterion weights; doing so would make the output indefensible to the mentor
and to reviewers.

## Why This Cannot Be Self-Resolved

Per AGENTS.md and the project analysis note:

- AHP weights encode expert judgment, stakeholder values, and literature evidence. They are not
  derivable from data alone.
- The HiWi can implement the calculation, consistency check, and sensitivity tooling, but cannot
  supply the judgment.
- The methodology figure treats AHP Criteria Hierarchy Development and Pairwise Comparison of
  Criteria and Sub-Criteria as expert tasks.

This package therefore prepares the elicitation instrument and procedure, and an explicitly
non-authoritative structural prior that must be replaced before any real overlay.

## Proposed Elicitation Protocol (Summary)

Full protocol and blank template:
`context/docs/mentor-explanation/AHP_Elicitation_Protocol_And_Template_2026-06-15.md`.

Key elements:

1. Criteria hierarchy confirmation: confirm the 7-criteria PIM hierarchy is still the intended
   set, OR record a revised hierarchy after V1 evidence sweep and the R1.2 mining-data
   decision. If R1.2 falls back to a reduced criteria set, the hierarchy must change before
   elicitation.
2. Expert panel composition: mentor plus any domain experts or stakeholders the mentor nominates.
3. Pairwise comparison procedure: each expert fills the Saaty 1-9 upper-triangle matrix
   independently.
4. Aggregation rule: geometric mean of individual judgments (the standard Saaty group-aggregation
   rule). Record each expert's matrix so sensitivity to aggregation can be audited.
5. Consistency review: compute CR; if CR > 0.1, return the matrix to the expert for revision
   with the most inconsistent pairs flagged. Document any waiver.
6. Sensitivity analysis (IFPM-038): perturb each weight by +/-20% (and run a one-at-a-time
   leave-one-criterion-out test) and report rank-reversal in the V1 priority classes.

## Illustrative Structural Prior (NON-AUTHORITATIVE)

The elicitation template file contains an illustrative structural prior derived from the
methodology figure's three-tier decomposition (Flood Hazard Criteria, Vulnerability & Exposure,
Post-Mining Opportunity & Value) translated into a Saaty matrix. It is flagged
NON-AUTHORITATIVE and must NOT be used to generate interpretable outputs. Its only legitimate use
is as a conversation starter for the expert elicitation session, so the expert can react to a
concrete starting point rather than a blank page.

Hard rules for the illustrative prior:

- It must never be the basis of a real-data overlay that gets interpreted.
- It must never be copied into `ifpm-flood-pipeline/configs/` as if it were a project matrix.
- It must be replaced by the elicited expert matrix before any V1 priority map is produced.
- Any use of it in a synthetic smoke test must label the output as a workflow diagnostic.

## Claim Boundary Fallback (Important)

If expert elicitation cannot be completed before the thesis deadline:

- Keep the AHP/overlay pipeline runnable on synthetic data only.
- Label any real-data run as a synthetic-weight workflow diagnostic, not a priority map.
- Do not publish, present, or interpret real-data priority classes as project findings.
- In public-facing docs, state that criterion weights were not expert-elicited within the project
  window and that all shown outputs are synthetic or diagnostic.

This fallback is consistent with the AGENTS.md modelling-claim boundary and is the recommended
default unless the mentor completes or delegates the elicitation.

## Decision Questions For Mentor

1. Will the mentor supply the pairwise comparison matrix for the (confirmed or revised) criteria
   hierarchy, or nominate domain experts to do so?
2. Is the 7-criteria PIM hierarchy still intended, or should it be revised given the V1 evidence
   sweep and the R1.2 mining-data decision?
3. What CR threshold does the mentor require (the pipeline defaults to 0.1)?
4. Does the mentor want a group elicitation (multiple experts aggregated by geometric mean) or a
   single expert matrix?
5. What sensitivity scenarios should accompany the first real-data run (IFPM-038)?

## Boundaries And Blockers

- No real-data AHP overlay is authorized by this document.
- The illustrative prior must not enter `configs/`, `examples/`, or any release archive.
- Elicitation must follow the recorded protocol; ad-hoc weights from a single informal conversation
  are not sufficient for an interpretable output.
- Claim-boundary fallback applies to public docs and interpretation only.

## Cross-References

- Risk source: `p1_risk_overview_2026-06-15.md`.
- Elicitation instrument: `AHP_Elicitation_Protocol_And_Template_2026-06-15.md`.
- Preflight gate: `real_data_execution_preflight_gate.md` (IFPM-D04 AHP weighting protocol,
  Gate G7 engineering readiness).
- Pipeline code: `ifpm-flood-pipeline/src/ifpm_flood_pipeline/ahp.py`,
  `ifpm-flood-pipeline/configs/example_pairwise_matrix.csv`.
- Decision tasks: IFPM-D04 (AHP weighting protocol), IFPM-038 (first-slice AHP weighting and
  sensitivity plan), IFPM-063 (this package).
