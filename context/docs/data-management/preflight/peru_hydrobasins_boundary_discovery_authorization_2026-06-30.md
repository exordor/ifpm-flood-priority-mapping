# Boundary-Discovery Authorization: HydroSHEDS Peru Prototype

Status: authorization written 2026-06-30. Pending execution. No Peru data has been downloaded yet.

## Authorization Boundary

This authorization covers one narrow download for Peru boundary discovery only. It does not
authorize SRTM, CHIRPS, HydroRIVERS, overlay, scoring, maps, validation, public release, or any
final Zimbabwe-Peru comparison.

Candidate HydroBASINS levels, HYBAS ids, and PFAF ids are the output of this discovery step, not
a prerequisite for starting it.

This is a boundary-only exception, the exact analogue of the already-executed Zimbabwe
HydroBASINS authorization (`hydrosheds_boundary_discovery_authorization_2026-06-10.md`). It does
not accept any Peru boundary (IFPM-D02 remains open) and does not promote Peru to an
interpretable-claim state. Outputs are `diagnostic_only`.

## Authorized Future Artifact

- Dataset id: `hydrosheds_peru_prototype`
- Purpose: identify candidate HydroBASINS units intersecting the Arequipa-Moquegua-Tacna
  administrative region, to turn the open Peru boundary question (IFPM-D02) into a concrete,
  evidence-backed decision rather than an abstract choice.
- Product: HydroBASINS standard South America, all levels 1-12, version 1c.
- Source page: `https://www.hydrosheds.org/products/hydrobasins`
- Source artifact:
  `https://data.hydrosheds.org/file/hydrobasins/standard/hybas_sa_lev01-12_v1c.zip`
- Source filename: `hybas_sa_lev01-12_v1c.zip`
- Content type from header check: `application/zip`
- Content length from header check: `334160720` bytes (~334 MB; smaller than the Africa analogue)
- Header check date: 2026-06-30
- Intended raw destination: `data/raw/hydrosheds_peru_prototype/`
- Intended temporary destination: `data/tmp/hydrosheds_peru_prototype/`
- Intended derived destination: `outputs/peru_boundary_discovery/`
- Disk-footprint judgement: to be confirmed at execution. The Africa analogue was about 0.55 GB;
  South America may be larger. Free space must be checked before download, as the Zimbabwe note
  required.

The `hybas_sa` naming and v1c versioning were confirmed against the HydroSHEDS product page
(search 2026-06-30); the Africa product used the identical `hybas_af_..._v1c` convention.

## Deferred Artifacts

These are not authorized by this note:

- HydroBASINS customized-with-lakes South America: `hybas_lake_sa_lev01-12_v1c.zip`
- HydroRIVERS South America geodatabase / shapefile
- HydroBASINS pour points (South America)
- legacy HydroSHEDS archive basins or rivers
- SRTM, CHIRPS, or any raster data for Peru (no boundary accepted yet)

HydroRIVERS can be reconsidered later only if river-network plausibility checking needs it.

## Licence And Citation State

HydroBASINS and HydroRIVERS product pages state that the databases are freely available for
scientific, educational, and commercial use, under the HydroSHEDS core product license in the
HydroSHEDS Technical Documentation. Downloading and using the data means accepting those terms.
This is the same license under which the Africa artifact was already downloaded.

Before any release or redistribution, re-check the exact license agreement text and
redistribution restrictions from the downloaded documentation and product page.

Citation target:

- Lehner, B., and Grill, G. (2013). Global river hydrography and network routing: baseline data
  and new approaches to study the world's large river systems. Hydrological Processes, 27(15),
  2171-2186. DOI: `10.1002/hyp.9740`.

## Non-Executed Download Plan

This is the command plan for the single authorized artifact, mirroring the Zimbabwe plan with
the South America artifact.

```bash
set -euo pipefail

dataset_id="hydrosheds_peru_prototype"
filename="hybas_sa_lev01-12_v1c.zip"
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

- Execution date: 2026-06-30
- Download completed: yes
- Actual archive size: `334160720` bytes (matches header check)
- SHA-256:
  `fb012e48419bda0a7f4d0ebc56efcd906ad0e3bde324b9c70fac9693e2d21a72`
- Extraction completed: yes
- Extracted file count: 85 (12 levels x 7 shapefile components + TechDoc PDF; same structure as the Africa artifact)
- Field schema verified against level 6: `HYBAS_ID, NEXT_DOWN, NEXT_SINK, MAIN_BAS, DIST_SINK, DIST_MAIN, SUB_AREA, UP_AREA, PFAF_ID, ENDO, COAST, ORDER, SORT, geometry`; CRS `EPSG:4326`; identical to the Africa product.
- Boundary result note:
  `context/docs/project-management/peru_diagnostic_readiness_report_2026-06-30.md`

## Discovery Outputs To Record After Download

HydroBASINS levels will be inspected against the Arequipa-Moquegua-Tacna administrative envelope
before accepting any boundary. The discovery will record:

- candidate levels intersecting the three departments;
- candidate HYBAS_ID / PFAF_ID / SUB_AREA / UP_AREA at each inspected level;
- overlap of each candidate with the administrative envelope;
- CRS: EPSG:4326;
- candidate geometry validity;
- accepted state: not accepted (diagnostic_only).

The Peru boundary remains unaccepted (IFPM-D02 open) until the mentor resolves the
administrative-region vs hydrographic-unit choice.

## Current No-Go Boundaries

- Do not download additional data from this authorization (no SRTM, CHIRPS, HydroRIVERS).
- Do not use HydroBASINS output for flood-risk interpretation.
- Do not copy extracted vectors into `context/` or `ifpm-flood-pipeline/`.
- Do not run SRTM, CHIRPS, overlay, or map-generation steps from this authorization.
- Do not treat any discovered candidate as the accepted Peru boundary.
- Do not run any Zimbabwe-Peru comparison (requires harmonized criteria, still blocked).
