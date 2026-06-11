# Mentor Next-Step Summary: IFPM Prototype Scope

Updated: 2026-06-11

Status: internal draft revised after mentor feedback. HydroBASINS boundary discovery and
Zimbabwe Geoportal Sub-Catchments boundary comparison have been executed as boundary-only checks;
no SRTM, CHIRPS, overlay, or interpretation has been run.

## One-Minute Message

The IFPM work has moved from dataset review into a controlled prototype plan. After mentor
feedback, the safest next step is to define the Zimbabwe prototype from a flood/mining-relevant
outlet and delineate the upstream catchment from that outlet. `Upper Mzingwane` remains the
regional context, but the operational boundary should be hydrologically linked to the outlet
rather than chosen only from existing named polygons. The purpose is not to claim a validated
flood-risk model yet. The purpose is to prove that data registration, preprocessing diagnostics,
standardization, AHP weighting, and weighted overlay can run in a traceable way.

## Current Prototype Scope

- First study side: Zimbabwe.
- Regional context: Upper Mzingwane.
- Operational study area: upstream catchment of the selected flood/mining-relevant outlet.
- Boundary rule: ask for a rough outlet, downstream impact point, dam, confluence, mining area,
  town, or map mark; then delineate the upstream catchment and compare it with Geoportal,
  HydroBASINS, and the literature `~2138 km2` reference.
- First dataset candidates: SRTM 1 Arc-Second, HydroBASINS/HydroRIVERS, and CHIRPS v3.
- First indicators: elevation, slope, drainage-distance or flow-accumulation proxy, rainfall
  summary, and optional sub-basin id for aggregation.
- Resolution boundary: terrain derivatives may use 30 m SRTM-compatible rasters, but CHIRPS
  rainfall is much coarser and should stay native, aggregated, or summarized by zones until the
  resampling rule is agreed.
- Excluded from the first slice unless better rules are supplied: full mining-pressure scoring,
  rehabilitation potential, and socioeconomic vulnerability. Mining remains relevant for choosing
  the outlet and later pressure criteria.

## What Is Ready

- Data governance is defined before download.
- Dataset registry notes exist for the three starter dataset candidates.
- Download preflight checklists exist. HydroBASINS boundary discovery and Zimbabwe Geoportal
  Sub-Catchments comparison have been executed for boundary evidence only; broader real-data
  downloads remain blocked.
- A dedicated Upper Mzingwane boundary decision package now records the discovered candidate
  HYBAS/PFAF ids, the Geoportal named sub-catchment evidence, and the remaining decision options.
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

1. Indicate the rough outlet or downstream impact point that should define the first catchment.
   A nearby town, dam, confluence, mining area, river reach, or map point is enough for a first
   test.
2. Confirm whether the first catchment can be delineated using HydroBASINS first, with optional
   DEM refinement later.
3. Confirm the modelling unit: raster pixels first, sub-basin aggregation, or a mixed workflow.
4. Choose the first temporal window for rainfall and validation evidence.
5. Decide which evidence can support validation: local records, satellite flood extent,
   Copernicus EMS, GloFAS, EM-DAT, DFO, field knowledge, or expert review.
6. Decide whether the first real-data output should remain workflow diagnostics or preliminary
   flood susceptibility. Flood risk or intervention priority would require additional exposure,
   vulnerability, mining, rehabilitation, and validation evidence.
7. Confirm who should provide AHP pairwise comparisons and how the consistency ratio should be
   reviewed.

## Proposed Next Actions

1. Ask the mentor for a rough outlet or downstream impact point.
2. Record the candidate outlet and choose the outlet-based delineation branch.
3. Choose the first temporal window and validation evidence hierarchy.
4. Complete the unresolved preflight items for SRTM, HydroBASINS/HydroRIVERS, and CHIRPS v3.
5. Only after mentor decisions and all unchecked preflight blockers are closed, download the
   smallest required real dataset subset under `data/`.
6. Run the existing diagnostics and synthetic-tested preprocessing workflow on the first real
   subset, keeping raw data under `data/` and outputs under `outputs/`.

## Suggested Meeting Closing

The current work is ready for mentor feedback on scope and validation design. It is not ready for
model-validity claims. The most useful mentor input now is a rough outlet or downstream impact
point, followed by a temporal window and validation evidence hierarchy so that the first real-data
prototype can stay small, traceable, and defensible.
