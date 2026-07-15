# Dataset Registry: ESA WorldCover 2021 Southern Peru Arequipa Region

Status: active for Arequipa Region land-cover and C-factor repair in the southern Peru
comparison catchment.

## Dataset Identity

- Dataset id: `esa_worldcover_2021_peru_pilot`
- Short name: ESA WorldCover 2021 v200
- Data class: `LOCAL_DATA`
- Reusable download: yes, for Arequipa Region prototype evidence and C-factor repair
- Project role: land-cover class and RUSLE C-factor proxy for Arequipa Region criteria stack
- Study area: Arequipa Region southern Peru comparison catchment in Arequipa Region, mainly
  the Vitor-La Joya-Santa Rita de Siguas area west of Arequipa city
- Temporal coverage: 2021 land-cover map

## Source And Access

- Source organization: ESA WorldCover consortium
- Source URL or portal: `https://esa-worldcover.org/en/data-access`
- Direct source artifacts:
  - `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_S18W072_Map.tif`
  - `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_S18W075_Map.tif`
- Product/version: ESA WorldCover 10 m 2021 v200
- Access date: 2026-06-30
- Access method: direct public S3 GeoTIFF URL
- Licence or terms: ESA WorldCover terms must be cited before public release
- Account, registration, or approval needed: none identified for direct tile URLs

## Download Plan

- Intended destination: `data/raw/esa_worldcover_2021_peru_pilot/`
- Expected file types: GeoTIFF plus local `.sha256` sidecar
- Expected file count: 2 tiles
- Reason for two tiles: Arequipa Region spans approximately `-72.315` to `-71.582` longitude, crossing the
  `-72` tile boundary. `S18W072` alone leaves the western part uncovered; `S18W075` is required.
- Temporary path, if any: `data/tmp/esa_worldcover_2021_peru_pilot/`

## Verification

- Download completed: yes
- Verification date: 2026-06-30
- Checksum scope: each downloaded GeoTIFF
- Checksum algorithm: SHA-256
- Files:
  - `ESA_WorldCover_10m_2021_v200_S18W072_Map.tif`
    - Size: 70,649,046 bytes
    - SHA-256: `4b4d2d8ca936965393ad5ae5b694b09a707005c64eb403823822e8c2343ba197`
  - `ESA_WorldCover_10m_2021_v200_S18W075_Map.tif`
    - Size: 33,292,084 bytes
    - SHA-256: `22e40c1b313a518e56ce477f9399d6016a6bb375d1816b7a112f9f4a456e8aca`
- Raw checksum manifest:
  `data/raw/esa_worldcover_2021_peru_pilot/worldcover_tiles.sha256`
- CRS or georeferencing checked: yes; both source tiles are `EPSG:4326`.

## Processing And Use

- Raw data path: `data/raw/esa_worldcover_2021_peru_pilot/`
- Derived output path: `outputs/esa_worldcover_2021_peru_pilot/c_factor/`
- Actual use: mosaic needed WorldCover tiles, clip/reproject to Arequipa Region reference grid, and derive
  land-cover pressure / C-factor proxy.
- Processed C-factor output:
  `outputs/esa_worldcover_2021_peru_pilot/c_factor/c_factor_peru_hybas_l7_6070641200_30m.tif`
- Arequipa Region C-factor grid check: passed, valid fraction inside Arequipa Region = `1.0`.
- Known limitations: static 2021 land cover is not active mining truth and does not capture
  seasonal cover-management variation.

## Release Boundary

- May be committed: no
- May be used in public examples: no unless replaced by synthetic or explicitly approved sample
- Public-safe summary available: this registry note only
