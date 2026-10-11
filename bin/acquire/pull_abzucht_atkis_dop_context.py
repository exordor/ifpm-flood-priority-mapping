#!/usr/bin/env python3
"""TOOLING: bounded official watercourse and current orthophoto context intake."""
import csv
from datetime import date, datetime, timezone
import hashlib
import html
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image
from pyproj import Transformer
import geopandas as gpd

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/validation/goslar_abzucht_atkis_dop_context'
TMP=ROOT/'data/tmp/goslar_abzucht_atkis_dop_context'
BASE=ROOT/'outputs/goslar_abzucht_diagnostics/fixed_scale'
ALIGN=ROOT/'outputs/goslar_abzucht_diagnostics/river_alignment'
WFS='https://opendata.lgln.niedersachsen.de/doorman/noauth/atkisbdlm_wfs_sf'
WMS='https://opendata.lgln.niedersachsen.de/doorman/noauth/dop_wms'
MAX_BYTES=10_000_000
COMMAND='.venv/bin/python bin/acquire/pull_abzucht_atkis_dop_context.py'


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def get(base,params,max_bytes=MAX_BYTES):
    url=base+'?'+urllib.parse.urlencode(params)
    last=None
    for attempt in range(3):
        try:
            request=urllib.request.Request(url,headers={'User-Agent':'IFPM bounded academic GIS check/1.0'})
            with urllib.request.urlopen(request,timeout=45) as response:
                body=response.read(max_bytes+1)
                if len(body)>max_bytes:raise ValueError('Response exceeds configured 10 MB cap')
                if response.status!=200:raise ValueError(f'HTTP {response.status}')
                return body,dict(url=url,content_type=response.headers.get('Content-Type'),
                                 content_length_header=response.headers.get('Content-Length'))
        except Exception as exc:
            last=exc
            if attempt==2:raise
    raise last


def install(name,body,staging):
    fd,path=tempfile.mkstemp(prefix=name+'.partial.',dir=staging)
    try:
        with os.fdopen(fd,'wb') as f:f.write(body);f.flush();os.fsync(f.fileno())
        dest=staging/name;os.replace(path,dest)
        return dest
    finally:
        if os.path.exists(path):os.unlink(path)


def capture_metadata(x,y):
    east,north=Transformer.from_crs(32632,25832,always_xy=True).transform(x,y)
    params={'SERVICE':'WMS','VERSION':'1.3.0','REQUEST':'GetFeatureInfo',
            'LAYERS':'ni_dop20_info','QUERY_LAYERS':'ni_dop20_info','STYLES':'',
            'CRS':'EPSG:25832','BBOX':f'{east-100:.3f},{north-100:.3f},{east+100:.3f},{north+100:.3f}',
            'WIDTH':'200','HEIGHT':'200','I':'100','J':'100',
            'INFO_FORMAT':'text/html','FORMAT':'image/png'}
    body,http=get(WMS,params,max_bytes=100_000)
    if 'text/html' not in (http['content_type'] or ''):raise ValueError('DOP info did not return HTML')
    plain=' '.join(html.unescape(re.sub('<[^>]+>',' ',body.decode('iso-8859-1','replace'))).split())
    match=re.search(r'Datum der Befliegung:\s*(\d{8})',plain)
    if not match:raise ValueError('DOP capture date missing from GetFeatureInfo')
    raw=match.group(1)
    date(int(raw[:4]),int(raw[4:6]),int(raw[6:]))
    return dict(capture_date=f'{raw[:4]}-{raw[4:6]}-{raw[6:]}',
                capture_date_scope='image_center_point_only',
                metadata_response_sha256=hashlib.sha256(body).hexdigest(),metadata_http=http)


def main():
    if sys.argv[1:]==['--metadata-only']:
        manifest_path=DATA/'source_manifest.json'
        manifest=json.loads(manifest_path.read_text())
        for label,record in manifest['dop']['windows'].items():
            x=(record['bbox_25832'][0]+record['bbox_25832'][2])/2
            y=(record['bbox_25832'][1]+record['bbox_25832'][3])/2
            x,y=Transformer.from_crs(25832,32632,always_xy=True).transform(x,y)
            record.update(capture_metadata(x,y))
        manifest['dop']['warning']='Image-center capture metadata only; mosaic may contain other dates. Not 2017 flood observation.'
        fd,tmp_path=tempfile.mkstemp(prefix='source_manifest.partial.',dir=DATA)
        try:
            with os.fdopen(fd,'w') as f:f.write(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
            os.replace(tmp_path,manifest_path)
        finally:
            if os.path.exists(tmp_path):os.unlink(tmp_path)
        print(json.dumps({label:row['capture_date'] for label,row in manifest['dop']['windows'].items()}))
        return
    with (ALIGN/'three_cases_brief.csv').open() as f:
        cases={row['case']:row for row in csv.DictReader(f)}
    with (ALIGN/'sustained_stream_gap_runs.csv').open() as f:
        runs=list(csv.DictReader(f))
    longest=max(runs,key=lambda row:float(row['approximate_sampled_span_m']))
    rectangle=json.loads((BASE/'expansion_manifest.json').read_text())['display_rectangle']['bounds_utm32n']
    transformer=Transformer.from_crs(32632,25832,always_xy=True)
    bbox=transformer.transform_bounds(rectangle[0]-300,rectangle[1]-300,
                                       rectangle[2]+300,rectangle[3]+300)
    bounds=','.join(f'{x:.3f}' for x in bbox)+',EPSG:25832'
    wfs_params={'SERVICE':'WFS','VERSION':'2.0.0','REQUEST':'GetFeature',
                'TYPENAMES':'adv:AX_Gewaesserachse','BBOX':bounds,
                'SRSNAME':'EPSG:25832','COUNT':'1000'}
    hits_params={**wfs_params,'RESULTTYPE':'hits'}
    hits_body,hits_http=get(WFS,hits_params,max_bytes=100_000)
    hits_root=ET.fromstring(hits_body)
    matched=int(hits_root.attrib.get('numberMatched','-1'))
    if not 0<matched<1000:raise ValueError(f'Unexpected WFS feature count: {matched}')
    gml,gml_http=get(WFS,wfs_params)
    root=ET.fromstring(gml)
    if not root.tag.endswith('FeatureCollection'):raise ValueError('WFS did not return a feature collection')
    returned=int(root.attrib.get('numberReturned','-1'))
    if returned!=matched:raise ValueError(f'Incomplete WFS page: {returned}/{matched}')
    TMP.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='snapshot.',dir=TMP))
    try:
        return acquire_snapshot(staging,gml,matched,returned,gml_http,hits_http,bbox,cases,longest,transformer)
    finally:
        if staging.exists():shutil.rmtree(staging)


def acquire_snapshot(staging,gml,matched,returned,gml_http,hits_http,bbox,cases,longest,transformer):
    gml_path=install('atkis_gewaesserachse.gml',gml,staging)
    features=gpd.read_file(gml_path)
    if len(features)!=returned or features.crs is None or features.crs.to_epsg()!=25832 or not features.geom_type.eq('LineString').all() or not features.is_valid.all():
        raise ValueError('Unexpected WFS geometry, count or CRS')
    windows={}
    for label,case in [('case_a',cases['A']),('case_c',cases['C'])]:
        windows[label]=(float(case['easting_m']),float(case['northing_m']),900.,650.,1500,1083)
    mid_x=(float(longest['start_easting_m'])+float(longest['end_easting_m']))/2
    mid_y=(float(longest['start_northing_m'])+float(longest['end_northing_m']))/2
    windows['longest_gap']=(mid_x,mid_y,1400.,900.,1600,1029)
    downloads={}
    for label,(x,y,width_m,height_m,width_px,height_px) in windows.items():
        xmin,ymin=transformer.transform(x-width_m/2,y-height_m/2)
        xmax,ymax=transformer.transform(x+width_m/2,y+height_m/2)
        params={'SERVICE':'WMS','VERSION':'1.3.0','REQUEST':'GetMap','LAYERS':'ni_dop20',
                'STYLES':'','CRS':'EPSG:25832','BBOX':','.join(f'{v:.3f}' for v in (xmin,ymin,xmax,ymax)),
                'WIDTH':str(width_px),'HEIGHT':str(height_px),'FORMAT':'image/png'}
        body,http=get(WMS,params)
        if not body.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError(f'WMS did not return PNG for {label}: {body[:250]!r}')
        dest=install(f'dop_{label}.png',body,staging)
        with Image.open(dest) as image:
            if image.size!=(width_px,height_px):raise ValueError('Unexpected WMS image dimensions')
            image.verify()
        downloads[label]=dict(path=str((DATA/dest.name).relative_to(ROOT)),bytes=dest.stat().st_size,
            sha256=sha(dest),bbox_25832=[xmin,ymin,xmax,ymax],width_px=width_px,height_px=height_px,
            ground_pixel_size_m=[width_m/width_px,height_m/height_px],http=http,
            **capture_metadata(x,y))
    manifest=dict(dataset_id='goslar_abzucht_atkis_dop_context',access_date=date.today().isoformat(),
        claim_level='validation_candidate/context',enters_pim_score=False,command=COMMAND,
        attribution='LGLN (2026), CC BY 4.0',
        wfs=dict(feature_type='adv:AX_Gewaesserachse',matched=matched,returned=returned,
                 path=str((DATA/gml_path.name).relative_to(ROOT)),bytes=gml_path.stat().st_size,
                 sha256=sha(gml_path),hits_http=hits_http,feature_http=gml_http,
                 bbox_25832=list(bbox)),
        dop=dict(service_layer='ni_dop20',windows=downloads,
                 warning='Image-center capture metadata only; mosaic may contain other dates. Not 2017 flood observation.'),
        local_selection_sources={str((ALIGN/'three_cases_brief.csv').relative_to(ROOT)):sha(ALIGN/'three_cases_brief.csv'),
                                 str((ALIGN/'sustained_stream_gap_runs.csv').relative_to(ROOT)):sha(ALIGN/'sustained_stream_gap_runs.csv')})
    (staging/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    backup=None
    if DATA.exists():
        backup=TMP/('previous_snapshot_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        DATA.rename(backup)
    try:staging.rename(DATA)
    except Exception:
        if backup is not None:backup.rename(DATA)
        raise
    if backup is not None:shutil.rmtree(backup)
    print(json.dumps(dict(wfs_features=returned,wfs_bytes=(DATA/gml_path.name).stat().st_size,
                          dop_bytes={k:v['bytes'] for k,v in downloads.items()}),indent=2))


if __name__=='__main__':main()
