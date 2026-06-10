# Download Preflight: HydroBASINS And HydroRIVERS Zimbabwe Prototype

Status: boundary-discovery preflight prepared; no data downloaded. Future execution still needs
explicit approval.

## Scope

- [x] The dataset has a clear project purpose: hydrological framework and aggregation units.
- [x] The required study area is known at project level: Upper Mzingwane prototype slice.
- [x] Candidate HydroBASINS ids are defined as the boundary-discovery output, not as a
      pre-download prerequisite.
- [x] The first discovery artifact is selected: HydroBASINS standard Africa all levels 1-12.
- [x] The temporal window is documented: static hydrographic baseline.
- [x] The expected source size is recorded: `549296874` bytes for
      `hybas_af_lev01-12_v1c.zip`.
- [x] The download is not a global mirror; intended scope is Africa archives only.

## Access And Licence

- [x] Source URL or portal is recorded in the registry note.
- [x] Product/version is recorded for the first discovery artifact: HydroBASINS standard Africa
      version 1c.
- [x] Product-page licence and citation pointers have been reviewed.
- [x] Licence source is recorded for preflight: HydroSHEDS core product license in the
      HydroSHEDS Technical Documentation.
- [ ] Exact downloaded licence text/version and redistribution restrictions will be verified
      after a future approved download.
- [x] Account, registration, approval, or payment requirements are documented.
- [x] Credentials, cookies, tokens, and private links will not be committed.

## Destination

- [x] Raw downloaded data will go under `data/raw/hydrosheds_zimbabwe_prototype/`.
- [x] Temporary downloads will go under `data/tmp/hydrosheds_zimbabwe_prototype/`.
- [x] Validation records are not part of this dataset.
- [x] Processed maps, diagnostics, and model outputs will go under `outputs/`.
- [x] Release bundles will go under `exports/` only as private/local bundles.
- [x] No real downloaded data will be copied into `context/` or `ifpm-flood-pipeline/`.

## Registry

- [x] A dataset registry note exists.
- [x] The note states this is reusable if the prototype proceeds.
- [x] The note includes source, product/version, access date, destination, and use.
- [x] The note includes licence/access constraints.
- [x] The note will include checksum or file-size evidence after download.
- [x] The note identifies checksum scope and expected/actual files.

## Safety Check

- [x] The target path is ignored by Git.
- [x] A non-executed future command plan includes `test ! -e` overwrite guards.
- [x] Partial or failed downloads can be identified and cleaned.
- [x] Partial path, attempt status, failure reason, and cleanup decision will be recorded.
- [x] The handoff will state that no data was downloaded yet.

## Boundary-Discovery Authorization

- Authorization note:
  `context/docs/data-management/preflight/hydrosheds_boundary_discovery_authorization_2026-06-10.md`
- Authorization state: prepared, not executed.
- Authorized future artifact:
  `https://data.hydrosheds.org/file/hydrobasins/standard/hybas_af_lev01-12_v1c.zip`
- Deferred artifacts: HydroBASINS customized-with-lakes, HydroRIVERS, pour points, and legacy
  HydroSHEDS archive layers.
- Discovery output: candidate levels, HYBAS ids, PFAF ids, dissolve/union rule, geometry/CRS,
  outlet plausibility, area comparison, and accepted/rejected/waived boundary state.
