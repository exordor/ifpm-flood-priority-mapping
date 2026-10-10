# Goslar expanded OSM input snapshot

Product: OpenStreetMap snapshot via Overpass, access 2026-09-14. Licence: ODbL, © OpenStreetMap contributors.

Study rectangle EPSG:32632: 555411, 5737748, 615576, 5792557; the source rectangle adds 3000 m on every side. Used by: road proximity and the seven-category facility proxy in the Goslar multi-river full-extent chain. Facilities keep the original class filter and tag precedence; roads keep all highway ways, including paths.

Acquisition command: `.venv/bin/python bin/acquire/pull_multiriver_osm.py`. Destination: `data/raw/goslar_multiriver_osm_v1/`; raw requests/responses kept.

Roads were fetched in 16 tiles from public Overpass instances (overpass-api.de, overpass.kumi.systems, overpass.private.coffee, VK Maps https://maps.mail.ru/osm/tools/overpass/api/interpreter) after full-window requests timed out. An ohsome API fallback returned HTTP 403 and contributes no data.

Files: roads 113,207 unique LineStrings (`roads.gpkg`); facilities 2,432 points (`facilities.gpkg`). All used responses are dated 2026-09-14 (UTC 14:19:31–15:00:19). `road_query_support.geojson` records the union of request windows; the evaluation boundary plus 3050 m has no uncovered area. Bytes and SHA-256 in `source_manifest.json`.

Known limitations: this snapshot is newer than the original Goslar OSM inputs, so overlap changes mix source vintage with boundary effects.
