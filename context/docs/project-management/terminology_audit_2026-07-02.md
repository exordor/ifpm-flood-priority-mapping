# Terminology Audit Against Mainstream Literature

Date: 2026-07-02

Verified and revised: 2026-07-03

Status: internal audit, now aligned with the active July 18 Zimbabwe-Peru
prototype workflow.

This report checks whether human-facing terms in mentor/boss outputs and figure
captions are standard GIS / flood-susceptibility / MCDA / USLE terms, mentor
terms, or clearly-labelled project-specific terms.

External source comparison was added on 2026-07-03 in `context/docs/glossary.md`.
The glossary now separates externally backed terms, literature-aligned modelling
terms, and project-specific communication terms. It records source support for
disaster-risk terminology, exposure/vulnerability, flood-susceptibility
conditioning factors, CHIRPS rainfall climatology, USLE/RUSLE rainfall erosivity,
raster NoData handling, and AHP pairwise comparison.

The main correction after the first audit was to stop using broad `*_proxy`
names in the active workflow. Current active criteria, manifests, figure labels,
and output filenames now use:

- `flood_conditioning_factors`
- `soil_erosion_factors`
- `land_cover_pressure`
- `mining_pressure`
- `exposure_indicators`
- `rainfall_climatology`

The active gate is `bin/check_active_terminology.py`. It fails if deprecated
terms leak back into active scripts or active output text/files.

## Verification Run

Commands used for the 2026-07-03 recheck:

```bash
.venv/bin/python bin/check_active_terminology.py
find outputs -name '*proxy*' -print | wc -l
rg -n "flood_hazard_proxy|erosion_structure_proxy|road_accessibility_proxy|rainfall_climatology_proxy|river_proximity_proxy|osm_mining_proxy|closeness_to_mining_proxy|distance_to_mining_proxy|rehabilitation_proxy|exposure_mining_proxy|proxy_0_1|Mining-proxy|socioeconomic_exposure|R-invariant|rainfail" context/docs/glossary.md context/docs/project-management/assumptions_log.md context/docs/project-management/terminology_audit_2026-07-02.md
rg -n "flood_hazard_proxy|erosion_structure_proxy|road_accessibility_proxy|rainfall_climatology_proxy|river_proximity_proxy|osm_mining_proxy|closeness_to_mining_proxy|distance_to_mining_proxy|rehabilitation_proxy|exposure_mining_proxy|proxy_0_1|Mining-proxy|socioeconomic_exposure|R-invariant|rainfail" bin context/configs outputs -g '*.py' -g '*.csv' -g '*.md' -g '*.txt' | rg -v 'bin/check_active_terminology.py'
```

Current result:

- active terminology gate: passed
- active `outputs/` filenames containing `proxy`: 0
- `glossary.md`, `assumptions_log.md`, and the current comparison outputs have
  been updated to the current terms
- `glossary.md` now includes a source-backed terminology table and source list
- active scripts, configs, and active output text/files are clean under
  `bin/check_active_terminology.py`
- a broad historical scan still finds old terms in archived autonomous
  prototypes, R-factor investigation scripts, deprecated USLE outputs, and
  historical task-board entries; those are not current naming authority

## Severity Key

- **P1** = invented term presented as standard, or standard term misused.
- **P2** = project-specific but acceptable if defined clearly.
- **P3** = internal-only or archival; no immediate action unless reused.

## P1 Findings

### P1-1. `flood_hazard_proxy` misused the standard word "hazard"

Original issue:

`flood_hazard_proxy` implied a flood hazard product, but the layer was actually
terrain-derived wetness/drainage evidence. A true flood hazard map normally
requires flood extent, depth/velocity, probability or return period. This project
does not have that evidence in the prototype outputs.

Current status: **fixed in the active workflow**.

Current active name:

- internal key: `flood_conditioning_factors`
- human label: "Flood conditioning factors"
- source description: TWI high-wetness + drainage proximity
- limitation: not hydraulic inundation depth and not a final flood-hazard map

Remaining risk:

Older archival docs may still discuss the old mistake. They must not be copied
into mentor/boss material.

### P1-2. `R-invariant` sounded like a field-standard erosion term

Original issue:

`R-invariant` described a real idea, but the term itself is not a mainstream
USLE/RUSLE term. The clearer wording is:

> K x LS x C erosion source structure; rainfall erosivity not applied.

Current status: **fixed in active workflow text and output tables**.

Allowed wording:

- "K x LS x C erosion source structure"
- "before applying rainfall erosivity"
- "not final soil-loss rate"

Avoid in mentor/boss/thesis-facing text:

- `R-invariant`
- "rainfall-invariant"

Remaining risk:

Some older R-factor investigation notes still use `R-invariant` as an internal
shorthand. Treat those as archival technical notes, not reusable writing.

## P2 Findings

### P2-0. Source-backed status

Current status: **partly source-backed, partly project-specific by design**.

The following terms are externally backed:

- disaster risk / flood risk, exposure, and vulnerability: UNDRR, IPCC, and
  PreventionWeb risk terminology
- rainfall erosivity / R-factor and USLE/RUSLE component factors: FAO and ESDAC
- rainfall climatology / CHIRPS resolution caveat: Climate Hazards Center
- NoData: GDAL and Rasterio raster documentation
- AHP pairwise comparison: Saaty's AHP literature

The following terms remain project-specific communication terms and must be
defined on first use:

- dominant priority driver
- contribution share
- stable hotspot
- priority intervention map / PIM

These project-specific terms are allowed for mentor/boss explanation but must
not be presented as standard method names.

### P2-1. "Dominant priority driver" is project-specific but useful

Current status: **allowed if defined on first use**.

Recommended definition:

> Each pixel is coloured by the criterion contributing the largest share of the
> prototype priority score.

This is acceptable for mentor/boss reporting because it answers "why is this
area high?" It should not be presented as a standard MCDA output name.

### P2-2. "Contribution share" is project-specific

Current status: **allowed if defined on first use**.

Recommended definition:

> Contribution share = one criterion's weighted value divided by the pixel's
> total weighted score.

Use only when showing driver explanations, not as a standalone scientific term.

### P2-3. "Stable hotspot" needs an explicit threshold definition

Current status: **allowed if defined**.

Current project definition:

> Stable hotspot = a cell that remains in the top-20% priority set across all
> tested weighting scenarios.

Do not use "stable" without saying whether stability is across weights, time,
or modelling assumptions.

### P2-4. "Coarse-to-reference-grid" is governance language

Current status: **allowed internally; use standard wording externally**.

Preferred external wording:

> CHIRPS rainfall was bilinearly resampled to the 30 m reference grid for
> scenario comparison. Its effective resolution remains about 5 km; it is not
> native 30 m rainfall evidence.

### P2-5. "Priority Intervention Map" / `PIM`

Current status: mentor's own project label, not a mainstream method name.

Use it only after defining it as a project-specific index. For broader academic
writing, "priority map" or "intervention-priority index" is safer.

### P2-6. `claim_level`

Current status: internal QA metadata, not a scientific term.

Translate in human-facing text:

- `diagnostic_only` -> "diagnostic check"
- `provisional` -> "working result, not yet validated"
- `sensitivity_scenario` -> "what-if scenario"
- `mentor_review_ready` -> "ready for review"
- `final_claim` -> use only after validation and explicit approval

## Cross-File Consistency Check

### Resolved

1. `flood_hazard_proxy` vs "Flood conditioning factors"
   - resolved to `flood_conditioning_factors`

2. `erosion_structure_proxy` vs "Soil erosion factors"
   - resolved to `soil_erosion_factors`

3. `road_accessibility_proxy` / `socioeconomic_exposure` vs "Exposure indicators"
   - active Zimbabwe and PE1 comparison now use `exposure_indicators`

4. `rainfall_climatology_proxy` vs `rainfall_climatology`
   - resolved to `rainfall_climatology`

5. Mining `proxy` filenames
   - active mining evidence now uses `mining_activity_indicator` or
     `osm_mining_indicator` naming where relevant

### Still Archival

Older project-management and R-factor investigation notes can still contain old
terms because they record historical experiments. They are not current naming
authority. If one is reused for a mentor message, figure caption, thesis section,
or report, translate it through `context/docs/glossary.md` first.

## Current Approved Human Labels

Use these labels in figures, captions, and mentor messages:

| Criterion family | Human-facing label |
|---|---|
| flood | Flood conditioning factors |
| sediment / erosion | Soil erosion factors |
| land cover | Land use/land cover |
| mining | Mining / ASM activity |
| exposure | Exposure indicators |
| rainfall | Rainfall |

Avoid:

- "flood hazard" unless the output contains hazard evidence such as inundation
  depth, extent, velocity, probability, or return period
- "flood risk map" unless validated impact/probability evidence exists
- "final intervention-priority map" unless weights, validation, and decision
  authority are explicitly accepted

## Active Prevention Rule

Before sending any mentor/boss-facing package, run:

```bash
.venv/bin/python bin/check_active_terminology.py
```

This check is intentionally stricter than ordinary internal notes. It blocks
deprecated active-workflow terms and generic `proxy` wording in current scripts,
configs, and active output text.

---

## Execution Appendix: Dead/Alive Verdict And Rewrite List

Date: 2026-07-02 (added after a live-vs-dead dependency check of every file
flagged by `outputs/zimbabwe_peru_prototype_comparison/full_project_terminology_check.csv`).

### Headline numbers from the full check

The full check reports 470 hits total across the whole repo:

- `violation`: **0** — no deprecated term in active/mentor-facing material
- `needs_review`: **226** — but see the reclassification below
- `allowed_reference`: 113 — glossary/audit text quoting deprecated terms on purpose
- `archival_reference`: 131 — historical/superseded records under `_archive/`

### Critical reclassification of the 226 needs_review hits

The check flags every occurrence of the substring `proxy`. Most of these are
**correct English usage of "proxy"** (代理变量), which is a standard term in
remote sensing, ecology, and spatial modelling. "Population count is an exposure
proxy" is not a terminology error. After manual classification:

- **185 of 226 are benign `proxy` English usage across 58 files** — no action.
- **41 hits are real** (snake_case identifier leaks or the coined `R-invariant`),
  across **15 files**.

### Live-vs-dead verdict for the 15 real-hit files

Each file was checked three ways: (1) DAG dependency — does any live script
consume its outputs; (2) does the current live pipeline (V1 v0.4 / PE1 / 7-18
board) reference it; (3) does the task board list it as current evidence.

| File | Verdict | Why | Action |
|---|---|---|---|
| `bin/factors/derive_peru_pilot_usle_soil_loss.py` | **LIVE** | IFPM-077 current evidence; output feeds PE1 sediment criterion | **Rewrite**: 5× `R-invariant` → standard wording, rerun |
| `bin/factors/derive_v2_usle_soil_loss.py` | **dead** | V2 R-factor work paused (IFPM-074, awaits mentor); no consumer | Do not rewrite now; handle when V2 resumes |
| `bin/visualize/plot_v2_rfactor_comparison_board.py` | **dead** | V2 R-factor comparison, V2 paused | Same as above |
| `bin/criteria/build_era5_rfactor_raster.py` | **dead** | ERA5 R-factor exploration; R-factor route moved to Hurni/Arnoldus | Same |
| `bin/criteria/build_v1_autonomous_criteria_stack.py` | **superseded** | v0.1 prototype, replaced by v0.2 criteria_stack | Archive, do not rewrite |
| `bin/scenarios/run_v1_autonomous_priority_scenarios.py` | **superseded** | v0.1 scenario, replaced | Archive |
| `bin/visualize/plot_v1_autonomous_prototype_board.py` | **superseded** | v0.1 board, replaced | Archive |
| `context/docs/project-management/boundary_v1_criteria_stack_v0_2_2026-06-29.md` | **LIVE record** | v0.2 is the current criteria stack | **Rewrite**: 3× snake_case leak |
| `context/docs/project-management/v1_multicriteria_evidence_package_2026-06-13.md` | **half-dead** | 6-13 evidence package, superseded by 6-29 v0.2 + 7-1 mentor pack | Archive |
| `context/docs/project-management/v1_full_methodology_evidence_sweep_2026-06-13.md` | **half-dead** | 6-13 sweep, superseded | Archive |
| `outputs/.../usle_soil_loss_diagnostics.json` | auto-product | generated by `derive_peru_pilot_usle_soil_loss.py` | Auto-fixed when its producer is rerun |
| `outputs/.../rfactor_method_exploration_diagnostics.json` | auto-product | generated | Auto-fixed or stays as historical |
| `outputs/boundary_v1/priority_scenarios_v0_2/handoff.md` | **LIVE record** | v0.2 priority handoff | **Rewrite**: 1× `R-invariant` |
| `context/docs/data-management/registry/geofabrik_osm_peru_pilot.md` | **LIVE** | active data registry | Low priority: 1× snake_case, fix on next registry touch |
| `context/docs/project-management/task_progress_board.md` | **living doc** | continuously updated | Fix opportunistically on next natural edit, no dedicated task |

### Rewrite list (the actual answer to "what must be rewritten")

Only **3 files** need active rewriting now. Everything else is dead, superseded,
auto-generated, or a living document to fix opportunistically.

1. **`bin/factors/derive_peru_pilot_usle_soil_loss.py`** — 5× `R-invariant`.
   Replace with "the erosion source structure (K × LS × C × P), which is
   independent of the chosen R-factor". Rerun to regenerate its JSON diagnostic.
2. **`context/docs/project-management/boundary_v1_criteria_stack_v0_2_2026-06-29.md`**
   — 3× snake_case leaks (`socioeconomic_exposure`, `erosion_structure_proxy`,
   `road_accessibility_proxy`) in mentor-visible description text. Replace with
   the glossary human labels.
3. **`outputs/boundary_v1/priority_scenarios_v0_2/handoff.md`** — 1× `R-invariant`.
   Replace with the standard wording.

### Archival candidates (would cut future check noise)

Moving these to `_archive/` would reclassify their hits from `needs_review` to
`archival_reference`, making the terminology check reflect real live problems:

- `bin/criteria/build_v1_autonomous_criteria_stack.py` + `run_v1_autonomous_priority_scenarios.py`
  + `plot_v1_autonomous_prototype_board.py` (the v0.1 autonomous set)
- `context/docs/project-management/v1_multicriteria_evidence_package_2026-06-13.md`
- `context/docs/project-management/v1_full_methodology_evidence_sweep_2026-06-13.md`

### Decision recorded

Per the 2026-07-02 session: **do not edit code now**. The live/dead verdict and
the 3-file rewrite list above are recorded here so the work can be picked up by
priority later. Archival of the v0.1 + 6-13 set is the highest-leverage
next step (it makes the terminology check honest), followed by the 3-file
rewrite.

### Execution (2026-07-03)

The decision above was executed the same day. Results:

**Archived (moved to `_archive/`, hits reclassified to `archival_reference`):**
- `bin/criteria/build_v1_autonomous_criteria_stack.py`
- `bin/scenarios/run_v1_autonomous_priority_scenarios.py`
- `bin/visualize/plot_v1_autonomous_prototype_board.py`
- `context/docs/project-management/v1_multicriteria_evidence_package_2026-06-13.md`
- `context/docs/project-management/v1_full_methodology_evidence_sweep_2026-06-13.md`
- v0.1 outputs (`outputs/v1_autonomous_prototype_v0_1/`) **kept in place** — still
  read as baseline by the live `prepare_boundary_v1_criteria_stack_v0_2_inventory.py`.
- task board evidence paths updated to point at the new archive locations.

**Rewritten (live files):**
- `bin/factors/derive_peru_pilot_usle_soil_loss.py` — 5× `R-invariant` replaced
  with "does not depend on the chosen R value" / "independent of the
  rainfall-erosivity factor R". Script reran; the regenerated
  `usle_soil_loss_diagnostics.json` is also clean. Stats unchanged (logic intact).
- `outputs/boundary_v1/priority_scenarios_v0_2/handoff.md` — 1× `R-invariant`
  replaced with the same standard wording.
- `context/docs/project-management/boundary_v1_criteria_stack_v0_2_2026-06-29.md`
  — **not rewritten**. On closer reading the 3 snake_case hits are legitimate
  identifier references in an internal engineering note ("criterion is now named
  X", "rename road-only evidence to X"), which the glossary and STYLE.md
  explicitly permit under `project-management/`. The earlier "needs rewrite"
  verdict was over-strict; corrected here.

**Terminology check delta:**
- `needs_review`: 226 → **193** (−33)
- `archival_reference`: 131 → **157** (+26, from the archival moves)
- `violation`: 0 → **0** (still clean)
- Remaining 16 live `R-invariant` hits are all in the **dead V2 R-factor set**
  (`derive_v2_usle_soil_loss.py`, `plot_v2_rfactor_comparison_board.py`,
  `build_era5_rfactor_raster.py`), plus 3 in the living `task_progress_board.md`
  and 1 in a historical exploration JSON. **Zero in active production code.**
  These are deferred until V2 R-factor work resumes (IFPM-074).
