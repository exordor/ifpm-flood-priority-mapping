# IFPM Data Management Notes

`registry/` holds one note per downloaded dataset: source, version, access date,
licence, download command and file size or checksum. Add one for every new download.

Data rule: raw and derived data stay out of Git; registry notes record where they came from.
Store downloaded data under ignored workspace paths such as `data/`, processed outputs under
`outputs/`, and packaged bundles under `exports/`.

## Registry note fields

New notes use these fields, in this order, leaving out any that do not apply:

- Dataset id
- Status (with date)
- Used by
- Source
- URL
- Product and version/DOI
- Access date
- Licence
- Spatial scope and CRS
- Temporal coverage
- Acquisition command
- Local path
- Files (name, bytes, SHA-256 or manifest)
- Native resolution
- Known limitations
