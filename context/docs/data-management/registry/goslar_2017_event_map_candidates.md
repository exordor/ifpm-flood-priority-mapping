# Goslar 2017 event-map candidates

- Dataset id: `goslar_2017_event_map_candidates_v1`
- Access date: 2026-08-20
- Study area: Goslar, Lower Saxony, Germany
- Event window: 24-26 July 2017; Goslar peak/catastrophe-alarm date: 26 July 2017
- Destination: `data/validation/goslar_2017_event_map_candidates_v1/`
- Outputs: `outputs/goslar_2017_event_map_candidates_v1/`
- Status: downloaded 2026-08-20; HQ100 regulatory context for the Abzucht comparison; not part of the PIM score

## Result of the search

No publicly downloadable official vector representing the observed 2017 Goslar inundation
footprint was found. The closest map is page 16 of a 2022 World Heritage Watch report. Its
caption describes areas affected in 2017, but the source printed beneath the map is the Lower
Saxony provisional flood-zone service. The map is therefore not independent event observation.
It can be shown as post-event hydraulic/regulatory context, but it must not be used as ground
truth for accuracy, recall, or weight optimization. The surrounding text also says June 2017,
whereas the documented flood occurred in July, which further limits the report as event lineage.

The official NLWKN July 2017 report, City of Goslar flood-protection page and Goslar fire-brigade
report provide event chronology and named affected places. They do not publish a continuous
event-footprint vector. These location statements can support a separate affected-location
context layer.

## Sources and artefacts

1. World Heritage Watch report, May 2022
   - URL: `https://world-heritage-watch.org/LangberichtGoslar06-06-2022.pdf`
   - Local file: `world_heritage_watch_goslar_2022.pdf`
   - SHA-256: `df2a946d5db831bbb0c93b59f3505ed9f660f5a9f8a3e6e309f935193c3b0053`
   - Relevant page: 16
   - Licence: not established; cite the source.
   - The 2022 figure may differ from the current 2026 ArcGIS feature; no dated layer snapshot
     accompanies it.

2. NLWKN / Lower Saxony ArcGIS layer 39, current provisional regulatory flood zones
   - Service: `https://www.umweltkarten-niedersachsen.de/arcgis/rest/services/HWSchutz_wms/MapServer/39`
   - Query envelope: `10.25,51.77,10.57,51.98` in EPSG:4326
   - Returned features: Grane, Weddebach, Radau, Abzucht ST Goslar
   - Local file: `nlwkn_current_regulatory_flood_zones_goslar.geojson`
   - SHA-256: `150f20d34b35063f15dc27ffbe5155092c38928c1c53e5968f211df62a57c369`
   - Delivery geometry: full features intersecting the envelope, not clipped to it.
   - Service snapshot: `nlwkn_layer39_metadata_2026-08-20.json`, SHA-256
     `7d3618a03ae65d046ec91e0e73681465c88a4d081de4082808f9d4ad3ff5acce`.
   - Product vintages: Abzucht is a 2026 two-dimensional hydraulic HQ100 regulatory product;
     Radau and Grane records date from 2021, and Weddebach from 2015.
   - Attribution: Lower Saxony NLWKN; service metadata states copyright 2026.
   - Usage/legal-position note:
     `https://www.nlwkn.niedersachsen.de/hochwasser_kuestenschutz/hochwasserschutz/ueberschwemmungsgebiete/lagegenauigkeit-und-rechtsverbindlichkeit-44199.html`
   - Semantic boundary: current official HQ100 hydraulic/regulatory polygons, not a 2017
     event reconstruction or observed water extent.

3. Official event/context pages
   - NLWKN event documentation: `https://www.nlwkn.niedersachsen.de/startseite/hochwasser_kustenschutz/hochwasserschutz/hintergrundinformationen/dokumentation_von_hochwasserereignissen/winterhochwasser_2023_2024/dokumentation-des-juli-hochwassers-2017-in-sudniedersachsen-241752.html`
   - City of Goslar: `https://www.goslar.de/wirtschafts-und-zukunftsort/klima-umwelt-gewaesserschutz/hochwasserschutz-1`
   - Goslar fire brigade: `https://feuerwehr-goslar.de/einsatzberichte/hochwasser-2017-in-goslar/`

## Reproducible download

```sh
curl -fsSL 'https://world-heritage-watch.org/LangberichtGoslar06-06-2022.pdf' \
  -o data/validation/goslar_2017_event_map_candidates_v1/world_heritage_watch_goslar_2022.pdf

# The map is the second image on page 16:
pdfimages -f 16 -l 16 -j \
  data/validation/goslar_2017_event_map_candidates_v1/world_heritage_watch_goslar_2022.pdf page16
mv page16-001.jpg \
  outputs/goslar_2017_event_map_candidates_v1/unverified_2017_caption_map_from_regulatory_service.jpg

curl -fsSL \
  'https://www.umweltkarten-niedersachsen.de/arcgis/rest/services/HWSchutz_wms/MapServer/39?f=pjson' \
  -o data/validation/goslar_2017_event_map_candidates_v1/nlwkn_layer39_metadata_2026-08-20.json

curl -fsSLG \
  'https://www.umweltkarten-niedersachsen.de/arcgis/rest/services/HWSchutz_wms/MapServer/39/query' \
  --data-urlencode 'where=1=1' \
  --data-urlencode 'geometry=10.25,51.77,10.57,51.98' \
  --data-urlencode 'geometryType=esriGeometryEnvelope' \
  --data-urlencode 'inSR=4326' \
  --data-urlencode 'spatialRel=esriSpatialRelIntersects' \
  --data-urlencode 'outFields=*' \
  --data-urlencode 'returnGeometry=true' \
  --data-urlencode 'outSR=4326' \
  --data-urlencode 'f=geojson' \
  -o data/validation/goslar_2017_event_map_candidates_v1/nlwkn_current_regulatory_flood_zones_goslar.geojson
```

## Known limitations

- Neither source is an observed 2017 footprint. HQ100 polygons are used for scenario agreement
  only; if they are used to tune weights they cannot also validate.
- Not available: the modelled 2017 maximum inundation extent from the `Hydraulische
  Neuberechnung Abzucht (HGN 02/2021)` event run (about 40 m³/s); it would have to be requested
  from Stadt Goslar (Fachdienst Umwelt und Gewaesserschutz).
