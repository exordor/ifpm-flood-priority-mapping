# Dataset Registry: Goslar official hydrology, flood context, and infrastructure v1

- Dataset id: `goslar_official_hydrology_and_flood_data`
- Status: downloaded 2026-08-17. The WRRL basin union is the Goslar chain boundary
  (`goslar_wrrl_basin`) and the OSM facilities feed the critical-infrastructure
  component; the HWRM layers, the NLWKN report and the Abzucht HQextrem map are context only.
- Access date: 2026-08-17 (Abzucht HQextrem PDF: received 2026-09-08)
- Study area: `goslar_harz_2024_focus_extent` and its 12 km context buffer
- Reproducible command:
  `.venv/bin/python bin/acquire/pull_goslar_official_hydrology_flood_infrastructure.py`
- Local path: `data/raw/goslar_official_hydrology_and_flood_data/`
- Event report: `data/validation/goslar_harz_2024_focus_area/official_event_and_hazard_data/`
- Derived outputs: `outputs/goslar_official_hydrology_and_flood_data/`
- Checksum manifest: `outputs/goslar_official_hydrology_and_flood_data/source_lineage.json`

## Sources

1. **NLWKN July 2017 flood report**
   - URL: https://www.nlwkn.niedersachsen.de/download/124949/Hochwasserbericht_Juli_2017.pdf
   - Local file: `NLWKN_Hochwasserbericht_Juli_2017.pdf`
   - Role: official event narrative, precipitation totals, gauged peaks and
     return-period context for the July 2017 event.
   - Important values: the precipitation centre was near Goslar/Bad Harzburg;
     Eckertalsperre recorded 304 mm in the event window and Schladen/Oker
     reached 357 cm on 26 July 2017.

2. **WRRL drainage basins and river-segment network**
   - URLs:
     https://www.umweltkarten-niedersachsen.de/Download_OE/WRRL/DrainBasin_Waterbody_LOCAL.zip
     and https://www.umweltkarten-niedersachsen.de/Download_OE/WRRL/WFD_RWSEG_LOCAL.zip
   - Role: official water-body/drainage-basin polygons and river segments. The
     focus extent overlaps seven basin/water-body polygons, led by `Abzucht`
     (13.85 km²), `Granetalsperre` (4.62 km²), `Grane` (3.22 km²), and
     `Okertalsperre` (0.47 km²).
   - Derived layers:
     `outputs/goslar_official_hydrology_and_flood_data/goslar_wfd_drainage_basins_focus_overlap.gpkg`
     and the chain boundary
     `outputs/goslar_official_hydrology_and_flood_data/goslar_official_hydrologic_reference_boundary.gpkg`
     (`goslar_wrrl_basin`, union of the seven polygons, 153.779 km²).

3. **HWRM-RL Oker and Innerste flood-hazard boundaries**
   - URLs:
     https://www.umweltkarten-niedersachsen.de/Download_OE/HWRM-RL/Daten/HWRM-RL_Daten_Oker.zip
     and https://www.umweltkarten-niedersachsen.de/Download_OE/HWRM-RL/Daten/HWRM-RL_Daten_Innerste.zip
   - Role: independent scenario flood-hazard boundary context (Oker HQ20/HQ100/
     HQextrem; Innerste HQ25/HQ100/HQextrem).
   - Mapped areas within the focus + 12 km context: about 1.23-2.76 km² per scenario.
   - Derived layer:
     `outputs/goslar_official_hydrology_and_flood_data/goslar_hwrm_flood_hazard_boundaries_12km.gpkg`
   - These are modelled regulatory scenarios, not the observed July 2017 inundation footprint.

4. **OpenStreetMap critical-infrastructure candidates**
   - Source: Overpass query for schools, hospitals/healthcare, emergency
     facilities, fire/police stations, works, substations and railway stations
     in Landkreis Goslar.
   - Local snapshot: `osm_goslar_infrastructure_overpass.json`
   - Licence: ODbL, © OpenStreetMap contributors.
   - Role: critical-infrastructure component of the Goslar chain (proximity to 375 filtered
     facilities in seven classes: substations, schools, fire stations, works, police, hospitals,
     railway stations; 2 km linear decay), replacing the WorldCover built-up proxy since
     2026-08-17. Filtered layer: `osm_goslar_infrastructure_candidates.gpkg`. Not an official
     facility inventory.

5. **Abzucht flood-hazard map HQextrem (NLWKN)**
   - Local file: `data/raw/goslar_official_hydrology_and_flood_data/Abzucht_Blatt01_HWGK_L.pdf`,
     5,686,154 bytes, SHA-256 `e7c7cf5fa23c83f4a5720e1388759744dabb930002d7d553d546b3d56ff289bb`.
     Project-supplied copy, received 2026-09-08.
   - Publisher URL (identified via the official 2019 link list; publisher copy not hash-compared):
     https://www.umweltkarten-niedersachsen.de/Download_OE/HWRM-RL/Abzucht/Abzucht_Blatt01_HWGK_L.pdf
     Sibling sheets HWGK_H/HWGK_M and HWRK_L/HWRK_H/HWRK_M exist.
   - Content: one-page *Hochwassergefahrenkarte HQextrem*, Abzucht, dated 31.12.2019, 1:25,000,
     ETRS 1989 UTM Zone 32N; inundation boundary and depth classes 0-0.5, >0.5-1, >1-2, >2-4, >4 m.
     Scenario map, not an observed 2017 footprint. Redistribution licence not verified.

## Related public sources (not downloaded)

- City of Goslar flood areas (HQ100; Abzucht provisional protection dated 01.04.2026):
  https://www.goslar.de/wirtschafts-und-zukunftsort/klima-umwelt-gewaesserschutz/gewaesserschutz/ueberschwemmungsgebiete-innerhalb-der-stadt-goslar
- Official announcement (HQ100, six 1:5,000 work maps held by the city, 1:25,000 overview):
  https://www.goslar.de/fileadmin/media-goslar/standort/gewaeserschutz/uesg/mbl-2026-139.pdf
- NLWKN live service
  https://www.umweltkarten-niedersachsen.de/arcgis/rest/services/HWSchutz_wms/MapServer :
  layers 17/18/19 frequent/HQ100/extreme hazard vectors; 20/21/22 inland depth map layers;
  39 provisional regulatory zones. A bbox query to 17-19 returned Oker, not a separate Abzucht
  feature.
- LGLN DGM1 (1 m COG, 1 km tiles, NoData -9999, CC-BY-4.0):
  https://dgm.stac.lgln.niedersachsen.de/collections/dgm1 ; Goslar tile
  `dgm1_32_598_5752_1_ni_2018` dated 2018-04-08.
- LGLN OpenGeoData catalogue (DOP imagery, building footprints):
  https://lgln-geodaten.niedersachsen.de/startseite/vertrieb_support/geodaten_marktplatz/opengeodata/opengeodata-220509.html
- LGLN open-data hub: https://ni-lgln-opengeodata.hub.arcgis.com/ (product pages returned HTTP 403).

## Known limitations

- A full upstream contributing area would need WRRL polygons combined with DEM delineation.
- No machine-readable 15-minute 2017 gauge time series was found.
- OSM infrastructure includes many micro-features (especially fire hydrants); only the seven
  filtered classes are used.
