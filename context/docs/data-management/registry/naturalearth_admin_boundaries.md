# Dataset Registry: Natural Earth 1:10m Admin Boundaries

Status: downloaded for study-area location visualization.

## Dataset Identity

- Dataset id: `naturalearth_admin_boundaries`
- Project role: country and first-level administrative boundary basemap for
  Zimbabwe and Peru study-area locator maps.
- Study areas: Zimbabwe Upper Mzingwane (background) and the former Peru study area (frozen).

## Source And Access

- Source organization: Natural Earth.
- Source URL or portal: `https://www.naturalearthdata.com/`
- Direct source artifacts:
  - `https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_admin_0_countries.zip`
  - `https://naturalearth.s3.amazonaws.com/10m_cultural/ne_10m_admin_1_states_provinces.zip`
- Product/version: Natural Earth cultural vectors, 1:10m scale.
- Access date: 2026-07-06.
- Access method: direct HTTPS download with `curl --location`.
- Licence or terms: public-domain Natural Earth terms; cite Natural Earth in
  public-facing figures.

## Download Record

- Raw destination: `data/raw/naturalearth_admin_boundaries/`
- Files:

| File | Bytes | SHA-256 |
|---|---:|---|
| `ne_10m_admin_0_countries.zip` | 4,930,492 | `ce1ac7036499a0edd641fbc093cd209a98f96a49d2eca8480aaacad35138a7f6` |
| `ne_10m_admin_1_states_provinces.zip` | 14,909,524 | `efc59726337323058f9446210adc96673179cd344e053666ee3d28cb58ba2b05` |

## Use And Limits

- Used as cartographic context only; study-area geometries come from the project boundary GPKGs.
