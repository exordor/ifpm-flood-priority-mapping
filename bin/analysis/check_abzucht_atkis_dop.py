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
    note=f'''# Abzucht 细河道与航拍复核

基于 LGLN ATKIS Basis-DLM `AX_Gewaesserachse` 小范围查询（{len(atkis)} 条线，约 {summary['atkis_axis_total_length_km']:.1f} km）及三个 DOP20 局部视图；LGLN (2026), CC BY 4.0。ATKIS 是独立于 DEM 的官方地物资料，但与旧 WRRL 的主河线几何高度相同，不能当作两份独立确认。三张DOP图**中心点**的WMS元数据日期分别为 {capture_dates}；拼接影像的其他位置可能是不同日期，只能用于较新的地物背景，不能视作2017年淹水。

217个WRRL Abzucht采样点到ATKIS任意河道轴线的中位距离 {summary['atkis_to_wfd_sample_median_m']:.2f}m、90分位 {summary['atkis_to_wfd_sample_p90_m']:.2f}m。原先标出的17段模型河网间隙中，{summary['prior_model_gap_samples']}/{summary['prior_model_gap_samples']}个采样点距ATKIS轴线≤15m。因此这些间隙不是旧WRRL独有的概化偏移；但距离到**任意**ATKIS轴线仍不能证明 Abzucht 主河道与模型线一一对应。

原始高分、HQ100外>150m的{len(far)}格：距ATKIS轴线≤30m {counts['within_30m']}格、30–60m {counts['30_to_60m']}格、60–90m {counts['60_to_90m']}格、>90m {counts['over_90m']}格。细河道资料解释了一部分远处高分与官方水系的空间贴近，但仍有大量远离所绘河道的格子。ATKIS没有记载不等于不存在地下涵洞或临时排水路径。

案例A距ATKIS河道 {summary['case_atkis_distances_m']['A']:.1f}m；案例C距 {summary['case_atkis_distances_m']['C']:.1f}m。案例C的模型流线落在铁路/建成区背景附近，当前航拍上不能单凭此点断定有无地下排水；更不能据此验证2017年洪水。三张叠加图供人工逐段核查。

本轮保持分数、权重和HQ100不变；ATKIS和DOP均不进入PIM。复现：`{COMMAND}`。逐段、逐格、案例表及哈希清单与图件同目录。
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
