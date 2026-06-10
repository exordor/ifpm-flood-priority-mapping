# Boundary-Discovery Authorization: HydroSHEDS Zimbabwe Prototype

Status: executed for the single authorized artifact. No other data has been downloaded.

## Authorization Boundary

This authorization covered one narrow download for boundary discovery only. It did not authorize
SRTM, CHIRPS, HydroRIVERS, overlay, scoring, maps, validation, or public release.

Candidate HydroBASINS levels, HYBAS ids, and PFAF ids are the output of this discovery step, not
a prerequisite for starting it.

## Authorized Future Artifact

- Dataset id: `hydrosheds_zimbabwe_prototype`
- Purpose: identify candidate HydroBASINS units for the Upper Mzingwane prototype boundary.
- Product: HydroBASINS standard Africa, all levels 1-12, version 1c.
- Source page: `https://www.hydrosheds.org/products/hydrobasins`
- Source artifact:
  `https://data.hydrosheds.org/file/hydrobasins/standard/hybas_af_lev01-12_v1c.zip`
- Source filename: `hybas_af_lev01-12_v1c.zip`
- Content type from header check: `application/zip`
- Content length from header check: `549296874` bytes
- Header check date: 2026-06-10
- Intended raw destination: `data/raw/hydrosheds_zimbabwe_prototype/`
- Intended temporary destination: `data/tmp/hydrosheds_zimbabwe_prototype/`
- Intended derived destination: `outputs/hydrosheds_zimbabwe_prototype/`
- Disk-footprint judgement: acceptable for a single controlled boundary-discovery attempt,
  because source size is about 0.55 GB and local free space was checked before this note.

## Deferred Artifacts

These are not authorized by this note:

- HydroBASINS customized-with-lakes Africa:
  `hybas_lake_af_lev01-12_v1c.zip`
- HydroRIVERS Africa geodatabase:
  `HydroRIVERS_v10_af.gdb.zip`
- HydroRIVERS Africa shapefile:
  `HydroRIVERS_v10_af_shp.zip`
- HydroBASINS pour points
- legacy HydroSHEDS archive basins or rivers

HydroRIVERS can be reconsidered later only if river-network plausibility checking needs it.

## Licence And Citation State

HydroBASINS and HydroRIVERS product pages state that the databases are freely available for
scientific, educational, and commercial use, under the HydroSHEDS core product license in the
HydroSHEDS Technical Documentation. Downloading and using the data means accepting those terms.

Before any release or redistribution, re-check the exact license agreement text and
redistribution restrictions from the downloaded documentation and product page.

Citation target:

- Lehner, B., and Grill, G. (2013). Global river hydrography and network routing: baseline data
  and new approaches to study the world's large river systems. Hydrological Processes, 27(15),
  2171-2186. DOI: `10.1002/hyp.9740`.

## Non-Executed Download Plan

This was the executed command plan for the single authorized artifact.

```bash
set -euo pipefail

dataset_id="hydrosheds_zimbabwe_prototype"
filename="hybas_af_lev01-12_v1c.zip"
url="https://data.hydrosheds.org/file/hydrobasins/standard/${filename}"
tmp_dir="data/tmp/${dataset_id}"
raw_dir="data/raw/${dataset_id}"
tmp_file="${tmp_dir}/${filename}.part"
raw_file="${raw_dir}/${filename}"

mkdir -p "${tmp_dir}" "${raw_dir}"
test ! -e "${tmp_file}"
test ! -e "${raw_file}"

curl --fail --location --output "${tmp_file}" "${url}"
shasum -a 256 "${tmp_file}" > "${tmp_file}.sha256"
mv "${tmp_file}" "${raw_file}"
mv "${tmp_file}.sha256" "${raw_file}.sha256"
```

The `test ! -e` checks are part of the overwrite guard. If either check fails, stop and inspect
the existing file before doing anything else.

## Execution Evidence

- Execution date: 2026-06-10
- Download completed: yes
- Actual archive size: `549296874` bytes
- SHA-256:
  `6b331a6e89d56c3a542dcee39a7e6e8700d0cf7c94083c5946c7db0d262a48d6`
- Extraction completed: yes
- Extracted file count: 85
- Boundary result note:
  `context/docs/project-management/hydrosheds_boundary_discovery_result_2026-06-10.md`

## Discovery Outputs To Record After Download

HydroBASINS levels were inspected before accepting any boundary. The current discovery recorded:

- primary candidate level: 7;
- primary candidate: `HYBAS_ID=1071528840`, `PFAF_ID=1245086`;
- finer nested candidates under `PFAF_ID=1245086`;
- CRS: EPSG:4326;
- candidate geometries inspected were valid;
- accepted state: not accepted.

The boundary remains unaccepted until mentor or authoritative local-boundary comparison resolves
the area and unit mismatch.

## Current No-Go Boundaries

- Do not download additional data from this authorization.
- Do not use HydroBASINS output for flood-risk interpretation.
- Do not copy extracted vectors into `context/` or `ifpm-flood-pipeline/`.
- Do not run SRTM, CHIRPS, overlay, or map-generation steps from this authorization.
