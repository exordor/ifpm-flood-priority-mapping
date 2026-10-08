#!/usr/bin/env python3
"""TOOLING: read-back checks and Chinese handoff for the expanded run."""
import json,sys
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd,rasterio
from rasterio.warp import reproject,Resampling
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from compare_goslar_multiriver import sha,read_grid,raster_mask,clean_ring,BASE
import compare_goslar_multiriver as maps
from matplotlib.ticker import MaxNLocator
OUT=ROOT/'outputs/goslar_multiriver_full_extent_v1/frozen_scale_v1'
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
 text='# 扩大边界后的多河流对比\n\n新范围完整包含保留的14项官方洪泛区资料及外围2公里对照区，并与原模型范围合并。面积'+f"{m['area_km2']:.2f}平方公里；30米格网中{qa['target_cells']:,}格位于评价区，{qa['scored_cells']:,}格有综合PIM，{qa['no_score_cells']:,}格无评分。状态：诊断性对比，不是最终洪水预测验证。\n\n"
 text+='## 原始34%洪水权重结果\n\n均值按洪泛区内／外围1公里列出，环带排除全部已取得的洪泛区；采用像元中心归属。官方划定范围与明确重现期的水力情景分开，公告日期不作洪灾发生年份。\n\n|河流/资料|评分格/洪泛区格|洪水指标 内/外|PIM 内/外|区内PIM≥0.6|\n|---|---:|---:|---:|---:|\n'
 summary=[]
 for _,p in products.iterrows():
  pi=get(p.product_id,'PIM','inside');po=get(p.product_id,'PIM','ring');fi=get(p.product_id,'Flood indicator','inside');fo=get(p.product_id,'Flood indicator','ring');cv=coverage[coverage.product_id==p.product_id].iloc[0]
  text+=f'|{p.river} / {p.scenario}|{int(pi.valid_cells):,}/{int(cv.total_cells):,}|{fi["mean"]:.3f}/{fo["mean"]:.3f}|{pi["mean"]:.3f}/{po["mean"]:.3f}|{pi.high_share:.1%}|\n'
  summary.append({'product_id':p.product_id,'river':p.river,'scenario':p.scenario,'family':p.family,'inside_cells':int(pi.valid_cells),'ring_cells':int(po.valid_cells),'flood_inside':fi['mean'],'flood_outside':fo['mean'],'pim_inside':pi['mean'],'pim_outside':po['mean'],'pim_high_share':pi.high_share})
 pd.DataFrame(summary).to_csv(OUT/'summary.csv',index=False)
 sf=pd.DataFrame(summary);reg=sf[sf.family=='regulatory']
 text+='\n洪水指标区内均值高于环带的河流：'+ '、'.join(reg.loc[reg.flood_inside>reg.flood_outside,'river'])+'；未高于环带：'+('、'.join(reg.loc[reg.flood_inside<=reg.flood_outside,'river']) or '无')+'。\n'
 text+='综合PIM区内均值高于环带的河流：'+ '、'.join(reg.loc[reg.pim_inside>reg.pim_outside,'river'])+'；未高于环带：'+('、'.join(reg.loc[reg.pim_inside<=reg.pim_outside,'river']) or '无')+'。这是同一口径下的描述性对照。\n'
 contribution=[];allflood=products.geometry.union_all()
 for _,p in products.iterrows():
  inside=raster_mask(p.geometry,ref)&valid;ring=raster_mask(clean_ring(p.geometry,1000,allflood),ref)&~raster_mask(allflood,ref)&valid
  for key,a in criteria.items():
   iv=float(a[inside].mean());ov=float(a[ring].mean());weight=n['main_weights'][key]
   contribution.append(dict(product_id=p.product_id,river=p.river,criterion=key,inside_mean=iv,ring_mean=ov,weight=weight,inside_contribution=iv*weight,ring_contribution=ov*weight,contribution_difference=(iv-ov)*weight))
 pd.DataFrame(contribution).to_csv(OUT/'criterion_comparison.csv',index=False)
 text+='\n各因素区内/外均值及对PIM差值的贡献在criterion_comparison.csv中列出；贡献是标准化因素得分乘原权重，不把低分直接解释为洪水不存在。\n'
 text+='\n## 权重敏感性\n\n|河流/资料|34% 区内/外PIM|50% 区内/外PIM|60% 区内/外PIM|70% 区内/外PIM|\n|---|---:|---:|---:|---:|\n'
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
 text+='\n## 对照设置的稳健性\n\n12项资料的洪水指标区内均值在六种设置下都高于环带；Innerste HQ100/HQ25在中心归属、1公里环带下仅高约0.0034/0.0024，改变设置后差值会变号，因此不能称其一致性明确。14项资料包含同河流不同情景，不能当作14条独立河流。\n\n'
 text+='|洪水权重|六种设置均为区内PIM更高|随设置改变方向|六种设置均为区内PIM更低|\n|---|---:|---:|---:|\n'
 for pct in [34,50,60,70]:
  q=stable[(stable.metric=='PIM')&(stable.flood_percent==pct)]
  text+=f'|{pct}%|{int((q.status=="positive_all").sum())}|{int((q.status=="mixed").sum())}|{int((q.status=="negative_all").sum())}|\n'
 text+='\n## 如何解释\n\n扩大边界解决的是评价覆盖不足，不能保证指标与官方洪泛区更一致。洪水指标与PIM分别比较；提高洪水权重会使PIM更接近现有洪水指标，并不会修正洪水指标自身的空间模式。详细敏感性表包含500米、1公里、2公里环带与中心/接触两种像元归属，不把像元当独立样本检验显著性。\n\n'
 text+='保留原标准化锚点与原人口空白规则。人口发布表省略格可能是真零或保密处理后的零，当前仍不填零；缺失组件通过原可用项权重重分配处理。因此有PIM评分不代表所有组件都有数据，详见component_coverage.csv。人口、土壤等缺项影响不能解释为真实低风险。\n\n'
 d=m['old_area_comparison'];text+=f'相对于未经设施边缘修复的原冻结34%基准，原区域重叠{d["common_cells"]:,}格的PIM平均绝对变化为{d["mean_absolute_change"]:.6f}，最大绝对变化为{d["max_absolute_change"]:.6f}。分因素变化见old_area_criterion_changes.csv。扩大汇流计算域、重投影网格变化、设施和水体边缘修复、OSM等源快照日期差异都会影响旧区域，不能把变化全部归因于边界本身。土壤原始数据在旧范围的重叠部分逐值一致，其对齐栅格的部分差异来自预处理而非土壤源值更新。原始栅格与权重未改写，输入哈希已核对。\n\n'
 text+=f'人口层旧区共同有效{popdelta["common_cells"]:,}格，原有效但新结果缺失{popdelta["old_valid_now_absent"]}格；共同有效格最大标准化差为{popdelta["max_absolute_difference"]:.6f}。这里保持的是原处理规则，并非承诺重投影后每格值不变。\n\n'
 text+='道路和设施采用2026年9月14日的OSM响应，实际快照时间为UTC 14:19:31–15:00:19，各请求日期与校验记录保存在来源清单中。7月旧缓存及未成功的Ohsome尝试均未用于评分；与原模型的快照日期差异仍需保留在解释中。\n\n'
 text+='地形计算域比评价矩形每边再外扩10.02公里，仍不是完整上游流域，汇流相关结果保留边界依赖。官方范围为法规/模型情景证据；范围外高分不称误报，重叠比例不称预测准确率。\n\n'
 text+='复现：`.venv/bin/python bin/analysis/run_goslar_multiriver_full.py`，随后`.venv/bin/python bin/analysis/report_goslar_multiriver_full.py`。PNG/SVG图采用相同左右双图、固定色阶和0.6阈值，图内不放结论。四张overview概览叠加8条河流的法规边界；6个HWRM情景各自单独出图，避免不同情景边界重叠。QGIS可直接读取两个GPKG和评分TIF。来源文件及校验在expansion_manifest.json，逐产品版本继承comparison_boundaries.gpkg属性。\n'
 (OUT/'READING_NOTE.md').write_text(text)
 files={str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='output_checksums.json'}
 (OUT/'output_checksums.json').write_text(json.dumps(files,indent=2)+'\n');print(json.dumps(qa,indent=2))
if __name__=='__main__':main()
