#!/usr/bin/env python3
"""TOOLING: download one public GHSL tile and retain only a native local window."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import urllib.request
import zipfile
import math
import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import Window, from_bounds

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT/'data/raw/ghsl2020_abzucht_population'
TMP = ROOT/'data/tmp/ghsl2020_abzucht_population'
FILENAME = 'GHS_POP_E2020_GLOBE_R2023A_54009_100_V1_0_R3_C19.zip'
URL = 'https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/GHS_POP_E2020_GLOBE_R2023A_54009_100/V1-0/tiles/'+FILENAME
EXPECTED_BYTES = 41019822
PINNED_SHA256 = '736d07c99453834235d62c2c9eab9f37450809d6621b9ea8d6255e4ae7f44dd1'

def digest(path):
    with path.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def main():
    RAW.mkdir(parents=True, exist_ok=True); TMP.mkdir(parents=True, exist_ok=True)
    archive = RAW/FILENAME
    manifest_path = RAW/'source_manifest.json'
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text())
        for filename, record in existing['files'].items():
            candidate = RAW/filename
            if candidate.stat().st_size != record['bytes'] or digest(candidate) != record['sha256']:
                raise ValueError(f'Pinned source changed: {filename}')
    if not archive.exists():
        partial = TMP/(FILENAME+'.part')
        with urllib.request.urlopen(URL, timeout=45) as response, partial.open('wb') as out:
            total = 0
            while chunk := response.read(1024*1024):
                total += len(chunk)
                if total > EXPECTED_BYTES: raise ValueError('Unexpected archive size; inspect source revision')
                out.write(chunk)
        if partial.stat().st_size != EXPECTED_BYTES: raise ValueError('Incomplete archive; partial retained')
        partial.replace(archive)
    if archive.stat().st_size != EXPECTED_BYTES: raise ValueError('Cached archive size differs')
    if digest(archive) != PINNED_SHA256: raise ValueError('Archive differs from pinned 2026-09-14 download')
    reference = ROOT/'outputs/goslar_abzucht_display_rectangle_v1/frozen_scale_v1/chain/terrain_preprocessing/goslar_focus_dem_utm32n_30m.tif'
    if manifest_path.exists():
        if existing['reference_grid_sha256'] != digest(reference): raise ValueError('Reference changed; use a new dataset version')
        print('Verified existing GHSL archive and native subset; no source rewritten')
        return
    with rasterio.open(reference) as ref: bounds, crs = ref.bounds, ref.crs
    with zipfile.ZipFile(archive) as z:
        names = [n for n in z.namelist() if n.lower().endswith('.tif')]
        if len(names) != 1: raise ValueError('Expected one GeoTIFF in tile archive')
    with rasterio.open(f'/vsizip/{archive}/{names[0]}') as src:
        bb = transform_bounds(crs, src.crs, *bounds, densify_pts=21)
        w = from_bounds(*bb, src.transform)
        col, row = math.floor(w.col_off)-5, math.floor(w.row_off)-5
        win = Window(col, row, math.ceil(w.col_off+w.width)+5-col, math.ceil(w.row_off+w.height)+5-row)
        if col < 0 or row < 0 or win.col_off+win.width > src.width or win.row_off+win.height > src.height:
            raise ValueError('Requested window extends outside this tile')
        a = src.read(1, window=win)
        profile = dict(src.profile, width=a.shape[1], height=a.shape[0], transform=src.window_transform(win), compress='deflate')
        path = RAW/'ghsl2020_population_native_100m.tif'
        with rasterio.open(path, 'w', **profile) as dst:
            dst.write(a, 1)
            dst.update_tags(source=URL, meaning='Modelled population count per native 100 m cell', epoch='2020', release='R2023A')
        metadata = dict(crs=str(src.crs), resolution=list(src.res), nodata=src.nodata, shape=list(a.shape), bounds=list(rasterio.windows.bounds(win,src.transform)))
    manifest = dict(dataset_id='ghsl2020_abzucht_population', source_url=URL, metadata_url='https://data.jrc.ec.europa.eu/dataset/2ff68a52-5b5b-4a22-8f40-c41da8332cfe',
                    licence='CC BY 4.0; European Commission JRC', retrieved_utc=datetime.now(timezone.utc).isoformat(),
                    command='.venv/bin/python bin/acquire/pull_abzucht_ghsl_population.py', native=metadata,
                    reference_grid_sha256=digest(reference), files={p.name:dict(bytes=p.stat().st_size,sha256=digest(p)) for p in [archive,path]})
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(manifest, indent=2))

if __name__ == '__main__': main()
