# Zimbabwe Geoportal Sub-Catchments Boundary Comparison

Updated: 2026-06-10

Status: controlled alternative-boundary check completed; final Upper Mzingwane boundary still
not accepted.

## Scope

This note records the narrow follow-up after HydroBASINS boundary discovery. It uses one
authorized Zimbabwe Geoportal Sub-Catchments Shapefile to compare local named sub-catchment
evidence against the HydroBASINS candidate for the Upper Mzingwane prototype.

This step did not download SRTM, CHIRPS, HydroRIVERS, validation data, or other Zimbabwe
Geoportal datasets. It did not run AHP-MCDA overlay, scoring, map interpretation, or flood-risk
claims.

## Source Artifact

- Dataset page: `https://zimgeoportal.org.zw/datasets/sub-catchments/`
- Dataset name: Zimbabwe Geoportal Sub-Catchments
- Version: `v1.0`
- Page update date: 2025-10-22
- Page-level licence: ODC-BY 1.0
- Downloaded artifact:
  `data/raw/zimbabwe_geoportal_subcatchments_2025/sub_catchments-1761163234.zip`
- SHA-256:
  `fb5a3528ca677f420e5030f146a7699027e93c765fcebe7ef45a59611b6f0cd2`
- Size: `629658` bytes
- Extracted layer:
  `data/raw/zimbabwe_geoportal_subcatchments_2025/extracted/sub_catchments.shp`

Raw files stay under ignored `data/raw/` paths and are not committed release assets.

## Data Integrity Check

- CRS: `EPSG:4326`
- Feature count: 47
- Geometry type: Polygon
- Geometry validity: 47 valid polygons, 0 empty geometries
- Name field: `SubCatchme`
- Matching feature: `Upper Mzingwane`

Anchor containment:

| Anchor | Geoportal feature |
| --- | --- |
| Mzingwane Dam | `Upper Mzingwane` |
| Esigodini | `Upper Mzingwane` |
| Gwanda | `Shashe` |

This anchor result supports the Geoportal feature as a relevant local named candidate. It does
not by itself prove that it is the correct modelling boundary.

## Area And Overlap Evidence

Method: geometries were loaded in `EPSG:4326`, candidate intersections were computed between
polygons, and areas were calculated as WGS84 geodesic areas in square kilometres. These overlap
values are geometric diagnostics only; they do not prove drainage topology or modelling
equivalence.

The Geoportal `Upper Mzingwane` feature has a geodesic area of about `7321.5 km2`.

The HydroBASINS level 7 candidate `HYBAS_ID=1071528840`, `PFAF_ID=1245086` has a geodesic area
of about `3689.5 km2` and a HydroBASINS `SUB_AREA` of `3700.0 km2`.

Key geometric relationship:

- `HYBAS_ID=1071528840` has about `98.9%` geometric coverage by the Geoportal `Upper
  Mzingwane` feature.
- It overlaps about `3648.9 km2` of the Geoportal feature.
- That is about `98.9%` of the HydroBASINS candidate area.
- It is only about `49.8%` of the Geoportal `Upper Mzingwane` area.

The rest of the Geoportal `Upper Mzingwane` feature overlaps other HydroBASINS level 7 units,
especially:

| HYBAS_ID | PFAF_ID | Overlap with Geoportal Upper Mzingwane |
| --- | --- | --- |
| `1071528840` | `1245086` | `3648.9 km2` |
| `1071525530` | `1245089` | `2216.4 km2` |
| `1071525480` | `1245088` | `631.2 km2` |
| `1071528850` | `1245087` | `416.5 km2` |
| `1071541770` | `1245085` | `308.6 km2` |

Local-only output tables:

- `outputs/zimbabwe_geoportal_subcatchments_2025/`
  `zimbabwe_geoportal_upper_mzingwane_boundary_comparison_2026-06-10.csv`
- `outputs/zimbabwe_geoportal_subcatchments_2025/`
  `zimbabwe_geoportal_upper_mzingwane_hydrobasins_level7_overlaps_2026-06-10.csv`

These output tables are diagnostics only and stay ignored under `outputs/`.

## Interpretation Of The Area Mismatch

The current evidence points to a boundary-definition mismatch rather than a simple data error.

Likely reasons:

1. The Zimbabwe Geoportal layer appears to represent named national sub-catchment or water
   management units. Its `Upper Mzingwane` polygon is broader than the HydroBASINS upstream
   drainage candidate.
2. HydroBASINS level 7 `HYBAS_ID=1071528840` is a hydrologically derived unit that contains
   Mzingwane Dam and Esigodini while excluding Gwanda, but it covers only about half of the
   Geoportal `Upper Mzingwane` polygon.
3. The untraced `~2138 km2` Upper Mzingwane reference is not reconciled with either dataset in
   this check. It may refer to a narrower study area, a different outlet, a sub-zone within the
   named sub-catchment, or a source-specific boundary. It should not be used as a hard acceptance
   target until its source, outlet, area method, and geometry definition are traced.

## Boundary Decision Impact

Current verdict: boundary still not accepted.

The Geoportal dataset resolves one earlier uncertainty: an alternative local named boundary is
available and it does identify `Upper Mzingwane`. However, it introduces a larger area mismatch.
It therefore cannot automatically replace the HydroBASINS candidate without a modelling-scope
decision.

Decision paths now become:

1. Use the Geoportal `Upper Mzingwane` feature as a broad local or management-style unit, with a
   documented explanation that it is about `7321.5 km2`.
2. Use HydroBASINS level 7 `HYBAS_ID=1071528840` as a narrower hydrological unit, with a waiver
   that it covers only about half of the Geoportal named unit.
3. Trace the source of the untraced `~2138 km2` reference and obtain or digitize the
   corresponding boundary if that is the intended study area.
4. Ask the mentor or a local authority to choose the intended boundary definition before SRTM,
   CHIRPS, overlay, or interpretation.

## Adversarial Review

Review mode: subagent-assisted adversarial review plus local final pass.

Correctness and domain-boundary angle:

- Finding: a named `Upper Mzingwane` feature or overstated hydrological-authority wording could
  make Geoportal look more authoritative than the current evidence supports.
- Triage: kept the verdict as `boundary still not accepted`, described Geoportal as a local
  named or management-unit candidate, stated the `7321.5 km2` area, documented that this is
  broader than both HydroBASINS level 7 and the untraced `~2138 km2` reference, and labelled
  overlaps as geometric diagnostics only.

Engineering and workspace-boundary angle:

- Finding: the real Shapefile, generated overlap CSVs, and direct resource URL could leak into
  committed or public material.
- Triage: kept raw data under ignored `data/raw/`, kept diagnostics under ignored `outputs/`,
  referenced only public-safe metadata and aggregate numeric evidence in this note, and labelled
  the direct resource URL as internal reproducibility evidence only.

Process angle:

- Finding: the preflight originally described a browser manual download, while the completed
  transfer used the resource URL discovered through the authenticated browser page.
- Triage: updated the registry and preflight execution record to state the actual method and
  to document that no credentials, cookies, tokens, or session material were recorded.

Reproducibility angle:

- Finding: area and overlap numbers needed a clear method statement.
- Triage: recorded that candidate intersections were computed from `EPSG:4326` geometries and
  measured as WGS84 geodesic areas in square kilometres.

## Next Action

Do not proceed to SRTM, CHIRPS, overlay, scoring, or map interpretation yet.

The next useful task is to trace the source of the untraced `~2138 km2` Upper Mzingwane
reference or ask the mentor which boundary definition is intended: Geoportal named
sub-catchment, HydroBASINS hydrological unit, or the narrower published-study boundary.
