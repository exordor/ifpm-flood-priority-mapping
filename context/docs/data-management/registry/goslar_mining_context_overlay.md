# Dataset Registry: Goslar mining context overlay v1

- Dataset id: `goslar_mining_context_overlay`
- Status: downloaded 2026-08-14; context overlay, not part of the PIM score
- Access date: 2026-08-14
- Study area: Goslar focus extent plus a 12 km context radius
- Output CRS: EPSG:32632
- Acquire command: `.venv/bin/python bin/acquire/pull_goslar_mining_overlay.py`
- Raw destination: `data/raw/goslar_mining_context_overlay/`
- Derived output: `outputs/goslar_mining_context_overlay/goslar_mining_context_overlay.gpkg`
- Provenance manifest: `outputs/goslar_mining_context_overlay/mining_overlay_manifest.json`

## Sources

1. LBEG/NIBIS `Bergwerkseigentum`, WFS 2.0, NodeId 75, feature type
   `cls:L34`. Official legal mining-right polygons, CC BY 4.0. The WFS query
   returned 42 fields intersecting the 12 km context buffer and 0 intersecting
   the focus extent itself. These polygons describe legal rights, not confirmed
   active extraction or disturbed ground.
2. OpenStreetMap via Overpass API. Query tags: `man_made=mine|adit|mineshaft`,
   `historic=mine|mineshaft`, `landuse=quarry`, and `industrial=mine`. ODbL
   1.0, attribution: © OpenStreetMap contributors. The downloader queries a
   centroid radius large enough to enclose the complete focus+12 km buffer,
   then applies the exact metric buffer as the final filter. The snapshot
   contains 155 point locations and 29 area geometries; 4 points and 1 area
   intersect the focus extent. Rammelsberg is retained as its multipolygon
   geometry rather than reduced to a centroid. Completeness, positional
   accuracy, and current operating status are not guaranteed.

Raw-response and derived-output SHA-256 values, feature counts and focus intersections are
recorded in `mining_overlay_manifest.json`.
