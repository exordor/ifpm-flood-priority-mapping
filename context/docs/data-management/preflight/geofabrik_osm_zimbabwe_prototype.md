# Download Preflight: Geofabrik OSM Zimbabwe Prototype

Status: complete.

## Scope

- [x] The dataset has a clear project purpose: candidate outlet settlement, road, bridge,
      waterway, and possible mine/quarry screening.
- [x] The required study area is known at project level: Upper Mzingwane candidate outlet
      search envelope.
- [x] The required temporal window is documented: current OSM extract at download date.
- [x] The exact artifact and byte size are selected:
      `zimbabwe-latest-free.gpkg.zip` -> `zimbabwe-260610-free.gpkg.zip`,
      `528811477` bytes.
- [x] The download is not a broad global mirror; it is a Zimbabwe country extract only.

## Access And Licence

- [x] Source URL or portal is recorded.
- [x] Exact product artifact/version is recorded.
- [x] Licence, terms, or citation requirements are identified as ODbL/OpenStreetMap/Geofabrik.
- [x] Account, registration, approval, or payment requirements are documented.
- [x] Credentials, cookies, tokens, and private links will not be committed.

## Destination

- [x] Raw downloaded data will go under `data/raw/geofabrik_osm_zimbabwe_prototype/`.
- [x] Temporary downloads will go under `data/tmp/geofabrik_osm_zimbabwe_prototype/`.
- [x] Validation records are not part of this dataset.
- [x] Processed diagnostics and clipped layers will go under `outputs/`.
- [x] Release bundles will go under `exports/` only after approval.
- [x] No real downloaded data will be copied into `context/` or `ifpm-flood-pipeline/`.

## Registry

- [x] A dataset registry note exists.
- [x] The note states this is reusable if the prototype proceeds.
- [x] The registry note includes source, access date, destination, and use.
- [x] The registry note includes licence/access constraints.
- [x] The registry note includes checksum and file-size evidence after download.
- [x] The registry note identifies expected/actual files after artifact selection.

## Safety Check

- [x] The target path is ignored by Git.
- [x] The command has overwrite guards.
- [x] Partial or failed downloads can be identified and cleaned.
- [x] Partial path, attempt status, failure reason, and cleanup decision will be recorded.
- [x] The handoff will state whether OSM evidence was actually used.
