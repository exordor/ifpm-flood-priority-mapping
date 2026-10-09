# IFPM Private Context

This directory contains internal project context for Codex-assisted reasoning and document
preparation.

It is not a deliverable code repository.

## Contents

- [Research map](docs/research-map/README.md): current scope, experiments, results, decisions and execution rules.
- `docs/data-management/registry/`: one note per dataset with source, version, access date and licence.
- `docs/glossary.md`: terminology.
- `docs/methodology/pim_transformation_flow.md`: PIM transformation flow (Chinese).
- `docs/mentor-explanation/`: English handover draft and email draft for Supervisor (read by
  `bin/package/build_supervisor_handover.py`).
- `configs/`: Zimbabwe criteria-stack config read by `bin/` scripts.

Mentor messages, early reviews, superseded plans and archives were removed in the
2026-10-08 handover cleanup; retrieve them from Git history if needed.

## Rule

Future code should not import, symlink, or depend on files here. If a context point needs to be
released, rewrite it into a public-safe document under `ifpm-flood-pipeline/docs_public/`.
