# PIM transformation flow: from raw data to the priority map

How the Secocha and Goslar chains compute the Priority Intervention Map (PIM) from raw data. The exact values are the ones recorded in `run_manifest.json` in each output folder. The code entry point is `bin/factors/run_secocha_pim_chain.py` (Goslar uses the same code, with the entry point `run_goslar_pim_chain.py`).

## 1. Three-layer structure

```
Raw data                    Components (0-1)              Main criteria (0-1) PIM
SRTM/Copernicus DEM   →  twi_wetness, drainage_proximity ┐
CHIRPS / REGNIE rain  →  rainfall_climatology            ┴→ Flood     0.34 ┐
SoilGrids K           →  soil_k_factor                   ┐                 │
DEM slope length      →  ls_factor                        ├→ Sediment  0.25 │
WorldCover            →  c_factor                        ┘                 │
WorldCover / CLMS     →  land_cover_pressure,            ┐                 ├→ PIM (0-1)
                         bare_soil_vegetation_loss,      ├→ Land Use  0.17 │
                         built_agriculture_road_expansion┘                 │
WorldCover / protect. →  water_wetland, protected        ─→ Environmental 0.10
OSM / pop. / bldgs    →  road_access, settlement_population,
                         critical_infrastructure          ─→ Socioeconomic 0.14 ┘
```

In the diagram, "DEM slope length" stands for the DEM-derived slope length and slope, "protect." for protected areas, "pop." for population and "bldgs" for buildings. The sub-weights are listed in `context/docs/research-map/DECISION_LOG.md`. Mining is not part of the calculation; it is only overlaid as a comparison layer after the PIM has been computed.

## 2. Rules for each step

**Three ways of converting to 0–1**
- Continuous values (TWI, distance, LS, K, rainfall, population, etc.): the 2nd and 98th percentiles within the study area are used as the lower and upper bounds, and values are scaled linearly and clipped to 0–1. Distance indicators are then converted to 1 − value, so that "closer means a higher score".
- Categorical data (WorldCover land classes): each class is mapped to a 0–1 value using a lookup table.
- Vector extents (protected areas, water bodies): 1 inside the extent, 0 outside it.

Percentile scaling gives a relative ranking within the study area, so the bounds change when the study area changes. The Goslar extension area reuses the bounds of the original Abzucht area (the "frozen normalization anchors"), so that scores in the new and old areas can be compared directly.

**Weighted sum**
- Components are combined into main criteria using the sub-weights, and main criteria are combined into the PIM using the top-level weights. The weights in each layer sum to 1.
- A score is only computed for pixels where every component has a value. If any component is missing, the pixel is NoData. It is not filled with 0, and the weight of the missing component is not redistributed to other components.
- Some older Goslar branches are an exception: when a component is missing, its weight is redistributed across the available components. This is noted in the descriptions of the affected experiments.

**Classed maps**: the PIM is split into five classes at equal intervals of 0.2, and values of 0.6 and above count as "high". The 0.6 cut-off is only a display break, not a validated flood threshold.

## 3. Limitations to keep in mind

- The native resolution of CHIRPS rainfall is about 5 km and SoilGrids is 250 m. Aligning them to the 30 m grid does not make them more precise.
- The sediment criterion is a relative score of erosion sources, not a soil loss amount (no R factor is used).
- Some field names are broader than what the data actually represent; see `context/docs/glossary.md` for details.
- Blank areas on the map are missing data, not low risk.
