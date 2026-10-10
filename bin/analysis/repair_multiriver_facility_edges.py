#!/usr/bin/env python3
"""TOOLING: buffered facility distance; preserve original lattice/support/weights."""
import json,csv
from pathlib import Path
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from affine import Affine
from scipy.ndimage import distance_transform_edt
from compare_goslar_multiriver import ROOT,BASE,sha,read_grid,raster_mask,clean_ring,write_csv,stats,make_map
from tune_abzucht_weights import weights_at,score_at
SOURCE=BASE.parent/'multiriver_weights_50_60_70_v1'
OUT=BASE.parent/'facility_edge_repair_v1'

def facility_score(geometries,ref,pad=68,decay=2000.):
    resolution=ref['transform'].a
    if resolution<=0 or ref['transform'].e!=-resolution or ref['transform'].b or ref['transform'].d:raise ValueError('Square north-up reference required')
    if pad<0:raise ValueError('Negative padding')
    transform=ref['transform']*Affine.translation(-pad,-pad)
    arr=rasterize([(g,1) for g in geometries],out_shape=(ref['height']+2*pad,ref['width']+2*pad),transform=transform,fill=0,dtype='uint8')
    if not arr.any():raise ValueError('No facility rasterized')
    result=np.clip(1-distance_transform_edt(arr==0,sampling=(resolution,resolution))/decay,0,1).astype('float32')
    return result[pad:pad+ref['height'],pad:pad+ref['width']]

def main():
    OUT.mkdir(parents=True,exist_ok=True);inputs={}
    def pin(p):inputs[str(p.relative_to(ROOT))]=sha(p);return p
    prior=json.loads(pin(SOURCE/'manifest.json').read_text())
    for rel,h in prior['inputs'].items():assert sha(pin(ROOT/rel))==h,rel
    m=json.loads((BASE/'chain/priority_scenarios/run_manifest.json').read_text());old,ref=read_grid(ROOT/m['priority_raster_lineage']['path']);valid=np.isfinite(old)
    criteria={k:read_grid(ROOT/e['path'],ref)[0] for k,e in m['criterion_raster_lineage'].items()}
    facility=read_grid(pin(BASE/'chain/exposure_indicators/built_infrastructure_exposure_0_1.tif'),ref)[0]
    pop=read_grid(pin(BASE/'chain/exposure_indicators/population_exposure_0_1.tif'),ref)[0]
    road=read_grid(pin(BASE/'chain/criteria_stack/criteria/road_access_proximity_0_1.tif'),ref)[0]
    features=gpd.read_file(pin(ROOT/'data/raw/goslar_official_hydrology_and_flood_data/osm_goslar_infrastructure_candidates.gpkg')).to_crs(ref['crs'])
    if not features.geom_type.eq('Point').all():raise ValueError('Expected retained point proxies')
    original=facility_score(features.geometry,ref,pad=0)
    assert np.max(abs(original[valid]-facility[valid]))<1e-7
    repaired=facility_score(features.geometry,ref,pad=68).astype('float64');repaired[~valid]=np.nan
    # Additional padding must not change any score under fixed 2km decay.
    larger=facility_score(features.geometry,ref,pad=100)
    assert np.array_equal(repaired[valid],larger[valid])
    assert np.all(repaired[valid]>=facility[valid]-1e-7)
    def combine(f):
        parts={'road_access_proximity':road,'settlement_population':pop,'critical_infrastructure':f};ws=m['component_weights']['socioeconomic']
        den=sum(w*np.isfinite(parts[k]) for k,w in ws.items());num=sum(w*np.nan_to_num(parts[k]) for k,w in ws.items())
        return np.divide(num,den,out=np.full(old.shape,np.nan),where=(den>0)&valid)
    replay=combine(facility);assert np.max(abs(replay[valid]-criteria['socioeconomic'][valid]))<1e-6
    changed=valid & (repaired!=facility)
    newcriteria=dict(criteria);newcriteria['socioeconomic']=criteria['socioeconomic'].copy()
    newcriteria['socioeconomic'][changed]=combine(repaired).astype('float32').astype('float64')[changed]
    def write(name,a):
        prof=dict(ref,dtype='float32',nodata=-9999.,count=1,compress='deflate');p=OUT/name
        with rasterio.open(p,'w',**prof) as ds:
            ds.write(np.where(valid,a,-9999.).astype('float32'),1)
            ds.update_tags(claim_level='sensitivity_scenario',repair='facility distance with 2040m aligned padding; original score extent',population='original unchanged')
        check,_=read_grid(p,ref);assert np.array_equal(check[valid],a[valid].astype('float32')) and np.array_equal(np.isfinite(check),valid)
    write('facility_score.tif',repaired);write('facility_score_delta.tif',repaired-facility);write('socioeconomic_score.tif',newcriteria['socioeconomic'])
    before={34:old};after={};weights={}
    for pct in [34,50,60,70]:
        w=weights_at(m['main_weights'],pct/100);weights[pct]=w
        if pct!=34:
            f=pin(SOURCE/f'pim_flood_{pct}.tif');assert sha(f)==prior['outputs'][f.name];before[pct]=read_grid(f,ref)[0]
        assert np.max(abs(score_at(criteria,w,valid)[valid]-before[pct][valid]))<1e-6
        after[pct]=score_at(newcriteria,w,valid)
        after[pct][valid & ~changed]=before[pct][valid & ~changed]
        assert np.array_equal(after[pct][valid & ~changed],before[pct][valid & ~changed])
        assert np.array_equal(np.isfinite(after[pct]),valid)
        assert np.min(after[pct][valid]-before[pct][valid])>-2e-7
        write(f'pim_flood_{pct}.tif',after[pct]);write(f'pim_delta_{pct}.tif',after[pct]-before[pct])
    gpkg=pin(BASE.parent/'multiriver_comparison_v1/comparison_boundaries.gpkg');ps=gpd.read_file(gpkg,layer='products');ex=gpd.read_file(gpkg,layer='ring_exclusion').geometry.union_all();rows=[];summary=[]
    for _,p in ps.iterrows():
        for touched in [False,True]:
            a=raster_mask(p.geometry,ref,touched)&valid
            for radius in [500,1000,2000]:
                b=raster_mask(clean_ring(p.geometry,radius,ex),ref,touched)&~raster_mask(ex,ref,touched)&~a&valid
                for pct in before:
                    for state,s in [('before',before[pct]),('repaired',after[pct])]:
                        i=stats(s,a);o=stats(s,b)
                        r=dict(product_id=p.product_id,river=p.river,family=p.family,scenario=p.scenario,flood_percent=pct,state=state,inclusion='all_touched' if touched else 'center',radius_m=radius,**{'inside_'+k:v for k,v in i.items()},**{'ring_'+k:v for k,v in o.items()},mean_gap=i['mean']-o['mean'] if i['mean'] is not None and o['mean'] is not None else None,high_share_gap=i['high_share']-o['high_share'] if i['high_share'] is not None and o['high_share'] is not None else None)
                        rows.append(r)
                        if not touched and radius==1000:summary.append(r)
    # Before rows must reproduce previous comparison for all settings.
    previous=list(csv.DictReader((SOURCE/'statistics.csv').open()))
    for r in rows:
        if r['state']!='before':continue
        o=next(x for x in previous if x['product_id']==r['product_id'] and float(x['flood_weight'])==r['flood_percent']/100 and x['inclusion']==r['inclusion'] and int(x['radius_m'])==r['radius_m'])
        for k in ['inside_valid_cells','ring_valid_cells','inside_mean','ring_mean','high_share_gap']:
            assert (r[k] is None and not o[k]) or (o[k] and abs(float(o[k])-r[k])<1e-12),(r,k)
    write_csv(OUT/'statistics.csv',rows);write_csv(OUT/'summary.csv',summary);write_csv(OUT/'weights.csv',[{'flood_percent':p,**w} for p,w in weights.items()])
    boundary=gpd.read_file(BASE/'expanded_boundary.gpkg').to_crs(ref['crs']).geometry.union_all();primary=[dict(p) for _,p in ps[ps.family=='regulatory'].iterrows()];inner=next(p for p in primary if p['river']=='Innerste')
    for pct in after:
        make_map(OUT/f'overview_{pct}',f'Goslar | Facility edge repair | Flood weight {pct}%',primary,boundary.bounds,criteria['flood_hazard'],after[pct],ref)
        make_map(OUT/f'innerste_{pct}',f'Innerste | Facility edge repair | Flood weight {pct}%',[inner],inner['geometry'].intersection(boundary).buffer(500).bounds,criteria['flood_hazard'],after[pct],ref)
    note='# Facility distance edge repair\n\nOnly the 375 originally retained facilities are placed in a computation grid buffered by 2040 m, and after the distance calculation the result is clipped back to the original 30 m grid; the population gaps, facility categories, 2 km decay, five criterion weights and original valid extent are all kept. No filtered-out facilities were added. Status: controlled repair scenario, not a final validation result.\n\n| River/source | Flood weight | Mean PIM inside extent before→after | Inside-minus-outside mean difference before→after | High-score share difference before→after (percentage points) |\n|---|---:|---|---|---|\n'
    for r in summary:
        if r['state']!='repaired' or r['mean_gap'] is None:continue
        b=next(x for x in summary if x['product_id']==r['product_id'] and x['flood_percent']==r['flood_percent'] and x['state']=='before')
        note+=f"| {r['river']} / {r['family']} / {r['scenario']} | {r['flood_percent']}% | {b['inside_mean']:.3f}→{r['inside_mean']:.3f} | {b['mean_gap']:+.3f}→{r['mean_gap']:+.3f} | {b['high_share_gap']*100:+.2f}→{r['high_share_gap']*100:+.2f} |\n"
    note+='\nThe table uses cell centers and the cleaned 1 km ring; the other settings are kept in statistics.csv. The high-score threshold is still 0.6. The four rivers without coverage keep empty statistics. The pre-repair baseline is fully reproduced, and a 3000 m buffer gives exactly the same facility scores. The quantized positions of facilities inside the original grid are unchanged, so the changes can be attributed to the existing facilities outside the grid that now enter the distance calculation.\n\nThe edge repair removes one implementation bias, but it does not resolve the population publication omission rule, the choice of facility categories or OSM completeness, and the PIM still cannot be treated as an inundation model. Neither the original model nor the earlier weight results were overwritten.\n\nReproduce: `.venv/bin/python bin/analysis/repair_multiriver_facility_edges.py`.\n'
    (OUT/'READING_NOTE.md').write_text(note)
    pin(Path(__file__))
    for p,h in inputs.items():assert sha(ROOT/p)==h,p
    changed=(repaired-facility)>1e-7
    (OUT/'manifest.json').write_text(json.dumps(dict(claim_level='sensitivity_scenario',command='.venv/bin/python bin/analysis/repair_multiriver_facility_edges.py',weights=weights,reference_grid=dict(crs=str(ref['crs']),transform=list(ref['transform']),shape=list(old.shape)),padding_cells=68,padding_m=2040,decay_m=2000,buffer3000_invariant=True,changed_facility_cells=int((changed&valid).sum()),same_valid_cells=int(valid.sum()),original_unchanged=True,inputs=inputs,outputs={p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json'}),indent=2)+'\n')
    print('Completed',len(rows),'rows;',int((changed&valid).sum()),'facility cells corrected')
if __name__=='__main__':main()
