# Peru exposure and event-context data implementation record

Date: 2026-07-08

Purpose: record the source assessment and the implementation completed on
2026-07-10 for three Peru reporting/model gaps:

- people exposed;
- adaptive capacity / socioeconomic vulnerability;
- event-point comparison context.

WorldPop, INEI poverty, and SINPAD records are now downloaded and registered.
The current implementation uses population/building evidence in the PIM,
exports poverty/health remoteness as context, and treats SINPAD as co-location
evidence rather than validation. The dataset registry files are authoritative.

## Implemented sequence

1. Add a population-exposure layer and summary statistic.
2. Upgrade the current socioeconomic criterion from road/access-only to
   road/access plus population and mapped-building exposure indicators.
3. Add an event-point co-location diagnostic using official Peru disaster records.
4. Use satellite flood extent and SIGRID/CENEPRED hazard products as secondary
   checks, not as the only validation evidence.

## Candidate sources

| Gap | Recommended source | Use in current project | Status / limitation | Proposed local destination |
|---|---|---|---|---|
| People exposed | WorldPop population count, Peru, 100 m | Count population inside high / very-high priority cells; optional socioeconomic exposure component | Good first choice for gridded population. Need choose year, constrained/unconstrained, adjusted/unadjusted population product. | `data/raw/worldpop_peru_population/` |
| People exposed fallback | GHSL GHS-POP | Cross-check population exposure totals against an independent global population grid | Coarser workflow and tile/product selection needed; useful as sensitivity check. | `data/raw/ghsl_peru_population/` |
| Age/dependency vulnerability | WorldPop age-sex structures or dependency ratio products | Estimate children/elderly/dependency exposure in priority areas | Useful for "vulnerable population exposed"; should not be called adaptive capacity alone. | `data/raw/worldpop_peru_age_sex/` |
| Poverty context | INEI Mapa de Pobreza Provincial y Distrital 2018 | District-level response-capacity context outside the PIM | District-scale, not pixel-scale; joined only as a district attribute. | `data/raw/inei_peru_poverty_2018/` |
| Health-service access | MINSA REUNIS / RENIPRESS / georeferenced health facilities | Distance or travel-time proxy to health facilities; supports emergency-response capacity discussion | Need confirm downloadable table with coordinates and licence before use. | `data/raw/minsa_peru_health_facilities/` |
| Current access indicator | OSM / Geofabrik roads already used | Road/access proximity and road length in high-priority areas | Already available; not socioeconomic vulnerability by itself. | existing `data/raw/geofabrik_osm_peru_pilot/` |
| Event context | INDECI SINPAD emergency records, ArcGIS REST `EMERGENCIAS_SINPAD` | Compare historical flood/rainfall event points and reported impacts with PIM classes | Point records are report locations, contain repeated coordinates, and are not flood extents. | `data/validation/indeci_sinpad_peru_flood_events/` |
| Validation secondary | CENEPRED / SIGRID flood hazard and risk products | Compare model high-priority areas with official susceptibility/hazard products | Useful as independent hazard-context comparison; not event validation. Need locate WMS/downloadable layers for Arequipa. | `data/validation/cenepred_sigrid_peru_flood_hazard/` |
| Validation secondary | Global Flood Database / MODIS events | Compare with observed flood extents where events overlap Peru/Arequipa | 250 m MODIS, 2000-2018, large-event bias; likely sparse for small semi-arid catchments. | `data/validation/global_flood_database_peru/` |
| Validation optional | Sentinel-1 event mapping | Build event-specific flood masks after selecting dates from SINPAD / reports | Best spatial detail, but requires event-date selection and a separate remote-sensing workflow. | `data/validation/sentinel1_peru_event_floods/` |

## How each gap should be resolved

### 1. People exposed

Preferred approach:

1. Download WorldPop Peru population count for a selected year, likely 2020 or
   latest available consistent product.
2. Reproject / resample to the Peru reference grid.
3. Keep population as a count surface, not a 0-1 score, for summary statistics.
4. Calculate:
   - total people inside the study boundary;
   - people in high and very-high PIM classes;
   - people in candidate top-priority areas;
   - people near high-priority mining/access intersections, if needed.

Recommended reporting label:

`People potentially exposed in high-priority cells`

Do not label this as observed affected population.

### 2. Socioeconomic exposure and response-capacity context

Current implementation:

1. Keep the current OSM road/access layer as an access component.
2. Combine WorldPop population and OSM mapped-building density as provisional
   infrastructure exposure.
3. Keep INEI poverty and OSM health-service remoteness as diagnostic context
   outside the current PIM.

```text
SV = 0.45 road/access proximity +
     0.55 infrastructure exposure

infrastructure exposure = 0.50 population + 0.50 mapped buildings
```

The exact weights should be exposed in the PIM subcriteria table.

Recommended reporting label: `Socioeconomic exposure indicators`

Avoid:

- `adaptive capacity` if only roads are used;
- `social vulnerability` if poverty/age/health access are not included.

### 3. Event-point co-location

Implemented approach:

1. Query INDECI SINPAD for Arequipa flood-relevant hazards:
   - `INUNDACION`
   - `LLUVIAS INTENSAS`
   - `ALUVIONES`
   - `HUAYCO`
   - `DESBORDE`
2. Keep point geometry and impact fields:
   - affected people: `SAFECTA`
   - displaced/affected households: `SDAMNI`
   - damaged/destroyed housing fields
   - roads affected/destroyed: `SCARRE_AFECTA`, `SCARRE_DESTRU`
   - bridges affected/destroyed: `SPUENTE_AFECTA`, `SPUENTE_DESTRU`
3. Intersect SINPAD points with PIM classes.
4. Report diagnostic co-location separately for all records, unique locations,
   flood records, and unique flood locations.
   - percent of relevant SINPAD events falling in high / very-high PIM cells;
   - whether affected-road/bridge records are concentrated in higher PIM
     classes;
   - distance of event points to top-priority cells.
5. Use SIGRID/CENEPRED and Global Flood Database as independent cross-checks.

Recommended reporting label: `Diagnostic co-location with official emergency records`

Do not write:

`validated flood-risk map`

until the event comparison is actually run and documented.

## Implemented scripts

1. `bin/acquire/query_peru_sinpad_flood_events.py`
   - Queries the INDECI ArcGIS REST service.
   - Filters Arequipa flood-relevant records.
   - Writes GeoPackage/CSV under `data/validation/`.

2. `bin/analysis/summarize_peru_population_by_pim_class.py`
   - Reads a downloaded WorldPop/GHSL raster.
   - Aligns it to the Peru reference grid.
   - Writes population exposure summaries under `outputs/`.

3. `bin/criteria/build_peru_exposure_indicators.py`
   - Combines population and mapped-building infrastructure with road/access.
   - Writes exposure indicators plus poverty and health-remoteness context.

4. `bin/analysis/compare_peru_pim_sinpad_colocation.py`
   - Intersects SINPAD records with PIM classes.
   - Writes co-location cohorts and a map-ready point overlay.

## Source links found

- WorldPop Hub: https://hub.worldpop.org/
- WorldPop age/sex structures: https://hub.worldpop.org/project/categories?id=8
- WorldPop dependency ratios: https://hub.worldpop.org/project/categories?id=10
- GHSL direct download: https://human-settlement.emergency.copernicus.eu/download.php
- INEI poverty map 2018: https://www.gob.pe/institucion/inei/informes-publicaciones/3204872-mapa-de-pobreza-provincial-y-distrital-2018
- MINSA REUNIS: https://www.minsa.gob.pe/reunis/
- INDECI SINPAD ArcGIS REST layer: https://geosinpad.indeci.gob.pe/indeci/rest/services/Emergencias/EMERGENCIAS_SINPAD/MapServer/0?f=pjson
- SIGRID / CENEPRED: https://www.gob.pe/13122-acceder-al-sistema-de-informacion-para-la-gestion-del-riesgo-de-desastres-sigrid
- Global Flood Database in Earth Engine: https://developers.google.com/earth-engine/datasets/catalog/GLOBAL_FLOOD_DB_MODIS_EVENTS_V1

## Search/probe evidence

- The INDECI SINPAD REST layer is queryable and exposes point geometry in
  EPSG:4326.
- A metadata probe on 2026-07-08 found fields for event type, year/month,
  department/province/district, affected people, damaged housing, affected
  roads, and affected bridges.
- A sample Arequipa query for flood/rainfall/aluvion-related event names returned
  records and a count of 1,955 candidate Arequipa records before study-boundary
  filtering.
