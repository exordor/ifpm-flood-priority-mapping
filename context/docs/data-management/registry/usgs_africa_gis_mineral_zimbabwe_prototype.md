# Dataset Registry: USGS Africa GIS Mineral Industries (Zimbabwe Prototype)

Status: downloaded for Zimbabwe V1 mining-criterion upgrade. Public-domain USGS data release;
the strongest openly downloadable mineral-facilities reference covering Zimbabwe.

## Dataset Identity

- Dataset id: `usgs_africa_gis_mineral_zimbabwe_prototype`
- Short name: USGS Africa GIS Geodatabase (mineral industries)
- Data class: `LOCAL_DATA`
- Reusable download: yes — public USGS ScienceBase release
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
- Account, registration, or approval needed: none
- Redistribution allowed: yes (public domain); still keep raw archive local-only per project rule

## Download Plan

- Intended destination: `data/raw/usgs_africa_gis_mineral_zimbabwe_prototype/`
- Expected file types: `Africa_GIS.gdb.zip` (zipped ESRI file geodatabase)
- Expected byte size: `138,139,197` bytes (~138 MB), confirmed via HTTP HEAD on 2026-07-03
- Download command: `curl -L -o data/raw/usgs_africa_gis_mineral_zimbabwe_prototype/Africa_GIS.gdb.zip "<sciencebase file url>"`
- Rate limits or quotas: none expected for ScienceBase public download
- Authentication handling: none
- Temporary path, if any: `data/tmp/usgs_africa_gis_mineral_zimbabwe_prototype/` for extraction
- Cleanup needed after extraction: keep the source zip; extract the geodatabase under data/tmp

## What This Dataset Is And Is Not

This dataset provides **known mineral facilities, deposits, exploration sites, and occurrences**
compiled by USGS from governmental and open sources. It is a **reference layer**, not an
active-mining-footprint map.

- IS: mine/deposit/facility points and polygons; mineral occurrence context; a structured,
  attributed, citable starting layer covering Zimbabwe.
- IS NOT: current ASM disturbance boundary; active vs inactive status; concession/title rights.

Per the project's criteria-design rule, this layer enters the mining-pressure criterion as
`mining_reference` (known facilities/deposits), combined with the existing OSM quarry/industrial
proxy. It does **not** become `active_mining_footprint` until a Sentinel-2/Landsat disturbance
layer is produced or official ASM data arrives (mentor 7/18 ask).

## Relationship To Other Mining Sources

| Source | Role | Status |
|---|---|---|
| OSM quarry/industrial (Geofabrik) | weak proxy, currently the only V1 mining layer | in use |
| **USGS Africa GIS** | known mines/deposits/facilities reference | **this download** |
| Zimbabwe Mining Cadastre Portal | official titles/concessions | blocked: portal data provisional + registration required, not obtainable |
| INGEMMET (Peru PE1) | official ASM points (Peru side only) | in use for PE1 |
| Sentinel-2 disturbance mapping | active footprint production | future; out of scope before 7/18 |

## Release Boundary

- May be committed: no (raw data stays local; only this registry note is committed)
- May be used in public examples: no unless replaced by synthetic or approved sample
- Public-safe summary available: yes, this registry note without local files
