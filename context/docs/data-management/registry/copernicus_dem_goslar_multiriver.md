# Copernicus DEM Goslar multiriver extension

- Dataset: Copernicus DEM GLO-30 public AWS COG tiles; 2026-09-14 access.
- Source: https://copernicus-dem-30m.s3.amazonaws.com/ ; public anonymous access, Copernicus DEM licence https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model .
- Scope: N51E009, N52E009, N52E010; reuses the original N51E010 tile. About 90 MB in total.
- Intended use: complete terrain source coverage for all retained Goslar multiriver flood extent products and buffered calculations; same source as the original Goslar chain.
- Destination: `data/raw/copernicus_dem_30m_goslar_multiriver_v1/`.
- Reproduce: `.venv/bin/python bin/acquire/pull_goslar_multiriver_dem.py`.
- Files: three GeoTIFF tiles; per-file bytes, SHA-256, source URL, CRS (EPSG:4326) and bounds in `source_manifest.json`.
