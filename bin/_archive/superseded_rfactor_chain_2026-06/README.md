# Superseded R-factor chain (archived 2026-07-05)

These 13 scripts belong to the deprecated V1/V2 R-factor investigation
(IFPM-074/079/080/081/082), paused since June 2026. The deprecated output
products (`a_mean`, `a_low_R50`, `a_high_R510`, `r_factor/`, `r_factor_v2/`,
`v2_rfactor/`) were physically deleted 2026-07-01. These scripts remain as
historical provenance only; they are not part of the active pipeline.

## Why archived

- The V1 CHIRPS R-factor used a wrong Renard-Freimund predictor and an invented
  break; the V2 "smoother R resolves bimodality" premise was invalidated.
- Two scripts already carried `raise SystemExit("DEPRECATED...")` guards.
- Several read output directories that no longer exist on disk.

## Important dependency (do NOT delete this archive)

`derive_v1_usle_soil_loss.py` is the provenance of
`outputs/v1_usle_soil_loss/a_structure_K_LS_C_30m.tif`, which **is still
consumed by 4 active scripts**:

- `bin/criteria/build_boundary_v1_criteria_stack.py`
- `bin/criteria/build_pe1_criteria_stack.py`
- `bin/factors/derive_peru_pilot_usle_soil_loss.py` (mirrors its logic)
- `bin/criteria/build_era5_rfactor_raster.py`

That raster already exists on disk, so the active chain does not need to
re-run `derive_v1_usle_soil_loss.py`. But this archive must be retained as the
record of how `a_structure` was produced.

## Files

| script | role | IFPM |
|---|---|---|
| derive_v1_chirps_rfactor.py | V1 R-factor (CHIRPS MFI, deprecated) | 074 |
| derive_v1_usle_soil_loss.py | V1 USLE A (deprecated; provenance of a_structure) | 077 |
| derive_v2_rfactor_candidates.py | V2 smoother R candidates | 079 |
| derive_v2_usle_soil_loss.py | V2 USLE A + hotspot survival | 080 |
| compare_v2_rfactor_candidates.py | V2 R candidate comparison CSVs | 079 |
| compute_era5_empirical_rfactor.py | ERA5 EI30 empirical R | 082 |
| explore_rfactor_methods.py | 4-method R exploration (superseded by 082) | 081 |
| verify_ls_factor_exponents.py | one-off LS exponent literature check | 080 |
| plot_v2_rfactor_comparison_board.py | V2 R comparison board | 079 |
| plot_era5_empirical_rfactor_board.py | ERA5 R board | 082 |
| plot_era5_rfactor_raster_board.py | ERA5 R raster board | 082 |
| plot_rfactor_exploration_board.py | R exploration board | 081 |
| plot_v1_usle_soil_loss_board.py | V1 USLE soil-loss board (inputs deleted) | 077 |
