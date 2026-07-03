# Project Objective Calibration

Date: 2026-07-02

## Why this note exists

A 2026-07-02 review of the project's original goal surfaced an ambiguity: the
mentor gave a broad methodology picture at the project start (2026-05 / first
commit 2026-06-02), then a narrower, more specific methodology slide on
2026-06-16. The two are not identical. This note records which version is
authoritative and why, so future work does not chase the deprecated broader
scope.

## The two versions

### Version A — Original methodology picture (project start)

Source: `context/assets/images/generated_image_1.png` / `generated_image_2.png`
(replicas of the mentor's original methodology figure), analysed 2026-07-02.

- Output: "Semi-arid Region Flood and Sediment Priority Map".
- Three top-level modules: Flood Hazard Indicators; Vulnerability and Exposure;
  **Post-Mining Opportunities and Value** (pit lakes, constructed wetlands,
  water-energy nexus, downstream sediment trapping).
- Five input-layer families: Flood Hazard, Sediment Risk, Land Use / Artisanal
  Mining, Environmental Sensitivity, Socioeconomic Factors.
- Full method chain includes **citizen-science inputs** (flash-flood reports,
  erosion hotspots, blocked culverts, sediment deposition, infrastructure
  impacts) and **stakeholder feedback iteration**.
- No mention of a Zimbabwe–Peru comparison.

### Version B — 2026-06-16 methodology slide (authoritative)

Source: `context/docs/mentor-explanation/Mentor_Methodology_Slide_Record_2026-06-16.md`
(the slide the mentor actively sent).

- PIM formula: `PIM = wF(FH) + wS(SR) + wL(LU) + wE(ES) + wSE(SV)` — five scored
  criteria.
- Pairwise matrix supplied (CR 0.022, consistent), labelled "example".
- **Rehabilitation Potential**: listed as an input layer but **omitted from the
  PIM formula and the matrix**. Role unconfirmed (sixth criterion vs post-score
  filter).
- **Citizen science and stakeholder iteration: absent.**
- Zimbabwe–Peru comparison: still not in the slide itself, but established as a
  project requirement by the dataset inventory and research review (2026-06-02).

## Decision: Version B (2026-06-16 slide) is authoritative

Rationale:
- It is the most recent and most specific statement of method the mentor gave.
- It is the version the mentor actively sent, not a legacy picture.
- The slide narrows the scope: five scored criteria, example weights, and an
  explicit open question on Rehabilitation Potential rather than treating it as
  a full third module.

## What this means for project scope

In scope (Version B):
- Five AHP-scored criteria (Flood, Sediment, Land Use/ASM, Environmental,
  Socioeconomic), plus the rainfall sensitivity criterion already added.
- Bilateral Zimbabwe–Peru prototype comparison (established requirement, not
  gated by the slide).
- AHP-MCDA weighted overlay producing a priority intervention map.
- Sensitivity analysis over weights.

Not required unless the mentor re-requests (Version A legacy):
- Citizen-science input module — dropped from Version B. Do not build it.
- Stakeholder feedback iteration loop — dropped from Version B. Do not build it.
- Post-mining opportunities as a full third module — reduced in Version B to an
  unconfirmed single layer (Rehabilitation Potential).

Open, mentor-gated:
- Rehabilitation Potential role (sixth criterion vs post-score filter). Tracked
  as IFPM-D05. Not buildable until the mentor answers.

## What this changes for current work

Nothing blocks the 7/18 deliverable. The integrated priority board, boss
process figure, and mentor message draft all operate inside Version B scope
(five-plus-one scored criteria, bilateral prototype, sensitivity scenario).
This note exists so that the broader original picture does not later pull the
project toward citizen-science or stakeholder-iteration work that the mentor
has since de-scoped.
