# Peru Engineering-Pilot Boundary Decision (Arequipa Region)

Date: 2026-06-30

Status: `engineering_pilot` — accepted for controlled Peru terrain-chain execution only. This is
**NOT** a research-value-selected boundary. It will be replaced if the mentor names a specific
Peru flood/mining-relevant site.

## What This Is

The working boundary displayed externally as **Arequipa Region** is a single HydroBASINS
South America level-7 unit selected to run the Peru terrain chain
(SRTM → DEM → slope → hydrology → grid gate) end-to-end, proving the Peru side works and is
comparable in scale to the Zimbabwe V1 prototype. It exists because the user decided to proceed
with a basin-defined boundary using a process pilot, rather than wait for the mentor to name a
specific Peru site.

## Why This Is Different From Zimbabwe V1

Zimbabwe V1 (`HB_L8_1081528840`) was selected from an **explicit mentor cue** ("the Level-8 basin
containing Mzingwane Dam, following the main channel downstream toward Gwanda"), and the mentor
acknowledged it with a thumbs-up. V1 corresponds to a real, named, flood/mining-relevant place.

Arequipa Region has **no mentor-named site behind it**. The mentor has given no Peru outlet, place name, or
flood/mining reference. Arequipa Region was therefore chosen by an explicit selection rule (below), not by
research value. This must be stated plainly in any mentor-facing or thesis-facing material.

## Selection Rule (Defensible And Explicit)

From the 110 L7 candidate basins intersecting the Arequipa-Moquegua-Tacna discovery envelope, Arequipa Region
was selected by:

1. **Drainage tendency = pacific_slope** — Pacific-slope basins have a genuine flood-relevant
   regime (coastal plain, populated valleys) and make a more meaningful pilot than highland/
   inland units, even though no specific site was named.
2. **Coverage ≥ 0.9** (intersect_area / SUB_AREA) — the basin lies fully inside the three-department
   envelope, not clipped at the edge.
3. **SUB_AREA in 2500-5500 km²** — comparable to Zimbabwe V1 (~3,700 km²), so the two prototypes
   are at the same scale.
4. **Non-terminal** (NEXT_DOWN exists) — the basin is part of a real drainage chain, not a
   domain-edge artifact.

Only 2 L7 candidates met all four criteria. Arequipa Region (`HYBAS_ID=6070641200`, SUB_AREA 2745.4 km²) was
chosen over the other (`6070648390`, 2723.0 km²) because it sits further west (closer to the
Pacific coast and the Arequipa metropolitan area), making it the more flood/plausibility-relevant
of the two.

## Arequipa Region Facts

| Field | Value |
|---|---|
| boundary_id | `PERU_HYBAS_L7_6070641200_HYBAS_L7_6070641200_engineering_pilot` |
| source | HydroBASINS South America standard v1c, level 7 |
| HYBAS_ID | 6070641200 |
| PFAF_ID | 6710203 |
| NEXT_DOWN | 6070029580 |
| SUB_AREA | 2745.4 km² |
| UP_AREA | 11119.2 km² |
| geo_area | 2736.1 km² |
| bounds (WSEN) | -72.308, -16.855, -71.588, -16.141 |
| area ratio Arequipa Region / Zimbabwe V1 | 0.74 |
| Arequipa city distance | ~17 km east of the pilot boundary |
| CRS | EPSG:4326 |

Outputs: `outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg` (+ manifest, anchor check,
diagnostic map).

## What This Authorizes

- Peru SRTM tile planning + scoped download for the Arequipa Region envelope (with its own Step S3
  authorization, mirroring the Zimbabwe SRTM flow).
- Peru DEM/slope/hydrology derivation at a Peru-appropriate CRS (UTM 18S, NOT the Zimbabwe
  UTM 35S reference grid).
- A Peru reference-grid rule, separate from the Zimbabwe V1 rule.

## What This Does NOT Authorize

- No claim that Arequipa Region is a research-meaningful Peru study area (no mentor-named site).
- No flood-risk, intervention-priority, or Zimbabwe-Peru comparison interpretation.
- No treatment of Arequipa Region as a final thesis boundary.
- No change to the Zimbabwe V1 reference-grid rule (Peru gets its own).

## Relationship To IFPM-D02

IFPM-D02 (Peru boundary rule) remains open. Arequipa Region is an engineering-pilot execution of "use a
hydrographic unit as the boundary" (option 2 of the three IFPM-D02 options), chosen to keep work
moving. If the mentor later names a specific Peru site or prefers a different boundary option,
Arequipa Region is replaced and the terrain chain is re-run against the new boundary. The workflow and
governance are reusable; only the boundary polygon changes.

## Next Action

Plan and download the SRTM tiles covering Arequipa Region + 5 km buffer, mirroring `plan_srtm_tiles_for_v1.py`
and `download_srtm_v1_tiles.py` but for the Peru envelope.
