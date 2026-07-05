# Download Preflight: ESA WorldCover 2021 Peru Pilot

Status: closed for PE1 repair download and processing.

## Scope

- [x] The dataset has a clear project purpose: repair PE1 land-cover / C-factor coverage.
- [x] The required study area is known: PE1 engineering pilot boundary.
- [x] The expected disk footprint is acceptable: one existing tile plus one missing tile, each
  about tens of MB compressed.
- [x] The download is not a broad mirror.

## Access And Licence

- [x] Source URLs are recorded in the registry note.
- [x] Product/version is recorded.
- [x] Licence or citation requirement must be cited before public release.
- [x] Account, registration, approval, or payment requirements are not expected.
- [x] Credentials, cookies, tokens, and private links will not be committed.

## Destination

- [x] Raw data will go under `data/raw/esa_worldcover_2021_peru_pilot/`.
- [x] Temporary downloads will go under `data/tmp/esa_worldcover_2021_peru_pilot/`.
- [x] Processed maps and summaries will go under `outputs/`.
- [x] No real downloaded data will be copied into `context/` or `ifpm-flood-pipeline/`.

## Safety Check

- [x] The target path is ignored by Git.
- [x] The command will not overwrite unrelated local data.
- [x] Partial downloads can be identified by `.part` suffix and retried.
- [x] The output will be labelled as PE1 engineering-pilot evidence, not final flood-risk evidence.

## Completion Evidence

- Raw files:
  - `data/raw/esa_worldcover_2021_peru_pilot/ESA_WorldCover_10m_2021_v200_S18W072_Map.tif`
  - `data/raw/esa_worldcover_2021_peru_pilot/ESA_WorldCover_10m_2021_v200_S18W075_Map.tif`
- File sizes:
  - `S18W072`: 70,649,046 bytes
  - `S18W075`: 33,292,084 bytes
- SHA-256 values:
  - `S18W072`: `4b4d2d8ca936965393ad5ae5b694b09a707005c64eb403823822e8c2343ba197`
  - `S18W075`: `22e40c1b313a518e56ce477f9399d6016a6bb375d1816b7a112f9f4a456e8aca`
- Processed outputs:
  - `outputs/esa_worldcover_2021_peru_pilot/c_factor/c_factor_pe1_30m.tif`
  - `outputs/srtm_1arcsec_peru_pilot/criteria_stack/criteria/land_cover_pressure_0_1.tif`
- Repair result:
  - PE1 C-factor valid fraction inside PE1: `1.0`
  - PE1 land-cover criterion valid fraction inside PE1: `1.0`
