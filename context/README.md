# IFPM Private Context

This directory contains internal project context for Codex-assisted reasoning and document
preparation.

It is not a deliverable code repository.

## Contents

- `docs/original/`: original dataset inventory Markdown source and local binary references.
- `docs/research-review/`: reviewed dataset inventory and methodology notes.
- `docs/deep-research/`: fact-checking and mentor-requirement review.
- `docs/data-management/`: dataset download registry templates and preflight checks.
- [Research map](docs/research-map/README.md): current scope, experiments, results and execution rules.
- [Project-management archive](docs/project-management/README.md): historical plans only, superseded by the research map.
- `docs/mentor-explanation/`: dated mentor packets, source slide records and reusable templates; check the current research scope before reusing older wording.
- `docs/project-analysis/`: workflow retrospectives; the initial project analysis is in the project-management archive.
- `references/`: reference papers (PDFs ignored by Git).

## Rule

Future code should not import, symlink, or depend on files here. If a context point needs to be
released, rewrite it into a public-safe document under `ifpm-flood-pipeline/docs_public/`.
