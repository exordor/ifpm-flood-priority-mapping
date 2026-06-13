# SRTM V1 Download And Inventory Note

Updated: 2026-06-12

Status: downloaded and inventoried for controlled V1 terrain diagnostics only.

## Scope

This note records the first SRTM terrain baseline download for the V1 working boundary. V1 remains
`accepted_with_waiver_for_controlled_prototype`; this download does not convert V1 into a final
thesis boundary.

## Download

- Dataset id: `srtm_1arcsec_zimbabwe_prototype`
- Working boundary: V1 / `HB_L8_1081528840_full_l7_chain`
- Tile source used: `https://step.esa.int/auxdata/dem/SRTMGL1/`
- Original product reference: SRTM 1 Arc-Second Global, DOI `10.5066/F7PR7TFT`
- Command: `.venv/bin/python bin/download_srtm_v1_tiles.py`
- Raw destination: `data/raw/srtm_1arcsec_zimbabwe_prototype/`
- Output destination: `outputs/srtm_1arcsec_zimbabwe_prototype/`
- Authentication: no login, cookie, token, or private link was used.

Downloaded files:

| Tile | Bytes | SHA-256 | Source file |
|---|---:|---|---|
| `S22E028` | 6,005,782 | `b456c297a3f9ff0c75a03cc616ab8fc3a1e52a8ce94cfc05483183ba58f8c738` | `S22E028.SRTMGL1.hgt.zip` |
| `S22E029` | 6,715,196 | `aa8ad5daf9c9c155df900d24077907249d83bfda74ab3dc10e161eef70537b68` | `S22E029.SRTMGL1.hgt.zip` |
| `S21E028` | 7,754,907 | `6d53552260081fa24308bbf2cbad369379462aabc08f59534396f48ea3161238` | `S21E028.SRTMGL1.hgt.zip` |
| `S21E029` | 7,653,703 | `be04b8316c3c217ce4dead923255abd0fce1c18abfd026bf6ef8fc391b6a4ba5` | `S21E029.SRTMGL1.hgt.zip` |
| `S20E028` | 6,346,821 | `e1f2cb4051e056fd32582da3b4d122f860082e5e53c509f79152fe0b8627ab2a` | `S20E028.SRTMGL1.hgt.zip` |
| `S20E029` | 6,686,332 | `de5a4b3cf2ab11b4264920539f5b86ea25f081861050dc1baca15dd2d2d2b71b` | `S20E029.SRTMGL1.hgt.zip` |

Total source archive size: `41,162,741` bytes.

## Inventory

Command: `.venv/bin/python bin/inventory_srtm_v1_tiles.py`

Inventory outputs:

- `outputs/srtm_1arcsec_zimbabwe_prototype/srtm_raw_file_manifest.csv`
- `outputs/srtm_1arcsec_zimbabwe_prototype/srtm_tile_inventory.csv`
- `outputs/srtm_1arcsec_zimbabwe_prototype/srtm_tile_coverage_check.png`
- `outputs/srtm_1arcsec_zimbabwe_prototype/srtm_download_handoff.md`

Local runtime dependency:

- `rasterio 1.5.0` was installed in the root `.venv` for raw HGT inventory.

Raster inventory summary:

- Driver: `SRTMHGT`
- CRS: `EPSG:4326`
- Shape: `3601 x 3601`
- Bands: `1`
- Data type: `int16`
- NoData: `-32768`
- Resolution: `0.0002777777777777778` degrees

## Limits

This step only closes SRTM download and raw-tile inventory for the controlled prototype. It does
not include CHIRPS, slope, flow accumulation, drainage-distance indicators, AHP-MCDA overlay,
flood-risk interpretation, or intervention-priority interpretation.

Before any terrain-derived indicator is used, create a separate preprocessing step that records
the metric CRS, mosaic/clip rule, void/NoData handling, and output diagnostics.
