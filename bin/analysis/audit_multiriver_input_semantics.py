#!/usr/bin/env python3
"""TOOLING: scale/contribution and retained facility-source audit; no model writes."""
import json
import zipfile
import hashlib
from pathlib import Path
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, box
from compare_goslar_multiriver import ROOT,BASE,read_grid,raster_mask,clean_ring,write_csv,sha
OUT=BASE.parent/'input_semantics_followup_v1'
ALIASES={'land_cover_pressure':'Land-cover runoff tendency proxy','bare_soil_vegetation_loss':'2018–2024 tree-cover decline share','built_agriculture_road_expansion':'Current built-up or cropland and road-proximity proxy','road_access_proximity':'Road proximity (20 km decay)','settlement_population':'Published census population component','critical_infrastructure':'Proximity to filtered OSM facilities (2 km decay)','water_wetland_context':'Water or wetland proximity (10 km decay)','protected_ecological_context':'Natura2000 protected-area proximity (10 km decay)','soil_k_factor':'Relative soil erodibility','ls_factor':'Hillslope LS factor (channels excluded)','c_factor':'Land-cover-assigned cover-management factor','rainfall_climatology':'Rainfall climatology indicator','twi_wetness':'Topographic wetness index','drainage_proximity':'Drainage-network proximity'}
def main():
 OUT.mkdir(parents=True,exist_ok=True);inputs={}
 def pin(p):inputs[str(p.relative_to(ROOT))]=sha(p);return p
 archive=pin(ROOT/'data/tmp/zensus2022_goslar/Zensus2022_Bevoelkerungszahl.zip')
 with zipfile.ZipFile(archive) as z:
  documentation=z.read('Datensatzbeschreibung_Bevoelkerungszahl_Gitterzellen.xlsx')
 assert hashlib.sha256(documentation).hexdigest()=='7bb3470e7edda1491e1095a4fecae622fd453abe86a937c8a4e2d14742adcc80'
 (OUT/'population_source_evidence.json').write_text(json.dumps(dict(source_url='https://www.zensus2022.de/static/Zensus_Veroeffentlichung/Zensus2022_Bevoelkerungszahl.zip',version='2 / 2024-09-30',metadata_sha256=hashlib.sha256(documentation).hexdigest(),evidence_cells=['Erläuterungen!B14','Erläuterungen!B16','Erläuterung zu CSV pro 100 m!B22'],interpretation='Published omission can mean true zero or CKM-induced zero; do not identify underlying true population per cell'),indent=2)+'\n')
 prior=json.loads(pin(BASE.parent/'component_semantics_v1/manifest.json').read_text())
 for rel,h in prior['inputs'].items():assert sha(pin(ROOT/rel))==h,rel
 m=json.loads((BASE/'chain/priority_scenarios/run_manifest.json').read_text());pim,ref=read_grid(ROOT/m['priority_raster_lineage']['path']);valid=np.isfinite(pim)
 components={};special={'water_wetland_context':'environmental_sensitivity_v0_1/water_wetland_context_0_1.tif','protected_ecological_context':'environmental_sensitivity_v0_1/protected_area_context_0_1.tif','settlement_population':'exposure_indicators/population_exposure_0_1.tif','critical_infrastructure':'exposure_indicators/built_infrastructure_exposure_0_1.tif'}
 for ws in m['component_weights'].values():
  for k in ws:components[k]=read_grid(pin(BASE/'chain'/special.get(k,f'criteria_stack/criteria/{k}_0_1.tif')),ref)[0]
 src=pin(BASE.parent/'multiriver_comparison_v1/comparison_boundaries.gpkg');ps=gpd.read_file(src,layer='products');ex=gpd.read_file(src,layer='ring_exclusion').geometry.union_all();zones={'whole_model':valid}
 geozones={}
 for _,p in ps[ps.family=='regulatory'].iterrows():
  a=raster_mask(p.geometry,ref)&valid
  if not a.any():continue
  zones[p.river+'_inside']=a;zones[p.river+'_ring']=raster_mask(clean_ring(p.geometry,1000,ex),ref)&~raster_mask(ex,ref)&~a&valid
  geozones[p.river]=p.geometry
 rows=[];contributions={}
 for criterion,ws in m['component_weights'].items():
  den=sum(w*np.isfinite(components[k]) for k,w in ws.items())
  for k,w in ws.items():
   ew=np.divide(w*np.isfinite(components[k]),den,out=np.zeros(pim.shape),where=den>0)
   c=np.nan_to_num(components[k])*ew*m['main_weights'][criterion];contributions[k]=c
   for name,z in zones.items():
    x=components[k][z&np.isfinite(components[k])];cc=c[z]
    rows.append(dict(zone=name,criterion=criterion,component=k,display_name=ALIASES[k],zone_cells=int(z.sum()),available_cells=len(x),missing_fraction=1-len(x)/z.sum(),nominal_component_weight=w,mean_effective_weight=float(ew[z].mean()),score_mean=float(x.mean()) if len(x) else None,score_std=float(x.std()) if len(x) else None,score_p05=float(np.quantile(x,.05)) if len(x) else None,score_p95=float(np.quantile(x,.95)) if len(x) else None,zero_fraction=float((x==0).mean()) if len(x) else None,pim_contribution_mean=float(cc.mean()),pim_contribution_std=float(cc.std())))
 error=float(np.max(abs(sum(contributions.values())[valid]-pim[valid])));assert error<1e-6
 write_csv(OUT/'component_scales_and_contributions.csv',rows)
 write_csv(OUT/'indicator_names.csv',[dict(internal_key=k,display_name=v) for k,v in ALIASES.items()])
 raw=pin(ROOT/'data/raw/goslar_official_hydrology_and_flood_data/osm_goslar_infrastructure_overpass.json');payload=json.loads(raw.read_text());accepted={'school','hospital','fire_station','police','works','substation','station'};features=[]
 for e in payload['elements']:
  t=e.get('tags',{});chosen=t.get('amenity') or t.get('railway') or t.get('power') or t.get('man_made');loc=e if e['type']=='node' else e.get('center',{})
  if 'lon' not in loc:continue
  kept=chosen in accepted
  features.append(dict(osm_type=e['type'],osm_id=e['id'],legacy_kept=kept,selected_class=chosen or '',healthcare=t.get('healthcare',''),emergency=t.get('emergency',''),name=t.get('name',''),geometry=Point(loc['lon'],loc['lat'])))
 facilities=gpd.GeoDataFrame(features,crs=4326).to_crs(ref['crs'])
 original=gpd.read_file(pin(ROOT/'data/raw/goslar_official_hydrology_and_flood_data/osm_goslar_infrastructure_candidates.gpkg')).to_crs(ref['crs'])
 assert set(zip(facilities.loc[facilities.legacy_kept,'osm_type'],facilities.loc[facilities.legacy_kept,'osm_id'].astype(str)))==set(zip(original.osm_type,original.osm_id.astype(str)))
 facilities.to_file(OUT/'facility_filter_audit.gpkg',layer='queried_objects',driver='GPKG')
 dropped=facilities[~facilities.legacy_kept];fc=[]
 for river,geo in geozones.items():
  # Use same set of scored cell centers as comparison; distances are point-proxy diagnostics.
  z=zones[river+'_inside'];rr,cc=np.where(z);import rasterio
  x,y=rasterio.transform.xy(ref['transform'],rr,cc);pts=gpd.GeoSeries(gpd.points_from_xy(x,y),crs=ref['crs'])
  grid=box(*rasterio.transform.array_bounds(ref['height'],ref['width'],ref['transform']))
  for label,frame in [('retained',facilities[facilities.legacy_kept]),('retained_inside_grid',facilities[facilities.legacy_kept & facilities.geometry.within(grid)]),('excluded_from_query',dropped)]:
   union=frame.geometry.union_all();distance=pts.distance(union).to_numpy() if len(frame) else np.full(len(pts),np.nan)
   fc.append(dict(river=river,selection=label,objects_within_2km_of_scored_centers=int(frame.geometry.distance(pts.union_all()).le(2000).sum()) if len(frame) else 0,scored_cells=len(pts),nearest_distance_mean_m=float(np.mean(distance)) if len(frame) else None,point_distance_score_mean=float(np.clip(1-distance/2000,0,1).mean()) if len(frame) else None,original_raster_score_mean=float(components['critical_infrastructure'][z].mean()),cells_with_object_within_2km=int((distance<=2000).sum())))
 write_csv(OUT/'facility_nearby_summary.csv',fc)
 (OUT/'facility_filter_summary.json').write_text(json.dumps(dict(raw_objects=len(payload['elements']),located_objects=len(facilities),retained=len(original),excluded=len(dropped),excluded_healthcare=int(dropped.healthcare.ne('').sum()),excluded_emergency=int(dropped.emergency.ne('').sum()),policy='Diagnostic inventory only; no excluded object added to model; suitability and completeness unverified'),indent=2)+'\n')
 pin(Path(__file__))
 for p,h in inputs.items():assert sha(ROOT/p)==h
 (OUT/'manifest.json').write_text(json.dumps(dict(claim_level='diagnostic_only',command='.venv/bin/python bin/analysis/audit_multiriver_input_semantics.py',model_changed=False,contribution_reconstruction_error=error,inputs=inputs,outputs={p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json'}),indent=2)+'\n')
 print('Completed',len(rows),'scale rows;',len(dropped),'excluded facility objects')
if __name__=='__main__':main()
