# Dataset Registry: INDECI SINPAD Peru event-point context

Status: queried 2026-07-10 for Arequipa flood/rainfall/aluvion-style emergency records; used for the former Peru study area (frozen, `peru_former`).

## Dataset Identity

- Dataset id: `indeci_sinpad_peru_flood_events`
- Short name: INDECI SINPAD flood-relevant emergency records, Arequipa
- Project role: event-point co-location context for Peru PIM priority classes
- Study area: Arequipa department, then the former Peru study area (frozen, `peru_former`) and a 20 km
  context buffer
- Spatial unit or mask: point records with department/province/district
  attributes
- Temporal coverage: event records as exposed by SINPAD service at access date

## Source And Access

- Source organization: INDECI Peru
- Source service:
  `https://geosinpad.indeci.gob.pe/indeci/rest/services/Emergencias/EMERGENCIAS_SINPAD/MapServer/0`
- Access method: public ArcGIS REST `/query`, no login
- Access date: 2026-07-10
- Licence or terms: public government GIS service; redistribution terms not stated

## Acquisition

- Destination: `data/validation/indeci_sinpad_peru_flood_events/`
- Query filter:
  `DEPARTAMENTO='AREQUIPA'` and flood-relevant `FENOMENO` names containing
  `INUND`, `LLUVI`, `ALUVI`, `HUAY`, or `DESBORDE`
- Script:
  `.venv/bin/python bin/acquire/query_peru_former_sinpad_flood_events.py`
  (Script removed 2026-10-11; recover with `git show 6e2ed8b:bin/acquire/query_peru_former_sinpad_flood_events.py`.)

## Files

- Checksum (SHA-256):
  `d34e1da366bc157104c62c9c446cce0a86d4b3845ae371eddec2aef8f88061f9`
- Raw GeoPackage: `arequipa_sinpad_flood_relevant.gpkg`, 638,976 bytes
- Arequipa flood-relevant records with valid geometry: 1,955
- Records inside the former Peru study area: 25
- Records inside the former Peru study area plus 20 km context buffer: 452
- Manifest:
  `outputs/peru_former_sinpad_flood_events/sinpad_download_manifest.json`
- CRS: EPSG:4326 points; boundary filtering uses `peru_former`

## Processing And Use

- Raw data path: `data/validation/indeci_sinpad_peru_flood_events/`
- Derived output path: `outputs/peru_former_sinpad_flood_events/`
- Use:
  - overlay flood/rainfall/aluvion emergency records with PIM priority classes;
  - compare all records, unique coordinates, explicitly flood-labelled records,
    and unique flood coordinates with the highest-priority quintile;
  - summarize affected people and damaged infrastructure fields as event context.
- Key fields:
  - `FENOMENO`, `DES_GRUPAL_FENOMENO`
  - `ANHO`, `MES`, `FECHA`
  - `DEPARTAMENTO`, `PROVINCIA`, `DISTRITO`, `COD_UBIGEO`
  - `SAFECTA`, `SDAMNI`, `SFALLE`, `SLESI`
  - `SCARRE_AFECTA`, `SCARRE_DESTRU`, `SPUENTE_AFECTA`, `SPUENTE_DESTRU`
- Known limitations:
  - event points may be administrative or report-location points, not mapped
    flood extents;
  - repeated coordinates are not independent observations;
  - records support co-location checks only, not inundation depth;
  - the filter intentionally includes intense rainfall and aluvion/debris-flow
    style hazards for semi-arid flood-prioritisation context.
