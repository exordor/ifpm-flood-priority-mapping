#!/usr/bin/env python3
"""TOOLING: independent ATKIS waterways and 2025 DOP checks for Abzucht cases."""
import atexit
import csv
from datetime import date, datetime, timezone
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
from PIL import Image
from pyproj import Transformer
import rasterio
import shapely
from shapely.geometry import box

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'data/validation/abzucht_atkis_dop_context_v1'
PREV=ROOT/'outputs/goslar_abzucht_display_rectangle_v1/river_alignment_v1'
BASE=ROOT/'outputs/goslar_abzucht_display_rectangle_v1/frozen_scale_v1'
DEST=ROOT/'outputs/goslar_abzucht_display_rectangle_v1/atkis_dop_check_v1'
COMMAND='.venv/bin/python bin/analysis/check_abzucht_atkis_dop.py'


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def read_csv(path):
    with path.open(newline='') as f:return list(csv.DictReader(f))


def table(path,rows):
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def classify_far_high(distance):
    if distance<=30:return 'within_30m'
    if distance<=60:return '30_to_60m'
    if distance<=90:return '60_to_90m'
    return 'over_90m'


def main():
    inputs={}
    def remember(path,expected=None):
        digest=sha(path)
        if expected and digest!=expected:raise ValueError(f'Hash mismatch: {path}')
        inputs[str(path.relative_to(ROOT))]=digest
        return path
    manifest=json.loads(remember(SOURCE/'source_manifest.json').read_text())
    gml=remember(ROOT/manifest['wfs']['path'],manifest['wfs']['sha256'])
    align_manifest=json.loads(remember(PREV/'manifest.json').read_text())
    samples_path=remember(PREV/'official_abzucht_30m_samples.csv',align_manifest['outputs']['official_abzucht_30m_samples.csv'])
    high_path=remember(PREV/'original_high_cells.csv',align_manifest['outputs']['original_high_cells.csv'])
    cases_path=remember(PREV/'three_cases_brief.csv',align_manifest['outputs']['three_cases_brief.csv'])
    runs_path=remember(PREV/'sustained_stream_gap_runs.csv',align_manifest['outputs']['sustained_stream_gap_runs.csv'])
    original_manifest=json.loads(remember(BASE/'chain/priority_scenarios/run_manifest.json').read_text())
    original_path=remember(ROOT/original_manifest['priority_raster_lineage']['path'],
                          original_manifest['priority_raster_lineage']['sha256'])
    stream_path=remember(BASE/'chain/hydrology_derivatives/goslar_focus_streams_t500.tif')
    hq_path=remember(BASE/'overlay/abzucht_hq100.gpkg')
    atkis=gpd.read_file(gml).to_crs(32632)
    if len(atkis)!=manifest['wfs']['returned'] or set(atkis.geom_type)!={'LineString'}:
        raise ValueError('ATKIS source feature count or geometry unexpected')
    atkis_union=atkis.geometry.union_all()
    hq=gpd.read_file(hq_path).to_crs(32632)
    if hq.empty or not hq.is_valid.all():raise ValueError('HQ100 invalid')
    samples=read_csv(samples_path)
    high=read_csv(high_path)
    cases=read_csv(cases_path)
    runs=read_csv(runs_path)
    capture_dates={label:record['capture_date'] for label,record in manifest['dop']['windows'].items()}
    for label,value in capture_dates.items():
        date.fromisoformat(value)
        if manifest['dop']['windows'][label].get('capture_date_scope')!='image_center_point_only':
            raise ValueError(f'DOP center-point date scope missing: {label}')
    def add_distance(rows):
        points=shapely.points([float(r['easting_m']) for r in rows],
                              [float(r['northing_m']) for r in rows])
        distances=shapely.distance(points,atkis_union)
        return [{**row,'distance_to_atkis_axis_m':float(distance)}
                for row,distance in zip(rows,distances)]
    samples=add_distance(samples);high=add_distance(high);cases=add_distance(cases)
    gap_samples=[row for row in samples if int(row['sustained_over_30m_run_id'])>0]
    if len(gap_samples)!=sum(int(row['sample_count']) for row in runs):
        raise ValueError('Sample/run linkage mismatch')
    run_table=[]
    for row in runs:
        members=[item for item in gap_samples if int(item['sustained_over_30m_run_id'])==int(row['run_id'])]
        distances=np.array([r['distance_to_atkis_axis_m'] for r in members])
        run_table.append(dict(run_id=int(row['run_id']),sample_count=len(members),
            approximate_span_m=float(row['approximate_sampled_span_m']),
            median_to_model_stream_center_m=float(row['median_nearest_model_stream_center_m']),
            median_to_atkis_axis_m=float(np.median(distances)),
            max_to_atkis_axis_m=float(np.max(distances)),
            atkis_within_15m=int((distances<=15).sum()),
            status='mapped_axis_near_WFD_but_model_stream_over_30m'))
    far=[row for row in high if float(row['distance_to_hq100_m'])>150]
    counts={label:sum(classify_far_high(row['distance_to_atkis_axis_m'])==label for row in far)
            for label in ('within_30m','30_to_60m','60_to_90m','over_90m')}
    if sum(counts.values())!=len(far):raise ValueError('Far high bins do not partition')
    summary=dict(claim_level='diagnostic_only',atkis_features=len(atkis),
        atkis_axis_total_length_km=float(atkis.length.sum()/1000),
        atkis_to_wfd_sample_median_m=float(np.median([x['distance_to_atkis_axis_m'] for x in samples])),
        atkis_to_wfd_sample_p90_m=float(np.percentile([x['distance_to_atkis_axis_m'] for x in samples],90)),
        prior_model_gap_samples=len(gap_samples),
        prior_model_gap_samples_atkis_within_15m=sum(x['distance_to_atkis_axis_m']<=15 for x in gap_samples),
        prior_model_gap_run_count=len(run_table),
        far_high_count=len(far),far_high_atkis_distance_bins=counts,
        far_high_on_model_stream_count=sum(row['on_model_stream']=='True' for row in far),
        far_high_on_model_stream_within_30m_atkis=sum(row['on_model_stream']=='True' and row['distance_to_atkis_axis_m']<=30 for row in far),
        case_atkis_distances_m={row['case']:row['distance_to_atkis_axis_m'] for row in cases},
        dop_center_point_capture_dates=capture_dates,
        interpretation='ATKIS and WFD main Abzucht line geometries nearly coincide; not two independent positional confirmations. DOP image-center metadata does not establish mosaic-wide capture dates or 2017 inundation.')
    out=Path(tempfile.mkdtemp(prefix='.atkis_dop_check_v1_incomplete_',dir=DEST.parent))
    atexit.register(shutil.rmtree,out,ignore_errors=True)
    table(out/'sample_atkis_distances.csv',samples)
    table(out/'run_atkis_check.csv',run_table)
    table(out/'high_cell_atkis_distances.csv',high)
    table(out/'case_atkis_check.csv',cases)
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    with rasterio.open(stream_path) as src:
        if str(src.crs)!='EPSG:32632' or src.transform.a!=30:
            raise ValueError('Unexpected model stream reference grid')
        stream=src.read(1,masked=True).filled(0)==1
        stream_transform=src.transform
    for label in ('case_a','case_c','longest_gap'):
        info=manifest['dop']['windows'][label]
        path=remember(ROOT/info['path'],info['sha256'])
        image=Image.open(path).convert('RGB')
        make_overlay(out,label,image,info,atkis,hq,stream,stream_transform,high,cases)
    note=f'''# Abzucht fine-scale watercourse and aerial imagery check

Based on a small-area query of the LGLN ATKIS Basis-DLM `AX_Gewaesserachse` ({len(atkis)} lines, about {summary['atkis_axis_total_length_km']:.1f} km) and three local DOP20 views; LGLN (2026), CC BY 4.0. ATKIS is official feature data independent of the DEM, but its main-channel geometry is nearly identical to the older WRRL line, so the two cannot be treated as two independent confirmations. The WMS metadata dates for the **center points** of the three DOP images are {capture_dates}. Other parts of the mosaic may have different dates, so the imagery serves as recent feature background.

The median distance from the 217 WRRL Abzucht sample points to any ATKIS watercourse axis is {summary['atkis_to_wfd_sample_median_m']:.2f} m, and the 90th percentile is {summary['atkis_to_wfd_sample_p90_m']:.2f} m. In the 17 previously flagged model stream-network gaps, {summary['prior_model_gap_samples']}/{summary['prior_model_gap_samples']} sample points lie ≤15 m from an ATKIS axis. These gaps are therefore not a generalization offset unique to the older WRRL line.

Of the {len(far)} original high-score cells more than 150 m outside HQ100, {counts['within_30m']} cells lie ≤30 m from an ATKIS axis, {counts['30_to_60m']} cells lie 30–60 m away, {counts['60_to_90m']} cells lie 60–90 m away and {counts['over_90m']} cells lie >90 m away. The fine-scale watercourse data explain why some of the distant high scores sit close to the official water network, but many cells remain far from any mapped watercourse.

Case A is {summary['case_atkis_distances_m']['A']:.1f} m from an ATKIS watercourse; Case C is {summary['case_atkis_distances_m']['C']:.1f} m away. The model flow line at Case C runs near a railway / built-up background. The current aerial imagery alone cannot decide whether underground drainage exists at this point. The three overlay maps are provided for manual section-by-section review.

This round keeps the scores, weights and HQ100 unchanged; neither ATKIS nor DOP enters the PIM. Reproduce: `{COMMAND}`. The per-run, per-cell and case tables and the hash manifest are in the same directory as the figures.
'''
    (out/'READING_NOTE.md').write_text(note)
    remember(Path(__file__))
    for name,digest in inputs.items():
        if sha(ROOT/name)!=digest:raise ValueError(f'Input changed during analysis: {name}')
    output_manifest=dict(boundary_id='goslar_abzucht_display_rectangle_v1',experiment_id='atkis_dop_check_v1',
        claim_level='diagnostic_only',command=COMMAND,enters_pim_score=False,
        method='Point-to-nearest-ATKIS-axis Euclidean distance in EPSG32632; DOP center-point capture metadata and visual overlays only',
        source_hashes=inputs,outputs={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='manifest.json'})
    (out/'manifest.json').write_text(json.dumps(output_manifest,ensure_ascii=False,indent=2)+'\n')
    if DEST.exists():
        previous=DEST.with_name(DEST.name+'_previous_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        DEST.rename(previous)
        try:out.rename(DEST)
        except Exception:
            previous.rename(DEST)
            raise
    else:out.rename(DEST)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


def make_overlay(out,label,image,info,atkis,hq,stream,transform,high,cases):
    to_utm=Transformer.from_crs(25832,32632,always_xy=True)
    xmin,ymin,xmax,ymax=to_utm.transform_bounds(*info['bbox_25832'])
    window=box(xmin,ymin,xmax,ymax)
    fig,ax=plt.subplots(figsize=(11,8))
    fig.subplots_adjust(left=.09,right=.98,top=.90,bottom=.21)
    ax.imshow(image,extent=(xmin/1000,xmax/1000,ymin/1000,ymax/1000),origin='upper')
    water=atkis[atkis.intersects(window)].copy()
    water.geometry=water.geometry.scale(.001,.001,origin=(0,0))
    water.plot(ax=ax,color='#00e5ff',linewidth=2.0,
               path_effects=[pe.Stroke(linewidth=3.5,foreground='#152c30'),pe.Normal()])
    boundary=hq.copy();boundary.geometry=boundary.geometry.scale(.001,.001,origin=(0,0))
    boundary.boundary.plot(ax=ax,color='#ffe545',linewidth=1.8,linestyle='--',
                           path_effects=[pe.Stroke(linewidth=3,foreground='#202020'),pe.Normal()])
    rows,cols=np.where(stream)
    sx,sy=rasterio.transform.xy(transform,rows,cols)
    sx=np.asarray(sx);sy=np.asarray(sy)
    local=(sx>=xmin)&(sx<=xmax)&(sy>=ymin)&(sy<=ymax)
    ax.scatter(sx[local]/1000,sy[local]/1000,s=5,c='#fa3636',marker='s',alpha=.85,linewidths=0)
    local_high=[row for row in high if xmin<=float(row['easting_m'])<=xmax and ymin<=float(row['northing_m'])<=ymax]
    ax.scatter([float(row['easting_m'])/1000 for row in local_high],
               [float(row['northing_m'])/1000 for row in local_high],
               s=18,facecolors='none',edgecolors='#a900cf',linewidths=1.2)
    for case in cases:
        x=float(case['easting_m']);y=float(case['northing_m'])
        if not window.covers(shapely.Point(x,y)):continue
        ax.scatter([x/1000],[y/1000],s=170,facecolors='white',edgecolors='black',linewidths=1.6,zorder=9)
        ax.text(x/1000,y/1000,case['case'],ha='center',va='center',fontsize=10,fontweight='bold',zorder=10)
    ax.set(xlim=(xmin/1000,xmax/1000),ylim=(ymin/1000,ymax/1000),
           xlabel='UTM easting (km)',ylabel='UTM northing (km)')
    ax.ticklabel_format(useOffset=False,style='plain')
    titles={'case_a':'Case A: high flood indicator inside HQ100',
            'case_c':'Case C: far red cell near model drainage',
            'longest_gap':'Longest official-line / model-stream gap'}
    fig.suptitle(titles[label],fontsize=16)
    fig.text(.09,.095,'Cyan: ATKIS watercourse axis  |  Red: DEM t500 stream cells  |  Yellow dashed: HQ100  |  Purple rings: high PIM cells',fontsize=9)
    fig.text(.09,.055,f'LGLN (2026), CC BY 4.0. DOP20 center metadata: {info["capture_date"]}; mosaic dates may vary; not 2017 flood evidence.',fontsize=9)
    for ext in ('png','pdf'):fig.savefig(out/f'{label}_atkis_dop_overlay.{ext}',dpi=170)
    plt.close(fig)


if __name__=='__main__':main()
