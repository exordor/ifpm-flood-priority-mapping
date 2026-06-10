# HydroSHEDS Boundary-Discovery Result

Updated: 2026-06-10

Status: discovery executed; boundary not accepted.

## Scope

This note records the first HydroBASINS boundary-discovery run for the Zimbabwe / Upper
Mzingwane prototype.

Executed:

- downloaded the authorized HydroBASINS standard Africa artifact;
- verified source size and SHA-256 checksum;
- extracted local shapefile levels 1-12 under `data/raw/`;
- inspected candidate HydroBASINS units around Mzingwane Dam, Esigodini, and Gwanda.

Not executed:

- no SRTM download;
- no CHIRPS download;
- no HydroRIVERS download;
- no overlay, map generation, scoring, validation, or flood-risk interpretation.

## Data Evidence

- Dataset id: `hydrosheds_zimbabwe_prototype`
- Source artifact: `hybas_af_lev01-12_v1c.zip`
- Source URL:
  `https://data.hydrosheds.org/file/hydrobasins/standard/hybas_af_lev01-12_v1c.zip`
- Raw archive path: `data/raw/hydrosheds_zimbabwe_prototype/hybas_af_lev01-12_v1c.zip`
- Actual archive size: `549296874` bytes
- SHA-256:
  `6b331a6e89d56c3a542dcee39a7e6e8700d0cf7c94083c5946c7db0d262a48d6`
- Extraction path:
  `data/raw/hydrosheds_zimbabwe_prototype/extracted/hybas_af_lev01-12_v1c/`
- Extracted file count: 85
- Extracted levels inspected: 6, 7, 8, and 9
- CRS observed from local shapefiles: EPSG:4326

Raw data and extracted vectors remain under ignored `data/` paths. No vector geometry was copied
into `context/` or `ifpm-flood-pipeline/`.

## Anchor Points Used

These points were used only as discovery anchors, not as official boundary evidence:

- Mzingwane Dam: latitude `-20.38701`, longitude `28.95789`
- Esigodini: latitude `-20.2925`, longitude `28.938056`
- Gwanda: approximate downstream contrast point, latitude `-20.933333`, longitude `29.0`

The aim was to find HydroBASINS units that contain the upper Mzingwane anchor points and to check
whether they separate from the downstream Gwanda area.

## Candidate Units

### Whole Mzingwane-Scale Context

- Level: 6
- Candidate containing Mzingwane Dam and Esigodini:
  - HYBAS_ID: `1061548150`
  - PFAF_ID: `124508`
  - SUB_AREA: `15986.1` km2
  - UP_AREA: `15987.0` km2
  - Geometry validity: valid
- Discovery note: this is too broad for Upper Mzingwane. It is useful only as Mzingwane-scale
  context.

### Primary HydroBASINS Candidate

- Level: 7
- Candidate containing Mzingwane Dam and Esigodini, but not Gwanda:
  - HYBAS_ID: `1071528840`
  - PFAF_ID: `1245086`
  - NEXT_DOWN: `1071541770`
  - SUB_AREA: `3700.0` km2
  - UP_AREA: `3700.4` km2
  - Geometry validity: valid
- Discovery note: this is the strongest single HydroBASINS candidate from the anchor-point
  test, but it is not accepted as the final Upper Mzingwane boundary because its area is larger
  than the commonly reported Upper Mzingwane sub-catchment area of about 2138 km2.

### Finer Nested Candidates Under PFAF 1245086

Level 8 units inside the level 7 candidate:

| HYBAS_ID | PFAF_ID | SUB_AREA km2 | UP_AREA km2 | Anchor note |
| --- | --- | ---: | ---: | --- |
| `1081520450` | `12450868` | `749.2` | `749.3` | contains Esigodini |
| `1081520560` | `12450869` | `546.9` | `546.9` | contains Mzingwane Dam |
| `1081522660` | `12450865` | `163.3` | `1885.2` | closest upstream-area candidate to 2138 km2 |
| `1081528170` | `12450863` | `1067.4` | `3418.0` | broader nested candidate |

Discovery note: no single level 8 unit cleanly represents Upper Mzingwane from the current
evidence. A union of level 8 units may be required, but that union must be checked against a
mentor-supplied or authoritative local boundary before acceptance.

### Downstream Contrast

- Gwanda falls outside the primary level 7 candidate:
  - level 7 HYBAS_ID: `1071542430`
  - level 7 PFAF_ID: `1246002`
  - SUB_AREA: `7907.3` km2
- Discovery note: the primary candidate separates the upper anchor area from a downstream
  contrast point, which is useful but not sufficient for acceptance.

## Boundary Acceptance State

Current state: not accepted.

Reason:

- HydroBASINS level 7 candidate `1071528840` is plausible but too broad relative to the
  commonly reported Upper Mzingwane area.
- Level 8 candidates separate the anchor points into smaller units and may require a union.
- No authoritative local Upper Mzingwane boundary has been compared yet.
- No mentor review has accepted the HydroBASINS candidate or a union rule.

## Next Required Decision

Choose one of these paths before SRTM, CHIRPS, overlay, or interpretation:

1. Ask the mentor for an authoritative Upper Mzingwane boundary or official sub-catchment unit.
2. Accept HydroBASINS level 7 `HYBAS_ID=1071528840` with a documented area-mismatch waiver.
3. Define and review a level 8 union under `PFAF_ID=1245086`, then compare its area and shape
   against local boundary evidence.

Until one path is accepted, this discovery result supports boundary discussion only.

## Adversarial Review

Review mode: local two-angle review after execution.

Correctness and domain-boundary angle:

- Finding: the discovered level 7 candidate could be mistaken for an accepted Upper Mzingwane
  boundary if only the strongest-candidate id is copied forward.
- Triage: documented the state as `boundary not accepted`, kept the area mismatch visible, and
  listed the mentor/local-boundary or waiver decision as required before SRTM, CHIRPS, overlay, or
  interpretation.

Engineering and workspace-boundary angle:

- Finding: candidate-unit notes originally used the label `Interpretation`, which could be
  confused with prohibited map or risk interpretation.
- Triage: renamed those labels to `Discovery note` and kept all raw archive, extracted vectors,
  checksum, and manifest files under ignored `data/raw/`.

Residual risk: the common Upper Mzingwane area reference is enough to block acceptance, but not
enough to define a replacement boundary. A mentor-supplied or authoritative local boundary remains
the next required input.
