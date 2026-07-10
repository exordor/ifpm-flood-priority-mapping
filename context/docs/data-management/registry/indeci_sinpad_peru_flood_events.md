# Dataset Registry: INDECI SINPAD Peru event-point context

Status: refreshed on 2026-07-10; public ArcGIS REST service query scripted for
Arequipa flood/rainfall/aluvion-style emergency records.

## Dataset Identity

- Dataset id: `indeci_sinpad_peru_flood_events`
- Short name: INDECI SINPAD flood-relevant emergency records, Arequipa
- Data class: `LOCAL_DATA`
- Reusable download: yes
- Project role: event-point co-location context for Peru PIM priority classes;
  not independent validation
- Study area: Arequipa department, then current Peru study boundary and 20 km
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
- Account, registration, or approval needed: none identified
- Licence or terms: public government GIS service; confirm redistribution terms
  before including raw records in any public release

## Download Plan

- Destination: `data/validation/indeci_sinpad_peru_flood_events/`
- Expected file types: GeoPackage and CSV
- Query filter:
  `DEPARTAMENTO='AREQUIPA'` and flood-relevant `FENOMENO` names containing
  `INUND`, `LLUVI`, `ALUVI`, `HUAY`, or `DESBORDE`
- Script:
  `.venv/bin/python bin/acquire/query_peru_sinpad_flood_events.py`
- Temporary path: none

## Verification

- Download completed: yes
- Download verification date: 2026-07-10
- Checksum scope: downloaded GeoPackage
- Checksum algorithm: SHA-256
- Checksum value:
  `d34e1da366bc157104c62c9c446cce0a86d4b3845ae371eddec2aef8f88061f9`
- Raw GeoPackage size: 638,976 bytes
- Arequipa flood-relevant records with valid geometry: 1,955
- Records inside the current Peru study boundary: 25
- Records inside the current Peru study boundary plus 20 km context buffer: 452
- Expected output manifest:
  `outputs/indeci_sinpad_peru_flood_events/sinpad_download_manifest.json`
- CRS or georeferencing check: input/output point geometry should be EPSG:4326;
  boundary filtering uses the current Peru pilot boundary

## Processing And Use

- Raw data path: `data/validation/indeci_sinpad_peru_flood_events/`
- Derived output path: `outputs/indeci_sinpad_peru_flood_events/`
- Planned use:
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
  - records support co-location diagnostics, not hydraulic inundation depth or
    model validation;
  - the filter intentionally includes intense rainfall and aluvion/debris-flow
    style hazards for semi-arid flood-prioritisation context.

## Release Boundary

- May be committed: no raw data
- May be used in public examples: no raw records unless terms are checked
- Public-safe summary available: this registry note and aggregate counts only
