# IFPM Flood Risk Modelling Workspace

This workspace uses a split boundary:

- the root Git repository is the private context/document repository;
- `ifpm-flood-pipeline/` is an independent deliverable code repository with a minimal
  synthetic-tested pipeline. Real-data use remains gated.

The current project mainline is Peru-first flood prioritisation modelling. The
working Peru case is:

- Arequipa Region, Peru — mainly the Vitor-La Joya-Santa Rita de Siguas
  catchment west of Arequipa city

Upper Mzingwane Catchment, Zimbabwe remains a secondary/background comparison
case and method-development baseline, but the active result sequence should now
lead with Peru.

## Directory Structure

```text
context/
  docs/
    original/             Original dataset inventory files.
    research-review/      Reviewed dataset inventory with dataset links and method notes.
    deep-research/        Deep research fact-check report on mentor requirements and review quality.
    data-management/      Internal dataset download registry templates and preflight checks.
    project-management/   Archive-only since 2026-07-05. Live research-governance is in research-map/.
    research-map/         Research map: experiments, results, decisions, reproducibility, hypotheses.
    project-analysis/     IFPM HiWi project analysis notes and workflow retrospectives.
    mentor-explanation/   Chinese and English oral explanation guides for mentor discussion.
  assets/
    images/               Supporting generated images.

ifpm-flood-pipeline/
  src/                     Minimal deliverable pipeline code.
  tests/                   Tests for the code repository.
  configs/                 Public-safe sample configs.
  examples/                Synthetic or approved public examples.
  docs_public/             Client/mentor-facing technical docs.
```

## Context Documents

- `context/docs/glossary.md` (shared term reference: maps internal code names to mentor-facing
  words; read before writing any mentor-facing text)
- `context/docs/original/Detailed_Dataset_Inventory_Zimbabwe_Peru.md`
- `context/docs/research-review/Detailed_Dataset_Inventory_Zimbabwe_Peru_research_review.md`
- `context/docs/deep-research/Deep_Research_Fact_Check_Mentor_Requirements.md`
- `context/docs/data-management/dataset_registry_template.md`
- `context/docs/data-management/download_preflight_checklist.md`
- `context/docs/data-management/registry/`
- `context/docs/data-management/preflight/`
- `context/docs/research-map/README.md` — research-governance framework (index)
- `context/docs/research-map/EXPERIMENTS.md` — experiment registry (replaces task_progress_board)
- `context/docs/research-map/RESULTS.md` — results synthesis (replaces rfactor_investigation_consolidated)
- `context/docs/research-map/REPRODUCIBILITY.md` — preflight gate + preprocessing design + claim-level ladder
- `context/docs/research-map/RESEARCH_QUESTIONS.md` — open questions + A-001..A-015 assumption register
- `context/docs/research-map/DECISION_LOG.md` — why each major choice was made
- `context/docs/research-map/HYPOTHESES.md` — testable claims with verdicts
- `context/docs/research-map/ARTIFACT_INDEX.md` — code / dataset / figure / config index
- `context/docs/project-management/_archive/superseded_process_notes_2026-06/outlet_based_catchment_research_plan_2026-06-11.md`
- `context/docs/project-management/_archive/superseded_process_notes_2026-06/multi_level_progress_review_2026-06-10.md`
- `context/docs/project-management/_archive/superseded_boundary_exploration_2026-06/hydrosheds_boundary_discovery_result_2026-06-10.md`
- `context/docs/project-management/_archive/superseded_boundary_exploration_2026-06/upper_mzingwane_boundary_decision_record_2026-06-10.md`
- `context/docs/project-management/_archive/superseded_process_notes_2026-06/zimbabwe_geoportal_subcatchments_boundary_comparison_2026-06-10.md`
- `context/docs/project-management/_archive/superseded_boundary_exploration_2026-06/upper_mzingwane_boundary_fact_check_2026-06-10.md`
- `context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/p1_risk_overview_2026-06-15.md`
- `context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/p1_validation_data_decision_package_2026-06-15.md`
- `context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/p1_mining_data_decision_package_2026-06-15.md`
- `context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/p1_ahp_weighting_decision_package_2026-06-15.md`
- `context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/p2_risk_overview_2026-06-15.md`
- `context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/p2_modelling_unit_decision_package_2026-06-15.md`
- `context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/p2_hydrology_derivatives_decision_package_2026-06-15.md`
- `context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/p2_sediment_risk_decision_package_2026-06-15.md`
- `context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/p2_peru_side_decision_package_2026-06-15.md`
- `context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/p2_boundary_acceptance_decision_package_2026-06-15.md`
- `context/docs/mentor-explanation/Mentor_Oral_Explanation_Zimbabwe_Peru_Flood_Risk_en.md`
- `context/docs/mentor-explanation/Mentor_Oral_Explanation_Zimbabwe_Peru_Flood_Risk_zh.md`
- `context/docs/mentor-explanation/Mentor_Next_Step_Summary_IFPM_2026-06-10.md`
- `context/docs/mentor-explanation/Upper_Mzingwane_Boundary_Decision_Package_2026-06-10.md`
- `context/docs/mentor-explanation/Mining_Data_Access_Request_Template_2026-06-15.md`
- `context/docs/mentor-explanation/AHP_Elicitation_Protocol_And_Template_2026-06-15.md`
- `context/docs/mentor-explanation/Mentor_Decision_Briefing_2026-06-15.md`
- `context/docs/mentor-explanation/Mentor_Teams_Messages_2026-06-15.md`
- `context/docs/mentor-explanation/STYLE.md`
- `context/docs/mentor-explanation/Mentor_RFactor_Figure_Send_Packet_2026-06-19.md`
- `context/docs/project-analysis/IFPM_HiWi_Project_Analysis.md`
- `context/docs/project-analysis/AI_Research_Document_Generation_Lessons_Learned.md`

## Boundary Rules

- Keep exploratory notes, mentor-meeting preparation, dataset review, open modelling questions,
  and generated images under `context/`.
- Put future reusable code only under `ifpm-flood-pipeline/`.
- Do not make code depend on files in `context/`.
- Do not put private notes, mentor strategy, raw/derived GIS data, local paths, or unresolved
  assumptions into the deliverable code repository.
- Store raw data, processing outputs, and export packages under ignored local directories such
  as `data/`, `outputs/`, and `exports/`.

## Existing Document Families

- `context/docs/original/`
  original dataset inventory files.
- `context/docs/research-review/`
  reviewed and expanded research inventory with dataset links and methodology notes.
- `context/docs/deep-research/`
  fact-checking of mentor requirements and review quality.
- `context/docs/data-management/`
  internal templates for dataset download registry notes and download preflight checks.
- `context/docs/project-management/`
  archive-only since 2026-07-05 (live research-governance moved to `research-map/`).
- `context/docs/research-map/`
  research-governance framework: experiments, results, decisions, reproducibility,
  hypotheses, artifact index, and todo.
- `context/docs/mentor-explanation/`
  English and Chinese oral explanation guides for mentor discussion.
- `context/docs/project-analysis/`
  project analysis notes and workflow retrospectives.

## Notes

- Markdown files are the version-managed source documents.
- Generated binary formats such as `.docx` and `.pdf` are ignored and can be exported again when
  the Markdown source is stable.
- The root repository should remain private. Release packages should come only from
  `ifpm-flood-pipeline/` after public-safe review.
