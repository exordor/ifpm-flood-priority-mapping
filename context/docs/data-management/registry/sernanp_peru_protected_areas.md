# SERNANP Peru national definitive protected areas (MapServer layer 0)

- Dataset id: `sernanp_peru_protected_areas`
- Owner: Servicio Nacional de Areas Naturales Protegidas por el Estado (SERNANP)
- Product: SERNANP national definitive protected areas,
  `ANPAdministracionNacionalDefinitivas` (MapServer layer 0)
- Source service: `https://geoservicios.sernanp.gob.pe/arcgis/rest/services/servicios_ogc/peru_sernanp_0102/MapServer/0`
- Access date: 2026-07-13
- Access method: public ArcGIS REST query, no account required
- Licence: not stated by the service metadata; attribute SERNANP
- Study area: former Peru study area (frozen, `peru_hybas_l7_6070641200`) plus a 5 km proximity buffer
- Used by: protected-area context in the Environmental criterion of the former Peru study area
- Destination: `data/raw/sernanp_peru_protected_areas/peru_hybas_l7_6070641200_sernanp_protected_areas.gpkg`
- Download command: `.venv/bin/python bin/acquire/query_peru_sernanp_protected_areas.py`
- Files: 2 features (Punta Hornillos guano islands; Salinas y Aguada Blanca), 212,992 bytes, SHA-256
  `68d87e1763a3e90424ffcc0449602a6299c3e0b58c30b7f7341d4f1130b663c7`; request details in `query_manifest.json`
- Known limitations: only MapServer layer 0 was queried; regional, private and transitional
  protected-area layers were not.
