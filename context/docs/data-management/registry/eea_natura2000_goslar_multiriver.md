# EEA Natura 2000 2024 extended Goslar source

- LOCAL_DATA, reusable; access date 2026-09-14.
- Source: https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/Natura2000Sites/MapServer . Service explicitly describes dataset version 2024; EEA reuse policy applies; anonymous public query, no account/payment.
- Scope: full intersecting features of layers 0 (Habitats/FFH) and 1 (Birds/SPA), for model evaluation envelope plus 10 km; EPSG32632 envelope [545411,5727748,625576,5802557]. Includes original scoring source families only.
- Query object ids first, then batches of full geometries to avoid record limits. No clipping of retained features.
- Destination: `data/raw/eea_natura2000_goslar_multiriver_v1/`; `protected.gpkg`, raw GeoJSON responses, service metadata and `source_manifest.json` preserve version/query/hashes/file sizes.
- Reproduce: `.venv/bin/python bin/acquire/pull_goslar_multiriver_natura.py`.
- Intended use: expand environmental protected-site distance context without changing original source family or model formula. Old source files remain unchanged.
