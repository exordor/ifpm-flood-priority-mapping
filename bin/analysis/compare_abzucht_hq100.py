#!/usr/bin/env python3
"""Local, fixed-weight HQ100 comparison. TOOLING; outputs are diagnostic_only."""
from pathlib import Path
import csv
import json
import sys
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import box
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'bin'))
from _lib.goslar_comparison import COLORS, LABELS, digest, read_grid, summarize  # noqa: E402
OUT = ROOT / 'outputs/goslar_wrrl_basin/abzucht_hq100_overlay'
MANIFEST = ROOT / 'outputs/goslar_pim_chain/priority_scenarios/run_manifest.json'
VECTOR = ROOT / 'data/validation/goslar_2017_regulatory_flood_context/nlwkn_current_regulatory_flood_zones_goslar.geojson'
COMMAND = '.venv/bin/python bin/analysis/compare_abzucht_hq100.py'

def main():
    m = json.loads(MANIFEST.read_text())
    pim_path = ROOT / m['priority_raster_lineage']['path']
    if digest(pim_path) != m['priority_raster_lineage']['sha256']:
        raise ValueError('PIM hash differs from run manifest')
    pim, profile = read_grid(pim_path)
    valid = np.isfinite(pim)
    if np.any((pim[valid] < 0) | (pim[valid] > 1)):
        raise ValueError('PIM outside [0,1]')
    vectors = gpd.read_file(VECTOR)
    vectors = vectors[vectors.uesg_id == 917].to_crs(profile['crs'])
    if len(vectors) != 1 or not vectors.is_valid.all():
        raise ValueError('Expected one valid Abzucht polygon')
    geom = vectors.geometry.union_all()
    grid_box = box(*rasterio.transform.array_bounds(profile['height'], profile['width'], profile['transform']))
    if geom.difference(grid_box).area > .01:
        raise ValueError('Flood polygon extends outside raster rectangle; coverage denominator needs expansion')
    def mask(g, touched=False):
        return geometry_mask([g], out_shape=pim.shape, transform=profile['transform'], invert=True, all_touched=touched)
    inside = mask(geom)
    ring = mask(geom.buffer(1000)) & ~inside
    zones = {'HQ100 polygon': inside, 'Outside polygon, within 1 km': ring, 'Full valid project': valid}
    stats = {name: summarize(pim, zone) for name, zone in zones.items()}
    boundary_path = ROOT / m['input_lineage']['boundary']['path']
    boundary = gpd.read_file(boundary_path).to_crs(profile['crs'])
    intersection = geom.intersection(boundary.geometry.union_all())
    weights = m['main_weights']
    contributions, inputs = [], [MANIFEST, VECTOR, pim_path, boundary_path]
    for key, weight in weights.items():
        item = m['criterion_raster_lineage'][key]
        path = ROOT / item['path']
        if digest(path) != item['sha256']:
            raise ValueError(f'Criterion hash differs: {key}')
        arr, _ = read_grid(path, profile)
        if not np.isfinite(arr[valid]).all():
            raise ValueError(f'Missing criterion on PIM support: {key}')
        contributions.append(arr * weight)
        inputs.append(path)
    contributions = np.stack(contributions)
    max_error = float(np.max(np.abs(contributions.sum(axis=0)[valid] - pim[valid])))
    if max_error > 1e-5:
        raise ValueError('Contributions do not reconstruct PIM')
    OUT.mkdir(parents=True, exist_ok=True)
    report = {
        'boundary_id': m['focus_area_id'], 'experiment_id': 'abzucht_hq100_overlay',
        'claim_level': 'diagnostic_only', 'evidence': '2026 HQ100 modelled regulatory scenario, local August snapshot',
        'enters_pim_score': False, 'weights_changed': False, 'event_accuracy': False,
        'command': COMMAND,
        'class_edges': [0, .2, .4, .6, .8, 1], 'high_definition': 'PIM >= 0.6; existing five equal-interval class boundaries',
        'sampling': 'Cell center inclusion; descriptive comparison, no significance test; ring is geographic context, not matched control',
        'coverage': {'polygon_area_km2': geom.area/1e6, 'area_inside_boundary_km2': intersection.area/1e6,
                     'fraction_inside_boundary': intersection.area/geom.area,
                     'inside_cells': int(inside.sum()), 'valid_inside_cells': int((inside & valid).sum()),
                     'nodata_inside_cells': int((inside & ~valid).sum())},
        'statistics': stats,
        'all_touched_sensitivity': summarize(pim, mask(geom, True)),
        'weights': weights, 'contribution_max_reconstruction_error': max_error,
        'inputs': {str(p.relative_to(ROOT)): digest(p) for p in inputs + [Path(__file__)]},
        'limits': ['NoData excluded from score summaries', 'HQ100 polygon is not observed flood extent',
                   'PIM integrates multiple criteria and is not inundation probability',
                   'Flood scenario and project indicators may share terrain or river information'],
    }
    with (OUT/'comparison.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['zone','valid_cells','mean_pim','median_pim','share_pim_ge_0_6','0_0.2','0.2_0.4','0.4_0.6','0.6_0.8','0.8_1'])
        for name,s in stats.items(): writer.writerow([name,s['valid_cells'],s['mean'],s['median'],s['high_share'],*s['class_counts']])
    means = {}
    with (OUT/'criterion_contributions.csv').open('w',newline='') as f:
        writer = csv.writer(f); writer.writerow(['criterion','weight','mean_contribution_hq100','mean_contribution_1km_ring'])
        for i,(key,w) in enumerate(weights.items()):
            vals = [float(contributions[i][zone & valid].mean()) for zone in [inside,ring]]
            means[key] = vals
            writer.writerow([key,w,*vals])
    report['mean_contributions'] = means
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    # Explicit categories: zero is a valid outside-polygon category, 255 is unused NoData.
    categories = np.zeros(pim.shape,dtype='uint8')
    categories[inside & ~valid] = 1
    categories[inside & valid & (pim < .6)] = 2
    categories[inside & valid & (pim >= .6)] = 3
    raster_profile = profile.copy(); raster_profile.update(dtype='uint8',nodata=255,count=1,compress='deflate')
    with rasterio.open(OUT/'hq100_comparison_categories.tif','w',**raster_profile) as dst:
        dst.write(categories,1)
        dst.update_tags(claim_level='diagnostic_only',categories='0=outside HQ100;1=HQ100 without PIM;2=HQ100 PIM<0.6;3=HQ100 PIM>=0.6')
    # GeoPackage remains a copy, leaving source geometry untouched.
    gpkg = OUT/'abzucht_hq100.gpkg'
    vectors.to_file(gpkg,layer='abzucht_hq100',driver='GPKG',mode='w')
    fig = plt.figure(figsize=(16,9),facecolor='white')
    gs = fig.add_gridspec(2,3,height_ratios=[3.4,1.3],left=.14,right=.97,top=.85,bottom=.20,wspace=.65,hspace=.48)
    ax1=fig.add_subplot(gs[0,:2]); ax2=fig.add_subplot(gs[0,2]); ax3=fig.add_subplot(gs[1,:2]); ax4=fig.add_subplot(gs[1,2])
    t=profile['transform']; extent=[t.c/1000,(t.c+t.a*profile['width'])/1000,(t.f+t.e*profile['height'])/1000,t.f/1000]
    plotvec=vectors.copy(); plotvec.geometry=plotvec.geometry.scale(xfact=.001,yfact=.001,origin=(0,0))
    plotbound=boundary.copy(); plotbound.geometry=plotbound.geometry.scale(xfact=.001,yfact=.001,origin=(0,0))
    xmin,ymin,xmax,ymax=geom.bounds
    for ax in [ax1,ax2]:
        ax.set_facecolor('#eef0f3'); ax.set_xlim(xmin/1000-.5,xmax/1000+.5); ax.set_ylim(ymin/1000-.5,ymax/1000+.5)
        ax.set_aspect('equal'); ax.tick_params(labelsize=8); ax.set_xlabel('UTM easting (km)',fontsize=9)
    img=ax1.imshow(np.ma.masked_invalid(pim),extent=extent,origin='upper',cmap=ListedColormap(COLORS),norm=BoundaryNorm([0,.2,.4,.6,.8,1.000001],5),interpolation='nearest')
    plotvec.boundary.plot(ax=ax1,color='#0656a0',linewidth=1.3)
    plotbound.boundary.plot(ax=ax1,color='#444444',linewidth=.7,linestyle='--')
    ax1.set_ylabel('UTM northing (km)',fontsize=9); ax1.set_title('Goslar / Abzucht: official HQ100 outline over current priority',loc='left',fontsize=12)
    ax1.legend(handles=[Line2D([0],[0],color='#0656a0',label='Official HQ100'),Line2D([0],[0],color='#444444',ls='--',label='Project boundary'),Patch(color='#eef0f3',label='No PIM data')],loc='lower right',fontsize=8)
    ax2.imshow(np.ma.masked_where(categories==0,categories),extent=extent,origin='upper',cmap=ListedColormap(['#8d96a4','#eac36b','#d54436']),norm=BoundaryNorm([.5,1.5,2.5,3.5],3),interpolation='nearest')
    plotvec.boundary.plot(ax=ax2,color='#0656a0',linewidth=.5)
    ax2.set_title('Coverage inside HQ100',loc='left',fontsize=12)
    ax2.legend(handles=[Patch(color=c,label=l) for c,l in [('#8d96a4','No PIM data'),('#eac36b','PIM < 0.6'),('#d54436','PIM >= 0.6')]],loc='lower right',fontsize=8)
    class_names=['0-.2','.2-.4','.4-.6','.6-.8','.8-1']
    bottom=np.zeros(3)
    for k,color in enumerate(COLORS):
        widths=np.array([100*s['class_counts'][k]/s['valid_cells'] for s in stats.values()])
        ax3.barh(np.arange(3),widths,left=bottom,color=color,label=class_names[k],edgecolor='white');bottom+=widths
    ax3.set_yticks(range(3),['Inside HQ100','Outside, within 1 km','Full valid project']);ax3.invert_yaxis();ax3.set_xlim(0,100)
    ax3.set_xlabel('Share of valid pixels (%)',fontsize=10);ax3.set_title('Priority distribution (NoData excluded)',loc='left',fontsize=12)
    ax3.legend(ncol=5,fontsize=8,loc='upper center',bbox_to_anchor=(.5,-.38),frameon=False,title='PIM score')
    a=np.array(list(means.values())); y=np.arange(5)
    ax4.barh(y-.17,a[:,0],height=.32,color='#0656a0',label='HQ100');ax4.barh(y+.17,a[:,1],height=.32,color='#a6b7c9',label='1 km ring')
    ax4.set_yticks(y,[LABELS[k] for k in weights],fontsize=8);ax4.invert_yaxis()
    ax4.set_xlabel('Mean weighted contribution',fontsize=9);ax4.set_title('What contributes to the score?',loc='left',fontsize=11)
    ax4.legend(fontsize=8,loc='lower right')
    si=stats['HQ100 polygon'];sr=stats['Outside polygon, within 1 km']
    fig.suptitle(f"Covered HQ100 area: mean priority {si['mean']:.2f} versus {sr['mean']:.2f} nearby",x=.045,ha='left',fontsize=21,fontweight='bold',y=.97)
    subtitle = (f'{100*intersection.area/geom.area:.0f}% of the official polygon lies inside the project boundary. Grey areas have no PIM result.' if intersection.area/geom.area < .999 else 'The full official polygon is now covered. Composite scores can still contain gaps in underlying inputs.')
    fig.text(.045,.91,subtitle,fontsize=12)
    fig.text(.045,.025,'Prototype scenario comparison | NLWKN HQ100 (2026; local snapshot) | Existing 30 m PIM and weights | Not observed-event accuracy',fontsize=10,color='#444444')
    for fmt in ['png','svg']:fig.savefig(OUT/f'abzucht_hq100_comparison.{fmt}',dpi=180)
    plt.close(fig)
    print(json.dumps({'coverage':report['coverage'],'stats':stats,'contributions':means},indent=2))

if __name__ == '__main__': main()
