# P1 Risk R1.2 Mining / ASM Data Decision Package

Date: 2026-06-15

Status: internal decision package. This document does not authorize any download, does not accept
any boundary, and does not authorize AHP overlay, flood-risk interpretation, or
intervention-priority interpretation. It inventories mining/ASM data holders, assesses public
alternatives, and proposes a claim-boundary fallback if local mining evidence cannot be closed.

## Risk Statement

R1.2 (P1): mining and artisanal/small-scale mining (ASM) evidence is critically insufficient for
the two methodology criteria that depend on it (Mining Location & Intensity; Rehabilitation
Potential).

Current evidence baseline:

- OSM quarry/industrial polygons inside V1: 2 features, repeatedly labelled weak proxy evidence,
  not official active ASM footprints.
- Zimbabwe Geoportal mining-related layers screened for the V1 review envelope: zero useful local
  overlap.
- No Zimbabwe Geological Survey data.
- No Ministry of Mines and Mining Development ASM registrations or concessions cadastre.
- No Sentinel-2 / Landsat mining-disturbance mapping.
- No tailings-area, mine-footprint, spoil-exposure, or official active-disturbance data.
- Peru side: no INGEMMET, no ANA, no mining data at all.

Consequence: the project title positions this as a flood-prioritization model for "semi-arid
artisanal mining landscapes". Two of the seven AHP criteria depend on mining evidence that is
currently absent. If this is not closed, the mining and rehabilitation criteria must be demoted
from quantitative layers to qualitative/context evidence, which materially changes the
deliverable scope.

## Why This Cannot Be Self-Resolved

Per AGENTS.md and the project analysis note, mining-data interpretation is explicitly a
mentor/domain decision (IFPM-D05: Mining-Data Interpretation Rule). The HiWi must not:

- invent ASM footprints from imagination;
- treat OSM quarry tags as active mining;
- treat mining concessions or cadastre records as active disturbance without a domain rule;
- run a speculative remote-sensing classification and label it official mining evidence.

Most of the highest-value local sources are non-public or access-constrained and require mentor
introduction. This package therefore prepares the asks rather than attempting downloads.

## Data Holders Inventory (Zimbabwe)

### Primary institutional sources

#### Zimbabwe Geological Survey (ZGS)

- Parent: Ministry of Mines and Mining Development (MMMD).
- Holdings: geological maps, mineral occurrence databases, historical ASM site records.
- Access: typically request-based through MMMD; may require institutional affiliation.
- Relevant to: geological context, known mineral occurrence density (gold, chromite in
  Matabeleland South).

#### Ministry of Mines and Mining Development (MMMD)

- Holdings: mining lease/claim registers, ASM registrations, cadastre records.
- Access: the cadastre is partially digitised; formal request usually required.
- Relevant to: Mining Density, Mine Area, official ASM footprint proxies.
- Caveat: concessions/claims are rights, not active disturbance. Must be paired with a domain
  rule (IFPM-D05) before use as a criterion.

#### Zimbabwe Miners Federation (ZMF)

- Role: representative body for ASM operators.
- Holdings: membership records, ASM site lists (often non-spatial or coarse).
- Access: mentor or institutional introduction.

#### Environmental Management Agency (EMA)

- Holdings: Environmental Impact Assessments (EIAs) for mining projects, environmental compliance
  records, rehabilitation plans.
- Access: EMA regional offices (Matabeleland South); formal request.
- Relevant to: Rehabilitation Potential criterion (rehab plans, bonded disturbance areas).

#### Zimbabwe National Water Authority (ZINWA)

- Holdings: water-use permits near mining operations, catchment water-quality records.
- Access: same institutional contact family as the unpublished National catchment database
  referenced in IFPM-043.
- Relevant to: sediment/mining water-impact cross-check.

### Public alternatives (processing, not download)

#### Sentinel-2 ASM disturbance time series

- Approach: compute BSI (Bare Soil Index) or NBR (Normalized Burn Ratio) time series over V1;
  detect persistent bare/ disturbed anomalies consistent with active ASM.
- Strength: public imagery, 10 m, defensible if validated against even a small sample of known
  ASM sites.
- Weakness: not an official inventory; requires a labelled sample and domain rule before it can
  enter AHP scoring.
- Cost: a new `bin/` processing pipeline comparable to the SRTM terrain chain; engineering effort
  not a data-access blocker.
- Recommendation: viable as a V1 proxy ONLY if the mentor defines what counts as ASM disturbance
  and provides even a small set of validation points.

#### Academic / open ASM footprint maps

- Several published datasets map ASM extent regionally or globally (for example academic ASM
  maps for sub-Saharan Africa, or DE Africa derivatives). These are candidate context layers but
  each must be licence-checked and method-cited before use.
- Recommendation: a focused literature search is needed before assuming any open ASM footprint
  product covers Matabeleland South at usable accuracy.

## Data Holders Inventory (Peru)

Peru is entirely unstarted. Mining data holders for the eventual comparative side:

- INGEMMET: mining concessions cadastre, GEOCATMIN portal; more publicly accessible than the
  Zimbabwe equivalent.
- MINEM (Ministerio de Energia y Minas): formal mining statistics and formal-vs-informal
  classification.
- ANA (Autoridad Nacional del Agua): hydrological and water-quality records.
- Note: Peru side remains blocked by IFPM-D02 (Peru boundary rule) and is out of scope for this
  package's immediate actions.

## Recommended Approach (Tiered)

1. Tier A (mentor-gated, highest local value): request ZGS/MMMD/EMA/ZINWA data through mentor
   introduction. Use the prepared request template at
   `context/docs/mentor-explanation/Mining_Data_Access_Request_Template_2026-06-15.md`.
2. Tier B (public, medium cost): commission a focused literature search for open ASM footprint
   products covering Matabeleland South; licence-check candidates before any use.
3. Tier C (engineering, conditional): defer Sentinel-2 ASM disturbance mapping until the mentor
   defines an ASM-disturbance rule and provides a small validation sample. Do not start this
   pipeline speculatively.

## Claim Boundary Fallback (Important)

If Tier A access is denied or delayed past the thesis timeline, and Tier B/C do not yield a
defensible mining layer:

- Demote Mining Location & Intensity and Rehabilitation Potential from quantitative AHP criteria
  to qualitative/context evidence in V1.
- Restate the V1 AHP hierarchy as a reduced criteria set (for example Flood Hazard, Terrain,
  Land Use / exposed population, Environmental Sensitivity, Socioeconomic Vulnerability) and
  explicitly document the demotion in any public-facing material.
- Add a Limitations statement: mining and rehabilitation criteria are documented as future work
  pending official ASM data; the V1 priority map must not be read as a mining-intervention plan.
- Keep the mining/rehabilitation evidence rows in the methodology matrix as context only, not as
  scored criteria.

This fallback is honest and preserves the scientific-defensibility boundary. It is the
recommended default unless the mentor closes Tier A access.

## Decision Questions For Mentor

1. Can the mentor provide or introduce the HiWi to Zimbabwe Geological Survey, MMMD, EMA, or ZINWA
   contacts for ASM and mining data in Matabeleland South?
2. Does the mentor hold any existing ASM site lists, mining-footprint shapefiles, or EMA
   rehabilitation records for the Upper Mzingwane area?
3. What domain rule should separate mining concessions/claims from active disturbance
   (IFPM-D05)?
4. If no official mining data is obtainable, is the mentor willing to accept a reduced-criteria
   V1 priority map with mining and rehabilitation demoted to context?
5. Should a Sentinel-2 ASM disturbance pipeline be built for V1, and if so, can the mentor
   provide a small set of known ASM sites for validation?

## Boundaries And Blockers

- No new real download is authorized by this document.
- Tier A access requires explicit mentor introduction; this package only prepares the ask.
- Tier B literature search is read-only and produces no data until a candidate is licence-checked.
- Tier C processing must not begin until an ASM-disturbance rule and validation sample exist.
- Claim-boundary fallback applies to public docs and interpretation only; it does not authorize
  real-data AHP overlay, which remains blocked by IFPM-D01/D06 and Step S5 and IFPM-D04/D05.

## Cross-References

- Risk source: `p1_risk_overview_2026-06-15.md`.
- Preflight gate: `real_data_execution_preflight_gate.md` (IFPM-D05 mining-data rule).
- Existing context: `v1_full_methodology_evidence_sweep_2026-06-13.md`,
  `v1_full_methodology_adversarial_review_2026-06-13.md`.
- Decision tasks: IFPM-D05 (mining-data interpretation rule), IFPM-062 (this package).
- Companion: `Mining_Data_Access_Request_Template_2026-06-15.md`.
