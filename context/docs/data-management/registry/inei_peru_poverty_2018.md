# Dataset Registry: INEI Peru poverty map 2018

Status: downloaded on 2026-07-08 and Arequipa district table extracted.

## Dataset Identity

- Dataset id: `inei_peru_poverty_2018`
- Short name: INEI Mapa de Pobreza Provincial y Distrital 2018
- Data class: `LOCAL_DATA`
- Reusable download: yes
- Project role: district-level poverty context for response-capacity discussion;
  excluded from the current Peru PIM criterion
- Study area: Arequipa department, joinable by UBIGEO/district
- Spatial unit or mask: administrative district table, not gridded raster
- Temporal coverage: poverty map 2018; projected population field for 2020

## Source And Access

- Source organization: Instituto Nacional de Estadística e Informática (INEI)
- Source page:
  `https://www.gob.pe/institucion/inei/informes-publicaciones/3204872-mapa-de-pobreza-provincial-y-distrital-2018`
- Downloaded source artifact:
  `https://cdn.www.gob.pe/uploads/document/file/3340937/Anexo%20Estad%C3%ADstico.xlsx?v=1656708741`
- Access date: 2026-07-08
- Access method: public government file download, no login
- Licence or terms: public government publication; confirm redistribution terms
  before raw file release

## Download Plan

- Destination: `data/raw/inei_peru_poverty_2018/`
- Raw file:
  `data/raw/inei_peru_poverty_2018/anexo_estadistico_mapa_pobreza_2018.xlsx`
- Extracted Arequipa table:
  `data/raw/inei_peru_poverty_2018/arequipa_district_poverty_2018.csv`
- Scripts/commands:
  - `curl -L --fail --retry 3 --user-agent 'Mozilla/5.0' <source-url> -o data/raw/inei_peru_poverty_2018/anexo_estadistico_mapa_pobreza_2018.xlsx`
  - `.venv/bin/python bin/acquire/extract_inei_arequipa_poverty.py`

## Verification

- Download completed: yes
- Verification date: 2026-07-08
- Workbook size: 553,923 bytes
- Workbook SHA-256:
  `fcc465d75abe7f7e20107d67fc3a947d606e2176d0c00fecb02ceafcca913f00`
- Arequipa extracted records: 109 districts
- Expected output manifest:
  `outputs/inei_peru_poverty_2018/inei_arequipa_poverty_manifest.json`

## Processing And Use

- Raw data path: `data/raw/inei_peru_poverty_2018/`
- Derived output path: `outputs/inei_peru_poverty_2018/`
- Planned use:
  - join district-level poverty interval/rank by UBIGEO to Arequipa district
    boundaries;
  - export as district-level response-capacity context outside the current PIM;
  - report as district-scale context, not as cell-scale observed vulnerability.
- Key extracted fields:
  - `ubigeo`
  - `provincia`
  - `distrito`
  - `poblacion_proyectada_2020`
  - `pobreza_total_ci95_inferior`
  - `pobreza_total_ci95_superior`
  - `grupo_robusto`
  - `ubicacion_pobreza_monetaria_total`
- Known limitations:
  - district-level; cannot directly validate pixel-scale PIM variation;
  - 2018 poverty map may not reflect current mining-region conditions;
  - must not be called adaptive capacity or inserted into the PIM without an
    explicit weighting and temporal-alignment decision.

## Release Boundary

- May be committed: no raw workbook or CSV unless release permission is explicit
- May be used in public examples: aggregate or synthetic summaries only
- Public-safe summary available: this registry note and aggregate statistics
