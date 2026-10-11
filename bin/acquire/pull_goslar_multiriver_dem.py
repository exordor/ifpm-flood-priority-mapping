#!/usr/bin/env python3
"""TOOLING: acquire three additional public Copernicus GLO30 source tiles."""
from pathlib import Path
import hashlib,json,urllib.request
import rasterio
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/raw/copernicus_dem_30m_goslar_multiriver'
TMP=ROOT/'data/tmp/copernicus_dem_30m_goslar_multiriver'
def main():
 OUT.mkdir(parents=True,exist_ok=True);TMP.mkdir(parents=True,exist_ok=True)
 records=[]
 for lat,lon in [(51,9),(52,9),(52,10)]:
  name=f'Copernicus_DSM_COG_10_N{lat:02d}_00_E{lon:03d}_00_DEM'
  url=f'https://copernicus-dem-30m.s3.amazonaws.com/{name}/{name}.tif'
  path=OUT/f'{name}.tif';tmp=TMP/f'{name}.tif.partial'
  if not path.exists():
   print('Download',name,flush=True)
   with urllib.request.urlopen(url,timeout=120) as src,tmp.open('wb') as dst:
    while chunk:=src.read(1024*1024):dst.write(chunk)
   with rasterio.open(tmp) as ds:
    assert ds.crs.to_epsg()==4326 and ds.width>0 and ds.height>0
   tmp.replace(path)
  with rasterio.open(path) as ds:meta={'crs':str(ds.crs),'bounds':list(ds.bounds),'shape':ds.shape,'nodata':ds.nodata}
  records.append({'path':str(path.relative_to(ROOT)),'source_url':url,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),**meta})
 original=ROOT/'data/raw/copernicus_dem_30m_goslar/Copernicus_DSM_COG_10_N51_00_E010_00_DEM.tif'
 records.append({'path':str(original.relative_to(ROOT)),'reused':True,'sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'bytes':original.stat().st_size})
 (OUT/'source_manifest.json').write_text(json.dumps({'dataset_id':'copernicus_dem_30m_goslar_multiriver','access_date':'2026-09-14','licence':'Copernicus DEM licence','files':records},indent=2)+'\n')
 print(json.dumps(records,indent=2))
if __name__=='__main__':main()
