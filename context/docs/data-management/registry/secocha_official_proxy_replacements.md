# Secocha official proxy replacements

- Dataset id: `secocha_official_proxy_replacements_v1`
- Access date: 2026-08-18
- Study area: active A7367 reference frame plus 25 km facility context and 5 km mining context
- Intended use: external evidence that reduces reliance on WorldCover built-up and mining-point proxies
- Claim level: `context_evidence`
- PIM use: excluded from scoring; FullAudit only, default-disabled
- Reusable/public release: local research reuse only. Public redistribution is not approved by this note.

## Sources

### MINEDU Censo Educativo 2023

- Portal: `https://escale.minedu.gob.pe/documents/inicio/Bases%20de%20datos/A.%20Censo%20Educativo/2023/`
- Product: `00_Padron.zip`, national 2023 education-service register
- Account: none
- Source size/checksum: 10,769,150 bytes; SHA-256 `4a2f80f4a43823d94790d887c609e8327155d82cd7ad9f4335f4cffdd1c873f4`
- Raw destination: `data/raw/minedu_censo_educativo_2023_secocha/`
- Quality/use: 111,715 service records yield 47 context locations within the exact 25 km filter; 12 are inside the active frame. Eleven records lack `CODLOCAL` and are retained separately at service-record level rather than being merged. Forty-six output locations are associated with declared records and one with an imputed source record. The raw DBF contains director/contact fields; the processed layer deliberately excludes them.
- Position/count limit: coordinates are statistical reference locations and are not building-accurate. Student/teacher attributes are sums reported across service rows, not deduplicated persons.
- Time: source vintage is Censo Educativo 2023; operation or damage status on 2023-02-05 is not established.

### MINAM health-facility service

- Service: `https://geoservidorperu.minam.gob.pe/arcgis/rest/services/hiroambienplanificacion/elementos_expuestos/MapServer/1`
- Product: official health-facility point context
- Account: none
- Raw destination: `data/raw/minam_health_facilities_secocha/`
- Quality/use: four records within the exact 25 km filter and zero inside the active frame. The service states that points can represent populated-centre locations rather than exact physical buildings, so the layer remains context evidence. It is a live-service retrieval; event-date status is not established.

### INGEMMET mining cadastre

- Service: `https://geocatmin.ingemmet.gob.pe/arcgis/rest/services/SERV_CATASTRO_MINERO_WGS84/MapServer`
- Products: layer 0 mining rights; layer 1 DGM mining-activity records
- Account: none
- Update semantics: service describes the rights cadastre as referential and updated daily
- Raw destination: `data/raw/ingemmet_catastro_minero_rights_secocha/`
- Quality/use: the ArcGIS envelope returned 176 layer-0 rights; exact 5 km distance filtering retains 173. Of these, 47 have reportable positive-area overlap of at least 1 m² with the active frame; seven additional machine-precision boundary slivers are not counted. Status counts are recorded in the machine-readable manifest. Two layer-1 records with administrative `ESTADO_MINEM=EXPLOTACIÓN` status remain within 5 km, but neither intersects the active frame.
- Limitation: legal rights and DGM administrative concession status are not verified active extraction footprints and cannot rule out informal activity.

## Reproduction and outputs

```text
.venv/bin/python bin/acquire/pull_secocha_official_proxy_replacements.py
```

- Processed GeoPackage: `outputs/secocha_official_proxy_replacements/secocha_official_exposure_mining.gpkg`
- Machine-readable manifest: `outputs/secocha_official_proxy_replacements/proxy_replacement_manifest.json`
- Short summary: `outputs/secocha_official_proxy_replacements/proxy_replacement_summary.md`
- QGIS delivery: `exports/qgis_packages/secocha/FullAudit/`

The acquisition compares ArcGIS count responses with returned GeoJSON feature counts and fails on service errors, count mismatches, or transfer-limit flags. The manifest records raw and processed SHA-256 hashes. The four new QGIS layers are kept outside the PIM score.
