# Dataset Registry: INGEMMET Catastro Minero (Southern Peru Arequipa Region)

Status: queried 2026-06-30 via the public ArcGIS REST API for the former Peru study area
(frozen, `peru_hybas_l7_6070641200`). Official Peru small-scale mining points; replaced the OSM
quarry/industrial proxy there.

## Dataset Identity

- Dataset id: `ingemmet_catastro_minero_peru_pilot`
- Short name: INGEMMET Pequeña Minería (small-scale / ASM mining points)
- Spatial unit or mask: query intersecting the Arequipa Region boundary envelope
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
  (carácter referencial, solo de consulta). Mining rights update daily. Re-check INGEMMET terms. Cite INGEMMET/GEOCATMIN.

## Services Inspected

- `SERV_PEQUENA_MINERIA` (layer 0, "Pequeña Minería", point) — USED. Small-scale/ASM mining
  points with mineral (e.g. Au), mine code (`cd_mtra`), coordinates, lab assays. This is the
  primary ASM pressure source.
- `SERV_CATASTRO_MINERO` (layer 3) — a specific named polygon case study (Marcona/SHOUGANG),
  not the general cadastre in the public REST layer list. Not used for Arequipa Region (0 features there).
- `SERV_CARTERA_PROYECTOS_MINEROS` (layers 0-2, point) — mining project portfolio. Available
  as a future extension if formal-project pressure is needed alongside ASM.

## Query Record (Arequipa Region)

- Access date: 2026-06-30
- Query bbox (EPSG:4326): approximately -72.31, -16.86, -71.59, -16.14 (Arequipa Region envelope)
- Features returned in Arequipa Region: **11** small-scale mining points (vs the OSM proxy's 32
  quarry/industrial polygons over Arequipa Region+5km, which were a weaker land-use proxy).
- Feature attributes include: `cd_mtra` (mine code), `mina` (mineral, e.g. Au), `este/norte/zona`
  (UTM), `longitud/latitud`, lab assays. The geometry is point.
- Local path: `data/raw/ingemmet_catastro_minero_peru_pilot/peru_hybas_l7_6070641200_pequena_mineria.gpkg`
  (106,496 bytes, SHA-256 `367083d9e3242f976ac45c31f03559f1f397cfe155887858a1274a74dfa6369a`, computed 2026-10-10 from the local file)

## Notes And Limits

- This is **point** data (mine occurrences/locations), not active-disturbance polygons. It locates
  ASM pressure more accurately than the OSM land-use proxy but does not by itself map active
  mining footprint. Treat as "ASM pressure point density/proximity", consistent with the claim
  level of the mining criterion.
- The catastro is "referential"; concession-status is not always reflected in the
  PEQUENA_MINERIA point layer. The SERV_CATASTRO_MINERO cadastre polygons would add concession
  status if a public layer becomes available.
- In the former Peru study area this replaced the OSM proxy as the mining-criterion source.
