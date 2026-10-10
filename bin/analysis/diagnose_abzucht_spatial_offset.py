#!/usr/bin/env python3
"""TOOLING: exact cell-centre distance from high scores to Abzucht HQ100."""
from pathlib import Path
from datetime import datetime, timezone
import atexit
import csv
import hashlib
import json
import shutil
import tempfile

import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from scipy.ndimage import distance_transform_edt
import shapely
from shapely.geometry import box

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/goslar_abzucht_display_rectangle_v1/frozen_scale_v1'
COMPLETE=BASE.parent/'input_completion_v2'
DEST=BASE.parent/'spatial_offset_v1'
COMMAND='.venv/bin/python bin/analysis/diagnose_abzucht_spatial_offset.py'
THRESHOLD=.6
LABELS=['Inside HQ100','Outside, 0–30 m','Outside, 30–60 m','Outside, 60–90 m',
        'Outside, 90–150 m','Outside, >150 m']
COLORS=['#25867a','#f2a03a','#f4c15b','#f6dd89','#aa75aa','#a93972']


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def classify_distance(distance,inside):
    """Signed role comes from exact point-in-polygon, not buffered raster masks."""
    result=np.full(distance.shape,-1,dtype='int8')
    result[inside]=0
    out=~inside
    result[out&(distance>0)&(distance<=30)]=1
    result[out&(distance>30)&(distance<=60)]=2
    result[out&(distance>60)&(distance<=90)]=3
    result[out&(distance>90)&(distance<=150)]=4
    result[out&(distance>150)]=5
    if (result<0).any():raise ValueError('Unclassified point on polygon boundary')
    return result


def analyze(high_rows,high_cols,score,transform,geometry,stream_distance):
    xx,yy=rasterio.transform.xy(transform,high_rows,high_cols)
    xx=np.asarray(xx); yy=np.asarray(yy)
    points=shapely.points(xx,yy)
    inside=shapely.intersects(geometry,points)
    distance=shapely.distance(points,geometry)
    group=classify_distance(distance,inside)
    cell_half=abs(transform.a)/2
    cells=shapely.box(xx-cell_half,yy-cell_half,xx+cell_half,yy+cell_half)
    touched=shapely.intersects(geometry,cells)
    near_stream=stream_distance[high_rows,high_cols]
    rows=[]
    for i in range(len(high_rows)):
        rows.append(dict(row=int(high_rows[i]),col=int(high_cols[i]),easting_m=float(xx[i]),northing_m=float(yy[i]),
                         score=float(score[high_rows[i],high_cols[i]]),distance_to_hq100_m=float(distance[i]),
                         distance_group=LABELS[int(group[i])],inside_hq100_center=bool(inside[i]),
                         cell_intersects_hq100=bool(touched[i]),distance_to_model_stream_m=float(near_stream[i])))
    return group,touched,near_stream,rows


def main():
    inputs={}
    def remember(path, expected=None):
        value=sha(path)
        if expected and value!=expected:raise ValueError('Source hash mismatch: '+str(path))
        inputs[str(path.relative_to(ROOT))]=value
        return path
    run=json.loads(remember(BASE/'chain/priority_scenarios/run_manifest.json').read_text())
    replay=json.loads(remember(COMPLETE/'manifest.json').read_text())
    for name,expected in replay['inputs'].items():remember(ROOT/name,expected)
    baseline_path=remember(ROOT/run['priority_raster_lineage']['path'],run['priority_raster_lineage']['sha256'])
    scenarios={'Original 34%':baseline_path,
               'Completed 34%':COMPLETE/'soil2017_hillslope/priority_fh_034.tif',
               'Completed 80%':COMPLETE/'soil2017_hillslope/priority_fh_080.tif'}
    for name,path in scenarios.items():
        if name!='Original 34%':remember(path,replay['outputs'][str(path.relative_to(COMPLETE))])
    hq=gpd.read_file(remember(BASE/'overlay/abzucht_hq100.gpkg'))
    with rasterio.open(baseline_path) as src:
        ref=src.profile;original=src.read(1,masked=True).astype('float64').filled(np.nan)
    if str(ref['crs'])!='EPSG:32632' or ref['transform'].a!=30 or ref['transform'].e!=-30:
        raise ValueError('Expected 30 m UTM32N grid')
    hq=hq.to_crs(ref['crs'])
    if hq.empty or not hq.is_valid.all():raise ValueError('Invalid official polygon')
    geometry=hq.geometry.union_all()
    bounds=json.loads(remember(BASE/'expansion_manifest.json').read_text())['display_rectangle']['bounds_utm32n']
    rectangle=geometry_mask([box(*bounds)],out_shape=original.shape,transform=ref['transform'],invert=True)
    inside_mask=geometry_mask([geometry],out_shape=original.shape,transform=ref['transform'],invert=True)
    stream_path=remember(BASE/'chain/hydrology_derivatives/goslar_focus_streams_t500.tif')
    with rasterio.open(stream_path) as src:
        if src.crs!=ref['crs'] or src.transform!=ref['transform'] or src.shape!=original.shape:
            raise ValueError('Model stream grid mismatch')
        stream=src.read(1,masked=True).filled(np.nan)==1
    if not stream.any():raise ValueError('No model stream pixels')
    stream_distance=distance_transform_edt(~stream)*30
    footprint=box(*rasterio.transform.array_bounds(ref['height'],ref['width'],ref['transform']))
    if geometry.difference(footprint).area>.01:raise ValueError('HQ100 outside reference grid')
    out=Path(tempfile.mkdtemp(prefix='.spatial_offset_v1_incomplete_',dir=DEST.parent))
    atexit.register(shutil.rmtree,out,ignore_errors=True)
    arrays={};summary=[];details=[]
    for name,path in scenarios.items():
        if name=='Original 34%':score=original
        else:
            with rasterio.open(path) as src:
                if src.crs!=ref['crs'] or src.transform!=ref['transform'] or src.shape!=original.shape:
                    raise ValueError('Scenario grid mismatch')
                score=src.read(1,masked=True).astype('float64').filled(np.nan)
        support=rectangle&np.isfinite(score)
        high=support&(score>=THRESHOLD)
        r,c=np.where(high)
        group,touched,near_stream,rows=analyze(r,c,score,ref['transform'],geometry,stream_distance)
        if not np.array_equal((group==0),inside_mask[r,c]):raise ValueError('Point/raster centre mismatch')
        for row in rows:row['scenario']=name
        details.extend(rows)
        counts=np.bincount(group,minlength=len(LABELS))
        outside=group>0
        outside_count=int(outside.sum())
        intersecting_outside=int((outside&touched).sum())
        near30_outside=int((group==1).sum())
        if intersecting_outside>near30_outside:raise ValueError('Cell overlap farther than expected')
        summary.append(dict(scenario=name,rectangle_cells=int(rectangle.sum()),scored_rectangle_cells=int(support.sum()),
            hq100_center_cells=int(inside_mask.sum()),scored_hq100_center_cells=int((inside_mask&np.isfinite(score)).sum()),
            high_cells=int(high.sum()),inside_hq100_high=int(counts[0]),outside_hq100_high=outside_count,
            outside_cell_intersects_hq100=intersecting_outside,
            outside_within_90m=int(counts[1:4].sum()),outside_over_150m=int(counts[5]),
            outside_over_150m_share=float(counts[5]/outside_count) if outside_count else None,
            outside_high_on_model_stream=int((outside&(near_stream==0)).sum()),
            far_over_150m_on_model_stream=int(((group==5)&(near_stream==0)).sum()),
            median_outside_distance_m=float(np.median([row['distance_to_hq100_m'] for row in rows if not row['inside_hq100_center']])) if outside_count else None))
        classes=np.zeros(original.shape,dtype='uint8')
        classes[~rectangle]=255
        classes[rectangle&~np.isfinite(score)]=254
        classes[r,c]=group+1
        pr=ref.copy();pr.update(driver='GTiff',count=1,dtype='uint8',nodata=255,compress='deflate')
        short={'Original 34%':'original_34','Completed 34%':'completed_34','Completed 80%':'completed_80'}[name]
        with rasterio.open(out/f'{short}_distance_classes.tif','w',**pr) as dst:
            dst.write(classes,1)
            dst.update_tags(claim_level='diagnostic_only',threshold='PIM >= 0.6',
                            classes='0=not high;1-6=LABELS order;254=score NoData;255=outside rectangle',
                            labels=json.dumps(LABELS,ensure_ascii=False))
        arrays[name]=classes
        for label,count in zip(LABELS,counts):
            summary.append(dict(scenario=name,distance_group=label,cells=int(count)))
    def table(path,rows):
        with (out/path).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    rollup=[x for x in summary if 'high_cells' in x]
    buckets=[x for x in summary if 'distance_group' in x]
    table('summary.csv',rollup)
    table('distance_buckets.csv',buckets)
    table('high_cells.csv',details)
    make_figures(out,arrays,rollup,buckets,ref,bounds,hq,stream)
    baseline=rollup[0]
    note=f'''# Distance between Abzucht high-score cells and the official HQ100

The current display rectangle, the 30 m grid and the combined-priority threshold ≥0.6 are fixed. Exact Euclidean distances are computed from high-score cell centers to the official polygon and grouped as 0/0-30/30-60/60-90/90-150/>150 m. Intersecting each cell square with the polygon identifies cells whose center falls outside HQ100 but whose edge touches it.

Original 34%: the rectangle has {baseline['high_cells']} high-score cells, {baseline['inside_hq100_high']} inside HQ100 and {baseline['outside_hq100_high']} outside. Among the outside high-score cells, {next(r['cells'] for r in buckets if r['scenario']=='Original 34%' and r['distance_group']==LABELS[1])} have their center within 30 m; the 30 m squares of {baseline['outside_cell_intersects_hq100']} cells actually touch the polygon; {baseline['outside_over_150m']} cells are more than 150 m away ({baseline['outside_over_150m_share']:.1%} of outside high-score cells). Edge rasterization therefore explains only a small part of the high scores outside HQ100.

In all three scenarios, all {baseline['hq100_center_cells']} cell centers inside HQ100 have a PIM value. The completed scenario has {rollup[1]['rectangle_cells']-rollup[1]['scored_rectangle_cells']} cells without a value in the display rectangle; they are kept as NoData in the analysis and not treated as low scores.

On the model's own extracted drainage lines (DEM flow-accumulation threshold 500), the original map has {baseline['outside_high_on_model_stream']} outside high-score cells; of the outside high-score cells more than 150 m from HQ100, {baseline['far_over_150m_on_model_stream']} fall directly on these drainage-line cells. The model score includes a drainage-proximity factor, so this alignment comes at least partly from the model's construction.

''' 
    for row in rollup[1:]:
        note+=f"- {row['scenario']}: {row['high_cells']} high-score cells; {row['inside_hq100_high']} inside HQ100, {row['outside_hq100_high']} outside; {row['outside_over_150m']} outside cells more than 150 m away.\n"
    note+='''
30/60/90 m are diagnostic distances only. The 30 m center test, the cell-edge intersection and the model drainage lines are counted separately. The flood sub-indicator and the combined PIM have different meanings; nearby high scores may also be driven by other criteria or other water systems.

To judge later whether the channel position is truly offset, bring in an independent official channel centerline or a high-accuracy aerial survey of the channel, and check the CRS, DEM and stream threshold. To validate the actual 2017 flood, obtain the event inundation extent or locatable observations separately.

Reproduce: `.venv/bin/python bin/analysis/diagnose_abzucht_spatial_offset.py`. Results: summary.csv, distance_buckets.csv, high_cells.csv, three classification rasters, PNG/SVG/PDF figures and manifest.json.
'''
    (out/'READING_NOTE.md').write_text(note)
    remember(Path(__file__))
    for name,value in inputs.items():
        if sha(ROOT/name)!=value:raise ValueError('Input changed during analysis')
    manifest=dict(boundary_id='goslar_abzucht_display_rectangle_v1',experiment_id='spatial_offset_v1',
        claim_level='diagnostic_only',command=COMMAND,threshold=THRESHOLD,reference='2026 official modelled HQ100, not observed 2017 extent',
        sampling='Exact UTM cell-centre point-to-polygon Euclidean distance; square-cell intersection sensitivity',
        comparison_extent='Existing display rectangle',stream='DEM-derived 30m stream cells at flow accumulation >500; not independent river survey',
        distance_edges_m=[0,30,60,90,150],distance_labels=LABELS,inside_is_distance_zero=True,
        source_hashes=inputs,summary=rollup,outputs={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='manifest.json'})
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    if DEST.exists():
        backup=DEST.with_name(DEST.name+'_previous_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        DEST.rename(backup)
        try:out.rename(DEST)
        except Exception:
            backup.rename(DEST)
            raise
    else:out.rename(DEST)
    print(json.dumps(rollup,ensure_ascii=False,indent=2))


def make_figures(out,arrays,summary,buckets,ref,bounds,hq,stream):
    t=ref['transform'];extent=[t.c/1000,(t.c+t.a*ref['width'])/1000,
                               (t.f+t.e*ref['height'])/1000,t.f/1000]
    hv=hq.copy();hv.geometry=hv.geometry.scale(.001,.001,origin=(0,0))
    titles=['Original weights (34% flood)','Completed inputs, 34% flood','Completed inputs, 80% flood']
    fig,axes=plt.subplots(1,3,figsize=(16,6.8))
    fig.subplots_adjust(top=.83,bottom=.28,left=.07,right=.98,wspace=.25)
    for ax,(name,classes),title in zip(axes,arrays.items(),titles):
        display=np.where((classes>=1)&(classes<=6),classes,np.nan)
        ax.imshow(np.ma.masked_invalid(display),extent=extent,origin='upper',interpolation='nearest',
                  cmap=ListedColormap(COLORS),norm=BoundaryNorm(np.arange(.5,7.5),6))
        hv.boundary.plot(ax=ax,color='#145b9b',linewidth=.85)
        ax.set(xlim=(bounds[0]/1000,bounds[2]/1000),ylim=(bounds[1]/1000,bounds[3]/1000),
               title=title,xlabel='UTM easting (km)',ylabel='UTM northing (km)')
        ax.ticklabel_format(useOffset=False,style='plain');ax.tick_params(labelsize=8)
    fig.suptitle('Goslar / Abzucht: high scores near and far from HQ100',fontsize=17)
    handles=[Patch(color=c,label=l) for c,l in zip(COLORS,LABELS)]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.065),ncol=3,fontsize=9,frameon=False)
    fig.text(.07,.185,'Blue outline: official HQ100 | Colored cells: composite score ≥ 0.6 | Same extent and 30 m grid',fontsize=10)
    fig.text(.07,.03,'Distance is from cell centre to HQ100; categories show proximity, not flood prediction accuracy.',fontsize=9)
    for ext in ['png','svg','pdf']:fig.savefig(out/f'distance_maps.{ext}',dpi=180)
    plt.close(fig)
    names=list(arrays)
    counts=np.array([[next(r['cells'] for r in buckets if r['scenario']==name and r['distance_group']==label)
                      for label in LABELS] for name in names])
    fig,ax=plt.subplots(figsize=(11,5.7));fig.subplots_adjust(left=.12,right=.96,top=.77,bottom=.24)
    x=np.arange(len(names));bottom=np.zeros(len(names))
    for j,(label,color) in enumerate(zip(LABELS,COLORS)):
        values=counts[:,j]
        ax.bar(x,values,bottom=bottom,color=color,label=label,width=.62)
        bottom+=values
    ax.set(xticks=x,xticklabels=titles,ylabel='High-scoring 30 m cells')
    fig.suptitle('High-score distance from the official HQ100 zone',fontsize=16)
    fig.legend(*ax.get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.5,.055),ncol=3,fontsize=9,frameon=False)
    fig.text(.08,.01,'Identical 0.6 threshold | Different input/weight scenarios change total high-cell counts',fontsize=9)
    for ext in ['png','svg','pdf']:fig.savefig(out/f'distance_counts.{ext}',dpi=180)
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,6.4))
    fig.subplots_adjust(top=.82,bottom=.19,left=.08,right=.98,wspace=.18)
    for ax,name,title in zip(axes,['Original 34%','Completed 80%'],
                             ['Original weights (34% flood)','Completed inputs, 80% flood']):
        classes=arrays[name]
        stream_image=np.where(stream,1.0,np.nan)
        ax.imshow(np.ma.masked_invalid(stream_image),extent=extent,origin='upper',
                  interpolation='nearest',cmap=ListedColormap(['#c5c8ce']),vmin=.5,vmax=1.5)
        far=classes==6
        on_stream=np.where(far&stream,1.0,np.nan)
        off_stream=np.where(far&~stream,1.0,np.nan)
        ax.imshow(np.ma.masked_invalid(on_stream),extent=extent,origin='upper',
                  interpolation='nearest',cmap=ListedColormap(['#d36c36']),vmin=.5,vmax=1.5)
        ax.imshow(np.ma.masked_invalid(off_stream),extent=extent,origin='upper',
                  interpolation='nearest',cmap=ListedColormap(['#873d85']),vmin=.5,vmax=1.5)
        hv.boundary.plot(ax=ax,color='#145b9b',linewidth=.85)
        ax.set(xlim=(bounds[0]/1000,bounds[2]/1000),ylim=(bounds[1]/1000,bounds[3]/1000),
               title=title,xlabel='UTM easting (km)',ylabel='UTM northing (km)')
        ax.ticklabel_format(useOffset=False,style='plain');ax.tick_params(labelsize=8)
    fig.suptitle('Far high scores and model-derived drainage',fontsize=16)
    fig.legend(handles=[Patch(color='#d36c36',label='>150 m from HQ100, on model stream'),
                        Patch(color='#873d85',label='>150 m from HQ100, off model stream'),
                        Patch(color='#c5c8ce',label='DEM-derived drainage cells')],
               loc='lower center',bbox_to_anchor=(.5,.055),ncol=3,fontsize=9,frameon=False)
    fig.text(.08,.015,'Drainage proximity contributes to the score; this DEM-derived alignment is not independent validation.',fontsize=9)
    for ext in ['png','svg','pdf']:fig.savefig(out/f'far_high_stream_context.{ext}',dpi=180)
    plt.close(fig)


if __name__=='__main__':main()
