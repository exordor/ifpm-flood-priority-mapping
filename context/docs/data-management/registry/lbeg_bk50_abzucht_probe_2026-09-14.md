# LBEG BK50 Abzucht soil-type context

Date: 2026-09-14. Status: downloaded; soil-type context only (no numerical K).

Source: https://nibis.lbeg.de/cardomap3/ and https://nibis.lbeg.de/net3/public/ikxcms/?pgid=2603 . Product: BK50 1:50,000 soil map (theme 1616; BK50KFAKTOR also inspected). Licence: CC BY 4.0 (https://nibis.lbeg.de/net3/public/ikxcms/?pgid=987). No account.

- Local path: `data/raw/lbeg_bk50_abzucht/bk50_abzucht_display_context.gpkg`, 352,256 bytes; checksum in adjacent `source_manifest.json` (export packaging can change on rerun).
- Command: `.venv/bin/python bin/acquire/pull_abzucht_bk50_context.py`. Uses public NIBIS `AxExportData`, theme `1616`, GPKG, exact display rectangle (26.3 km²). The server returns whole intersecting polygons without clipping.
- Content: 164 features in EPSG:25832 (one invalid source polygon, kept as is). Typed soil polygons cover 561/561 HQ100 grid centres. Fields include `pronum`, `botyp`, `nutzung`; no texture, organic carbon or numeric K. BK50KFAKTOR/L2131 is a two-feature method-coverage layer; no downloadable numerical K or profile-horizon table was found.
- Known limitations: 1:50,000 scale; rasterizing onto 30 m does not make it 30 m evidence. Numerical K for Abzucht comes from `soilgrids2017_abzucht` instead.

BGR KA1000 (https://services.bgr.de/arcgis/rest/services/boden/bodengefaehrdungen/MapServer/1) was not used: it covers arable soils only (BÜK1000N and CORINE 2006).
