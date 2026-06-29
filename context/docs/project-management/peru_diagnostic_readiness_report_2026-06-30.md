# Peru Diagnostic Readiness Report (Boundary Discovery + Data Inventory)

Date: 2026-06-30

Status: `diagnostic_only`. This report records the first Peru boundary-discovery run and a
data-readiness inventory. It does NOT accept any Peru boundary (IFPM-D02 remains open), does NOT
download SRTM/CHIRPS, does NOT run overlay or interpretation, and does NOT make any Zimbabwe-Peru
comparison claim.

## Scope

Executed:

- one boundary-only HydroBASINS South America download (the Peru analogue of the already-executed
  Zimbabwe HydroBASINS Africa authorization);
- candidate-basin discovery against a discovery envelope around the Arequipa-Moquegua-Tacna
  administrative departments;
- a data-readiness inventory of every Peru-relevant source already identified in the project.

Not executed: SRTM download, CHIRPS download, terrain derivation, overlay, scoring,
flood-risk interpretation, intervention mapping, validation, and any cross-country comparison.

## Data Evidence

- Dataset id: `hydrosheds_peru_prototype`
- Source artifact: `hybas_sa_lev01-12_v1c.zip`
- Source URL: `https://data.hydrosheds.org/file/hydrobasins/standard/hybas_sa_lev01-12_v1c.zip`
- Raw archive: `data/raw/hydrosheds_peru_prototype/hybas_sa_lev01-12_v1c.zip`
- Actual size: `334160720` bytes (~334 MB)
- SHA-256: `fb012e48419bda0a7f4d0ebc56efcd906ad0e3bde324b9c70fac9693e2d21a72`
- Extraction: complete; 85 files; 12 levels (lev01-12); field schema identical to the Africa
  product (`HYBAS_ID, NEXT_DOWN, NEXT_SINK, MAIN_BAS, DIST_SINK, DIST_MAIN, SUB_AREA, UP_AREA,
  PFAF_ID, ENDO, COAST, ORDER, SORT`); CRS `EPSG:4326`.
- License: HydroSHEDS core product license (same as the Africa artifact); freely available for
  scientific/educational/commercial use.
- Authorization: `context/docs/data-management/preflight/peru_hydrobasins_boundary_discovery_authorization_2026-06-30.md`

Raw and extracted data stay under ignored `data/`. No vectors copied into `context/` or
`ifpm-flood-pipeline/`.

## Discovery Envelope

Peru has no named catchment or outlet, only the three administrative departments Arequipa,
Moquegua, and Tacna. A coarse rectangular discovery envelope
(lon -73.5 to -68.8, lat -18.7 to -14.8, EPSG:4326) was used to narrow the HydroBASINS search.
**This envelope is a discovery proxy, not an authoritative administrative boundary.** Its purpose
is to turn IFPM-D02 from an abstract choice into a concrete set of candidate units with real
areas. The actual department polygons (INEI/GADM or an accepted local source) are still needed
before any boundary is accepted.

## Candidate Basins Found

Intersections of HydroBASINS South America with the discovery envelope, by level:

| Level | Units intersecting | SUB_AREA sum km2 | Envelope intersect km2 | Pacific-slope | Highland/inland |
|---:|---:|---:|---:|---:|---:|
| 4 | 5 | 4,245,481 | 160,594 | 0 | 5 |
| 5 | 11 | 1,086,395 | 160,594 | 3 | 8 |
| 6 | 30 | 364,158 | 160,608 | 6 | 24 |
| 7 | 110 | 226,826 | 160,623 | 23 | 87 |
| 8 | 268 | 191,939 | 160,629 | 30 | 238 |

The envelope-intersect area converges at about `160,600 km2` from level 5 onward (this is the
coarse envelope area, larger than the real three departments which are about `95,745 km2` total).
At L7, individual units range from about `2.8` to `14,300 km2`; at L8 from about `0.6` to
`3,670 km2`.

Topology check at the finest inspected level (L8): `23,783` total units in South America,
`2,050` terminal units (`NEXT_DOWN=0`), `0` dangling `NEXT_DOWN` references. Topology is
`likely_ok` for tracing.

Notable L7 candidates (largest envelope overlap):

| HYBAS_ID | PFAF_ID | SUB_AREA km2 | UP_AREA km2 | Envelope intersect km2 | Drainage |
|---:|---:|---:|---:|---:|---|
| 6070620850 | 6640594 | 7,271 | 7,271 | 7,245 | highland/inland |
| 6070576400 | 6229989 | 14,300 | 14,300 | 5,900 | highland/inland |
| 6070029380 | 6710140 | 5,799 | 5,799 | 5,780 | highland/inland |
| 6070617650 | 6710409 | 5,666 | 5,666 | 5,646 | highland/inland |

Full candidate table: `outputs/peru_boundary_discovery/peru_candidate_basins.csv`.
Discovery figure: `outputs/peru_boundary_discovery/peru_boundary_discovery.png`.

Observations:

- The three named departments span two drainage tendencies: a Pacific-slope coastal fringe and
  a highland/inland area trending toward the Amazon. This confirms the catchment-versus-region
  bias risk already flagged in the Peru decision package: an administrative-region boundary
  mixes Pacific-slope and highland flood regimes.
- At L7, individual unit areas (thousands of km2) are comparable in order of magnitude to the
  Zimbabwe V1 prototype catchment (~3,700 km2), so a hydrographic-unit definition would let
  Peru match Zimbabwe's scale for comparison.

## Boundary Acceptance State

Not accepted. The Peru boundary (IFPM-D02) remains open. The three documented options are now
informed by real candidate areas:

1. **Administrative regions** (Arequipa+Moquegua+Tacna, ~95,745 km2): matches the named study
   area but mixes Pacific-slope and highland flood regimes, and mixes multiple hydrological
   basins. Largest scope.
2. **ANA/HydroBASINS hydrographic units**: hydrologically coherent; this discovery shows viable
   L7 units exist in the 5,000-14,000 km2 range. Does not match the named administrative region.
3. **Clipped hydrological units** (hydrographic units intersecting the three departments):
   compromise; the L7/L8 candidates found here are the input to such a clip.

None can be accepted without (a) the mentor resolving the admin-vs-hydrographic choice and
(b) an authoritative administrative polygon source (the discovery envelope is a proxy).

## Data-Readiness Inventory (Peru Side)

What is ready, what is identified-but-ungated, and what is missing, per criterion family:

| Criterion family | Peru source | Status | Blocks on |
|---|---|---|---|
| Terrain (DEM, slope, hydrology) | SRTM 1 arc-second (public) | ready to download once boundary accepted | IFPM-D02 + Step S2/S3 |
| Rainfall / R-factor | CHIRPS v3 (public) | ready; same workflow as Zimbabwe | IFPM-D02 + Step S1/S3 |
| Land cover / C-factor | ESA WorldCover (public) | ready; same lookup as Zimbabwe | IFPM-D02 + Step S3 |
| Soil / K-factor | SoilGrids 250m (public) | ready; same workflow as Zimbabwe | IFPM-D02 + Step S3 |
| **Mining / ASM** | **INGEMMET/GEOCATMIN (public, better than Zimbabwe)** | identified; registry+preflight needed | Step S2/S3 (no mentor gate) |
| Validation | ANA / SENAMHI hydrometeorological | identified; request-based | mentor introduction (IFPM-D03) |
| Population / exposure | WorldPop PER 2020 (public) | ready | IFPM-D02 + Step S3 |
| Roads / infrastructure | Geofabrik Peru OSM (public) | ready | IFPM-D02 + Step S3 |
| Boundary | this HydroBASINS discovery | diagnostic candidates found | **IFPM-D02 (mentor decision)** |

Key contrast with Zimbabwe: Peru's mining cadastre (INGEMMET/GEOCATMIN) is publicly accessible,
unlike Zimbabwe's. This is the one criterion where Peru is strictly better positioned than the
Zimbabwe V1 (which has only a weak OSM proxy).

## What Becomes Executable Once IFPM-D02 Resolves

If the mentor picks a boundary option, the Peru terrain chain can run in parallel using the
already-proven Zimbabwe workflow: SRTM tile plan + download + DEM/slope + hydrology + grid gate.
The public global sources (SRTM, CHIRPS, WorldCover, SoilGrids, WorldPop) are all applicable to
Peru without new institutional access. Only INGEMMET/GEOCATMIN and ANA/SENAMHI need their own
registry+preflight notes before download.

A Peru-specific terrain reference grid rule (UTM 18S, not the Zimbabwe UTM 35S) will be needed
before any Peru terrain standardization or overlay; the Zimbabwe rule is Zimbabwe-only.

## Next Actions

1. Surface IFPM-D02 to the mentor with this discovery as evidence: which boundary option
   (administrative / hydrographic / clipped), and is Peru a hard requirement for the thesis?
2. If a hydrographic option is preferred, the L7 candidates here are the starting set for a
   reviewed union, mirroring the Zimbabwe V1 waiver path.
3. Obtain an authoritative Peru administrative boundary (INEI/GADM/accepted local source) to
   replace the discovery envelope before any boundary acceptance.

## What This Report Does NOT Do

- Does not accept any Peru boundary.
- Does not authorize SRTM, CHIRPS, or any raster download.
- Does not run overlay, scoring, or interpretation.
- Does not make any Zimbabwe-Peru comparison claim.
- Does not treat the discovery envelope as an authoritative administrative boundary.

## Cross-References

- Authorization: `context/docs/data-management/preflight/peru_hydrobasins_boundary_discovery_authorization_2026-06-30.md`
- Peru decision package: `p2_peru_side_decision_package_2026-06-15.md`
- Zimbabwe analogue (result): `hydrosheds_boundary_discovery_result_2026-06-10.md`
- Execution status policy Peru Rule: `execution_status_policy.md`
- Discovery script: `bin/discover_peru_candidate_basins.py`
- Discovery outputs: `outputs/peru_boundary_discovery/`
