# IFPM Glossary

Status: active shared term reference. Use this when writing any mentor-facing message,
briefing, or figure caption so internal code names do not leak into human communication.

## Rule

This file is the single source of truth for **what to call things when writing for the mentor
or any human reader**. Internal code names (`V1`, `boundary_v1`, `HB_L8_*`, `HYBAS_ID`,
`Gate G*`, `IFPM-*`, `diagnostic_only`) stay inside engineering notes under
`project-management/` and `data-management/`. They do not appear in `mentor-explanation/`
documents, figure captions, or anything the mentor reads.

If a concept has both an internal name and a human name below, use the human name in
mentor-facing text. Internal names appear in this file only so the author can map them.

---

## 1. The Study Area: One Name Outside

The single biggest source of confusion is that one piece of ground has eight different names
in the workspace. Outside the workspace, use **one** name.

| Context | Name to use |
|---|---|
| **Mentor-facing text (always)** | the Upper Mzingwane catchment (our V1 prototype) |
| Internal engineering notes | `V1` or `boundary_v1` |
| HydroBASINS database id (internal only) | `HYBAS_ID=1071528840` / `HB_L8_1081528840` |

**Key facts to keep consistent:**

- The V1 prototype catchment area is about `3689.5 km2`.
- It is a **prototype working boundary, not the final thesis boundary**.
- It contains Mzingwane Dam and Esigodini; it excludes Gwanda.
- The often-cited literature reference is `~2138 km2` for "Upper Mzingwane", but no checked
  source supplied a reusable boundary polygon for that value, so it is unresolved.

When the mentor sees any of these, they should all read as the same place. Never write
`HB_L8_1081528840` or `HYBAS_ID=...` in a mentor document; write "the V1 prototype catchment".

---

## 2. Criteria Names: v0.1 vs v0.2 (Old and New Must Not Coexist In Text)

The criteria were renamed in v0.2 to describe what the data actually measure. When writing
about the current state, use the **v0.2 (new) names**. The old names appear here only so old
references can be translated.

| v0.1 name (old, deprecated) | v0.2 name (current) | What it actually is | In core overlay? |
|---|---|---|---|
| `sediment_structure` | `erosion_structure_proxy` | R-invariant erosion *source structure* (K x LS x C); not sediment risk, magnitude needs an R value | yes |
| `landuse_asm_pressure` | split into `land_cover_pressure` + `mining_pressure` | land-cover pressure and mining pressure are now **separate** criteria, not averaged together | both yes |
| `environmental_sensitivity` | `river_proximity_proxy` | distance-to-river proxy; **demoted out of the core overlay** (too thin to be an environmental claim) | no |
| `socioeconomic_exposure` | `road_accessibility_proxy` | distance-to-road proxy; **demoted out of the core overlay** (not true exposure) | no |
| `flood_hydrology` | `flood_hazard_proxy` | TWI high-wetness + drainage proximity; terrain flood-susceptibility proxy | yes |

Current v0.2 **core** criteria (the five that enter a weighted overlay): `flood_hazard_proxy`,
`erosion_structure_proxy`, `land_cover_pressure`, `mining_pressure`, plus rainfall when added.

Never write "sediment_structure" in a mentor document as if it means sediment loss — it does
not. Use "erosion structure proxy" and note that magnitude depends on the R-factor.

---

## 3. R-Factor Terms (The Most Technical Area)

| Term | Meaning | Mentor-friendly wording |
|---|---|---|
| R-factor / rainfall erosivity | the rainfall energy term in USLE/RUSLE that drives erosion | "rainfall erosivity (the R-factor)" |
| `R-invariant` | the spatial structure that does not depend on the R value (K x LS x C) | "the erosion pattern that stays the same no matter which R value we pick" |
| MFI | Modified Fournier Index, a monthly-rainfall summary used to estimate R | "a standard rainfall-intensity index" |
| EI30 / I30 | storm kinetic energy times 30-minute intensity; the true R definition | "storm-level rainfall energy" |
| LOW R-family | R ~ 240-320 (Hurni, Epworth); matches ERA5 hourly lower-bound check | "the lower R estimate" |
| HIGH R-family | R ~ 1380-3719 (Renard-Freimund, Arnoldus, Elwell-Stocking) | "the higher R estimate" |
| Provisional R | R = 238.6, the current working default (LOW family, Arnoldus 1980 power-law, V1 zonal mean) | "our working R value, treated as provisional" |

**Two facts to state plainly when R comes up:**

- There are two incompatible R-families about 6x apart; this is an open method choice, not a
  bug. We are using the lower family as the working default and the higher family as a
  sensitivity check.
- The earlier V1 R/A outputs are deprecated (a wrong formula produced a false pattern). Do not
  cite old R or soil-loss numbers.

---

## 4. Map Type Words: Do Not Mix These Up

These four words mean different things and the project's credibility depends on keeping them
straight. The project currently produces **only the first two**, never a validated risk map.

| Word | Means | Does the project have this? |
|---|---|---|
| **susceptibility map** | where flooding/erosion is *likely* based on terrain and proxies, no probability | yes (what the prototype is) |
| **priority / suitability map** | relative ranking of where intervention matters, under chosen weights | yes (with documented AHP weights) |
| **flood-risk map** | validated probability/magnitude of flood impact | **no** — no validation data |
| **intervention-priority map** | authoritative plan of where to act | **no** — needs validation + official weights |

When unsure, default to "susceptibility" or "priority". Never call an output a "flood-risk
map" unless it has been validated. The project title says "flood risk", but every actual output
so far is susceptibility or priority — say so.

---

## 5. Internal Numbering Systems (For Internal Use Only)

The workspace has three overlapping numbering systems. They never appear in mentor text.

### Gate G1-G7 (engineering readiness gates)

These are internal process gates in `real_data_execution_preflight_gate.md`.

| Gate | Plain meaning |
|---|---|
| Gate G1 | the boundary must be accepted before download/overlay |
| Gate G2 | the modelling unit (pixel vs sub-basin) must be chosen |
| Gate G3 | the rainfall time window and product must be chosen |
| Gate G4 | dataset-specific download preflight must be closed |
| Gate G5 | a download authorization record must be written |
| Gate G6 | execution rules after download |
| Gate G7 | pipeline engineering readiness (tests, grid checks) |

### IFPM-D0X (open mentor decisions)

| ID | Plain meaning |
|---|---|
| IFPM-D01 | final modelling unit decision |
| IFPM-D02 | Peru boundary rule |
| IFPM-D03 | validation evidence hierarchy |
| IFPM-D04 | AHP weighting protocol |
| IFPM-D05 | mining-data interpretation rule |
| IFPM-D06 | Upper Mzingwane boundary acceptance |

Note: **Gate G2 and IFPM-D01 are the same decision** (modelling unit). **Gate G1 and IFPM-D06
overlap** (boundary). When writing for the mentor, name the decision, not the gate.

### IFPM-0XX (task tracking)

These are task-board entries in `task_progress_board.md`. They never appear in mentor text.

### Output claim levels (status tags)

Internal status tags from `execution_status_policy.md`: `diagnostic_only`, `provisional`,
`sensitivity_scenario`, `mentor_review_ready`, `final_claim`. These label how confident an
output is. Do not paste the tag into mentor text; translate it (e.g. `provisional` → "working
result, defensible but not yet validated").

---

## 6. Quick Translation Table (Internal Code -> Mentor Words)

| If you find this in a note | Write this to the mentor |
|---|---|
| `V1` / `boundary_v1` | "the V1 prototype catchment" or "the Upper Mzingwane prototype" |
| `HB_L8_*` / `HYBAS_ID=*` | "the prototype catchment" (with its area if needed) |
| `Gate G2` | "the modelling-unit decision" |
| `Gate G1` / `IFPM-D06` | "the boundary decision" |
| `IFPM-0XX` | (delete — it is an internal task id) |
| `diagnostic_only` | "an internal diagnostic, not a result" |
| `provisional` | "a working result, defensible but not yet validated" |
| `sensitivity_scenario` | "a what-if check under different assumptions" |
| `R-invariant` | "the erosion pattern that does not depend on the R value" |
| `sediment_structure` (old) | "erosion structure proxy" |
| `landuse_asm_pressure` (old) | "land-cover pressure and mining pressure" |
