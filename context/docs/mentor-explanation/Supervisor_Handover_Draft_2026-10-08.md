# IFPM handover to Supervisor

Draft prepared on 8 October 2026. File transfer and receipt are not yet confirmed.

Supervisor,

My contract has ended, and I am handing over the IFPM work completed so far. I am no longer responsible for continuing the project. I have organised the available material below so that you or the next researcher can locate the results, understand their limits, and continue from the existing work.

I have working flood-prioritisation prototypes for Secocha and Goslar, together with maps, source records, processing scripts and diagnostic comparisons. These are weighted indicator maps, not a validated flood-prediction model. The most important unresolved issue is the relationship between the combined priority score and flood evidence: in the expanded Goslar comparison, the flood indicator is higher inside all eight regulatory river zones than in their surrounding 1 km rings, but the combined score is higher in only three.

## What I am handing over

| Material | What it provides | Current limitation |
|---|---|---|
| Secocha prototype | Five scored criteria, weighted priority map, separate mining context, and historical-event evidence | The approximately 30 km² study window is a map reference extent, not a catchment or observed event footprint. The result is provisional. |
| Goslar comparison and sensitivity results | Expanded coverage of eight regulatory river zones and six hydraulic scenarios; flood weights of 34%, 50%, 60% and 70%; tables explaining criterion contributions | These are diagnostic comparisons. Regulatory or modelled flood zones are not observed event footprints, and weight changes do not establish predictive accuracy. |
| Existing presentation and QGIS sharing package | Editable slides, review and audit QGIS projects, Excel references and editable diagrams | The package is dated 18 August. It predates the September Goslar work and should be used with the newer results, not described as a complete final handover. |
| Processing scripts and source records | Local analytical workflow, input provenance, output manifests and checks | Reproduction needs the local data and output dependencies as well as the code. A clean-machine reproduction has not been established by this handover preparation. |
| Independent deliverable repository | Minimal reusable pipeline and synthetic examples/tests | This is a separate code scaffold; it does not contain the full real-data research workspace. |

## How I suggest reading the results

I would start with the existing review QGIS projects for orientation, then read the expanded Goslar comparison and its contribution tables. The expanded comparison covers approximately 739 km² and all 14 retained official products. Having a combined score throughout the evaluation area does not mean every component has complete evidence.

The retained Secocha and expanded Goslar run manifests both record top-level weights of 34% flood, 25% soil-erosion factors, 17% land-cover pressure, 10% environmental indicators and 14% socioeconomic indicators. Some overview documents still describe older weights. For these specific results, the run manifests identify the weights actually recorded with the outputs; this does not make them final approved scientific weights.

I would keep the following limits with any further presentation:

- The combined index measures several priorities. A low combined score does not establish low inundation risk. The score boundary of 0.6 is a display/classification choice, not a validated flood threshold.
- Mining is a separate context overlay in these runs. It is not independent validation of flood performance.
- Coarse rainfall and soil inputs retain their effective source resolution even when aligned to a 30 m grid.
- Missing component evidence and available-component reweighting need to remain visible. Missing data must not be interpreted as an absence of people or as low risk.
- Some legacy field names are broader than the evidence: tree-cover decline is a vegetation-loss proxy, and static proximity does not measure expansion. The September semantics notes explain these distinctions.
- The earlier Peru area and Zimbabwe work remain background/provenance. Known-invalid older rainfall-erosivity and soil-loss products must not be reused as accepted results.

## Work remaining after transfer

The next researcher will need to decide how the combined priority index should be evaluated against flood evidence, preserve an independent evaluation source if weights are tuned, and review component coverage and proxy meanings. The handover snapshot includes the September results, but testing the transferred materials on the recipient's machine remains outstanding. These are outstanding project tasks, not commitments for me to undertake after the end of my contract.

## File locator for the receiving researcher

Paths below are relative to `02_Research_Workspace/` inside the handover package, except the first row, which starts from the package root. They are local locations, not download links. This draft does not mean the files have already been transferred.

| Start here | Relative location |
|---|---|
| Existing sharing package (from package root) | `01_Review_August_Snapshot/README.txt` |
| Secocha review project | `outputs/peru_secocha_qgis_project_package_compact/IFPM_Peru_Secocha_ReviewMap.qgz` |
| Goslar review project | `outputs/goslar_qgis_project_package_compact/IFPM_Goslar_ReviewMap.qgz` |
| Newer Goslar comparison, currently explained in Chinese | `outputs/goslar_multiriver_full_extent_v1/frozen_scale_v1/READING_NOTE.md` |
| Goslar criterion contributions | `outputs/goslar_multiriver_full_extent_v1/frozen_scale_v1/criterion_comparison.csv` |
| Goslar component coverage | `outputs/goslar_multiriver_full_extent_v1/frozen_scale_v1/component_coverage.csv` |
| Goslar stored validation report | `outputs/goslar_multiriver_full_extent_v1/frozen_scale_v1/validation.json` |
| Goslar source/run lineage | `outputs/goslar_multiriver_full_extent_v1/frozen_scale_v1/expansion_manifest.json` |
| Goslar recorded weights | `outputs/goslar_multiriver_full_extent_v1/frozen_scale_v1/chain/priority_scenarios/run_manifest.json` |
| Secocha recorded weights | `outputs/peru_secocha_a7367_reference_extent_v1/priority_scenarios/run_manifest.json` |
| Secocha stored grid and coverage checks | `outputs/peru_secocha_a7367_reference_extent_v1/quality_assurance/chain_validation.json` |
| Secocha event-evidence files | `outputs/secocha_2023_validation/` |
| Dataset sources and access conditions | `context/docs/data-management/registry/` |
| Experiment history, including September changes | `context/docs/research-map/EXPERIMENTS.md` |
| Root runtime dependencies | `pyproject.toml` |
| Separate deliverable code | `ifpm-flood-pipeline/README.md` |

Keep each QGIS package folder intact, including its data and styles. The review projects are orientation material; their inclusion of the September extension has not been verified. Use the newer Goslar output directory directly for those results.

### Technical reproduction pointers

The existing experiment records give the following commands, run from the workspace root with its local Python environment and required inputs present:

```sh
.venv/bin/python bin/analysis/run_goslar_multiriver_full.py
.venv/bin/python bin/analysis/report_goslar_multiriver_full.py
.venv/bin/python bin/validate/validate_peru_secocha_chain.py
```

The first two commands regenerate results and the third rewrites its validation report. I have not rerun these commands as part of preparing this draft. Stored validation reports record successful checks for both output groups; they do not establish scientific validation or successful reproduction on another machine. Do not use older quick-start commands targeting the frozen former Peru output tree.

The working tree contains substantial uncommitted and untracked research work. A Git clone alone will not reproduce this local state, and ignored data/output folders also need a deliberate transfer. Preserve the root research workspace and independent deliverable repository separately. Transfer only the agreed project materials, with source access and redistribution conditions retained; private contextual notes are not a public release package.

### Transfer status

This is a draft inventory and explanation. The transfer destination, selected files, recipient access and successful opening on Supervisor's machine remain unconfirmed. The contract end date is not specified here beyond the statement that the contract has ended. No future support period is promised.
