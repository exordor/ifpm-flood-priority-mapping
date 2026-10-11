# Dataset Registry: MapBiomas Peru Collection 3 Change Pilot

Status: downloaded 2026-08-05 for the former Peru study area (frozen, `peru_former`).

## Dataset Identity

- Dataset id: `mapbiomas_peru_collection3_peru_former`
- Short name: MapBiomas Peru Collection 3 annual LULC
- Project role: replace single-date BV and BE state proxies with observed annual land-cover transitions
- Study area: former Peru study area (frozen), boundary `peru_former`
- Spatial unit or mask: 30 m EPSG:32718 grid of the former Peru study area
- Temporal coverage: stable-window pilot years 2014-2016 and 2022-2024; source series is available annually from 1985 to 2024

## Source And Access

- Source organization: MapBiomas Peru
- Source URL or portal: `https://peru.mapbiomas.org/en/colecciones-de-mapbiomas-peru/`
- Product/version: Collection 3, integration v1, annual land-cover and land-use classification
- Access date: 2026-08-05
- Access method: direct public GeoTIFF download
- Licence or terms: Creative Commons CC-BY; source attribution required
- Citation requirement: `MapBiomas Peru Project - Collection 3 of the Annual Land Cover and Land Use Series for Peru, acquired 2026-08-05 through https://peru.mapbiomas.org/`

## Acquisition

- Source artifact names:
  - `peru_collection3_integration_v1-classification_2014.tif`
  - `peru_collection3_integration_v1-classification_2015.tif`
  - `peru_collection3_integration_v1-classification_2016.tif`
  - `peru_collection3_integration_v1-classification_2022.tif`
  - `peru_collection3_integration_v1-classification_2023.tif`
  - `peru_collection3_integration_v1-classification_2024.tif`
- Download command or manual steps: `bin/data/download_peru_former_mapbiomas_change.sh`

## Download Record

- Attempt date: 2026-08-05
- Archive state: six of six downloaded and verified

## Files

- Checksum values:
  - 2014: `90449fcc0c53dfccfdbec17bf577410580509287bfbb990d3ae53aaf9707fd47`
  - 2015: `adf8760ff08f05de5aa1189d0bcdc25ab821def20876e4e2ec36d72d8c698c4c`
  - 2016: `2fb25a794c8af2827a2d7424c72220bedff6cb9b7eddd401b65a15c66f8c9b19`
  - 2022: `00fae2cc33f1dadf65adc821b4764eb07c1e69952a6329a9c91fcb16fed881cf`
  - 2023: `6694fead757601a8ec8532ec73f057b7155326966e7b2c68fb29bdb99c5816cc`
  - 2024: `307b17670cdd441f3457da6a47c48277b40d4e33ced3a4843daa509b53db4a21`
- Files: six GeoTIFFs and six `.sha256` sidecars, 634,310,355 bytes in total
- File-count evidence: six readable single-band GeoTIFFs
- CRS or georeferencing checked: yes; all six rasters are EPSG:4326 with identical extent and approximately 30 m angular resolution
- Geometry/raster integrity checked: yes; all six opened successfully and were aligned to the EPSG:32718 reference grid with 100% study-area coverage

## Processing And Use

- Raw data path: `data/raw/mapbiomas_peru_collection3_peru_former/`
- Derived output path: `outputs/peru_former_mapbiomas_collection3_change/`
- Scripts or commands used: download script above and `bin/factors/derive_peru_former_mapbiomas_change.py`
- Standardization/preprocessing notes: categorical classes are aligned to the 30 m reference grid with nearest-neighbour resampling; 2014-2016 and 2022-2024 are each reduced by pixel majority before change detection
- Known limitations: 30 m thematic classifications are recommended by MapBiomas for use up to approximately 1:100,000; class changes can include classification uncertainty and require a transition-stability rule
- Use: temporal evidence for BV and the built-up/agricultural parts of BE
