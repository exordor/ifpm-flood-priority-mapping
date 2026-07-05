# July 18 Deliverable Scope

Date: 2026-07-02

## Why this note exists

A 2026-07-02 direction-setting session found that the project's "next step" was
lost: the task board's In-Progress items all had vague next actions ("decide
whether..."), while the last five commits were engineering-only `bin/` refactors
with no scientific value. The session diagnosed the root cause and locked the
scope for the 7/18 mentor trip deliverable.

## Diagnosis (why the work felt stuck)

The bilateral comparison the mentor wants already existed at ~80% completion,
but it was buried in `outputs/` and never entered the task board's next steps.
Work drifted to engineering refactoring because the real scientific direction
was invisible.

Three mentor/boss-facing artifacts already exist and are individually sound, but
they are **scattered across two output directories** and each is missing one
piece:

| artifact | location | what it has | what it lacks |
|---|---|---|---|
| bilateral comparison board | `outputs/zimbabwe_peru_prototype_comparison/` | priority_mean, top-20% hotspot, summary CSV, mentor message draft | no dominant-criterion (pixel-colouring) panel — the one thing the mentor explicitly asked for |
| dominant-criterion pixel map | `outputs/mentor_boss_priority_explanation/` | per-pixel winning criterion, contribution shares | claim level not on figure face; takeaway is a question not a statement; not in the comparison pack |
| boss process figure | `outputs/mentor_boss_priority_explanation/data_analysis_process_for_boss.pdf` | 6-step flow with claim level | no goal header; does not show this is a two-country comparison |

## Mentor signal (2026-07-02 Teams message)

The mentor independently asked for exactly what is already half-built:

1. **Zimbabwe ASM**: confirmed artisanal/scattered, no official locations; she
   will ask the Zimbabwe contact at the conference. This is structural, not a
   data-collection failure on our side.
2. **Pixel colouring for priority criteria** — she asked for this in her own
   words. We already have it; it just is not in the comparison pack.
3. **A short boss presentation of the data-analysis process** — already built;
   needs a goal header and a bilateral label.

She also floated a contingency: if Zimbabwe ASM data is not obtainable, she may
switch the Zimbabwe site to Voi (Kenya), her home country, where she has more
control. This is a potential boundary change, recorded in `assumptions_log.md`,
not a current action.

## Deliverable scope (locked for 7/18)

Two audiences, one preparation cycle. Built entirely from existing data and
existing scripts. No new criteria, no new downloads, no final claims.

Implementation update 2026-07-03: the integrated comparison pack has been
generated under `outputs/zimbabwe_peru_prototype_comparison/`. The new main
board uses a true 2x2 map layout, includes dominant-criterion pixel colouring,
top-20% hotspot frequency, a plain claim-level note on the figure face, a short
caption, and a short Teams draft. The boss process figure is also copied into
the same comparison pack so the mentor/boss materials are no longer split across
two output directories.

### Deliverable 1 — Mentor comparison pack (primary)

A single integrated main figure that carries the mentor's three asks at once:
bilateral comparison + per-pixel priority-criterion colouring + a clear "why".
Four panels: Zimbabwe dominant criterion, Peru dominant criterion, Zimbabwe
top-20% hotspot frequency, Peru top-20% hotspot frequency. One-sentence takeaway
across the top. Claim level on the figure face, not only in the caption.

Plus an updated mentor message that states the pixel-colouring map is ready and
records the Voi contingency.

### Deliverable 2 — Boss short process figure (secondary)

The existing 6-step process figure with a goal header ("identify the flood-risk
driver criteria in two mountain catchments") and a bilateral label. Kept short.

### Out of scope for 7/18

- No new Zimbabwe mining work (waits on the mentor's conference ask).
- No Voi site switch (a recorded contingency only).
- No final flood-risk claim, no final Zimbabwe-Peru comparison, no weight
  authorisation (all still gated).
- No broad `bin/` refactoring as the primary activity.

## QA criteria (Report-Friendly Figure Rule)

Each figure must pass:

- a non-participant identifies study area, main result, and key driver within
  30 seconds;
- claim level stated on the figure face in plain language;
- takeaway is a statement, not a question;
- legends/colourbars/captions do not hide evidence;
- criterion names are plain, not internal codes.

## Lineage

Built from:
- `outputs/boundary_v1/rainfall_exposure_v0_4/` (Zimbabwe priority)
- `outputs/srtm_1arcsec_peru_pilot/priority_scenarios/` (Peru priority)
- `outputs/mentor_boss_priority_explanation/{zimbabwe,peru}/dominant_criterion_code.tif`
- `bin/visualize/plot_zimbabwe_peru_prototype_comparison.py`
- `bin/visualize/plot_mentor_boss_priority_explanation_package.py`
- `bin/visualize/plot_july18_integrated_priority_board.py`

All inputs are existing `sensitivity_scenario` / `engineering_pilot` outputs.
No download, no overlay re-run, no claim promotion.
