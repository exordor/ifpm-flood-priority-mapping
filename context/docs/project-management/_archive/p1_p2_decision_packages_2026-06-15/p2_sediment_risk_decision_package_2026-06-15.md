# P2 Risk R2.1 Sediment Risk Layer Decision Package

Date: 2026-06-15

Status: internal decision package. This document does not authorize any download, AHP overlay,
flood-risk interpretation, or intervention-priority interpretation. It maps the USLE/RUSLE
factor plan, identifies which factors are derivable from existing data and which need new
sources, and drafts public-safe preflight scaffolding for SoilGrids.

## Risk Statement

R2.1 (P2): the sediment-risk layer is entirely missing.

Original methodology (Section 2, Sediment Risk Layer) specifies the USLE model
`A = R x K x LS x C x P`, producing an Annual Soil Loss Map and a Sediment Risk Map. Current
state of each factor:

| Factor | Meaning | Data status | Derivable from existing data? |
|---|---|---|---|
| R | Rainfall erosivity | CHIRPS rainfall exists (V1 comparison done); R-factor computation NOT implemented | Yes (from existing CHIRPS), needs an R-factor formula decision |
| K | Soil erodibility | SoilGrids NOT downloaded | No; needs SoilGrids download (public) |
| LS | Slope-length / slope-steepness | SRTM DEM exists; LS NOT derived | Yes (from existing DEM), needs accepted hydro-conditioning (see R2.2) |
| C | Cover-management | ESA WorldCover exists (rough proxy); Sentinel-2/Landsat C-factor NOT derived | Partially; WorldCover is a coarse proxy; proper C-factor needs Sentinel-2 time series |
| P | Support practice | NOT available; typically set to 1 where unknown | No; needs local practice data or explicit assumption |

Consequence: the methodology promises a Sediment Risk Map, but zero of the five USLE factors are
currently computed. Without this, "Sediment Risk" cannot enter the AHP criteria hierarchy as a
quantitative layer, and the deliverable title's "Flood and Sediment Priority" framing is at
risk.

## Factor Plan

### R-factor (rainfall erosivity)

- Source: existing CHIRPS v3 inputs under `data/raw/chirps_v3_zimbabwe_prototype/`.
- Need: choose an R-factor formula (e.g. RUSLE modified Fournier index, or an
  event-energy-based formula). The formula choice is a domain decision.
- Output: native CHIRPS-grid R-factor diagnostics and V1 zonal summary; NOT a 30 m raster
  (CHIRPS-30m rule applies).
- Status: engineering-actionable once the formula is chosen; no new download.

### K-factor (soil erodibility)

- Source: SoilGrids 250m (ISRIC), public, CC BY 4.0. Provides soil properties (clay, silt, sand,
  organic carbon) from which K-factor is computed via one of the standard pedotransfer functions
  (e.g. Williams, Sharply-Williams).
- Need: SoilGrids download (public-safe) + K-factor formula decision.
- Preflight scaffolding: drafted under
  `context/docs/data-management/registry/soilgrids_250m_sediment_candidate.md` and
  `context/docs/data-management/preflight/soilgrids_250m_sediment_candidate.md`.
- Resolution note: SoilGrids is 250 m. It must NOT be resampled to 30 m as if it were
  pixel-level truth. Treat as 250 m diagnostics or V1/sub-basin zonal summary.

### LS-factor (slope length and steepness)

- Source: existing V1 DEM.
- Need: accepted hydrological-conditioning assumptions (R2.2 package), because LS depends on
  slope length which depends on flow accumulation / accumulated area.
- Output: V1 30 m LS raster, after grid gate.
- Status: engineering-actionable once R2.2 assumptions A1-A5 are accepted; no new download.

### C-factor (cover-management)

- Source: ESA WorldCover 2021 (already downloaded) as a coarse proxy; Sentinel-2 time series for
  a proper dynamic C-factor (NOT yet processed).
- Need: a mapping from land-cover / NDVI seasonal dynamics to C-factor values. This is a domain
  decision (which lookup table or which NDVI-based formula).
- Output: V1 30 m C-factor proxy from WorldCover as a first approximation; Sentinel-2 upgrade as
  future work.
- Status: partially engineering-actionable now (WorldCover proxy); full C-factor needs
  Sentinel-2 processing (engineering effort) plus a C-factor rule (domain decision).

### P-factor (support practice)

- Source: typically not available at this resolution for the Upper Mzingwane.
- Need: explicit domain decision. Common default is P = 1 (no support practice) where unknown,
  which removes P from the multiplication (identity).
- Output: documented assumption; no spatial layer unless local practice data arrives.
- Status: a documented assumption is sufficient for a first prototype; record the limitation.

## Recommended Sequencing

1. R-factor: choose a formula and compute from existing CHIRPS (no new download). Native grid +
   V1 summary only.
2. K-factor: close SoilGrids preflight, authorize scoped download, compute K via a chosen
   pedotransfer function. 250 m diagnostics + V1 summary.
3. LS-factor: wait for R2.2 hydro-conditioning acceptance, then derive from existing DEM.
4. C-factor: compute a WorldCover-based proxy now; flag Sentinel-2 upgrade as future work.
5. P-factor: record P = 1 assumption with limitation.

Only after all five factors exist at compatible units can an Annual Soil Loss Map be produced.
Even then, the multi-resolution inputs (R at ~5 km, K at 250 m, LS/C at 30 m) mean the sediment
output should be reported per the chosen modelling-unit branch (R2.4), not as a single
high-resolution raster.

## Claim Boundary Fallback

If the full USLE chain cannot be completed in time:

- Demote Sediment Risk from a quantitative AHP criterion to qualitative/context evidence in V1
  (same fallback pattern as the mining-data R1.2 package).
- Keep any produced factors (R, K, LS, C) as documented diagnostic evidence.
- State in public-facing docs that the sediment layer is partial and that the V1 priority map
  must not be read as a sediment-intervention plan.
- If the mentor accepts, the reduced-criteria hierarchy (per R1.2 fallback) drops both Mining
  and Sediment from scored criteria, leaving a flood-hazard/terrain/exposure/environmental
  priority map.

## Decision Questions For Mentor

1. Which R-factor formula should be used (modified Fournier index from monthly CHIRPS, or an
   energy-based formula requiring sub-daily data the project does not have)?
2. Is a SoilGrids-based K-factor acceptable at 250 m, or does the mentor prefer a local soil
   source?
3. Which C-factor mapping should be used (WorldCover lookup table, NDVI-based formula, or a
   mentor-supplied table)?
4. Is P = 1 acceptable as a documented default, or does the mentor have practice data?
5. If the full USLE chain cannot be completed, is demoting Sediment Risk to context acceptable?

## Boundaries And Blockers

- No new download is authorized by this document. SoilGrids download needs Step S3 authorization
  and mentor scope confirmation first.
- SoilGrids must NOT be resampled to 30 m as pixel-level truth; 250 m diagnostics or V1/sub-basin
  zonal summary only.
- LS-factor derivation depends on the R2.2 hydro-conditioning assumptions being accepted first.
- The sediment layer depends on the R2.4 modelling-unit decision for how multi-resolution factors
  are reconciled.
- Claim-boundary fallback applies to public docs and interpretation only.

## Cross-References

- Risk overview: `p2_risk_overview_2026-06-15.md`.
- Coupled package: `p2_hydrology_derivatives_decision_package_2026-06-15.md` (LS-factor
  dependency).
- Modelling unit: `p2_modelling_unit_decision_package_2026-06-15.md`.
- Mining fallback (pattern reference): `p1_mining_data_decision_package_2026-06-15.md`.
- CHIRPS comparison: `chirps_v1_rainfall_comparison_2026-06-13.md`.
- Preflight scaffolding: `context/docs/data-management/registry/soilgrids_250m_sediment_candidate.md`,
  `context/docs/data-management/preflight/soilgrids_250m_sediment_candidate.md`.
- Decision tasks: IFPM-064 (this package).
