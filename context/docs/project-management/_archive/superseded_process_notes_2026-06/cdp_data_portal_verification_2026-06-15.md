# CDP Data Portal Verification 2026-06-15

Status: data-processing record. Verifies the reachability, login requirements, and download
mechanisms of the candidate and existing data portals before download/processing. Performed via
Chrome DevTools Protocol (Playwright driving the user's Chrome on port 9222) plus CKAN/API curl
checks. No dataset was bulk-downloaded except the EM-DAT Zimbabwe country profile (8688 bytes).

## Tools Used

- `bin/check_data_portals.py` - CDP-based portal check (screenshots + DOM link analysis).
- CKAN API curl for HDX resource verification.
- rasterio HTTP VRT windowed-read verification for SoilGrids.
- Report: `outputs/data_portal_check/portal_check_report.json` + PNG screenshots.

## Findings By Portal

### SoilGrids (files.isric.org) - GO, immediately usable

- `https://files.isric.org/soilgrids/latest/data/` is an Apache directory listing.
- Per-property subdirectories (clay, silt, sand, soc, bdod, cec, cfvo, nitrogen, ocd, ocs,
  phh2o, landmask, wrb) each contain `_mean.vrt` / `Q0.05.vrt` / `Q0.5.vrt` / `Q0.95.vrt` at the
  six standard depth slices.
- No login. VRT is cloud-optimised; rasterio reads a V1-sized window via HTTP range requests
  without downloading the global raster.
- CRS: Interrupted Goode Homolosine (ESRI:54017), 250 m, int16, NoData -32768, values stored x10.
- Action: preflight mechanism corrected from "bulk download" to "windowed VRT HTTP read". K-factor
  already produced (see `soilgrids_v1_kfactor_processing_2026-06-15.md`).

### EM-DAT - GO, route changed

- Old HDX dataset id `emdat-international-disaster-database` is 404 (removed).
- HDX now distributes per-country profiles. Zimbabwe profile:
  `emdat-country-profiles-zwe`, 8688 bytes XLSX, anonymous direct download, updated 2026-06-13.
- Downloaded to `data/raw/emdat_public_validation_candidate/emdat_country_profile_zwe_2026-06-13.xlsx`.
- SHA-256: `46b76917a82f52b7849134664b75bb4d3b36e4219cf8d901c7328326e7b08884`.
- emdat.be full database still requires registration; the HDX country-profile route is the public
  path and is sufficient for Zimbabwe temporal/event-magnitude context.
- Action: EM-DAT registry URL corrected; download complete.

### GloFAS - DOWNGRADED, not publicly accessible as assumed

- NOT on the Climate Data Store: CDS catalogue returns 139 datasets, zero containing "glofas";
  all `cems-glofas-*` dataset URLs return 404. The preflight assumption (CDS API + `~/.cdsapirc`)
  was wrong.
- GloFAS moved to the Copernicus EMS portal (`global-flood.emergency.copernicus.eu`), which
  requires a separate account (not the CDS account).
- Public products on the EMS portal are FORECASTS (medium-range, seasonal, impact) and GFM
  monitoring, NOT the historical reanalysis needed for 1985-2024 validation.
- Historical river-discharge reanalysis likely requires ECMWF MARS access (restricted to member
  states).
- Action: GloFAS registry/preflight downgraded from "Tier A public candidate" to "historical
  data access restricted; possibly infeasible without ECMWF access". Validation layer should rely
  on EM-DAT + DFO (already held) + optional Sentinel-1 SAR instead.

### Existing Sources (re-verified, all working)

- CHIRPS (chc.ucsb.edu): 200, anonymous, CC licence visible. The "login_likely" flag was a
  false positive from nav-bar text.
- HydroSHEDS: 200; some products may require registration.
- ESA-WorldCover: 200, anonymous.
- WorldPop: 200, anonymous, CC licence visible.
- HDX: 200, anonymous download works (login link is header-only).
- All already-used sources remain accessible.

## Implications For The Data Plan

- SoilGrids K-factor: done (windowed read; no bulk download needed).
- EM-DAT Zimbabwe profile: done (anonymous download).
- GloFAS: defer; rely on other validation sources.
- CDS account (which the user logged into) is useful for ERA5/ERA5-Land if a rainfall
  cross-check against CHIRPS is later desired, but not for GloFAS.

## Cross-References

- SoilGrids K-factor: `soilgrids_v1_kfactor_processing_2026-06-15.md`.
- Original scaffolding: `context/docs/data-management/registry/soilgrids_250m_sediment_candidate.md`,
  `emdat_public_validation_candidate.md`, `glofas_public_validation_candidate.md` (these record the
  pre-verification assumptions and should be read alongside this correction note).
- CDP screenshots: `outputs/data_portal_check/`.
