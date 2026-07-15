# SERNANP Peru national definitive protected areas (MapServer layer 0)

- Dataset id: `sernanp_peru_protected_areas`
- Owner: Servicio Nacional de Areas Naturales Protegidas por el Estado (SERNANP)
- Product: SERNANP national definitive protected areas,
  `ANPAdministracionNacionalDefinitivas` (MapServer layer 0)
- Source service: `https://geoservicios.sernanp.gob.pe/arcgis/rest/services/servicios_ogc/peru_sernanp_0102/MapServer/0`
- Access date: 2026-07-13
- Access method: public ArcGIS REST query, no account required
- Licence: not stated by the service metadata; retain source attribution and treat the local extract as internal research data
- Study area: Arequipa Region plus a 5 km proximity buffer
- Intended use: national definitive protected-area context inside the
  provisional Environmental criterion
- Destination: `data/raw/sernanp_peru_protected_areas/peru_hybas_l7_6070641200_sernanp_protected_areas.gpkg`
- Reusable: yes for the same source date and Arequipa Region boundary; refresh before a final claim
- Download command: `.venv/bin/python bin/acquire/query_peru_sernanp_protected_areas.py`
- Expected scope: a small vector extract; the 2026-07-13 count preflight returned two intersecting features for the buffered Arequipa Region envelope
- Integrity evidence: `query_manifest.json` records the request URL, feature count, file size, and SHA-256 after download
- Claim boundary: this download queried only MapServer layer 0. Regional,
  private, and transitional protected-area layers in the service were not
  queried, so zero Arequipa Region features in this layer is not evidence that Arequipa Region has no
  protected or ecologically sensitive areas. Protected-area geometry also does
  not by itself validate ecological sensitivity.
