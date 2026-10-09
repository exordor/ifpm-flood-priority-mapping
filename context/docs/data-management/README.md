# IFPM Data Management Notes

This folder contains internal templates for managing real IFPM dataset downloads.

Use these files before downloading GIS, raster, vector, validation, or sample data. Every real
download should have at least a minimal registry note, even if it is exploratory or not meant to
be reused.

- `registry/`: dataset-specific registry notes (the authoritative record).

Templates, preflight notes, reference-grid rules and archived candidates were
removed in the 2026-10-08 handover cleanup; retrieve them from Git history if
needed.

Before moving from notes to any real download, also check the cross-dataset gate in
`context/docs/research-map/REPRODUCIBILITY.md` (§3 Real-data execution preflight gate).

Real downloaded data must stay outside this folder. Store it under ignored workspace paths such
as `data/`, keep processed outputs under `outputs/`, and keep packaged bundles under `exports/`.
