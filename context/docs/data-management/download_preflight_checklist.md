# Download Preflight Checklist

Complete this checklist before downloading real project data.

## Scope

- [ ] The dataset has a clear project purpose.
- [ ] The required study area is known.
- [ ] The required temporal window is known or the uncertainty is documented.
- [ ] The expected disk footprint is acceptable.
- [ ] The download is not a broad bulk mirror unless explicitly approved.

## Access And Licence

- [ ] Source URL or portal is recorded.
- [ ] Product/version is recorded.
- [ ] Licence, terms, or citation requirements are checked.
- [ ] Account, registration, approval, or payment requirements are documented.
- [ ] Credentials, cookies, tokens, and private links will not be committed.

## Destination

- [ ] Raw downloaded data will go under `data/raw/<dataset_id>/` or another approved
      `data/` subdirectory.
- [ ] Temporary downloads will go under `data/tmp/<dataset_id>/` or `tmp/`.
- [ ] Validation records will go under `data/validation/<dataset_id>/`.
- [ ] Processed maps, diagnostics, and model outputs will go under `outputs/`.
- [ ] Release bundles will go under `exports/`.
- [ ] No real downloaded data will be copied into `context/` or `ifpm-flood-pipeline/`.

## Registry

- [ ] A dataset registry note exists or will be created under
      `context/docs/data-management/`.
- [ ] The note states whether the download is reusable or exploratory.
- [ ] The registry note includes source, product/version, access date, destination, and use.
- [ ] The registry note includes licence/access constraints.
- [ ] The registry note will include checksum or file-size evidence after download.
- [ ] The registry note will identify the checksum scope and expected/actual files.

## Safety Check

- [ ] The target path is ignored by Git.
- [ ] The command will not overwrite unrelated local data.
- [ ] Partial or failed downloads can be identified and cleaned.
- [ ] Partial path, attempt status, failure reason, and cleanup decision will be recorded if the
      download does not complete cleanly.
- [ ] The handoff will state what was downloaded and what remains unverified.
