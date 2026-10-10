# Dataset Registry: SoilGrids 250m Sediment Candidate

Status: used 2026-07-13 for the Zimbabwe V1 K-factor (Zimbabwe background only). Read remotely by
windowed HTTP from the ISRIC VRT collection; no local raw download.

## Dataset Identity

- Dataset id: `soilgrids_250m_sediment_candidate`
- Short name: SoilGrids 250m (ISRIC)
- Project role: soil erodibility K for the USLE/RUSLE sediment-risk factor
- Study area: Zimbabwe V1 working catchment
- Spatial unit or mask: SoilGrids global 250 m grid, clipped to the V1 bounding box
- Temporal coverage: SoilGrids contemporary soil properties

## Source And Access

- Source organization: ISRIC - World Soil Information
- Source URL: `https://files.isric.org/soilgrids/latest/data/` (VRT collection);
  SoilGrids page `https://www.isric.org/explore/soilgrids`
- Product/version: SoilGrids 250m, `latest` at the access date; clay, silt, sand and organic
  carbon mean layers at six depth slices
- Access date: 2026-07-13
- Access method: windowed HTTP read of the VRTs for the V1 bounding box; the source CRS is read
  from each VRT and every property/depth window is reprojected to the clay 0-5 cm window
- Licence or terms: CC BY 4.0; attribution to ISRIC required

## Processing And Use

- Scripts: `bin/factors/derive_v1_soilgrids_kfactor.py`, `bin/criteria/build_v1_soil_k_factor.py`
- Derived outputs: `outputs/soilgrids_250m_sediment_candidate/` (`k_factor_0_5cm_250m.tif`,
  `k_factor_0_30cm_avg_250m.tif`, `k_factor_diagnostics.json`) and
  `outputs/srtm_1arcsec_zimbabwe_prototype/soil_k_factor/`
- Method: Williams (1995) K from clay/silt/sand/organic carbon
- Result: V1 0-5 cm K range 0.134-0.248 US units; 59,006 valid native-grid cells inside the
  rasterized boundary
- Checksum: not recorded
- Known limitations: 250 m resolution is much coarser than the 30 m terrain grid; the
  pedotransfer function choice changes absolute K values; the `/latest/` endpoint is mutable, so
  exact upstream reconstruction is not guaranteed.
