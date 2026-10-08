# Dataset Registry: Goslar official hydrology, flood context, and infrastructure v1

- Dataset id: `goslar_official_hydrology_flood_infrastructure_v1`
- Status / claim level: `validation_candidate/context`; independent overlays and
  evidence, not active PIM score inputs
- Access date: 2026-08-17
- Study area: `goslar_harz_2024_focus_extent` and its 12 km context buffer
- Reproducible command:
  `.venv/bin/python bin/acquire/pull_goslar_official_hydrology_flood_infrastructure.py`
- Raw destination: `data/raw/goslar_official_hydrology_and_flood_data/`
- Event-report destination:
  `data/validation/goslar_harz_2024_focus_area/official_event_and_hazard_data/`
- Derived destination: `outputs/goslar_official_hydrology_and_flood_data/`
- Checksum manifest: `outputs/goslar_official_hydrology_and_flood_data/source_lineage.json`

## Sources

1. **NLWKN July 2017 flood report**
   - URL: https://www.nlwkn.niedersachsen.de/download/124949/Hochwasserbericht_Juli_2017.pdf
   - Local file: `NLWKN_Hochwasserbericht_Juli_2017.pdf`
   - Role: official event narrative, precipitation totals, gauged peaks and
     return-period context for the July 2017 event.
   - Important values: the precipitation centre was near Goslar/Bad Harzburg;
     Eckertalsperre recorded 304 mm in the event window and Schladen/Oker
     reached 357 cm on 26 July 2017.

2. **WRRL drainage basins and river-segment network**
   - URLs:
     https://www.umweltkarten-niedersachsen.de/Download_OE/WRRL/DrainBasin_Waterbody_LOCAL.zip
     and https://www.umweltkarten-niedersachsen.de/Download_OE/WRRL/WFD_RWSEG_LOCAL.zip
   - Role: official water-body/drainage-basin polygons and river segments. The
     focus extent overlaps seven basin/water-body polygons, led by `Abzucht`
     (13.85 km²), `Granetalsperre` (4.62 km²), `Grane` (3.22 km²), and
     `Okertalsperre` (0.47 km²).
   - Derived layer:
     `outputs/goslar_official_hydrology_and_flood_data/goslar_wfd_drainage_basins_focus_overlap.gpkg`

3. **HWRM-RL Oker and Innerste flood-hazard boundaries**
   - URLs:
     https://www.umweltkarten-niedersachsen.de/Download_OE/HWRM-RL/Daten/HWRM-RL_Daten_Oker.zip
     and https://www.umweltkarten-niedersachsen.de/Download_OE/HWRM-RL/Daten/HWRM-RL_Daten_Innerste.zip
   - Role: independent scenario flood-hazard boundary context (Oker HQ20/HQ100/
     HQextrem; Innerste HQ25/HQ100/HQextrem).
   - Context check: the former ZLW focus extent had no HWRM overlap, while the
     current official WRRL reference grid has 62 direct 30 m overlap cells.
     Within the focus+12 km context, mapped areas total about 1.23-2.76 km²
     per scenario.
   - Derived layer:
     `outputs/goslar_official_hydrology_and_flood_data/goslar_hwrm_flood_hazard_boundaries_12km.gpkg`
   - Boundary: these are modelled regulatory scenarios, **not** the observed
     July 2017 inundation footprint and not event validation labels.

4. **OpenStreetMap critical-infrastructure candidates**
   - Source: Overpass query for schools, hospitals/healthcare, emergency
     facilities, fire/police stations, works, substations and railway stations
     in Landkreis Goslar.
   - Local snapshot: `osm_goslar_infrastructure_overpass.json`
   - Licence: ODbL, © OpenStreetMap contributors.
   - Role: independent candidate replacement for the WorldCover built-up proxy
     after class selection and QA. It is not yet an active PIM component.

## QA and remaining gaps

- Source archives and the official PDF have SHA-256 entries in
  `source_lineage.json`.
- Official basin polygons now resolve the main hydrologic naming/geometry gap
  around Goslar, but a full upstream contributing area still requires a
  chain-level decision on combining WRRL polygons and/or DEM delineation.
- HWRM hazard layers provide independent regulatory hazard context but do not
  replace a 2017 observed flood extent.
- The official NLWKN report supplies event precipitation/gauge peak context;
   a machine-readable 15-minute 2017 gauge time series has not yet been found.
- OSM infrastructure includes many emergency micro-features (especially fire
  hydrants); only selected facility classes should be promoted to an exposure
  indicator after explicit filtering.
- The accepted QGIS overlay snapshot contains 375 candidate facilities from
  seven classes: substations, schools, fire stations, works, police, hospitals
  and railway stations. It is stored as
  `osm_goslar_infrastructure_candidates.gpkg` and remains external to scoring.

## 2026-08-17 provisional chain integration

- The active Goslar chain now uses
  `goslar_wrrl_water_bodies_reference_v1` (153.779 km², union of the seven
  official WRRL polygons intersecting the former focus extent) instead of the
  ZLW layout box. The union is a provisional official water-body reference,
  not an observed 2017 flood footprint.
- The SoilGrids K snapshot was refetched for the enlarged official-basin
  window and pinned under `data/raw/soilgrids_250m_goslar_official_basin/`.
- Road access uses a full Overpass road snapshot for the official basin window;
  population uses the official Zensus 2022 100 m grid filtered to that window.
- `critical_infrastructure` now uses proximity to 375 filtered OSM facility
  candidates (2 km linear decay), replacing the WorldCover built-up proxy for
  the active chain. It remains community evidence, not an official facility
  inventory.
- With an official hydrologic reference and an independent infrastructure
  proxy, the active Goslar output status is upgraded from `diagnostic_only`
  to `provisional`, matching Secocha's evidence level. It is still not
  `final_claim`: no observed 2017 inundation footprint has been obtained.
- `bare_soil_vegetation_loss` remains all-zero because the CLMS HRL requests
  are still queued. Its Secocha weight is retained for strict cross-site
  comparability; replacement awaits HRL download and QA.

## 2026-09-08 reference intake from mentor

- Classification: PDF `LOCAL_DATA`; this registry addition `INTERNAL_CONTEXT`.
- Receipt: user-provided Teams screenshot shows Supervisor Weber sharing the PDF
  and two public links on 2026-09-08. Original publisher download URL was not
  supplied; private sharing URLs are intentionally not recorded.
- Local file: `data/raw/goslar_official_hydrology_and_flood_data/Abzucht_Blatt01_HWGK_L.pdf`
- Intake: moved the existing user download into the raw-data folder; no new
  remote dataset download. Size: 5686154 bytes; SHA-256: `e7c7cf5fa23c83f4a5720e1388759744dabb930002d7d553d546b3d56ff289bb`.
- Visual inspection of the one-page PDF: **Hochwassergefahrenkarte HQextrem**,
  Abzucht, NLWKN / Niedersachsen, dated 31.12.2019, scale 1:25,000.
  Printed CRS: ETRS 1989 UTM Zone 32N 8 Stellen. Legend includes inundation
  boundary and water-depth classes 0-0.5, >0.5-1, >1-2, >2-4, >4 m.
  The map is a scenario reference, not an observed 2017 flood footprint.
- Public link checked 2026-09-08:
  https://www.goslar.de/wirtschafts-und-zukunftsort/klima-umwelt-gewaesserschutz/gewaesserschutz/ueberschwemmungsgebiete-innerhalb-der-stadt-goslar
  The page describes designated flood areas using a 100-year design event
  and lists Abzucht provisional protection dated 01.04.2026. Keep this HQ100
  regulatory reference separate from the supplied HQextrem map. The linked
  Abzucht document itself has not yet been inspected.
- Discovery portal supplied:
  https://ni-lgln-opengeodata.hub.arcgis.com/
  Web text extraction returned no content; specific products, availability,
  resolution and licences remain unverified.
- Reuse: local reference inspection is possible; redistribution licence and
  original publisher file URL remain unverified. No scoring/weight changes.
- Status: `diagnostic_only`, independent scenario/reference candidate.
- Next useful step: locate native Abzucht scenario/regulatory polygons, check
  study-area coverage and CRS, then compare with PIM as scenario agreement.
  No event-validation claim or weight fitting follows from this intake.
- Inspection command: `pdftotext -layout` returned no readable map text;
  `pdftoppm -scale-to 2400 -singlefile -png` rendered the PDF for visual review.

## 2026-09-08 exploration results

- Outputs (`OUTPUT`, `diagnostic_only`):
  `outputs/goslar_reference_exploration_2026_09_08/reference_use_table.csv`
  and `coverage_check.json`. The JSON pins the three input hashes and method.
- Existing GeoJSON selection `uesg_id=917` is valid. Live layer39 attributes
  match its name, 2D calculation basis and reported area; live geometry was
  not downloaded or hash-compared.
- Abzucht polygon: 0.495468 km²; intersection with the current project boundary:
  0.297448 km² (60.0338%). On the existing 30 m raster, 561 cell centers are
  within the polygon and raster extent: 337 valid, 224 NoData. This checks
  coverage only; NoData is not low priority or model error.
- Official announcement text inspected:
  https://www.goslar.de/fileadmin/media-goslar/standort/gewaeserschutz/uesg/mbl-2026-139.pdf
  It confirms HQ100, six 1:5,000 work maps held at the city authority, and a
  1:25,000 overview. Detailed sheets were not acquired; the web screenshot
  request timed out. This announcement is not 2017 event geometry.
- Public attachment URL identified via the official 2019 link list:
  https://www.umweltkarten-niedersachsen.de/Download_OE/HWRM-RL/Abzucht/Abzucht_Blatt01_HWGK_L.pdf
  Publisher copy was not downloaded/hash-compared. The list also identifies
  HWGK_H/HWGK_M and HWRK_L/HWRK_H/HWRK_M siblings; contents remain uninspected.
- Live service:
  https://www.umweltkarten-niedersachsen.de/arcgis/rest/services/HWSchutz_wms/MapServer
  Layers 17/18/19: frequent/HQ100/extreme hazard vectors; 20/21/22: inland
  depth raster map layers; 39: provisional regulatory zones. An attribute-only
  bbox query (10.39,51.87,10.50,51.93; EPSG:4326) to 17-19 returned Oker,
  not a separately named Abzucht feature. Native Abzucht HQextrem geometry
  availability is therefore unresolved. Former HWRM_wms is absent from the
  live service directory. Map images are not quantitative depth grids.
- DGM1 metadata: https://dgm.stac.lgln.niedersachsen.de/collections/dgm1
  Confirms 1 m COG, 1 km tiles, NoData -9999 and CC-BY-4.0. Goslar metadata
  query returned `dgm1_32_598_5752_1_ni_2018`, dated 2018-04-08, with a COG
  download URL. No terrain downloaded; this date is after the 2017 event.
- Official LGLN catalogue confirms DOP imagery and building footprints:
  https://lgln-geodaten.niedersachsen.de/startseite/vertrieb_support/geodaten_marktplatz/opengeodata/opengeodata-220509.html
  Hub product pages returned HTTP 403; DGM STAC works. Local imagery dates,
  footprint coverage and their product-specific licences remain untested.
- Recommended sequence: coverage-aware HQ100 overlay with fixed weights;
  explain disagreement using criterion contributions; then small-area DGM1
  sensitivity and building exposure if useful. Evidence used to fit weights
  becomes calibration evidence and needs separate validation evidence.
- No model, weight or remote raster/vector/PDF download changes.
- Runtime: root `.venv` GeoPandas/Rasterio/NumPy, system curl for metadata.
  Initial metadata probe: `ModuleNotFoundError: No module named 'requests'`;
  curl succeeded without installation. An attempted registry append failed
  with a shell heredoc quoting error before execution; a direct patch was used.
- Local review checked semantics, dates, coverage denominators and output
  placement. No pipeline/code implementation was added.

Reproduce polygon coverage from the workspace root:

```sh
.venv/bin/python - <<'PY'
import geopandas as gpd
p = 'data/validation/goslar_2017_event_map_candidates_v1/nlwkn_current_regulatory_flood_zones_goslar.geojson'
a = gpd.read_file(p)
a = a[a.uesg_id == 917].to_crs(32632)
b = gpd.read_file('outputs/goslar_official_hydrology_and_flood_data/goslar_official_hydrologic_reference_boundary.gpkg').to_crs(a.crs)
g = a.geometry.union_all()
print(g.area / 1e6, g.intersection(b.geometry.union_all()).area / g.area)
PY
```
