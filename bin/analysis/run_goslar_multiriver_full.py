#!/usr/bin/env python3
"""TOOLING: full retained flood-product extent; frozen scale, isolated outputs."""
import sys,json,math,zipfile
from pathlib import Path
import numpy as np,geopandas as gpd,pandas as pd,rasterio
from rasterio.features import geometry_mask,rasterize
from rasterio.transform import from_origin
from rasterio.warp import reproject,Resampling,transform_bounds
from scipy.ndimage import distance_transform_edt
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'bin'),str(Path(__file__).parent)]
from run_abzucht_expanded import load
from abzucht_fixed_scale_normalization import apply
from compare_goslar_multiriver import BASE,sha,read_grid,raster_mask,clean_ring,write_csv,stats,make_map
from repair_abzucht_gaps import census_grid
from tune_abzucht_weights import weights_at,score_at
OUT=ROOT/'outputs/goslar_multiriver_full_extent/fixed_scale'

def main():
 # Full runs deliberately recompute stages; stale checkpoints are never trusted.
 OUT.mkdir(parents=True,exist_ok=True);inputs={}
 def pin(p):inputs[str(p.relative_to(ROOT))]=sha(p);return p
 oldm=json.loads(pin(BASE/'chain/priority_scenarios/run_manifest.json').read_text())
 for e in [oldm['priority_raster_lineage'],*oldm['criterion_raster_lineage'].values()]:assert sha(pin(ROOT/e['path']))==e['sha256']
 old,oref=read_grid(ROOT/oldm['priority_raster_lineage']['path']);oldgeom=gpd.read_file(pin(BASE/'expanded_boundary.gpkg')).geometry.union_all()
 ps=gpd.read_file(pin(BASE.parent/'multiriver_comparison/comparison_boundaries.gpkg'),layer='products');allflood=ps.geometry.union_all();geom=oldgeom.union(allflood.buffer(2000))
 t=oref['transform'];minx,miny,maxx,maxy=geom.bounds;x=t.c+math.floor((minx-t.c)/30)*30;y=t.f+math.ceil((maxy-t.f)/30)*30
 ref=dict(oref,width=math.ceil((maxx-x)/30),height=math.ceil((y-miny)/30),transform=from_origin(x,y,30,30));shape=(ref['height'],ref['width']);mask=raster_mask(geom,ref)
 bc=334;bref=dict(ref,width=ref['width']+2*bc,height=ref['height']+2*bc,transform=ref['transform']*rasterio.Affine.translation(-bc,-bc));crop=(slice(bc,bc+shape[0]),slice(bc,bc+shape[1]))
 gpd.GeoDataFrame({'boundary_id':['goslar_multiriver_full_extent']},geometry=[geom],crs=ref['crs']).to_file(OUT/'expanded_boundary.gpkg',layer='expanded_boundary',driver='GPKG')
 ps.to_file(OUT/'comparison_boundaries.gpkg',layer='products',driver='GPKG');ps.drop(columns='geometry').to_csv(OUT/'source_inventory.csv',index=False)
 c=load('multiriver_chain',ROOT/'bin/factors/run_goslar_pim_chain.py');paths={k:v for k,v in vars(c).items() if isinstance(v,Path)}
 for key,p in paths.items():
  if p.is_relative_to(paths['OUT_BASE']):setattr(c,key,OUT/'chain'/p.relative_to(paths['OUT_BASE']))
  elif p.is_relative_to(paths['WC_DIR']):setattr(c,key,OUT/'landcover'/p.relative_to(paths['WC_DIR']))
 c.BOUNDARY_GPKG=OUT/'expanded_boundary.gpkg';c.BOUNDARY_LAYER='expanded_boundary';c.FOCUS_AREA_ID='goslar_multiriver_full_extent';c.SOILGRIDS_K_SNAPSHOT=ROOT/'data/raw/soilgrids_250m_goslar_multiriver/k_factor_0_30cm_avg_250m_us.tif'
 c.ROADS=ROOT/'data/raw/goslar_multiriver_osm/roads.gpkg';c.INFRASTRUCTURE=ROOT/'data/raw/goslar_multiriver_osm/facilities.gpkg';c.PROTECTED_RAW=ROOT/'data/raw/eea_natura2000_goslar_multiriver/protected.gpkg';c.ZENSUS_RAW=OUT/'sources';c.CLMS_BARE_SOIL=paths['CLMS_BARE_SOIL']
 # Require complete acquisition manifests before any expensive model stage.
 osm=json.loads(pin(c.ROADS.parent/'source_manifest.json').read_text())
 for name in ['roads','facilities']:
  assert sha(pin(c.ROADS.parent/f'{name}.gpkg'))==osm['sources'][name]['gpkg_sha256']
 assert osm['sources']['roads'].get('acquisition_complete') is True, 'Road acquisition must be complete for required source support'
 for meta in [c.PROTECTED_RAW.parent/'source_manifest.json',ROOT/'data/raw/copernicus_dem_30m_goslar_multiriver/source_manifest.json',c.SOILGRIDS_K_SNAPSHOT.parent/'soilgrids_goslar_diagnostics.json']:pin(meta)
 anchors=json.loads(pin(BASE/'frozen_normalization.json').read_text());(OUT/'frozen_normalization.json').write_text(json.dumps(anchors,indent=2)+'\n');stage='';index=0
 def norm(data,mask=None,**kwargs):
  nonlocal index
  par=anchors[f'{stage}:{index}'];index+=1;return apply(data,par,mask),par['clip_low'],par['clip_high']
 c.percentile_minmax=norm;c.normalize_2_98=norm
 def write(p,a,profile=ref,masked=True):
  p.parent.mkdir(parents=True,exist_ok=True);a=a.copy()
  if masked:a[~mask]=np.nan
  c.write_raster(p,np.where(np.isfinite(a),a,c.NODATA),profile['transform'],profile['crs'])
 def warp(p,profile=ref,resampling=Resampling.nearest,percent=False):
  pin(p)
  with rasterio.open(p) as ds:
   out=np.full((profile['height'],profile['width']),np.nan,'float32')
   source=rasterio.band(ds,1);source_transform=ds.transform;source_nodata=ds.nodata
   if percent:
    bounds=transform_bounds(profile['crs'],ds.crs,*rasterio.transform.array_bounds(profile['height'],profile['width'],profile['transform']),densify_pts=21)
    w=rasterio.windows.from_bounds(*bounds,ds.transform).round_offsets().round_lengths();w=rasterio.windows.Window(w.col_off-3,w.row_off-3,w.width+6,w.height+6)
    source=ds.read(1,window=w,boundless=True,masked=True).astype('float32').filled(np.nan);source[(source<0)|(source>100)]=np.nan;source_transform=ds.window_transform(w);source_nodata=np.nan
   reproject(source,out,src_transform=source_transform,src_crs=ds.crs,src_nodata=source_nodata,dst_transform=profile['transform'],dst_crs=profile['crs'],dst_nodata=np.nan,resampling=resampling)
  return out
 checkpoint=OUT/'checkpoints';checkpoint.mkdir(exist_ok=True)
 def run(name,fn):
  nonlocal stage,index
  stage=name;index=0
  print('Run',name,flush=True);fn();(checkpoint/name).write_text('complete\n')
 def terrain():
  files=[ROOT/'data/raw/copernicus_dem_30m_goslar/Copernicus_DSM_COG_10_N51_00_E010_00_DEM.tif',*sorted((ROOT/'data/raw/copernicus_dem_30m_goslar_multiriver').glob('*.tif'))]
  if len(files)!=4:raise ValueError('Four DEMtiles required')
  dem=np.full((bref['height'],bref['width']),np.nan,'float32')
  for p in files:
   a=warp(p,bref,Resampling.bilinear);z=np.isfinite(a);dem[z]=a[z]
  if not np.isfinite(dem).all():raise ValueError('DEM canvas gaps')
  write(c.DEM_BUFFERED,dem,bref,False);write(c.DEM,dem[crop])
  gy,gx=np.gradient(dem.astype('float64'),30,30);s=np.degrees(np.arctan(np.hypot(gx,gy)))
  write(c.SLOPE_BUFFERED,s,bref,False);write(c.SLOPE,s[crop])
 run('terrain',terrain)
 def landcover():
  wc=warp(paths['WORLDCOVER_FILE']);assert np.isfinite(wc[mask]).all()
  for lut,p in [('WORLDCOVER_CFACTOR_LUT',c.CFACTOR),('LAND_USE_PRESSURE_LUT',c.LAND_USE_PRESSURE),('LAND_COVER_RUNOFF_LUT',c.LAND_COVER_RUNOFF),('BARE_SOIL_LOSS_LUT',c.BARE_SOIL_LOSS),('BUILT_UP_LUT',c.BUILT_UP_PRESSURE),('AGRICULTURAL_LUT',c.AGRICULTURAL_PRESSURE)]:
   a=np.full(shape,np.nan,'float32')
   for k,v in getattr(c,lut).items():a[wc==k]=v
   write(p,a)
  tcd={yr:warp(ROOT/f'data/raw/clms_hrl_tcd_goslar_official_basin/{yr}/goslar_official_basin_tcd_{yr}_10m_mosaic.tif',resampling=Resampling.average,percent=True) for yr in [2018,2024]}
  for a in tcd.values():a[(a<0)|(a>100)]=np.nan
  write(c.CLMS_TCD_LOSS,np.clip((tcd[2018]-tcd[2024])/100,0,1));write(OUT/'landcover/worldcover_aligned.tif',wc)
 run('landcover',landcover)
 def hydrology():
  tmp=OUT/'tmp_hydrology';tmp.mkdir(exist_ok=True)
  filled=tmp/'filled.tif';pointer=tmp/'pointer.tif';acc=tmp/'acc.tif';sca=tmp/'sca.tif';twi=tmp/'twi.tif'
  c.run_wbt('fill_depressions_wang_and_liu',dem=str(c.DEM_BUFFERED),output=str(filled),fix_flats=True)
  c.run_wbt('d8_pointer',dem=str(filled),output=str(pointer),esri_pntr=False)
  for output,kind in [(acc,'cells'),(sca,'specific contributing area')]:c.run_wbt('d8_flow_accumulation',i=str(pointer),output=str(output),out_type=kind,pntr=True,esri_pntr=False)
  c.run_wbt('wetness_index',sca=str(sca),slope=str(c.SLOPE_BUFFERED),output=str(twi))
  for source,target in [(filled,c.FILLED),(pointer,c.D8_PNTR),(acc,c.FLOW_ACC_CELLS),(sca,c.FLOW_ACC_SCA),(twi,c.TWI)]:
   a=read_grid(source)[0];write(target,a[crop])
  flow=read_grid(acc)[0];streams=np.isfinite(flow)&(flow>500);distance=distance_transform_edt(~streams,sampling=(30,30));write(c.DISTANCE,distance[crop]);write(c.STREAMS_T500,streams[crop].astype('float32'))
 run('hydrology',hydrology);run('ls_factor',c.stage_ls_factor)
 run('soilgrids_kfactor',lambda:(pin(c.SOILGRIDS_K_SNAPSHOT),c.stage_soilgrids_kfactor()))
 def proximity(geometries,decay,buffer=10020):
  pad=math.ceil(buffer/30);prof=dict(ref,width=ref['width']+2*pad,height=ref['height']+2*pad,transform=ref['transform']*rasterio.Affine.translation(-pad,-pad))
  a=rasterize([(g,1) for g in geometries],out_shape=(prof['height'],prof['width']),transform=prof['transform'],fill=0,dtype='uint8');assert a.any()
  d=distance_transform_edt(a==0,sampling=(30,30))[pad:pad+shape[0],pad:pad+shape[1]];return np.clip(1-d/decay,0,1),d
 def roads():
  frame=gpd.read_file(pin(c.ROADS)).to_crs(ref['crs']);a,d=proximity(frame.geometry,20000,3000)
  # Query is at least3km outside target bounding rectangle; if nearest road is
  # closer, unseen roads beyond query cannot be closer.
  if d[mask].max()>=3000:raise ValueError('Road querybuffer insufficient for nearest-neighbour coverage')
  write(c.ROAD_ACCESS,a)
 run('osm_roads',roads)
 for path in c.REGNIE_RAW_DIR.glob('raw/*.asc.gz'):pin(path)
 run('rainfall',c.stage_rainfall)
 def protected():
  a,_=proximity(gpd.read_file(pin(c.PROTECTED_RAW)).to_crs(ref['crs']).geometry,10000);write(c.ES_DIR/'protected_area_context_0_1.tif',a)
 run('protected_areas',protected);run('criteria_stack',c.stage_criteria_stack)
 def exposure():
  with zipfile.ZipFile(pin(ROOT/'data/tmp/zensus2022_goslar/Zensus2022_Bevoelkerungszahl.zip')) as z:frame=pd.read_csv(z.open('Zensus2022_Bevoelkerungszahl_100m-Gitter.csv'),sep=';')
  bounds=transform_bounds(ref['crs'],3035,*rasterio.transform.array_bounds(*shape,ref['transform']),densify_pts=21)
  selected,a,p=census_grid(frame,bounds);f=OUT/'sources/population_native_100m.tif';write(f,a,p,False)
  dest=np.full(shape,np.nan,'float32');reproject(a,dest,src_transform=p['transform'],src_crs=p['crs'],dst_transform=ref['transform'],dst_crs=ref['crs'],resampling=Resampling.sum);pin(f);dest[~mask]=np.nan
  if np.any(mask&(dest==0)):raise ValueError('Unexpected zero population after legacy warp; inspect source-domain coverage')
  std,_,_=norm(dest,mask,constant_policy='zeros')
  write(c.EXPOSURE_DIR/'population_exposure_0_1.tif',std)
  infra,_=proximity(gpd.read_file(pin(c.INFRASTRUCTURE)).to_crs(ref['crs']).geometry,2000,2040)
  write(c.EXPOSURE_DIR/'built_infrastructure_exposure_0_1.tif',infra)
 run('exposure_indicators',exposure)
 def environment():
  wc=warp(paths['WORLDCOVER_FILE'],bref);assert np.isfinite(wc).all();a=np.isin(wc,[80,90]);distance=distance_transform_edt(~a,sampling=(30,30));water=np.clip(1-distance[crop]/10000,0,1);write(c.ES_DIR/'water_wetland_context_0_1.tif',water)
 run('environmental_sensitivity',environment)
 # Avoid legacy metadata references to files no longer used by this bounded wrapper.
 oldlineage=c.lineage_record
 c.lineage_record=lambda p: oldlineage(p) if p.exists() else {'path':str(p.relative_to(ROOT)),'status':'not_used_by_expanded_wrapper'}
 run('priority_scenarios',c.stage_priority_scenarios)
 nmfile=c.SCENARIO_DIR/'run_manifest.json';nm=json.loads(nmfile.read_text());nm.update(boundary_id='goslar_multiriver_full_extent',experiment_id='fixed_scale',claim_level='diagnostic_only');nm['normalization']['method']='Original frozen anchors; no refit'
 nm['focus_area_name']='Original model union all retained official flood products plus 2km buffer'
 nm['boundary_contract']={'id':'goslar_multiriver_full_extent','source':'old model union retained flood polygons plus 2km','area_km2':geom.area/1e6,'claim':'comparison domain, not hydrologic catchment'}
 nm['hydrology_buffer_m']=10020;nm['data_sources']['dem']='Four Copernicus GLO30 tiles N51/N52 E009/E010';nm['input_lineage']['population']=oldlineage(OUT/'sources/population_native_100m.tif')
 nm['input_lineage']['wrapper']=oldlineage(Path(__file__));nm['input_lineage']['dem_tiles']=[oldlineage(ROOT/r) for r in inputs if 'Copernicus_DSM_' in r]
 nm['normalization']['frozen_parameters']=str((OUT/'frozen_normalization.json').relative_to(ROOT));nm['note']='Expanded controlled comparison; data gaps retained; new source versions and larger hydrology can change overlap'
 nm['input_lineage'].pop('dem',None);nm['input_lineage'].pop('clms_bare_soil',None);nm['data_sources'].pop('clms_bare_soil',None)
 nmfile.write_text(json.dumps(nm,indent=2)+'\n')
 pim=read_grid(ROOT/nm['priority_raster_lineage']['path'],ref)[0];criteria={k:read_grid(ROOT/e['path'],ref)[0] for k,e in nm['criterion_raster_lineage'].items()};valid=np.isfinite(pim);scores={34:pim}
 for pct in [50,60,70]:scores[pct]=score_at(criteria,weights_at(nm['main_weights'],pct/100),valid);write(OUT/f'pim_flood_{pct}.tif',scores[pct])
 coverage=[];rows=[];all_masks={t:raster_mask(allflood,ref,t) for t in [False,True]};masked_flood=np.where(valid,criteria['flood_hazard'],np.nan)
 for _,p in ps.iterrows():
  inside=raster_mask(p.geometry,ref);ring=raster_mask(clean_ring(p.geometry,1000,allflood),ref)&~all_masks[False]
  coverage.append(dict(product_id=p.product_id,river=p.river,family=p.family,scenario=p.scenario,source_area_km2=p.geometry.area/1e6,geometric_coverage=p.geometry.intersection(geom).area/p.geometry.area,total_cells=int(inside.sum()),scored_cells=int((inside&valid).sum()),unscored_cells=int((inside&~valid).sum())))
  for touched in [False,True]:
   target=raster_mask(p.geometry,ref,touched)
   for radius in [500,1000,2000]:
    control=raster_mask(clean_ring(p.geometry,radius,allflood),ref,touched)&~all_masks[touched]&~target
    for pct,s in scores.items():
     for zone,z in [('inside',target),('ring',control)]:
      for metric,a in [('PIM',s),('Flood indicator',masked_flood)]:rows.append(dict(product_id=p.product_id,river=p.river,family=p.family,scenario=p.scenario,flood_percent=pct,inclusion='all_touched' if touched else 'center',radius_m=radius,metric=metric,zone=zone,**stats(a,z)))
 write_csv(OUT/'coverage.csv',coverage);write_csv(OUT/'comparison.csv',rows)
 availability=[]
 for path in list(c.CRITERIA_DIR.glob('*_0_1.tif'))+[c.EXPOSURE_DIR/'population_exposure_0_1.tif',c.EXPOSURE_DIR/'built_infrastructure_exposure_0_1.tif',c.ES_DIR/'protected_area_context_0_1.tif',c.ES_DIR/'water_wetland_context_0_1.tif']:
  a=read_grid(path,ref)[0];availability.append(dict(layer=path.stem,valid_cells=int((mask&np.isfinite(a)).sum()),total_cells=int(mask.sum())))
 write_csv(OUT/'component_coverage.csv',availability)
 oldaligned=np.full(shape,np.nan,'float32');reproject(old,oldaligned,src_transform=oref['transform'],src_crs=oref['crs'],src_nodata=np.nan,dst_transform=ref['transform'],dst_crs=ref['crs'],dst_nodata=np.nan,resampling=Resampling.nearest)
 both=np.isfinite(oldaligned)&valid;write(OUT/'old_area_delta.tif',np.where(both,pim-oldaligned,np.nan))
 overlap=[]
 for key,entry in oldm['criterion_raster_lineage'].items():
  a,pr=read_grid(ROOT/entry['path']);aligned=np.full(shape,np.nan,'float32');reproject(a,aligned,src_transform=pr['transform'],src_crs=pr['crs'],src_nodata=np.nan,dst_transform=ref['transform'],dst_crs=ref['crs'],dst_nodata=np.nan,resampling=Resampling.nearest)
  z=np.isfinite(aligned)&np.isfinite(criteria[key]);d=criteria[key][z]-aligned[z]
  overlap.append(dict(criterion=key,common_cells=int(z.sum()),old_mean=float(aligned[z].mean()),new_mean=float(criteria[key][z].mean()),mean_signed_change=float(d.mean()),mean_absolute_change=float(abs(d).mean()),max_absolute_change=float(abs(d).max())))
 write_csv(OUT/'old_area_criterion_changes.csv',overlap)
 comparison=dict(common_cells=int(both.sum()),mean_absolute_change=float(np.abs(pim[both]-oldaligned[both]).mean()),max_absolute_change=float(np.abs(pim[both]-oldaligned[both]).max()))
 primary=[dict(p) for _,p in ps[ps.family=='regulatory'].iterrows()]
 for pct,s in scores.items():make_map(OUT/f'overview_{pct}',f'Goslar region | Flood weight {pct}%',primary,geom.bounds,criteria['flood_hazard'],s,ref)
 for p in primary:make_map(OUT/p['river'].lower(),p['river']+' | Expanded coverage', [p],p['geometry'].buffer(500).bounds,criteria['flood_hazard'],pim,ref)
 for _,p in ps[ps.family!='regulatory'].iterrows():make_map(OUT/str(p.product_id),f'{p.river} | {p.scenario}',[dict(p)],p.geometry.buffer(500).bounds,criteria['flood_hazard'],pim,ref)
 pin(Path(__file__));pin(ROOT/'bin/factors/run_goslar_pim_chain.py')
 for helper in ['abzucht_fixed_scale_normalization.py','compare_goslar_multiriver.py','repair_abzucht_gaps.py','tune_abzucht_weights.py']:pin(Path(__file__).parent/helper)
 for path,h in inputs.items():assert sha(ROOT/path)==h,path
 report=dict(boundary_id='goslar_multiriver_full_extent',experiment_id='fixed_scale',claim_level='diagnostic_only',area_km2=geom.area/1e6,grid_shape=list(shape),target_cells=int(mask.sum()),scored_cells=int(valid.sum()),hydrology_buffer_m=10020,flow_boundary_limitation='Buffered comparison domain, not a complete upstream catchment; hydrology may change on overlap',normalization='frozen original anchors',weights=nm['main_weights'],old_area_comparison=comparison,source_vintage_note=osm.get('snapshot_note','See pinned OSM source manifest for timestamps'),preprocessing_note='Overlap change includes differing vector snapshots, larger terrain domain and grid reprojection effects; native SoilGrids overlap was verified identical',inputs=inputs,command='.venv/bin/python bin/analysis/run_goslar_multiriver_full.py',coverage=coverage)
 (OUT/'expansion_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
