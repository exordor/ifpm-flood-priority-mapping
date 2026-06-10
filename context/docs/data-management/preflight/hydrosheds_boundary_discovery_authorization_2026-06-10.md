# Boundary-Discovery Authorization: HydroSHEDS Zimbabwe Prototype

Status: prepared, not executed. No data has been downloaded.

## Authorization Boundary

This authorization prepares one narrow future download for boundary discovery only. It does not
authorize SRTM, CHIRPS, HydroRIVERS, overlay, scoring, maps, validation, or public release.

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

Do not run this command in this goal. It is a future manual plan after explicit approval.

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

## Discovery Outputs To Record After Future Download

After a future approved download, inspect HydroBASINS levels before accepting any boundary.
Record:

- selected candidate level or levels;
- candidate HYBAS ids and PFAF ids;
- whether the candidate is a single basin or a union/dissolve of multiple units;
- geometry validity and CRS;
- approximate area and outlet/downstream plausibility for Upper Mzingwane;
- comparison against any mentor-supplied or authoritative local boundary;
- accepted, rejected, or accepted-with-waiver state;
- checksum, actual file size, extraction state, and cleanup disposition.

Until those outputs exist, the boundary remains unaccepted.

## Current No-Go Boundaries

- Do not download within this goal.
- Do not use HydroBASINS output for flood-risk interpretation.
- Do not copy extracted vectors into `context/` or `ifpm-flood-pipeline/`.
- Do not run SRTM, CHIRPS, overlay, or map-generation steps from this authorization.
