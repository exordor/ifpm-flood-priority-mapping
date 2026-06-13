# Download Preflight: Copernicus DEM Zimbabwe Prototype

Status: planned; not ready to download.

## Scope

- [x] The dataset has a clear project purpose: DEM-based outlet snapping and independent
      catchment delineation if HydroBASINS candidates remain ambiguous.
- [ ] The required study area or bounding box is selected.
- [x] The temporal window is documented: static DEM.
- [ ] The expected disk footprint is known and acceptable.
- [x] The download will not be a broad global mirror.

## Access And Licence

- [x] Source URL or portal is recorded.
- [ ] Exact product, tile list, and access route are recorded.
- [x] Licence, terms, and citation requirement are checked at page level.
- [ ] Account, registration, or approval requirements are documented for the selected route.
- [x] Credentials, cookies, tokens, and private links will not be committed.

## Destination

- [x] Raw downloaded data will go under `data/raw/copernicus_dem_zimbabwe_prototype/`.
- [x] Temporary downloads will go under `data/tmp/copernicus_dem_zimbabwe_prototype/`.
- [x] Validation records are not part of this dataset.
- [x] Processed diagnostics will go under `outputs/`.
- [x] Release bundles will go under `exports/` only after approval.
- [x] No real downloaded data will be copied into `context/` or `ifpm-flood-pipeline/`.

## Registry

- [x] A dataset registry note exists.
- [x] The note states this is reusable if the DEM branch proceeds.
- [x] The registry note includes source, access date, destination, and use.
- [x] The registry note includes licence/access constraints.
- [ ] The registry note includes checksum or file-size evidence after download.
- [ ] The registry note identifies expected/actual files after tile selection.

## Safety Check

- [x] The target path is ignored by Git.
- [ ] The command has overwrite guards.
- [x] Partial or failed downloads can be identified and cleaned.
- [x] Partial path, attempt status, failure reason, and cleanup decision will be recorded.
- [x] The handoff will state whether Copernicus DEM was actually used.
