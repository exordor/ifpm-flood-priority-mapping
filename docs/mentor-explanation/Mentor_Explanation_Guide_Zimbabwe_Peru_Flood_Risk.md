# Mentor Explanation Guide: Zimbabwe and Peru Flood Risk Study

This guide explains the original document and the research review in simple language. It is written so you can explain the project clearly to your mentor, even if you do not yet feel confident with the technical details.

## 1. The One-Sentence Explanation

We are preparing the data and method for a comparative flood-risk study in Zimbabwe and Peru, using GIS layers such as rainfall, terrain, land use, mining activity, environmental sensitivity, population exposure, and rehabilitation potential.

In simple words:

> We want to identify which places are more vulnerable to flood-related problems, especially where mining and environmental damage may make the risk worse, and where intervention or rehabilitation should be prioritized.

## 2. What the Original Document Was Trying To Do

The original document is a first inventory. It lists the main data layers that might be needed before modelling begins.

It has 10 main parts:

1. Flood hazard
2. Sediment risk
3. Land use and ASM pressure
4. Environmental sensitivity
5. Socioeconomic vulnerability
6. Mining location and intensity
7. Rehabilitation potential
8. AHP-MCDA framework
9. Priority intervention model
10. Validation

The original document is useful because it gives the overall structure of the study. But it was still incomplete because it mostly listed dataset names. It did not fully explain:

- where to download each dataset;
- whether each dataset is really suitable;
- what GIS preprocessing is required;
- what limitations each dataset has;
- how to validate the final model;
- how to explain the AHP-MCDA weighting clearly.

That is why the research review was needed.

## 3. What My Research Review Added

The research review did not replace the original document. It strengthened it.

The review added:

- real dataset links;
- notes on whether each dataset is suitable;
- GIS preprocessing steps;
- extra datasets that may be needed;
- risks and limitations;
- clearer AHP-MCDA weighting advice;
- a better way to think about mining activity;
- a clearer distinction between risk and rehabilitation feasibility;
- a short draft email reply to the mentor.

The main message of the review is:

> The framework is good as a starting point, but before modelling we must verify the data sources, define the study boundaries, prepare the GIS layers properly, validate mining and flood data, and test the AHP weights.

## 4. Basic Concepts You Need To Understand

### Flood Hazard

Flood hazard means the physical possibility of flooding.

It depends on things like:

- how much rain falls;
- how intense the rain is;
- where rivers are;
- how steep or flat the land is;
- how water flows across the landscape.

Simple explanation for mentor:

> For flood hazard, I use rainfall, DEM, rivers, drainage, slope, flow accumulation, and wetness-related terrain indicators to estimate where flooding is more likely.

### Sediment Risk

Sediment risk means the risk that soil, mining waste, or eroded material is washed into rivers.

This matters because mining and bare soil can make rivers more polluted and can worsen downstream flood impacts.

The original document uses the RUSLE model:

`A = R x K x LS x C x P`

Simple meaning:

- `A` = estimated soil loss
- `R` = rainfall erosivity, how powerful rainfall is for erosion
- `K` = soil erodibility, how easily soil erodes
- `LS` = slope length and steepness
- `C` = land cover or vegetation protection
- `P` = conservation practices

Simple explanation for mentor:

> For sediment risk, I plan to use a RUSLE-based approach. It will combine rainfall, soil properties, slope, land cover, and mining disturbance to estimate where erosion and sediment delivery may be high.

### Land Use and ASM Pressure

Land use means how the land is covered or used, such as vegetation, bare soil, water, urban areas, agriculture, or mining.

ASM means artisanal and small-scale mining.

This matters because mining and bare soil can change runoff and erosion.

Simple explanation for mentor:

> I use land-cover data and satellite imagery to identify vegetation, bare soil, land-use change, and possible ASM expansion.

### Environmental Sensitivity

Environmental sensitivity means places where damage would be more serious.

Examples:

- protected areas;
- wetlands;
- rivers;
- biodiversity hotspots;
- permanent or seasonal water bodies.

Simple explanation for mentor:

> Environmental sensitivity helps identify places where flood, erosion, or mining impacts could harm important ecosystems.

### Socioeconomic Vulnerability

Socioeconomic vulnerability means people, infrastructure, and services that may be affected.

Examples:

- population density;
- settlements;
- roads;
- schools;
- health facilities;
- exposed buildings.

Simple explanation for mentor:

> This layer helps show where flood or mining-related impacts may affect people and infrastructure.

### Mining Location and Intensity

Mining location means where mining rights or mining activity are located.

Mining intensity means how strong the mining pressure is, for example:

- number of mining areas;
- size of mining footprint;
- tailings or spoil areas;
- distance from mining to rivers;
- mining density in a sub-catchment.

Important caution:

> A mining concession is not the same as active mining.

A concession means someone has the legal right to mine, but it does not prove that mining is currently happening there. Active mining needs to be checked with satellite images, official data, or field/expert validation.

Simple explanation for mentor:

> I separate official mining rights from observed mining disturbance. This is important because concessions do not always equal active mining footprints.

### Rehabilitation Potential

Rehabilitation potential means where restoration or intervention may be useful.

But it has two sides:

1. Need: where damage or risk is high.
2. Feasibility: where restoration is actually possible.

For example, an area may be badly degraded but too steep, too remote, or legally complicated. That means it has high need but low feasibility.

Simple explanation for mentor:

> I suggest treating rehabilitation as both a need problem and a feasibility problem. High-risk areas are not always easy to rehabilitate.

### AHP-MCDA

AHP-MCDA is a way to combine many GIS layers into one priority map.

AHP means Analytic Hierarchy Process.

MCDA means Multi-Criteria Decision Analysis.

Simple meaning:

> We have many factors. Some are more important than others. AHP helps us decide the weights, and MCDA combines the weighted layers into a final score.

Example:

- rainfall might be very important;
- population exposure might also be important;
- mining pressure might be important in mining areas;
- environmental sensitivity matters where ecosystems are vulnerable.

The original document uses the Saaty scale:

- 1 = equal importance
- 3 = moderately more important
- 5 = strongly more important
- 7 = very strongly more important
- 9 = extremely more important

Consistency Ratio, or CR, checks whether expert judgments are internally consistent.

Simple explanation for mentor:

> I will use AHP to assign weights, but I need expert input and a consistency-ratio check. If CR is above 0.10, the weights should be revised.

## 5. Original Document Explained Section By Section

### 1. Flood Hazard Layer

Original idea:

Use rainfall, DEM, rivers, and watershed data to understand where flooding is more likely.

Datasets:

- CHIRPS rainfall
- ERA5-Land rainfall
- SRTM DEM
- ALOS PALSAR DEM
- HydroSHEDS rivers
- HydroBASINS watersheds

What this means:

> This layer describes the physical flood conditions.

Review improvement:

I added more specific data links and preprocessing steps, such as rainfall extremes, DEM correction, flow accumulation, slope, distance to rivers, and validation with local rainfall or flood data.

What to tell mentor:

> The original flood hazard layer is reasonable, but I need to define the study period, process rainfall extremes, derive hydrological terrain variables from DEM, and validate with observed flood or rainfall data.

### 2. Sediment Risk Layer

Original idea:

Use soil, rainfall, DEM, land cover, and mining spoil areas to estimate erosion and sediment risk.

What this means:

> This layer asks where soil or mining waste may be washed away and transported into rivers.

Review improvement:

I added SoilGrids, GloREDa, CHIRPS, Sentinel-2, Landsat, and RUSLE preprocessing details. I also noted that RUSLE estimates soil loss, not automatically sediment reaching the river.

What to tell mentor:

> I will use RUSLE as a screening tool for erosion risk, but I should add a sediment-delivery proxy, for example distance to rivers and hydrological connectivity.

### 3. Land Use and ASM Pressure

Original idea:

Use ESA WorldCover, Sentinel-2, Landsat, and Google Earth Pro to map land cover and mining pressure.

What this means:

> This layer looks at how land surface conditions and mining disturbance affect runoff and erosion.

Review improvement:

I added that Sentinel-2 and Landsat need cloud masking, seasonal compositing, indices such as NDVI and bare soil index, and validation for ASM mapping.

What to tell mentor:

> Land cover data gives the baseline, but ASM mapping needs satellite interpretation and validation because global land-cover products may not identify mining accurately.

### 4. Environmental Sensitivity

Original idea:

Use protected areas, water bodies, biodiversity, and river ecosystems.

What this means:

> This layer shows where environmental damage would be more serious.

Review improvement:

I added WDPA/Protected Planet, JRC Global Surface Water, GBIF, KBA, Ramsar, and quality-control steps.

What to tell mentor:

> Environmental sensitivity should include protected areas, wetlands, rivers, and biodiversity records, but GBIF data needs careful filtering because occurrence data can be biased.

### 5. Socioeconomic Vulnerability

Original idea:

Use population density, infrastructure, and settlement data.

What this means:

> This layer identifies who or what may be affected by flood risk.

Review improvement:

I added WorldPop, GHSL, OSM/Geofabrik, HOTOSM/HDX roads, and the need to check data completeness.

What to tell mentor:

> I will use population and infrastructure layers to estimate exposure, but if I want true vulnerability, I may also need poverty, housing quality, age, disability, or adaptive capacity data.

### 6. Mining Location and Intensity

Original idea:

Use Zimbabwe and Peru mining sources, Sentinel-2 mapping, and geological data.

What this means:

> This layer tries to measure how mining activity may increase flood, erosion, and pollution risk.

Review improvement:

I separated Peru and Zimbabwe data. Peru has stronger official mining cadastre access through INGEMMET/GEOCATMIN. Zimbabwe data may require more verification. I also emphasized that concessions are not the same as active mining.

What to tell mentor:

> For mining, I will combine official cadastre or concession data with observed mining footprints from satellite imagery, because legal mining rights do not always show actual mining disturbance.

### 7. Rehabilitation Potential

Original idea:

Use Sentinel-2, water data, DEM, WorldPop, and HydroSHEDS to identify areas suitable for rehabilitation.

What this means:

> This layer asks where intervention or restoration might be useful.

Review improvement:

I recommended separating rehabilitation need from feasibility.

What to tell mentor:

> I think rehabilitation potential should not just mean damaged areas. It should also include whether rehabilitation is realistic, accessible, and socially or legally feasible.

### 8. AHP-MCDA Framework

Original idea:

Use seven criteria and AHP weights to combine them.

What this means:

> We create several maps, give each map a weight, and combine them into a final priority map.

Review improvement:

I recommended using expert input, checking consistency ratio, and running sensitivity analysis.

What to tell mentor:

> The AHP structure is useful, but the weights should not be arbitrary. They should come from expert pairwise comparisons, pass the consistency-ratio check, and be tested through sensitivity analysis.

### 9. Priority Intervention Model

Original idea:

Combine all weighted criteria into one priority score.

Original formula:

`PIM = wF(FH) + wS(SR) + wL(LU) + wE(ES) + wV(SV) + wM(ML) + wR(RP)`

Simple meaning:

> Each factor gets a score and a weight. Then we add them together to get the final priority score.

Review improvement:

I suggested separating risk from intervention feasibility:

- first calculate risk;
- then calculate intervention priority.

What to tell mentor:

> I propose separating the risk model from the intervention model, because high-risk areas are not always the easiest or most suitable places for rehabilitation.

### 10. Validation

Original idea:

Use historical floods, EM-DAT, Dartmouth Flood Observatory, sediment studies, expert surveys, community consultation, and government reports.

What this means:

> Validation checks whether the model results make sense.

Review improvement:

I added CEMS, GloFAS/GFM, JRC Global Surface Water, local reports, and possible ROC/AUC or success-rate validation.

What to tell mentor:

> Before final modelling, I need to define the validation dataset. The model should be checked against historical flood events, satellite flood observations, local records, expert review, or community consultation.

## 6. The Most Important Things To Tell Your Mentor

If you only remember five points, remember these:

1. The framework is good as a starting point.
2. I added real dataset links and checked dataset suitability.
3. Mining data must be treated carefully because mining concessions are not the same as active mining.
4. AHP weights need expert input, consistency checking, and sensitivity analysis.
5. Before modelling, we must confirm study boundaries, preprocessing steps, and validation datasets.

## 7. Simple English Explanation You Can Say To Your Mentor

You can say:

> My original document was a first dataset inventory and methodology framework. It listed the main layers needed for comparative flood risk modelling in Zimbabwe and Peru, including flood hazard, sediment risk, land use, environmental sensitivity, socioeconomic vulnerability, mining pressure, and rehabilitation potential.

Then say:

> After the review, I expanded the document by adding real dataset links, checking whether the datasets are suitable, and identifying the GIS preprocessing steps needed before modelling.

Then say:

> One important point is that I should not treat mining concessions as active mining areas. I need to combine official mining data with satellite-based mining footprint mapping and validation.

Then say:

> For the AHP-MCDA part, I understand that weights should not be arbitrary. They should be based on expert pairwise comparisons, checked using the consistency ratio, and tested with sensitivity analysis.

Then say:

> I also realized that rehabilitation potential should probably be treated in two parts: where rehabilitation is needed, and where rehabilitation is feasible.

Finally say:

> Before modelling, I need to confirm the study-area boundaries, select the temporal period, finish GIS preprocessing, define the validation data, and agree on the weighting approach.

## 8. Questions You Can Ask Your Mentor

These are good questions to ask:

1. Should the Peru study area be treated as an administrative region or as hydrological basins inside the region?
2. Should rehabilitation potential be part of the main risk model, or should it be a second-stage intervention model?
3. Which criteria should receive the highest weight: flood hazard, socioeconomic exposure, mining pressure, or sediment risk?
4. Do we have access to local flood records, rainfall stations, or streamflow data?
5. For Zimbabwe, do we have reliable official mining data, or should satellite mapping be the main source?
6. What validation method would you prefer if historical flood data are limited?

## 9. Short Version For Meeting Notes

The original document proposes the main data layers and AHP-MCDA structure for flood-risk prioritization. The research review strengthens it by adding official dataset links, preprocessing steps, suitability notes, validation options, and methodological cautions. The key improvements are clearer data sourcing, careful treatment of mining data, stronger validation planning, sensitivity testing for AHP weights, and separating risk from rehabilitation feasibility.

## 10. Confidence Level

You can confidently say:

- The project structure is clear.
- The main data categories are appropriate.
- More work is needed before modelling begins.
- The biggest uncertainties are study-area boundary definition, mining data reliability, local validation data, and AHP weight selection.

Do not say:

- The model is already complete.
- The final weights are decided.
- Mining concessions equal active mining.
- Global datasets are enough without validation.
- AHP-MCDA can replace hydrological/inundation modelling if actual flood depth or flood extent is required.
