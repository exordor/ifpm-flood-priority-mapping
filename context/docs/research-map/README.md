# IFPM Research Map

This folder is the canonical research-navigation layer for the IFPM flood-risk
modelling workspace. It replaces the older `project-management/` planning notes
with the standard research-governance structure: research questions, hypotheses,
experiments, results, artifacts, decisions, and reproducibility.

The old `project-management/` folder was removed in the 2026-10-08 handover
cleanup; its files remain in Git history.

## File index

All nine files listed below are **active**. Three are binding **control files**
named in AGENTS.md and must stay consistent with the codebase and each other.
The remaining six, including this README, are derived working documents and
indexes fed by the experiments and decisions recorded in the control files.

| File | Role | Tier |
|---|---|---|
| `README.md` | this index | active (derived) |
| `RESEARCH_OVERVIEW.md` | what the project is researching, scope, current status | **control** (named in AGENTS.md) |
| `REPRODUCIBILITY.md` | environment, runbook, preflight gate, claim-level ladder, grid rules | **control** (named in AGENTS.md) |
| `EXPERIMENTS.md` | master registry of every `experiment_id` joined to IFPM-NNN task IDs | **control** (named in AGENTS.md) |
| `RESEARCH_QUESTIONS.md` | open scientific and methodological questions, defaults-taken register, A-001..A-015 assumption register | active (derived) |
| `HYPOTHESES.md` | testable claims with verdicts (supported / rejected / unresolved) | active (derived) |
| `RESULTS.md` | per-experiment observation / evidence / interpretation, claim level | active (derived) |
| `ARTIFACT_INDEX.md` | index of code, datasets, figures, prompts, configs (keep / archive / delete) | active (derived) |
| `DECISION_LOG.md` | why each major choice was made (context / decision / reason / alternatives) | active (derived) |

The three control files (`RESEARCH_OVERVIEW`, `REPRODUCIBILITY`, `EXPERIMENTS`)
plus the workspace `AGENTS.md` and root `README.md` are the small set that must
agree on scope, status, claim-level vocabulary, and the active experiment list.
The six derived files are updated as work happens; they may lag the control
files but must not contradict them.

## How to read this folder

- Start at `RESEARCH_OVERVIEW.md` for project scope and status.
- Use `EXPERIMENTS.md` as the master registry; every `experiment_id` cited in
  `RESULTS.md`, `HYPOTHESES.md`, or `DECISION_LOG.md` is defined there.
- `REPRODUCIBILITY.md` holds the binding execution rules (preflight gate,
  claim-level ladder, grid compatibility, preprocessing design).
- All claim language follows the `claim_level` ladder defined in
  `REPRODUCIBILITY.md` (diagnostic_only → provisional → sensitivity_scenario →
  mentor_review_ready → final_claim).

## Adjacent canonical sources (not duplicated here)

- Dataset registries: `context/docs/data-management/registry/*.md` (one per
  dataset; the authoritative provenance record).
- Per-output handoffs and manifest CSVs: `outputs/<experiment_id>/handoff.md`,
  `outputs/<experiment_id>/*_manifest.csv`.
- Pipeline code and DAG runner: `bin/` and `bin/README.md`.
- Deliverable pipeline: `ifpm-flood-pipeline/`.

## Lineage

Created 2026-07-05 by consolidating these source files (removed from the working
tree on 2026-10-08; still in Git history):
`task_progress_board.md`, `assumptions_log.md`, `rfactor_investigation_consolidated.md`,
`real_data_execution_preflight_gate.md`, `real_data_preprocessing_design.md`,
`execution_status_policy.md`, `mentor_methodology_slide_interpretation_2026-06-16.md`,
`project_objective_calibration_2026-07-02.md`, `july18_deliverable_scope_2026-07-02.md`,
`boundary_v1_criteria_stack_v0_2_2026-06-29.md`, `terminology_audit_2026-07-02.md`,
and the old `project-management/README.md` index.

The completed old-area Peru PIM refresh plan is in Git history only. Its commands target the frozen former Peru baseline and must not
be used as current execution instructions.
