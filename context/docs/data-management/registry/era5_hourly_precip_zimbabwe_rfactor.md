# ERA5 hourly precipitation (open-meteo) for V1 R-factor EI30 experiment

Dataset id: `era5_hourly_precip_zimbabwe_rfactor`

Status: downloaded 2026-06-19 for the Zimbabwe V1 R-factor experiment (Zimbabwe background only).

## Source
- Provider: open-meteo archive API (ERA5 reanalysis, ECMWF/Copernicus), no account required
- URL: `https://archive-api.open-meteo.com/v1/era5`
- Product: ERA5 single-level reanalysis, variable `precipitation` (mm, hourly)
- Licence: Copernicus ERA5 licence (public; open-meteo terms allow non-commercial research use)
- Access date: 2026-06-19

## Purpose
Empirical USLE/RUSLE R-factor (EI30) from hourly rainfall, used to choose between the two
literature R-factor ranges for Zimbabwe (HIGH ~1400-3700 vs LOW ~240-320). CHIRPS daily is not
storm-resolved, and GPM IMERG (half-hourly) needs a NASA Earthdata account.

## Coverage
- Spatial: V1 working catchment centroid, 6 compass points and a regular point grid across V1
  (lon 28.50-29.35, lat -20.96 to -20.03)
- Temporal: 2018-2023
- Resolution: hourly (ERA5 native). Hourly is coarser than 30-min breakpoint data, so the computed
  I30 and R are a lower bound on the true EI30 R.

## Files
- Local path: `data/raw/era5_hourly_precip_zimbabwe_rfactor/`
- 52 JSON responses (`era5_hourly_<point>_2018-2023.json`, `grid_<lon>_<lat>_2018-2023.json`),
  68,364,740 bytes in total
- Checksum: not recorded
- Derived raster: `bin/criteria/build_era5_rfactor_raster.py`
  (Script removed 2026-10-11; recover with `git show 6e2ed8b:bin/criteria/build_era5_rfactor_raster.py`.)

## Known limitations
ERA5 reanalysis precipitation can under-estimate convective storm intensity in semi-arid tropical
regions, so the empirical R is itself an estimate.
