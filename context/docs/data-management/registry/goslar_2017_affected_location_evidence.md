# Goslar 2017 affected-location evidence

- Dataset id: `goslar_2017_affected_locations_v1`
- Data class: `LOCAL_DATA` with derived `OUTPUT`
- Status: `provisional`
- Claim level: `validation_candidate`
- Event window: 24-26 July 2017; Goslar peak/catastrophe-alarm date 26 July 2017
- Study area: Goslar Altstadt and Theresienhof, Lower Saxony, Germany
- Raw/curated catalog: `data/validation/goslar_2017_affected_locations_v1/source_locations.json`
- Derived outputs: `outputs/goslar_2017_affected_location_evidence/`
- Reusable: internally reusable with source attribution and the stated positional/claim limits
- PIM inclusion: no; the current PIM weights remain unchanged

## Intended use

Build a location-based historical-event consistency check by positioning officially reported
affected places and sampling the current provisional Goslar PIM. This is preferable to treating
an unverified satellite or regulatory flood polygon as event truth. The points are positive
affected-place samples, not a complete inundation footprint or a representative affected/unaffected
sample.

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
- Purpose: present-day reference placement of officially named locations
- Precision: bridge/facility centroids are approximately 5-30 m; street and square positions are
  representative centroids and may not coincide with the exact damaged building, overflow point,
  evacuation address or full affected reach.
- Impact claims come from the official event sources, not from OpenStreetMap.

The curated catalog retains the selected OSM object id or coordinate method for every location.
The selected coordinates must not be interpreted as parcel-level damage observations.

## Processing

Run:

```sh
.venv/bin/python bin/analysis/build_goslar_2017_affected_location_evidence.py
```

Inputs:

- curated location catalog described above;
- `outputs/srtm_1arcsec_goslar/priority_scenarios/scenarios/priority_goslar_direct_pim.tif`;
- fixed descriptive thresholds: High `PIM >= 0.60`, Very High `PIM >= 0.80`.

Outputs:

- `goslar_2017_affected_location_evidence.gpkg`, layer `affected_location_evidence`;
- `affected_location_pim_samples.csv`;
- `location_consistency_summary.json`;
- `goslar_2017_affected_locations_vs_pim.png`;
- `manifest.json` with input/output SHA-256 hashes, raster grid profile and limitations.

For each point the process records the sampled PIM value, display class, approximate distance to
the nearest High cell, maximum PIM within 100 m, source organisation/URL/locator, coordinate
source and positional limitation. NoData is not replaced with zero; a location without valid PIM
support fails the run.

## Claim boundary

Permitted interpretation:

> Do the currently documented 2017 affected-place samples fall within or near current PIM High
> areas?

Prohibited metrics/claims:

- flood-extent recall;
- flooded/non-flooded accuracy;
- intersection over union;
- false-positive flood area;
- validated PIM or causal weight adequacy.

The first comparison keeps weights frozen. If these 2017 samples are later used to tune weights,
they become calibration evidence and another event or spatial holdout is required for validation.

## Location sensitivity update (2026-09-07)

The display label is now “Goslar 2017 flood impacts and emergency response
(approximate locations)”. New diagnostic tables retain all nine records and separate
individual evidence types. `bin/analysis/goslar_2017_location_diagnostics.json` records
four provisional locality/reach groups and radii 0, 30, 50, 100 and 200 m.
The six lower-Abzucht records receive one combined group weight: records sharing a PIM cell are averaged first, then unique cells within each group,
then the four group fractions are averaged equally.
These groups are neither surveyed river reaches nor independent statistical samples.

`radius_location_samples.csv` preserves individual radius results;
`radius_group_background_comparison.csv` compares evidence types, reach groups,
equal-weight group means, all valid PIM cells, and valid cells within 1 km of the
reference locations. Background fractions measure High-cell availability, not
unaffected controls. The local background is conditioned on the selected sites.
At radius 0 use the containing pixel; at positive radii use High pixel centres.
NoData is excluded from background denominators. A High cell outside the local
background mask can support a location inside it; cells beyond the PIM domain are
unknown. All new comparisons are `diagnostic_only`, not accuracy estimates.
SciPy is required by the local diagnostic tool. Run the existing builder command
above, then the FullAudit and ReviewMap builders to refresh packaged copies:

```sh
.venv/bin/python bin/package/build_goslar_qgis_project_package.py
.venv/bin/python bin/package/build_goslar_compact_qgis_project.py
.venv/bin/python -m unittest discover -s tests -p 'test_goslar_2017_affected_location_evidence.py'
```

Source coordinate precision estimates are unverified, and the nominal event date
is not a per-location observation timestamp. No original catalog or PIM weights
are changed by this update.
