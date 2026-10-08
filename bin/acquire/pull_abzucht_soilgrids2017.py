#!/usr/bin/env python3
"""TOOLING: bounded native windows from the superseded official 2017 archive."""
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import Window, from_bounds

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
from pull_goslar_soilgrids_window import williams_k
OUT=ROOT/'data/raw/soilgrids2017_abzucht'
BASE='https://files.isric.org/soilgrids/former/2017-03-10/data/'
REF=ROOT/'outputs/goslar_abzucht_display_rectangle_v1/frozen_scale_v1/chain/terrain_preprocessing/goslar_focus_dem_utm32n_30m.tif'
PROPS={'CLYPPT':'clay','SLTPPT':'silt','SNDPPT':'sand','ORCDRC':'soc'}
DEPTHS=[0,5,15,30]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def depth_average(values):
    """Trapezoid-integrate four depth-point K predictions across 0–30 cm."""
    if len(values)!=4:raise ValueError('Expected K at depths 0, 5, 15, 30 cm')
    return sum((values[i]+values[i+1])*.5*(DEPTHS[i+1]-DEPTHS[i])/30 for i in range(3))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest_path=OUT/'source_manifest.json'
    if manifest_path.exists():
        m=json.loads(manifest_path.read_text())
        if m['reference_sha256']!=sha(REF):raise ValueError('Reference drift')
        for name,item in m['files'].items():
            if sha(OUT/name)!=item['sha256']:raise ValueError('Pinned data drift: '+name)
        if m['implementation_sha256']!=sha(Path(__file__)):raise ValueError('Acquisition code changed; inspect before reuse')
        if m['formula_implementation_sha256']!=sha(Path(__file__).with_name('pull_goslar_soilgrids_window.py')):raise ValueError('Formula helper changed')
        print('Verified cached SoilGrids 2017 acquisition');return
    # Partial acquisitions stay visibly marked until all sources are verified.
    (OUT/'INCOMPLETE.txt').write_text('Acquisition incomplete; only source_manifest.json establishes a complete pinned snapshot.\n')
    with rasterio.open(REF) as d:bounds=transform_bounds(d.crs,'EPSG:4326',*d.bounds,densify_pts=21)
    bounds=[bounds[0]-.01,bounds[1]-.01,bounds[2]+.01,bounds[3]+.01]
    from concurrent.futures import ThreadPoolExecutor
    import time
    receipt_path=OUT/'download_receipts.json'
    receipts=json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
    def acquire(job):
        level,depth,code,key=job
        name=f'{code}_M_sl{level}_250m_ll.tif';url=BASE+name
        if name in receipts:
            rec=receipts[name]
            for fn,item in rec['files'].items():
                if sha(OUT/fn)!=item['sha256']:raise ValueError('Partial cache drift: '+fn)
            if rec['bounds_wgs84']!=bounds:raise ValueError('Partial cache extent drift')
            with rasterio.open(OUT/name) as d:
                a=d.read(1,masked=True).filled(np.nan);grid=(str(d.crs),tuple(d.transform),a.shape)
            return name,rec,grid
        for attempt in range(3):
            try:
                with urlopen(Request(url,headers={'Range':'bytes=0-1023'}),timeout=40) as response:
                    if response.status!=206:raise ValueError('No bounded range support')
                    headers=dict(content_range=response.headers.get('Content-Range'),etag=response.headers.get('ETag'))
                    response.read(1024)
                with urlopen(url+'.xml',timeout=40) as response:xml=response.read(50000)
                text=' '.join(t.text.strip() for t in ET.fromstring(xml).iter() if t.text and t.text.strip())
                if f'depth {depth/100:.2f} m' not in text:raise ValueError('Unexpected source depth')
                if ('g / kg' if key=='soc' else 'percent') not in text:raise ValueError('Unexpected source units')
                with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',GDAL_HTTP_TIMEOUT='120',
                      GDAL_HTTP_MAX_RETRY='2',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif'):
                    # Distinct retry URL bypasses any cached truncated remote range.
                    address='/vsicurl/'+url+(f'?bounded_retry={attempt}' if attempt else '')
                    with rasterio.open(address) as d:
                        wf=from_bounds(*bounds,transform=d.transform)
                        c0,r0=int(np.floor(wf.col_off)),int(np.floor(wf.row_off))
                        c1,r1=int(np.ceil(wf.col_off+wf.width)),int(np.ceil(wf.row_off+wf.height))
                        w=Window(c0,r0,c1-c0,r1-r0)
                        a=d.read(1,window=w,masked=True).astype('float32').filled(np.nan)
                        profile=dict(driver='GTiff',height=a.shape[0],width=a.shape[1],count=1,dtype='float32',
                                 crs=d.crs,transform=d.window_transform(w),nodata=-9999.,compress='deflate')
                        grid=(str(d.crs),tuple(profile['transform']),a.shape)
                v=a/10 if key=='soc' else a
                if np.any(v[np.isfinite(v)]<0) or np.any(v[np.isfinite(v)]>100):raise ValueError('Invalid percent')
                with rasterio.open(OUT/name,'w',**profile) as d:d.write(np.where(np.isfinite(a),a,-9999).astype('float32'),1)
                (OUT/(name+'.xml')).write_bytes(xml)
                rec=dict(bounds_wgs84=bounds,http_range=headers,source_url=url,
                         files={fn:dict(bytes=(OUT/fn).stat().st_size,sha256=sha(OUT/fn)) for fn in [name,name+'.xml']})
                print(name,'valid',int(np.isfinite(a).sum()),'/',a.size,flush=True)
                return name,rec,grid
            except Exception as e:
                print(name,'attempt',attempt+1,type(e).__name__,str(e),flush=True)
                if attempt==2:raise
                time.sleep(1)
    jobs=[(level,depth,code,key) for level,depth in enumerate(DEPTHS,1) for code,key in PROPS.items()]
    native_ref=None
    with ThreadPoolExecutor(max_workers=4) as pool:
        for name,rec,grid in pool.map(acquire,jobs):
            if native_ref is None:native_ref=grid
            elif native_ref!=grid:raise ValueError('Native grids do not align')
            receipts[name]=rec
            receipt_path.write_text(json.dumps(receipts,indent=2)+'\n')
    files={fn:item for rec in receipts.values() for fn,item in rec['files'].items()}
    m=dict(dataset_id='soilgrids2017_abzucht',access_date='2026-09-14',source=BASE,
           reference_sha256=sha(REF),reference_path=str(REF.relative_to(ROOT)),bounds_wgs84=bounds,
           effective_resolution='nominal 250m; geographic 1/480 degree grid',license='ODbL per SoilGrids2017 FAQ',
           source_model='Superseded 2017 predictions; separate version alternative, not recovered 2020 data',
           units=dict(texture='percent',soc='g/kg; analysis divides by 10 to percent'),
           files=files,http_range_checks={name:r['http_range'] for name,r in receipts.items()},
           implementation_sha256=sha(Path(__file__)),
           formula_implementation_sha256=sha(Path(__file__).with_name('pull_goslar_soilgrids_window.py')))
    manifest_path.write_text(json.dumps(m,indent=2)+'\n');(OUT/'INCOMPLETE.txt').unlink()
    print('Pinned',len(files),'raw source files; derive K under outputs with complete_abzucht_inputs.py')


if __name__=='__main__':main()
