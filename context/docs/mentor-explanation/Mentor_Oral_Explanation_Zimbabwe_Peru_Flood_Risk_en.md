# Mentor Oral Explanation: Zimbabwe and Peru Flood Risk Study

> Note: this speaking guide was written early (2026-06-10), before the rainfall-erosivity
> (R-factor) investigation. It still reflects the dataset-inventory and methodology stage and
> does not cover the R-factor findings, the autonomous prototype, or the current criteria. Use
> the newer `Mentor_Trip_Data_Request_Package_2026-06-29.md` and the R-factor briefing for the
> current state. Kept here as a speaking aid for the early-stage inventory discussion only.

This is a short speaking guide for explaining the reviewed dataset inventory and methodology framework to the mentor. It is written for a meeting or informal discussion, not as a technical report.

## 1. Main Message

I can explain the review in one sentence:

> I reviewed the dataset inventory to check whether the proposed data sources and AHP-MCDA framework are suitable for a comparative flood-risk and rehabilitation-priority study in Zimbabwe and Peru, and I identified what still needs to be confirmed before modelling starts.

The most important point is:

> The framework is strong enough for mentor feedback, but it is not yet a final modelling specification. Before modelling, we still need to confirm the modelling unit, time period, validation data, data-access constraints, and weighting protocol.

## 2. Two-Minute Speaking Script

I would start with:

> Thank you for sending the inventory. I reviewed it against the points you asked about: dataset availability and suitability, GIS preprocessing, the AHP-MCDA framework, mining and rehabilitation criteria, and remaining gaps before modelling.

Then I would summarize:

> Overall, the structure is appropriate. The main data categories are rainfall and flood hazard, sediment and erosion risk, land cover and mining disturbance, environmental sensitivity, socioeconomic exposure, official mining information, rehabilitation potential, and validation data.

Then explain what was improved:

> I added official data-entry links and suitability notes for the main datasets. I also separated datasets that are directly open from datasets that may require registration, licence acceptance, account workflows, or manual download checks.

Then state the key caution:

> The public URLs have been manually checked and are reachable, but that does not yet prove that all data can be downloaded directly, that licences are cleared, or that the GIS layers are complete and ready for modelling.

Then close with the modelling decision:

> My main recommendation is to use globally consistent datasets for comparability, then add national datasets where they are authoritative. But before modelling we should agree on the final spatial unit, temporal window, validation approach, and AHP weighting process.

## 3. How I Addressed The Mentor's Requests

### Dataset Availability And Suitability

What I can say:

> I checked the proposed datasets and added real access links where possible. For the core cross-country data, CHIRPS v3, SRTM, HydroBASINS, ESA WorldCover, Sentinel-1/2, Landsat, WorldPop, GHSL, OSM, WDPA, GBIF, and flood-event validation sources are suitable starting points.

Important details:

- CHIRPS v3 should be the main rainfall source; CHIRPS v2 should only be kept for compatibility with older studies.
- SRTM is a clear baseline DEM; Copernicus DEM GLO-30 can be used as a comparison but should be documented as a DSM.
- ESA WorldCover is useful as a land-cover baseline, but not as the only evidence for land-use change.
- Peru has a stronger official mining data route through INGEMMET/GEOCATMIN.
- Zimbabwe's mining cadastre is official but should be treated carefully because the portal indicates that data may still be provisional or under cleaning.

What I should not overclaim:

> I should not say that all datasets are already fully downloaded and ready. I can say that the retained public entry links were opened successfully, but account access, licence acceptance, data export, and GIS quality still need to be checked.

### GIS Preprocessing Requirements

What I can say:

> The review makes the preprocessing requirements more explicit. The key steps are boundary definition, CRS harmonization, clipping, raster alignment, resolution harmonization, DEM conditioning, hydrological derivatives, cloud masking, seasonal compositing, distance indicators, and zonal statistics.

The main preprocessing decision:

> I recommend deriving raster indicators first, then aggregating them to sub-basin or hydrographic units for the final comparison. This should be more stable than relying only on pixel-level AHP outputs.

Important issue:

> Upper Mzingwane is a catchment, while Arequipa-Moquegua-Tacna is currently defined more like an administrative region. We need to decide whether the Peru analysis should use administrative boundaries, ANA hydrographic units, or hydrological units clipped by the administrative region.

### AHP-MCDA Framework And Weighting

What I can say:

> The AHP-MCDA framework is useful for combining multiple criteria, but the weights should not be arbitrary. They should come from expert pairwise comparison, be checked using the consistency ratio, and then tested through sensitivity analysis.

Recommended structure:

- Keep the main criteria: flood hazard, sediment risk, land use and mining disturbance, environmental sensitivity, socioeconomic exposure, mining pressure, and rehabilitation potential.
- Separate hazard, exposure, mining pressure, and rehabilitation opportunity before assigning weights.
- Run sensitivity analysis to see whether the final priority map changes strongly when weights change.

Short explanation:

> AHP helps organize expert judgement, but it does not remove uncertainty. I should report both the selected weights and how sensitive the results are to weight changes.

### Mining Location And Rehabilitation Potential Criteria

What I can say:

> I separated official mining rights from observed mining disturbance. A concession or cadastre polygon does not automatically mean active mining, so it should be checked using satellite imagery, high-resolution interpretation, or local knowledge.

For Peru:

> INGEMMET/GEOCATMIN should be the main official route for mining information.

For Zimbabwe:

> The official mining cadastre and Ministry of Mines sources are useful, but they need validation because the cadastre data may be provisional.

For rehabilitation:

> I suggest separating rehabilitation need from rehabilitation feasibility. A place can have high damage or high risk, but still be difficult to rehabilitate because of slope, access, land tenure, remoteness, social conditions, or legal constraints.

Short explanation:

> High risk does not always mean high rehabilitation priority. The final intervention layer should consider both need and feasibility.

### Gaps Before Modelling Begins

What I can say:

> The main gaps are not only missing datasets. They are modelling decisions that need to be fixed before the GIS workflow starts.

High-priority gaps:

1. Final modelling unit: pixel, sub-basin, hydrographic unit, or administrative-hydrological hybrid.
2. Temporal window: which years or flood seasons will be used.
3. Validation data: historical flood records, satellite flood extent, EM-DAT, Dartmouth, Copernicus EMS, GloFAS, local reports, or expert review.
4. Mining validation: official cadastre plus remote-sensing evidence.
5. AHP protocol: who provides expert judgement, how many rounds, and what consistency threshold is used.
6. Data access: which sources are open, account-based, licence-based, or request-based.

## 4. Key Technical Cautions To Mention

If there is time, I should mention these cautions because they show that I understand the modelling risk:

- CHIRPS v3 should be preferred over CHIRPS v2.
- RUSLE estimates sheet and rill erosion risk, not actual sediment delivery to rivers.
- WorldCover should not be used alone to prove land-use change between 2020 and 2021.
- Mining concessions are not the same as active mining footprints.
- AHP-MCDA can produce a relative priority or susceptibility map, but it is not a physically based flood-inundation model.
- Validation should be planned before final weights are locked.

## 5. Questions To Ask The Mentor

I should ask clear decision questions:

1. For Peru, should the final analysis use administrative regions, ANA hydrographic units, or hydrological sub-basins inside the three regions?
2. Should the final product be a flood susceptibility map, a flood risk map, or an intervention-priority map?
3. Should rehabilitation potential be part of the main risk model, or should it be a second-stage priority model?
4. Which validation evidence would you prefer if local hydrometric data are limited?
5. Who should provide the AHP pairwise comparisons, and how many expert rounds are realistic?
6. For Zimbabwe mining data, do we have local or institutional sources that can help validate the cadastre and satellite interpretation?

## 6. If The Mentor Asks: "Is The Document Ready?"

Suggested answer:

> It is ready for methodological feedback and data-source review, but I would not treat it as a final modelling protocol yet. The next step is to lock the study units, time window, validation data, and AHP weighting protocol.

## 7. If The Mentor Asks: "What Did You Change?"

Suggested answer:

> I prepared a reviewed version that adds official links, suitability notes, preprocessing requirements, methodological cautions, validation options, and unresolved decisions.

## 8. If The Mentor Asks: "What Is The Biggest Risk?"

Suggested answer:

> The biggest risk is not lack of data alone. It is comparability. Zimbabwe is defined as a catchment and Peru as a larger administrative region, so the modelling unit must be made consistent before normalization, weighting, and comparison.

Another important answer:

> A second risk is mining-data reliability. Official mining rights need to be separated from actual mining disturbance, especially where cadastral data are incomplete or provisional.

## 9. Short Closing Statement

I can close the discussion with:

> My conclusion is that the framework is solid, but the modelling phase should start only after we finalize the spatial unit, temporal window, validation dataset, data-access constraints, and expert-weighting protocol. I would appreciate your guidance on these decisions before I move from data inventory to GIS implementation.

## 10. Very Short Version

If I only have one minute:

> I reviewed the inventory and added official dataset links, suitability notes, preprocessing requirements, AHP-MCDA cautions, mining-data caveats, rehabilitation criteria, and validation options. The framework is suitable for mentor review, but before modelling we still need to confirm the modelling unit, time window, validation data, and AHP weighting process. The most important methodological cautions are that mining concessions are not active mining footprints, RUSLE is an erosion-screening method rather than a sediment-delivery model, and AHP weights need expert input plus sensitivity analysis.
