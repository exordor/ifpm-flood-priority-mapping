#!/usr/bin/env python3
"""TOOLING: present existing baseline overlap and drivers; OUTPUT only, no scoring."""
from pathlib import Path
import csv
import hashlib
import json

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import box
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/goslar_abzucht_diagnostics/fixed_scale'
EXPLANATION=BASE.parent/'explanation'
OUT=BASE.parent/'original_question'

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    inputs={}
    def remember(p):
        inputs[str(p.relative_to(ROOT))]=sha(p)
        return p
    previous=json.loads(remember(EXPLANATION/'manifest.json').read_text())
    for name,digest in previous['inputs'].items():
        if sha(ROOT/name)!=digest:raise ValueError('Explanation source has changed: '+name)
    m=json.loads(remember(BASE/'chain/priority_scenarios/run_manifest.json').read_text())
    cases=json.loads(remember(EXPLANATION/'cases.json').read_text())
    bounds=json.loads(remember(BASE/'expansion_manifest.json').read_text())['display_rectangle']['bounds_utm32n']
    path=remember(ROOT/m['priority_raster_lineage']['path'])
    if sha(path)!=m['priority_raster_lineage']['sha256']:raise ValueError('Priority lineage mismatch')
    with rasterio.open(path) as d:pim=d.read(1,masked=True).filled(np.nan);t=d.transform;crs=d.crs
    def mask(g):return geometry_mask([g],out_shape=pim.shape,transform=t,invert=True)
    hq=gpd.read_file(remember(BASE/'overlay/abzucht_hq100.gpkg')).to_crs(crs)
    inside=mask(hq.geometry.union_all());rectangle=mask(box(*bounds));valid=rectangle&np.isfinite(pim)
    if not np.isfinite(pim[rectangle]).all():raise ValueError('Display rectangle contains NoData')
    high=pim>=.6
    groups={'C':valid&inside&high,'A':valid&inside&~high,'B':valid&~inside&high}
    names={'C':'Inside HQ100, PIM ≥ 0.6','A':'Inside HQ100, PIM < 0.6','B':'Outside HQ100, PIM ≥ 0.6'}
    colors={'C':'#087f8c','A':'#e7a245','B':'#ac4d91'}
    criteria={}
    for k,v in m['criterion_raster_lineage'].items():
        p=remember(ROOT/v['path'])
        if sha(p)!=v['sha256']:raise ValueError('Criterion lineage mismatch')
        with rasterio.open(p) as d:
            if d.transform!=t or d.crs!=crs or d.shape!=pim.shape:raise ValueError('Grid mismatch')
            criteria[k]=d.read(1,masked=True).filled(np.nan)
    for c in cases:
        r,col=c['row'],c['col'];key=c['case']
        if not groups[key][r,col] or abs(pim[r,col]-c['pim'])>1e-6:raise ValueError('Case mismatch')
        if abs(criteria['flood_hazard'][r,col]-c['flood_indicator'])>1e-6:raise ValueError('Case flood indicator mismatch')
        if not np.allclose(rasterio.transform.xy(t,r,col),(c['easting'],c['northing']),rtol=0,atol=1e-6):raise ValueError('Case coordinate mismatch')
        if groups[key].sum()!=c['candidate_cells']:raise ValueError('Case group support mismatch')
        for k,w in m['main_weights'].items():
            if abs(criteria[k][r,col]*w-c['contributions'][k])>1e-6:raise ValueError('Contribution mismatch')
    counts={k:int(v.sum()) for k,v in groups.items()}
    htotal=counts['A']+counts['C'];share=100*counts['C']/htotal
    by_case={c['case']:c for c in cases}
    ring=mask(hq.geometry.union_all().buffer(1000))&~inside&np.isfinite(pim)
    fh_in=float(criteria['flood_hazard'][inside&valid].mean());fh_out=float(criteria['flood_hazard'][ring].mean())
    pim_in=float(pim[inside&valid].mean());pim_out=float(pim[ring].mean())
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'group_summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['group','description','cells','area_km2','denominator']);w.writeheader()
        for k in ['C','A','B']:w.writerow(dict(group=k,description=names[k],cells=counts[k],area_km2=counts[k]*abs(t.a*t.e)/1e6,denominator='Display rectangle; centre-based 30 m raster classification'))
    classified=np.where(valid,0,np.nan)
    for i,k in enumerate(['C','A','B'],1):classified[groups[k]]=i
    profile=dict(driver='GTiff',count=1,height=pim.shape[0],width=pim.shape[1],crs=crs,transform=t,dtype='uint8',nodata=255,compress='deflate')
    with rasterio.open(OUT/'overlap_categories.tif','w',**profile) as d:
        d.write(np.where(valid,classified,255).astype('uint8'),1)
        d.update_tags(classes='0 outside HQ100 below threshold;1 inside high;2 inside below;3 outside high',threshold='PIM >= 0.6',claim_level='diagnostic_only')
    fig=plt.figure(figsize=(14,9))
    grid=fig.add_gridspec(2,3,left=.09,right=.96,top=.84,bottom=.08,height_ratios=[1.7,1],hspace=.52,wspace=.55)
    ax=fig.add_subplot(grid[0,:])
    extent=[t.c/1000,(t.c+t.a*pim.shape[1])/1000,(t.f+t.e*pim.shape[0])/1000,t.f/1000]
    ax.imshow(np.ma.masked_invalid(classified),extent=extent,cmap=ListedColormap(['#eeeeeb',*[colors[k] for k in ['C','A','B']]]),norm=BoundaryNorm([-.5,.5,1.5,2.5,3.5],4),interpolation='nearest')
    hq.geometry.scale(.001,.001,origin=(0,0)).boundary.plot(ax=ax,color='#15568a',linewidth=.8)
    ax.set_xlim(bounds[0]/1000,bounds[2]/1000);ax.set_ylim(bounds[1]/1000,bounds[3]/1000)
    ax.set_aspect('equal');ax.set_xlabel('UTM easting (km)');ax.set_ylabel('UTM northing (km)');ax.ticklabel_format(useOffset=False,style='plain')
    ax.text(1.04,.97,'Blue: HQ100 outline\nGrey: outside HQ100, PIM < 0.6',transform=ax.transAxes,
            va='top',fontsize=8,bbox=dict(facecolor='white',edgecolor='none',alpha=.9,pad=3))
    for c in cases:
        x,y=c['easting']/1000,c['northing']/1000
        ax.plot(x,y,'o',mfc='white',mec='black',ms=7)
        ax.annotate(c['case'],(x,y),xytext=(8,9),textcoords='offset points',weight='bold',fontsize=12,bbox=dict(facecolor='white',edgecolor='none',alpha=.9,pad=1))
    fig.suptitle('Goslar / Abzucht: HQ100 and composite priority',fontsize=19,y=.985)
    handles=[Patch(facecolor=colors[k],label=f'{k}: {names[k]} ({counts[k]} cells)') for k in ['C','A','B']]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.52,.945),frameon=False,ncol=1,fontsize=10)
    labels=['Flood\nconditioning','Erosion\nfactors','Land-cover\npressure','Environmental\ncontext','Exposure\nindicators']
    for i,key in enumerate(['C','A','B']):
        c=next(v for v in cases if v['case']==key);a=fig.add_subplot(grid[1,i])
        values=[c['contributions'][k] for k in m['main_weights']]
        bars=a.barh(np.arange(5),values,color=['#276c96','#af8052','#669958','#8882ae','#ad6f79'])
        a.set_yticks(np.arange(5),labels,fontsize=9);a.invert_yaxis();a.set_xlim(0,.30);a.set_xticks([0,.1,.2,.3]);a.set_xlabel('Contribution to priority',fontsize=9)
        a.bar_label(bars,fmt='%.3f',padding=3,fontsize=8)
        a.set_title(f'{key}: priority {c["pim"]:.3f} | flood {c["flood_indicator"]:.3f}',fontsize=11,loc='left',pad=12)
    for fmt in ['png','svg','pdf']:fig.savefig(OUT/f'original_question_comparison.{fmt}',dpi=180)
    plt.close(fig)
    support=previous['support']['Display rectangle'];complete_share=100*support['all_components_present']/support['pixels']
    note=f'''# Answer to the original question

Question: do the cells with high PIM priority (0.6 or above) coincide with the official Abzucht HQ100 flood zone?

The flood sub-indicator is higher inside HQ100 than in the surrounding ring, but the overlap between the high combined-priority areas and the HQ100 zone is limited.

This package uses only the original population, the original soil inputs, the original weights and the fixed normalization scales; the GHSL replacement population is not used. The main figure is generated from existing rasters and the three verified example points; scoring was not rerun or modified.

- {htotal} 30 m cells inside HQ100: {counts['C']} high-score cells ({share:.2f}%) and {counts['A']} cells below 0.6 ({100-share:.2f}%). The rectangle also contains {counts['B']} high-score cells outside HQ100. Grey in the figure is the remaining area.
- Mean flood sub-indicator: {fh_in:.3f} inside HQ100 and {fh_out:.3f} in the full outer 1 km ring; the combined PIM is {pim_in:.3f} and {pim_out:.3f}.
- Component completeness: cells with values for all {previous['component_count']} model components make up {complete_share:.2f}% of the display rectangle; the other cells lack at least one component, and the original workflow redistributes its weight to the available components.
- Point C (agreement): PIM {by_case['C']['pim']:.3f}, flood {by_case['C']['flood_indicator']:.3f}. Flood, land cover and other factors together produce the high total score.
- Point A (inside the floodplain, not high-scoring): PIM {by_case['A']['pim']:.3f}, flood {by_case['A']['flood_indicator']:.3f}. The flood contribution is still high, but the land-cover and erosion contributions are small, so the combined score does not reach 0.6.
- Point B (high score outside the floodplain): PIM {by_case['B']['pim']:.3f}, flood {by_case['B']['flood_indicator']:.3f}. Land cover and other factors are also high, so the cell scores high outside this HQ100 scenario.

All three examples lack soil K, hillslope LS and population. The erosion term uses only the remaining C factor, and the exposure term is computed from the remaining components. Each case is the cell closest to its group's median PIM.

Open point: whether the PIM should express flood hazard or combined intervention priority. If it is the latter, the flood sub-indicator on its own is the quantity to compare with HQ100.

The legend classes come from a cell-center overlay, so fine boundary differences are affected by the 30 m grid.

Reproduce: `.venv/bin/python bin/analysis/present_abzucht_original_question.py`. The run checks upstream source hashes, group counts, example-point groups and contribution values; the output manifest is manifest.json.
'''
    (OUT/'READING_NOTE.md').write_text(note)
    message=f'''I found a partial correspondence with the official Abzucht HQ100 zone, but limited overlap with our high combined-priority class. Only {share:.1f}% of the zone reaches a priority score of 0.6 or above. The flood indicator itself is higher inside the zone than in the surrounding 1 km area ({fh_in:.3f} versus {fh_out:.3f}).

I marked three examples on the map. At A, the flood indicator is high, but lower contributions from other factors keep the total below 0.6. At C, several factors support a high total. B is high-scoring outside the official zone, which does not by itself establish a false alarm. All three examples have missing soil and population inputs, so I have kept the interpretation preliminary and left the weights unchanged.

Should I evaluate PIM as flood hazard, or as a broader intervention-priority score? This determines whether matching the flood zone is the right target for the combined map.
'''
    (OUT/'message_to_supervisor.txt').write_text(message)
    remember(Path(__file__))
    for name,digest in inputs.items():
        if sha(ROOT/name)!=digest:raise ValueError('Input changed during presentation')
    manifest=dict(boundary_id='goslar_abzucht_display_rectangle',experiment_id='original_question',claim_level='diagnostic_only',
                  command='.venv/bin/python bin/analysis/present_abzucht_original_question.py',source_experiment='fixed_scale',
                  ghsl_used=False,scores_changed=False,weights_changed=False,threshold=.6,group_counts=counts,inputs=inputs,
                  outputs={p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json'})
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(counts))

if __name__=='__main__':main()
