# Dataset Registry: Global Mining Polygons v2 (Zimbabwe Slice)

Status: downloaded and intersected with the Upper Mzingwane prototype boundary.

## Dataset Identity

- Dataset id: `global_mining_polygons_v2_zimbabwe`
- Project role: satellite-interpreted mining land-use footprint for a Zimbabwe
  priority-map context overlay
- Study area: Zimbabwe / Upper Mzingwane prototype boundary
- Spatial unit: global polygons filtered to `ISO3_CODE = ZWE`, then clipped to the boundary
- Observation basis: mining-related land cover interpreted from 2019 Sentinel-2 imagery

## Source And Access

- Source organization: PANGAEA / IIASA FINEPRINT
- Dataset: Maus et al. (2022), Global-scale mining polygons (Version 2)
- DOI: `10.1594/PANGAEA.942325`
- Landing page: `https://doi.org/10.1594/PANGAEA.942325`
- Direct file: `https://download.pangaea.de/dataset/942325/files/global_mining_polygons_v2.gpkg`
- Access date: 2026-07-14
- Licence: CC BY-SA 4.0
- Account required: no
- Reported validation: overall accuracy 88.3%; mine-class user accuracy 97.2%

## Acquisition

- Destination: `data/raw/global_mining_polygons_v2_zimbabwe/global_mining_polygons_v2.gpkg`
- Command:
  `curl -L -o data/raw/global_mining_polygons_v2_zimbabwe/global_mining_polygons_v2.gpkg <direct-file-url>`
- Derived outputs: `outputs/slide_ready_figures/zimbabwe_evidence_overlays/`

## Claim Boundary

The polygons represent visible mining-related land use, including large-scale and some artisanal
or small-scale mining. They do not identify legal mining titles, current operational status, or
ASM ownership. They may be shown as `mapped mining land-use footprint`, not as verified active ASM
sites or official mining claims.

The dataset is non-exhaustive. Its interpretation campaign was limited to a 10 km buffer around
34,820 source mining coordinates from the S&P metals and mining database. The six intersections
inside the working boundary therefore mean six mapped footprints in this dataset, not that the
study area contains only six mining sites. The available attributes do not distinguish large-scale
mining from ASM.

## Files

- Actual size: 24,657,920 bytes
- SHA-256: `6936e2743a21ba952b4de3e4b6f77099a0aa4479f7e2639d9d1b0787876a3ea1`
- Global feature count: 44,929
- Zimbabwe feature count: 320
- Features intersecting the working boundary: 6
- Mapped mining land-use area inside the working boundary: 1.832867 km2
- Derived layer: `outputs/slide_ready_figures/zimbabwe_evidence_overlays/zimbabwe_mapped_mining_footprints.gpkg`

The official Zimbabwe Mining Cadastre remains unsuitable for bulk use because its public portal
states that records are provisional and the map/download service is not openly available. The
IPIS 2019 Runde Valley ASM dataset is a useful regional source, but its WFS endpoint was unavailable
during the 2026-07-14 check and its coverage may not intersect Upper Mzingwane.
