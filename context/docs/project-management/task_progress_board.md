# IFPM Task Progress And Plan Board

Updated: 2026-07-02

Board restructured 2026-07-02: completed and superseded tasks moved from In Progress to Done (byte-for-byte, no content change); the ten mentor-gated decision packages (IFPM-061..070) compressed to a one-line index under "Awaiting mentor decisions" (full text in `_archive/p1_p2_decision_packages_2026-06-15/`); In Progress now holds the active implementation tasks. No task was deleted. Prior layout preserved in `task_progress_board.md.bak` until verified.

Scope: private project planning for the IFPM comparative flood-risk modelling workspace.

## Current Position

The workspace now has a clean split between private context and deliverable code. The minimal
AHP-MCDA weighted-overlay pipeline exists, data-download governance is defined, and future work
should move from method scaffolding to a controlled data/preprocessing prototype.

A 2026-06-15 project risk and data-gap review identified three P1 blocking risks: R1.1 validation
data effectively zero, R1.2 mining/ASM data critically insufficient, and R1.3 AHP weights with no
expert source. Decision packages, public-safe preflight scaffolding, a mentor mining-data request
template, an AHP elicitation protocol with a non-authoritative illustrative prior (CR verified
0.0406), and a consolidated claim-boundary fallback strategy are complete. All three remain
decision-gated and do not authorize any download, overlay, or interpretation.

A second 2026-06-15 pass covered the five P2 serious risks: R2.1 sediment-risk layer entirely
missing (USLE/RUSLE factor plan), R2.2 hydrology derivatives incomplete (hydrological-conditioning
assumptions A1-A5), R2.3 Peru side entirely blank, R2.4 modelling unit undecided (IFPM-D01), and
R2.5 final boundary not accepted. Decision packages, a SoilGrids preflight draft, and a
dependency-ordered sequencing plan are complete. Several P2 items are engineering-actionable from
existing data once their documented decisions are accepted; none authorizes overlay or
interpretation.

A 2026-06-15 scope clarification separated the HiWi data-processing role from the mentor/thesis
claim role. Data production (authorized public downloads, preprocessing, indicator derivation,
standardization, diagnostic overlays with documented weights) is GO and self-authorizing via
documented defaults. Interpretable claims (validated flood-risk map, intervention priority,
Zimbabwe-Peru comparison, publication) remain NO-GO and are the mentor's calls. The next
data-processing work proceeds without waiting for thesis-level mentor decisions.

On 2026-06-16 the mentor provided a methodology slide defining the PIM formula and a five-criteria
pairwise comparison matrix (Flood, Sediment, Land Use/ASM, Environmental, Socioeconomic). The
matrix is internally consistent (CR 0.022) and structurally aligns with the deliverable pipeline's
already-implemented overlay. However, the slide labels the matrix as an example, so it is recorded
as a mentor-provided candidate, not a final authorised weight matrix. The slide also leaves the
role of `Rehabilitation Potential` (input layer listed but absent from the PIM formula and matrix)
unconfirmed, which keeps the final AHP criteria hierarchy open at five or six criteria.

On 2026-06-16 the mentor also answered the V1 USLE R-factor bimodality question (IFPM-074): keep
V1 as a diagnostic baseline, switch V2 to a smoother R, and test whether the spatial hotspot
pattern survives. This unblocks V2 R-factor engineering as a HiWi data-processing action without
waiting for a thesis-level claim. The absolute A values remain R-dependent until the V2 smoother-R
robustness check is run (see IFPM-074/IFPM-077).

Do not start broad data downloads yet. HydroSHEDS boundary discovery has been executed for one
authorized artifact, and the Zimbabwe Geoportal Sub-Catchments alternative has been downloaded
and compared for boundary evidence. Mentor feedback now reframes the next step: define the study
catchment from the flood/mining-relevant outlet instead of choosing only between existing named
boundaries. V1 / `HB_L8_1081528840_full_l7_chain` is now
`accepted_with_waiver_for_controlled_prototype` after the mentor gave a thumbs-up reaction to the
evidence board. The V1 working boundary package, SRTM tile preflight, scoped SRTM raw-tile
download/inventory, V1 DEM/slope preprocessing, raster grid gate, terrain-only standardization
diagnostics, CHIRPS rainfall comparison, full methodology evidence sweep, and the deliverable
pipeline's Step S5 engineering readiness (IFPM-060) are complete. Model overlay, flood-risk
interpretation, and intervention interpretation remain blocked pending mentor decisions.

On 2026-06-24 the mentor-provided Voi rainfall archive was moved into managed raw-data storage and
rainfall-only intake was completed (IFPM-086). The selected Voi rainfall candidates are daily
records, not 5/15/30-minute real-time rainfall intensity. They can support only exploratory
monthly/annual R-range checks unless a true sub-daily rainfall intensity source is provided.

On 2026-06-25 the main workflow was moved back from Voi-side checking to an autonomous V1
prototype score (IFPM-087). Existing grid-compatible V1 evidence layers were combined into five
methodology-aligned criteria, then tested under four weight scenarios. The output is a provisional
autonomous prototype and hotspot-stability diagnostic, not a validated flood-risk map, not an
intervention-priority map, and not a final thesis boundary claim. Voi remains optional external
rainfall/R sanity-check evidence only.

On 2026-06-29 the project response to the mentor's 18 July trip question was reframed as a data
request and evidence-hardening task (IFPM-088/089). The V1 prototype is fixed as the current
baseline. The immediate need is a practical Zimbabwe/Peru data-request package for mining/ASM,
observed flood impact, rainfall, catchment/outlet confirmation, exposure, land use, and
rehabilitation evidence. In parallel, V1 v0.2 should harden the weakest current criteria:
mining/ASM pressure and socioeconomic exposure.

Also on 2026-06-29, defensive gates were converted into execution-status rules (IFPM-090). The
new rule is: uncertainty reduces claim level; it does not automatically pause execution.
Diagnostic, provisional, and sensitivity outputs may proceed when lineage, assumptions, and claim
level are explicit. Final flood-risk, intervention-priority, and final Zimbabwe-Peru comparison
claims remain gated.

On 2026-06-30 the Peru side, previously entirely blank, started with its first boundary-discovery
run (IFPM-091). HydroBASINS standard South America was downloaded under a boundary-only
authorization (the Peru analogue of the Zimbabwe HydroBASINS Africa discovery), and candidate
basins intersecting a discovery envelope around Arequipa-Moquegua-Tacna were found. This turns the
open Peru boundary decision (IFPM-D02) from an abstract choice into a concrete set of candidate
units with real areas. It does not accept any Peru boundary, run overlay, or make a cross-country
comparison. The data-readiness inventory shows the public global sources are ready for Peru
without new institutional access, and Peru's mining cadastre (INGEMMET/GEOCATMIN) is publicly
accessible — strictly better than Zimbabwe's OSM-only mining proxy.

Also on 2026-06-30, the Peru terrain chain was started with an engineering-pilot boundary PE1
(IFPM-092). Because the mentor has not named a specific Peru site, PE1 was selected by an explicit
rule (pacific-slope, fully inside the three-department envelope, area comparable to Zimbabwe V1,
non-terminal) to run the terrain chain end-to-end and prove comparability — it is NOT a
research-selected boundary. The chain completed: PE1 boundary exported (2745 km2, ratio 0.74 vs
Zimbabwe V1), 2 SRTM tiles downloaded, PE1 DEM built (EPSG:32718, 30 m, elevation 145-3188 m),
and a Peru reference-grid rule recorded. Peru now has a working terrain chain at a comparable
scale. PE1 will be replaced if the mentor names a specific Peru site. No overlay, interpretation,
or Zimbabwe-Peru comparison is authorized.

## Done

### IFPM-001 Workspace Boundary Split

- Status: done
- Evidence: root context repo and independent `ifpm-flood-pipeline/` repo are separated.

### IFPM-002 Dataset Inventory Review

- Status: done
- Evidence: reviewed inventory and fact-check notes exist under `context/docs/research-review/`
  and `context/docs/deep-research/`.

### IFPM-003 Mentor Explanation Package

- Status: done
- Evidence: English and Chinese mentor explanation guides exist under
  `context/docs/mentor-explanation/`.

### IFPM-004 Minimal AHP-Overlay Pipeline

- Status: done
- Evidence: `ifpm-flood-pipeline` commit `d2af7a4` implements AHP weights, CR checks,
  GeoTIFF overlay, tests, and CLI.

### IFPM-005 Data Download Governance

- Status: done
- Evidence: root commit `f88a758` adds download registry templates, checklist, and AGENTS rules.

### IFPM-006 Post-Implementation Review Rule

- Status: done
- Evidence: AGENTS now requires adversarial review and hardening after non-trivial
  implementation.

### IFPM-010 Project Task Board

- Status: done
- Evidence: this task progress board exists under `context/docs/project-management/`.

### IFPM-014 Multi-Level Progress Review

- Status: done; no P1 was found, but P2 gates remain before real-data overlay.
- Evidence: `context/docs/project-management/_archive/superseded_process_notes_2026-06/multi_level_progress_review_2026-06-10.md`.
- Next action: fix the boundary-discovery and engineering-readiness blockers recorded in the
  review report.

### IFPM-071 CDP Data Portal Verification

- Status: complete. Verified reachability, login, and download mechanism for candidate and
  existing portals via Chrome DevTools Protocol.
- Evidence: `context/docs/project-management/_archive/superseded_process_notes_2026-06/cdp_data_portal_verification_2026-06-15.md`,
  `bin/acquire/check_data_portals.py`, `outputs/data_portal_check/portal_check_report.json` + screenshots.
- Key results: SoilGrids is a VRT directory listing (no login, windowed HTTP read, no bulk
  download); EM-DAT HDX route changed to per-country profiles (Zimbabwe downloaded); GloFAS is
  NOT on CDS and its historical reanalysis is not publicly accessible (downgraded).

### IFPM-072 V1 SoilGrids K-Factor (USLE)

- Status: complete as a 250 m diagnostic data product.
- Evidence: `bin/factors/derive_v1_soilgrids_kfactor.py`,
  `context/docs/project-management/soilgrids_v1_kfactor_processing_2026-06-15.md`,
  `outputs/soilgrids_250m_sediment_candidate/k_factor_0_5cm_250m.tif`,
  `k_factor_0_30cm_avg_250m.tif`, `k_factor_diagnostics.json`.
- Key result: V1 K-factor (0-5 cm, US units) mean 0.1695, range [0.082, 0.251]; depth-stable;
  Williams 1995 formula. Kept at native 250 m; NOT resampled to 30 m.

### IFPM-073 EM-DAT Zimbabwe Country Profile Download

- Status: complete (anonymous HDX download, 8688 bytes).
- Evidence: `data/raw/emdat_public_validation_candidate/emdat_country_profile_zwe_2026-06-13.xlsx`,
  SHA-256 `46b76917a82f52b7849134664b75bb4d3b36e4219cf8d901c7328326e7b08884`.
- Key result: temporal/event-magnitude context for Zimbabwe validation; route corrected from the
  removed full-database dataset id to the per-country profile.

### IFPM-074 V1 USLE R-Factor (CHIRPS Modified Fournier)

- Status: superseded by the 2026-06-19 formula audit. The old 0.05 deg diagnostic is retained only
  as an error trace; it must not be used as R evidence.
- Evidence: `bin/factors/derive_v1_chirps_rfactor.py`,
  `usle_factor_batch_processing_2026-06-15.md`.
  (The deprecated `outputs/chirps_v3_zimbabwe_prototype/r_factor/` products were removed
  2026-07-01; see `outputs/v1_usle_soil_loss/DEPRECATED_DUE_TO_R_FACTOR_ERROR.md`.)
- Current interpretation: the old pattern was produced by a wrong Renard-Freimund
  predictor/break-point setup. All old V1/V2 R and A products are deprecated.
- Next action: do not regenerate the old V1 R/A workflow. Use the verified R-factor send packet
  and ask for the next R-method decision.

### IFPM-079 V2 Smoother R-Factor Candidates and Hotspot Survival Test

- Status: deprecated as an R/A communication package. The structure-test numbers may be revisited
  later, but the old board and causal framing must not be sent.
- Evidence:
  `context/docs/project-management/rfactor_investigation_consolidated.md` (includes the
  literature-integrity correction section),
  `bin/factors/derive_v2_rfactor_candidates.py`, `bin/factors/derive_v2_usle_soil_loss.py`,
  `bin/visualize/plot_v2_rfactor_comparison_board.py`, `bin/investigate/compare_v2_rfactor_candidates.py`.
  (The deprecated `outputs/.../r_factor_v2/` and `outputs/v1_usle_soil_loss/v2_rfactor/`
  products were removed 2026-07-01; the survival numbers are recorded in the consolidated
  note §5, and the full deprecation list is in
  `outputs/v1_usle_soil_loss/DEPRECATED_DUE_TO_R_FACTOR_ERROR.md`.)
- Current safe reading:
  - The old board is blocked.
  - The hotspot-survival numbers remain usable only as a possible future R-invariant structure
    check, not as evidence that any R formula is correct.
  - No V2 candidate is currently recommended.
- Literature-integrity review (2026-06-19, REVISED severity after a deeper pass against the
  original PDF; see IFPM-080):
  - REMOVED a "Lo et al. (1985)" candidate (R = 0.0737*MFI^1.81): Lo et al. 1985 used mean annual
    precipitation (not MFI), and the 0.0737/1.81 coefficients had no traceable source. Unverified.
  - UPGRADED TO HIGH (was "variable confusion"): the V1 R applies the P-based Renard-Freimund
    coefficients (0.0483/1.61/587.8/1.219/0.004105) to MFI with an INVENTED break at MFI=80. The
    paper's F-based (MFI) form breaks at F=55 mm. V1's MFI range (70-117) lies entirely in the
    upper branch of the correct form, so the V1 bimodality is an ARTIFACT of the wrong break, not
    a real erosivity structure. This means the V2 "resolve the bimodality" premise does NOT hold.
    V1/V2 R absolute values are NOT trustworthy until the correct method is chosen.
  - CORRECTED (was "non-universal"): the Arnoldus coefficients ARE Arnoldus 1977's original values
    (Renard-Freimund Eq 8: R=0.264*F^1.50), but Arnoldus's R units are metric (t-m cm ha-1 h-1
    yr-1), inconsistent with the USLE-standard MJ mm ha-1 h-1 yr-1. Unit mismatch, not
    non-universality.
  - Verified correct: K-factor conversion 0.1317 (Foster et al. 1981); LS constants 22.13/0.0896
    (Moore & Nieber 1989). LS exponents 0.4/1.2 verified against USDA-ARS GISus-M (Oliveira et al.
    2015, eq 13): the UCA LS form uses m in [0.4-0.56] and n in [1.2-1.3]; 0.4/1.2 are the
    lower-bound starting combination of that documented range.
- Impact on open risks/decisions:
  - The V2 "resolve the bimodality" framing does NOT hold (the bimodality was an artifact). Do not
    present V2 to the mentor as fixing a real V1 problem.
  - The V2 hotspot-survival test REMAINS VALID as a structure test (it uses the R-invariant
    K x LS x C reference and is independent of the R formula).
  - V1/V2 R-factor absolute values are NOT trustworthy; re-run of the R and USLE A factors is
    needed once the mentor chooses the correct R method for semi-arid Zimbabwe.
  - The correct F-form yields very high R for V1's MFI range, suggesting the US-calibrated
    Renard-Freimund relations may not transfer here; this is a mentor methodological decision.
  - Does NOT unblock flood-risk, AHP overlay, or intervention-priority interpretation.
- Next action: PAUSED on V2 mentor communication. Do NOT send the V2 board until Finding 2
  (IFPM-080) is resolved. Surface the R-factor method question to the mentor FIRST as the highest
  priority; the V2 structural results may be shared later, clearly separated from R-absolute-value
  claims.

### IFPM-080 USLE Formula And Citation Integrity Audit

- Status: complete as an internal audit record. A defensive sweep of every USLE/RUSLE formula,
  coefficient, unit, and citation in the V1 and V2 USLE tooling, after a spot-check found an
  unverified R-factor coefficient.
- Evidence: `context/docs/project-management/rfactor_investigation_consolidated.md`,
  `bin/investigate/verify_ls_factor_exponents.py`, `outputs/literature_verification/` (capture records).
- Key results (REVISED 2026-06-19 after a deeper pass against the original PDF):
  - FABRICATED and removed: the "Lo et al. (1985)" V2 R candidate (0.0737*MFI^1.81) had no
    traceable source. (See IFPM-079 for the removal.)
  - UPGRADED TO HIGH: the V1 R applies the P-based Renard-Freimund coefficients to MFI with an
    INVENTED break at MFI=80. The paper's F-based (MFI) form breaks at F=55 mm; V1's MFI range
    lies entirely in its upper branch, so the V1 bimodality is an artifact of the wrong break, not
    a real structure. V1/V2 R absolute values NOT trustworthy; needs mentor decision on the correct
    R method (the correct F-form yields very high R for this MFI range, questioning transferability
    of the US-calibrated relations to semi-arid Zimbabwe). Re-run of R and USLE A needed once
    chosen.
  - CORRECTED: Arnoldus coefficients ARE Arnoldus 1977's original values (R=0.264*F^1.50, Renard-
    Freimund Eq 8), but use metric units inconsistent with the USLE-standard R unit. Unit mismatch,
    not non-universality.
  - VERIFIED CORRECT: K-factor US->SI conversion 0.1317 (Foster et al. 1981); LS constants
    22.13/0.0896 and exponents 0.4/1.2 (Moore & Nieber 1989; 0.4/1.2 are the lower bound of the
    documented m[0.4-0.56]/n[1.2-1.3] range per USDA-ARS GISus-M, Oliveira et al. 2015 eq 13).
- Impact: the Renard-Freimund compound error is the most serious finding - it manufactured the V1
  bimodality that motivated the V2 exercise, so V1/V2 R and USLE A absolute values are NOT
  trustworthy and the "V2 resolves the bimodality" framing does not hold. The V2 hotspot-survival
  test remains valid as a structure test (R-invariant reference). K/LS findings are unaffected.
  Does NOT unblock any interpretable claim.
- Next action: PAUSED on V2 mentor communication. Hand the R-factor method question to the mentor
  FIRST (highest priority): which R method suits semi-arid Zimbabwe? Then re-derive the V1 R and
  USLE A; the V2 smoother-R exercise may be moot if the correct method is already smooth. Do NOT
  send the V2 board or the "V2 fixes the bimodality" framing until Finding 2 is resolved.
- Deprecation markers (2026-06-19): all V1/V2 R-factor and USLE A products are marked DEPRECATED
  in their output directories. Markers (local, not git-tracked since `outputs/` is ignored):
  - `outputs/v1_usle_soil_loss/DEPRECATED_DUE_TO_R_FACTOR_ERROR.md` (main notice + full product
    list). The per-directory pointer markers under `r_factor/` and `r_factor_v2/` were removed
    with those deprecated directories on 2026-07-01; this main notice is the surviving record.
  NOT deprecated and safe as a re-derivation base: `a_structure_K_LS_C_30m.tif` (R-invariant,
  K and LS verified correct). The V2 hotspot-survival NUMBERS remain valid as a structure test
  only. Re-run of R and A waits on the mentor's R-method decision.

### IFPM-081 Exploratory R-Factor Method Comparison For Semi-Arid Zimbabwe

- Status: complete as an exploratory experiment. Runs four literature-based R-factor methods on
  the V1 CHIRPS inputs and compares them to measured Zimbabwe R values, to turn the R-method
  question into an evidence-backed decision rather than an abstract choice.
- Evidence:
  `context/docs/project-management/rfactor_investigation_consolidated.md`,
  `bin/investigate/explore_rfactor_methods.py`, `bin/visualize/plot_rfactor_exploration_board.py`,
  `outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/rfactor_method_exploration_diagnostics.json`,
  `outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/mentor_rfactor_exploration_board.png`.
- Key results (V1 MFI mean 92.92, P_annual mean 583.5 mm; measured Zimbabwe R ~330, semi-arid
  range 150-400):
  - A: corrected Arnoldus (Nakil & Khire 2023, with 17.02 unit conversion): R = 2329 (7x measured).
  - B: RF F-based correct (Eq 13/14): R = 3719 (11x measured).
  - C: RF P-based correct (Eq 11/12): R = 1380 (4x measured).
  - D: OLD V1 (wrong): R = 408 (1.2x measured; closest only because errors cancelled).
  - E: Hurni (1985) regional R-P regression (R = -8.12 + 0.562*P): R = 320.
  - F: Epworth/Merritt (R = 38.5 + 0.35*M, the Harare RUSLE equation): R = 243.
  - REVISED CONCLUSION (the earlier "Hurni matches measured, so US formulas don't transfer" was
    wrong): the methods split into TWO incompatible R-families ~6x apart. HIGH-R family
    (Arnoldus 2329 / RF-F 3719 / RF-P 1380 / Elwell-Stocking-1976 Zimbabwe-native ~2000) all
    agree, including the Zimbabwe-native relation. LOW-R family (Hurni 320 / Epworth 243) agree
    with each other. The "measured" Epworth 329 was computed with the F equation, so it is
    CIRCULAR evidence - it confirms F, not the true R. No independent EI30 measurement exists for
    V1. The real open question: which family uses the correct R definition/units?
- Impact: reframes the R-method question from "fix the coefficient" / "non-transferable formulas"
  to "two unresolved literature R-families; needs a primary EI30 dataset or a mentor ruling".
  Supports IFPM-080 Finding 2 with concrete numbers. Does NOT re-derive V1 R or replace the
  deprecated products.
- Next action: SUPERSEDED - see IFPM-082, which adds an empirical ERA5 EI30 R that arbitrates the
  families. (The two-families framing and the Epworth-circularity finding stand; the family choice
  is now informed by empirical data.)

### IFPM-082 Empirical ERA5 EI30 R-Factor To Arbitrate The Two R-Families

- Status: complete as an exploratory experiment. Computes an empirical USLE/RUSLE R-factor from
  ERA5 hourly precipitation (open-meteo, no auth) to arbitrate the HIGH vs LOW R-families from
  IFPM-081 with INDEPENDENT (non-circular) data.
- Evidence:
  `context/docs/project-management/rfactor_investigation_consolidated.md`,
  `bin/investigate/compute_era5_empirical_rfactor.py`, `bin/visualize/plot_era5_empirical_rfactor_board.py`,
  `outputs/v1_usle_soil_loss/rfactor_empirical_era5/era5_empirical_rfactor_diagnostics.json`,
  `outputs/v1_usle_soil_loss/rfactor_empirical_era5/mentor_era5_empirical_rfactor_board.png`,
  `context/docs/data-management/registry/era5_hourly_precip_v1_rfactor.md`.
- Method: standard EI30 algorithm on ERA5 hourly (2018-2023, 7 V1 points), Wischmeier-Smith and
  Brown-Foster kinetic-energy forms, I60 as a lower bound on I30 (hourly != 30-min) plus an I30
  estimate.
- Key results (spatial-mean empirical R):
  - Wischmeier-Smith, I60 lower bound: R = 460; I30 est: 506.
  - Brown-Foster, I60 lower bound: R = 358; I30 est: 394.
  - Empirical R (~360-506) sits in/near the LOW family (Hurni/Epworth 240-320) and is ~4x BELOW
    the HIGH family (RF/Arnoldus/Elwell 1380-3719).
  - Because ERA5 hourly is a lower bound on true 30-min EI30, real R is likely above the empirical
    values but still well below the HIGH family.
- Current conclusion: the ERA5 hourly lower-bound check sits near the lower range and well below
  the high-family values. This supports asking the mentor for an R-method decision, but it does not
  validate a final R or A value.
- Impact: do not use the deprecated V1 R/A products. Use ERA5 only as lower-bound supporting
  evidence unless the mentor accepts it as the next rerun source.
- Extension (2026-06-19): extended to a 45-point V1 grid as an exploratory R diagnostic. The
  derived A layers are sensitivity outputs only and are not approved for mentor communication.
- Next action: do not send the ERA5 R/A raster board as accepted evidence. Send only the verified
  Figure 1 and Figure 2 package if the user approves.

### IFPM-083 Mentor Briefing: USLE R-Factor Investigation

- Status: superseded by the 2026-06-19 send/no-send verification pass. The older briefing remains
  as a work log, but should not be sent as-is.
- Evidence:
  `context/docs/project-management/rfactor_investigation_consolidated.md`
  and `context/docs/mentor-explanation/Mentor_RFactor_Figure_Send_Packet_2026-06-19.md`.
- Current send decision: Figure 1 (R-method comparison) and Figure 2 (ERA5 lower-bound check) are
  conditionally sendable with the safer captions. Figure 3 and all V1/V2 R/A boards are blocked.
- Current recommendation wording: ask the mentor which R route to use for the next V1 rerun
  (ERA5-based provisional R, or first seek rain-gauge/GPM data). Do not present any current A,
  flood-risk, or intervention-priority result as accepted.
- Next action: remove the unsafe Teams draft contents and resend only from the verified send
  packet if the user approves.

### IFPM-084 V1 Hydrology Candidate Evidence Standardization

- Status: complete as candidate evidence for mentor review (no overlay). Fills the gap left by
  IFPM-055: terrain had three 0-1 candidates but hydrology had none.
- Evidence: `bin/package/standardize_v1_hydrology.py`, `bin/visualize/plot_v1_hydrology_evidence_board.py`,
  `outputs/srtm_1arcsec_zimbabwe_prototype/hydrology_standardization/` (two 0-1 candidates +
  diagnostics CSV + handoff + mentor board),
  `outputs/v1_full_methodology_evidence_sweep/v1_full_methodology_evidence_matrix.csv` (updated).
- Key results:
  - `v1_twi_high_wetness_0_1.tif`: TWI standardized, higher TWI -> higher value (wet/converging
    flood-susceptible). Clip [5.23, 14.21], mean 0.28.
  - `v1_drainage_proximity_0_1.tif`: distance-to-drainage standardized (inverted), closer ->
    higher value (flood exposure). Clip [0, 800m], mean 0.63.
  - Same 2-98 percentile + min-max method as terrain candidates, so terrain and hydrology are
    comparable. Both pass the V1 raster grid gate (grid_compatible=true).
- Status: CANDIDATE EVIDENCE, NOT overlay-ready. Per AGENTS.md, no criterion enters AHP overlay or
  interpretation until the mentor confirms the criteria hierarchy (IFPM-D01/D04) and modelling
  unit (IFPM-D01).
- Next action: present alongside the terrain candidates (IFPM-055/056) in the next mentor review
  of the criteria hierarchy.

### IFPM-085 R-Factor Investigation Independent Verification

- Status: complete. A first-principles re-check of every formula, coefficient, and headline number
  in IFPM-079..082, by hand-calculating each method from the primary sources and comparing to the
  script output.
- Evidence: `context/docs/project-management/rfactor_investigation_consolidated.md`.
- Key results:
  - Renard-Freimund Eq 11-14 coefficients and break points (850/55 mm) re-extracted from the
    original PDF: confirmed.
  - Six R methods hand-calc vs script: A/B/C/E/F within <2% (non-linear mean effect); D's 25%
    difference explained by the 29/103 low/high-branch split (weighted mean 405.5 matches the
    raster's 408). No real error.
  - ERA5 EI30 algorithm: kinetic-energy equations correct, magnitudes in the literature range,
    annual R reproduced (508/462). Pareto effect (top-5 storms = 49% of R) physically plausible.
  - Elwell table, Epworth equation, LS exponents 0.4/1.2, K 0.1317, hydrology standardization: all
    verified.
  - ONE sourcing inaccuracy flagged and fixed: the "Arnoldus-family" method (A) uses Nakil & Khire
    2023's form whose base coefficient (0.152) is not Arnoldus 1977's 0.264; the briefing now says
    "Arnoldus-family" not "Arnoldus with a unit fix". Does not change the conclusion.
- Impact: the briefing's headline numbers are now backed by independent hand-calculation, not by
  "the script ran". No conclusion changes.

### IFPM-086 Mentor Voi Rainfall Intake

- Status: complete as rainfall-only intake; final R-factor calculation not started.
- Evidence:
  `context/docs/data-management/registry/mentor_voi_rainfall_measurements_2026-06-24.md`,
  `context/docs/project-management/mentor_voi_rainfall_intake_2026-06-24.md`,
  `bin/acquire/inventory_mentor_voi_rainfall_archive.py`, `bin/acquire/intake_mentor_voi_rainfall.py`, and ignored
  outputs under `outputs/mentor_voi_rainfall_intake/`.
- Key results:
  - Managed raw archive:
    `data/raw/mentor_voi_rainfall_measurements_2026-06-24/[PRIVATE_ARCHIVE_REDACTED]`.
  - Selected two Voi rainfall candidates:
    `[PRIVATE_WORKBOOK_REDACTED]` and `[PRIVATE_CSV_REDACTED]`.
  - Both selected rainfall candidates are daily records; no selected file supports strict
    `EI30/I30`.
  - Mean annual rainfall checks: `Precip_mm` [PRIVATE_RAINFALL_REDACTED], XLSX `Rain` [PRIVATE_RAINFALL_REDACTED], CSV
    `Rain` [PRIVATE_RAINFALL_REDACTED].
  - QSWAT+ weather files are inventoried but deferred because spot checks showed non-Voi
    coordinates and they are not treated as the mentor's Voi rainfall measurement data.
- Impact: Voi data may be used only for exploratory R-method range checking. It is not a V1 Upper
  Mzingwane rainfall replacement and does not unblock deprecated V1/V2 R/A outputs.
- Next action: if requested, compute separate exploratory daily/monthly empirical R candidates from
  `Precip_mm`, XLSX `Rain`, and CSV `Rain`, while keeping strict EI30 blocked.

### IFPM-087 V1 Autonomous Prototype Scoring v0.1

- Status: complete as provisional autonomous prototype scoring; not a final flood-risk or
  intervention-priority result.
- Evidence:
  `context/docs/project-management/v1_autonomous_prototype_v0_1_2026-06-25.md`,
  `bin/criteria/build_v1_autonomous_criteria_stack.py`,
  `bin/scenarios/run_v1_autonomous_priority_scenarios.py`,
  `bin/visualize/plot_v1_autonomous_prototype_board.py`, and ignored outputs under
  `outputs/v1_autonomous_prototype_v0_1/`.
- Key results:
  - Five criteria were built on the V1 reference grid: flood/hydrology, sediment structure,
    land use/ASM pressure, environmental sensitivity, and socioeconomic exposure.
  - All criteria and checked priority rasters passed the V1 raster grid gate.
  - The methodology-slide candidate matrix remains internally consistent (`CR=0.022046`) but is
    still treated as candidate/example weighting, not a final authorised AHP matrix.
  - Top-20% stable hotspot area across all four scenarios: `436.907 km2`.
  - Top-20% hotspot area in at least one scenario: `1066.03 km2`.
  - Mean priority standard deviation across scenarios: `0.04697`.
- Impact: the project now has a defensible autonomous baseline for asking whether hotspot patterns
  survive weight changes. It does not rely on Voi rainfall and does not revive deprecated R/A
  products.
- Next action: run external critique on `gpt_pro_review_prompt.md`, then refine the weakest
  criterion before any thesis-facing interpretation.

### IFPM-088 Mentor Trip Data Request Package For 18 July

- Status: complete as mentor-facing draft; ready to adapt for Teams or meeting preparation.
- Evidence:
  `context/docs/mentor-explanation/Mentor_Trip_Data_Request_Package_2026-06-29.md`.
- Key result: the request list is now focused on what the mentor can ask Zimbabwe and Peru
  contacts before or during the 18 July trip:
  - official mining / ASM locations and active/inactive status;
  - rehabilitation / environmental records;
  - observed flood-affected areas and flood event dates/damages;
  - local rainfall records and station metadata;
  - catchment/outlet confirmation;
  - local exposure, land-use, and infrastructure data.
- Impact: the mentor question is now answerable without sending a long technical progress report.
  The project can provide a practical data checklist before the trip.
- Next action: turn the package into the exact Teams reply or a one-page printable checklist if
  requested.

### IFPM-090 Defensive Gate Surgery / Execution Status Policy

- Status: complete as policy and gate-document update.
- Evidence:
  `AGENTS.md`,
  `context/docs/project-management/execution_status_policy.md`,
  `context/docs/project-management/assumptions_log.md`,
  `context/docs/project-management/real_data_execution_preflight_gate.md`,
  `context/docs/data-management/v1_terrain_reference_grid_rule.md`,
  `context/docs/data-management/preflight/chirps_v3_zimbabwe_prototype.md`,
  `context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/p1_ahp_weighting_decision_package_2026-06-15.md`,
  `context/docs/project-management/rfactor_investigation_consolidated.md`,
  and `context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/p2_risk_overview_2026-06-15.md`.
- Key result: CHIRPS/rainfall, AHP matrices, new R-factor families, and Peru readiness work are
  no longer treated as globally paused. They may proceed as `diagnostic_only`, `provisional`, or
  `sensitivity_scenario` outputs with metadata and claim-level limits.
- Still blocked: final flood-risk claims, intervention-priority claims, final approved AHP weights,
  native-30 m rainfall claims, reuse of deprecated R/A products, and final Zimbabwe-Peru
  comparison before harmonized criteria/normalization/thresholds.
- Next action: implement the next executable experiment: rainfall-included vs rainfall-excluded
  V1 scenario, or AHP slide-matrix scenario config, with explicit `claim_level`.

### IFPM-091 Peru Boundary Discovery And Diagnostic Readiness

- Status: complete as `diagnostic_only` boundary discovery + data-readiness inventory. Peru was
  previously entirely blank (zero Peru data, scripts, or outputs). This is the first Peru work.
- Evidence:
  `context/docs/data-management/preflight/peru_hydrobasins_boundary_discovery_authorization_2026-06-30.md`,
  `context/docs/project-management/peru_diagnostic_readiness_report_2026-06-30.md`,
  `bin/acquire/discover_peru_candidate_basins.py`, ignored raw under
  `data/raw/hydrosheds_peru_prototype/`, ignored outputs under
  `outputs/peru_boundary_discovery/`.
- Key results:
  - Downloaded HydroBASINS standard South America (`hybas_sa_lev01-12_v1c.zip`, 334 MB,
    SHA-256 recorded) under a boundary-only authorization, the exact analogue of the Zimbabwe
    HydroBASINS Africa discovery.
  - Found candidate basins intersecting a discovery envelope around Arequipa-Moquegua-Tacna:
    L7 units in the 2.8-14,300 km2 range (comparable to Zimbabwe V1 ~3,700 km2). Envelope
    intersect converges at about 160,600 km2. Topology likely_ok (0 dangling references).
  - Confirmed the catchment-vs-region bias risk: the three departments mix Pacific-slope and
    highland/inland drainage tendencies.
  - Data-readiness inventory shows the public global sources (SRTM, CHIRPS, WorldCover,
    SoilGrids, WorldPop) are ready for Peru without new institutional access; Peru mining
    cadastre (INGEMMET/GEOCATMIN) is publicly accessible (strictly better than Zimbabwe's
    OSM-only proxy).
- Impact: Peru moves from "entirely blank" to "IFPM-D02 is now a concrete choice backed by
  real candidate areas, and the data chain is ready to run once the boundary option is picked."
  Does NOT accept any Peru boundary, run overlay, or make a Zimbabwe-Peru comparison.
- Next action: surface IFPM-D02 to the mentor with this discovery as evidence (administrative vs
  hydrographic vs clipped boundary; is Peru a hard thesis requirement?); obtain an authoritative
  administrative polygon to replace the discovery envelope before any boundary acceptance.

### IFPM-092 Peru Engineering-Pilot Terrain Chain (PE1)

- Status: complete as `diagnostic_only` / `engineering_pilot` terrain chain. PE1 is NOT a
  research-selected boundary; it was chosen by an explicit selection rule (pacific-slope, fully
  inside the three-department envelope, area comparable to Zimbabwe V1, non-terminal) to run the
  Peru terrain chain end-to-end and prove comparability. It will be replaced if the mentor names a
  specific Peru site.
- Evidence:
  `context/docs/project-management/peru_pilot_boundary_decision_2026-06-30.md`,
  `context/docs/data-management/peru_pilot_terrain_reference_grid_rule.md`,
  `bin/package/export_peru_pilot_boundary.py`, `bin/acquire/plan_srtm_tiles_for_peru_pilot.py`,
  `bin/factors/preprocess_srtm_peru_pilot_dem.py`, ignored raw under
  `data/raw/srtm_1arcsec_peru_pilot/`, ignored outputs under
  `outputs/peru_pilot_boundary/` and `outputs/srtm_1arcsec_peru_pilot/`.
- Key results:
  - PE1 = HydroBASINS L7 `HYBAS_ID=6070641200`, `2745.4 km2` (ratio 0.74 vs Zimbabwe V1 ~3689.5
    km2), pacific-slope, ~17 km west of Arequipa city.
  - Downloaded 2 SRTMGL1 tiles (`S17W073`, `S17W072`, ~25 MB total, SHA-256 recorded) from the
    ESA STEP mirror (same source as Zimbabwe, no login).
  - PE1 DEM: `EPSG:32718` (UTM 18S), 30 m, float32, NoData -9999.0, elevation 144.9-3188.3 m,
    valid fraction 0.4506. This DEM is the Peru reference grid (separate from Zimbabwe's
    EPSG:32735 reference).
  - A Peru reference-grid rule is recorded so future Peru terrain derivatives must match it.
- Impact: the Peru side can now run the same terrain/hydrology/USLE workflow as Zimbabwe. Peru is
  no longer entirely blank; it has a working terrain chain at a comparable scale. This does NOT
  make PE1 a research-meaningful site, does NOT authorize overlay or interpretation, and does NOT
  make a Zimbabwe-Peru comparison.
- Next action: derive PE1 slope + hydrology (the next terrain derivatives), mirroring the
  Zimbabwe `derive_srtm_v1_slope.py` / `derive_v1_hydrology.py` against the PE1 reference grid.

### IFPM-093 Peru PE1 Full Evidence Stack + Prototype Priority Map

- Status: complete as `diagnostic_only` / `engineering_pilot` prototype. PE1 now has a full
  evidence stack and a priority map comparable to Zimbabwe V1 v0.2.
- Evidence: `bin/factors/derive_peru_pilot_usle_soil_loss.py`, `bin/criteria/build_pe1_criteria_stack.py`,
  `bin/scenarios/run_pe1_priority_scenarios.py`, ignored outputs under
  `outputs/srtm_1arcsec_peru_pilot/{ls_factor,usle_soil_loss,criteria_stack,priority_scenarios}/`
  and `outputs/esa_worldcover_2021_peru_pilot/`, `outputs/soilgrids_250m_peru_pilot/`.
- Key results:
  - USLE factors complete: LS (hillslope mean 3.70), K (0.1815 US, native 250m), C (mean 0.6096,
    bare/sparse dominant on arid Andean Pacific slope). PE1 USLE structure + provisional-R soil
    loss (LOW R=238.6 mean 8.74 t/ha/yr vs Zimbabwe 0.50 — steeper + barer terrain, expected).
  - Criteria stack: 3 criteria (flood_hazard, erosion_structure, land_cover_pressure) on the PE1
    30m grid. Mining + socioeconomic exposure DEFERRED (no Peru OSM/INGEMMET data processed yet) —
    recorded as gaps, NOT invented.
  - Priority scenarios (equal + flood/erosion heavy): top-20% stable hotspot across both
    scenarios `379.183 km2` (Zimbabwe V1 v0.2 ref `431.907 km2` with 4-6 criteria). PE1 board
    produced.
- Physical-comparison signal: PE1 C-factor (0.61, bare) vs Zimbabwe (0.04, shrub/grass), and PE1
  soil loss (8.74) vs Zimbabwe (0.50) — the two sites have fundamentally different erosion
  regimes (arid Andean Pacific slope vs semi-humid savanna). This is a real, defensible contrast,
  not noise.
- Impact: Peru is no longer entirely blank — it has a working full terrain/hydrology/USLE chain
  AND a provisional priority map at a comparable scale to Zimbabwe. The two countries can now be
  compared structurally. This does NOT make PE1 research-selected, does NOT authorize validated
  flood-risk claims, and does NOT by itself complete a Zimbabwe-Peru comparison (needs harmonized
  criteria + the missing mining/exposure criteria).
- Next action: obtain Peru OSM (roads/places/mining proxy) and/or INGEMMET/GEOCATMIN to fill the
  mining + exposure criteria; or present the Zimbabwe-Peru structural comparison to the mentor
  with explicit claim-level limits.

### IFPM-094 Peru PE1 Mining + Exposure Criteria (OSM) And Full 5-Criteria Priority Map

- Status: complete. PE1 now has all 5 criteria comparable to Zimbabwe v0.2, including the mentor-
  slide-mapped priority scenario.
- Evidence:
  `context/docs/data-management/registry/geofabrik_osm_peru_pilot.md`,
  `bin/criteria/build_pe1_osm_proximity_criteria.py`, `bin/criteria/build_pe1_criteria_stack.py`,
  `bin/scenarios/run_pe1_priority_scenarios.py`, ignored raw under
  `data/raw/geofabrik_osm_peru_pilot/`, ignored outputs under
  `outputs/geofabrik_osm_peru_pilot/pe1_proximity/` and
  `outputs/srtm_1arcsec_peru_pilot/priority_scenarios/`.
- Key results:
  - Downloaded Geofabrik Peru OSM (597 MB, SHA-256 recorded) under the same ODbL license as the
    Zimbabwe extract.
  - Built two proximity criteria: `mining_pressure` (32 quarry/industrial polygons in PE1+5km —
    stronger than Zimbabwe V1's 2 polygons) and `socioeconomic_exposure` (6210 roads).
  - PE1 criteria stack now has 5 criteria: flood_hazard, erosion_structure, land_cover,
    mining_pressure, socioeconomic_exposure.
  - Priority scenarios (equal + mentor_slide_mapped CR=0.022 + flood_erosion_heavy): top-20%
    stable hotspot across all 3 scenarios `368.411 km2` (Zimbabwe V1 v0.2 ref `431.907 km2`).
    PE1 priority board produced.
- Impact: Peru PE1 is now methodologically symmetric to Zimbabwe V1 v0.2 — same 5-criteria
  structure, same slide-matrix scenario, comparable hotspot-stability output. The two countries
  can now be structurally compared with the same weighting. Still diagnostic_only /
  engineering_pilot: not a validated flood-risk map, not an intervention plan, PE1 not a
  research-selected boundary, no harmonized final comparison claim yet.
- Next action: present the Zimbabwe-Peru structural comparison (5-criteria priority maps, slide-
  matrix scenarios, hotspot stability) to the mentor with explicit claim-level limits; or upgrade
  the mining criterion from OSM proxy to INGEMMET/GEOCATMIN official cadastre.

### IFPM-095 Peru PE1 Mining Criterion Upgrade (INGEMMET Official ASM Points)

- Status: complete. Upgraded the PE1 mining criterion from the weak OSM quarry/industrial proxy
  to official INGEMMET Pequeña Minería (small-scale/ASM mining) point evidence.
- Evidence:
  `context/docs/data-management/registry/ingemmet_catastro_minero_peru_pilot.md`,
  `bin/acquire/extract_pe1_ingemmet_mining.py`, `bin/criteria/build_pe1_criteria_stack.py` (mining input switched
  to INGEMMET), ignored raw under
  `data/raw/ingemmet_catastro_minero_peru_pilot/`, ignored outputs under
  `outputs/ingemmet_catastro_minero_peru_pilot/`.
- Key results:
  - Verified INGEMMET GEOCATMIN is publicly queryable via ArcGIS REST
    (`/arcgis/rest/services/SERV_PEQUENA_MINERIA/MapServer/0`), no login.
  - Queried 11 official ASM mining points inside the PE1 envelope (mineral codes, e.g. Au; mine
    codes; lab assays) — official-source evidence, strictly stronger than the OSM proxy.
  - Rebuilt the PE1 mining_pressure criterion from INGEMMET point proximity; reran the 5-criteria
    priority scenarios. Stable top-20% hotspot shifted to `307.356 km2` (was 368 with the OSM
    proxy) — the official ASM locations produce a more precise, defensible pressure pattern.
- Impact: PE1's mining criterion is now `provisional` official-source evidence, not a weak land-use
  proxy. This is the one criterion where Peru is strictly better evidenced than Zimbabwe (Zimbabwe
  still has only the OSM proxy; its official mining data remains ungated/awaited via mentor).
  Still point-proximity, not active-disturbance polygons; not a validated mining truth.
- Next action: present the full PE1 5-criteria prototype (now with official mining) alongside the
  Zimbabwe V1 v0.2 prototype for the structural Zimbabwe-Peru comparison.

### IFPM-096 Peru PE1 Rainfall Criterion (CHIRPS Coarse-To-Grid) And Full 6-Criteria Symmetry

- Status: complete. PE1 now has a rainfall criterion, reaching full 6-criteria symmetry with the
  merged Zimbabwe v0.3 (which added rainfall_sensitivity_v0_3).
- Evidence: `bin/criteria/build_pe1_rainfall_criterion.py`, `bin/criteria/build_pe1_criteria_stack.py`,
  `bin/scenarios/run_pe1_priority_scenarios.py`, ignored outputs under
  `outputs/srtm_1arcsec_peru_pilot/rainfall_criterion/` and
  `outputs/srtm_1arcsec_peru_pilot/priority_scenarios/`.
- Key results:
  - Built PE1 rainfall_climatology from CHIRPS v3 latam Dec-Mar rainy-season mean
    (HTTP windowed read, 2014/15-2023/24), bilinear-resampled to the PE1 30m grid. Coarse-to-grid
    governance identical to Zimbabwe A-010 (PE1 = A-012): IFPM_NOTE band tag,
    `sensitivity_scenario`, effective resolution ~5 km, not pixel-level 30 m rainfall.
  - PE1 raw rainfall: 37.6-292.9 mm/season, mean ~78 (arid Andean Pacific slope; Zimbabwe V1 is
    wetter — another real physical-contrast signal).
  - PE1 criteria stack now 6 criteria: flood conditioning, soil erosion factors, land cover, mining, exposure,
    rainfall. Priority scenarios (equal + mentor_slide CR=0.022 + flood_erosion_heavy):
    top-20% stable hotspot 299.57 km2.
- Impact: PE1 is now methodologically symmetric to the merged Zimbabwe V1 v0.3 — same 6-criteria
  structure including the coarse-to-grid rainfall criterion. The two prototypes can be compared
  with identical weighting and identical criterion families. Still diagnostic_only /
  engineering_pilot / sensitivity_scenario: no validated risk, PE1 not research-selected, no
  harmonized final comparison claim.
- Next action: present the Zimbabwe (V1 v0.3) vs Peru (PE1) structural comparison to the mentor;
  both sides now share the full 6-criteria methodology.

### IFPM-075 V1 Hydrology Derivatives (whitebox)

- Status: complete as 30 m diagnostic rasters; all grid_compatible.
- Evidence: `bin/factors/derive_v1_hydrology.py`,
  `outputs/srtm_1arcsec_zimbabwe_prototype/hydrology_derivatives/` (filled DEM, D8 flow dir,
  flow accumulation cells+SCA, streams at t100/500/1000/5000, distance-to-drainage, TWI),
  `hydrology_grid_check.csv`, `usle_factor_batch_processing_2026-06-15.md`.
- Key result: max flow accumulation 4,036,878 cells = 3633 km2 (~98.5% reaches outlet); chosen
  threshold t500 = 0.45 km2; TWI 3.13-27.23. Float32/64 routing bug found and fixed. V1 edge
  caveat recorded. Unblocks LS-factor.

### IFPM-076 V1 USLE C-Factor (WorldCover lookup)

- Status: complete as 10m + 30m V1-grid diagnostic; grid_compatible.
- Evidence: `bin/factors/derive_v1_worldcover_cfactor.py`,
  `outputs/esa_worldcover_2021_v1_methodology/c_factor/c_factor_v1_30m.tif`,
  `usle_factor_batch_processing_2026-06-15.md`.
- Key result: V1 area-weighted mean C 0.0429 (within expected 0.03-0.06); lookup applied after
  mode resampling (10m->30m legitimate fine->coarse aggregation).

### IFPM-077 V1 LS-Factor And USLE Annual Soil Loss Diagnostic

- Status: complete as a 30 m diagnostic; A absolute values flagged (R-dependent). The R-dependence
  caveat now has a mentor-directed resolution path (2026-06-16, see IFPM-074): V1 stays as
  baseline, V2 uses a smoother R, and the LS x C x K hotspot structure is re-tested under V2.
- Evidence: `bin/factors/derive_v1_ls_factor.py`, `bin/factors/derive_v1_usle_soil_loss.py`,
  `outputs/srtm_1arcsec_zimbabwe_prototype/ls_factor/`,
  `outputs/v1_usle_soil_loss/a_structure_K_LS_C_30m.tif` (R-invariant base; the deprecated
  a_mean / a_low_R50 / a_high_R510 / a_mean_classes products were removed 2026-07-01),
  `ls_factor_and_usle_soil_loss_processing_2026-06-15.md`.
- Key results: LS hillslope mean 1.563, p95 5.511 (Moore-Nieber, channel-masked, capped 50). USLE
  A-mean 0.50 t/ha/yr; ~87% of V1 < 1 t/ha/yr (very low); erosion hotspots where steep slopes
  meet cropland/bare ground. Absolute A depends on the bimodal R-factor; spatial structure
  (LS x C x K) is trustworthy. Completes 5/5 USLE factors and the first V1 soil-loss diagnostic.

### IFPM-078 Mentor Methodology Slide Received (2026-06-16)

- Status: received and recorded as internal evidence; not an authorisation of final weights,
  overlay, or interpretation.
- Evidence:
  `context/docs/mentor-explanation/Mentor_Methodology_Slide_Record_2026-06-16.md`,
  `context/docs/project-management/mentor_methodology_slide_interpretation_2026-06-16.md`,
  `context/images/mentor_methodology_slide_2026-06-16.png`.
- Key results:
  - The slide defines the Priority Intervention Map index as
    `PIM = wF(FH) + wS(SR) + wL(LU) + wE(ES) + wSE(SV)` (five scored criteria), which structurally
    matches the deliverable pipeline's already-implemented weighted overlay.
  - The slide supplies a mentor-provided candidate pairwise matrix over the five criteria, computed
    at CR 0.022 (consistent): Flood 0.490, Sediment 0.226, Environmental 0.141, Land Use/ASM 0.087,
    Socioeconomic 0.056.
  - The slide labels the matrix as an example, so it is a candidate, not an authorisation. It must
    not enter `configs/` or generate interpretable outputs until explicitly confirmed.
  - The slide lists `Rehabilitation Potential` as an input layer but omits it from the PIM formula
    and pairwise matrix, leaving the final AHP criteria hierarchy open at five or six criteria.
- Impact on open risks/decisions:
  - Partially advances R1.3 / IFPM-063 (a mentor-provided candidate matrix now exists, but the
    authorisation question is still open).
  - Confirms the five-criteria PIM structure against the deliverable pipeline, reducing hierarchy
    uncertainty for the five named criteria.
  - Opens IFPM-D05 / Rehabilitation-Potential role (sixth scored criterion vs post-score
    scenario/filter) as a new explicit mentor question.
- Next action: surface the two slide-derived mentor questions (matrix authorisation; Rehabilitation
  Potential role). Do not promote the candidate matrix to `configs/`, do not run real-data overlay,
  and do not interpret outputs until the matrix and hierarchy are confirmed.

## In Progress

### IFPM-011 First Controlled Data Slice

- Status: V1 accepted with waiver for controlled prototype use; scoped SRTM raw-tile download and
  inventory, DEM/slope preprocessing, grid gate, and terrain-only standardization diagnostics are
  complete.
- Next action: decide whether the next controlled slice is mentor-facing terrain explanation,
  modelling-unit selection, or rainfall preflight. Keep overlay and interpretation blocked.

### IFPM-012 Raster Preprocessing Design

- Status: design drafted; real-data execution remains blocked until mentor decisions and
  preflight blockers are closed.
- Evidence: `context/docs/project-management/real_data_preprocessing_design.md`.
- Next action: use the execution preflight gate to close outlet, boundary, modelling-unit,
  temporal-window, and dataset-specific blockers before downloading or processing source data.

### IFPM-013 Real-Data Execution Preflight Gate

- Status: gate revised; scoped SRTM raw-tile download, inventory, DEM/slope preprocessing, grid
  gate, and terrain-only standardization diagnostics are complete. Current verdict remains
  `NO-GO` for CHIRPS, overlay, and interpretation.
- Evidence: `context/docs/project-management/real_data_execution_preflight_gate.md`.
- Next action: choose the modelling-unit branch and decide whether rainfall should stay as
  native-resolution/zonal summary context. Keep CHIRPS, overlay, and interpretation blocked until
  their own gates are closed.

### IFPM-089 V1 v0.2 Weakest-Criteria Hardening Plan

- Status: first inventory complete; hotspot comparison and revised maps not yet implemented.
- Evidence:
  `context/docs/project-management/v1_v0_2_weakest_criteria_hardening_2026-06-29.md`,
  `bin/prepare_v1_v0_2_weakest_criteria_inventory.py`, and ignored outputs under
  `outputs/v1_autonomous_prototype_v0_2/`.
- Key result: V1 v0.2 should not repeat broad experiments. It should preserve V1 v0.1 as baseline
  and harden the two weakest criteria:
  - `landuse_asm_pressure`: currently C-factor plus weak OSM mining proxy;
  - `socioeconomic_exposure`: currently road/access proximity, not observed exposure.
- Impact: this keeps the project moving autonomously while still aligning with the mentor's data
  trip. Missing data becomes a concrete request list rather than a blocker.
- Next action: compare the v0.1 stable hotspots against road-river crossings, OSM places,
  GHSL/WorldPop native summaries, and mining proxy without calling the comparison validation.

### IFPM-097 July 18 Mentor/Boss Comparison Pack

- Status: mentor/boss-facing visual package generated for final review. The package integrates the
  two-country prototype comparison with pixel-level dominant-criterion colouring and a short boss
  process figure.
- Evidence:
  `bin/visualize/plot_july18_integrated_priority_board.py` and ignored outputs under
  `outputs/zimbabwe_peru_prototype_comparison/`.
- Key result: the 7/18 package now has one main figure with four readable panels, a claim-level
  note on the figure face, a separate process figure, captions, and a short Teams draft. It uses
  existing Zimbabwe/Peru sensitivity-scenario outputs only.
- Next action: final visual QA and send-pack selection with the user. Do not open new modelling
  work before this packet is reviewed.

### Awaiting mentor decisions (gate-blocked)

The ten P1/P2 decision packages (IFPM-061..068) plus the compressed mentor briefing (IFPM-069) and the data-processor scope split (IFPM-070) are all `decision package complete; awaits mentor`. Their full text lives in `context/docs/project-management/_archive/p1_p2_decision_packages_2026-06-15/`; this subsection is a one-line index, not the decision content.

- **IFPM-061** P1 R1.1 Validation Data Decision Package — decision package and public-safe preflight scaffolding complete
- **IFPM-062** P1 R1.2 Mining Data Decision Package — decision package and mentor request template complete
- **IFPM-063** P1 R1.3 AHP Weighting Decision Package — partially advanced. A mentor-provided candidate pairwise matrix now exists but is not yet authorised as final. Decision package and elicitation instrument still await mentor confirmation
- **IFPM-064** P2 R2.1 Sediment Risk Decision Package — decision package and SoilGrids preflight scaffolding complete
- **IFPM-065** P2 R2.2 Hydrology Derivatives Decision Package — hydrological-conditioning assumptions A1-A5 drafted
- **IFPM-066** P2 R2.4 Modelling Unit Decision Package (IFPM-D01) — trade-off matrix and Branch-1 recommendation complete
- **IFPM-067** P2 R2.3 Peru Side Decision Package — scope and data-holder inventory complete
- **IFPM-068** P2 R2.5 Final Boundary Acceptance Decision Package — public-source hunt consolidated as exhausted
- **IFPM-069** Mentor Decision Briefing (Compressed) — the ~35 individual mentor questions across P1/P2 packages are compressed into eight dependency-ordered key decisions in three batches
- **IFPM-070** Data-Processor Scope Split In Governance — complete
## Current Milestones And Gates

### IFPM-020 Select Prototype Study Slice

- Priority: P1
- Task: choose Zimbabwe or Peru, exact boundary rule, and output resolution.
- Status: done for controlled prototype boundary; final thesis boundary remains open.
- Completion evidence:
  `context/docs/project-management/_archive/superseded_boundary_exploration_2026-06/v1_working_boundary_decision_2026-06-12.md`.

### IFPM-021 Create First Dataset Registry Notes

- Priority: P1
- Task: create registry notes for the first three selected datasets.
- Status: done for SRTM, HydroBASINS/HydroRIVERS, and CHIRPS v3.
- Completion evidence: three registry notes exist under `context/docs/data-management/registry/`.

### IFPM-022 Complete Download Preflight Checklists

- Priority: P1
- Task: complete the checklist for each selected dataset.
- Status: SRTM preflight ready for V1; CHIRPS remains blocked pending temporal/model-unit choices.
- Completion evidence: three preflight notes exist under `context/docs/data-management/preflight/`.

### IFPM-027 Close Real-Data Execution Gate

- Priority: P1
- Task: turn the consolidated preflight gate from `NO-GO` to a scoped `GO` for one dataset or
  one tiny prototype bundle.
- Status: scoped SRTM tile planning, download, and raw inventory completed against V1. General
  data download remains blocked by modelling-unit, rainfall-window, and engineering-readiness
  blockers.
- Completion evidence: updated gate record plus selected dataset preflight note with no
  unchecked pre-download blocking item.

### IFPM-029 Prepare HydroSHEDS Boundary Discovery

- Priority: P1
- Task: make candidate HydroBASINS ids a discovery output and prepare the non-executed download
  authorization.
- Status: done before execution; superseded by IFPM-039.
- Completion evidence:
  `context/docs/data-management/preflight/hydrosheds_boundary_discovery_authorization_2026-06-10.md`
  and updated HydroSHEDS registry/preflight notes.

### IFPM-039 Execute HydroSHEDS Boundary Discovery

- Priority: P1
- Task: download the authorized HydroBASINS standard Africa artifact and identify candidate
  HYBAS/PFAF ids without running SRTM, CHIRPS, overlay, or map interpretation.
- Status: done; boundary not accepted.
- Completion evidence:
  `context/docs/project-management/_archive/superseded_boundary_exploration_2026-06/hydrosheds_boundary_discovery_result_2026-06-10.md`.

### IFPM-040 Prepare Upper Mzingwane Boundary Decision Package

- Priority: P1
- Task: convert HydroBASINS discovery output into a mentor-facing decision package and internal
  decision record without accepting a boundary or running real-data overlay.
- Status: done; superseded as the active next-step framing by IFPM-044 outlet-based catchment
  planning after mentor feedback.
- Completion evidence:
  `context/docs/mentor-explanation/Upper_Mzingwane_Boundary_Decision_Package_2026-06-10.md`
  and `context/docs/project-management/_archive/superseded_boundary_exploration_2026-06/upper_mzingwane_boundary_decision_record_2026-06-10.md`.

### IFPM-041 Execute Zimbabwe Geoportal Sub-Catchments Boundary Comparison

- Priority: P1
- Task: use the authenticated Zimbabwe Geoportal Sub-Catchments dataset as the first alternative
  local named-boundary check, without downloading SRTM/CHIRPS or running overlay.
- Status: done; boundary still not accepted.
- Completion evidence:
  `context/docs/project-management/_archive/superseded_process_notes_2026-06/zimbabwe_geoportal_subcatchments_boundary_comparison_2026-06-10.md`,
  `context/docs/data-management/registry/zimbabwe_geoportal_subcatchments_2025.md`, and
  `context/docs/data-management/preflight/zimbabwe_geoportal_subcatchments_2025.md`.
- Key result: the Geoportal `Upper Mzingwane` polygon contains Mzingwane Dam and Esigodini and
  excludes Gwanda, but its area is about `7321.5 km2`. HydroBASINS level 7
  `HYBAS_ID=1071528840` is nearly contained within it but covers only about `49.8%` of the
  Geoportal named feature.

### IFPM-042 Fact-Check Upper Mzingwane Area References

- Priority: P1
- Task: verify whether the `~2138 km2` Upper Mzingwane area reference has external support and
  whether it supplies usable boundary geometry.
- Status: done; area reference is reported but source/geometry-unresolved.
- Completion evidence:
  `context/docs/project-management/_archive/superseded_boundary_exploration_2026-06/upper_mzingwane_boundary_fact_check_2026-06-10.md`.
- Key result: external sources support `~2138 km2`, but no checked source supplied a reusable GIS
  boundary, outlet point, projection, or area method. Boundary acceptance remains blocked.

### IFPM-043 Trace Upper Mzingwane 2138 km2 Boundary Source

- Priority: P1
- Task: find whether the `~2138 km2` Upper Mzingwane value traces to a public boundary file,
  official water-management GIS source, feasibility-study map, or author-held study-area polygon.
- Status: done for public-source hunt; boundary still not accepted.
- Completion evidence:
  `context/docs/project-management/_archive/superseded_boundary_exploration_2026-06/upper_mzingwane_boundary_source_hunt_2026-06-10.md`.
- Key result: modern papers repeatedly report or use the `~2138 km2` study area but do not expose
  reusable geometry. The strongest source leads are ZINWA's unpublished National catchment
  database, older Bulawayo/Matabeleland-Zambezi feasibility-study maps, Surveyor General map
  channels, or an author-requested study-area polygon.
- Next action: request the actual polygon/source citation from authors, ZINWA, mentor, or the
  feasibility-study/map holders before accepting any boundary or downloading SRTM/CHIRPS.

### IFPM-044 Reframe Prototype As Outlet-Based Catchment

- Priority: P1
- Task: revise the research plan after mentor feedback so the first prototype uses an
  outlet-based catchment definition instead of choosing only between existing named boundaries.
- Status: done as planning update; superseded by V1 working boundary waiver.
- Completion evidence:
  `context/docs/project-management/_archive/superseded_process_notes_2026-06/outlet_based_catchment_research_plan_2026-06-11.md`,
  revised `context/docs/project-management/_archive/superseded_boundary_exploration_2026-06/prototype_study_slice_decision.md`, and revised
  `context/docs/project-management/real_data_execution_preflight_gate.md`.
- Key result: `Upper Mzingwane` is now treated as the regional context, while the operational
  prototype boundary should be the upstream catchment of a mentor-selected or mentor-provisional
  flood/mining-relevant outlet.
- Next action: continue using V1 only under the prototype waiver; do not treat it as the final
  thesis boundary.

### IFPM-045 Candidate Outlet Discovery First Pass

- Priority: P1
- Task: generate provisional outlet and catchment candidates from existing local HydroBASINS and
  Zimbabwe Geoportal data, without accepting a boundary or downloading SRTM/CHIRPS.
- Status: done for first pass; needs domain validation and optional river/flood/mining evidence.
- Completion evidence:
  `context/docs/project-management/_archive/superseded_boundary_exploration_2026-06/candidate_outlet_exploration_2026-06-11.md`,
  `bin/_archive/superseded_outlet_exploration_2026-06/discover_candidate_outlets.py`, and local ignored outputs under
  `outputs/_archive/superseded_outlet_exploration_2026-06/candidate_outlet_discovery/`.
- Key result: `HB_L8_1081522660_literature_near` was the first script-ranked machine prior with
  area about `1879.9 km2`; after the 2026-06-12 mentor cue it is no longer the primary
  recommendation.
- Next action: use professional map evidence and the mentor's Level-8 downstream-to-Gwanda cue to
  review V1 / `HB_L8_1081528840_full_l7_chain`.

### IFPM-046 Candidate Outlet Diagnostic Figure Upgrade

- Priority: P1
- Task: upgrade the candidate outlet diagnostic outputs so a non-GIS reader can understand why
  C1-C7 are outlet proxies and how `target_id -> NEXT_DOWN` encodes flow direction.
- Status: done for explanation package; C1 later demoted by mentor-driven visual review and
  boundary still not accepted.
- Completion evidence:
  `bin/_archive/superseded_outlet_exploration_2026-06/export_candidate_topology.py`, revised `bin/_archive/superseded_outlet_exploration_2026-06/plot_candidate_outlets.py`,
  `outputs/_archive/superseded_outlet_exploration_2026-06/candidate_outlet_discovery/diagnostic_map_explained.png`,
  `outputs/_archive/superseded_outlet_exploration_2026-06/candidate_outlet_discovery/diagnostic_c1_flow_explainer.png`,
  `outputs/_archive/superseded_outlet_exploration_2026-06/candidate_outlet_discovery/diagnostic_topology_table.png`, and
  `outputs/_archive/superseded_outlet_exploration_2026-06/candidate_outlet_discovery/candidate_topology_edges.csv`.
- Key result: the package separates overview, C1 flow/topology explanation, and topology table
  views. It explicitly labels all C-points as outlet proxies, not measured outlets or accepted
  thesis boundaries.
- Next action: keep these figures as machine-prior diagnostics only; use IFPM-048 for the
  mentor-facing visual evidence package.

### IFPM-048 Professional Map Visual Outlet Review

- Priority: P1
- Task: use professional map evidence to interpret the mentor cue: Level-8 basin containing
  Mzingwane Dam and the main Mzingwane River channel downstream toward Gwanda.
- Status: done for mentor-review evidence package; V1 accepted with waiver for controlled
  prototype use, but final thesis boundary still not accepted.
- Completion evidence:
  `context/docs/project-management/_archive/superseded_boundary_exploration_2026-06/professional_map_outlet_review_2026-06-12.md`,
  `bin/_archive/superseded_outlet_exploration_2026-06/prepare_outlet_review_sources.py`, `bin/_archive/superseded_outlet_exploration_2026-06/compare_visual_outlets.py`,
  `bin/_archive/superseded_outlet_exploration_2026-06/plot_professional_outlet_review.py`,
  `outputs/_archive/superseded_outlet_exploration_2026-06/professional_outlet_review/mentor_outlet_evidence_board.png`, and
  `outputs/_archive/superseded_outlet_exploration_2026-06/professional_outlet_review/visual_outlet_candidates.csv`.
- Key result: V1 / `HB_L8_1081528840_full_l7_chain` is now
  `accepted_with_waiver_for_controlled_prototype`. C1 /
  `HB_L8_1081522660_literature_near` is demoted to machine prior only.
- Evidence notes: HydroRIVERS, Geofabrik OSM, and Geoportal Rivers were downloaded and clipped;
  Geoportal Flood Prone Zones has zero features intersecting the review envelope.
- Next action: use IFPM-049/050 outputs as the input to the next SRTM download authorization.

### IFPM-049 V1 Working Boundary Package

- Priority: P1
- Task: export the V1 working boundary, manifest, anchor check, and diagnostic map without
  downloading DEM or running overlay.
- Status: done; prototype-only waiver, not final thesis boundary.
- Completion evidence:
  `bin/package/export_v1_working_boundary.py`,
  `context/docs/project-management/_archive/superseded_boundary_exploration_2026-06/v1_working_boundary_decision_2026-06-12.md`,
  `outputs/v1_working_boundary/v1_working_boundary.gpkg`,
  `outputs/v1_working_boundary/v1_working_boundary_manifest.csv`,
  `outputs/v1_working_boundary/v1_anchor_check.csv`, and
  `outputs/v1_working_boundary/v1_boundary_diagnostic.png`.
- Key result: V1 area remains about `3689.484 km2`; Mzingwane Dam and Esigodini are inside V1,
  while Gwanda, Filabusi approx, and West Nicholson approx are outside.
- Next action: use V1 as the mask for the scoped SRTM download step only.

### IFPM-050 SRTM Tile Preflight For V1

- Priority: P1
- Task: compute SRTM tile names from the V1 boundary plus 5 km buffer, without downloading data.
- Status: done for pre-download planning; superseded by IFPM-051.
- Completion evidence:
  `bin/acquire/plan_srtm_tiles_for_v1.py`,
  `outputs/v1_working_boundary/srtm_v1_tile_plan.csv`,
  `outputs/v1_working_boundary/srtm_v1_tile_plan.gpkg`, and
  `outputs/v1_working_boundary/srtm_v1_preflight_summary.md`.
- Key result: planned bbox EPSG:4326 is
  `28.514098, -21.007996, 29.398052, -19.984062`; planned tiles are `S22E028`,
  `S22E029`, `S21E028`, `S21E029`, `S20E028`, and `S20E029`.
- Next action: superseded by IFPM-051.

### IFPM-051 SRTM V1 Download And Raw Inventory

- Priority: P1
- Task: download only the six approved SRTMGL1 tiles, record source file evidence, compute
  checksums, and verify raw raster metadata without deriving terrain indicators.
- Status: done for raw download and inventory; no terrain preprocessing or overlay was run.
- Completion evidence:
  `bin/acquire/download_srtm_v1_tiles.py`,
  `bin/acquire/inventory_srtm_v1_tiles.py`,
  `context/docs/project-management/srtm_v1_download_and_inventory_2026-06-12.md`,
  `outputs/srtm_1arcsec_zimbabwe_prototype/srtm_raw_file_manifest.csv`,
  `outputs/srtm_1arcsec_zimbabwe_prototype/srtm_tile_inventory.csv`, and
  `outputs/srtm_1arcsec_zimbabwe_prototype/srtm_tile_coverage_check.png`.
- Key result: six ZIP archives were downloaded from the ESA STEP SRTMGL1 mirror without login,
  totaling `41,162,741` bytes. Each tile opens as `SRTMHGT`, `EPSG:4326`, `3601 x 3601`, one
  `int16` band, NoData `-32768`.
- Next action: plan and execute a separate terrain preprocessing step only after recording metric
  CRS, mosaic/clip rule, void/NoData handling, and output diagnostics.

### IFPM-052 SRTM V1 Terrain Preprocessing

- Priority: P1
- Task: convert the downloaded SRTM raw tiles into V1 DEM and slope diagnostic rasters without
  hydrological conditioning, rainfall, overlay, or interpretation.
- Status: done for DEM, QA hillshade visualization, and slope diagnostics.
- Completion evidence:
  `bin/factors/preprocess_srtm_v1_dem.py`,
  `bin/factors/derive_srtm_v1_slope.py`,
  `bin/visualize/plot_srtm_v1_terrain_qa.py`,
  `context/docs/project-management/srtm_v1_terrain_preprocessing_2026-06-12.md`, and
  `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_terrain_preprocessing_diagnostics.csv`.
- Key result: final DEM and slope rasters are `EPSG:32735`, `30 m`, single-band `float32`, NoData
  `-9999.0`, and both have `1.0` valid-cell fraction inside V1. DEM elevation ranges from about
  `863.0` to `1531.5 m`; slope ranges from `0.0` to `55.6 degrees`.
- Next action: implement or run a V1 raster-grid gate before using terrain derivatives in any
  standardization or score.

### IFPM-053 V1 Terrain Reference Grid Rule

- Priority: P1
- Task: fix the V1 terrain raster compatibility rule in a saved project file so later terrain
  derivatives cannot silently drift from the V1 DEM grid.
- Status: done as an internal rule; no new data downloaded and no overlay run.
- Completion evidence:
  `context/docs/data-management/v1_terrain_reference_grid_rule.md`.
- Key result: the current V1 DEM is the only reference raster for V1 terrain derivatives.
  Overlay is blocked unless candidate terrain rasters match its CRS, transform, resolution,
  shape, band count, dtype, NoData, and V1 valid-cell coverage. CHIRPS is explicitly excluded
  from pixel-level 30 m terrain-grid overlay.
- Next action: add or run `bin/package/check_v1_raster_grid.py` before any future V1 standardization,
  scoring, or weighted overlay.

### IFPM-054 V1 Raster Grid Gate

- Priority: P1
- Task: implement the executable gate that checks V1 terrain rasters against the fixed reference
  DEM before any standardization, scoring, or overlay.
- Status: done for current final V1 DEM and slope rasters.
- Completion evidence:
  `bin/package/check_v1_raster_grid.py` and
  `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_preprocessing/v1_raster_grid_check.csv`.
- Key result: the final V1 DEM and final V1 slope are `grid_compatible=true`. A buffered-DEM
  failure probe correctly failed on transform, width, height, and bounds mismatch.
- Next action: decide terrain standardization rules for elevation and slope before any scoring or
  weighted overlay. CHIRPS remains excluded from the 30 m terrain-grid overlay path.

### IFPM-055 V1 Terrain Standardization Diagnostics

- Priority: P1
- Task: generate terrain-only 0-1 diagnostic candidates from the V1 DEM and slope rasters after
  the raster grid gate, without CHIRPS, AHP weights, overlay, or interpretation.
- Status: done for prototype diagnostic candidates.
- Completion evidence:
  `bin/package/standardize_v1_terrain.py`,
  `context/docs/project-management/v1_terrain_standardization_rule_2026-06-13.md`, and
  `outputs/srtm_1arcsec_zimbabwe_prototype/terrain_standardization/v1_terrain_standardization_diagnostics.csv`.
- Key result: elevation lowland context, low-slope susceptibility, and high-slope runoff-pressure
  candidates were produced with 2nd-98th percentile min-max scaling and passed the V1 raster grid
  gate.
- Next action: decide whether the mentor-facing terrain explanation should use low-slope
  susceptibility, high-slope runoff pressure, or keep both as alternatives before any AHP criteria
  hierarchy or overlay work.

### IFPM-056 V1 Terrain Mentor Package

- Priority: P1
- Task: convert terrain-only standardized diagnostics into a mentor-facing figure board, caption,
  evidence table, and handoff without adding CHIRPS, AHP weights, overlay, or interpretation.
- Status: done for mentor review package.
- Completion evidence:
  `bin/visualize/plot_v1_terrain_mentor_package.py`,
  `context/docs/project-management/v1_terrain_mentor_package_2026-06-13.md`, and
  `outputs/v1_terrain_mentor_package/mentor_v1_terrain_diagnostic_board.png`.
- Key result: the package presents lowland context, low-slope susceptibility, and high-slope
  runoff-pressure alternative as terrain-only diagnostic candidates. The low-slope layer is the
  primary mentor-review candidate; high-slope runoff pressure is retained as an alternative.
- Next action: send the board and short question to the mentor before choosing a terrain criterion
  direction for any future AHP criteria hierarchy.

### IFPM-057 V1 Multi-Criteria Evidence Package

- Priority: P1
- Task: combine existing terrain, river/flood context, exposure, mining proxy, and rainfall
  readiness/gap evidence into a mentor-facing criteria review package without CHIRPS download,
  AHP weights, overlay, or interpretation.
- Status: done for first mentor review package.
- Completion evidence:
  `bin/package/prepare_v1_multicriteria_evidence.py`,
  `bin/visualize/plot_v1_multicriteria_evidence_board.py`,
  `context/docs/project-management/_archive/superseded_process_notes_2026-06/v1_multicriteria_evidence_package_2026-06-13.md`, and
  `outputs/v1_multicriteria_evidence_package/mentor_v1_multicriteria_evidence_board.png`.
- Key result: the evidence package covers terrain, hydro/flood context, exposure, mining proxy,
  and rainfall readiness. Rainfall is marked as a CHIRPS preflight gap, Geoportal Flood Prone
  Zones have zero local overlap, and OSM quarry/industrial features are labelled weak proxy
  mining evidence.
- Next action: ask the mentor which evidence families should enter the first prototype criteria
  set before any AHP hierarchy, CHIRPS processing, or overlay.

### IFPM-058 V1 CHIRPS Rainfall Comparison

- Priority: P1
- Task: process multiple CHIRPS rainfall definitions for the V1 working catchment and compare
  annual background, rainy-season accumulation, anomaly, monthly peak, pentad peak, and one
  daily RNL-derived peak without choosing a final rainfall criterion.
- Status: done for mentor-review sensitivity package.
- Completion evidence:
  `bin/acquire/plan_chirps_v1_rainfall_metrics.py`,
  `bin/acquire/download_chirps_v1_rainfall_inputs.py`,
  `bin/investigate/compare_chirps_v1_rainfall_metrics.py`,
  `bin/visualize/plot_chirps_v1_rainfall_comparison.py`,
  `context/docs/project-management/chirps_v1_rainfall_comparison_2026-06-13.md`,
  and
  `outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/mentor_v1_chirps_rainfall_comparison_board.png`.
- Key result: 561 scoped CHIRPS inputs were downloaded or clipped, all readable at `EPSG:4326`
  and about `0.05 degree`. V1 recent annual and rainy-season anomaly are both about `17.5%`,
  while pentad peak has a much different spatial pattern from long-term annual rainfall.
- Next action: ask the mentor whether rainfall should enter the first prototype criteria set as
  background climate, rainy-season accumulation, recent anomaly, monthly/pentad extreme, daily
  sensitivity only, or context only. Keep AHP weights, 30 m CHIRPS resampling, weighted overlay,
  flood-risk interpretation, and intervention-priority mapping blocked.

### IFPM-059 V1 Full Methodology Evidence Sweep

- Priority: P1
- Task: process every methodology factor into comparable candidate evidence rows and supporting
  layers without creating AHP weights, weighted overlay, flood-risk maps, or intervention maps.
- Status: done for mentor-review evidence package.
- Completion evidence:
  `bin/acquire/download_v1_methodology_inputs.py`,
  `bin/package/prepare_v1_full_methodology_evidence.py`,
  `bin/package/prepare_v1_methodology_raster_layers.py`,
  `bin/package/prepare_v1_methodology_vector_layers.py`,
  `bin/criteria/build_v1_full_methodology_evidence_matrix.py`,
  `bin/visualize/plot_v1_full_methodology_evidence.py`,
  `context/docs/project-management/_archive/superseded_process_notes_2026-06/v1_full_methodology_evidence_sweep_2026-06-13.md`,
  `context/docs/project-management/_archive/superseded_process_notes_2026-06/v1_full_methodology_adversarial_review_2026-06-13.md`, and
  `outputs/v1_full_methodology_evidence_sweep/v1_full_methodology_evidence_matrix.csv`.
- Key result: the matrix now covers flood hazard, rainfall, terrain, land use / ASM,
  environmental sensitivity, socioeconomic vulnerability, and rehabilitation potential. New
  processed evidence includes ESA WorldCover, WorldPop, GHSL built-up/population, JRC Global
  Surface Water, DFO Zimbabwe-level historical flood context, and WDPCA Zimbabwe
  protected/conserved areas.
- Next action: use the matrix and separated panels to ask the mentor which evidence families are
  eligible for the first prototype criteria set. Keep AHP weights, overlay, flood-risk
  interpretation, and intervention-priority mapping blocked.

### IFPM-060 V1 Deliverable Step S5 Engineering Readiness

- Priority: P1
- Task: close the five Step S5 / IFPM-028 engineering-readiness items so the weighted-overlay
  deliverable pipeline is safe for controlled real-data execution, without running real-data
  overlay, AHP weighting on real data, or interpretation.
- Status: done for engineering readiness; overlay and interpretation remain blocked.
- Completion evidence: `ifpm-flood-pipeline` commit `39f6b33` adds a durable geospatial fixture
  pair (`tests/fixtures/score_5x5.tif`, `zones_5x5.tif`) with a stable-signature regression test
  and `tests/GEOSPATIAL.md`; finite-value/mask summaries in `raster_diagnostics`; 0-1 overlay-input
  enforcement with `--allow-out-of-range` override; per-layer valid fractions + intersection
  mask-loss reporting in the overlay diagnostics; and a new `zonal.py` + `zonal-score` CLI for the
  sub-basin/tabular scoring branch. Tests: 36 -> 51 passing, 0 skipped; ruff clean.
- Key result: the deliverable pipeline now exposes value readiness, enforces standardized overlay
  inputs, reports mask loss, and supports a zonal scoring path. Step S5 engineering readiness is
  closed; the verdict stays `NO-GO` for real-data overlay pending mentor decisions.
- Next action: keep overlay and interpretation blocked; close IFPM-D01 (modelling unit) and the
  criteria/boundary decisions before any controlled real-data overlay run.

### IFPM-028 Close Pre-Real-Data Engineering Readiness

- Priority: P1
- Task: make the synthetic-tested pipeline safe enough for controlled real-data overlay.
- Status: closed-scoped for engineering readiness; real-data overlay and interpretation remain
  blocked pending mentor decisions on modelling unit, criteria, and final boundary.
- Completion evidence: `ifpm-flood-pipeline` commit `39f6b33` closes all five Step S5 items (durable
  geospatial verification target, finite-value/mask diagnostics, 0-1 overlay-input enforcement,
  per-layer mask-loss reporting, and a zonal scoring branch). Tests run with the `geospatial`
  extra installed: 36 -> 51 passing, 0 skipped (rasterio 1.5.0); `ruff check` + `ruff format` clean.
- Next action: keep overlay and interpretation blocked until IFPM-D01 (modelling unit) and the
  criteria/boundary decisions are closed; the pipeline is now executable for a controlled run.

### IFPM-023 Implement Raster Grid Diagnostics

- Priority: P1
- Task: add checks for CRS, transform, resolution, shape, band count, and NoData.
- Status: done in deliverable code.
- Completion evidence: `ifpm-flood-pipeline` commit `81c14e8` adds raster diagnostics,
  CLI support, and tests.

### IFPM-024 Implement Standardization Rules

- Priority: P1
- Task: start with synthetic rasters before real data.
- Status: done in deliverable code.
- Completion evidence: `ifpm-flood-pipeline` commit `758dd10` adds min-max standardization,
  NoData preservation, diagnostics, CLI support, and tests.

### IFPM-025 Run Synthetic Preprocessing-To-Overlay Smoke Test

- Priority: P2
- Task: run a full synthetic flow through preprocessing and overlay.
- Status: done in deliverable code.
- Completion evidence: `ifpm-flood-pipeline` commit `f21fb77` adds a synthetic
  preprocessing-to-overlay smoke test and output profile regression checks.

### IFPM-026 Prepare Mentor-Facing Next-Step Summary

- Priority: P2
- Task: summarize prototype scope, unresolved decisions, and validation plan.
- Status: done as internal draft.
- Completion evidence:
  `context/docs/mentor-explanation/Mentor_Next_Step_Summary_IFPM_2026-06-10.md`.

## Blocked Or Needs Decision

### IFPM-D01 Final Modelling Unit

- Decision needed: pixel, HydroBASINS/sub-basin, ANA hydrographic unit, or mixed mask.
- Why it matters: controls normalization, aggregation, and comparability.

### IFPM-D06 Upper Mzingwane Boundary Acceptance

- Decision needed: final thesis boundary remains open. For controlled prototype work, V1 /
  `HB_L8_1081528840_full_l7_chain` is accepted with waiver. C1 /
  `HB_L8_1081522660_literature_near` is now only a machine prior. Geoportal named sub-catchment,
  HydroBASINS level 7 candidate, a reviewed HydroBASINS union, or the narrower `~2138 km2`
  literature boundary remain comparison/proxy options.
- Why it matters: the outlet controls the operational catchment. The plausible comparison
  boundaries are not equivalent: HydroBASINS level 7 is about `3700 km2`; Geoportal `Upper
  Mzingwane` is about `7321.5 km2`; the reported but source/geometry-unresolved `~2138 km2`
  reference still needs outlet, area-method, and boundary-geometry tracing.
- Current evidence: HydroBASINS discovery, Geoportal boundary comparison, literature fact-check,
  public source hunt, mentor feedback, the 2026-06-11 candidate outlet first pass, the
  2026-06-12 professional map review, mentor thumbs-up acknowledgement, V1 working boundary
  package, SRTM tile preflight, SRTM raw-tile inventory, and V1 DEM/slope preprocessing completed.
  CHIRPS, overlay, and interpretation remain blocked.

### IFPM-D02 Peru Boundary Rule

- Decision needed: administrative regions, hydrographic units, or clipped hydrological units.
- Why it matters: avoids catchment-versus-region bias.

### IFPM-D03 Validation Evidence Hierarchy

- Decision needed: which evidence can support validation or calibration.
- Why it matters: determines whether outputs are susceptibility, risk, or intervention maps.

### IFPM-D04 AHP Weighting Protocol

- Decision needed: who supplies expert pairwise comparisons and how CR is reviewed. A
  mentor-provided candidate matrix now exists (2026-06-16 slide, CR 0.022) but is slide-labelled
  as an example, so the authorisation step is still open.
- Why it matters: prevents arbitrary weights.

### IFPM-D05 Mining-Data Interpretation Rule

- Decision needed: how to separate concessions, cadastre records, and active disturbance.
- Why it matters: avoids treating mining rights as active mining footprints.

## Backlog

- IFPM-030: add dataset manifest schema for download records.
- IFPM-031: add optional downloader helpers with explicit output directories only.
- IFPM-032: add raster standardization config format.
- IFPM-033: add validation-event ingest design for EM-DAT, DFO, Copernicus EMS, or GloFAS.
- IFPM-034: add sensitivity-analysis utilities for AHP weights.
- IFPM-035: add public-safe technical docs for the minimal pipeline.
- IFPM-036: build a small dashboard or report view after approved sample data exists.
- IFPM-037: add fixed-threshold class configuration for comparison-safe maps.
- IFPM-038: add a first-slice AHP weighting protocol and sensitivity plan.
- IFPM-047: add official mining routes or verified active-disturbance evidence if needed after
  the terrain prototype.

## Verification Gates

Before data download:

- Dataset registry note exists.
- Download preflight checklist is complete.
- Target path is ignored by Git.
- Licence/account constraints are documented.

Before code handoff:

- Tests pass.
- Ruff check and format check pass where applicable.
- Adversarial review findings are triaged.
- Parent workspace boundary check passes.

Before any public release:

- No private context, raw/derived GIS data, credentials, local paths, or unresolved assumptions.
- Public-safe docs do not depend on `../context`, `../data`, or `../outputs`.
- Release package comes from `ifpm-flood-pipeline/`, not root `exports/`.
