# Mentor Next-Step Summary: IFPM Prototype Scope

Status: internal draft for mentor-facing discussion. No real data has been downloaded.

## One-Minute Message

The IFPM work has moved from dataset review into a controlled prototype plan. The safest next
step is to use the Zimbabwe / Upper Mzingwane Catchment side as the first workflow slice, because
the study area is already framed as a catchment. The purpose is not to claim a validated flood
risk model yet. The purpose is to prove that data registration, preprocessing diagnostics,
standardization, AHP weighting, and weighted overlay can run in a traceable way before real data
downloads begin.

## Current Prototype Scope

- First study side: Zimbabwe.
- Working study area: Upper Mzingwane Catchment.
- Boundary rule: catchment or HydroBASINS-compatible sub-catchment boundary, pending mentor
  confirmation or a better local boundary.
- First dataset candidates: SRTM 1 Arc-Second, HydroBASINS/HydroRIVERS, and CHIRPS v3.
- First indicators: elevation, slope, drainage-distance or flow-accumulation proxy, rainfall
  summary, and optional sub-basin id for aggregation.
- Resolution boundary: terrain derivatives may use 30 m SRTM-compatible rasters, but CHIRPS
  rainfall is much coarser and should stay native, aggregated, or summarized by zones until the
  resampling rule is agreed.
- Excluded from the first slice unless better rules are supplied: mining pressure,
  rehabilitation potential, and socioeconomic vulnerability.

## What Is Ready

- Data governance is defined before download.
- Dataset registry notes exist for the three starter dataset candidates.
- Download preflight checklists exist, but downloads remain blocked by unresolved scope and
  licence/details checks.
- The deliverable pipeline can derive AHP weights from a pairwise matrix and check the
  consistency ratio.
- The pipeline can standardize single-band GeoTIFF layers to a 0-1 scale while preserving
  NoData.
- Raster diagnostics can report CRS, transform, resolution, shape, band count, NoData, and
  overlay-readiness checks.
- A synthetic end-to-end smoke test now covers standardization, raster diagnostics, weighted
  overlay, score output, class output, and diagnostics without using real data.

## What Is Not Ready To Claim

- This is not a validated flood-risk model.
- It is not yet a Zimbabwe-Peru comparison.
- It is not yet an intervention-priority map.
- It does not yet validate mining impact or rehabilitation suitability.
- It does not prove that all real source data can be downloaded, licenced, aligned, or validated.

## Decisions Needed From Mentor

1. Confirm the Zimbabwe first-slice boundary: HydroBASINS sub-basin, another catchment boundary,
   or a locally authoritative boundary.
2. Confirm the modelling unit: raster pixels first, sub-basin aggregation, or a mixed workflow.
3. Choose the first temporal window for rainfall and validation evidence.
4. Decide which evidence can support validation: local records, satellite flood extent,
   Copernicus EMS, GloFAS, EM-DAT, DFO, field knowledge, or expert review.
5. Decide whether the first real-data output should remain workflow diagnostics or preliminary
   flood susceptibility. Flood risk or intervention priority would require additional exposure,
   vulnerability, mining, rehabilitation, and validation evidence.
6. Confirm who should provide AHP pairwise comparisons and how the consistency ratio should be
   reviewed.

## Proposed Next Actions

1. Get mentor confirmation of the Zimbabwe boundary and modelling unit.
2. Choose the first temporal window and validation evidence hierarchy.
3. Complete the unresolved preflight items for SRTM, HydroBASINS/HydroRIVERS, and CHIRPS v3.
4. Only after mentor decisions and all unchecked preflight blockers are closed, download the
   smallest required real dataset subset under `data/`.
5. Run the existing diagnostics and synthetic-tested preprocessing workflow on the first real
   subset, keeping raw data under `data/` and outputs under `outputs/`.

## Suggested Meeting Closing

The current work is ready for mentor feedback on scope and validation design. It is not ready for
model-validity claims. The most useful mentor input now is a concrete boundary decision, a
temporal window, and a validation evidence hierarchy so that the first real-data prototype can
stay small, traceable, and defensible.
