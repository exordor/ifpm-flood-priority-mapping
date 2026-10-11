# Decision Log

Decisions still in force, newest first. Superseded decisions are in Git history.

## 2026-08-14 — Goslar uses the same weights as Secocha

A temporary Goslar-specific reweighting was withdrawn so the two cases stay directly
comparable. Goslar runs the Secocha chain unchanged on its own inputs.

## 2026-08-09 — Secocha replaces the former Peru area

The official 2023 Secocha event evidence lies about 118 km outside the former area
(`peru_former`), so the model could not be compared with it there. The active
boundary became `secocha_reference_extent`. The former area's outputs
(`outputs/peru_former_pim_chain/`) are frozen; key files are hashed in
`FROZEN_BASELINE.json` and must not be overwritten.

## 2026-08-07 — Supervisor's complete weight table

Top level: Flood 0.34, Sediment 0.25, Land Use 0.17, Environmental 0.10, Socioeconomic 0.14.

| Criterion | Sub-weights |
|---|---|
| Flood | rainfall 0.35, TWI 0.25, drainage proximity 0.40 |
| Sediment | soil K 0.25, LS 0.50, C 0.25 |
| Land Use | land-cover pressure 0.40, bare/vegetation loss 0.35, built/agriculture/road 0.25 |
| Environmental | water/wetland 0.65, protected areas 0.35 |
| Socioeconomic | road access 0.35, settlement/population 0.35, critical infrastructure 0.30 (proxied by building density) |

The earlier test weights (0.35/0.25/0.20/0.12/0.08) gave nearly the same ranking
(rho 0.988, top-20% Jaccard 0.85); see `outputs/peru_former_pim_chain/pim_versions/comparison_02_no_mining_vs_07_supervisor/`.

## 2026-08-07 — Mining removed from the score

On Supervisor's direction, mining has zero weight in every criterion. It is shown
only as a separate overlay after the PIM is computed, to see whether mining areas
coincide with high-priority areas.

## 2026-07-06 — R-factor and USLE soil loss dropped

The June V1/V2 R-factor products used wrong coefficients and were deleted. Sediment
is an additive score of normalized K, LS and C and does not need R. Reopen only if
an absolute soil-loss rate (t/ha/yr) is required.

## 2026-06-16 — Method: five-criterion PIM by weighted overlay

From the mentor's methodology slide: PIM = weighted sum of Flood, Sediment, Land Use,
Environmental and Socioeconomic criteria, each normalized to 0–1. This is a
prioritisation index, not hydrodynamic flood modelling. Citizen science, stakeholder
iteration and a post-mining module are out of scope.
