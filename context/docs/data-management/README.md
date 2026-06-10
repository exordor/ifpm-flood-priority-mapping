# IFPM Data Management Notes

This folder contains internal templates for managing real IFPM dataset downloads.

Use these files before downloading GIS, raster, vector, validation, or sample data. Every real
download should have at least a minimal registry note, even if it is exploratory or not meant to
be reused.

- `dataset_registry_template.md`: reusable metadata template for each dataset.
- `download_preflight_checklist.md`: checklist to complete before each download.
- `registry/`: dataset-specific registry notes.
- `preflight/`: dataset-specific download preflight notes.

Before moving from notes to any real download, also check the cross-dataset gate in
`context/docs/project-management/real_data_execution_preflight_gate.md`.

Real downloaded data must stay outside this folder. Store it under ignored workspace paths such
as `data/`, keep processed outputs under `outputs/`, and keep packaged bundles under `exports/`.
