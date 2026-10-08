# Copernicus DEM Goslar multiriver extension

- Classification: LOCAL_DATA, reusable local source snapshot.
- Dataset: Copernicus DEM GLO-30 public AWS COG tiles; 2026-09-14 access.
- Source: https://copernicus-dem-30m.s3.amazonaws.com/ ; public anonymous access, Copernicus DEM licence https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model .
- Scope: N51E009, N52E009, N52E010; reuse original N51E010. About 90 MB additional source data expected, no credentials/payment.
- Intended use: complete terrain source coverage for all retained Goslar multiriver flood extent products and buffered calculations; diagnostic/provisional expansion, same model inputs family.
- Destination: `data/raw/copernicus_dem_30m_goslar_multiriver_v1/`; partial downloads under matching `data/tmp/`.
- Reproduce: `.venv/bin/python bin/acquire/pull_goslar_multiriver_dem.py`.
- File sizes, checksums, exact source URLs and source raster metadata: destination `source_manifest.json` after successful validation.
