#!/usr/bin/env python3
"""Consistent historical OSM roads fallback; reuses completed facilities snapshot."""
import gzip,json,hashlib,urllib.request,urllib.parse,time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import box,shape,mapping
ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'data/raw/goslar_multiriver_osm';TMP=ROOT/'data/tmp/goslar_multiriver_osm'
STAMP='2026-07-27T09:00:00Z';ENDPOINT='https://api.ohsome.org/v1/elements/geometry';BOUNDS=(552411,5734748,618576,5795557)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fetch(args):
 iy,ix,bounds=args;p=RAW/f'ohsome_roads_{iy}_{ix}.geojson';mp=p.with_suffix('.request.json')
 if p.exists():return json.loads(p.read_text()),json.loads(mp.read_text())
 params={'bboxes':','.join(map(str,bounds)),'time':STAMP,'filter':'highway=* and type:way','properties':'tags,metadata','clipGeometry':'false'}
 errors=[]
 for attempt in range(3):
  try:
   req=urllib.request.Request(ENDPOINT,data=urllib.parse.urlencode(params).encode(),headers={'Accept-Encoding':'gzip','User-Agent':'IFPM-research/1.0'})
   with urllib.request.urlopen(req,timeout=240) as response:
    blob=response.read()
    if response.headers.get('Content-Encoding')=='gzip':blob=gzip.decompress(blob)
   content=json.loads(blob)
   if content.get('type')!='FeatureCollection':raise RuntimeError(content)
   temp=TMP/f'ohsome_{iy}_{ix}.part';temp.write_bytes(blob);temp.replace(p)
   meta={'endpoint':ENDPOINT,'params':params,'query_bounds_epsg4326':bounds,'bytes':len(blob),'sha256':sha(p),'access_time_utc':datetime.now(timezone.utc).isoformat(),'errors':errors,'features':len(content['features'])}
   mp.write_text(json.dumps(meta,indent=2));print('ohsome tile',iy,ix,len(content['features']),flush=True);return content,meta
  except Exception as e:errors.append(str(e));print('ohsome error',iy,ix,repr(e),flush=True);time.sleep(60)
 raise RuntimeError(errors)
def main():
 RAW.mkdir(parents=True,exist_ok=True);TMP.mkdir(parents=True,exist_ok=True)
 boundary=gpd.read_file(ROOT/'outputs/goslar_multiriver_full_extent/fixed_scale/expanded_boundary.gpkg').to_crs(32632).geometry.union_all().buffer(3050)
 support=gpd.GeoSeries([boundary],crs=32632).to_crs(4326).iloc[0]
 west,south,east,north=Transformer.from_crs(32632,4326,always_xy=True).transform_bounds(*BOUNDS,densify_pts=21)
 jobs=[];skipped=[]
 for iy in range(4):
  for ix in range(4):
   bb=[west+(east-west)*ix/4,south+(north-south)*iy/4,west+(east-west)*(ix+1)/4,south+(north-south)*(iy+1)/4]
   if box(*bb).intersects(support):jobs.append((iy,ix,bb))
   else:skipped.append({'tile':[iy,ix],'bounds':bb,'status':'outside_required_support'})
 sources=[];features={}
 with ThreadPoolExecutor(max_workers=2) as pool:
  for fc,meta in pool.map(fetch,jobs):
   sources.append(meta)
   for f in fc['features']:
    key=f['properties'].get('@osmId',f.get('id'))
    if key is None:raise RuntimeError('No OSM id')
    features[key]=f
 frame=gpd.GeoDataFrame.from_features(list(features.values()),crs=4326).to_crs(32632)
 # Keep arbitrary original tags without SQLite field name conflicts.
 rows=[]
 for f in features.values():
  props=f['properties'];rows.append({'osm_id':str(props.get('@osmId',f.get('id'))),'highway':props.get('highway',''),'name':props.get('name',''),'surface':props.get('surface',''),'tags':json.dumps(props,ensure_ascii=False,sort_keys=True),'geometry':shape(f['geometry'])})
 frame=gpd.GeoDataFrame(rows,crs=4326).to_crs(32632);path=RAW/'roads.gpkg';frame.to_file(path,layer='roads',driver='GPKG')
 checked=gpd.read_file(path);assert len(checked)==len(rows) and checked.crs.to_epsg()==32632 and checked.geometry.is_valid.all()
 queried=gpd.GeoSeries([box(*j[2]) for j in jobs],crs=4326).union_all();assert support.difference(queried).area<1e-12
 facilities=RAW/'facilities.gpkg';facility_meta=json.loads((RAW/'facilities.request.json').read_text());facility_meta.update(gpkg_sha256=sha(facilities),gpkg_bytes=facilities.stat().st_size,retained_count=len(gpd.read_file(facilities)))
 manifest={'dataset_id':'goslar_multiriver_osm','licence':'ODbL, OpenStreetMap contributors','source_bounds_epsg32632':BOUNDS,'query_bounds_epsg4326':[west,south,east,north],'source_buffer_m':3000,'coverage_policy':'Roads cover evaluation boundary buffered3050m; facilities entire source rectangle. Skipped road tiles lie outside required support.','sources':{'facilities':facility_meta,'roads':{'acquisition_complete':True,'endpoint':ENDPOINT,'snapshot':STAMP,'snapshot_note':'Consistent historical OSM snapshot, older than original roads; do not attribute all overlap differences to expansion.','tile_requests':sources,'skipped_tiles':skipped,'successful_query_support_epsg4326':mapping(queried),'retained_count':len(frame),'gpkg_sha256':sha(path),'gpkg_bytes':path.stat().st_size}}}
 (RAW/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('COMPLETE ROADS',len(frame),flush=True)
if __name__=='__main__':main()
