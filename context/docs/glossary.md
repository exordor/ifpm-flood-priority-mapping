# IFPM Glossary

## Criteria and components

| Code | Criterion | Components (field names) |
|---|---|---|
| FH | Flood hazard / flood conditioning | `rainfall_climatology` (CHIRPS rainy-season mean, ~5 km native), `twi_wetness`, `drainage_proximity` |
| SE | Sediment (soil-erosion factors) | `soil_k_factor` (SoilGrids, 250 m native), `ls_factor`, `c_factor` (from WorldCover) |
| LU | Land use | `land_cover_pressure`, `bare_soil_vegetation_loss`, `built_agriculture_road_expansion` |
| ES | Environmental | `water_wetland_context`, `protected_ecological_context` |
| SV | Socioeconomic | `road_access_proximity`, `settlement_population`, `critical_infrastructure` |

PIM (Priority Intervention Map) is the weighted sum of the five criteria, 0–1.

Field names that say more than the data show:

- `bare_soil_vegetation_loss` in Goslar is tree-cover loss (CLMS 2018–2024), not bare soil.
- `built_agriculture_road_expansion` is static proximity, not measured expansion.
- `critical_infrastructure` is mapped-building density, not an infrastructure inventory.
- Sediment is an erosion-source score, not measured sediment transport or soil loss.

## Map words

| Word | Meaning | Does the project produce it? |
|---|---|---|
| Priority map (PIM) | Relative ranking under chosen weights | Yes |
| Susceptibility | Where conditions favour flooding, without probability | Yes (flood criterion) |
| Flood-risk map | Validated probability or impact of flooding | No |

## Boundary ids

| Id | Meaning |
|---|---|
| `peru_secocha_a7367_reference_extent_v1` | Active Secocha 30 km² map-reference window (not a catchment) |
| `goslar_abzucht_display_rectangle_v1`, `goslar_multiriver_full_extent_v1` | Active Goslar comparison extents |
| `peru_hybas_l7_6070641200` | Former Peru area (frozen) |
| `boundary_v1` | Zimbabwe Upper Mzingwane (background) |

## Claim levels in manifests

`diagnostic_only` (pipeline or data check), `provisional` (working result, not validated),
`sensitivity_scenario` (what-if under other weights or inputs), `validation_candidate`
(evidence that could be used for validation once reviewed). No output is a final claim.
