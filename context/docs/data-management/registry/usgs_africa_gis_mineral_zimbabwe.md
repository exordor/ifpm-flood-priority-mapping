# Dataset Registry: USGS Africa GIS Mineral Industries (Zimbabwe Prototype)

Status: downloaded 2026-07-03 for the Zimbabwe V1 mining criterion (Zimbabwe background only).

## Dataset Identity

- Dataset id: `usgs_africa_gis_mineral_zimbabwe`
- Short name: USGS Africa GIS Geodatabase (mineral industries)
- Project role: known mines / deposits / facilities / exploration sites reference layer for the
  Zimbabwe mining-pressure criterion. An upgrade over the OSM quarry/industrial proxy.
- Study area: Zimbabwe / Upper Mzingwane Catchment prototype slice (V1)
- Spatial unit or mask: filter the Africa-wide geodatabase to Zimbabwe, then clip to V1 boundary
- Temporal coverage: data compiled 2008–2019 (USGS data release published 2021-08-13)

## Source And Access

- Source organization: U.S. Geological Survey (USGS)
- Source portal: USGS ScienceBase catalog item `607611a9d34e018b3201cbbf`
- Source URL:
  - Landing page: `https://www.sciencebase.gov/catalog/item/607611a9d34e018b3201cbbf`
  - USGS data catalog: `https://data.usgs.gov/datacatalog/data/USGS:607611a9d34e018b3201cbbf`
  - Direct file: `Africa_GIS.gdb.zip`
    `https://www.sciencebase.gov/catalog/file/get/607611a9d34e018b3201cbbf?f=__disk__30%2F8a%2Fb1%2F308ab140de2e0a1384172068209374d19ae4a65a`
- Product/version: Compilation of Geospatial Data (GIS) for the Mineral Industries and Related
  Infrastructure of Africa (USGS data release)
- DOI: `10.5066/P97EQWXP`
- Access date: 2026-07-03
- Access method: direct HTTPS download from ScienceBase; no login required
- Licence or terms: public domain (USGS work). Cite the USGS data release and DOI.
- Citation requirement: cite DOI 10.5066/P97EQWXP and the USGS data release title

## Acquisition

- Local path: `data/raw/usgs_africa_gis_mineral_zimbabwe/`
- Download command: `curl -L -o data/raw/usgs_africa_gis_mineral_zimbabwe/Africa_GIS.gdb.zip "<direct file URL above>"`
- Files: `Africa_GIS.gdb.zip`, 138,139,197 bytes, SHA-256
  `bd00e2a1d8d0a6cbb37bb9179c6828170ae7bd37c1e6af40219b24404455be67` (computed 2026-10-10 from the local file)

## What This Dataset Is And Is Not

This dataset provides **known mineral facilities, deposits, exploration sites, and occurrences**
compiled by USGS from governmental and open sources. It is a **reference layer**, not an
active-mining-footprint map.

- IS: mine/deposit/facility points and polygons; mineral occurrence context; a structured,
  attributed, citable starting layer covering Zimbabwe.
- IS NOT: current ASM disturbance boundary; active vs inactive status; concession/title rights.

In the Zimbabwe V1 chain this layer enters the mining-pressure criterion as `mining_reference`
(known facilities/deposits), combined with the OSM quarry/industrial proxy. It is not an active
mining footprint.

## Relationship To Other Mining Sources

| Source | Role | Status |
|---|---|---|
| OSM quarry/industrial (Geofabrik) | weak proxy, currently the only V1 mining layer | in use |
| **USGS Africa GIS** | known mines/deposits/facilities reference | this note |
| Zimbabwe Mining Cadastre Portal | official titles/concessions | blocked: portal data provisional + registration required, not obtainable |
| INGEMMET (Peru Arequipa Region) | official ASM points (Peru side only) | former Peru study area (frozen) |
