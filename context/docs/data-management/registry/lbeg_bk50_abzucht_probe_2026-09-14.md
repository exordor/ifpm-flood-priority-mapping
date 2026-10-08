# LBEG BK50 Abzucht acquisition probe

Classification: INTERNAL_CONTEXT. Date: 2026-09-14. Status: diagnostic_only.

Purpose: seek numerical soil erodibility data for the existing Abzucht/Goslar display extent; do not treat rendered WMS colours as numerical K.
Source: https://nibis.lbeg.de/cardomap3/ and https://nibis.lbeg.de/net3/public/ikxcms/?pgid=2603 . Product: BK50KFAKTOR, BK50 1:50,000. Metadata dated 2026-06-17 states OpenData CC BY 4.0 and free download via NIBIS. No account used.
Scope: service metadata and, if available, a small local clipped vector export (under 100 square kilometres; anticipated under 20 MB). No state-wide download. Reusable only after numeric schema, licence, and local coverage are checked.
Destination: probe responses under ignored `data/tmp/lbeg_bk50_abzucht_probe/`; accepted data would go to `data/raw/lbeg_bk50_abzucht/`. Curl requests to public capabilities, map configuration and export API reproduce exploration. File-size and checksum evidence will be recorded for retained responses/data. Do not persist session tokens from service responses in committed files.

BGR KA1000 was screened out: its official description restricts coverage to arable soils from BÜK1000N and CORINE 2006; it cannot plausibly solve urban/alluvial missing coverage by itself. Source: https://services.bgr.de/arcgis/rest/services/boden/bodengefaehrdungen/MapServer/1 .

## Result

- Acquired reusable **soil-type context**, not numerical K: `data/raw/lbeg_bk50_abzucht/bk50_abzucht_display_context.gpkg`, 352,256 bytes; final checksum is pinned in adjacent `source_manifest.json` (export packaging can change on rerun).
- Command: `.venv/bin/python bin/acquire/pull_abzucht_bk50_context.py`. Uses public NIBIS `AxExportData`, theme `1616`, GPKG, exact existing display rectangle (26.3 square kilometres). No credentials or export URLs are persisted. The server returns whole intersecting polygons, rather than clipping polygon edges.
- Reopened 164 features in EPSG:25832. One source polygon is invalid; source is preserved and an in-memory `make_valid` was used only for the coverage check. Typed soil polygons cover 561/561 HQ100 grid centres. This disproves treating absent SoilGrids values as evidence that no soil is present.
- BK50 licence confirmed at https://nibis.lbeg.de/net3/public/ikxcms/?pgid=987 : CC BY 4.0. Scale remains 1:50,000; rasterizing onto 30 m would not make it native 30 m evidence.
- Public `GetFeatureInfo` for PkgId=24/L816 at UTM32N 600000,5751000 returns profile number 256937, soil type B4 (Tiefe Braunerde), land use G, geological type, and groundwater fields. Export contains the same fields (`pronum`, `botyp`, `nutzung` etc.), no texture, organic carbon or numeric K. Auxiliary L848/L29/L58 return regional soil classifications only. BK50KFAKTOR/L2131 is a two-feature method-coverage layer. No verified downloadable numerical K/profile-horizon table was located through these public paths.
- Numerical gap remains a separate input task. Keep the official profile numbers as identifiers for a potential targeted data request; do not invent numerical K from soil-type names. Parent experiment investigates a full archived SoilGrids numerical alternative separately.
