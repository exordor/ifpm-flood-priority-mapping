# Upper Mzingwane Boundary Source Hunt

Updated: 2026-06-10

Status: source hunt completed for public evidence. Boundary still not accepted.

## Question

Find where the commonly reported `~2138 km2` Upper Mzingwane area may come from, and
separate repeat citations from sources that could actually provide boundary geometry.

This search did not download SRTM, CHIRPS, overlay inputs, or new real GIS boundary data. Public
PDFs were parsed only as temporary research evidence.

## Short Answer

The `~2138 km2` value is real as a repeated literature value, but the public sources checked do
not expose the exact GIS boundary, outlet definition, projection, or area-calculation method.

The strongest boundary-source leads are:

1. `ZINWA. 2003. National catchment database. Unpublished GIS database, Harare.`
2. Later `ZINWA (2010), National catchment database, unpublished GIS database, Harare`
   references in drought and local-knowledge studies.
3. The `Bulawayo-Matabeleland-Zambezi: Water supply feasibility study` record, which confirms
   a 1996 three-volume water-supply feasibility study with maps, graphs, and tables.
4. The 1995 `Bulawayo/Matabeleland Water Supply Feasibility Study, Zimbabwe` entry listed in
   the LBPTC 2010 scoping report for `Upper Umzingwane`.
5. Surveyor General / local map-sales sources mentioned by LBPTC 2010 for Zimbabwe
   sub-catchments and rivers.

These are leads, not accepted data. They require access through ZINWA, Zimbabwe Surveyor
General, the feasibility-study holder/library, an author request, or mentor-provided files.

## Evidence Classes

### Area Repeaters

These sources support that `2138 km2` is a published value, but they do not supply reusable
geometry.

| Source | Evidence | Boundary source exposed? |
| --- | --- | --- |
| Maviza and Ahmed 2020, International Journal of Remote Sensing | Uses Upper-Mzingwane as the study area and reports Landsat 5 TM / Landsat 8 OLI imagery for 1989, 2004, 2013, and 2018. The public text shows the study-area map and area-based LULC outputs, but does not publish or name the study-area polygon source. | no |
| Maviza, Grab, and Engelbrecht 2022 / public preprint | Reports UMS covers `2138 km2`; uses selected precipitation stations and station-distance criteria. | no |
| Chisadza et al. 2023, Geomatics, Natural Hazards and Risk | Reports approximately `2138 km2`; figure caption says `Source: Author`; data availability says materials can be requested from the first author. | no |
| Chisadza et al. 2022 surface-water study | Reports `2,138 km2` and then uses Landsat imagery from USGS EarthExplorer for 1990, 2000, 2011, and 2020. | no |
| Frontiers WEF nexus article, 2026 | Lists four Mzingwane sub-catchments with Upper Mzingwane at `2,138 km2`, citing LBPTC 2010, Sibanda et al. 2020, and Maviza et al. 2022. | no |

### Boundary-Source Leads

These sources are more likely to explain where the boundary geometry came from, but they are
not currently open downloadable shapefiles.

| Lead | Why it matters | Current limitation |
| --- | --- | --- |
| ZINWA National catchment database, 2003 | Love et al. 2005 uses a Mzingwane map with `Base map after ZINWA (2003)` and cites the unpublished GIS database. | unpublished GIS database |
| ZINWA National catchment database, 2010 | Later drought/local-knowledge papers cite `ZINWA (2010), National catchment database, unpublished GIS database, Harare`. | unpublished GIS database |
| Bulawayo/Matabeleland water-supply feasibility studies | LBPTC 2010 lists a 1995 feasibility study for `Upper Umzingwane`; FAO AGRIS confirms a 1996 Bulawayo-Matabeleland-Zambezi feasibility study with maps, graphs, and tables. | bibliographic record only |
| Surveyor General map data | LBPTC 2010 says Zimbabwe sub-catchments/rivers maps were available through Surveyor General map sales in formats such as GeoTIFF, JPEG, and AutoCAD conversion. | access and licensing unclear |
| Author-held study-area polygon | Maviza and Ahmed 2020 and Chisadza et al. 2023 include study-area maps and area-based outputs, so an underlying polygon likely exists even though the public text does not disclose it. | source not disclosed in public text |

## Checked Details

### Maviza and Ahmed 2020

Public page:

`https://www.researchgate.net/publication/340597367_Analysis_of_past_and_future_multi-temporal_land_use_and_land_cover_changes_in_the_semi-arid_Upper-Mzingwane_sub-catchment_in_the_Matabeleland_south_province_of_Zimbabwe`

DOI:

`https://doi.org/10.1080/01431161.2020.1731001`

Useful facts:

- Study area: Upper-Mzingwane sub-catchment in Matabeleland South.
- Remote sensing inputs: Landsat 5 TM and Landsat 8 OLI for 1989, 2004, 2013, and 2018.
- Processing: Random Forest, SVM, TerrSet Land Change Modeller / Markov Chain / MLP.
- The public text shows the study-area map and area-based LULC outputs, but does not identify
  or publish the study-area polygon source.

Interpretation:

- This is a key modern source for the `2138 km2` boundary concept.
- It is not enough to reproduce the exact boundary unless the authors or supplementary files
  provide the study-area polygon.

### Chisadza et al. 2023

Public PDF mirror:

`https://artefacts-discovery.researcher.life/full_text/DA-2/79/7913cbcb7eb0397b902642ff16b97ab6/full_text/3ee601a3a1244c126f790c859bb44edc.pdf`

DOI:

`https://doi.org/10.1080/19475705.2023.2190857`

Useful facts:

- Reports the study site covers approximately `2138 km2`.
- Figure 1 caption marks the study-area map as `Source: Author`.
- Data sources include Landsat TM/ETM/OLI from USGS EarthExplorer, SRTM DEM from USGS,
  ZIMSTAT population records, CHIRPS precipitation, and TerraClimate ET/runoff.
- Data availability states the data/materials can be made available from the first author upon
  reasonable request.

Interpretation:

- This is evidence that the same boundary concept is active in recent local studies.
- The best path from this paper is an author request for the study-area polygon or source note.

### Love, Taigbenu, and Jonker 2005

Public PDF:

`https://assets.publishing.service.gov.uk/media/57a08ca1e5274a27b2001305/WP1-Mzingwane.pdf`

Useful facts:

- The report is `An overview of the Mzingwane Catchment, Zimbabwe`.
- Figure 1 says the Mzingwane base map is after `ZINWA (2003)`.
- The references cite `ZINWA. 2003. National catchment database. Unpublished GIS database,
  Harare.`
- It reports broader Mzingwane-related catchment areas, but not the `2138 km2` Upper
  Mzingwane polygon.

Interpretation:

- This is the strongest public clue for an authoritative GIS source behind local Mzingwane
  catchment/subcatchment maps.
- Because the database is unpublished, it cannot yet be treated as reusable project data.

### LBPTC 2010

Public PDF:

`https://dsc.duq.edu/cgi/viewcontent.cgi?article=1000&context=limpopo-reports`

Useful facts from local text extraction:

- The main report has Table 3.1 for proposed sub-basins and lists `Mzingwane 20 348
  Zimbabwe`, which is a broader basin concept, not the `2138 km2` Upper Mzingwane study area.
- Table 4.3 lists `Bulawayo/ Matabeleland Water Supply Feasibility Study, Zimbabwe`, dated
  1995, under `Upper Umzingwane`.
- Table 4.8 points to Zimbabwe sub-catchments and rivers map availability through Surveyor
  General map sales.

Interpretation:

- The Frontiers 2026 article cites LBPTC 2010 for the four-subcatchment area list, but the
  main report text checked so far does not itself expose a `2138 km2` GIS polygon.
- LBPTC is still useful as a pointer to older feasibility studies and Surveyor General/ZINWA
  map channels.

### FAO AGRIS Feasibility-Study Record

Public bibliographic record:

`https://agris.fao.org/search/en/providers/122524/records/64775dba6dafec353e5131ae`

Useful facts:

- Record title: `Bulawayo-Matabeleland-Zambezi: Water supply feasibility study`.
- Year: 1996.
- Publisher/corporate author: Matabeleland Zambezi Water Trust, Harare.
- The record says it is in three volumes and includes maps, graphs, and tables.

Interpretation:

- This may be related to, or a nearby bibliographic expression of, the LBPTC 1995
  `Bulawayo/Matabeleland Water Supply Feasibility Study` lead.
- It is not a boundary source until the actual volumes/maps are obtained and checked.

## Working Conclusion

The most likely explanation is a source-chain split:

1. Modern remote-sensing and vulnerability papers use or reproduce a narrower Upper Mzingwane
   study polygon with area around `2138 km2`.
2. The public papers usually expose remote-sensing/climate/population inputs, but not the
   study-area polygon source.
3. Older water-management sources point toward ZINWA and feasibility-study GIS/map products,
   many of which are unpublished or library-held.
4. The open Zimbabwe Geoportal `Upper Mzingwane` feature and HydroBASINS candidate are valid
   comparison sources but do not match the `2138 km2` literature polygon.

Therefore the `2138 km2` value should be treated as:

`literature-reported and repeatedly used, with probable ZINWA/author-held/local-study boundary
origin, but still unreproducible from public geometry`.

## Next Search Actions

1. Contact or request data from the first/corresponding authors of Chisadza et al. 2023 and
   Maviza and Ahmed 2020 for the Upper Mzingwane study-area polygon and source citation.
2. Ask ZINWA or the Mzingwane Catchment office for the `National catchment database` boundary
   layer or an official Upper Mzingwane sub-catchment polygon.
3. Locate the 1995/1996 Bulawayo-Matabeleland-Zambezi feasibility-study volumes and inspect
   maps/tables for Upper Umzingwane boundary/area.
4. Ask the mentor whether an author-requested polygon, ZINWA polygon, digitized published
   figure, or HydroBASINS-compatible approximation is acceptable for the first prototype.

## Adversarial Review

Correctness/domain angle:

- Risk: treating repeated `2138 km2` mentions as proof of geometry would create a false
  boundary acceptance.
- Response: this note keeps repeaters separate from geometry-source leads and keeps the
  boundary blocked.

Engineering/boundary angle:

- Risk: temporary PDFs or extracted text could leak into committed data.
- Response: only this public-source summary is tracked; public PDFs and extracted text remain
  under ignored temporary paths.

Decision angle:

- Risk: spending more time searching open web may have diminishing returns because the strongest
  sources are unpublished or author-held.
- Response: next actions shift from web search to author/authority/mentor request.
