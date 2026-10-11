#!/usr/bin/env python3
"""TOOLING: bounded independent-river and score-driver check for Abzucht."""
import atexit
import csv
from datetime import datetime, timezone
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.features import geometry_mask
from scipy.spatial import cKDTree
from shapely.geometry import box
import shapely

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/goslar_abzucht_diagnostics/fixed_scale'
COMPLETE=BASE.parent/'input_completion'
DEST=BASE.parent/'river_alignment'
WFD=ROOT/'data/raw/goslar_official_hydrology_and_flood_data/WFD_RWSEG_LOCAL.zip'
LINEAGE=ROOT/'outputs/goslar_official_hydrology_and_flood_data/source_lineage.json'
PRIORITY=BASE/'chain/priority_scenarios'
WEIGHTS={'flood_hazard':.34,'sediment':.25,'landuse_asm':.17,
         'environmental':.10,'socioeconomic':.14}
FLOOD_COMPONENTS={'rainfall_climatology':.35,'twi_wetness':.25,'drainage_proximity':.40}
COMMAND='.venv/bin/python bin/analysis/check_abzucht_river_alignment.py'


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def line_samples(geometry, spacing=30., with_positions=False):
    """Sample by total line length so small clipped fragments are not overweighted."""
    def parts(value):
        if value.is_empty:return []
        if value.geom_type=='LineString':return [value] if value.length else []
        if value.geom_type in ('MultiLineString','GeometryCollection'):
            return [line for part in value.geoms for line in parts(part)]
        if value.geom_type in ('Point','MultiPoint'):return []
        raise TypeError(f'Unexpected river geometry: {value.geom_type}')
    segments=parts(geometry)
    if not segments:return []
    lengths=np.array([line.length for line in segments])
    edges=np.r_[0,np.cumsum(lengths)]
    positions=np.arange(spacing/2,edges[-1],spacing)
    result=[]
    for position in positions:
        index=min(int(np.searchsorted(edges,position,side='right')-1),len(segments)-1)
        point=segments[index].interpolate(float(position-edges[index]))
        result.append(dict(point=point,part_index=index,
                           distance_along_part_m=float(position-edges[index]),
                           cumulative_distance_m=float(position)) if with_positions else point)
    return result


def representative(indices, values, target=None):
    """Use the lower-indexed cell closest to the group's median score."""
    if len(indices)==0:raise ValueError('No cells in representative case group')
    if target is None:target=float(np.median(values[indices]))
    return int(indices[np.argmin(abs(values[indices]-target))])


def main():
    inputs={}
    def remember(path, expected=None):
        digest=sha(path)
        if expected and digest!=expected:raise ValueError(f'Source hash mismatch: {path}')
        inputs[str(path.relative_to(ROOT))]=digest
        return path
    run=json.loads(remember(PRIORITY/'run_manifest.json').read_text())
    completion=json.loads(remember(COMPLETE/'manifest.json').read_text())
    lineage=json.loads(remember(LINEAGE).read_text())
    remember(WFD,lineage['sources']['river_segments']['sha256'])
    score_path=remember(ROOT/run['priority_raster_lineage']['path'],run['priority_raster_lineage']['sha256'])
    completed_path=COMPLETE/'soil2017_hillslope/priority_fh_034.tif'
    remember(completed_path,completion['outputs'][str(completed_path.relative_to(COMPLETE))])
    hq=gpd.read_file(remember(BASE/'overlay/abzucht_hq100.gpkg'))
    bounds=json.loads(remember(BASE/'expansion_manifest.json').read_text())['display_rectangle']['bounds_utm32n']
    rectangle=box(*bounds)
    with rasterio.open(score_path) as src:
        profile=src.profile;score=src.read(1,masked=True).astype('float64').filled(np.nan)
    if str(profile['crs'])!='EPSG:32632' or profile['transform'].a!=30 or profile['transform'].e!=-30:
        raise ValueError('Expected 30 m UTM32N reference grid')
    shape=score.shape;transform=profile['transform']
    def read_aligned(path,expected=None):
        remember(path,expected)
        with rasterio.open(path) as src:
            if src.crs!=profile['crs'] or src.transform!=transform or src.shape!=shape:
                raise ValueError(f'Grid mismatch: {path}')
            return src.read(1,masked=True).astype('float64').filled(np.nan)
    completed=read_aligned(completed_path)
    criteria={}
    for name in WEIGHTS:
        rec=run['criterion_raster_lineage'][name]
        criteria[name]=read_aligned(ROOT/rec['path'],rec['sha256'])
    flood_parts={}
    for name in FLOOD_COMPONENTS:
        flood_parts[name]=read_aligned(BASE/f'chain/criteria_stack/criteria/{name}_0_1.tif')
    stream_path=BASE/'chain/hydrology_derivatives/goslar_focus_streams_t500.tif'
    remember(stream_path)
    with rasterio.open(stream_path) as src:
        if src.crs!=profile['crs'] or src.transform!=transform or src.shape!=shape:
            raise ValueError('Stream grid mismatch')
        stream=src.read(1,masked=True).filled(0)==1
    hq=hq.to_crs(profile['crs'])
    if hq.empty or not hq.is_valid.all():raise ValueError('Invalid HQ100 polygon')
    polygon=hq.geometry.union_all()
    # GeoPandas expects bbox coordinates in the archive's CRS for zipped shapefiles.
    bbox=Transformer.from_crs(profile['crs'],'EPSG:4647',always_xy=True).transform_bounds(*bounds)
    archive=f'zip://{WFD}!WFD_RWSEG_LOCAL.shp'
    lines=gpd.read_file(archive,bbox=bbox).to_crs(profile['crs'])
    lines=lines[lines.intersects(rectangle)].copy()
    names=set(lines['S_NAME'])
    if names!={'Abzucht','Oker'}:raise ValueError(f'Unexpected official river names in rectangle: {names}')
    official=lines.geometry.union_all()
    abzucht=lines.loc[lines['S_NAME']=='Abzucht','geometry'].union_all()
    feature_dates=sorted({value.date().isoformat() if hasattr(value,'date') else str(value)
                          for value in lines['Datum'].dropna()})
    plot_lines=lines.copy()
    plot_lines['geometry']=plot_lines.intersection(rectangle)
    plot_lines=plot_lines[~plot_lines.geometry.is_empty]
    target=abzucht.intersection(polygon)
    sampled=line_samples(target,with_positions=True)
    samples=[item['point'] for item in sampled]
    if not samples:raise ValueError('No Abzucht official-line samples inside HQ100')
    sr,sc=np.where(stream)
    sx,sy=rasterio.transform.xy(transform,sr,sc)
    stream_tree=cKDTree(np.column_stack((sx,sy)))
    sampled_xy=np.array([(point.x,point.y) for point in samples])
    river_to_stream,nearest_stream=stream_tree.query(sampled_xy)
    sustained_ids=np.zeros(len(sampled),dtype=int)
    runs=[];active=[]
    def finish_run():
        if len(active)>=3:
            run_id=len(runs)+1
            sustained_ids[active]=run_id
            start=sampled[active[0]];end=sampled[active[-1]]
            runs.append(dict(run_id=run_id,part_index=start['part_index'],sample_count=len(active),
                approximate_sampled_span_m=len(active)*30,
                start_easting_m=float(start['point'].x),start_northing_m=float(start['point'].y),
                end_easting_m=float(end['point'].x),end_northing_m=float(end['point'].y),
                median_nearest_model_stream_center_m=float(np.median(river_to_stream[active])),
                max_nearest_model_stream_center_m=float(np.max(river_to_stream[active]))))
        active.clear()
    for i,distance in enumerate(river_to_stream):
        if distance>30:
            if active and sampled[i]['part_index']!=sampled[active[-1]]['part_index']:
                finish_run()
            active.append(i)
        else:finish_run()
    finish_run()
    sample_rows=[dict(sample_index=i,easting_m=float(point.x),northing_m=float(point.y),
                      part_index=int(sampled[i]['part_index']),
                      distance_along_part_m=float(sampled[i]['distance_along_part_m']),
                      sustained_over_30m_run_id=int(sustained_ids[i]),
                      nearest_model_stream_cell_distance_m=float(river_to_stream[i]),
                      nearest_model_stream_row=int(sr[nearest_stream[i]]),
                      nearest_model_stream_col=int(sc[nearest_stream[i]]))
                 for i,point in enumerate(samples)]
    rect_mask=geometry_mask([rectangle],out_shape=shape,transform=transform,invert=True)
    hq_mask=geometry_mask([polygon],out_shape=shape,transform=transform,invert=True)
    high=rect_mask&np.isfinite(score)&(score>=.6)
    rr,cc=np.where(high)
    xx,yy=rasterio.transform.xy(transform,rr,cc)
    points=shapely.points(xx,yy)
    hq_distance=shapely.distance(points,polygon)
    official_distance=shapely.distance(points,official)
    abzucht_distance=shapely.distance(points,abzucht)
    model_distance=stream_tree.query(np.column_stack((xx,yy)))[0]
    inside=shapely.intersects(polygon,points)
    high_rows=[]
    for i in range(len(rr)):
        high_rows.append(dict(row=int(rr[i]),col=int(cc[i]),easting_m=float(xx[i]),northing_m=float(yy[i]),
            original_pim=float(score[rr[i],cc[i]]),inside_hq100=bool(inside[i]),
            distance_to_hq100_m=float(hq_distance[i]),distance_to_selected_wrrl_m=float(official_distance[i]),
            distance_to_selected_abzucht_m=float(abzucht_distance[i]),
            distance_to_model_stream_center_m=float(model_distance[i]),
            on_model_stream=bool(stream[rr[i],cc[i]])))
    far=(~inside)&(hq_distance>150)
    original_values=score[rr,cc]
    candidate_inside=np.where(hq_mask&np.isfinite(score)&(score<.6)&
                              (criteria['flood_hazard']>=.5)&np.isfinite(completed))
    ir,ic=candidate_inside
    if not len(ir):raise ValueError('No inside-low/high-flood case')
    flood_values=criteria['flood_hazard'][ir,ic]
    high_flood=flood_values>=np.quantile(flood_values,.75)
    cand=np.where(high_flood)[0]
    chosen_inside=representative(cand,flood_values)
    case_indices=[('A — inside HQ100, low PIM despite high flood indicator',int(ir[chosen_inside]),int(ic[chosen_inside]))]
    near=np.where((~inside)&(hq_distance>0)&(hq_distance<=30)&np.isfinite(completed[rr,cc]))[0]
    j=representative(near,original_values)
    case_indices.append(('B — high PIM just outside HQ100',int(rr[j]),int(cc[j])))
    remote=np.where(far&(official_distance>90)&(model_distance==0)&np.isfinite(completed[rr,cc]))[0]
    j=representative(remote,original_values)
    case_indices.append(('C — far high PIM on model stream, away from mapped WRRL lines',int(rr[j]),int(cc[j])))
    cases=[]
    for label,r,c in case_indices:
        px,py=rasterio.transform.xy(transform,r,c)
        pt=shapely.Point(px,py)
        contributions={name:float(weight*criteria[name][r,c]) for name,weight in WEIGHTS.items()}
        reconstructed=sum(contributions.values())
        if abs(reconstructed-score[r,c])>2e-6:raise ValueError(f'PIM contribution mismatch at {label}')
        flood_reconstructed=sum(weight*flood_parts[name][r,c] for name,weight in FLOOD_COMPONENTS.items())
        if abs(flood_reconstructed-criteria['flood_hazard'][r,c])>2e-6:
            raise ValueError(f'Flood component mismatch at {label}')
        row=dict(case=label,row=r,col=c,easting_m=float(px),northing_m=float(py),
            inside_hq100=bool(polygon.intersects(pt)),distance_to_hq100_m=float(pt.distance(polygon)),
            distance_to_selected_wrrl_m=float(pt.distance(official)),
            distance_to_model_stream_center_m=float(stream_tree.query([px,py])[0]),
            original_pim=float(score[r,c]),completed_34_pim=float(completed[r,c]),
            original_flood_indicator=float(criteria['flood_hazard'][r,c]),
            dominant_contribution=max(contributions,key=contributions.get),
            rainfall_component=float(flood_parts['rainfall_climatology'][r,c]),
            twi_component=float(flood_parts['twi_wetness'][r,c]),
            drainage_component=float(flood_parts['drainage_proximity'][r,c]))
        row.update({f'original_{name}_contribution':value for name,value in contributions.items()})
        cases.append(row)
    summary=dict(claim_level='diagnostic_only',reference='Official WRRL river segments; Abzucht HQ100 model scenario',
        model_stream='Nearest DEM-derived t500 stream cell centre, not one-to-one Abzucht channel alignment; t500 drainage participates in scoring',
        wrrl_rivers=sorted(names),wrrl_selected_feature_dates=feature_dates,
        official_abzucht_length_in_hq100_m=float(target.length),
        official_abzucht_samples_30m=len(samples),
        official_abzucht_to_model_stream_center_median_m=float(np.median(river_to_stream)),
        official_abzucht_to_model_stream_center_p90_m=float(np.percentile(river_to_stream,90)),
        official_abzucht_samples_within_30m=int((river_to_stream<=30).sum()),
        official_abzucht_samples_within_60m=int((river_to_stream<=60).sum()),
        sustained_over_30m_runs_at_least_3_samples=len(runs),
        longest_sustained_run_approx_m=max((row['approximate_sampled_span_m'] for row in runs),default=0),
        original_high_cells_in_rectangle=len(rr),original_high_outside_hq100=int((~inside).sum()),
        original_high_farther_than_150m=int(far.sum()),
        far_high_within_60m_of_wrrl=int((far&(official_distance<=60)).sum()),
        far_high_over_90m_from_wrrl=int((far&(official_distance>90)).sum()),
        far_high_on_model_stream=int((far&(model_distance==0)).sum()),
        hq100_center_cells=int(hq_mask.sum()),
        original_scored_hq100_center_cells=int((hq_mask&np.isfinite(score)).sum()),
        completed_scored_hq100_center_cells=int((hq_mask&np.isfinite(completed)).sum()))
    out=Path(tempfile.mkdtemp(prefix='.river_alignment_v1_incomplete_',dir=DEST.parent))
    atexit.register(shutil.rmtree,out,ignore_errors=True)
    def csv_write(name,rows):
        with (out/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    csv_write('official_abzucht_30m_samples.csv',sample_rows)
    if runs:csv_write('sustained_stream_gap_runs.csv',runs)
    csv_write('original_high_cells.csv',high_rows)
    csv_write('three_cases.csv',cases)
    brief=[dict(case=chr(65+i),easting_m=round(row['easting_m'],1),northing_m=round(row['northing_m'],1),
        inside_hq100=row['inside_hq100'],distance_to_hq100_m=round(row['distance_to_hq100_m'],1),
        distance_to_selected_wrrl_m=round(row['distance_to_selected_wrrl_m'],1),
        original_pim=round(row['original_pim'],3),completed_34_pim=round(row['completed_34_pim'],3),
        original_flood_indicator=round(row['original_flood_indicator'],3),
        original_flood_contribution=round(row['original_flood_hazard_contribution'],3),
        original_other_four_contribution=round(row['original_pim']-row['original_flood_hazard_contribution'],3))
        for i,row in enumerate(cases)]
    csv_write('three_cases_brief.csv',brief)
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    figure(out,profile,rectangle,polygon,plot_lines,stream,rr,cc,hq_distance,cases,sample_rows)
    note=f'''# Abzucht channel position and high-score cell diagnosis

Same 30 m EPSG:32632 grid, original 34% flood weight, PIM ≥0.6 threshold and existing display rectangle. The official WRRL network uses the locally archived Abzucht/Oker reaches (selected feature dates: {', '.join(feature_dates)}). It is independent of the model DEM stream network.

Within HQ100 the official Abzucht line is about {summary['official_abzucht_length_in_hq100_m']/1000:.2f} km long; {len(samples)} points were sampled at equal 30 m spacing along its total length. The distance to the **nearest center of any model drainage-line cell** has a median of {summary['official_abzucht_to_model_stream_center_median_m']:.1f} m and a 90th percentile of {summary['official_abzucht_to_model_stream_center_p90_m']:.1f} m; {summary['official_abzucht_samples_within_30m']}/{len(samples)} are ≤30 m and {summary['official_abzucht_samples_within_60m']}/{len(samples)} are ≤60 m. In addition, {len(runs)} runs of at least 3 consecutive sample points lie >30 m from the nearest model drainage cell center; the longest is about {summary['longest_sustained_run_approx_m']:.0f} m. Their locations are shown as red dots on the map and in `sustained_stream_gap_runs.csv`. These values measure stream-network proximity, not a one-to-one offset of the main Abzucht channel: the nearest point may belong to a model tributary, and the distance also includes 30 m grid positioning and generalization differences in the official network.

The original map has {summary['original_high_farther_than_150m']} high-score cells outside HQ100 and more than 150 m from its boundary. Of these, {summary['far_high_within_60m_of_wrrl']} are ≤60 m from the selected official WRRL lines and {summary['far_high_over_90m_from_wrrl']} are >90 m from both selected official lines. Distances use the full geometry of the selected reaches, and only the plot is clipped to the display rectangle, so points near the edge do not get inflated distances from plot clipping. The WRRL data cover only the water-body reaches selected here. Of the distant high-score cells, {summary['far_high_on_model_stream']} lie on model drainage-line cells; drainage proximity is already part of the score.

The three cases were selected automatically by pre-stated filtering rules. A: among HQ100 cells with flood indicator ≥0.5 and original PIM <0.6, take the top flood-indicator quartile and choose the cell closest to that group's median flood indicator. B: among original high-score cells 0–30 m outside HQ100, choose the cell closest to the group's median original PIM. C: among original high-score cells >150 m outside HQ100 that lie on a model drainage line and >90 m from the official lines, choose the cell closest to the group's median original PIM. Ties are broken by row/column order.

| Case | HQ100 position | Original PIM | Completed 34% PIM | Flood indicator | Weighted flood contribution | Other four combined | Distance to selected official line |
|---|---|---:|---:|---:|---:|---:|---:|
| A | inside | {brief[0]['original_pim']:.3f} | {brief[0]['completed_34_pim']:.3f} | {brief[0]['original_flood_indicator']:.3f} | {brief[0]['original_flood_contribution']:.3f} | {brief[0]['original_other_four_contribution']:.3f} | {brief[0]['distance_to_selected_wrrl_m']:.1f} m |
| B | outside {brief[1]['distance_to_hq100_m']:.1f} m | {brief[1]['original_pim']:.3f} | {brief[1]['completed_34_pim']:.3f} | {brief[1]['original_flood_indicator']:.3f} | {brief[1]['original_flood_contribution']:.3f} | {brief[1]['original_other_four_contribution']:.3f} | {brief[1]['distance_to_selected_wrrl_m']:.1f} m |
| C | outside {brief[2]['distance_to_hq100_m']:.1f} m | {brief[2]['original_pim']:.3f} | {brief[2]['completed_34_pim']:.3f} | {brief[2]['original_flood_indicator']:.3f} | {brief[2]['original_flood_contribution']:.3f} | {brief[2]['original_other_four_contribution']:.3f} | {brief[2]['distance_to_selected_wrrl_m']:.1f} m |

The original TWI and drainage-proximity components of all three cells have already reached 1.0, so their high flood indicator is linked to these saturated values. The cells illustrate how individual scores are built.

The case table lists the original PIM, the original flood indicator, the weighted contributions of the original five criteria, and the PIM with a 34% flood weight after input completion. Scores and contributions are all read from the original rasters and checked by reconstruction. The completed PIM serves only as a sensitivity comparison; some of its criterion inputs have been replaced, so the difference between the two reflects both input and weight changes.

Next-step decisions: if the flood indicator is low inside the local blue outline and the model stream line stays far from the official line, check the DEM, the flow-accumulation threshold and the stream positioning first. If the flood indicator is high but the combined score is low, discuss the combined criterion contributions. If distant red cells are far from the two large WRRL rivers, confirm small channels with finer independent watercourse data or imagery.

Reproduce: `{COMMAND}`. Outputs: equally spaced points along the line, sustained stream-network gaps, distances from all original high-score cells to the selected official lines, the three cases, a summary, maps and a hash manifest.
'''
    (out/'READING_NOTE.md').write_text(note)
    remember(Path(__file__))
    for name,digest in inputs.items():
        if sha(ROOT/name)!=digest:raise ValueError(f'Input changed during analysis: {name}')
    manifest=dict(boundary_id='goslar_abzucht_display_rectangle',experiment_id='river_alignment',
        claim_level='diagnostic_only',command=COMMAND,method='WRRL line sampled every 30m by total length within HQ100; Euclidean distance to nearest DEM t500 raster cell centre; original PIM high cells compared to full geometries of selected WRRL segments',
        scenario='Original fixed 34% flood PIM; completed 34% shown only as sensitivity context',
        source_hashes=inputs,outputs={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='manifest.json'})
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    if DEST.exists():
        previous=DEST.with_name(DEST.name+'_previous_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        DEST.rename(previous)
        try:out.rename(DEST)
        except Exception:
            previous.rename(DEST)
            raise
    else:out.rename(DEST)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


def figure(out,profile,rectangle,polygon,lines,stream,rr,cc,hq_distance,cases,sample_rows):
    t=profile['transform']
    extent=[t.c/1000,(t.c+t.a*profile['width'])/1000,
            (t.f+t.e*profile['height'])/1000,t.f/1000]
    fig,axes=plt.subplots(1,2,figsize=(14,7))
    fig.subplots_adjust(left=.08,right=.98,top=.83,bottom=.17,wspace=.17)
    for ax in axes:
        image=np.where(stream,1.,np.nan)
        ax.imshow(np.ma.masked_invalid(image),extent=extent,origin='upper',
                  cmap=matplotlib.colors.ListedColormap(['#d4d8dc']),vmin=.5,vmax=1.5,
                  interpolation='nearest')
        geom=gpd.GeoSeries([polygon],crs=profile['crs']).scale(.001,.001,origin=(0,0))
        geom.boundary.plot(ax=ax,color='#0b9bcc',linewidth=1.3,linestyle='--')
        for name,color in [('Abzucht','#1b2028'),('Oker','#28804b')]:
            subset=lines[lines.S_NAME==name].copy()
            subset.geometry=subset.geometry.scale(.001,.001,origin=(0,0))
            subset.plot(ax=ax,color=color,linewidth=1.6)
        x,y=rasterio.transform.xy(t,rr,cc)
        x=np.asarray(x)/1000;y=np.asarray(y)/1000
        inside=hq_distance==0;near=(hq_distance>0)&(hq_distance<=30)
        middle=(hq_distance>30)&(hq_distance<=150);far=hq_distance>150
        ax.scatter(x[inside],y[inside],s=10,c='#248d81',marker='s',linewidths=0,zorder=5)
        ax.scatter(x[near],y[near],s=10,c='#e28b37',marker='s',linewidths=0,zorder=5)
        ax.scatter(x[middle],y[middle],s=10,c='#d3ad62',marker='s',linewidths=0,zorder=5)
        ax.scatter(x[far],y[far],s=9,c='#a73774',marker='s',linewidths=0,zorder=5)
        marked=[row for row in sample_rows if row['sustained_over_30m_run_id']]
        ax.scatter([row['easting_m']/1000 for row in marked],
                   [row['northing_m']/1000 for row in marked],s=7,c='#e23e38',
                   marker='o',linewidths=0,zorder=7)
        for i,case in enumerate(cases,1):
            px=case['easting_m']/1000;py=case['northing_m']/1000
            ax.scatter([px],[py],s=112,facecolors='white',edgecolors='black',linewidths=1.4,zorder=8)
            ax.text(px,py,str(i),ha='center',va='center',fontsize=8,fontweight='bold',zorder=9)
        ax.ticklabel_format(useOffset=False,style='plain');ax.tick_params(labelsize=8)
        ax.set(xlabel='UTM easting (km)',ylabel='UTM northing (km)')
    bounds=rectangle.bounds
    axes[0].set(xlim=(bounds[0]/1000,bounds[2]/1000),ylim=(bounds[1]/1000,bounds[3]/1000),title='Full comparison rectangle')
    cx=(cases[0]['easting_m']+cases[1]['easting_m'])/2000
    cy=(cases[0]['northing_m']+cases[1]['northing_m'])/2000
    axes[1].set(xlim=(cx-.6,cx+.6),ylim=(cy-.4,cy+.4),
                title='Close-up near cases 1 and 2')
    fig.suptitle('Abzucht: official river versus model drainage and high scores',fontsize=16)
    fig.text(.08,.085,'Cyan dashed: HQ100  |  Black: WRRL Abzucht  |  Green: WRRL Oker  |  Gray: DEM drainage  |  Red dots: sustained >30 m gap',fontsize=9)
    fig.text(.08,.045,'High PIM: teal inside  |  orange 0–30 m outside  |  gold 30–150 m outside  |  magenta >150 m outside  |  1–3: cases',fontsize=9)
    fig.text(.08,.013,'Gap means distance to any model stream cell, not one-to-one channel offset or 2017 flood evidence.',fontsize=9)
    for ext in ('png','svg','pdf'):fig.savefig(out/f'river_alignment_map.{ext}',dpi=180)
    plt.close(fig)


if __name__=='__main__':main()
