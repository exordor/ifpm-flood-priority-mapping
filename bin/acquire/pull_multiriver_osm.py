#!/usr/bin/env python3
"""Acquire finite-window expanded OSM sources, preserving original proxy classes."""
import gzip,hashlib,json,re,time,urllib.request,urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import LineString,Point,box,mapping
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'data/raw/goslar_multiriver_osm_v1'
TMP=ROOT/'data/tmp/goslar_multiriver_osm_v1'
BOUNDS=(552411,5734748,618576,5795557)
CLASSES={'school','hospital','fire_station','police','works','substation','station'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fetch(kind,query):
    dest=RAW/f'{kind}.json';(RAW/f'{kind}.overpass').write_text(query)
    meta=RAW/f'{kind}.request.json'
    if dest.exists():
        saved=json.loads(meta.read_text())
        assert sha(dest)==saved['sha256'],f'Cached source hash mismatch: {dest.name}'
        return json.loads(dest.read_text()),saved
    errors=[]
    for endpoint in ['https://maps.mail.ru/osm/tools/overpass/api/interpreter']*3:
        try:
            request=urllib.request.Request(endpoint,data=urllib.parse.urlencode({'data':query}).encode(),headers={'User-Agent':'IFPM-research-data-acquisition/1.0','Accept-Encoding':'gzip'})
            with urllib.request.urlopen(request,timeout=150) as response:
                blob=response.read()
                if response.headers.get('Content-Encoding')=='gzip':blob=gzip.decompress(blob)
            payload=json.loads(blob)
            if payload.get('remark'):raise RuntimeError(payload['remark'])
            if not payload.get('elements'):raise RuntimeError('Empty Overpass response')
            partial=TMP/f'{kind}.part';partial.write_bytes(blob);partial.replace(dest)
            metadata={'endpoint':endpoint,'query':query,'access_time_utc':datetime.now(timezone.utc).isoformat(),'osm_base_timestamp':payload.get('osm3s',{}).get('timestamp_osm_base'),'bytes':len(blob),'sha256':sha(dest),'errors_before_success':errors}
            meta.write_text(json.dumps(metadata,indent=2));return payload,metadata
        except Exception as e:
            errors.append(f'{endpoint}: {type(e).__name__}: {e}');print(errors[-1],flush=True)
            delay=60
            if isinstance(e,urllib.error.HTTPError):
                try:delay=max(60,int(e.headers.get('Retry-After','60')))
                except ValueError:delay=60
            time.sleep(delay)
    raise RuntimeError(errors)
def main():
    RAW.mkdir(parents=True,exist_ok=True);TMP.mkdir(parents=True,exist_ok=True)
    west,south,east,north=Transformer.from_crs(32632,4326,always_xy=True).transform_bounds(*BOUNDS,densify_pts=21)
    bbox=f'{south},{west},{north},{east}'
    support=gpd.read_file(ROOT/'outputs/goslar_multiriver_full_extent_v1/frozen_scale_v1/expanded_boundary.gpkg').to_crs(32632).geometry.union_all().buffer(3050)
    support=gpd.GeoSeries([support],crs=32632).to_crs(4326).iloc[0]
    roads_query=f'[out:json][timeout:240];way["highway"]({bbox});out geom;'
    facilities_query=f'[out:json][timeout:240];('+''.join(f'nwr[{tag}]({bbox});' for tag in ['"amenity"="school"','"amenity"="hospital"','"amenity"="fire_station"','"amenity"="police"','"emergency"','"healthcare"','"man_made"="works"','"power"="substation"','"railway"="station"'])+');out center;'
    sources={}
    for kind,q in [('facilities',facilities_query),('roads',roads_query)]:
        if kind=='roads':
            parts=[];requests=[]
            def tile(pair):
                iy,ix=pair
                a=south+(north-south)*iy/4;b=west+(east-west)*ix/4;c=south+(north-south)*(iy+1)/4;d=west+(east-west)*(ix+1)/4
                tq=f'[out:json][timeout:120];way["highway"]({a},{b},{c},{d});out geom;'
                parent=RAW/f'roads_{iy}_{ix}.json'
                if parent.exists():part,request=fetch(f'roads_{iy}_{ix}',tq)
                else:
                    children=[];child_requests=[]
                    for cy in range(2):
                        for cx in range(2):
                            aa=a+(c-a)*cy/2;bb=b+(d-b)*cx/2;cc=a+(c-a)*(cy+1)/2;dd=b+(d-b)*(cx+1)/2
                            if not box(bb,aa,dd,cc).intersects(support):
                                child_requests.append({'query_bounds_epsg4326':[bb,aa,dd,cc],'status':'outside_required_support','note':'Not acquired; not evidence of zero roads'})
                                continue
                            child_q=f'[out:json][timeout:25][maxsize:67108864];way["highway"]({aa},{bb},{cc},{dd});out geom;'
                            child,child_meta=fetch(f'roads_{iy}_{ix}_sub_{cy}_{cx}',child_q)
                            children.extend(child['elements']);child_requests.append(child_meta)
                            print('road subtile',iy,ix,cy,cx,len(child['elements']),flush=True)
                    part={'elements':children}
                    parent.write_text(json.dumps(part))
                    request={'parent_query':tq,'children':child_requests,'sha256':sha(parent),'bytes':parent.stat().st_size,'completion':'all required children acquired; disjoint children explicitly skipped'}
                    (RAW/f'roads_{iy}_{ix}.request.json').write_text(json.dumps(request,indent=2))
                print('road tile',iy,ix,len(part['elements']),flush=True)
                return part,request
            with ThreadPoolExecutor(max_workers=2) as pool:
                for part,request in pool.map(tile,[(iy,ix) for iy in range(4) for ix in range(4)]):
                    parts.extend(part['elements']);requests.append(request)
            payload={'elements':parts};metadata={'tile_requests':requests,'deduplication':'osm type and id','acquisition_complete':True,'required_support':'outputs/goslar_multiriver_full_extent_v1/frozen_scale_v1/expanded_boundary.gpkg buffered3050m'}
        else:payload,metadata=fetch(kind,q)
        rows=[];seen=set()
        for el in payload['elements']:
            key=(el['type'],el['id'])
            if key in seen:continue
            seen.add(key);tags=el.get('tags',{})
            common={'osm_type':el['type'],'osm_id':el['id'],'name':tags.get('name',''),'tags':json.dumps(tags,ensure_ascii=False,sort_keys=True)}
            if kind=='roads':
                coords=[(p['lon'],p['lat']) for p in el.get('geometry',[]) if 'lon'in p and 'lat'in p]
                if len(coords)<2:continue
                common.update(highway=tags.get('highway',''),surface=tags.get('surface',''),geometry=LineString(coords))
            else:
                cls=tags.get('amenity') or tags.get('railway') or tags.get('power') or tags.get('man_made')
                if cls not in CLASSES:continue
                pt=el if el['type']=='node' else el.get('center',{})
                if 'lon'not in pt:continue
                common.update(facility_class=cls,operator=tags.get('operator',''),geometry=Point(pt['lon'],pt['lat']))
            rows.append(common)
        frame=gpd.GeoDataFrame(rows,crs=4326).to_crs(32632);path=RAW/f'{kind}.gpkg'
        frame.to_file(path,layer=kind,driver='GPKG')
        reread=gpd.read_file(path);assert len(reread)==len(frame) and reread.crs.to_epsg()==32632
        assert reread.geometry.is_valid.all() and not reread.geometry.is_empty.any()
        metadata.update(retained_count=len(frame),raw_count=len(payload['elements']),gpkg_sha256=sha(path),gpkg_bytes=path.stat().st_size)
        sources[kind]=metadata;print(kind,len(frame),flush=True)
    manifest={'dataset_id':'goslar_multiriver_osm_v1','licence':'ODbL; OpenStreetMap contributors','source_bounds_epsg32632':BOUNDS,'query_bounds_epsg4326':[west,south,east,north],'source_buffer_m':3000,'coverage_policy':'Roads complete only over evaluation boundary buffered3050m, within finite query window; disjoint child windows explicitly skipped, never treated as empty source. Facilities complete over full query window. Full returned ways and representative facility centers retained.','facility_selection':'Original seven classes and amenity-or-railway-or-power-or-man_made precedence','roads_selection':'All highway ways','snapshot_note':'Live snapshot; original model used older snapshot. Temporal changes possible.','sources':sources}
    rectangles=[]
    for parent in sources['roads']['tile_requests']:
        for record in parent.get('children',[parent]):
            if record.get('status')=='outside_required_support':continue
            qs,qw,qn,qe=map(float,re.search(r'way\["highway"\]\(([^)]+)\)',record['query']).group(1).split(','))
            rectangles.append(box(qw,qs,qe,qn))
    query_support=unary_union(rectangles)
    assert support.difference(query_support).area<1e-12
    support_path=RAW/'road_query_support.geojson'
    support_path.write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','properties':{'kind':'successful_query_support','crs':'EPSG4326'},'geometry':mapping(query_support)}]}))
    sources['roads'].update(query_support_path=str(support_path.relative_to(ROOT)),query_support_sha256=sha(support_path),required_support_uncovered_area_degrees2=support.difference(query_support).area,required_support_buffer_m=3050)
    (RAW/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
