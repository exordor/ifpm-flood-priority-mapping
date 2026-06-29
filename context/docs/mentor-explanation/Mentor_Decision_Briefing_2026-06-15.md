# Mentor Decision Briefing: Eight Key Decisions

Date: 2026-06-15

Status: internal mentor-facing briefing. Compresses the ~35 individual questions scattered across
the P1 and P2 risk decision packages into eight dependency-ordered key decisions, grouped into
three batches. This briefing does not authorize any download, boundary acceptance, AHP overlay,
flood-risk interpretation, or intervention-priority interpretation.

## Scope Note (Added 2026-06-15)

The HiWi is the **data processor**, not the thesis author. The decisions below are framed for the
mentor because they are thesis/claim-level calls: what the deliverable must achieve, what counts
as validation, what weights are authoritative, what the final boundary is, whether Peru is
required. None of them block the HiWi's data-processing work, which proceeds on already-authorized
data with documented defaults.

The HiWi needs answers to these decisions only to know how to **label** outputs (diagnostic vs
interpretable) and what additional data to request access to. Data production itself does not wait
for these answers.

## How To Use This Briefing

Present the three batches in order. Each batch has a clear purpose:

- **Batch A (decisions 1-3)** defines whether the project is viable and what the mentor
  contributes. These must be answered first; everything else depends on them.
- **Batch B (decisions 4-6)** locks the methodology so engineering can proceed. Most are
  confirmations of HiWi recommendations, so they should be fast.
- **Batch C (decisions 7-8)** is conditional refinement, needed only if Batch A triggers a
  fallback or if validation is required.

If the mentor cannot answer all of Batch A in one meeting, **data processing still proceeds** on
already-authorized data with documented defaults (hydrology derivatives, LS/R/K/C factors,
diagnostic overlays). What waits is **interpretation and any new data access that needs mentor
introduction** — not data production. Do not infer answers; record them as open and label
affected outputs as diagnostic-only until the mentor decides. Each decision below states what an
answer unblocks and what the fallback is if the answer is negative.

For each decision, the HiWi recommendation is marked **(recommended)** where it exists. The
mentor only needs to confirm or override.

---

## Batch A: Viability And Mentor Contribution

### Decision 1: Minimum Viable Thesis (Mentor's Call; Does Not Block Data Processing)

> If all external data access fails, is a **terrain-only, Zimbabwe-only, no-independent-validation
> priority/suitability map** acceptable as the thesis floor? Or are validation, mining data, and
> the Peru comparison all hard requirements?

- This is a **thesis-scope decision for the mentor**, not a blocker for the HiWi. The HiWi
  produces data products regardless of this answer; the answer only determines whether those
  products are sufficient as a thesis or must be supplemented.
- Unblocks: the mentor's own fallback strategy; defines what "done" means for the thesis.
- If **suitability map is acceptable**: most P1/P2 risks become scope reductions, not blockers.
- If **all are hard requirements**: the project needs mentor-mediated data access (Decision 2)
  and a longer timeline; some requirements may be infeasible.
- This is the single highest-leverage question for the mentor. It replaces P1-Q (validation
  required?), R1.2-Q4 (mining demotion acceptable?), R2.1-Q5 (sediment demotion acceptable?),
  and R2.3-Q1 (Peru required?).

### Decision 2: Data The Mentor Can Provide Or Unlock

> Do you, your collaborators, or your institutional contacts hold any of the following for the
> Upper Mzingwane / Matabeleland South area:
> (a) the catchment boundary polygon;
> (b) historical flood-extent, water-level, or impact records;
> (c) ASM site locations, mining-concession boundaries, or EMA rehabilitation records;
> (d) published sediment-yield, turbidity, or flood-event field data?
> Can you introduce ZINWA, Zimbabwe Geological Survey, MMMD, or EMA contacts?

- Unblocks: R1.1 (validation), R1.2 (mining), R2.5 (boundary) substantively.
- This replaces eight individual "do you hold X" questions across the P1/P2 packages.
- If **yes to any**: that risk moves from "blocked" to "processable".
- If **no to all**: the relevant fallbacks trigger (see Decision 1); the project proceeds on
  public data only.

### Decision 3: AHP Expert Weights Commitment

> Can you supply, or nominate domain experts to supply, the **pairwise comparison matrix** for
> the criteria hierarchy within a defined window? Or will expert weights not be available during
> the project?

- Unblocks: R1.3 (AHP weights); determines whether any real-data overlay can be interpreted.
- If **yes**: I have a pairwise-comparison template ready; the project can then produce an
  interpretable priority map.
- If **no**: all real-data outputs stay labelled as workflow diagnostics with synthetic weights;
  no priority map is interpretable. This is the hard boundary on what the project can claim.

---

## Batch B: Methodology Lock (Mostly Confirmations)

### Decision 4: Final Boundary

> Should **the V1 prototype catchment (~3689.5 km²)** be promoted from a working prototype
> boundary to the accepted thesis boundary? **(recommended)** If not, when can you provide the
> polygon?

- Unblocks: the boundary decision; area-dependent reporting; the sub-basin modelling-unit
  upgrade path.
- Default if mentor agrees: the V1 catchment accepted, with the area discrepancy vs the
  literature `~2138 km²` documented as a limitation.
- Alternatives if mentor objects: the Geoportal named sub-catchment (~7321.5 km²), or wait for
  a mentor-supplied polygon.
- Replaces R2.5-Q2/Q3/Q4.

### Decision 5: Modelling Unit

> For the first prototype, use **terrain-only raster screening, with rainfall as context (not in
> the score)**. **(recommended)** Acceptable?

- Unblocks: the modelling-unit decision; the first interpretable real-data run path.
- Rationale: the V1 DEM is ready; avoids a false-precision trap from treating coarse rainfall as
  30 m detail; matches the existing pipeline; produces the fastest defensible result.
- Sub-basin aggregation (rainfall in the score) is the natural upgrade once the final boundary
  and a sub-basin layer are accepted.
- Replaces R2.4-Q1/Q2/Q3.

### Decision 6: Methodology Defaults Bundle

> Are the following HiWi-recommended defaults acceptable? If any must change, name it; otherwise
> this confirms all at once.
>
> - **(a) Hydrology**: sink-fill-to-spill; D8 flow direction; V1 edge treated as outlet.
> - **(b) USLE factors**: R = modified Fournier index from CHIRPS; K = SoilGrids 250m via a
>   standard pedotransfer function; C = WorldCover lookup table (Sentinel-2 upgrade as future
>   work); P = 1 (documented assumption).
> - **(c) AHP protocol**: CR threshold = 0.1; sensitivity = +/-20% per weight plus
>   leave-one-criterion-out; single-expert matrix unless mentor nominates a panel.
> - **(d) Channel threshold**: deferred to a threshold-sensitivity figure the mentor reviews
>   before a single value is chosen.

- Unblocks: R2.2 (hydrology engineering), R2.1 (sediment factor chain), R1.3 protocol details,
  in one confirmation.
- This bundle replaces twelve individual method-choice questions. Each item is a HiWi
  recommendation drawn from standard practice; the mentor only needs to flag overrides.
- Replaces R2.2-Q1/Q2/Q3, R2.1-Q1/Q2/Q3/Q4, R1.3-Q3/Q4/Q5.

---

## Batch C: Conditional Refinement

### Decision 7: Validation Tier (Only If Decision 1 Requires Validation)

> If independent validation is a hard requirement, which tier should the HiWi pursue first?
> - **Tier A**: EM-DAT + GloFAS (public, low V1 spatial precision, fastest).
> - **Tier B**: Sentinel-1 SAR flood-extent processing (public, needs engineering + a confirmed
>   event date).
> - **Tier C**: ZINWA / DCP local records (highest value, needs mentor introduction).
> **(recommended: Tier A first as context, Tier C in parallel if access opens)**

- Only needed if Decision 1 answers "validation is required".
- Replaces R1.1-Q4.

### Decision 8: Criteria Hierarchy (Only If Decisions 1/2 Trigger Fallbacks)

> If mining and/or sediment data cannot be obtained, is a **reduced-criteria hierarchy**
> acceptable? The reduced set would drop Mining Location, Rehabilitation Potential, and/or
> Sediment Risk from scored AHP criteria to qualitative/context evidence, leaving a
> Flood-Hazard / Terrain / Land-Use / Environmental / Socioeconomic priority map.

- Only needed if Decision 2 returns "no mining/sediment data".
- Tied to Decision 1: if the suitability-map floor is accepted, reduced criteria is consistent.
- Replaces R1.3-Q2 (hierarchy confirmation) and the demotion fallbacks in R1.2/R2.1.

---

## What Each Batch Unblocks

| Batch | If answered | Unblocks |
|---|---|---|
| A (1-3) | positively | The full path to an interpretable V1 deliverable |
| A (1-3) | negatively / "no data" | Triggers documented fallbacks; project shrinks to a defined floor |
| B (4-6) | confirmed | Engineering: hydrology derivatives, USLE chain, first real-data run |
| C (7-8) | as needed | Validation path; final criteria hierarchy |

## Fallback Mapping (If Mentor Says "No" Or "I Don't Have It")

| Decision | Negative answer | Fallback (already documented) |
|---|---|---|
| 1 | "all hard requirements" | Project is data-access-dependent; timeline risk; scope negotiation needed |
| 1 | "suitability map OK" | R1.1, R1.2, R2.1, R2.3 fallbacks active; reduced deliverable proceeds |
| 2 | "no data held" | Public-data-only path; Tier A context; mining/sediment demoted |
| 3 | "no expert weights" | All outputs labelled synthetic-weight diagnostics; no interpretable priority map |
| 4 | "V1 not acceptable" | Wait for polygon; or use Geoportal boundary; timeline risk |
| 5 | "Branch 1 not acceptable" | Use Branch 3 (mixed); Branch 2 needs more prerequisites |
| 6 | specific override | Revise only the flagged item; rest of bundle stands |

## What Was Compressed Out And Why

The following were folded into the eight decisions above because they are HiWi recommendations
needing only confirmation, not independent mentor judgement:

- CR threshold (0.1 is standard) -> Decision 6c.
- Sensitivity scenarios (+/-20% is standard) -> Decision 6c.
- R-factor / K-factor / C-factor / P-factor formula choices -> Decision 6b.
- Hydro-conditioning algorithm choices -> Decision 6a.
- Channel threshold value -> Decision 6d (deferred to a figure).
- Peru boundary option specifics -> folded into Decision 1 (Peru required?) and deferred until
  Zimbabwe methodology locks.
- Sub-basin layer choice for Branch 2 -> deferred; only relevant if Decision 5 selects Branch 2.

If the mentor wants to discuss any folded item in detail, I have the full per-factor questions
ready and can bring them up individually.

