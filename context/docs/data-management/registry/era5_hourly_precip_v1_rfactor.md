# ERA5 hourly precipitation (open-meteo) for V1 R-factor EI30 experiment

Dataset id: `era5_hourly_precip_v1_rfactor`

## Source
- Provider: open-meteo archive API (ERA5 reanalysis, ECMWF/Copernicus), no account required
- URL: `https://archive-api.open-meteo.com/v1/era5`
- Product: ERA5 single-level reanalysis, variable `precipitation` (mm, hourly)
- Licence: Copernicus ERA5 licence (public; open-meteo terms allow non-commercial research use)
- Access date: 2026-06-19

## Purpose
Exploratory experiment to compute an empirical USLE/RUSLE R-factor (EI30) from hourly rainfall,
in order to arbitrate the two incompatible literature R-families (HIGH ~1400-3700 vs LOW ~240-320)
identified in `context/docs/research-map/RESULTS.md` (§R-factor). CHIRPS daily is not storm-resolved and
cannot yield EI30; GPM IMERG (half-hourly) requires a NASA Earthdata account that is not available,
so ERA5 hourly via open-meteo is the best no-authentication high-temporal-resolution option.

## Coverage
- Spatial: V1 working catchment centroid + a small grid of points across V1 (lon 28.56-29.35,
  lat -20.96 to -20.03)
- Temporal: multiple years (e.g. 2018-2023) to get a multi-year mean R
- Resolution: hourly (ERA5 native). CAVEAT: hourly != 30-min breakpoint, so the computed I30 and
  R are a LOWER BOUND on the true EI30 R. This is acceptable for a family-arbitration experiment
  (order-of-magnitude), not for a quantitative validated R.

## Destination
`data/raw/era5_hourly_precip_v1_rfactor/` (LOCAL_DATA; gitignored)

## Reusability
Reusable: open-meteo is stable and free; the query is documented in the download script.

## Integrity caveat
ERA5 reanalysis precipitation can under-estimate convective storm intensity in semi-arid tropical
regions. The empirical R from ERA5 is therefore itself an estimate with its own uncertainty; it is
one more data point in the family comparison, not ground truth.
