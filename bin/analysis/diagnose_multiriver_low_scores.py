#!/usr/bin/env python3
"""TOOLING: immutable component semantics and normalization diagnostics."""
import json
from pathlib import Path
import numpy as np
import geopandas as gpd
from compare_goslar_multiriver import ROOT,BASE,sha,read_grid,raster_mask,clean_ring,write_csv
OUT=BASE.parent/'component_semantics_v1'
SOURCE=BASE.parent/'multiriver_comparison_v1'
def main():
    OUT.mkdir(parents=True,exist_ok=True);inputs={}
    def read(path,ref=None):inputs[str(path.relative_to(ROOT))]=sha(path);return read_grid(path,ref)
    prior=json.loads((SOURCE/'manifest.json').read_text())
    for rel,h in prior['inputs'].items():assert sha(ROOT/rel)==h,rel
    for f in [BASE/'frozen_normalization.json',Path(__file__).with_name('compare_goslar_multiriver.py')]:inputs[str(f.relative_to(ROOT))]=sha(f)
    m=json.loads((BASE/'chain/priority_scenarios/run_manifest.json').read_text())
    inputs[str((BASE/'chain/priority_scenarios/run_manifest.json').relative_to(ROOT))]=sha(BASE/'chain/priority_scenarios/run_manifest.json')
    pim,ref=read(ROOT/m['priority_raster_lineage']['path']);valid=np.isfinite(pim)
    layers={k:read(ROOT/e['path'],ref)[0] for k,e in m['criterion_raster_lineage'].items()}
    special={'water_wetland_context':'environmental_sensitivity_v0_1/water_wetland_context_0_1.tif','protected_ecological_context':'environmental_sensitivity_v0_1/protected_area_context_0_1.tif','settlement_population':'exposure_indicators/population_exposure_0_1.tif','critical_infrastructure':'exposure_indicators/built_infrastructure_exposure_0_1.tif'}
    components={}
    for ws in m['component_weights'].values():
        for k in ws:components[k]=read(BASE/'chain'/special.get(k,f'criteria_stack/criteria/{k}_0_1.tif'),ref)[0]
    rawpaths={'ls_raw':'chain/ls_factor/goslar_focus_ls_factor_capped50_hillslope_30m.tif','soil_k_raw':'chain/soil_k_factor/soil_k_factor_aligned_250m_effective_30m.tif','c_raw':'landcover/c_factor_goslar_focus_30m.tif','slope_degrees':'chain/terrain_preprocessing/goslar_focus_slope_degrees_utm32n_30m.tif','tree_cover_decline_fraction':'landcover/clms_tcd_vegetation_loss_2018_2024_goslar_official_basin_30m.tif'}
    raw={k:read(BASE/p,ref)[0] for k,p in rawpaths.items()};wc=read(BASE/'landcover/worldcover_aligned.tif',ref)[0]
    anchors=json.loads((BASE/'frozen_normalization.json').read_text());checks=[]
    for k,r,a in [('ls_factor','ls_raw','criteria_stack:2'),('soil_k_factor','soil_k_raw','soilgrids_kfactor:0'),('c_factor','c_raw','criteria_stack:3')]:
        par=anchors[a];s=np.clip((raw[r]-par['clip_low'])/(par['clip_high']-par['clip_low']),0,1);z=valid&np.isfinite(s)&np.isfinite(components[k]);err=float(np.max(abs(s[z]-components[k][z])))
        assert err<1e-5,(k,err)
        assert np.array_equal(np.isfinite(s)&valid,np.isfinite(components[k])&valid),k
        checks.append(dict(component=k,raw=rawpaths[r],anchor_low=par['clip_low'],anchor_high=par['clip_high'],max_error=err,finite_mask_equal=bool(np.array_equal(np.isfinite(s)&valid,np.isfinite(components[k])&valid))))
    geo=SOURCE/'comparison_boundaries.gpkg';inputs[str(geo.relative_to(ROOT))]=sha(geo)
    ps=gpd.read_file(geo,layer='products');ex=gpd.read_file(geo,layer='ring_exclusion').geometry.union_all()
    rows=[];classes=[];effective=[]
    for _,p in ps[ps.family=='regulatory'].iterrows():
        inside=raster_mask(p.geometry,ref)&valid
        if not inside.any():continue
        ring=raster_mask(clean_ring(p.geometry,1000,ex),ref)&~raster_mask(ex,ref)&~inside&valid
        for zone,z in [('inside',inside),('ring',ring)]:
            for family,group in [('criterion',layers),('component',components),('raw',raw)]:
                for k,a in group.items():
                    vals=a[z&np.isfinite(a)];n=len(vals)
                    rows.append(dict(river=p.river,zone=zone,family=family,layer=k,zone_cells=int(z.sum()),valid_cells=n,missing_share=1-n/z.sum(),mean=float(vals.mean()) if n else None,median=float(np.median(vals)) if n else None,p10=float(np.quantile(vals,.1)) if n else None,p90=float(np.quantile(vals,.9)) if n else None,zero_share=float((vals==0).mean()) if n else None))
            for cat in np.unique(wc[z&np.isfinite(wc)]):classes.append(dict(river=p.river,zone=zone,class_code=int(cat),cells=int((z&(wc==cat)).sum()),share=float((wc[z]==cat).mean())))
            for criterion,ws in m['component_weights'].items():
                den=sum(w*np.isfinite(components[k]) for k,w in ws.items())
                rec=np.zeros(pim.shape)
                for k,w in ws.items():
                    ew=np.divide(w*np.isfinite(components[k]),den,out=np.zeros(pim.shape),where=den>0)
                    rec+=np.nan_to_num(components[k])*ew
                    effective.append(dict(river=p.river,zone=zone,criterion=criterion,component=k,nominal_weight=w,mean_effective_weight=float(ew[z].mean())))
                assert np.max(abs(rec[z]-layers[criterion][z]))<1e-5
    write_csv(OUT/'component_statistics.csv',rows);write_csv(OUT/'landcover_composition.csv',classes);write_csv(OUT/'effective_component_weights.csv',effective);write_csv(OUT/'normalization_checks.csv',checks)
    write_note(rows)
    inputs[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    for p,h in inputs.items():assert sha(ROOT/p)==h
    (OUT/'manifest.json').write_text(json.dumps(dict(claim_level='diagnostic_only',command='.venv/bin/python bin/analysis/diagnose_multiriver_low_scores.py',inputs=inputs,model_changed=False,normalization_checks=checks,outputs={p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json'}),indent=2)+'\n')
    for r in rows:
        if r['zone']=='inside' and r['family']!='raw':print(r['river'],r['layer'],r['mean'],'missing',round(r['missing_share'],3))
def write_note(rows):
    text='# 非洪水因素低分语义诊断\n\n本轮判断是：侵蚀和土地利用低分大体符合现有输入及计算规则，但这些规则衡量的内容不等于河流淹没风险。环境项并不低；社会经济项存在代理含义和人口覆盖限制。三项冻结标准化回放通过，未发现这三项数值方向写反或计算不一致；这不证明标准化锚点、代理指标及输入分类已经获得现实验证。\n\n范围：原始34%模型、官方划定范围内有效格、同一清理后1公里环带。模型输入与权重不修改。复现：`.venv/bin/python bin/analysis/diagnose_multiriver_low_scores.py`。\n\n| 河流 | 侵蚀因子 内/外 | 土地利用 内/外 | 环境 内/外 | 社会经济 内/外 |\n|---|---|---|---|---|\n'
    for river in ['Abzucht','Grane','Oker','Innerste']:
        cells=[]
        for k in ['sediment','landuse_asm','environmental','socioeconomic']:
            values=[next(r['mean'] for r in rows if r['river']==river and r['layer']==k and r['zone']==z) for z in ['inside','ring']]
            cells.append('/'.join(f'{v:.3f}' for v in values))
        text+='| '+river+' | '+' | '.join(cells)+' |\n'
    text+='\n## 逐因素判断\n\n1. 侵蚀因子：低分在部分地方具有可解释性，但不等于低淹没风险。\nOker范围内平均坡度2.91度，外围10.68度；范围内现有WorldCover分类约63.8%树木、29.1%草地。低坡度与较低C赋值共同产生低侵蚀分。Grane也表现为范围内坡度较缓。Innerste则不能套用“更平缓”的解释：其12格内坡度和LS高于外围，低侵蚀综合分主要与森林/草地C低值等评分组合有关。\nC按地类查表，森林原始0.001经0–0.2锚点变为0.005，草地0.02变为0.1；数值小符合当前覆盖管理代理方向。LS冻结锚点约0.055–24.779，而Oker有效LS平均1.269，低标准化值可由该尺度解释。K仅说明相对于冻结锚点的位置；250米有效分辨率不能提供30米土壤细节。\n现有sediment为K、LS、C的加权平均，不是RUSLE乘积或实际泥沙产出。USDA对RUSLE2的说明是坡面细沟/细沟间侵蚀及搬运过程，不能直接代替河流淹没判断：[USDA ARS](https://www.ars.usda.gov/southeast-area/oxford-ms/national-sedimentation-laboratory/watershed-physical-processes-research/research/rusle2/revised-universal-soil-loss-equation-2-how-rusle2-computes-rill-and-interrill-erosion/)。\n\n2. 土地利用：低分符合窄代理含义，部分名称不准确。\nland_cover_pressure实际采用径流压力查表：树木0.15、草地0.35、农田0.70、建成区1。bare_soil_vegetation_loss实际是2018–2024树冠密度正向下降比例，Oker均值0.0052（约0.52个百分点），因此接近0不表示地表没有洪水风险，也不代表没有裸土。稳定的农田、草地和建成区不会因这一项自动得高分。\nbuilt_agriculture_road_expansion实际是现状建成区/农业类别与道路邻近性的组合，未测量扩张；应称为现状开发/农业与道路邻近代理。该命名差异需要修正解释，但本轮不更改模型代码或结果。三项直接合成中，树冠变化的实测量级与其他查表/距离分值不同；共同处于0–1不等于影响尺度已匹配，这是后续校准问题，不能仅为提高分数而重拉伸。\n\n3. 环境项：不是压低评分的主要因素。\n四条河流范围内环境均值约0.85–0.96。它来自水体/湿地及保护区邻近性，支持“靠近这些对象”的解释，不代表完整生态敏感性。\n\n4. 社会经济：Oker与Abzucht并不低，Innerste不能据此判断人口稀少。\n范围内人口分项缺失比例：Grane69.2%、Abzucht54.5%、Oker77.7%、Innerste100%。缺人口不是零人口。Innerste基础设施邻近分约0.011，道路邻近分约0.985；去掉缺失人口后，剩余两项重分配权重产生约0.535的社会经济分。这只表明现有OSM候选设施邻近程度低，不能证明真实设施少或社会脆弱性低。20公里道路衰减让所有范围内道路分接近1，区分能力有限；现有分项也未衡量收入、应对能力等脆弱性因素。\n\n## 缺项与标准化边界\n\nLS会在汇流量大于500格的河道单元被主动置空；另有输入无效情况，不能把所有LS空值归因于此。K和人口另有覆盖不足。分项缺失后按剩余权重重新平均，因此缺项可能抬高也可能降低结果，方向必须看缺失项原本应有的值；不能声称缺项自动压低PIM。\nnormalization_checks.csv核对原始K/LS/C到冻结评分的公式、有限值掩膜和最大误差；effective_component_weights.csv列出空间变化的有效分项权重。土地分类和土壤属性尚未以地面调查或独立高分辨率数据核验，本次是输入—公式—含义一致性检查。\n\n## 优先处理顺序\n\n先把代理名称与实际含义对齐，保留能解释的低值；再查清人口空白的覆盖/无记录含义，以及OSM设施完整性；之后评估树冠变化与其他0–1分项是否有可比较的量纲、道路衰减尺度是否有依据。确认这些问题后才考虑新的评分规则。当前没有证据支持把所有非洪水低分统一抬高。\n'
    (OUT/'READING_NOTE.md').write_text(text)

if __name__=='__main__':main()
