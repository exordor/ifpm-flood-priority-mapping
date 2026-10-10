# IFPM Flood Risk Modelling Workspace

> New to this project? Start with [HANDOVER.md](HANDOVER.md) (handover
> note, 2026-10-08). It summarises the current state, directory map and next steps.

The root repository is the research workspace (scripts in `bin/`, docs in `context/`, local `data/` and `outputs/`); `ifpm-flood-pipeline/` is the reusable code package.

Active cases: Secocha (Peru) and Goslar (Germany). Zimbabwe is a background case.

- **Secocha, Arequipa, Peru** (`peru_secocha_a7367_reference_extent_v1`): a provisional 30 km² reference window, not a catchment; see `context/docs/research-map/EXPERIMENTS.md` for detail.
- **Goslar, Germany** (Abzucht and the multi-river comparison under `outputs/goslar_multiriver_full_extent_v1/`): compares the priority index with official flood zones.

The former Peru area `peru_hybas_l7_6070641200` is a frozen baseline. Its outputs are kept under `outputs/srtm_1arcsec_peru_pilot/` and must not receive new runs.

## Directory Structure

See the directory map in [HANDOVER.md](HANDOVER.md) §3.

## Document Navigation

- [Experiments](context/docs/research-map/EXPERIMENTS.md): current experiments, commands and results.
- [Decision log](context/docs/research-map/DECISION_LOG.md): decisions in force, including weights.
- [Dataset registry](context/docs/data-management/registry/): source and licence per dataset.
- [Terminology](context/docs/glossary.md).
- [Internal context](context/README.md): what is kept under `context/`.
- [Local tooling](bin/README.md): processing and verification entry points.
