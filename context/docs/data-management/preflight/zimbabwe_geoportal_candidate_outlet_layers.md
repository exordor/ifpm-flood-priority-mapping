# Download Preflight: Zimbabwe Geoportal Candidate Outlet Layers

Status: complete.

## Scope

- [x] The dataset group has a clear project purpose: river-exit and flood-impact support for
      candidate outlet review.
- [x] The required study area is known at project level: candidate outlet search envelope.
- [x] The required temporal window is documented as portal update date per layer.
- [x] Initial expected disk footprint is acceptable for Rivers and Flood Prone Zones.
- [x] The download is not a broad portal mirror; only selected outlet-evidence layers may be
      downloaded.

## Access And Licence

- [x] Source URLs or portal pages are recorded.
- [x] Product/version metadata is recorded where visible.
- [x] Licence notes are recorded where visible.
- [x] Account/login requirement is documented.
- [x] Credentials, cookies, tokens, and private links will not be committed.

## Destination

- [x] Raw downloaded data will go under `data/raw/zimbabwe_geoportal_candidate_outlet_layers/`.
- [x] Temporary downloads will go under `data/tmp/zimbabwe_geoportal_candidate_outlet_layers/`.
- [x] Validation records are not part of this dataset group.
- [x] Processed diagnostics will go under `outputs/`.
- [x] Release bundles will go under `exports/` only after approval.
- [x] No real downloaded data will be copied into `context/` or `ifpm-flood-pipeline/`.

## Registry

- [x] A dataset registry note exists.
- [x] The note states whether the downloads are reusable.
- [x] The registry note includes source, product/version, access date, destination, and use.
- [x] The registry note includes licence/access constraints.
- [x] The registry note includes checksum and file-size evidence after download.
- [x] The registry note identifies actual files after authenticated download.

## Safety Check

- [x] The target path is ignored by Git.
- [x] The manual download/extraction workflow has overwrite guards.
- [x] Partial or failed downloads can be identified and cleaned.
- [x] Partial path, attempt status, failure reason, and cleanup decision will be recorded.
- [x] The handoff will state which layers were actually downloaded and used.
