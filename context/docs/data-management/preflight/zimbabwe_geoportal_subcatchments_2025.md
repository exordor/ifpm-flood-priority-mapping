# Download Preflight: Zimbabwe Geoportal Sub-Catchments 2025

Status: completed for controlled boundary-comparison download.

## Scope

- [x] The dataset has a clear project purpose: compare a local Zimbabwe sub-catchment boundary
      candidate against the HydroBASINS Upper Mzingwane candidate.
- [x] The required study area is known: Zimbabwe / Upper Mzingwane prototype.
- [x] The required temporal window is not applicable because this is a static boundary layer.
- [x] The expected disk footprint is acceptable: about `614.9 KB` Shapefile or `2.2 MB` GeoJSON.
- [x] The download is not a broad bulk mirror; it is one small boundary layer.

## Access And Licence

- [x] Source URL or portal is recorded:
      `https://zimgeoportal.org.zw/datasets/sub-catchments/`
- [x] Product/version is recorded: Sub-Catchments, `v1.0`, updated 2025-10-22.
- [x] Licence, terms, or citation requirements are checked at page level: ODC-BY 1.0.
- [x] Account, registration, approval, or payment requirements are documented: login required.
- [x] Credentials, cookies, tokens, and private links will not be committed.

## Destination

- [x] Raw downloaded data will go under `data/raw/zimbabwe_geoportal_subcatchments_2025/`.
- [x] Temporary downloads will go under `data/tmp/zimbabwe_geoportal_subcatchments_2025/` or
      the browser downloads folder before being moved.
- [x] Validation records are not expected for this boundary-comparison step.
- [x] Processed diagnostics will go under `outputs/zimbabwe_geoportal_subcatchments_2025/`.
- [x] Release bundles will go under `exports/` only if explicitly approved.
- [x] No real downloaded data will be copied into `context/` or `ifpm-flood-pipeline/`.

## Registry

- [x] A dataset registry note exists:
      `context/docs/data-management/registry/zimbabwe_geoportal_subcatchments_2025.md`
- [x] The note states whether the download is reusable or exploratory.
- [x] The registry note includes source, product/version, access date, destination, and use.
- [x] The registry note includes licence/access constraints.
- [x] The registry note will include checksum or file-size evidence after download.
- [x] The registry note identifies checksum scope and expected/actual files.

## Safety Check

- [x] The target path is ignored by Git.
- [x] The command or manual download will not overwrite unrelated local data.
- [x] Partial or failed downloads can be identified and cleaned.
- [x] Partial path, attempt status, failure reason, and cleanup decision will be recorded if the
      download does not complete cleanly.
- [x] The handoff will state what was downloaded and what remains unverified.

## Authorization

Authorized operation:

- Download exactly one Zimbabwe Geoportal Sub-Catchments resource.
- Prefer Shapefile if both Shapefile and GeoJSON are available because it is smaller.
- Use the in-app browser session to verify the dataset page and resource link.
- Download the verified Shapefile resource to `data/raw/zimbabwe_geoportal_subcatchments_2025/`.

Not authorized:

- Downloading Main Catchments, other Zimbabwe Geoportal layers, SRTM, CHIRPS, HydroRIVERS, or
  additional validation datasets in this step.
- Running overlay, scoring, flood-risk interpretation, or release packaging.

## Execution Record

- Execution date: 2026-06-10
- Browser access: the in-app browser opened the authenticated Sub-Catchments dataset page and
  confirmed that the page listed Shapefile and GeoJSON resources.
- Downloaded artifact:
  `data/raw/zimbabwe_geoportal_subcatchments_2025/sub_catchments-1761163234.zip`
- Resource URL verified on page:
  `https://pub-2e9c8e4ccd4f4a4d8b4ae8ee68fdf713.r2.dev/datasets/resources/sub_catchments-1761163234.zip`
- Direct resource URL handling: internal reproducibility evidence only; do not treat it as a
  public release link without licence/access review.
- Download command class: direct `curl` transfer of the verified resource URL.
- Authentication handling: no credentials, cookies, tokens, or session material were recorded in
  project files or download commands.
- Actual size: `629658` bytes.
- SHA-256:
  `fb5a3528ca677f420e5030f146a7699027e93c765fcebe7ef45a59611b6f0cd2`
- Extraction manifest:
  - `extracted/sub_catchments.cpg`
  - `extracted/sub_catchments.dbf`
  - `extracted/sub_catchments.prj`
  - `extracted/sub_catchments.qmd`
  - `extracted/sub_catchments.shp`
  - `extracted/sub_catchments.shx`

## Verification Result

- CRS: `EPSG:4326`
- Feature count: 47 polygon features.
- Geometry integrity: 47 valid polygons, 0 empty geometries.
- Attribute field used for candidate names: `SubCatchme`.
- Geoportal candidate found: `Upper Mzingwane`.
- Anchor check:
  - Mzingwane Dam falls in `Upper Mzingwane`.
  - Esigodini falls in `Upper Mzingwane`.
  - Gwanda falls in `Shashe`, not `Upper Mzingwane`.
- Area check: Geoportal `Upper Mzingwane` geodesic area is about `7321.5 km2`.
- Area method: geometries were loaded in `EPSG:4326`; polygon intersections were computed
  geometrically, and areas were calculated as WGS84 geodesic areas in square kilometres.
- Boundary decision impact: this data improves local named-boundary evidence, but it does not
  close boundary acceptance because its area is much larger than both HydroBASINS level 7
  `HYBAS_ID=1071528840` and the untraced `~2138 km2` Upper Mzingwane reference.
