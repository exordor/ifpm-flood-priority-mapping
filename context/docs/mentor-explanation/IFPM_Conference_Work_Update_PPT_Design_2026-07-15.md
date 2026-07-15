# IFPM conference work update PPT design

I will use this draft to show the work I have completed, not to present a final thesis claim.
The audience should leave with three points: I have built an end-to-end spatial workflow; I have
produced traceable prototype results for Peru and a secondary Zimbabwe comparison; and the
remaining limits are mainly evidence and validation gaps rather than a missing processing chain.

## Story and scope

The deck follows the working process: study-area framing, data collection, preprocessing,
criterion construction, weighted overlay, interpretation, packaging, validation diagnostics, and
remaining data gaps. Peru is the main case. Zimbabwe appears only after the Peru result to show
that the workflow has also been implemented in a second setting with weaker evidence.

The deck will contain 14 editable slides:

1. My completed IFPM work
2. The workflow now runs from source data to reviewable GIS results
3. Peru is the active case; Zimbabwe is a secondary method comparison
4. I assembled and governed the spatial data stack
5. I converted source datasets to comparable analysis layers
6. Five criteria connect the raw evidence to the priority map
7. The five Peru criterion maps are complete
8. The Peru weighted map identifies relative priority, not validated flood risk
9. Contribution and overlay maps explain why locations receive higher scores
10. The Zimbabwe workflow is complete but its evidence is weaker
11. The outputs are directly reviewable in QGIS and reproducible from manifests
12. Current event records support a diagnostic check, not validation
13. The remaining data gaps are specific and prioritised
14. The completed work establishes a usable prototype and a clear next evidence step

## Visual and wording rules

Existing report figures and briefing boards are the primary visuals. Slides use plain language,
first-person statements, one claim per page, and editable text. Internal experiment identifiers,
engineering gate names, and unsupported AHP-consistency claims do not appear. Each result slide
states its evidence boundary once in a short footer. The design leaves space for the mentor to add
context or conclusions.

## Evidence boundaries

The Peru result uses the current five-criterion direct-weight scenario. It is described as a
relative-priority prototype. The SINPAD comparison is a sparse point co-location diagnostic.
Zimbabwe is described as a secondary completed workflow with weaker mining, socioeconomic, and
validation evidence. No slide calls either map a validated flood-risk or intervention-decision
product.

## Deliverables and checks

The final editable PPTX will be stored under `context/presentations/`. Its source module and all
temporary renders will remain outside the repository. Every slide will be rendered and checked for
overlap, clipping, legibility, source accuracy, and scientific claim boundaries before handoff.
