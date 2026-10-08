#!/usr/bin/env python3
"""TOOLING: bounded official BK50 context export; this is not numerical soil K."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
import io
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/raw/lbeg_bk50_abzucht'
API = 'https://nibis.lbeg.de/cardomap3/ajaxpro/IDU.App.ExportCardoMap.CardoMap.Controls.Export.Export,IDU.App.ExportCardoMap.ashx'

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'outputs/goslar_abzucht_display_rectangle_v1/frozen_scale_v1/expansion_manifest.json'
    bounds = json.loads(source.read_text())['display_rectangle']['bounds_utm32n']
    left, bottom, right, top = bounds
    assert 0 < (right-left)*(top-bottom) < 100e6
    geom = f'gPOLY:{left}|{bottom}|{right}|{bottom}|{right}|{top}|{left}|{top}|{left}|{bottom};25832'
    request = {'data': {'themeIds': ['1616'], 'epsgCode': 25832,
                        'filterGeom': geom, 'exportFormat': 'GPKG'}}
    response = subprocess.check_output(['curl', '-fsSL', '--retry', '2', '--max-time', '60',
        '-H', 'X-AjaxPro-Method: AxExportData', '-H', 'Content-Type: application/json',
        '--data-binary', json.dumps(request), API])
    result = json.loads(response)
    if 'value' not in result or not result['value'].startswith('/cardomap3/'):
        raise RuntimeError('NIBIS export failed: ' + str(result))
    archive = subprocess.check_output(['curl', '-fsSL', '--retry', '2', '--max-time', '60',
        '--max-filesize', '20000000', 'https://nibis.lbeg.de' + result['value']])
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        gpkg_names = [n for n in z.namelist() if n.endswith('.gpkg')]
        if len(gpkg_names) != 1:
            raise ValueError('Unexpected export contents')
        path = RAW / 'bk50_abzucht_display_context.gpkg'
        path.write_bytes(z.read(gpkg_names[0]))
    frame = gpd.read_file(path)
    assert frame.crs.to_epsg() == 25832 and len(frame) > 0
    grid = ROOT / 'outputs/goslar_abzucht_display_rectangle_v1/frozen_scale_v1/chain/priority_scenarios/scenarios/priority_goslar_direct_pim.tif'
    zone_file = ROOT / 'data/validation/goslar_2017_event_map_candidates_v1/nlwkn_current_regulatory_flood_zones_goslar.geojson'
    with rasterio.open(grid) as ds:
        zones = gpd.read_file(zone_file)
        zone = zones[zones.uesg_id == 917].to_crs(ds.crs).geometry.union_all()
        typed = frame[frame.botyp.notna()].to_crs(ds.crs)
        # Repair is in-memory only; raw downloaded polygons remain unchanged.
        typed_geom = typed.geometry.make_valid().union_all()
        hq = geometry_mask([zone], out_shape=ds.shape, transform=ds.transform, invert=True)
        soil = geometry_mask([typed_geom], out_shape=ds.shape, transform=ds.transform, invert=True)
        coverage = {'hq100_cells': int(hq.sum()), 'hq100_soil_type_cells': int((hq & soil).sum()),
                    'method': 'cell centre on existing 30 m grid; in-memory make_valid; soil type is not numeric K',
                    'grid_path': str(grid.relative_to(ROOT)), 'zone_path': str(zone_file.relative_to(ROOT))}
    manifest = {'dataset_id': 'lbeg_bk50_abzucht', 'access_date': '2026-09-14',
        'product': 'BK50 Niedersachsen, 1:50000, theme 1616', 'licence': 'CC BY 4.0',
        'metadata_url': 'https://nibis.lbeg.de/net3/public/ikxcms/?pgid=987',
        'endpoint': API, 'request': request, 'bounds_epsg25832': bounds,
        'claim_level': 'diagnostic_only', 'semantic_use': 'soil-type context; not numerical erodibility K',
        'features': len(frame), 'fields': [c for c in frame.columns if c != 'geometry'],
        'invalid_geometry_count': int((~frame.geometry.is_valid).sum()),
        'coverage_check': coverage,
        'geometry_note': 'Server returns whole intersecting polygons. Preserve source geometry; repair and clip only in derived outputs.',
        'files': {path.name: {'bytes': path.stat().st_size,
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}},
        'command': '.venv/bin/python bin/acquire/pull_abzucht_bk50_context.py'}
    (RAW / 'source_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(manifest, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
