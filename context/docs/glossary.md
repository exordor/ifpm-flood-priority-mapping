# IFPM Glossary

Status: active shared term reference. Use this when writing any mentor-facing message,
briefing, or figure caption so internal code names do not leak into human communication.

## Rule

This file is the single source of truth for **what to call things when writing for the mentor
or any human reader**. Internal code names (`V1`, `boundary_v1`, `HB_L8_*`, `HYBAS_ID`,
`Step S*`, `IFPM-*`, `diagnostic_only`) stay inside engineering notes under
`project-management/` and `data-management/`. They do not appear in `mentor-explanation/`
documents, figure captions, or anything the mentor reads.

If a concept has both an internal name and a human name below, use the human name in
mentor-facing text. Internal names appear in this file only so the author can map them.

## Source-Backed Scope

This glossary now separates three levels of terminology support:

1. **External standard terms**: terms backed by disaster-risk, GIS, USLE/RUSLE, GDAL, or AHP
   references.
2. **Literature-aligned modelling terms**: terms commonly used in flood-susceptibility and
   GIS-MCDA papers, but still dependent on the specific indicator set.
3. **Project-specific communication terms**: terms used only to explain this prototype. These
   must be defined on first use and must not be presented as field-standard terms.

| Approved term | Deprecated / avoid | Project meaning | Source support | Allowed context | Not allowed context |
|---|---|---|---|---|---|
| Flood conditioning factors | `flood_hazard_proxy`; flood hazard | Terrain and drainage indicators that condition flood susceptibility, currently TWI high-wetness and drainage proximity | Flood-susceptibility GIS-MCDA papers commonly use "conditioning factors" for elevation, slope, rainfall, distance to river, TWI, LULC, soil and drainage factors [S10, S11] | Prototype susceptibility / priority criteria | Do not call it flood hazard unless inundation extent, depth, velocity, probability, or return period is modelled |
| Flood susceptibility map | flood-risk map | A relative map of where flood-prone conditions are more likely under selected indicators | Flood-susceptibility GIS-MCDA literature [S10, S11] | Prototype output when validation is absent | Do not use for validated probability or impact claims |
| Flood risk | susceptibility; priority | Potential adverse consequences from hazard interacting with exposure and vulnerability | UNDRR and IPCC frame risk through hazard, exposure and vulnerability [S1, S3] | Thesis title, conceptual framing, final validated risk discussion | Do not use for current unvalidated priority/susceptibility outputs |
| Exposure indicators | `socioeconomic_exposure`; road-only vulnerability | Roads, settlements, assets, bridges or people potentially located in affected areas; current road/access layer is only a partial indicator | UNDRR/IPCC/PreventionWeb separate exposure from vulnerability and risk [S3, S4] | Data request, candidate criterion, exposure screening | Do not call road proximity alone socioeconomic vulnerability |
| Vulnerability | road accessibility; exposure | Conditions that increase susceptibility to hazard impacts | UNDRR vulnerability terminology [S2] | Only when social, economic, physical, institutional, or adaptive-capacity evidence exists | Do not infer vulnerability from roads alone |
| Soil erosion factors | `sediment_structure`; `erosion_structure_proxy` | K x LS x C source structure and related erosion-screening factors; rainfall erosivity must be handled separately | USLE/RUSLE component factors are standard in FAO soil-erosion material [S5, S6] | Erosion-screening criterion or RUSLE factor discussion | Do not call it observed sediment delivery or final sediment risk |
| Rainfall erosivity (R-factor) | generic rainfall; `R-invariant` | USLE/RUSLE rainfall energy term, ideally derived from storm energy and intensity | FAO and ESDAC define R-factor / rainfall erosivity through rainfall kinetic energy and 30-minute intensity [S5, S7] | RUSLE/USLE discussion, sensitivity scenario | Do not use monthly rainfall directly as true EI30 without method caveat |
| Rainfall climatology | `rainfall_climatology_proxy` | Coarse rainfall pattern used as a sensitivity-scenario criterion | CHIRPS is a 0.05 degree gridded rainfall time series; resampling must retain the effective-resolution warning [S13] | Scenario comparison with source/resolution caveat | Do not present as native 30 m rainfall evidence |
| Land use/land cover | broad land-use risk | WorldCover/LULC-derived pressure or context | LULC is commonly used as a flood-conditioning factor in susceptibility studies [S10, S11] | Candidate criterion, context layer | Do not combine with mining unless the component weights are explicit |
| Mining / ASM activity | mining truth from OSM only | Mining-related mapped features or official mining/ASM data, with source strength stated | Project-specific criterion; source strength depends on OSM vs official cadastre | Mining-pressure criterion or data gap | Do not imply official ASM footprint when only OSM quarry/industrial evidence is used |
| NoData | zero risk; low score | Raster cells without valid data, represented by a NoData value or mask | GDAL and Rasterio document NoData values/masks as raster metadata and masks [S8, S9] | Raster QA, coverage, grid compatibility | Never fill NoData with 0 for scoring unless a documented imputation method is approved |
| AHP pairwise comparison | final approved weights | Expert judgement method using pairwise comparison and the Saaty scale | AHP literature uses pairwise comparisons and 1-9 scale [S12] | Sensitivity-scenario weights, mentor review | Do not call slide/example weights final approved weights |
| Dominant priority driver | standard MCDA term | The criterion contributing the largest share of a pixel's weighted score | Project-specific explanation term derived from weighted overlay math | Mentor/boss figure explaining "why high" | Must be defined on first use; do not present as a standard algorithm name |
| Stable hotspot | final priority area | Cells that remain in the top-20% priority set across tested weighting scenarios | Project-specific sensitivity-analysis term | Sensitivity-scenario comparison | Do not imply temporal stability or validated hotspot persistence |

### Source List

- **S1** UNDRR. Disaster risk terminology. https://www.undrr.org/terminology/disaster-risk
- **S2** UNDRR. Vulnerability terminology. https://www.undrr.org/terminology/vulnerability
- **S3** IPCC AR6 WGII Annex II Glossary. https://www.ipcc.ch/report/ar6/wg2/downloads/report/IPCC_AR6_WGII_Annex-II.pdf
- **S4** PreventionWeb. Exposure, Understanding Disaster Risk. https://www.preventionweb.net/understanding-disaster-risk/component-risk/exposure
- **S5** FAO. Universal Soil Loss Equation. https://www.fao.org/land-water/land/land-governance/land-resources-planning-toolbox/category/details/en/c/1236441/
- **S6** FAO. Global Soil Erosion Modelling. https://www.fao.org/land-water/land/land-governance/land-resources-planning-toolbox/category/details/en/c/1236446/
- **S7** ESDAC. Rainfall erosivity. https://esdac.jrc.ec.europa.eu/themes/rainfall-erosivity-europe
- **S8** GDAL. Raster Data Model. https://gdal.org/en/stable/user/raster_data_model.html
- **S9** Rasterio. Nodata masks. https://rasterio.readthedocs.io/en/stable/topics/masks.html
- **S10** Example flood-susceptibility GIS-MCDA paper. https://www.mdpi.com/2073-4441/17/7/937
- **S11** Example flood-conditioning-factor terminology in flood susceptibility mapping. https://www.sciencedirect.com/science/article/pii/S0921818125001407
- **S12** Saaty, T. L. "How to make a decision: The Analytic Hierarchy Process." European Journal of Operational Research, 1990. DOI: https://doi.org/10.1016/0377-2217(90)90057-I
- **S13** Climate Hazards Center. CHIRPS rainfall data. https://www.chc.ucsb.edu/data/chirps

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

| v0.1 name (old, deprecated) | Current name | What it actually is | In current comparison? |
|---|---|---|---|
| `sediment_structure` | `soil_erosion_factors` | K x LS x C erosion source structure; rainfall erosivity must be documented separately | yes |
| `landuse_asm_pressure` | split into `land_cover_pressure` + `mining_pressure` | land-cover pressure and mining pressure are now **separate** criteria, not averaged together | both yes |
| `environmental_sensitivity` | `river_proximity_indicators` | distance-to-river evidence; **not used as a standalone environmental-sensitivity claim** | no |
| road-only exposure layer | `exposure_indicators` | road/access proximity evidence; not observed vulnerability | yes |
| `flood_hydrology` | `flood_conditioning_factors` | TWI high-wetness + drainage proximity; terrain flood-conditioning evidence | yes |

Current comparison criteria: `flood_conditioning_factors`, `soil_erosion_factors`,
`land_cover_pressure`, `mining_pressure`, `exposure_indicators`, and
`rainfall_climatology`.

Never write "sediment_structure" in a mentor document as if it means sediment loss — it does
not. Use "soil erosion factors" and note that the erosion magnitude depends on the R-factor.

---

## 3. R-Factor Terms (The Most Technical Area)

| Term | Meaning | Mentor-friendly wording |
|---|---|---|
| R-factor / rainfall erosivity | the rainfall energy term in USLE/RUSLE that drives erosion | "rainfall erosivity (the R-factor)" |
| K x LS x C erosion source structure | the spatial part of USLE/RUSLE before applying rainfall erosivity | "the erosion pattern before we choose the R value" |
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
| **susceptibility map** | where flooding/erosion is *likely* based on conditioning indicators, no probability | yes (what the prototype is) |
| **priority / suitability map** | relative ranking of where intervention matters, under chosen weights | yes (with documented AHP weights) |
| **flood-risk map** | validated probability/magnitude of flood impact | **no** — no validation data |
| **intervention-priority map** | authoritative plan of where to act | **no** — needs validation + official weights |

When unsure, default to "susceptibility" or "priority". Never call an output a "flood-risk
map" unless it has been validated. The project title says "flood risk", but every actual output
so far is susceptibility or priority — say so.

---

## 5. Internal Numbering Systems (For Internal Use Only)

The workspace uses two internal numbering families. They never appear in mentor text.

> **Migration note (2026-06-29):** the old "Gate G1-G7" engineering-gate numbering was merged
> into this scheme. The two Gates that carried a real decision (G1 boundary, G2 modelling unit)
> were folded into **IFPM-D06** and **IFPM-D01** respectively. The five Gates that were pure
> engineering checklists (G3-G7) were renumbered as **Step S1-S5**. Old documents and git history
> still say "Gate G*"; treat any such reference via the table below.

### IFPM-D0X (open decisions — the only decision numbering)

These are the mentor/domain decisions. They are the only place a "decision" is recorded.

| ID | Plain meaning | (was) |
|---|---|---|
| IFPM-D01 | final modelling unit decision (pixel vs sub-basin vs mixed) | Gate G2 |
| IFPM-D02 | Peru boundary rule | — |
| IFPM-D03 | validation evidence hierarchy | — |
| IFPM-D04 | AHP weighting protocol | — |
| IFPM-D05 | mining-data interpretation rule | — |
| IFPM-D06 | Upper Mzingwane boundary acceptance (final thesis boundary) | Gate G1 |

### Step S1-S5 (execution steps — engineering checklists, not decisions)

These are internal engineering steps in `context/docs/research-map/REPRODUCIBILITY.md` (§3 Preflight gate). They verify
readiness; they do not record a decision.

| Step | Plain meaning | (was) |
|---|---|---|
| Step S1 | the rainfall time window and product must be chosen | Gate G3 |
| Step S2 | dataset-specific download preflight must be closed | Gate G4 |
| Step S3 | a download authorization record must be written | Gate G5 |
| Step S4 | execution rules after download | Gate G6 |
| Step S5 | pipeline engineering readiness (tests, grid checks) | Gate G7 |

### IFPM-0XX (task tracking)

These are experiment-registry entries in `context/docs/research-map/EXPERIMENTS.md`. They never appear in mentor text.

### Output claim levels (status tags)

Internal status tags from `context/docs/research-map/REPRODUCIBILITY.md` (§2 Execution status policy): `diagnostic_only`, `provisional`,
`sensitivity_scenario`, `mentor_review_ready`, `final_claim`. These label how confident an
output is. Do not paste the tag into mentor text; translate it (e.g. `provisional` → "working
result, defensible but not yet validated").

---

## 6. Quick Translation Table (Internal Code -> Mentor Words)

| If you find this in a note | Write this to the mentor |
|---|---|
| `V1` / `boundary_v1` | "the V1 prototype catchment" or "the Upper Mzingwane prototype" |
| `HB_L8_*` / `HYBAS_ID=*` | "the prototype catchment" (with its area if needed) |
| `IFPM-D01` | "the modelling-unit decision" |
| `IFPM-D06` | "the boundary decision" |
| `Step S1`-`S5` | (delete — internal engineering step) |
| `IFPM-0XX` | (delete — it is an internal task id) |
| `diagnostic_only` | "an internal diagnostic, not a result" |
| `provisional` | "a working result, defensible but not yet validated" |
| `sensitivity_scenario` | "a what-if check under different assumptions" |
| old R-independent shorthand | "the K x LS x C erosion structure before applying R" |
| `sediment_structure` (old) | "soil erosion factors" |
| `landuse_asm_pressure` (old) | "land-cover pressure and mining pressure" |
