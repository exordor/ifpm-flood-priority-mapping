# Dataset Registry: INGEMMET Catastro Minero (Peru Pilot)

Status: queried via the public ArcGIS REST API for PE1 features. This is the authoritative
official Peru mining cadastre — a strict upgrade over the OSM quarry/industrial proxy.

## Dataset Identity

- Dataset id: `ingemmet_catastro_minero_peru_pilot`
- Short name: INGEMMET Pequeña Minería (small-scale / ASM mining points)
- Reusable download: yes — features are queryable by bounding box via the public REST API
- Spatial unit or mask: query intersecting the PE1 boundary envelope
- Temporal coverage: INGEMMET "small-scale mining" module (Memorando N° 0738-2014-INGEMMET/DRME);
  records carry `f_mtra` dates.

## Source And Access

- Source organization: INGEMMET (Instituto Geológico Minero y Metalúrgico del Perú)
- Source portal: GEOCATMIN `https://geocatminnube.ingemmet.gob.pe/geocatmin/`
- Service endpoint (machine-readable): ArcGIS REST
  `https://geocatminnube.ingemmet.gob.pe/arcgis/rest/services/SERV_PEQUENA_MINERIA/MapServer/0`
- Access method: public ArcGIS MapServer query API (`/query`), no login. The portal is an
  ArcGIS JS web GIS; the underlying MapServer is publicly queryable.
- Licence or terms: INGEMMET states the catastro data are "referential, for consultation only"
  (carácter referencial, solo de consulta). Mining rights update daily. Re-check INGEMMET terms
  before any public release/redistribution. Cite INGEMMET/GEOCATMIN.
- Account, registration, or approval needed: none for query/read.

## Services Inspected

- `SERV_PEQUENA_MINERIA` (layer 0, "Pequeña Minería", point) — USED. Small-scale/ASM mining
  points with mineral (e.g. Au), mine code (`cd_mtra`), coordinates, lab assays. This is the
  primary ASM pressure source.
- `SERV_CATASTRO_MINERO` (layer 3) — a specific named polygon case study (Marcona/SHOUGANG),
  not the general cadastre in the public REST layer list. Not used for PE1 (0 features there).
- `SERV_CARTERA_PROYECTOS_MINEROS` (layers 0-2, point) — mining project portfolio. Available
  as a future extension if formal-project pressure is needed alongside ASM.

## Query Record (PE1)

- Access date: 2026-06-30
- Query bbox (EPSG:4326): approximately -72.31, -16.86, -71.59, -16.14 (PE1 envelope)
- Features returned in PE1: **11** small-scale mining points (vs the OSM proxy's 32
  quarry/industrial polygons over PE1+5km, which were a weaker land-use proxy).
- Feature attributes include: `cd_mtra` (mine code), `mina` (mineral, e.g. Au), `este/norte/zona`
  (UTM), `longitud/latitud`, lab assays. The geometry is point.
- Raw destination: `data/raw/ingemmet_catastro_minero_peru_pilot/`

## Notes And Limits

- This is **point** data (mine occurrences/locations), not active-disturbance polygons. It locates
  ASM pressure more accurately than the OSM land-use proxy but does not by itself map active
  mining footprint. Treat as "ASM pressure point density/proximity", consistent with the claim
  level of the mining criterion.
- The catastro is "referential"; concession-status is not always reflected in the
  PEQUENA_MINERIA point layer. The SERV_CATASTRO_MINERO cadastre polygons would add concession
  status if a public layer becomes available.
- This upgrades the PE1 mining criterion from `diagnostic_only` OSM proxy to `provisional`
  official-source point evidence. It does not make the criterion a validated active-mining truth.
