# IFPM Assumptions Log

Date: 2026-06-29

Status: active concise assumption register.

| id | assumption | status | applies to | consequence |
|---|---|---|---|---|
| A-001 | V1 remains the controlled prototype boundary, not the final thesis boundary. | provisional | V1 outputs | Use V1 for diagnostics/prototypes; do not claim final boundary. |
| A-002 | Coarse rainfall may be used through zonal aggregation or labelled coarse-to-reference-grid resampling. | sensitivity_scenario | CHIRPS/rainfall criteria | Do not describe rainfall as native 30 m evidence. |
| A-003 | The 2026-06-16 mentor-slide AHP matrix may be used as a sensitivity scenario. | sensitivity_scenario | AHP weights | Do not call it final approved weights. |
| A-004 | Deprecated R/A products remain invalid, but new R-factor families may be generated with fresh lineage. | provisional | R-factor/RUSLE work | Keep old products separate; do not pause new provisional R work. |
| A-005 | OSM quarry/industrial evidence is a mining proxy, not official ASM truth. | diagnostic_only | mining/ASM criterion | Use only as proxy/context until official data arrives. |
| A-006 | Road proximity is an exposure/access proxy, not socioeconomic vulnerability. | diagnostic_only | exposure criterion | Use road evidence cautiously and request observed flood-impact data. |
| A-007 | Peru can run data-readiness and terrain diagnostics in parallel. | diagnostic_only | Peru side | Do not make final Zimbabwe-Peru comparison until harmonized. |
| A-008 | The Peru Arequipa-Moquegua-Tacna discovery envelope is a discovery proxy, not an authoritative administrative boundary. | diagnostic_only | Peru boundary discovery | Candidate basins are discovery outputs; IFPM-D02 stays open until mentor resolves admin-vs-hydrographic and an authoritative polygon is obtained. |
| A-009 | PE1 is an engineering-pilot Peru boundary, chosen by a selection rule, NOT a research-value-selected site (no mentor-named Peru outlet exists). | engineering_pilot | Peru terrain chain | PE1 proves the Peru chain works and is comparable to Zimbabwe V1; replace it if the mentor names a specific Peru site. No flood-risk/comparison claim from PE1. |
| A-010 | The `rainfall_climatology_proxy` criterion (rainfall_sensitivity_v0_3) is a 0.05 deg CHIRPS rainy-season mean bilinear-resampled to the V1 30 m grid; resampling-edge NoData slivers inside V1 are nearest-EDT filled. | sensitivity_scenario | rainfall criterion, rainfall_sensitivity_v0_3 | Effective resolution is ~5 km, NOT native 30 m rainfall; use only for overlay-sensitivity testing, never as pixel-level rainfall evidence or final flood-risk claim. Mirrors the V2 R-factor diagnostic waiver. |
| A-011 | The hotspot-exposure diagnostic (hotspot_exposure_diagnostic_v0_3) measures spatial co-location of v0.2 stable hotspots with exposure proxies; weak co-location means hotspots reflect natural-pressure overlap, not observed exposure. | diagnostic_only | exposure diagnostic | Does NOT validate hotspots as flood risk; supports the data-request argument for real exposure/flood-observation data rather than claiming current hotspots are validated. |
