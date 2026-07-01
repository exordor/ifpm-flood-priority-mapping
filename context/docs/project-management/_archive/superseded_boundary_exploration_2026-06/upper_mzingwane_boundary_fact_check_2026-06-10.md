# Upper Mzingwane Boundary Fact Check

Updated: 2026-06-10

Status: fact check completed for boundary-source claims; boundary still not accepted.

## Fact-Check Questions

1. Does the Zimbabwe Geoportal Sub-Catchments dataset exist with the recorded metadata?
2. Is the `~2138 km2` Upper Mzingwane area reference supported by external sources?
3. Does HydroBASINS support the kind of candidate boundary use recorded in this project?
4. Do local geometry checks reproduce the current area and overlap numbers?
5. Does any checked source provide a ready-to-use accepted modelling boundary?

## External Sources Checked

### Zimbabwe Geoportal

- Dataset page:
  `https://zimgeoportal.org.zw/datasets/sub-catchments/`
- Dataset catalogue page:
  `https://zimgeoportal.org.zw/datasets/?page=4`

Verified facts:

- The page title is `Sub-Catchments`.
- The dataset summary says it covers Zimbabwe sub-catchments across the entire country.
- The catalogue lists `Sub-Catchments`, update date `Oct. 22, 2025`, organisation not
  specified, licence `ODC-BY 1.0`, and resource formats `geojson` and `shapefile`.

Limitations:

- The public page/catalogue verifies dataset identity and catalogue metadata.
- It does not prove that the `Upper Mzingwane` feature is the intended thesis modelling boundary.
- It does not resolve redistribution or public release permission for downloaded artifacts.

### HydroBASINS / HydroSHEDS

- HydroBASINS product page:
  `https://www.hydrosheds.org/products/hydrobasins`
- HydroBASINS technical documentation v1.c:
  `https://data.hydrosheds.org/file/technical-documentation/HydroBASINS_TechDoc_v1c.pdf`

Verified facts:

- HydroBASINS is a global vector polygon product for sub-basin boundaries.
- It provides nested sub-basins at multiple scales and uses a coding scheme for topology such as
  upstream and downstream connectivity.
- It is derived from HydroSHEDS core layers at 15 arc-second resolution.
- It is suitable for candidate hydrological-unit discovery.

Limitations:

- HydroBASINS does not automatically define local or official Zimbabwe water-management
  boundaries.
- A HydroBASINS candidate still needs a project decision or waiver before it can become the
  prototype mask.

### Literature Area Reference

Sources found:

- Frontiers in Sustainability, 2026, WEF nexus study:
  `https://www.frontiersin.org/journals/sustainability/articles/10.3389/frsus.2026.1768279/full`
- Chisadza et al., 2023, ecological vulnerability study:
  `https://artefacts-discovery.researcher.life/full_text/DA-2/79/7913cbcb7eb0397b902642ff16b97ab6/full_text/3ee601a3a1244c126f790c859bb44edc.pdf`
- Maviza, Grab, and Engelbrecht, 2022, Springer bibliographic record:
  `https://link.springer.com/article/10.1007/s00704-022-04040-5`
- Public preprint mirror of the same Maviza et al. study text:
  `https://www.academia.edu/129926399/Twentieth_century_precipitation_trends_in_the_upper_Mzingwane_sub_catchment_of_the_northern_Limpopo_basin_Zimbabwe`
- Maviza and Ahmed, 2020, figure/context mirror:
  `https://www.researchgate.net/figure/Study-area-map-Upper-Mzingwane-sub-catchment-showing-its-location-within-the-Mzingwane_fig1_340597367`

Source-chain evidence table:

| Source | Role | `2138 km2`? | Geometry? |
| --- | --- | --- | --- |
| Frontiers WEF nexus, 2026 | Derivative; cites LBPTC/Sibanda/Maviza | yes | no |
| Chisadza et al., 2023 | Peer-reviewed study-area description | yes | no |
| Maviza et al., 2022 | Springer version-of-record metadata | metadata only | no |
| Public Maviza preprint mirror | Public mirror of study text | yes | mirror only |
| Maviza and Ahmed, 2020 mirror | Figure/context page | contextual | mirror only |

Access date for all sources in the table: 2026-06-10.

Verified facts:

- Multiple external sources report Upper Mzingwane at or around `2138 km2`.
- The 2026 WEF nexus article lists Mzingwane's four sub-catchments and gives Upper Mzingwane as
  `2,138 km2`, citing LBPTC (2010), Sibanda et al. (2020), and Maviza et al. (2022).
- The 2023 ecological vulnerability paper states that its Upper Mzingwane study area covers
  approximately `2138 km2`.
- The public preprint mirror for Maviza et al. states that UMS covers `2138 km2`, while the
  Springer page verifies the article's version-of-record bibliographic metadata and DOI.

Updated interpretation:

- The `~2138 km2` reference should no longer be called simply `untraced`.
- It is now `literature-reported, repeatedly cited, but source-chain- and
  geometry-unresolved`.

Remaining limitation:

- None of the checked sources resolved the primary source chain back to an authoritative GIS
  boundary file, outlet point, exact polygon, projection, or area-computation method for the
  `~2138 km2` boundary.
- Therefore the `~2138 km2` area still cannot be used as a hard geometry target or model mask.

## Local Geometry Recheck

Command class:

- `uv run --with geopandas --with pyogrio --with shapely --with pyproj --with pandas python`

Method:

- Loaded Geoportal `sub_catchments.shp` in `EPSG:4326`.
- Loaded HydroBASINS level 7 from the local HydroBASINS Standard Africa artifact.
- Computed polygon intersections geometrically.
- Computed areas with WGS84 geodesic area in square kilometres.
- Tested anchor-point containment with `covers()`.

Local diagnostic outputs:

- Under `outputs/zimbabwe_geoportal_subcatchments_2025/`:
  - `zimbabwe_geoportal_upper_mzingwane_boundary_comparison_2026-06-10.csv`
  - `zimbabwe_geoportal_upper_mzingwane_hydrobasins_level7_overlaps_2026-06-10.csv`
- Under `outputs/hydrosheds_boundary_decision/`:
  - `upper_mzingwane_boundary_candidate_table_2026-06-10.csv`
- These outputs are diagnostics only. They do not create or accept a modelling boundary.

Reproduced facts:

| Check | Result |
| --- | --- |
| Geoportal feature count | 47 |
| Geoportal CRS | `EPSG:4326` |
| Geoportal valid geometries | 47 / 47 |
| Geoportal `Upper Mzingwane` area | `7321.482 km2` |
| HydroBASINS `HYBAS_ID=1071528840` geodesic area | `3689.484 km2` |
| HydroBASINS `SUB_AREA` attribute | `3700.0 km2` |
| Geoportal/HydroBASINS intersection | `3648.885 km2` |
| HydroBASINS candidate covered by Geoportal share | `0.988996` |
| Geoportal feature covered by HydroBASINS candidate share | `0.498381` |
| Mzingwane Dam anchor | Geoportal `Upper Mzingwane` |
| Esigodini anchor | Geoportal `Upper Mzingwane` |
| Gwanda contrast anchor | Geoportal `Shashe` |

## Fact-Check Conclusion

The original area concern was valid, but the exact status has changed.

Earlier phrasing:

- `untraced ~2138 km2 reference`

More accurate phrasing after fact check:

- `literature-reported, repeatedly cited, but source-chain- and geometry-unresolved ~2138 km2
  reference`

The boundary problem remains unresolved because the project now has three non-equivalent
boundary concepts:

1. Literature-reported `~2138 km2` Upper Mzingwane study area, but no reusable geometry yet.
2. HydroBASINS level 7 `HYBAS_ID=1071528840`, about `3700 km2`, globally consistent hydrological
   unit.
3. Zimbabwe Geoportal `Upper Mzingwane`, about `7321.5 km2`, local named or management-style
   sub-catchment feature.

No checked source proves that any one of these is the accepted modelling boundary for the IFPM
prototype. SRTM, CHIRPS, overlay, scoring, and interpretation remain blocked.

## Next Verification Step

Find the actual boundary geometry or authoritative definition behind the `~2138 km2` literature
area. The first public-source hunt is recorded in
`context/docs/project-management/upper_mzingwane_boundary_source_hunt_2026-06-10.md`.
Priority paths:

1. Request the Upper Mzingwane study-area polygon and source citation from the relevant authors.
2. Ask ZINWA or the Mzingwane Catchment office for the `National catchment database` boundary
   layer, or ask the mentor whether they can supply/approve the intended polygon.
3. Locate the 1995/1996 Bulawayo-Matabeleland-Zambezi feasibility-study volumes/maps and check
   whether they define `Upper Umzingwane`.
4. If only a figure is available, georeference or digitize it as a provisional boundary only
   after explicit review.

## Adversarial Review

Correctness and domain-boundary angle:

- Finding: `literature-supported` could overstate the `~2138 km2` source chain because checked
  sources repeat the area but do not supply an authoritative polygon, outlet, projection, or
  area method.
- Triage: downgraded the label to `literature-reported, repeatedly cited, but source-chain- and
  geometry-unresolved`, added the source-chain evidence table, and kept the boundary state as
  not accepted.
- Finding: the HydroSHEDS discovery note still implied that no local boundary candidate had been
  compared.
- Triage: updated it to state that the Geoportal named-feature comparison is complete, but no
  mentor or local authority has accepted it as the modelling boundary.

Engineering and workspace-boundary angle:

- Finding: tracked docs now depend on this fact-check note.
- Triage: this note must be staged with the referencing docs.
- Finding: the Geoportal direct object URL was unnecessary in committed registry/preflight docs.
- Triage: removed the exact object URL and kept portal page, resource name, checksum, and
  file-size evidence instead.
- Finding: local geometry values needed a traceable evidence pointer.
- Triage: added the local diagnostic output paths and clarified that they are diagnostics only.

Validation after triage:

- `git diff --check`
- `bash bin/validate-boundary.sh`
- sensitive scan for credentials, object URL fragments, and portal login material
