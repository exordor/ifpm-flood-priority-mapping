# CHIRPS V1 Rainfall Comparison

Date: 2026-06-13

Status: completed for mentor-review rainfall sensitivity. This is not an AHP overlay, flood-risk
map, intervention-priority map, or final thesis-boundary claim.

## Purpose

The previous CHIRPS blocker was that a single rainfall temporal window and timestep had not been
chosen. The current step resolves that by comparing several plausible rainfall interpretations
side by side:

- annual climate background;
- recent annual background;
- recent annual anomaly;
- long-term rainy-season accumulation;
- recent rainy-season accumulation;
- recent rainy-season anomaly;
- recent monthly rainfall peak;
- recent pentad rainfall peak;
- one recent daily RNL-derived peak.

The goal is to show the mentor how the rainfall evidence changes under different definitions
before any criterion is selected for scoring.

## Data Scope

Dataset id: `chirps_v3_zimbabwe_prototype`

Raw data path: `data/raw/chirps_v3_zimbabwe_prototype/`

Downloaded inputs:

- 44 annual Africa GeoTIFFs for 1981-2024.
- 215 monthly Africa GeoTIFFs for November-March rainy seasons 1981/82-2023/24.
- 150 pentad Africa GeoTIFFs for November-March rainy seasons 2019/20-2023/24.
- 152 daily RNL COG-derived V1 bbox GeoTIFFs for 2023-11-01 to 2024-03-31.

Verification:

- 561/561 inputs readable by `rasterio`.
- CRS: `EPSG:4326`.
- Resolution: approximately `0.05 x 0.05` degrees.
- Total raw bytes recorded in manifest: `1,837,685,335`.
- SHA-256 recorded per file in
  `outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/chirps_v1_raw_file_manifest.csv`.

## Outputs

Main outputs:

- `outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/v1_rainfall_metric_summary.csv`
- `outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/v1_rainfall_metric_correlation.csv`
- `outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/mentor_v1_chirps_rainfall_comparison_board.png`
- `outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/mentor_v1_chirps_rainfall_comparison_board.pdf`
- `outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/mentor_v1_chirps_rainfall_caption.md`
- `outputs/chirps_v3_zimbabwe_prototype/rainfall_comparison/v1_chirps_rainfall_comparison_handoff.md`

Individual metric panels are also saved as `panel_<metric_id>.png/pdf` in the same output folder.

Scripts:

- `bin/acquire/plan_chirps_v1_rainfall_metrics.py`
- `bin/acquire/download_chirps_v1_rainfall_inputs.py`
- `bin/investigate/compare_chirps_v1_rainfall_metrics.py`
- `bin/visualize/plot_chirps_v1_rainfall_comparison.py`

## Key Results

V1 mean values:

| Metric | V1 mean | Unit | Meaning |
|---|---:|---|---|
| `annual_mean_1981_2024` | 583.45 | mm/year | long-term annual background |
| `annual_recent_mean_2020_2024` | 684.42 | mm/year | recent annual background |
| `annual_recent_anomaly_pct` | 17.55 | percent | recent annual anomaly |
| `rainy_season_mean_1981_2024` | 503.93 | mm/season | long-term Nov-Mar accumulation |
| `rainy_season_recent_mean_2019_2024` | 589.91 | mm/season | recent Nov-Mar accumulation |
| `rainy_season_recent_anomaly_pct` | 17.51 | percent | recent rainy-season anomaly |
| `rainy_season_monthly_peak_2019_2024` | 315.16 | mm/month | largest recent rainy-season month |
| `rainy_season_pentad_peak_2019_2024` | 162.24 | mm/pentad | largest recent rainy-season pentad |
| `daily_rnl_peak_2023_2024` | 28.29 | mm/day | derived daily RNL peak for one recent season |

Interpretation for mentor review:

- Long-term annual and long-term rainy-season patterns are almost the same spatial signal
  (`pearson_r` about `0.997`), so both may be redundant for a first prototype.
- Recent annual and recent rainy-season patterns are also very similar (`pearson_r` about
  `0.994`).
- Recent anomaly is positive across V1 in both annual and rainy-season definitions, with mean
  anomaly around `17.5%`.
- Pentad peak has weak spatial correlation with the long-term annual background (`pearson_r`
  about `0.034`), so short-duration rainfall tells a different story from annual climate.
- Daily RNL peak is useful as a sensitivity check, but it is derived by disaggregating
  pentad/monthly CHIRPS using ERA5 daily ratios and should not be treated as more authoritative
  than the monthly/pentad products.

## Decision Question

Ask the mentor:

Which rainfall interpretation should be considered for the first prototype criteria set?

Options to discuss:

- annual or rainy-season climate background;
- recent anomaly;
- monthly peak;
- pentad peak;
- daily RNL peak as sensitivity only;
- rainfall as context only until validation or event evidence is available.

## Boundaries And Blockers

- CHIRPS is about `0.05 degree`, much coarser than the 30 m SRTM terrain layers.
- CHIRPS must remain native-grid diagnostics or V1/sub-basin zonal summaries.
- Do not resample CHIRPS to the V1 30 m terrain grid for pixel-level scoring.
- Do not run AHP weights, weighted overlay, flood-risk interpretation, or intervention-priority
  interpretation from this package.
- V1 remains `accepted_with_waiver_for_controlled_prototype`, not the final thesis boundary.
