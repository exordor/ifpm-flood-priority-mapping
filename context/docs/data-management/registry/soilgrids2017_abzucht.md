# Archived SoilGrids 2017 Abzucht alternative

- Classification: LOCAL_DATA; dataset id `soilgrids2017_abzucht`.
- Source: https://files.isric.org/soilgrids/former/2017-03-10/data/
- Product/version: superseded SoilGrids250m 2017-03-10, native WGS84 ~250 m;
  sand, silt, clay and organic carbon at standard depths 0/5/15/30 cm.
- Access date: 2026-09-14. Public HTTP range access, no account. ISRIC's 2017
  FAQ specifies ODbL; retain source attribution and derivative provenance.
- Documentation: https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_2017.html
  and https://isric.org/news/soilgrids-version-2017-services-communication
- Scope: existing Abzucht model grid plus small native-cell halo; read windows
  only. Never download multi-GB global files. HTTP 206/range support required;
  expected local clips <5 MB. Temporary attempts under data/tmp/soilgrids2017_abzucht/.
- Intended use: investigate whether older soil predictions cover masked urban
  areas; a separate version sensitivity, not recovered current SoilGrids values.
- Expected destination: data/raw/soilgrids2017_abzucht/.
- Steps: inspect source XML and HTTP range support, window-read 16 property-depth
  rasters and verify grids/units. Pin byte sizes/SHA-256 in source manifest.
  The analysis script derives K under outputs, using the existing Williams
  formula and documented trapezoidal integration of K at 0/5/15/30 cm.
- Reusable: conditional on successful range access and metadata/coverage checks.
- Acquisition command and actual checksum/file-size evidence will be added after
  the bounded attempt; unsuccessful attempts must be recorded explicitly.

- Acquisition command: `.venv/bin/python bin/acquire/pull_abzucht_soilgrids2017.py`.
- Analysis command: `.venv/bin/python bin/analysis/complete_abzucht_inputs.py`.
- First attempt stopped because the XML spells SOC units `g / kg`, not `g/kg`;
  parsing was corrected without changing the unit conversion (divide by 10 for %).
- Second attempt stopped at the organic-carbon window with
  `TIFFReadEncodedStrip() failed` / `Read error at scanline 15444`.
  No completed manifest was produced. Download now uses four independent small
  window requests, up to three attempts, and verified per-file receipts for resume.
  Incomplete data remain labelled `INCOMPLETE.txt`; no whole global TIFF is fetched.

## Verified result

- Final acquisition succeeded: 16 source GeoTIFF clips and 16 XML metadata files,
  389,541 bytes total. All native grids align (95 × 141 cells); each has
  13,263/13,395 valid source cells. Cached acquisition reopens and verifies hashes.
- Raw `source_manifest.json` SHA-256:
  `0d02114f41d5a0ed9eab3d4c2f15b1e8d00d1ecb6e55100b3bad71952cdf7286`.
  Per-file byte sizes, SHA-256, source URLs, HTTP range headers and extent recorded there.
- Derived K is under `outputs/goslar_abzucht_display_rectangle_v1/input_completion_v2/`,
  never raw data. Soil K covers 561/561 HQ100 cells, 21,120/21,198 ring cells,
  and 29,136/29,315 display-rectangle cells. Residual gaps remain NoData.
- Reusable as an attributed older-version sensitivity input. It replaces the
  complete soil layer, not just gaps; finite coverage is not evidence that 2017
  predictions are more accurate than the current SoilGrids version.
