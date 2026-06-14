# P2 Risk R2.2 Hydrology Derivatives Decision Package

Date: 2026-06-15

Status: internal decision package. This document records the hydrological-conditioning
assumptions required by the real-data execution preflight gate before flow accumulation, TWI,
drainage density, stream order, and drainage-distance derivatives may be produced. It does not
authorize running those derivatives, AHP overlay, flood-risk interpretation, or
intervention-priority interpretation.

## Risk Statement

R2.2 (P2): hydrology derivatives are incomplete. Only DEM and slope exist for V1.

Original methodology (Section 1, Flood Hazard Layer) requires: slope, aspect, flow direction,
flow accumulation, drainage density, stream order, TWI. Current state:

- Done: DEM (EPSG:32735, 30 m, float32), slope (degrees), both grid-gated
  (IFPM-052, IFPM-054).
- Missing: flow direction, flow accumulation, drainage density, stream order, TWI, aspect,
  distance to drainage network.

The preflight gate explicitly defers these: "keep flow accumulation and drainage-distance proxies
deferred until hydrological conditioning assumptions are explicitly documented." This package
records those assumptions so the derivatives can be unblocked for diagnostic production.

Consequence: "distance to drainage network" and "flow accumulation" are core flood-hazard
indicators in the methodology. Without them, the Flood Hazard criterion is missing two of its
named drivers. The deliverable would rely on slope/elevation alone, which is a weaker hazard
proxy.

## Why This Needs Documented Assumptions First

Hydrology derivatives are not unique functions of the DEM. They depend on choices that change the
output and that have real trade-offs:

- sink filling changes downstream connectivity;
- the flow-direction algorithm (D8, D-infinity, MFD) changes how dispersal is represented;
- the channel initiation threshold changes drainage density and stream-order results;
- boundary handling changes whether the V1 edge is treated as outlet or sealed.

Producing these derivatives without recording the choices would make the outputs
non-reproducible and non-auditable. The gate requires the assumptions to be documented before
production so the outputs are defensible.

## Hydrological-Conditioning Assumptions (To Be Confirmed)

These are the assumption categories that must be recorded before any V1 hydrology derivative is
produced. Each is presented with options and a candidate default; the mentor must confirm or
revise before production.

### A1. Sink filling

- Options: (a) no filling (preserve raw depressions); (b) fill all sinks to spill
  (Wang-Liu/Planchon-Darboux); (c) fill only shallow sinks below a depth threshold.
- Candidate default: (b) fill to spill, because the methodology uses flow accumulation for
  drainage-network derivation, which requires continuous flow paths. Record the filled-DEM
  volume and the count/depth of filled sinks as diagnostics.
- Trade-off: filling can connect spurious flow paths across artefact depressions; not filling
  terminates flow prematurely in dry catchments. Semi-arid ephemeral catchments like the Upper
  Mzingwane may have real closed depressions, so the filled volume must be inspected.

### A2. Flow direction algorithm

- Options: (a) D8 (single-direction, O'Callaghan-Mark); (b) D-infinity (Tarboton, dispersed);
  (c) MFD (multiple-flow, Freeman/Quinn).
- Candidate default: (a) D8 for the first V1 prototype, because drainage-network derivation,
  stream order, and drainage density are most cleanly defined on D8, and the methodology's
  "distance to drainage" indicator is channel-based. Keep D-infinity as an alternative for TWI
  if dispersion matters.
- Trade-off: D8 produces streaky artefacts on planar areas; D-infinity/MFD are smoother but
  complicate stream-order definition.

### A3. Channel initiation threshold

- Options: a fixed flow-accumulation threshold (e.g. 100, 500, 1000, 5000 contributing cells) or
  a threshold derived from drainage-density calibration.
- Candidate default: record diagnostics at several thresholds (100, 500, 1000, 5000 cells) and
  let the mentor choose the channel network that best matches HydroRIVERS/Geoportal rivers in
  V1, rather than picking a number unilaterally.
- Trade-off: a low threshold over-densifies the channel network; a high threshold misses
  ephemeral headwater channels that matter for flash-flood and sediment connectivity.

### A4. Grid, CRS, and mask

- Binding rule: all derivatives must match the V1 terrain reference grid (EPSG:32735, 30 m,
  the DEM's transform, width, height, dtype float32, NoData -9999.0) and pass
  `bin/check_v1_raster_grid.py` before any standardization or overlay.
- V1 valid-cell coverage is the mask. Derivatives outside V1 are NoData.

### A5. Boundary handling

- Options: (a) treat the V1 boundary edge as the catchment outlet (allow flow to exit); (b) seal
  the edge (no flow exits).
- Candidate default: (a) allow flow to exit at the V1 boundary, because V1 is itself a
  HydroBASINS basin unit whose boundary should approximate a ridge/outlet divide. Record edge
  outflow cells as diagnostics.
- Trade-off: V1 is a Level-8 basin chained from a Level-7; internal sub-basins exist, so
  edge-as-outlet is a catchment-scale approximation, not a guarantee of correct internal
  routing.

## Derivation Plan (Once Assumptions Are Accepted)

When A1-A5 are confirmed, the following V1 diagnostic rasters would be produced under
`outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/` (or a sibling
`hydrology_derivatives/` folder), with no new data download:

1. `v1_dem_filled.tif` (conditioned DEM, with fill diagnostics).
2. `v1_flow_direction_d8.tif` (D8 codes).
3. `v1_flow_accumulation.tif` (contributing cells or contributing area in m2).
4. `v1_drainage_network_<threshold>.tif` (channel cells at each candidate threshold).
5. `v1_stream_order.tif` (Strahler or similar on the chosen network).
6. `v1_drainage_density.tif` (optional kernel-based density).
7. `v1_twi.tif` (optional; requires slope and specific catchment area).
8. `v1_distance_to_drainage.tif` (Euclidean or cost distance to the chosen channel network).

Each must pass the V1 raster grid gate before standardization or overlay. These are diagnostic
candidates only; they do not enter AHP scoring until their own gates close.

## Engineering Unblocked By Accepted Assumptions

Once A1-A5 are confirmed by the mentor:

- a `bin/derive_v1_hydrology.py` (or split scripts) can be written using the existing V1 DEM
  and standard tooling (for example `richdem`, `pysheds`, `whitebox` via Python, or GDAL);
- the dependency would be recorded as root `.venv` local tooling only, not as a public pipeline
  dependency (matching the scipy precedent in the full-methodology sweep);
- outputs stay under `outputs/`, never in `ifpm-flood-pipeline/` or `context/`.

This is engineering-actionable without any new download. The blocker is the documented
assumptions, not data access.

## Decision Questions For Mentor

1. Are the candidate defaults for A1 (fill to spill), A2 (D8), A4 (V1 reference grid), A5
   (edge-as-outlet) acceptable, or should alternatives be used?
2. Which channel initiation threshold (A3) best matches the Mzingwane channel network? Can the
   mentor review a threshold-sensitivity figure before a single value is chosen?
3. Should TWI be produced for the first prototype, or is flow accumulation + drainage distance
   sufficient?
4. Is the resulting drainage network to be validated against HydroRIVERS / Geoportal rivers
   before it enters any Flood Hazard criterion?

## Boundaries And Blockers

- No hydrology derivative is produced by this document. Production requires accepted A1-A5.
- Derivatives are diagnostic candidates; they do not authorize AHP overlay, flood-risk
  interpretation, or intervention-priority interpretation.
- All derivatives must pass the V1 raster grid gate.
- This package does not close Gate G2 (modelling unit); it only prepares the terrain derivatives
  that either modelling-unit branch would use.

## Cross-References

- Risk overview: `p2_risk_overview_2026-06-15.md`.
- Preflight gate: `real_data_execution_preflight_gate.md` (immediate next action on flow
  accumulation deferral).
- Reference grid rule: `context/docs/data-management/v1_terrain_reference_grid_rule.md`.
- Terrain preprocessing: `srtm_v1_terrain_preprocessing_2026-06-12.md`.
- Standardization rule: `v1_terrain_standardization_rule_2026-06-13.md`.
- Decision tasks: IFPM-065 (this package); coupled with R2.1 sediment LS factor.
