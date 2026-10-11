#!/usr/bin/env python3
"""TOOLING: read-back checks and English handoff for the expanded run."""
import json,sys
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd,rasterio
from rasterio.warp import reproject,Resampling
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from compare_goslar_multiriver import sha,read_grid,raster_mask,clean_ring,BASE
import compare_goslar_multiriver as maps
from matplotlib.ticker import MaxNLocator
OUT=ROOT/'outputs/goslar_multiriver_full_extent/fixed_scale'
def main():
 m=json.loads((OUT/'expansion_manifest.json').read_text());n=json.loads((OUT/'chain/priority_scenarios/run_manifest.json').read_text());old=json.loads((BASE/'chain/priority_scenarios/run_manifest.json').read_text())
 for p,h in m['inputs'].items():assert sha(ROOT/p)==h,p
 assert json.loads((OUT/'frozen_normalization.json').read_text())==json.loads((BASE/'frozen_normalization.json').read_text())
 pim,ref=read_grid(ROOT/n['priority_raster_lineage']['path']);_,oref=read_grid(ROOT/old['priority_raster_lineage']['path']);valid=np.isfinite(pim)
 assert ref['crs']==oref['crs'] and ref['transform'].a==30 and ref['transform'].e==-30
 assert abs((ref['transform'].c-oref['transform'].c)/30-round((ref['transform'].c-oref['transform'].c)/30))<1e-8
 assert abs((ref['transform'].f-oref['transform'].f)/30-round((ref['transform'].f-oref['transform'].f)/30))<1e-8
 products=gpd.read_file(OUT/'comparison_boundaries.gpkg',layer='products');boundary=gpd.read_file(OUT/'expanded_boundary.gpkg').geometry.union_all();mask=raster_mask(boundary,ref)
 assert len(products)==14 and products.product_id.is_unique and products.geometry.is_valid.all()
 assert all(g.difference(boundary).area<1e-5 for g in products.geometry)
 assert not (valid&~mask).any()
 criteria={k:read_grid(ROOT/e['path'],ref)[0] for k,e in n['criterion_raster_lineage'].items()}
 errors={}
 for pct in [34,50,60,70]:
  weights={k:(pct/100 if k=='flood_hazard' else v*(1-pct/100)/(1-.34)) for k,v in n['main_weights'].items()}
  a=pim if pct==34 else read_grid(OUT/f'pim_flood_{pct}.tif',ref)[0]
  assert np.array_equal(np.isfinite(a),valid)
  expected=sum(criteria[k]*v for k,v in weights.items());error=float(np.max(abs(a[valid]-expected[valid])));assert error<2e-6
  assert (a[valid]>=0).all() and (a[valid]<=1).all();errors[str(pct)]=error
 table=pd.read_csv(OUT/'comparison.csv');coverage=pd.read_csv(OUT/'coverage.csv')
 assert len(table)==1344 and not table.duplicated(['product_id','flood_percent','inclusion','radius_m','metric','zone']).any()
 assert (coverage.scored_cells+coverage.unscored_cells==coverage.total_cells).all()
 for _,p in products.iterrows():
  inside=raster_mask(p.geometry,ref);r=table[(table.product_id==p.product_id)&(table.flood_percent==34)&(table.inclusion=='center')&(table.radius_m==1000)&(table.metric=='PIM')&(table.zone=='inside')].iloc[0]
  z=inside&valid;assert int(r.valid_cells)==int(z.sum())
  assert abs(r['mean']-float(pim[z].mean()))<1e-6
  assert abs(r.high_share-float((pim[z]>=.6).mean()))<1e-9
 oldpop,op=read_grid(BASE/'chain/exposure_indicators/population_exposure_0_1.tif');newpop=read_grid(OUT/'chain/exposure_indicators/population_exposure_0_1.tif',ref)[0]
 aligned=np.full(pim.shape,np.nan,'float32');reproject(oldpop,aligned,src_transform=op['transform'],src_crs=op['crs'],src_nodata=np.nan,dst_transform=ref['transform'],dst_crs=ref['crs'],dst_nodata=np.nan,resampling=Resampling.nearest)
 common=np.isfinite(aligned)&np.isfinite(newpop);popdelta={'common_cells':int(common.sum()),'max_absolute_difference':float(abs(aligned[common]-newpop[common]).max()),'old_valid_now_absent':int((np.isfinite(aligned)&~np.isfinite(newpop)).sum())}
 qa={'status':'passed','products':len(products),'comparison_rows':len(table),'population_overlap':popdelta,'original_input_hashes_unchanged':True,'frozen_anchors_equal':True,'old_lattice_preserved':True,'all_products_geometrically_contained':True,'score_reconstruction_max_errors':errors,'target_cells':int(mask.sum()),'scored_cells':int(valid.sum()),'no_score_cells':int((mask&~valid).sum())}
 # Narrow river extents need explicit tick density after equal-aspect layout.
 original_subplots=maps.plt.subplots
 def sparse_subplots(*args,**kwargs):
  fig,axes=original_subplots(*args,**kwargs)
  for ax in np.asarray(axes).flat:ax.xaxis.set_major_locator(MaxNLocator(nbins=3))
  return fig,axes
 corrected=[]
 try:
  maps.plt.subplots=sparse_subplots
  for _,p in products.iterrows():
   bounds=p.geometry.buffer(500).bounds
   if (bounds[2]-bounds[0])/(bounds[3]-bounds[1])>=.50:continue
   name=p.river.lower() if p.family=='regulatory' else p.product_id
   title=p.river+' | Expanded coverage' if p.family=='regulatory' else f'{p.river} | {p.scenario}'
   maps.make_map(OUT/name,title,[dict(p)],bounds,criteria['flood_hazard'],pim,ref);corrected.append(name)
 finally:maps.plt.subplots=original_subplots
 qa['narrow_map_tick_corrections']=corrected;qa['report_tool_sha256']=sha(Path(__file__))
 (OUT/'validation.json').write_text(json.dumps(qa,indent=2)+'\n')
 def get(pid,metric,zone,pct=34):return table[(table.product_id==pid)&(table.flood_percent==pct)&(table.inclusion=='center')&(table.radius_m==1000)&(table.metric==metric)&(table.zone==zone)].iloc[0]
 text='# Multi-river comparison after boundary expansion\n\nThe new extent fully contains the 14 retained official flood-area sources and a 2 km outer reference zone, merged with the original model extent. Area: '+f"{m['area_km2']:.2f} km2; on the 30 m grid, {qa['target_cells']:,} cells lie in the assessment area, {qa['scored_cells']:,} cells have a composite PIM and {qa['no_score_cells']:,} cells have no score.\n\n"
 text+='## Results with the original 34% flood weight\n\nMeans are listed for inside the flood area / the outside 1 km ring; the ring excludes all acquired flood areas, and cells are assigned by cell center. Official designated extents are kept separate from hydraulic scenarios with an explicit return period, and announcement dates are not treated as flood-event years.\n\n|River/source|Scored cells/flood-area cells|Flood indicator inside/outside|PIM inside/outside|PIM≥0.6 inside|\n|---|---:|---:|---:|---:|\n'
 summary=[]
 for _,p in products.iterrows():
  pi=get(p.product_id,'PIM','inside');po=get(p.product_id,'PIM','ring');fi=get(p.product_id,'Flood indicator','inside');fo=get(p.product_id,'Flood indicator','ring');cv=coverage[coverage.product_id==p.product_id].iloc[0]
  text+=f'|{p.river} / {p.scenario}|{int(pi.valid_cells):,}/{int(cv.total_cells):,}|{fi["mean"]:.3f}/{fo["mean"]:.3f}|{pi["mean"]:.3f}/{po["mean"]:.3f}|{pi.high_share:.1%}|\n'
  summary.append({'product_id':p.product_id,'river':p.river,'scenario':p.scenario,'family':p.family,'inside_cells':int(pi.valid_cells),'ring_cells':int(po.valid_cells),'flood_inside':fi['mean'],'flood_outside':fo['mean'],'pim_inside':pi['mean'],'pim_outside':po['mean'],'pim_high_share':pi.high_share})
 pd.DataFrame(summary).to_csv(OUT/'summary.csv',index=False)
 sf=pd.DataFrame(summary);reg=sf[sf.family=='regulatory']
 text+='\nRivers whose mean flood indicator inside is higher than in the ring: '+ ', '.join(reg.loc[reg.flood_inside>reg.flood_outside,'river'])+'; not higher than the ring: '+(', '.join(reg.loc[reg.flood_inside<=reg.flood_outside,'river']) or 'none')+'.\n'
 text+='Rivers whose mean composite PIM inside is higher than in the ring: '+ ', '.join(reg.loc[reg.pim_inside>reg.pim_outside,'river'])+'; not higher than the ring: '+(', '.join(reg.loc[reg.pim_inside<=reg.pim_outside,'river']) or 'none')+'.\n'
 contribution=[];allflood=products.geometry.union_all()
 for _,p in products.iterrows():
  inside=raster_mask(p.geometry,ref)&valid;ring=raster_mask(clean_ring(p.geometry,1000,allflood),ref)&~raster_mask(allflood,ref)&valid
  for key,a in criteria.items():
   iv=float(a[inside].mean());ov=float(a[ring].mean());weight=n['main_weights'][key]
   contribution.append(dict(product_id=p.product_id,river=p.river,criterion=key,inside_mean=iv,ring_mean=ov,weight=weight,inside_contribution=iv*weight,ring_contribution=ov*weight,contribution_difference=(iv-ov)*weight))
 pd.DataFrame(contribution).to_csv(OUT/'criterion_comparison.csv',index=False)
 text+='\n## Weight sensitivity\n\n|River/source|34% PIM inside/outside|50% PIM inside/outside|60% PIM inside/outside|70% PIM inside/outside|\n|---|---:|---:|---:|---:|\n'
 for _,p in products.iterrows():
  text+='|'+p.river+' / '+p.scenario+'|'+ '|'.join(f'{get(p.product_id,"PIM","inside",w)["mean"]:.3f}/{get(p.product_id,"PIM","ring",w)["mean"]:.3f}' for w in [34,50,60,70])+'|\n'
 stability=[]
 for metric,pcts in [('Flood indicator',[34]),('PIM',[34,50,60,70])]:
  for pct in pcts:
   subset=table[(table.metric==metric)&(table.flood_percent==pct)]
   pivot=subset.pivot(index=['product_id','radius_m','inclusion'],columns='zone',values='mean')
   for pid,part in (pivot['inside']-pivot['ring']).groupby(level='product_id'):
    assert len(part)==6
    lo=float(part.min());hi=float(part.max());stability.append(dict(product_id=pid,metric=metric,flood_percent=pct,minimum_difference=lo,maximum_difference=hi,status='positive_all' if lo>0 else ('negative_all' if hi<0 else 'mixed')))
 stable=pd.DataFrame(stability);stable.to_csv(OUT/'sensitivity_stability.csv',index=False)
 text+='\n## Robustness to reference settings\n\nFor 12 sources, the mean flood indicator inside is higher than in the ring under all six settings. For Innerste HQ100/HQ25 it is only about 0.0034/0.0024 higher with center assignment and the 1 km ring, and the sign of the difference flips under other settings, so their consistency cannot be called clear. The 14 sources include different scenarios of the same river and cannot be treated as 14 independent rivers.\n\n'
 text+='|Flood weight|Inside PIM higher in all six settings|Direction varies with settings|Inside PIM lower in all six settings|\n|---|---:|---:|---:|\n'
 for pct in [34,50,60,70]:
  q=stable[(stable.metric=='PIM')&(stable.flood_percent==pct)]
  text+=f'|{pct}%|{int((q.status=="positive_all").sum())}|{int((q.status=="mixed").sum())}|{int((q.status=="negative_all").sum())}|\n'
 text+='\n## How to interpret\n\nExpanding the boundary fixes insufficient assessment coverage; it does not guarantee closer agreement between the indicators and the official flood areas. The flood indicator and the PIM are compared separately. Raising the flood weight brings the PIM closer to the existing flood indicator, but it does not correct the spatial pattern of the flood indicator itself. The detailed sensitivity table covers 500 m, 1 km and 2 km rings and two cell-assignment rules (center/touched); cells are not treated as independent samples for significance testing.\n\n'
 text+='The original normalization anchors and the original rule for population gaps are kept. Missing components are handled by redistributing the weight to the originally available components. Having a PIM score therefore does not mean that every component has data; see component_coverage.csv. The effect of missing components such as population or soil cannot be interpreted as genuinely low risk.\n\n'
 d=m['old_area_comparison'];text+=f'Relative to the original frozen 34% baseline without facility edge repair, the mean absolute PIM change over the {d["common_cells"]:,} overlapping cells of the original area is {d["mean_absolute_change"]:.6f}, and the maximum absolute change is {d["max_absolute_change"]:.6f}. Changes by criterion are in old_area_criterion_changes.csv. The enlarged flow-accumulation domain, changes in the reprojected grid, facility and water-body edge repair, and differences in source snapshot dates (OSM and others) all affect the old area, so the changes cannot all be attributed to the boundary itself. The original soil data are identical value by value where they overlap the old extent; part of the differences in the aligned raster comes from preprocessing, not from updated soil source values.\n\n'
 text+='The terrain domain extends a further 10.02 km beyond each side of the assessment rectangle; it is still not the complete upstream catchment, so flow-accumulation results remain boundary-dependent.\n\n'
 text+='Reproduce: `.venv/bin/python bin/analysis/run_goslar_multiriver_full.py`, then `.venv/bin/python bin/analysis/report_goslar_multiriver_full.py`. The PNG/SVG figures use the same left/right two-panel layout, fixed color scale and 0.6 threshold. The four overview maps overlay the regulatory boundaries of 8 rivers; each of the 6 HWRM scenarios has its own map so that boundaries of different scenarios do not overlap. QGIS can read the two GPKG files and the score TIFs directly. Source files and checksums are in expansion_manifest.json, and the version of each product is carried in the attributes of comparison_boundaries.gpkg.\n'
 (OUT/'READING_NOTE.md').write_text(text)
 files={str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='output_checksums.json'}
 (OUT/'output_checksums.json').write_text(json.dumps(files,indent=2)+'\n');print(json.dumps(qa,indent=2))
if __name__=='__main__':main()
