# Goslar additional regulatory floodplain vectors

Status: downloaded 2026-09-14; used for the Goslar multi-river comparison.

- Dataset id: `goslar_multiriver_regulatory`
- Portal: https://www.goslar.de/wirtschafts-und-zukunftsort/klima-umwelt-gewaesserschutz/gewaesserschutz/ueberschwemmungsgebiete-innerhalb-der-stadt-goslar
- Service: https://www.umweltkarten-niedersachsen.de/arcgis/rest/services/HWSchutz_wms/MapServer
- Access date: 2026-09-14. Current regulatory snapshot, not observed flood events.
- Used by: `multiriver_comparison` and the full multi-river extent; supplements the Abzucht/Grane/Radau/Wedde snapshot with Ecker, Schamlahbach, Oker and Innerste for fixed-model spatial comparison.
- Scope: discovery envelope WGS84 10.2,51.7,10.8,52.1. Retrieve complete selected features without clipping: layer39 UESG691 Ecker, UESG632 Schamlahbach; layer40 UESG793 Oker-6 Stadt Goslar, UESG792 Innerste-5 Stadt Goslar. City-specific Oker/Innerste selected instead of adjoining municipal regulations. Coverage denominator is the complete selected official feature, not whole river basin.
- Public vector query, no account. Server copyright: © 2026, daten@nlwkn.niedersachsen.de. No explicit reuse licence found in layer metadata.
- Reproduce: `.venv/bin/python bin/acquire/pull_goslar_multiriver_regulatory.py`.
- The webpage's regulation dates for Oker/Innerste (2017-05-02) differ from server effective-date field von_datum (2017-05-24); retain both separately. Ecker webpage date 2015-05-13; Schamlah 2014-09-03. Dates are not event observations.

## Acquisition result

Acquired four complete features successfully (2026-09-14); SHA256 and complete original attributes in `data/validation/goslar_multiriver_regulatory/source_manifest.json`:

| River | UESG id / layer | Bytes | SHA256 |
|---|---|---:|---|
| Ecker | 691 / 39 | 94365 | f150136446bf34549a6403746bc56f5c83f42bedbb741eff1146338374c91021 |
| Schamlah | 632 / 39 | 11615 | ae83f7bc4e2be377a4fc4de0cb0d0a2bb7c5ea7ef7959fbf0de0678c9dd20c43 |
| Oker | 793 / 40 | 340149 | 0d0a22c841d98f1f9cd7def692f0e37c2a0a3fa8ab79058529f08c1f83f11db4 |
| Innerste | 792 / 40 | 20607 | 9d9afbbb957e671d003b9e75ff614538587994f332a143525f1bd75149e49d6b |

Merged file: `regulatory_features.geojson`, original properties plus source_layer, river and webpage_announcement_date. Individual responses retain original properties. All four geometries nonempty/valid after EPSG32632 transformation, source checksums verified.
