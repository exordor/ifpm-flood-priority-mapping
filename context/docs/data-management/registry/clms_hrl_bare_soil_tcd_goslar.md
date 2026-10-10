# Dataset Registry: CLMS HRL bare-soil and tree-cover windows for Goslar

- Dataset id: `clms_hrl_bare_soil_tcd_goslar`
- Status: downloaded 2026-08-17/18. TCD decline 2018-2024 is the land-change (vegetation-loss)
  component of the LU criterion in the Goslar chain; Bare Soil After 2017-2024 is kept as a
  diagnostic series. Replaced the rejected Sentinel-2 MBI candidate
  (`sentinel2_l2a_goslar_bare_soil_candidate`).
- Access date: 2026-08-17 (2024 Bare Soil After), 2026-08-18 (2017-2023 Bare Soil After, TCD 2018 and 2024)
- Licence: Copernicus Programme data terms; attribution `Contains modified Copernicus Sentinel/CLMS data`.

## Products

1. HRL VLCC Bare Soil After 2017-present (`CLMS_HRLVLCC_CPBSA`, 10 m, Europe, yearly), dataset UID
   `bb6a2f6a0eca45b1b46ce83364fd6b6b`; years 2017-2024. Value: bare-soil period after the main crop
   season (percent of a year), not a binary bare-ground mask.
2. HRL VLCC Tree Cover Density 2018-present (`CLMS_HRLVLCC_TCD`, 10 m, Europe, yearly), dataset UID
   `f954d06dfb5442b4910f0ccea9070917`; years 2018 and 2024. Value: percent tree cover.

- Tiles: `E43N31` and `E43N32`, EPSG:3035, version V01_R00.
- Source file inventory (public COG manifest):
  `https://csv.dataspace.copernicus.eu/CLMS/landcover_landuse/cropping_patterns/clms_vlcc_bare-soil-after_europe_10m_yearly_v1/clms_vlcc_bare-soil-after_europe_10m_yearly_v1_cog.csv`
  and the equivalent `tree_cover_density/..._cog.csv`.

## Acquisition

- Access: CDSE S3 (endpoint `https://eodata.dataspace.copernicus.eu`, bucket `eodata`); needs a CDSE
  account and S3 credential (anonymous access returns 401/403).
- Commands: `.venv/bin/python bin/acquire/pull_goslar_clms_bare_soil_direct.py` and
  `.venv/bin/python bin/acquire/pull_goslar_clms_tcd_direct.py`.
- Local paths: `data/raw/clms_hrl_bare_soil_goslar_official_basin/<year>/` (218,041,199 bytes, 16 source
  tiles plus 8 annual mosaics) and `data/raw/clms_hrl_tcd_goslar_official_basin/<year>/`
  (194,791,672 bytes, 4 source tiles plus 2 mosaics).

## Files

Source tiles (SHA-256 computed 2026-10-10 from the local files):

| File | Bytes | SHA-256 |
|---|---:|---|
| `2017/CLMS_HRLVLCC_CPBSA_S2017_R10m_E43N31_03035_V01_R00.tif` | 7,334,596 | `8002ea22609eb8c4b0a6954417420960ea539f255e05b1e7e9ec8d0ddb4ab384` |
| `2017/CLMS_HRLVLCC_CPBSA_S2017_R10m_E43N32_03035_V01_R00.tif` | 9,166,210 | `b3030d79b3e7be38753b2ece2fc35f95a8e1f8f58e481dcc8bfdd7a678b4f321` |
| `2018/CLMS_HRLVLCC_CPBSA_S2018_R10m_E43N31_03035_V01_R00.tif` | 7,135,503 | `36244f4430ce3ee5f1b20b8087becb240a17b81ab9a20450978a86a8b6be0fff` |
| `2018/CLMS_HRLVLCC_CPBSA_S2018_R10m_E43N32_03035_V01_R00.tif` | 9,012,199 | `dde0c6cff4b898800e662aabc7282f74547d0117a9f5435feca4751cd2cf719f` |
| `2019/CLMS_HRLVLCC_CPBSA_S2019_R10m_E43N31_03035_V01_R00.tif` | 7,831,880 | `722ef6576ace1387e3638f90d4eabf2f8f2523a16d95bbcf6aaa724d07393ca1` |
| `2019/CLMS_HRLVLCC_CPBSA_S2019_R10m_E43N32_03035_V01_R00.tif` | 9,220,414 | `2c13f42dde0e9270df837a416257c54c3779e4cfad1830c296fb737d7d43418f` |
| `2020/CLMS_HRLVLCC_CPBSA_S2020_R10m_E43N31_03035_V01_R00.tif` | 7,059,530 | `a9b1c370a3aa22d22e3ac31fcb17752f1e1dc73156f79953ca4c31424476a44b` |
| `2020/CLMS_HRLVLCC_CPBSA_S2020_R10m_E43N32_03035_V01_R00.tif` | 8,741,448 | `77b5fc9a951a0ad1bf32961f2f2af43775d88de5915d91a217fece65b229ace7` |
| `2021/CLMS_HRLVLCC_CPBSA_S2021_R10m_E43N31_03035_V01_R00.tif` | 7,120,605 | `a4af6843d5b30744fd74f0127a6ed038cccc6ce2a8bd12e5d8de343c4bfbe07d` |
| `2021/CLMS_HRLVLCC_CPBSA_S2021_R10m_E43N32_03035_V01_R00.tif` | 8,766,646 | `c29ac79a1b1a9f3591e9cbe68c1aeb621b60eab2c75d1a7dd577b41f2e831632` |
| `2022/CLMS_HRLVLCC_CPBSA_S2022_R10m_E43N31_03035_V01_R00.tif` | 7,023,665 | `1348c0d4ad8d230aa2485428ebee56b312930507afcfc611d57f49329952a7e1` |
| `2022/CLMS_HRLVLCC_CPBSA_S2022_R10m_E43N32_03035_V01_R00.tif` | 8,654,902 | `2244e321bc327332d3a1207769ccb1a11bae39a5b3ed7ea9b3537c2d776a2a90` |
| `2023/CLMS_HRLVLCC_CPBSA_S2023_R10m_E43N31_03035_V01_R00.tif` | 7,330,355 | `ec1411d0ed90eea11b8dd56e4604dbff0eb3ffedce28d5c1fbada11c64f8034f` |
| `2023/CLMS_HRLVLCC_CPBSA_S2023_R10m_E43N32_03035_V01_R00.tif` | 8,983,611 | `2be26bfe0817823b74308480ecc597c57c788f742cdb684957b628eba66afa71` |
| `2024/CLMS_HRLVLCC_CPBSA_S2024_R10m_E43N31_03035_V01_R00.tif` | 12,592,164 | `64b49d17d5a2919016e6e73000e23713c7f53a1f4bf8c19a7aad165e16cc25cd` |
| `2024/CLMS_HRLVLCC_CPBSA_S2024_R10m_E43N32_03035_V01_R00.tif` | 16,017,757 | `28b04179810114e27a61aa298b2568a8ba15341ca6d09b732d63d08312722bed` |
| `2018/CLMS_HRLVLCC_TCD_S2018_R10m_E43N31_03035_V01_R00.tif` | 31,193,162 | `7022354f6acaacd2d4380b6974c183596218a143ae3eb62f85ac25bb6c2a851b` |
| `2018/CLMS_HRLVLCC_TCD_S2018_R10m_E43N32_03035_V01_R00.tif` | 24,957,554 | `6a3c81506d5344d4fc1072f729b0f3c50c3db7e5ff47f73ef006d4eacbec1a26` |
| `2024/CLMS_HRLVLCC_TCD_S2024_R10m_E43N31_03035_V01_R00.tif` | 32,345,188 | `53b7f5e34b0cbf5008b9ee5b5e020bffeefb0a28ae8c47ba5a84967382c43e48` |
| `2024/CLMS_HRLVLCC_TCD_S2024_R10m_E43N32_03035_V01_R00.tif` | 27,996,387 | `a41c0d55112530db16a50f5aa50c98bc78d2809d5fdbf1c080abc8cb2c93c53e` |

Derived 30 m layers (official-basin grid) and their hashes and diagnostics are in
`outputs/esa_worldcover_2021_goslar/c_factor/`:

- `clms_tcd_vegetation_loss_2018_2024_goslar_official_basin_30m.tif`: positive percent-point TCD
  decline 2018-2024; 170,882 valid cells, 94,552 non-zero (`clms_tcd_vegetation_loss_diagnostics.json`).
- `clms_bare_soil_after_<year>_goslar_official_basin_30m.tif`, 2017-2024: valid coverage
  96.2-98.0% (`clms_bare_soil_after_series_diagnostics.json`).

## Known limitations

- Bare Soil After is an agricultural bare-soil indicator; it does not separate built-up or water
  false positives.
- The criterion field is still named `bare_soil_vegetation_loss`, but the active input is
  tree-cover loss.
