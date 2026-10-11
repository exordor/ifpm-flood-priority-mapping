# Zensus 2022 population, Goslar multi-river full extent (100 m clip)

- Dataset id: `zensus2022_goslar_multiriver`
- Status (with date): active since 2026-10-11; replaces the read of the staged national archive
  `data/tmp/zensus2022_goslar/Zensus2022_Bevoelkerungszahl.zip`, which is no longer present.
- Used by: `bin/analysis/run_goslar_multiriver_full.py` (population exposure of the
  `goslar_multiriver_full_extent` / `fixed_scale` run). The script still rebuilds the clip from
  the national archive if that archive is restored at the path above.
- Source: Statistisches Bundesamt (Destatis), Zensus 2022, population per 100 m grid cell.
- URL: Zensus 2022 grid data download page, https://www.zensus2022.de (national file
  `Zensus2022_Bevoelkerungszahl.zip` containing `Zensus2022_Bevoelkerungszahl_100m-Gitter.csv`).
- Product and version/DOI: Zensus 2022 Bevölkerungszahl, 100 m Gitter (national archive
  SHA-256 `1a8428d31eab264c8717bfdcbf40fbd66c217edb2e2a98d0e67741bd8a1a941a`, as recorded in
  `outputs/goslar_multiriver_full_extent/fixed_scale/expansion_manifest.json`).
- Access date: national archive as used by the 2026-09-14 full-extent run; clip promoted to
  `data/raw/` on 2026-10-11.
- Licence: Datenlizenz Deutschland – Namensnennung – Version 2.0 (DL-DE-BY-2.0).
- Spatial scope and CRS: cells whose centres fall in the EPSG:3035 bounds of the
  `goslar_multiriver_full_extent` 30 m grid (739 km² target area), EPSG:3035, 100 m.
- Temporal coverage: census reference date 2022-05-15.
- Acquisition command: derived by `census_grid()` (now `bin/_lib/goslar_comparison.py`) inside
  `.venv/bin/python bin/analysis/run_goslar_multiriver_full.py`, which wrote
  `outputs/goslar_multiriver_full_extent/fixed_scale/sources/population_native_100m.tif`;
  that file was copied unchanged to the local path below.
- Local path: `data/raw/zensus2022_goslar_multiriver/`
- Files: `population_native_100m.tif` (72,839 bytes, SHA-256
  `3a0ace691c7f7b09500acf23c7292634c5cd22ecb81d02c3867dd946f246bcb0`, identical to the hash
  recorded for the derived clip in `expansion_manifest.json`); `source_manifest.json`.
- Native resolution: 100 m.
- Known limitations: resident population only; cells missing from the published table
  (no residents or suppressed for confidentiality) are NoData, not zero. Covers only the
  full-extent bounds; a larger extent needs the national archive again.
