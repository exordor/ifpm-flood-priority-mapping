# P2 Risk R2.3 Peru Side Decision Package

Date: 2026-06-15

Status: internal decision package. This document does not authorize any download, boundary
acceptance, AHP overlay, flood-risk interpretation, or intervention-priority interpretation for
Peru. It records the Peru-side scope gap, boundary options, data holders, and a recommended
sequencing relative to the Zimbabwe V1 work.

## Risk Statement

R2.3 (P2): the Peru comparative side is entirely blank.

The project is titled as a comparative flood-risk study of the Upper Mzingwane Catchment
(Zimbabwe) and the Arequipa-Moquegua-Tacna Region (Peru). Current state:

- `data/raw/` contains zero Peru datasets.
- No Peru boundary accepted (IFPM-D02 Peru boundary rule open).
- No Peru SRTM, CHIRPS, WorldCover, WorldPop, or mining data.
- No INGEMMET, MINEM, or ANA data accessed.
- All V1 preprocessing, evidence sweeps, and mentor packages are Zimbabwe-only.

Consequence: the comparative dimension of the project is zero. If Peru is a thesis requirement,
the current trajectory produces a single-site study, not a comparison. This must be explicitly
reconciled with the mentor before late-stage scope shock.

## Peru Boundary Options (IFPM-D02)

The original inventory names the "Arequipa-Moquegua-Tacna Region" as the Peru study area. This is
an administrative-region definition, which creates a catchment-versus-region bias risk (the same
class of risk flagged for Zimbabwe). Options:

1. Administrative regions (Arequipa + Moquegua + Tacna departments): matches the named study
   area but mixes multiple hydrological basins and includes Pacific-slope and highland areas
   with very different flood regimes.
2. Hydrographic units (ANA hydrographic units, or HydroBASINS South America): hydrologically
   coherent but does not match the named administrative region; needs a selection rule.
3. Clipped hydrological units intersecting the administrative regions: a compromise that keeps
   the named region's footprint while using hydrological boundaries for analysis.

Each option needs the same kind of boundary-acceptance evidence the Zimbabwe side required
(IFPM-D06 equivalent). None is currently documented.

## Peru Data Holders

#### INGEMMET (Instituto Geologico Minero y Metalurgico)

- Holdings: mining concessions cadastre (GEOCATMIN portal), geological maps, mineral occurrence
  data. More publicly accessible than the Zimbabwe equivalent.
- Access: GEOCATMIN web portal; typically direct download or WMS/WFS.
- Relevant to: Mining Location & Intensity criterion for Peru (the Peru-side equivalent of the
  Zimbabwe mining-data R1.2 gap, but with better public access).

#### MINEM (Ministerio de Energia y Minas)

- Holdings: formal mining statistics, formal-vs-informal classification, mining-related
  environmental compliance.
- Access: public statistics; formal cadastre via INGEMMET.

#### ANA (Autoridad Nacional del Agua)

- Holdings: hydrological stations, water-quality records, hydrographic unit boundaries.
- Access: request-based in some cases; boundary data partially public.
- Relevant to: Peru boundary (option 2/3), validation evidence (gauges), sediment context.

#### Public global sources (same families as Zimbabwe)

- SRTM 1 arc-second, CHIRPS v3, ESA WorldCover, WorldPop, GHSL, JRC Global Surface Water,
  HydroBASINS/HydroRIVERS South America, SoilGrids. All public and applicable to Peru without
  new institutional access.

## Why Peru Should Not Start Yet

Starting Peru now would duplicate the entire Zimbabwe V1 pipeline (boundary discovery, SRTM
preflight, DEM preprocessing, CHIRPS comparison, evidence sweep) before the Zimbabwe side has
closed its own P1/P2 gates. That would multiply unresolved questions rather than resolve them.

The defensible sequencing is:

1. Close the Zimbabwe P1/P2 decision gates first (boundary, modelling unit, AHP weights,
   validation, mining, sediment, hydrology).
2. Lock the agreed methodology (criteria hierarchy, standardization rules, modelling-unit
   branch, validation protocol) on the Zimbabwe side.
3. Then replicate the locked methodology to Peru, using Peru boundary options and Peru data
   holders, so the comparison is methodologically symmetric.

Starting Peru before the methodology is locked risks the two sides diverging in criteria,
resolution, and validation, which would invalidate the comparison.

## Recommended Approach

1. Defer all Peru downloads and processing until the Zimbabwe V1 methodology is locked.
2. Now: confirm with the mentor that the comparative scope is still required and on what
   timeline. If Peru is required, record the boundary option preference (1/2/3 above) so the
   Peru preflight can be drafted when the time comes.
3. When Peru starts: reuse the same public-source families (SRTM, CHIRPS, WorldCover, etc.) and
   the same governance (registry + preflight + Step S3 authorization per dataset).
4. Peru mining data: INGEMMET/GEOCATMIN is the one Peru-specific source with better public
   access than Zimbabwe; it should be the first Peru-specific dataset considered when Peru
   begins.

## Claim Boundary Fallback

If Peru cannot be completed within the thesis timeline:

- Reframe the deliverable explicitly as a single-site Zimbabwe flood-prioritization study, with
  Peru documented as future comparative work.
- State in public-facing docs that the comparative dimension is deferred, not falsified.
- Keep the methodology pipeline Peru-ready (same code, same source families) so Peru can be
  added later without rework.

This is honest and preserves the engineering investment. It is the recommended default unless
the mentor confirms Peru is a hard requirement on a fixed timeline.

## Decision Questions For Mentor

1. Is the Peru comparative side a hard thesis requirement, or is a single-site Zimbabwe study
   acceptable with Peru as future work?
2. If Peru is required, what is the timeline, and which boundary option (administrative regions,
   hydrographic units, or clipped units) is preferred?
3. Should the HiWi begin Peru preflight drafting now, or wait until the Zimbabwe methodology is
   locked?
4. Is INGEMMET/GEOCATMIN the agreed primary source for Peru mining data when Peru begins?

## Boundaries And Blockers

- No Peru download is authorized by this document.
- Peru boundary acceptance (IFPM-D02) remains open.
- Peru should not start until the Zimbabwe methodology is locked, to preserve comparative
  symmetry.
- Claim-boundary fallback applies to public docs and scope statements only.

## Cross-References

- Risk overview: `p2_risk_overview_2026-06-15.md`.
- Preflight gate: `real_data_execution_preflight_gate.md` (IFPM-D02 Peru boundary rule;
  excluded from the Zimbabwe gate scope).
- Zimbabwe mining data (pattern reference): `p1_mining_data_decision_package_2026-06-15.md`.
- Original inventory: `context/docs/original/Detailed_Dataset_Inventory_Zimbabwe_Peru.md`.
- Decision tasks: IFPM-D02 (Peru boundary rule), IFPM-067 (this package).
