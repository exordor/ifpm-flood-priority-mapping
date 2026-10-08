#!/usr/bin/env python3
"""TOOLING: diagnostic explanation of frozen rectangle scores; no model edits."""
from pathlib import Path
import json,csv,hashlib
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import box,Point
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap,BoundaryNorm
from matplotlib.lines import Line2D

from compare_abzucht_hq100 import read_grid, summarize, COLORS, LABELS
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/goslar_abzucht_display_rectangle_v1/frozen_scale_v1'
OUT=ROOT/'outputs/goslar_abzucht_display_rectangle_v1/explanation_v1'

def component_support(arrays):
    return np.isfinite(np.stack(arrays)).sum(axis=0).astype('uint8')

def representative(mask,score):
    """Nearest median score; ties resolved by distance to candidate centroid."""
    rr,cc=np.where(mask & np.isfinite(score))
    if not len(rr):raise ValueError('No candidate for declared case type')
    vals=score[rr,cc]; diff=np.abs(vals-np.median(vals))
    distance=(rr-rr.mean())**2+(cc-cc.mean())**2
    idx=np.lexsort((cc,rr,distance,diff))[0]
    return int(rr[idx]),int(cc[idx])

def main():
    mpath=BASE/'chain/priority_scenarios/run_manifest.json';m=json.loads(mpath.read_text())
    inputs=[mpath,BASE/'expansion_manifest.json']
    def read(path,ref=None):
        inputs.append(path);return read_grid(path,ref)
    pim,ref=read(ROOT/m['priority_raster_lineage']['path'])
    criteria={k:read(ROOT/v['path'],ref)[0] for k,v in m['criterion_raster_lineage'].items()}
    for item in [m['priority_raster_lineage'],*m['criterion_raster_lineage'].values()]:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256']
    fh=criteria['flood_hazard'];weights=m['main_weights']
    paths={}
    for group,components in m['component_weights'].items():
        for key in components:
            if key=='water_wetland_context':p=BASE/'chain/environmental_sensitivity_v0_1/water_wetland_context_0_1.tif'
            elif key=='protected_ecological_context':p=BASE/'chain/environmental_sensitivity_v0_1/protected_area_context_0_1.tif'
            elif key=='settlement_population':p=BASE/'chain/exposure_indicators/population_exposure_0_1.tif'
            elif key=='critical_infrastructure':p=BASE/'chain/exposure_indicators/built_infrastructure_exposure_0_1.tif'
            else:p=BASE/f'chain/criteria_stack/criteria/{key}_0_1.tif'
            paths[key]=p
    comps={k:read(p,ref)[0] for k,p in paths.items()};count=component_support(list(comps.values()));n=len(comps)
    vpath=BASE/'overlay/abzucht_hq100.gpkg';inputs.append(vpath)
    hq=gpd.read_file(vpath).to_crs(ref['crs']);g=hq.geometry.union_all()
    bounds=json.loads((BASE/'expansion_manifest.json').read_text())['display_rectangle']['bounds_utm32n']
    def mask(geom):return geometry_mask([geom],out_shape=pim.shape,transform=ref['transform'],invert=True)
    rectangle=mask(box(*bounds));inside=mask(g)&rectangle;ring=mask(g.buffer(1000))&~mask(g)&np.isfinite(pim)
    valid=np.isfinite(pim);zones={'HQ100':inside,'Full outside 1 km ring':ring,'Display rectangle':rectangle}
    rows=[]
    for name,zone in zones.items():
        for metric,a in [('Flood indicator',fh),('PIM',pim)]:
            s=summarize(a,zone);rows.append({'zone':name,'metric':metric,**{k:v for k,v in s.items() if k!='class_counts'}})
    support={name:{'pixels':int((zone&valid).sum()),'all_components_present':int((zone&valid&(count==n)).sum()),'missing_by_component':{k:int((zone&valid&~np.isfinite(a)).sum()) for k,a in comps.items()}} for name,zone in zones.items()}
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'score_comparison.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    profile=ref.copy();profile.update(dtype='uint8',nodata=255,count=1)
    with rasterio.open(OUT/'component_count.tif','w',**profile) as dst:
        dst.write(np.where(rectangle&valid,count,255).astype('uint8'),1)
        dst.update_tags(meaning=f'Number of finite model components among {n}; not correctness or accuracy',claim_level='diagnostic_only')
    t=ref['transform'];extent=[t.c/1000,(t.c+t.a*ref['width'])/1000,(t.f+t.e*ref['height'])/1000,t.f/1000]
    hv=hq.copy();hv.geometry=hv.geometry.scale(.001,.001,origin=(0,0))
    def draw(ax,a,title,cmap=None,norm=None,limits=bounds):
        img=ax.imshow(np.ma.masked_invalid(a),extent=extent,origin='upper',cmap=cmap or ListedColormap(COLORS),norm=norm or BoundaryNorm([0,.2,.4,.6,.8,1.000001],5),interpolation='nearest')
        hv.boundary.plot(ax=ax,color='#005da8',linewidth=.9)
        ax.set_xlim(limits[0]/1000,limits[2]/1000);ax.set_ylim(limits[1]/1000,limits[3]/1000);ax.set_aspect('equal')
        ax.set_title(title,loc='left',fontsize=12);ax.set_xlabel('UTM easting (km)');ax.set_ylabel('UTM northing (km)');ax.tick_params(labelsize=8);ax.ticklabel_format(useOffset=False,style='plain')
        return img
    def save(fig,name):
        for fmt in ['png','svg']:fig.savefig(OUT/f'{name}.{fmt}',dpi=180)
        plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(13,6.5));fig.subplots_adjust(left=.07,right=.96,top=.78,bottom=.19,wspace=.22)
    draw(axes[0],fh,'Flood-conditioning indicator (0-1)');im=draw(axes[1],pim,'Composite priority (0-1)')
    fig.suptitle('Separate flood response from composite priority',fontsize=20,y=.96)
    fhrows=[r for r in rows if r['metric']=='Flood indicator'];pr=[r for r in rows if r['metric']=='PIM']
    fig.text(.07,.87,f"HQ100 / full 1 km ring mean: flood indicator {fhrows[0]['mean']:.3f} / {fhrows[1]['mean']:.3f}; composite {pr[0]['mean']:.3f} / {pr[1]['mean']:.3f}",fontsize=12)
    cax=fig.add_axes([.30,.105,.4,.023]);fig.colorbar(im,cax=cax,orientation='horizontal',ticks=[0,.2,.4,.6,.8,1]);fig.text(.07,.025,'Blue: official HQ100 outline | Same 0-1 scale; not inundation probability | Prototype scenario comparison',fontsize=10)
    save(fig,'01_flood_vs_priority')
    fig,axes=plt.subplots(1,2,figsize=(13,6.5));fig.subplots_adjust(left=.07,right=.96,top=.78,bottom=.20,wspace=.30)
    im=draw(axes[0],np.where(rectangle&valid,count,np.nan),f'Available model components (out of {n})',ListedColormap(plt.get_cmap('viridis')(np.linspace(0,1,n-int(count[rectangle&valid].min())+1))),BoundaryNorm(np.arange(int(count[rectangle&valid].min())-.5,n+1.5),n-int(count[rectangle&valid].min())+1))
    missing=support['Display rectangle']['missing_by_component'];ks=[k for k,v in missing.items() if v]
    axes[1].barh(range(len(ks)),[100*missing[k]/support['Display rectangle']['pixels'] for k in ks],color='#bd664f')
    names={'soil_k_factor':'Soil K','settlement_population':'Population','ls_factor':'Hillslope LS','twi_wetness':'Wetness (TWI)'}
    axes[1].set_yticks(range(len(ks)),[names.get(k,k.replace('_',' ')) for k in ks]);axes[1].set_xlim(0,100);axes[1].set_xlabel('Unavailable in display rectangle (%)');axes[1].set_title('Which components are unavailable?',loc='left',fontsize=12)
    full=100*support['Display rectangle']['all_components_present']/support['Display rectangle']['pixels']
    fig.suptitle(f'Only {full:.1f}% of the rectangle has all {n} components',fontsize=20,y=.96)
    fig.text(.07,.87,'A finite composite score can use fewer components. Availability does not measure data quality.',fontsize=12)
    cax=fig.add_axes([.12,.105,.3,.022]);fig.colorbar(im,cax=cax,orientation='horizontal',ticks=range(int(count[rectangle&valid].min()),n+1))
    fig.text(.07,.025,'Missing values remain missing | LS absence includes deliberate channel exclusion | No model weights changed',fontsize=10)
    save(fig,'02_component_availability')
    candidates=[('A','HQ100; PIM below 0.6',inside&valid&(pim<.6)),('B','Outside HQ100; PIM at least 0.6',rectangle&~inside&valid&(pim>=.6)),('C','HQ100; PIM at least 0.6',inside&valid&(pim>=.6))]
    cases=[]
    for label,desc,zone in candidates:
        r,c=representative(zone,pim);x,y=rasterio.transform.xy(t,r,c)
        cases.append({'case':label,'description':desc,'candidate_cells':int(zone.sum()),'row':r,'col':c,'easting':x,'northing':y,'pim':float(pim[r,c]),'flood_indicator':float(fh[r,c]),'components_present':int(count[r,c]),'missing':[k for k,a in comps.items() if not np.isfinite(a[r,c])],'contributions':{k:float(criteria[k][r,c]*weights[k]) for k in weights},'geometry':Point(x,y)})
    roads_path=ROOT/'data/raw/goslar_official_hydrology_and_flood_data/osm_goslar_official_basin_roads.gpkg';inputs.append(roads_path)
    roads=gpd.read_file(roads_path).to_crs(ref['crs']);roads=roads[roads.intersects(box(*bounds))]
    rv=roads.copy();rv.geometry=rv.geometry.scale(.001,.001,origin=(0,0))
    fig,axes=plt.subplots(2,3,figsize=(15,9));fig.subplots_adjust(left=.11,right=.97,top=.82,bottom=.21,wspace=.40,hspace=.46)
    for i,case in enumerate(cases):
        x,y=case['easting'],case['northing'];local=[x-450,y-450,x+450,y+450]
        case_im=draw(axes[0,i],pim,f"{case['case']}: {case['description']}",limits=local)
        rv.plot(ax=axes[0,i],color='#525252',linewidth=.5,alpha=.75)
        axes[0,i].plot(x/1000,y/1000,'o',ms=9,mfc='white',mec='black');axes[0,i].annotate(case['case'],(x/1000,y/1000),xytext=(8,8),textcoords='offset points',fontweight='bold')
        axes[0,i].set_xlim(local[0]/1000,local[2]/1000);axes[0,i].set_ylim(local[1]/1000,local[3]/1000)
        vals=list(case['contributions'].values());ax=axes[1,i];ax.barh(range(5),vals,color=['#236e9c','#ad7941','#659c56','#7977aa','#bd6565'])
        ax.set_yticks(range(5),[LABELS[k] for k in weights],fontsize=8);ax.invert_yaxis();ax.set_xlim(0,.35);ax.set_xlabel('Contribution to composite score')
        ax.set_title(f"PIM {case['pim']:.3f} | Flood {case['flood_indicator']:.3f}\n{case['components_present']}/{n} components available",fontsize=11,loc='left')
    fig.suptitle('Goslar / Abzucht: three locations explain score differences',fontsize=20,y=.96)
    fig.text(.08,.895,'Nearest group-median PIM, then spatial-centroid tie-break | Blue: HQ100; grey lines: roads; dot: selected pixel',fontsize=11)
    fig.text(.08,.03,'Outside HQ100 does not mean flood-free. Illustrative pixels are not representative event samples. Missing components are listed in cases.json.',fontsize=10)
    cax=fig.add_axes([.32,.09,.4,.018]);fig.colorbar(case_im,cax=cax,orientation='horizontal',ticks=[0,.2,.4,.6,.8,1]);cax.set_title('Local-map PIM score',fontsize=9)
    save(fig,'03_explanation_cases')
    serial=[{k:v for k,v in c.items() if k!='geometry'} for c in cases]
    (OUT/'cases.json').write_text(json.dumps(serial,indent=2)+'\n')
    gpd.GeoDataFrame([{k:c[k] for k in ['case','description','pim','flood_indicator','components_present']} for c in cases],geometry=[c['geometry'] for c in cases],crs=ref['crs']).to_file(OUT/'case_locations.gpkg',layer='cases',driver='GPKG')
    # Reconstruct criteria from available components to verify interpretation.
    max_errors={}
    for group,ws in m['component_weights'].items():
        numerator=np.zeros(pim.shape);denominator=np.zeros(pim.shape)
        for key,w in ws.items():
            a=comps[key];ok=np.isfinite(a);numerator+=np.where(ok,a*w,0);denominator+=ok*w
        calc=np.divide(numerator,denominator,out=np.full(pim.shape,np.nan),where=denominator>0)
        ok=rectangle&valid;max_errors[group]=float(np.max(np.abs(calc[ok]-criteria[group][ok])))
        assert max_errors[group]<1e-5
    final_error=float(np.max(np.abs(sum(criteria[k]*w for k,w in weights.items())[rectangle&valid]-pim[rectangle&valid])))
    assert final_error<1e-5
    max_errors['final_pim']=final_error
    manifest={'claim_level':'diagnostic_only','command':'.venv/bin/python bin/analysis/explain_abzucht_comparison.py','component_count':n,'component_names':list(comps),'support':support,'statistics':rows,'case_selection':'Closest to group median PIM; tie nearest candidate pixel centroid; no forced extremum','reconstruction_errors':max_errors,'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in set(inputs+[Path(__file__),Path(__file__).with_name('compare_abzucht_hq100.py')])},'limits':['All components present is availability, not accuracy or complete raw-data provenance','PIM threshold 0.6 retained for illustrative groups, not calibrated flood threshold','Nearby comparison is not a matched control','Roads are existing OSM snapshot, not verified asset inventory']}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    text = f"""# Goslar / Abzucht 对比图改进说明

状态：diagnostic_only。评分、权重和阈值未改动；本包解释现有结果。

洪水子指标在 HQ100 区域与完整周边 1 km 环带的均值分别为 {fhrows[0]['mean']:.3f} 和 {fhrows[1]['mean']:.3f}，综合评分为 {pr[0]['mean']:.3f} 和 {pr[1]['mean']:.3f}。两个量的语义不同，均不直接表示淹水概率；环带包含地图外的部分，属于描述性地理对照。

- [洪水子指标与综合评分](01_flood_vs_priority.png)：同范围、同颜色分级。洪水子指标对洪泛区的响应更突出，综合评分还取决于其他因素。
- [模型分项可用性](02_component_availability.png)：全部 {n} 个模型分项都有有限值的像元占 {full:.2f}%。其余像元缺少至少一项，但原流程会重新分配分项权重而仍然得到综合分。LS 的缺失包括主动排除河道；人口缺失记录的含义仍不确定。分项都有值也不等于来源准确或独立。
- [三个位置及贡献](03_explanation_cases.png)：每组选最接近该组 PIM 中位数的像元，再按空间位置解开并列。背景灰线为已有 OSM 道路。具体坐标、候选数量和缺项见 cases.json，位置可用 case_locations.gpkg 加载。

"""
    for case in serial:
        text += f"## 位置 {case['case']}：{case['description']}\n\nPIM={case['pim']:.3f}，洪水子指标={case['flood_indicator']:.3f}；可用分项 {case['components_present']}/{n}。缺项：{', '.join(case['missing']) or '无'}。\n\n"
    text += """位置 A 的洪水子指标已经较高，但综合分仍不到 0.6。侵蚀分项的贡献很低，不过这里 K 和 LS 都缺失，侵蚀项实际由剩下的 C 因子支撑，不能据此断言当地实际侵蚀很低。土地覆盖项贡献也较低。这解释了综合分与洪水子指标的差别。

位置 B 在官方 HQ100 范围外，洪水子指标仍较高，且土地覆盖等因素共同抬高综合分。它提示需要复核局部河网和各项数据，但在缺少实测证据时不能称作误报。位置 C 展示洪泛区内达到 0.6 的例子，也有缺项；高分不能替代完整数据证据。

本次完成的是诊断与表达改进，没有修补原始人口/土壤数据或修改模型。下一步若修复缺项，应作为另一个有明确数据语义的实验。

复现：`.venv/bin/python bin/analysis/explain_abzucht_comparison.py`。分项到五个指标、五个指标到 PIM 的重建误差必须小于 1e-5；输入哈希记录在 manifest.json。
"""
    (OUT/'READING_NOTE.md').write_text(text)
    print(json.dumps({'support':support,'scores':rows,'cases':serial},indent=2))

if __name__=='__main__':main()
