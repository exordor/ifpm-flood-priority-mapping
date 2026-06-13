# V1 Full Methodology Evidence Sweep Adversarial Review

Status: completed locally. Subagents were not used in this turn; the review was performed as a
local fallback with two angles: domain/correctness and engineering/data governance.

## Domain / Correctness Review

Findings and fixes:

- P2: DFO historical flood data was initially only a source/gap row. Fixed by using the HDX CKAN
  resource to download and process the DFO SHP zip. The output now records 9 Zimbabwe-related
  historical flood records and 0 valid event points inside V1 plus one degree.
- P2: Official protected areas were initially a gap. Fixed by downloading WDPCA Zimbabwe through
  HDX and processing V1 overlap. The output now records 2 overlapping protected/conserved-area
  polygons.
- P2: GHSL was initially discovered but not processed, even though the methodology audit called
  for WorldPop/GHSL/OSM exposure evidence. Fixed by downloading HDX GHSL built-up surface and
  population rasters, clipping them to V1, adding `v1_ghsl_summary.csv`, and adding a GHSL
  cross-check row to the socioeconomic vulnerability evidence matrix.
- P2: JRC `change` and `transitions` layers are categorical codes, not continuous values. Fixed
  by adding interpretation notes that their means should not be interpreted as continuous metrics.
- P2: Rehabilitation potential lacked explicit proximity components. Fixed by generating V1 30 m
  distance and 0-1 proximity rasters for rivers, roads, and weak mining proxy features.

Residual risks:

- DFO is historical event-point/centroid context, not local inundation extent or flood-depth
  validation.
- OSM quarry/industrial features are weak mining proxy evidence, not official active ASM
  footprints.
- WDPCA overlap is environmental context; using it as an AHP criterion still requires mentor or
  domain approval.
- No AHP weights, weighted overlay, flood-risk map, or intervention-priority map were produced.

## Engineering / Data-Governance Review

Findings and fixes:

- P2: The first implementation had a 451-line preparation script, which violated the local
  review-friendly scripting rule. Fixed by splitting it into:
  - `bin/prepare_v1_methodology_raster_layers.py`
  - `bin/prepare_v1_methodology_vector_layers.py`
  - `bin/build_v1_full_methodology_evidence_matrix.py`
  - a short orchestrator, `bin/prepare_v1_full_methodology_evidence.py`
- P2: New real downloads needed registry/preflight closure. Fixed for ESA WorldCover, WorldPop,
  GHSL, JRC Global Surface Water, DFO Global Flood Archive, and WDPCA Zimbabwe.
- P3: `scipy` was required for distance transforms. Recorded as a root `.venv` local tooling
  dependency in the project note, not a public pipeline dependency.

Verification run:

- `.venv/bin/python -m py_compile bin/download_v1_methodology_inputs.py bin/prepare_v1_full_methodology_evidence.py bin/prepare_v1_methodology_raster_layers.py bin/prepare_v1_methodology_vector_layers.py bin/build_v1_full_methodology_evidence_matrix.py bin/plot_v1_full_methodology_evidence.py`
- `bash bin/validate-boundary.sh`
- `git diff --check`
- Requirement audit confirmed all seven methodology factor families are represented in
  `outputs/v1_full_methodology_evidence_sweep/v1_full_methodology_evidence_matrix.csv`.
