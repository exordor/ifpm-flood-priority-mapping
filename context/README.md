# IFPM Private Context

This directory contains internal project context for Codex-assisted reasoning and document
preparation.

It is not a deliverable code repository.

## Contents

- `docs/original/`: original dataset inventory Markdown source and local binary references.
- `docs/research-review/`: reviewed dataset inventory and methodology notes.
- `docs/deep-research/`: fact-checking and mentor-requirement review.
- `docs/data-management/`: dataset download registry templates and preflight checks.
- `docs/project-management/`: internal task progress boards and planning notes.
- `docs/mentor-explanation/`: English and Chinese oral explanation guides.
- `docs/project-analysis/`: IFPM HiWi project analysis and workflow retrospectives.
- `assets/images/`: generated images used in internal documents.

## Rule

Future code should not import, symlink, or depend on files here. If a context point needs to be
released, rewrite it into a public-safe document under `ifpm-flood-pipeline/docs_public/`.
