# Goslar 2017 affected-location evidence

- Dataset id: `goslar_2017_affected_locations`
- Status: compiled 2026-08-21; nine officially reported affected places, positioned with OSM;
  sampled against the Goslar PIM. Not part of the PIM score.
- Event window: 24-26 July 2017; Goslar peak/catastrophe-alarm date 26 July 2017
- Study area: Goslar Altstadt and Theresienhof, Lower Saxony, Germany
- Curated catalog: `data/validation/goslar_2017_affected_locations/source_locations.json`
- Derived outputs: `outputs/goslar_2017_affected_location_evidence/`

## Event-evidence sources

1. NLWKN, *Das Juli-Hochwasser 2017 im südlichen Niedersachsen*
   - URL: `https://www.nlwkn.niedersachsen.de/download/124949/Hochwasserbericht_Juli_2017.pdf`
   - Relevant evidence: report page 25 (PDF page 29), including the fully flooded historic
     Marktplatz and evacuation of a care home.
2. Freiwillige Feuerwehr Goslar, *Hochwasser 2017 in Goslar*
   - URL: `https://feuerwehr-goslar.de/einsatzberichte/hochwasser-2017-in-goslar/`
   - Relevant evidence: named response, evacuation and damage locations including Theresienhof,
     Neue Straße, Trollmönch, Domstraße, An der Abzucht, Glockengießerstraße and
     Knochenhauerstraße.
3. Stadt Goslar, *Hochwasserschutz*
   - URL: `https://www.goslar.de/wirtschafts-und-zukunftsort/klima-umwelt-gewaesserschutz/hochwasserschutz-1`
   - Relevant evidence: damage to the Abzucht wall and Moritz-von-Sachsen-Platz near
     Trollmönchbrücke.

## Coordinate source and precision

- Provider: OpenStreetMap Nominatim and Overpass
- Access date: 2026-08-21
- Portals: `https://nominatim.openstreetmap.org/search` and
  `https://overpass-api.de/api/interpreter`
- Licence: OpenStreetMap data, ODbL; attribute OpenStreetMap contributors
- Precision: bridge/facility centroids are approximately 5-30 m; street and square positions are
  representative centroids and may not coincide with the exact damaged building, overflow point,
  evacuation address or full affected reach.
- Impact claims come from the official event sources, not from OpenStreetMap.

The catalog keeps the OSM object id or coordinate method for every location.

## Processing

```sh
.venv/bin/python bin/analysis/build_goslar_2017_affected_location_evidence.py
(Script removed 2026-10-11; recover with `git show cc4f247:bin/analysis/build_goslar_2017_affected_location_evidence.py`.)
```

- Inputs: the catalog above;
  `outputs/goslar_pim_chain/priority_scenarios/scenarios/priority_goslar_direct_pim.tif`;
  thresholds High `PIM >= 0.60`, Very High `PIM >= 0.80`.
- Outputs: `goslar_2017_affected_location_evidence.gpkg` (layer `affected_location_evidence`),
  `affected_location_pim_samples.csv`, `location_consistency_summary.json`,
  `goslar_2017_affected_locations_vs_pim.png`, `manifest.json` (input/output SHA-256),
  `radius_location_samples.csv`, `radius_group_background_comparison.csv`.
- Per point: sampled PIM, class, distance to the nearest High cell, maximum PIM within 100 m,
  source and positional limitation. NoData is not replaced with zero.
- Radius check (2026-09-07): radii 0/30/50/100/200 m; four locality/reach groups defined in
  `goslar_2017_location_diagnostics.json` (next to this note) (the six lower-Abzucht records form one
  group), group fractions averaged equally and compared with all valid PIM cells and cells within
  1 km.

## Known limitations

- The points are affected places only, not an inundation footprint or an affected/unaffected
  sample, so recall, accuracy and IoU cannot be computed.
- Coordinate precision is approximate, and the event date is not a per-location timestamp.
