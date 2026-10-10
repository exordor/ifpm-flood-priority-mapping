# IFPM Data Management Notes

`registry/` holds one note per downloaded dataset: source, version, access date,
licence, download command and file size or checksum. Add one for every new download.

Real downloaded data must stay outside this folder. Store it under ignored workspace paths such
as `data/`, keep processed outputs under `outputs/`, and keep packaged bundles under `exports/`.
