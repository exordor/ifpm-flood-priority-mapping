#!/usr/bin/env python3
"""TOOLING: source-backed replacements and explicit LS applicability scenarios."""
from pathlib import Path
import sys
import csv
import json
import tempfile
from datetime import datetime, timezone
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.features import geometry_mask
import geopandas as gpd
from shapely.geometry import box

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'bin'),str(Path(__file__).parent)]
sys.path.insert(0,str(ROOT/'bin/acquire'))
from compare_abzucht_hq100 import read_grid, digest, COLORS, LABELS
from repair_abzucht_gaps import score as legacy_score, write
from abzucht_fixed_scale_normalization import apply
from tune_abzucht_weights import weights_at
from pull_abzucht_soilgrids2017 import PROPS, DEPTHS, depth_average
from pull_goslar_soilgrids_window import williams_k

BASE=ROOT/'outputs/goslar_abzucht_diagnostics/fixed_scale'
DEST=BASE.parent/'input_completion'
SOIL=ROOT/'data/raw/soilgrids2017_abzucht'
WEIGHTS=[.34,.45,.55,.65,.75,.76,.77,.78,.79,.80]
COMMAND='.venv/bin/python bin/analysis/complete_abzucht_inputs.py'


def terrain_ls(slope, sca):
    valid=np.isfinite(slope)&np.isfinite(sca)&(slope>=0)&(sca>=0)
    result=np.full(slope.shape,np.nan,dtype='float32')
    result[valid]=np.minimum(50.,(sca[valid]/22.13)**.4*(np.sin(np.radians(slope[valid]))/.0896)**1.2)
    return result


def strict_criteria(parts, components, domain, channel=None):
    """Require every applicable component. LS alone is not applicable in channels.

    In the declared hillslope scenario, channel erosion factors use K/C at
    0.5/0.5, i.e. the original .25/.25 normalized over applicable components.
    No missing K, population or any other applicable input is renormalized away.
    """
    output={}
    for group, weights in components.items():
        numerator=np.zeros(domain.shape,dtype='float64')
        denominator=np.zeros(domain.shape,dtype='float64')
        valid=domain.copy()
        for key,w in weights.items():
            applicable=domain & (~channel if key=='ls_factor' and channel is not None else True)
            valid &= ~applicable | np.isfinite(parts[key])
            numerator[applicable]+=np.where(np.isfinite(parts[key][applicable]),parts[key][applicable],0)*w
            denominator[applicable]+=w
        a=np.full(domain.shape,np.nan)
        good=valid&(denominator>0)
        a[good]=numerator[good]/denominator[good]
        output[group]=a.astype('float32').astype('float64')
    return output


def weighted(criteria, weights, domain):
    ok=domain & np.all(np.isfinite(np.stack(list(criteria.values()))),axis=0)
    result=np.full(domain.shape,np.nan)
    result[ok]=sum(criteria[k][ok]*w for k,w in weights.items())
    return result.astype('float32').astype('float64')


def stats(a, zone):
    v=a[zone & np.isfinite(a)]
    return dict(total=int(zone.sum()),valid=int(v.size),
                mean=float(v.mean()) if v.size else None,
                high_share=float((v>=.6).mean()) if v.size else None)


def main():
    inputs={}
    def pin(p,expected=None):
        h=digest(p)
        if expected and h!=expected:raise ValueError('Source hash mismatch: '+str(p))
        inputs[str(p.relative_to(ROOT))]=h
        return p
    def read(p,ref=None):return read_grid(pin(p),ref)[0]
    m=json.loads(pin(BASE/'chain/priority_scenarios/run_manifest.json').read_text())
    anchors=json.loads(pin(BASE/'frozen_normalization.json').read_text())
    old,ref=read_grid(pin(ROOT/m['priority_raster_lineage']['path'],m['priority_raster_lineage']['sha256']))
    domain=np.isfinite(old)
    baseline_criteria={k:read_grid(pin(ROOT/v['path'],v['sha256']),ref)[0] for k,v in m['criterion_raster_lineage'].items()}
    explanation=json.loads(pin(BASE.parent/'explanation/manifest.json').read_text())
    for name,h in explanation['inputs'].items():pin(ROOT/name,h)
    parts={}
    special={'water_wetland_context':'environmental_sensitivity/water_wetland_context_0_1.tif',
             'protected_ecological_context':'environmental_sensitivity/protected_area_context_0_1.tif',
             'settlement_population':'exposure_indicators/population_exposure_0_1.tif',
             'critical_infrastructure':'exposure_indicators/built_infrastructure_exposure_0_1.tif'}
    for weights in m['component_weights'].values():
        for key in weights:
            parts[key]=read(BASE/'chain'/special.get(key,f'criteria_stack/criteria/{key}_0_1.tif'),ref)
    replay,_=legacy_score(parts,m,domain)
    error=float(np.max(np.abs(replay[domain]-old[domain])))
    if error>1e-6:raise ValueError('Baseline cannot be reconstructed')
    gap=BASE.parent/'gap_repair'
    gm=json.loads(pin(gap/'manifest.json').read_text())
    for name,h in gm['inputs'].items():pin(ROOT/name,h)
    upgraded=dict(parts)
    for key in ['settlement_population','twi_wetness']:
        name=f'ghsl_flat_0.1deg/{key}.tif'
        upgraded[key]=read_grid(pin(gap/name,gm['outputs'][name]['sha256']),ref)[0]
    sm=json.loads(pin(SOIL/'source_manifest.json').read_text())
    pin(ROOT/sm['reference_path'],sm['reference_sha256'])
    for name,v in sm['files'].items():pin(SOIL/name,v['sha256'])
    pin(ROOT/'bin/acquire/pull_abzucht_soilgrids2017.py',sm['implementation_sha256'])
    pin(ROOT/'bin/acquire/pull_goslar_soilgrids_window.py',sm['formula_implementation_sha256'])
    native_ref=None;kvals=[]
    for level,depth in enumerate(DEPTHS,1):
        values={}
        for code,key in PROPS.items():
            a,pr=read_grid(SOIL/f'{code}_M_sl{level}_250m_ll.tif',native_ref)
            if native_ref is None:native_ref=pr
            values[key]=a/10 if key=='soc' else a
        total=values['clay']+values['sand']+values['silt']
        if np.any(np.abs(total[np.isfinite(total)]-100)>3):raise ValueError('Texture sum inconsistent')
        kvals.append(williams_k(values['clay'],values['silt'],values['sand'],values['soc'])*.1317)
    native_k=depth_average(kvals).astype('float32')
    k=np.full(old.shape,np.nan,dtype='float32')
    reproject(native_k,k,src_transform=native_ref['transform'],src_crs=native_ref['crs'],src_nodata=np.nan,
              dst_transform=ref['transform'],dst_crs=ref['crs'],dst_nodata=np.nan,resampling=Resampling.nearest)
    k[~domain]=np.nan
    complete=dict(upgraded)
    complete['soil_k_factor']=apply(k,anchors['soilgrids_kfactor:0'],domain)
    slope=read(BASE/'chain/terrain_preprocessing/goslar_focus_slope_degrees_utm32n_30m.tif',ref)
    sca=read(BASE/'chain/hydrology_derivatives/goslar_focus_flow_accumulation_sca.tif',ref)
    flow=read(BASE/'chain/hydrology_derivatives/goslar_focus_flow_accumulation.tif',ref)
    channel=domain & (flow>500)
    ls=terrain_ls(slope,sca)
    ls_old=read(BASE/'chain/ls_factor/goslar_focus_ls_factor_capped50_hillslope_30m.tif',ref)
    if not np.array_equal(domain & ~np.isfinite(ls_old),channel):raise ValueError('LS missing beyond channel exclusion')
    ls_error=float(np.max(np.abs(ls[domain&~channel]-ls_old[domain&~channel])))
    if ls_error>1e-4:raise ValueError('LS replay differs from baseline formula')
    allterrain=dict(complete)
    allterrain['ls_factor']=apply(ls,anchors['criteria_stack:2'],domain)
    hq=gpd.read_file(pin(BASE/'overlay/abzucht_hq100.gpkg')).to_crs(ref['crs'])
    geom=hq.geometry.union_all()
    def mask(g):return geometry_mask([g],out_shape=old.shape,transform=ref['transform'],invert=True)
    inside=mask(geom)
    ring=mask(geom.buffer(1000))&~inside
    bk_dir=ROOT/'data/raw/lbeg_bk50_abzucht'
    bk_manifest=json.loads(pin(bk_dir/'source_manifest.json').read_text())
    bk_path=bk_dir/'bk50_abzucht_display_context.gpkg'
    bk=gpd.read_file(pin(bk_path,bk_manifest['files'][bk_path.name]['sha256'])).to_crs(ref['crs'])
    bk_typed=bk[bk.botyp.notna()].copy()
    bk_typed.geometry=bk_typed.geometry.make_valid()
    bk_coverage=mask(bk_typed.geometry.union_all())
    bk_evidence=dict(hq100_cells=int(inside.sum()),soil_type_cells=int((inside&bk_coverage).sum()),
                     numerical_k_available=False,role='Independent soil-type context, never used as numeric K')
    bounds=json.loads(pin(BASE/'expansion_manifest.json').read_text())['display_rectangle']['bounds_utm32n']
    rect=mask(box(*bounds))
    zones={'HQ100':inside,'Ring_1km':ring,'Rectangle':rect,'Model_domain':domain}
    grid_box=box(*rasterio.transform.array_bounds(ref['height'],ref['width'],ref['transform']))
    if geom.buffer(1000).difference(grid_box).area>.01:raise ValueError('Ring clipped by grid')
    scenarios={'baseline':parts,'population_twi':upgraded,'soil2017_hillslope':complete,'soil2017_allterrain':allterrain}
    criteria={'baseline':baseline_criteria,'population_twi':legacy_score(upgraded,m,domain)[1],
              'soil2017_hillslope':strict_criteria(complete,m['component_weights'],domain,channel),
              'soil2017_allterrain':strict_criteria(allterrain,m['component_weights'],domain)}
    out=Path(tempfile.mkdtemp(prefix='.input_completion_v2_incomplete_',dir=DEST.parent))
    write(out/'soil_k_2017_native_si.tif',native_k,native_ref,claim_level='sensitivity_scenario',
          meaning='Williams K at 0,5,15,30cm, trapezoidal 0-30cm mean, US-to-SI factor 0.1317')
    def save(name,a,**tags):write(out/name,a,ref,claim_level='sensitivity_scenario',**tags)
    save('bk50_soil_type_coverage.tif',np.where(domain,bk_coverage,np.nan),meaning='Official typed-soil coverage; no numerical K value inferred')
    coverage=[];summary=[];rasters={}
    for name,components in scenarios.items():
        full=np.all(np.isfinite(np.stack(list(components.values()))),axis=0)&domain
        applicable_full=full.copy()
        if name!='soil2017_allterrain':
            applicable_full=domain.copy()
            for key,a in components.items():applicable_full &= np.isfinite(a)|(channel if key=='ls_factor' else False)
        for zone,z in zones.items():
            summary.append(dict(scenario=name,zone=zone,total=int(z.sum()),all_14=int((z&full).sum()),
                                all_applicable=int((z&applicable_full).sum()),channel_cells=int((z&channel).sum())))
            for key,a in components.items():
                valid=z&np.isfinite(a)
                na=z&channel if name!='soil2017_allterrain' and key=='ls_factor' else np.zeros(z.shape,bool)
                coverage.append(dict(scenario=name,zone=zone,component=key,total=int(z.sum()),valid=int(valid.sum()),
                                     not_applicable=int(na.sum()),unknown=int((z&~np.isfinite(a)&~na).sum())))
        if name.startswith('soil2017'):
            for key,a in components.items():save(f'{name}/components/{key}.tif',a,meaning=key)
            for key,a in criteria[name].items():save(f'{name}/criteria/{key}.tif',a,meaning=LABELS[key])
        count=np.isfinite(np.stack(list(components.values()))).sum(axis=0)
        save(f'{name}/component_count.tif',np.where(domain,count,np.nan),meaning='Finite components; not observational accuracy')
        for f in WEIGHTS:
            a=weighted(criteria[name],weights_at(m['main_weights'],f),domain)
            rasters[name,f]=a
            save(f'{name}/priority_fh_{round(f*100):03d}.tif',a,flood_weight=str(f),meaning='Composite scenario score, not inundation probability')
    save('soil_k_2017_si.tif',k,units='t ha h / (ha MJ mm)',effective_resolution='nominal 250 m',resampling='nearest')
    wc=read(BASE/'landcover/worldcover_aligned.tif',ref)
    save('remaining_soil_gap_mask.tif',np.where(domain,~np.isfinite(k),np.nan),meaning='Unfilled soil source gaps, not zero erodibility')
    remaining_gaps=[]
    for zname,z in zones.items():
        codes,counts=np.unique(wc[z&~np.isfinite(k)],return_counts=True)
        for code,count in zip(codes,counts):
            remaining_gaps.append(dict(zone=zname,worldcover_code=float(code) if np.isfinite(code) else 'NoData',cells=int(count)))
    save('ls_allterrain_capped50.tif',np.where(domain,ls,np.nan),meaning='Formula extended into channels for sensitivity only; not accepted hillslope LS there')
    save('ls_not_applicable_channel_mask.tif',np.where(domain,channel,np.nan),meaning='Flow accumulation >500 cells; hillslope LS excluded here')
    # Fixed support across all four data alternatives, and across all tested weights.
    common=domain&np.all(np.isfinite(np.stack([rasters[n,.34] for n in scenarios])),axis=0)
    save('comparison_common_support.tif',np.where(domain,common,np.nan))
    comparisons=[];contributions=[]
    for name in scenarios:
        for f in WEIGHTS:
            a=rasters[name,f]
            for zname,z in zones.items():
                comparisons.append(dict(scenario=name,flood_weight=f,zone=zname,**stats(a,z&common)))
            for key,w in weights_at(m['main_weights'],f).items():
                contributions.append(dict(scenario=name,flood_weight=f,criterion=key,
                    inside=float(np.mean(criteria[name][key][inside&common])*w),
                    ring=float(np.mean(criteria[name][key][ring&common])*w)))
    k_comparison=[]
    old_k=read(BASE/'chain/soil_k_factor/soil_k_factor_aligned_250m_effective_30m.tif',ref)
    for name,z in zones.items():
        both=z&np.isfinite(old_k)&np.isfinite(k)
        k_comparison.append(dict(zone=name,shared_cells=int(both.sum()),
          mean_old=float(np.mean(old_k[both])),mean_new=float(np.mean(k[both])),
          mean_absolute_difference=float(np.mean(np.abs(k[both]-old_k[both]))),
          below_frozen_anchor=int((z&np.isfinite(k)&(k<anchors['soilgrids_kfactor:0']['clip_low'])).sum()),
          above_frozen_anchor=int((z&np.isfinite(k)&(k>anchors['soilgrids_kfactor:0']['clip_high'])).sum())))
    def table(name,rows):
        with (out/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    for name,rows in [('coverage.csv',coverage),('coverage_summary.csv',summary),('weight_comparison.csv',comparisons),
                      ('contributions.csv',contributions),('soil_version_comparison.csv',k_comparison)]:table(name,rows)
    if remaining_gaps:table('remaining_soil_gaps.csv',remaining_gaps)
    table('weights.csv',[dict(flood_weight=f,**weights_at(m['main_weights'],f)) for f in WEIGHTS])
    rankings=[]
    for name in scenarios:
        for f in WEIGHTS:
            i=next(r for r in comparisons if r['scenario']==name and r['flood_weight']==f and r['zone']=='HQ100')
            o=next(r for r in comparisons if r['scenario']==name and r['flood_weight']==f and r['zone']=='Ring_1km')
            if i['high_share'] is None or o['high_share'] is None:raise ValueError('No common comparison cells')
            rankings.append(dict(scenario=name,flood_weight=f,inside_high=i['high_share'],ring_high=o['high_share'],
                                 high_share_gap=i['high_share']-o['high_share']))
    table('weight_ranking.csv',rankings)
    make_figures(out,summary,rankings,rasters,rect&domain,bounds,hq,ref,contributions)
    for source in [Path(__file__),ROOT/'bin/analysis/repair_abzucht_gaps.py',ROOT/'bin/analysis/abzucht_fixed_scale_normalization.py',
                   ROOT/'bin/analysis/compare_abzucht_hq100.py',ROOT/'bin/analysis/tune_abzucht_weights.py',ROOT/'bin/_lib/standardization.py']:pin(source)
    bests={name:max([r for r in rankings if r['scenario']==name],key=lambda r:(r['high_share_gap'],-r['flood_weight'])) for name in scenarios}
    report='''# Abzucht input completion and weight recalculation

This round replaces inputs that had gaps with the full-layer GHSL2020 population estimate and the SoilGrids2017 soil prediction. Old and new soil versions are not mixed, and missing values are not filled with zero. Zero-slope TWI keeps the 0.1-degree candidate lower bound. The original data and earlier experiments are retained.

Recalculation confirms that all missing LS values come from the original channel exclusion (flow accumulation >500 cells), not from missing DEM data. soil2017_hillslope keeps these locations as not applicable and explicitly forms the erosion factor in channels from K and C at 50% each; a missing value in any other applicable input still blocks scoring of that indicator. soil2017_allterrain additionally extends the same LS formula into the channels as a method-sensitivity scenario; it must not be described as valid hillslope LS data restored in the channels.

All replacement sources are predictions or model estimates (SoilGrids2017 is an older version than the current one); complete coverage does not imply accuracy. Soil K keeps the old normalization anchors; clipping counts and version differences in the overlap area are in soil_version_comparison.csv.

'''
    for name in scenarios:
        r=next(r for r in summary if r['scenario']==name and r['zone']=='HQ100')
        report+=f"- {name}: all 14 components present in HQ100 {r['all_14']}/{r['total']}; all applicable components present {r['all_applicable']}/{r['total']}.\n"
    report+='\nAll tried weights (the original main weights and 34–80%) were recalculated on the same common support domain.\n\n'
    report+=f"The official German BK50 soil types cover {bk_evidence['soil_type_cells']}/{bk_evidence['hq100_cells']} cells inside HQ100. The public fields contain no numeric K, so they serve only as background on soil presence and type; K was not guessed from soil names.\n\n"
    for name,r in bests.items():report+=f"- {name}: at the fixed 0.6 threshold, the highest gap among this round's candidates is at a flood weight of {r['flood_weight']:.0%}, with an inside-outside high-score share difference of {100*r['high_share_gap']:.2f} percentage points.\n"
    report+=f'\nReproduce: `.venv/bin/python bin/acquire/pull_abzucht_soilgrids2017.py`, then `{COMMAND}`. The rationale for the original population replacement is in the existing gap_repair.\n'
    (out/'READING_NOTE.md').write_text(report)
    # Reopen all persisted arrays; exact score/class support equality.
    for (name,f),a in rasters.items():
        b=read_grid(out/f'{name}/priority_fh_{round(f*100):03d}.tif',ref)[0]
        if not np.array_equal(a,b,equal_nan=True):raise ValueError('Saved score differs')
    for name,h in inputs.items():
        if digest(ROOT/name)!=h:raise ValueError('Input changed during run')
    manifest=dict(boundary_id='goslar_abzucht_display_rectangle',experiment_id='input_completion',
      claim_level='sensitivity_scenario',command=COMMAND,inputs=inputs,baseline_replay_error=error,ls_replay_error=ls_error,
      normalization=anchors,main_weights=m['main_weights'],component_weights=m['component_weights'],
      channel_component_weights={'soil_k_factor':.5,'c_factor':.5,'ls_factor':'not_applicable'},
      strict_policy='For soil2017 scenarios all applicable components required; no missing-source renormalization',
      inherited_baseline_policy='baseline/population_twi reproduce available-component renormalization only for comparison',
      methods=dict(population='GHSL2020 whole-layer 100m model count allocation',soil=sm,
                   soil_k='Williams K at depth points0/5/15/30cm, trapezoidal0-30cm mean, US-to-SI x0.1317; candidate soil representation',
                   twi='existing 0.1 degree slope-floor sensitivity on missing flat cells only',
                   ls='Hillslope channel exclusion preserved; alternate allterrain formula is sensitivity only'),
      common_support={name:dict(total=int(z.sum()),valid=int((z&common).sum())) for name,z in zones.items()},
      official_bk50_context=bk_evidence,
      best_tested_at_fixed_06=bests,coverage=summary,soil_version_comparison=k_comparison,
      independent_validation=False,outputs={str(p.relative_to(out)):digest(p) for p in out.rglob('*') if p.is_file()})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if DEST.exists():
        backup=DEST.with_name(DEST.name+'_previous_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));DEST.rename(backup)
        try:out.rename(DEST)
        except Exception:backup.rename(DEST);raise
    else:out.rename(DEST)
    print(json.dumps(dict(coverage=[r for r in summary if r['zone']=='HQ100'],best=bests),indent=2))


def make_figures(out,summary,rankings,rasters,rect,bounds,hq,ref,contributions):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    from matplotlib.colors import ListedColormap,BoundaryNorm
    names=['baseline','population_twi','soil2017_hillslope','soil2017_allterrain']
    labels=['Original','Population + flat TWI','Population + soil\n(hillslope rule)','Population + soil\n(all-terrain LS test)']
    fig,ax=plt.subplots(figsize=(10,5));fig.subplots_adjust(left=.13,right=.97,top=.78,bottom=.27)
    rows=[next(r for r in summary if r['scenario']==n and r['zone']=='HQ100') for n in names]
    x=np.arange(4)
    a=[100*r['all_14']/r['total'] for r in rows];b=[100*r['all_applicable']/r['total'] for r in rows]
    bars=ax.bar(x-.17,a,width=.34,label='All 14 finite',color='#7198ac');ax.bar_label(bars,fmt='%.1f%%',padding=3)
    bars=ax.bar(x+.17,b,width=.34,label='All applicable inputs available',color='#237d6c');ax.bar_label(bars,fmt='%.1f%%',padding=3)
    ax.set(xticks=x,xticklabels=labels,ylim=(0,115),ylabel='HQ100 cells (%)');ax.legend(loc='upper left',bbox_to_anchor=(0,1.23),ncol=2,frameon=False)
    fig.suptitle('Goslar / Abzucht: input coverage improves; channel LS remains a method choice',fontsize=14)
    fig.text(.06,.06,'Model-derived replacements | Hillslope LS is not applicable in channels; all-terrain LS is an explicit sensitivity test.',fontsize=9)
    for ext in ['png','svg','pdf']:fig.savefig(out/f'coverage_comparison.{ext}',dpi=170)
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,5));fig.subplots_adjust(left=.16,right=.97,top=.80,bottom=.23,wspace=.45)
    for ax,zone,title in zip(axes,['inside','ring'],['Inside HQ100','Outside, within 1 km']):
        baseline={r['criterion']:r[zone] for r in contributions if r['scenario']=='baseline' and r['flood_weight']==.34}
        for offset,name,label in [(-.18,'soil2017_hillslope','Replaced inputs, hillslope rule'),(.18,'soil2017_allterrain','All-terrain LS sensitivity')]:
            values={r['criterion']:r[zone] for r in contributions if r['scenario']==name and r['flood_weight']==.34}
            ax.barh(np.arange(5)+offset,[values[k]-baseline[k] for k in baseline],height=.34,label=label)
        ax.set(yticks=np.arange(5),yticklabels=[LABELS[k] for k in baseline],title=title,xlabel='Change in mean contribution')
        ax.xaxis.set_major_locator(MaxNLocator(4))
        ax.axvline(0,color='#777777',linewidth=.8);ax.invert_yaxis()
    fig.suptitle('Which criteria explain the score change',fontsize=16)
    fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',ncol=2,frameon=False)
    fig.text(.10,.86,'At the original 34% flood weight | Arithmetic contribution differences, not causal effects',fontsize=10)
    for ext in ['png','svg','pdf']:fig.savefig(out/f'input_change_drivers.{ext}',dpi=170)
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,5));fig.subplots_adjust(top=.81,bottom=.22,wspace=.28)
    for name,label in zip(names,labels):
        rows=[r for r in rankings if r['scenario']==name]
        axes[0].plot([100*r['flood_weight'] for r in rows],[100*r['inside_high'] for r in rows],'o-',label=label.replace('\n',' '))
        axes[1].plot([100*r['flood_weight'] for r in rows],[100*r['high_share_gap'] for r in rows],'o-')
    axes[0].set(ylabel='HQ100 cells scoring ≥0.6 (%)',xlabel='Flood weight (%)')
    axes[1].set(ylabel='Inside minus 1 km ring high share (pp)',xlabel='Flood weight (%)')
    for ax in axes:ax.grid(alpha=.2)
    fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',ncol=2,fontsize=9,frameon=False)
    fig.suptitle('Goslar / Abzucht: recheck weight response after replacing missing inputs',fontsize=15)
    fig.text(.1,.86,'Same comparison support and 0.6 cutoff | Source and channel-method effects are shown separately',fontsize=10)
    for ext in ['png','svg','pdf']:fig.savefig(out/f'weight_recheck.{ext}',dpi=170)
    plt.close(fig)
    t=ref['transform'];extent=[t.c/1000,(t.c+t.a*ref['width'])/1000,(t.f+t.e*ref['height'])/1000,t.f/1000]
    hv=hq.copy();hv.geometry=hv.geometry.scale(.001,.001,origin=(0,0))
    fig,axes=plt.subplots(2,2,figsize=(12,10));fig.subplots_adjust(top=.88,bottom=.13,hspace=.3,wspace=.22)
    for ax,name,label in zip(axes.flat,names,labels):
        im=ax.imshow(np.ma.masked_invalid(np.where(rect,rasters[name,.34],np.nan)),extent=extent,
          cmap=ListedColormap(COLORS),norm=BoundaryNorm([0,.2,.4,.6,.8,1.000001],5),interpolation='nearest')
        hv.boundary.plot(ax=ax,color='#1767aa',linewidth=.8)
        ax.set(xlim=(bounds[0]/1000,bounds[2]/1000),ylim=(bounds[1]/1000,bounds[3]/1000),
               title=label.replace('\n',' '),xlabel='UTM easting (km)',ylabel='UTM northing (km)')
        ax.ticklabel_format(useOffset=False,style='plain')
    fig.suptitle('Goslar / Abzucht: isolate input changes at the original 34% flood weight',fontsize=15)
    cax=fig.add_axes([.32,.075,.36,.018]);fig.colorbar(im,cax=cax,orientation='horizontal',ticks=[0,.2,.4,.6,.8,1])
    fig.text(.08,.025,'Blue: HQ100; white: missing soil input | Prototype source/method comparison, not validated flood risk.',fontsize=9)
    for ext in ['png','svg','pdf']:fig.savefig(out/f'input_change_maps.{ext}',dpi=170)
    plt.close(fig)


if __name__=='__main__':main()
