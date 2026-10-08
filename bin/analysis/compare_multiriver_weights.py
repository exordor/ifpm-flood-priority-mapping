#!/usr/bin/env python3
"""TOOLING: fixed-input multi-river weight sensitivity, 34/50/60/70%."""
import json
from pathlib import Path
import numpy as np
import geopandas as gpd
import rasterio
from compare_goslar_multiriver import BASE, ROOT, sha, lineage_entries, read_grid, raster_mask, clean_ring, stats, write_csv, make_map
from tune_abzucht_weights import weights_at, score_at
SOURCE=BASE.parent/'multiriver_comparison_v1'
OUT=BASE.parent/'multiriver_weights_50_60_70_v1'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    inputs={}
    def pin(p):inputs[str(p.relative_to(ROOT))]=sha(p);return p
    prior=json.loads(pin(SOURCE/'manifest.json').read_text())
    for rel,digest in prior['inputs'].items():
        assert sha(pin(ROOT/rel))==digest,rel
    gpkg=pin(SOURCE/'comparison_boundaries.gpkg')
    assert sha(gpkg)==prior['outputs']['comparison_boundaries.gpkg']
    m=json.loads(pin(BASE/'chain/priority_scenarios/run_manifest.json').read_text())
    for e in lineage_entries([m['input_lineage'],m['criterion_raster_lineage'],m['priority_raster_lineage']]):assert sha(pin(ROOT/e['path']))==e['sha256']
    baseline,ref=read_grid(ROOT/m['priority_raster_lineage']['path'])
    criteria={k:read_grid(ROOT/e['path'],ref)[0] for k,e in m['criterion_raster_lineage'].items()}
    valid=np.isfinite(baseline)
    replay=score_at(criteria,m['main_weights'],valid)
    assert np.array_equal(np.isfinite(replay),valid)
    assert np.max(np.abs(replay[valid]-baseline[valid]))<1e-6
    products=gpd.read_file(gpkg,layer='products').to_crs(ref['crs'])
    exclusion=gpd.read_file(gpkg,layer='ring_exclusion').to_crs(ref['crs']).geometry.union_all()
    boundary=gpd.read_file(BASE/'expanded_boundary.gpkg').to_crs(ref['crs']).geometry.union_all()
    scenarios={34:baseline};weights={34:m['main_weights']}
    for pct in [50,60,70]:
        w=weights_at(m['main_weights'],pct/100);s=score_at(criteria,w,valid)
        assert np.array_equal(np.isfinite(s),valid)
        scenarios[pct]=s;weights[pct]=w
        profile=ref.copy();profile.update(dtype='float32',nodata=-9999.,count=1,compress='deflate')
        f=OUT/f'pim_flood_{pct}.tif'
        with rasterio.open(f,'w',**profile) as ds:ds.write(np.where(valid,s,-9999.).astype('float32'),1)
        check,_=read_grid(f,ref)
        assert np.array_equal(check[valid],s[valid]) and np.array_equal(np.isfinite(check),valid)
    rows=[];summary=[]
    for _,p in products.iterrows():
        for touched in [False,True]:
            inside=raster_mask(p.geometry,ref,touched)&valid
            for radius in [500,1000,2000]:
                ring=raster_mask(clean_ring(p.geometry,radius,exclusion),ref,touched)&~raster_mask(exclusion,ref,touched)&~inside&valid
                for pct,s in scenarios.items():
                    a=stats(s,inside);b=stats(s,ring)
                    row=dict(product_id=p.product_id,river=p.river,family=p.family,scenario=p.scenario,flood_weight=pct/100,inclusion='all_touched' if touched else 'center',radius_m=radius,
                             **{'inside_'+k:v for k,v in a.items()},**{'ring_'+k:v for k,v in b.items()},
                             mean_gap=a['mean']-b['mean'] if a['mean'] is not None and b['mean'] is not None else None,
                             high_share_gap=a['high_share']-b['high_share'] if a['high_share'] is not None and b['high_share'] is not None else None)
                    rows.append(row)
                    if not touched and radius==1000:summary.append(row)
    write_csv(OUT/'statistics.csv',rows);write_csv(OUT/'summary.csv',summary)
    write_csv(OUT/'weights.csv',[{'flood_percent':pct,**w} for pct,w in weights.items()])
    # Original 34% values must reproduce the preceding comparison exactly.
    import csv
    with (SOURCE/'statistics.csv').open() as f:old=list(csv.DictReader(f))
    for r in rows:
        if r['flood_weight']!=.34:continue
        for zone in ['inside','ring']:
            o=next(x for x in old if x['product_id']==r['product_id'] and x['metric']=='PIM' and x['inclusion']==r['inclusion'] and int(x['radius_m'])==r['radius_m'] and x['zone']==zone)
            assert int(o['valid_cells'])==r[zone+'_valid_cells']
            if o['mean']:assert abs(float(o['mean'])-r[zone+'_mean'])<1e-12
    primary=[dict(p) for _,p in products.iterrows() if p.family=='regulatory']
    for pct in [50,60,70]:
        make_map(OUT/f'overview_{pct}',f'Goslar | Flood weight {pct}%',primary,boundary.bounds,criteria['flood_hazard'],scenarios[pct],ref)
        for p in primary:
            if not (raster_mask(p['geometry'],ref)&valid).any():continue
            make_map(OUT/f"{p['river'].lower()}_{pct}",f"{p['river']} | Flood weight {pct}%",[p],p['geometry'].intersection(boundary).buffer(500).bounds,criteria['flood_hazard'],scenarios[pct],ref)
    note='# 洪水因素权重50%、60%、70%的多河流对比\n\n状态：权重敏感性情景。仅改变五项组合权重；其他四项按原比例缩减。原人口、土壤、归一化、有效范围和0.6阈值不变。左图洪水子指标不变，右图为对应权重PIM。\n\n复现：`.venv/bin/python bin/analysis/compare_multiriver_weights.py`。\n\n| 河流/资料 | 洪水权重 | 内/外均值 | 均值差 | 内/外高分比例 | 高分比例差（百分点） |\n|---|---:|---|---:|---|---:|\n'
    for r in summary:
        if r['mean_gap'] is None:continue
        note+=f"| {r['river']} / {r['family']} / {r['scenario']} | {r['flood_weight']:.0%} | {r['inside_mean']:.3f}/{r['ring_mean']:.3f} | {r['mean_gap']:+.3f} | {r['inside_high_share']:.2%}/{r['ring_high_share']:.2%} | {r['high_share_gap']*100:+.2f} |\n"
    note+='\n表中采用中心归属和清理后的1公里环带；所有已取得官方洪泛范围从环带排除。完整六种设置在statistics.csv。四条无覆盖河流保留空结果，不能评价；Innerste主比较仅12格。原边界来源、覆盖分母和缺项沿用multiriver_comparison_v1。\n\n稳健性：以下为六种设置下高分比例差的最小值至最大值（百分点）。\n\n'
    for _,p in products.iterrows():
        if not any(r['product_id']==p.product_id and r['mean_gap'] is not None for r in rows):continue
        parts=[]
        for pct in [34,50,60,70]:
            v=[r['high_share_gap']*100 for r in rows if r['product_id']==p.product_id and r['flood_weight']==pct/100 and r['high_share_gap'] is not None]
            parts.append(f'{pct}%：{min(v):+.2f}～{max(v):+.2f}')
        note+=f'- {p.river} / {p.family} / {p.scenario}：'+ '；'.join(parts)+'。\n'
    note+='\n解释边界：提高洪水权重会让综合PIM更接近洪水子指标。若洪水指标原本在范围内较高，均值差随权重增大是加权公式的预期行为；需要同时看高分比例差及跨河流稳定性。不能只凭范围内变红选择权重，也不能据此验证其他优先级目标。此轮用同一批洪泛资料比较权重，属于参考资料引导的敏感性分析，不是独立验证；不自动选择最终权重。\n'
    (OUT/'READING_NOTE.md').write_text(note)
    pin(Path(__file__));pin(Path(__file__).with_name('tune_abzucht_weights.py'))
    for p,d in inputs.items():assert sha(ROOT/p)==d,p
    manifest=dict(claim_level='sensitivity_scenario',boundary_id='goslar_abzucht_display_rectangle_v1',experiment_id='multiriver_weights_50_60_70_v1',inputs=inputs,weights=weights,baseline_changed=False,original_population_soil=True,paired_valid_cells=int(valid.sum()),baseline_regression=True,source_comparison=str(SOURCE.relative_to(ROOT)),command='.venv/bin/python bin/analysis/compare_multiriver_weights.py',outputs={p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json'})
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Complete:',len(rows),'rows;',len(summary),'main rows; 15 PNG/SVG pairs; 3 rasters')
if __name__=='__main__':main()
