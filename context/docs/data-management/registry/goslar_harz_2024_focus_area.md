# Dataset Registry: Goslar Harz 2024 focus area

Status: source files registered 2026-08-07. Defines the original ZLW focus extent (minimum
study-area anchor for Goslar).

## Dataset Identity

- Dataset id: `goslar_harz_2024_focus_area`
- Focus area: Goslar 2017 flood catchment and intended sensor study area, Harz,
  Lower Saxony, Germany
- Focus extent (layout): WGS84 10.3646-10.4194 E, 51.8544-51.9089 N
- Project role: Goslar focus-area context; not a PIM input

## Source And Access

Project-supplied source files, stored under
`data/validation/goslar_harz_2024_focus_area/source_materials/`:

1. `ZDIN-2024.goslar_catchment.qgz` - QGIS project (QGIS 3.22.7, saved
   2024-04-25) with drainage-basin layer references, a
   sensor-station CSV reference and print layouts. External data sources live
   on a Windows project path and are not bundled with the QGZ.
2. `ZLW2024.04.24_catchment_and_sensors.pdf` - QGIS print export (2023-06-12)
   titled "ZLW SENSORS & EINZUGSGEBEIT" showing the drainage basin, sensor
   locations and ATKIS water features.
3. `ZDIN_goslar_2017flood_intended_study_area.png` - ZDIN slide identifying
   the 2017 flood catchment (source: EWAZ Energie- und Wasserspeicher Harz,
   Massnahme 6: Hochwasserschutz Goslar) and the intended sensor study area.

- Access method: local files provided by the project; no download required
- Access date: 2026-08-07
- Checksums and sizes: `outputs/goslar_harz_2024_focus_area/source_registration_manifest.json`

## Processing And Use

- Evidence packet: `outputs/goslar_harz_2024_focus_area/event_evidence.csv`
- Focus extent layer: `outputs/goslar_harz_2024_focus_area/goslar_focus_extent.geojson`
- Spatial scope check: `outputs/goslar_harz_2024_focus_area/spatial_scope_check.json`
- Location map: `outputs/goslar_harz_2024_focus_area/comparison_maps/`
- Key facts:
  - The QGIS print-layout extent defines the Goslar focus box (10.36-10.42 E,
    51.85-51.91 N).
  - The ZDIN slide attributes the 2017 flood catchment to EWAZ Harz
    Hochwasserschutz Goslar (Massnahme 6).

## Known Limits

- The QGZ references external Windows-path data (DRAINAGE_BASIN_DE, sensor
  CSV) that is not bundled; sensor coordinates are not machine-readable in the
  PDF export.
- The focus extent is a project-layout reference box, not a mapped flood or
  hazard footprint.
- The ZDIN slide is a project attribution, not an official flood report.
