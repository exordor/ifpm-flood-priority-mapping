#!/usr/bin/env python3
"""TOOLING: full-feature official EEA Natura2024 extended source acquisition."""
import urllib.request,urllib.parse,json,hashlib
from pathlib import Path
import geopandas as gpd
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'data/raw/eea_natura2000_goslar_multiriver'
SERVICE='https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/Natura2000Sites/MapServer'
BBOX=[545411,5727748,625576,5802557]
def query(url,params):
 with urllib.request.urlopen(url+'?'+urllib.parse.urlencode(params),timeout=120) as r:j=json.load(r)
 if 'error' in j:raise RuntimeError(j['error'])
 return j
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 meta=query(SERVICE,{'f':'json'});assert '2024' in meta['description'];(OUT/'service_metadata.json').write_text(json.dumps(meta,indent=2))
 records=[];allfeatures=[]
 for layer,label in [(0,'FFH'),(1,'SPA')]:
  base={'f':'json','where':'1=1','geometry':','.join(map(str,BBOX)),'geometryType':'esriGeometryEnvelope','inSR':32632,'spatialRel':'esriSpatialRelIntersects','returnIdsOnly':'true'}
  ids=sorted(query(f'{SERVICE}/{layer}/query',base)['objectIds']);features=[]
  for i in range(0,len(ids),40):
   q={'f':'geojson','objectIds':','.join(map(str,ids[i:i+40])),'outFields':'*','outSR':4326,'returnGeometry':'true'}
   result=query(f'{SERVICE}/{layer}/query',q);assert not result.get('exceededTransferLimit',False);features+=result['features']
  assert len(features)==len(ids)
  for f in features:f['properties'].update(source_layer=layer,directive_class=label,source='EEA Natura2000 2024')
  p=OUT/f'layer_{layer}.geojson';p.write_text(json.dumps({'type':'FeatureCollection','features':features}))
  allfeatures+=features;records.append({'layer':layer,'label':label,'query':base,'object_ids':ids,'feature_count':len(features)})
 v=gpd.GeoDataFrame.from_features(allfeatures,crs=4326);v.to_file(OUT/'protected.gpkg',layer='protected',driver='GPKG')
 files=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(OUT.iterdir()) if p.name!='source_manifest.json']
 (OUT/'source_manifest.json').write_text(json.dumps({'dataset_id':'eea_natura2000_goslar_multiriver','source_url':SERVICE,'product_version':2024,'access_date':'2026-09-14','licence':'EEA reuse policy','geometry_clipped':False,'query_records':records,'files':files},indent=2)+'\n')
 print(json.dumps({'features':len(v),'counts':[r['feature_count'] for r in records],'columns':list(v.columns)},indent=2))
if __name__=='__main__':main()
