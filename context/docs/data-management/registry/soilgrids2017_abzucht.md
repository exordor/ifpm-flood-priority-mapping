# Archived SoilGrids 2017 Abzucht alternative

- Source: https://files.isric.org/soilgrids/former/2017-03-10/data/
- Product/version: superseded SoilGrids250m 2017-03-10, native WGS84 ~250 m;
  sand, silt, clay and organic carbon at standard depths 0/5/15/30 cm.
- Access date: 2026-09-14. Public HTTP range access, no account. ISRIC's 2017
  FAQ specifies ODbL; retain source attribution and derivative provenance.
- Documentation: https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_2017.html
  and https://isric.org/news/soilgrids-version-2017-services-communication
- Used by: the Abzucht soil-replacement scenario (`input_completion_v2`); fills soil K where the
  current SoilGrids version is masked (urban areas). It replaces the complete soil layer.
- Local path: `data/raw/soilgrids2017_abzucht/`
- Acquisition command: `.venv/bin/python bin/acquire/pull_abzucht_soilgrids2017.py`
  (HTTP range window reads; no whole global TIFF is fetched).
- Analysis command: `.venv/bin/python bin/analysis/complete_abzucht_inputs.py` (Williams K,
  trapezoidal integration at 0/5/15/30 cm).

## Files

- 16 source GeoTIFF clips and 16 XML metadata files, 389,541 bytes total. All native grids
  align (95 × 141 cells); each has 13,263/13,395 valid source cells.
- Raw `source_manifest.json` SHA-256:
  `0d02114f41d5a0ed9eab3d4c2f15b1e8d00d1ecb6e55100b3bad71952cdf7286`.
  Per-file byte sizes, SHA-256, source URLs, HTTP range headers and extent recorded there.
- Derived K is under `outputs/goslar_abzucht_display_rectangle_v1/input_completion_v2/`,
  never raw data. Soil K covers 561/561 HQ100 cells, 21,120/21,198 ring cells,
  and 29,136/29,315 display-rectangle cells. Residual gaps remain NoData.
- Known limitations: superseded version; wider coverage does not mean the 2017 predictions are
  more accurate than the current SoilGrids version.
