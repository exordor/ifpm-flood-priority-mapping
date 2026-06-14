# P1 Risk R1.1 Validation Data Decision Package

Date: 2026-06-15

Status: internal decision package. This document does not authorize any download, AHP overlay,
flood-risk interpretation, or validation claim. It inventories candidate validation sources,
assesses their realistic V1 coverage, drafts public-safe preflight scaffolding, and proposes a
claim-boundary fallback if local validation evidence cannot be closed.

## Risk Statement

R1.1 (P1): validation evidence for V1 is effectively zero.

Current evidence baseline:

- DFO Global Flood Archive: 9 Zimbabwe-related records, 0 valid event points inside V1 plus one
  degree. Centroid/point context only, not inundation extent.
- Geoportal Flood Prone Zones: 0 features intersecting the V1 review envelope.
- No EM-DAT, Copernicus EMS, or GloFAS ingestion. IFPM-033 (validation-event ingest design)
  remains in backlog.
- No historical flood-extent polygons, sediment observations, turbidity records, or published
  sediment-yield studies ingested.
- No citizen-science flood/erosion/blocked-culvert/sediment-deposition/infrastructure-impact
  points.

Consequence: without validation, deliverables must be labelled priority/suitability maps, not
validated flood-risk maps. Most thesis-level and publication-level validity requirements cannot
be met from current evidence.

## Candidate Validation Source Inventory

Each source is classified by access tier, expected V1 coverage, and validation strength.

### Tier A: Public, low cost, likely low V1 spatial precision

#### EM-DAT (CRED International Disaster Database)

- Access: public via HDX and direct API; CC BY-NC-SA 4.0 for non-commercial use.
- Spatial precision: country-level admin-1 at best; usually national entries only.
- Temporal: 1900-present, structured disaster events.
- Realistic V1 strength: weak for spatial validation, useful for temporal/magnitude context and
  for confirming whether large flood events occurred in Matabeleland South during the CHIRPS
  window.
- Preflight scaffolding: drafted under
  `context/docs/data-management/registry/emdat_public_validation_candidate.md` and
  `context/docs/data-management/preflight/emdat_public_validation_candidate.md`.

#### GloFAS (Copernicus Global Flood Awareness System)

- Access: public via CEMS Climate Data Store; Copernicus licence (free, cite source).
- Spatial precision: river network cells at about 0.1 degree; reaches and catchment outlets only,
  not overland inundation.
- Temporal: reanalysis 1979-present plus seasonal forecasts.
- Realistic V1 strength: moderate for outlet-scale discharge exceedance events; can corroborate
  whether the V1 outlet saw return-period discharge events. Weak for spatial flood extent.
- Preflight scaffolding: drafted under
  `context/docs/data-management/registry/glofas_public_validation_candidate.md` and
  `context/docs/data-management/preflight/glofas_public_validation_candidate.md`.

### Tier B: Public, medium cost, requires processing (strongest public candidate)

#### Sentinel-1 SAR flood extent (event-based)

- Access: public via Copernicus Open Access Hub, ASF Vertex, or Microsoft Planetary Computer.
- Spatial precision: 10-20 m, suitable for V1 30 m grid.
- Temporal: 2014-present, 6-12 day revisit depending on orbit.
- Realistic V1 strength: strongest public candidate for actual inundation extent, but only for
  dates with cloud-free SAR acquisitions coincident with a flood event. Requires a SAR processing
  pipeline (radiometric calibration, speckle filtering, thresholding or change detection).
- Cost: not a download blocker, but an engineering effort comparable to a new bin/ pipeline.
- Recommendation: defer until at least one confirmed V1 flood event date exists (from EM-DAT,
  GloFAS, or mentor) so the SAR acquisition search has a target.

#### Sentinel-2 optical flood proxies (post-event)

- Access: public via the same hubs.
- Realistic V1 strength: weaker than SAR for inundation (cloud occlusion, confusion with
  shadows/urban), usable as cross-check only.

### Tier C: Mentor-gated or access-constrained (highest local value)

#### ZINWA / DMS / local government flood records

- Zimbabwe National Water Authority (ZINWA): historical flood/water-level records, the same
  source family that holds the unpublished National catchment database referenced in
  IFPM-043.
- Department of Civil Protection / Disaster Management Ministry (now Department of Civil
  Protection): event impact records.
- District-level DCP/Matabeleland South records.
- Realistic V1 strength: potentially the only source with true local flood extents, but
  access requires mentor introduction and may carry redistribution constraints.

#### Published Mzingwane / Matabeleland flood and sediment studies

- Literature fact-check (IFPM-043 lineage) already showed authors repeatedly cite
  ~2138 km2 but do not release reusable geometry. A parallel literature search for flood-event
  or sediment-yield field studies in the Upper Mzingwane is needed before assuming any published
  validation exists.

## Recommended Approach (Tiered)

1. Tier A first, as low-risk context: close EM-DAT and GloFAS preflight and authorize a scoped
   download ONLY for temporal/event-magnitude context, explicitly labelled as non-spatial
   validation. This extends the V1 evidence baseline without overclaiming.
2. Tier B conditional: keep Sentinel-1 SAR processing deferred until a confirmed event date
   exists. Do not start a SAR pipeline speculatively.
3. Tier C via mentor: surface ZINWA / DMS / local records as a mentor-decision ask in the
   mining-data and next-step packages, because the same institutional contacts likely hold both
   mining and flood records.

## Claim Boundary Fallback (Important)

If none of Tier A/B/C yields usable local validation evidence before the thesis deadline:

- Reframe the deliverable from "validated flood-risk map" to "multi-criteria flood and sediment
  priority/suitability map with an explicitly acknowledged validation gap".
- State in all public-facing docs that outputs are decision-support priorities, not probabilistic
  hazard estimates, and are not suitable for engineering design or regulatory flood zoning.
- Add a "Limitations" section to any future `docs_public/` material stating: no independent
  validation dataset was available for V1; priority ranks are relative within the study area and
  should not be read as absolute flood-risk probabilities.
- Keep the AHP/overlay pipeline runnable but never interpret a real-data run as a validated model.

This fallback is honest, defensible, and consistent with the AGENTS.md modelling-claim boundary.
It is the recommended default unless a mentor decision explicitly closes the validation gate.

## Decision Questions For Mentor

1. Does the mentor, ZINWA, or the Department of Civil Protection hold any historical flood-extent
   polygons, gauge records, or impact reports for the Upper Mzingwane / Matabeleland South area
   between 1985 and 2024?
2. Are there published Upper Mzingwane field studies with sediment-yield, turbidity, or
   flood-event data the HiWi can cite?
3. Is the mentor willing to accept a priority/suitability map (no independent validation) as the
   V1 deliverable, or is validation a hard requirement for the thesis?
4. If validation is a hard requirement, which tier (A/B/C) should the HiWi pursue first, and can
   the mentor provide the necessary introductions for Tier C?

## Boundaries And Blockers

- No new real download is authorized by this document. Tier A downloads require Gate G5
  authorization records and mentor scope confirmation first.
- Tier B SAR processing must not begin until a confirmed V1 event date exists.
- Tier C access requires explicit mentor/data-holder introduction.
- Claim-boundary fallback applies to public docs and interpretation only; it does not authorize
  real-data AHP overlay, which remains blocked by Gates G1/G2/G7 and IFPM-D01/D04.

## Cross-References

- Risk source: `p1_risk_overview_2026-06-15.md`.
- Preflight gate: `real_data_execution_preflight_gate.md` (Gate G4 dataset-specific preflight,
  IFPM-033 backlog).
- Existing context: `srtm_v1_terrain_preprocessing_2026-06-12.md`,
  `chirps_v1_rainfall_comparison_2026-06-13.md`,
  `v1_full_methodology_evidence_sweep_2026-06-13.md`.
- Decision tasks: IFPM-D03 (validation evidence hierarchy), IFPM-061 (this package).
