#!/usr/bin/env python3
"""TOOLING: multi-river descriptive comparison of immutable original model outputs."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import sys

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import box, Point
from shapely.ops import unary_union
from shapely import make_valid
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from compare_abzucht_hq100 import read_grid, summarize, COLORS
from explain_abzucht_comparison import representative

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/goslar_abzucht_diagnostics/fixed_scale'
OUT=BASE.parent/'multiriver_comparison'
RAW=ROOT/'data/validation/goslar_multiriver_regulatory'
LOCAL=ROOT/'data/validation/goslar_2017_regulatory_flood_context/nlwkn_current_regulatory_flood_zones_goslar.geojson'
HWRM=ROOT/'outputs/goslar_official_hydrology_and_flood_data/goslar_hwrm_flood_hazard_boundaries_12km.gpkg'
ANNOUNCEMENTS={'Abzucht':'2026-04-01','Grane':None,'Oker':'2017-05-02','Innerste':'2017-05-02','Radau':'2021-01-27','Ecker':'2015-05-13','Schamlah':'2014-09-03','Wedde':'2015-04-15'}
IDS={917:'Abzucht',842:'Grane',793:'Oker',792:'Innerste',844:'Radau',691:'Ecker',632:'Schamlah',686:'Wedde'}
WEB='https://www.goslar.de/wirtschafts-und-zukunftsort/klima-umwelt-gewaesserschutz/gewaesserschutz/ueberschwemmungsgebiete-innerhalb-der-stadt-goslar'


def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def lineage_entries(value):
    if isinstance(value,dict):
        if 'path' in value and 'sha256' in value:yield value
        else:
            for child in value.values():yield from lineage_entries(child)
    elif isinstance(value,list):
        for child in value:yield from lineage_entries(child)


def union_polygons(geometries):
    values=[g for g in geometries if g is not None and not g.is_empty]
    if any(not g.is_valid or g.geom_type not in ('Polygon','MultiPolygon') for g in values):
        raise ValueError('Invalid or non-polygon source; repair requires explicit lineage')
    return unary_union(values)


def raster_mask(geometry, ref, touched=False):
    shape=(ref['height'],ref['width'])
    if geometry.is_empty:return np.zeros(shape,dtype=bool)
    return geometry_mask([geometry],out_shape=shape,transform=ref['transform'],invert=True,all_touched=touched)


def clean_ring(geometry, radius, exclusion):
    return geometry.buffer(radius).difference(geometry).difference(exclusion)


def stats(array, zone):
    result=summarize(array,zone)
    return {k:v for k,v in result.items() if k!='class_counts'}


def date_value(value):
    if value is None or value!=value:return None
    return datetime.fromtimestamp(float(value)/1000,timezone.utc).date().isoformat()


def write_csv(path, rows):
    if not rows:raise ValueError('No rows for '+str(path))
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def main():
    inputs={}
    def remember(path):
        inputs[str(path.relative_to(ROOT))]=sha(path);return path
    def read(path,ref=None):return read_grid(remember(path),ref)
    manifest=json.loads(remember(BASE/'chain/priority_scenarios/run_manifest.json').read_text())
    # Verify parent lineage and preserve all original raster files.
    for entry in lineage_entries([manifest['priority_raster_lineage'],manifest['criterion_raster_lineage'],manifest['input_lineage']]):
        if sha(ROOT/entry['path'])!=entry['sha256']:raise ValueError('Baseline lineage mismatch')
        remember(ROOT/entry['path'])
    pim,ref=read(ROOT/manifest['priority_raster_lineage']['path'])
    if str(ref['crs'])!='EPSG:32632' or ref['transform'].a!=30 or ref['transform'].e!=-30:
        raise ValueError('Expected original 30 m UTM32N reference')
    criteria={k:read(ROOT/v['path'],ref)[0] for k,v in manifest['criterion_raster_lineage'].items()}
    flood=criteria['flood_hazard'];valid=np.isfinite(pim)&np.isfinite(flood)
    boundary=gpd.read_file(remember(BASE/'expanded_boundary.gpkg')).to_crs(ref['crs']).geometry.union_all()
    components={}
    for ws in manifest['component_weights'].values():
        for k in ws:
            if k=='water_wetland_context':p='environmental_sensitivity/water_wetland_context_0_1.tif'
            elif k=='protected_ecological_context':p='environmental_sensitivity/protected_area_context_0_1.tif'
            elif k=='settlement_population':p='exposure_indicators/population_exposure_0_1.tif'
            elif k=='critical_infrastructure':p='exposure_indicators/built_infrastructure_exposure_0_1.tif'
            else:p=f'criteria_stack/criteria/{k}_0_1.tif'
            components[k]=read(BASE/'chain'/p,ref)[0]
    acquisition=json.loads(remember(RAW/'source_manifest.json').read_text())
    new_path=remember(RAW/'regulatory_features.geojson')
    if sha(new_path)!=acquisition['combined_sha256']:raise ValueError('Acquisition checksum mismatch')
    for source in acquisition['sources']:
        if sha(remember(ROOT/source['file']))!=source['sha256']:raise ValueError('Raw source checksum mismatch')
    if sha(LOCAL)!='150f20d34b35063f15dc27ffbe5155092c38928c1c53e5968f211df62a57c369':raise ValueError('Original regulatory snapshot changed')
    sources=[(remember(LOCAL),'2026-08-20'),(new_path, '2026-09-14')]
    products=[]
    for path,snapshot in sources:
        frame=gpd.read_file(path).to_crs(ref['crs'])
        for source_id,group in frame.groupby('uesg_id'):
            source_id=int(source_id)
            if source_id not in IDS:continue
            river=IDS[source_id];row=group.iloc[0]
            versions={date_value(x) for x in group.von_datum}
            if len(versions)!=1:raise ValueError('Multiple effective dates in one regulatory id')
            layer=40 if source_id in [792,793] else 39
            products.append(dict(product_id=f'regulatory_{river.lower()}_{source_id}',river=river,family='regulatory',scenario='regulatory_extent',
                                 source_id=str(source_id),announcement_date=ANNOUNCEMENTS[river],effective_date=next(iter(versions)),
                                 snapshot=snapshot,source_path=str(path.relative_to(ROOT)),source_url=f'https://www.umweltkarten-niedersachsen.de/arcgis/rest/services/HWSchutz_wms/MapServer/{layer}',
                                 source_scope='Full selected regulatory feature; may extend beyond city/model boundary',feature_count=len(group),
                                 geometry=union_polygons(group.geometry)))
    if len({p['river'] for p in products})!=len(products):raise ValueError('Duplicate primary river product')
    missing=[r for r in ANNOUNCEMENTS if r not in {p['river'] for p in products}]
    h=gpd.read_file(remember(HWRM)).to_crs(ref['crs'])
    repairs=[]
    for idx,g in h.geometry.items():
        if not g.is_valid:
            fixed=make_valid(g)
            if fixed.geom_type=='GeometryCollection':fixed=union_polygons(x for x in fixed.geoms if x.geom_type in ('Polygon','MultiPolygon'))
            repairs.append(dict(source_row=int(idx),river=h.loc[idx,'RiverName'],scenario=h.loc[idx,'ReturnPeri'],method='shapely.make_valid; polygon parts only',area_before_m2=g.area,area_after_m2=fixed.area))
            h.loc[idx,'geometry']=fixed
    if set(h.MapType)!= {'FloodPlain'}:raise ValueError('Expected flood extent features only')
    for (river,period,archive),group in h.groupby(['RiverName','ReturnPeri','source_archive']):
        if river not in ['Oker','Innerste']:continue
        products.append(dict(product_id=f'hwrm_{river.lower()}_{period.lower()}',river=river,family='hydraulic_scenario',scenario=period,
                             source_id=archive,announcement_date=None,effective_date=None,snapshot='2026-08-17',
                             source_path=str(HWRM.relative_to(ROOT)),source_url=f'https://www.umweltkarten-niedersachsen.de/Download_OE/HWRM-RL/Daten/{archive}',
                             source_scope='Union of retained local context features; not a complete river/city extent',feature_count=len(group),
                             geometry=union_polygons(group.geometry)))
    # Union is used ONLY to exclude other official scenarios from geographic rings;
    # each target polygon, version and return period remains a separate comparison.
    exclusion=union_polygons(p['geometry'] for p in products)
    OUT.mkdir(parents=True,exist_ok=True)
    gpd.GeoDataFrame(products,geometry='geometry',crs=ref['crs']).to_file(OUT/'comparison_boundaries.gpkg',layer='products',driver='GPKG')
    gpd.GeoDataFrame({'role':['ring_exclusion_only']},geometry=[exclusion],crs=ref['crs']).to_file(OUT/'comparison_boundaries.gpkg',layer='ring_exclusion',driver='GPKG')
    inventory=[];results=[];coverage=[];cases=[];case_geo=[];map_items=[];errors={};drivers=[]
    for product in products:
        geometry=product['geometry'];pid=product['product_id']
        center=raster_mask(geometry,ref);touched=raster_mask(geometry,ref,True)
        area=geometry.area;overlap=geometry.intersection(boundary).area
        n=int((center&valid).sum());nt=int((touched&valid).sum())
        status='compared' if n else ('edge_only' if nt else 'no_model_coverage')
        inv={k:v for k,v in product.items() if k!='geometry'}
        inv.update(status=status,source_area_km2=area/1e6,inside_boundary_km2=overlap/1e6,
                   boundary_coverage_fraction=min(1.,overlap/area) if area else None,center_cells_in_grid=int(center.sum()),center_valid_cells=n,
                   center_nodata_cells_in_grid=int((center&~valid).sum()),all_touched_valid_cells=nt)
        inventory.append(inv)
        for inclusion in ['center','all_touched']:
            inside=raster_mask(geometry,ref,inclusion=='all_touched')
            for radius in [500,1000,2000]:
                ring_geometry=clean_ring(geometry,radius,exclusion)
                ring=raster_mask(ring_geometry,ref,inclusion=='all_touched')
                # Rasterisation can reintroduce edge contacts: remove every excluded
                # flood cell using the same inclusion rule, and the target cells.
                ring &= ~raster_mask(exclusion,ref,inclusion=='all_touched') & ~inside
                for zone,zone_mask in [('inside',inside),('ring',ring)]:
                    supported=zone_mask&valid
                    rowbase=dict(product_id=pid,river=product['river'],family=product['family'],scenario=product['scenario'],
                                 inclusion=inclusion,radius_m=radius,zone=zone,grid_cells=int(zone_mask.sum()),paired_valid_cells=int(supported.sum()),
                                 nodata_cells_in_grid=int((zone_mask&~valid).sum()),
                                 zone_vector_area_km2=(geometry if zone=='inside' else ring_geometry).area/1e6,
                                 zone_inside_boundary_km2=(geometry if zone=='inside' else ring_geometry).intersection(boundary).area/1e6)
                    for metric,array in [('Flood indicator',flood),('PIM',pim)]:
                        results.append({**rowbase,'metric':metric,**stats(array,supported)})
                    if inclusion=='center' and radius==1000:
                        for key,array in criteria.items():
                            mean=float(array[supported].mean()) if supported.any() else None
                            drivers.append(dict(product_id=pid,zone=zone,criterion=key,cells=int(supported.sum()),mean_score=mean,weight=manifest['main_weights'][key],mean_contribution=mean*manifest['main_weights'][key] if mean is not None else None))
                        for key,array in components.items():
                            coverage.append(dict(product_id=pid,zone=zone,component=key,total_cells=int(supported.sum()),valid_cells=int((supported&np.isfinite(array)).sum())))
        if n or nt:
            focused=geometry.intersection(boundary)
            limits=focused.buffer(500).bounds
            map_items.append((pid,product['river']+' | '+('Regulatory flood zone' if product['family']=='regulatory' else product['scenario']),[product],limits))
        clean1=raster_mask(clean_ring(geometry,1000,exclusion),ref)&~raster_mask(exclusion,ref)&~center&valid
        for group,candidate in [('C',center&valid&(pim>=.6)),('A',center&valid&(pim<.6)),('B',clean1&(pim>=.6))]:
            if not candidate.any():continue
            r,c=representative(candidate,pim);x,y=rasterio.transform.xy(ref['transform'],r,c)
            contribution={k:float(v[r,c]*manifest['main_weights'][k]) for k,v in criteria.items()}
            if abs(sum(contribution.values())-pim[r,c])>1e-5:raise ValueError('Contribution reconstruction mismatch')
            missing_components=[k for k,a in components.items() if not np.isfinite(a[r,c])]
            entry=dict(product_id=pid,river=product['river'],scenario=product['scenario'],group=group,candidate_cells=int(candidate.sum()),
                       row=int(r),col=int(c),easting=float(x),northing=float(y),pim=float(pim[r,c]),flood_indicator=float(flood[r,c]),
                       missing_components=missing_components,contributions=contribution)
            cases.append(entry)
            case_geo.append({**{k:v for k,v in entry.items() if k not in ['missing_components','contributions']},
                             'missing_components':','.join(missing_components),**{'contribution_'+k:v for k,v in contribution.items()},'geometry':Point(x,y)})
    for river in missing:
        row={k:None for k in inventory[0]};row.update(river=river,family='regulatory',scenario='regulatory_extent',announcement_date=ANNOUNCEMENTS[river],status='missing_spatial_data')
        inventory.append(row)
    abz=next(p for p in products if p['river']=='Abzucht' and p['family']=='regulatory')
    am=raster_mask(abz['geometry'],ref)&valid
    if am.sum()!=561 or ((pim>=.6)&am).sum()!=34 or abs(pim[am].mean()-.4697896121551221)>1e-6:
        raise ValueError('Abzucht frozen baseline regression failed')
    # Verify actual component-to-criterion reconstruction on existing support.
    for k,weights in manifest['component_weights'].items():
        num=np.zeros(pim.shape);den=np.zeros(pim.shape)
        for component,w in weights.items():
            a=components[component];finite=np.isfinite(a);num+=np.where(finite,a*w,0);den+=finite*w
        reconstructed=np.divide(num,den,out=np.full(pim.shape,np.nan),where=den>0)
        errors[k]=float(np.max(np.abs(reconstructed[valid]-criteria[k][valid])))
        if errors[k]>1e-5:raise ValueError('Component reconstruction failed: '+k)
    write_csv(OUT/'river_inventory.csv',inventory);write_csv(OUT/'statistics.csv',results);write_csv(OUT/'component_coverage.csv',coverage)
    (OUT/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    if case_geo:gpd.GeoDataFrame(case_geo,geometry='geometry',crs=ref['crs']).to_file(OUT/'comparison_boundaries.gpkg',layer='cases',driver='GPKG')
    primary=[p for p in products if p['family']=='regulatory']
    make_map(OUT/'00_regulatory_overview','Goslar | Regulatory flood zones',primary,boundary.bounds,flood,pim,ref)
    for pid,title,selected,limits in map_items:
        make_map(OUT/pid,title,selected,limits,flood,pim,ref)
    write_csv(OUT/'criterion_contributions.csv',drivers)
    report(OUT,inventory,results,cases,drivers)
    remember(Path(__file__));remember(Path(__file__).with_name('compare_abzucht_hq100.py'));remember(Path(__file__).with_name('explain_abzucht_comparison.py'))
    for path,digest in inputs.items():
        if sha(ROOT/path)!=digest:raise ValueError('Input changed during comparison: '+path)
    outmanifest=dict(boundary_id='goslar_abzucht_display_rectangle',experiment_id='multiriver_comparison',claim_level='diagnostic_only',
                     command='.venv/bin/python bin/analysis/compare_goslar_multiriver.py',scores_changed=False,weights_changed=False,ghsl_used=False,
                     reference_grid=dict(crs=str(ref['crs']),shape=list(pim.shape),transform=list(ref['transform'])),
                     ring_policy='500/1000/2000 m; exclude union of ALL acquired regulatory and hydraulic scenario footprints, including alternative scenarios of the same river; same raster inclusion rule; paired finite PIM/FH support',
                     case_selection='Nearest group median PIM; tie nearest candidate centroid. B uses cleaned 1 km ring, not map rectangle. Empty groups omitted.',
                     coverage_denominator='Full retained product geometry, not total river length or full city; vector boundary-area fraction separate from raster valid-cell counts',
                     acquisition=acquisition,geometry_repairs=repairs,webpage=WEB,component_reconstruction_errors=errors,abzucht_regression=dict(cells=561,high_cells=34,mean=float(pim[am].mean())),
                     inputs=inputs,products=len(products),figures=1+len(map_items),
                     outputs={p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json' and not p.name.startswith('qa_')})
    (OUT/'manifest.json').write_text(json.dumps(outmanifest,indent=2)+'\n')
    print(json.dumps([{'river':r['river'],'family':r['family'],'scenario':r['scenario'],'cells':r['center_valid_cells'],'coverage':r['boundary_coverage_fraction'],'status':r['status']} for r in inventory],indent=2))


def make_map(path,title,products,limits,flood,pim,ref):
    t=ref['transform'];extent=[t.c/1000,(t.c+t.a*ref['width'])/1000,(t.f+t.e*ref['height'])/1000,t.f/1000]
    fig,axes=plt.subplots(1,2,figsize=(13,7));fig.subplots_adjust(left=.075,right=.965,top=.87,bottom=.17,wspace=.22)
    cmap=ListedColormap(COLORS);cmap.set_bad('#f0f0f0');norm=BoundaryNorm([0,.2,.4,.6,.8,1.000001],5)
    for ax,array,label in zip(axes,[flood,pim],['Flood-conditioning indicator','Composite priority (PIM)']):
        im=ax.imshow(np.ma.masked_invalid(array),extent=extent,origin='upper',cmap=cmap,norm=norm,interpolation='nearest')
        for p in products:
            gs=gpd.GeoSeries([p['geometry']],crs=ref['crs']).scale(.001,.001,origin=(0,0))
            gs.boundary.plot(ax=ax,color='#005da8',linewidth=.8)
        ax.set_facecolor('#f0f0f0')
        ax.set_xlim(limits[0]/1000,limits[2]/1000);ax.set_ylim(limits[1]/1000,limits[3]/1000);ax.set_aspect('equal')
        ax.set_title(label,fontsize=12,loc='left');ax.set_xlabel('UTM easting (km)');ax.set_ylabel('UTM northing (km)');ax.ticklabel_format(useOffset=False,style='plain');ax.tick_params(labelsize=8)
        span=(limits[2]-limits[0])/1000;length=next((v for v in [5,2,1,.5,.2,.1] if v<span/4),.05)
        x=limits[0]/1000+.06*span;y=limits[1]/1000+.06*(limits[3]-limits[1])/1000
        ax.plot([x,x+length],[y,y],color='black',linewidth=2);ax.text(x+length/2,y,f'{length:g} km',ha='center',va='bottom',fontsize=8,bbox=dict(facecolor='white',edgecolor='none',alpha=.8,pad=1))
    fig.suptitle(title,fontsize=19,y=.965)
    cb=fig.add_axes([.33,.10,.36,.024]);fig.colorbar(im,cax=cb,orientation='horizontal',ticks=[0,.2,.4,.6,.8,1])
    fig.legend(handles=[Line2D([0],[0],color='#005da8',label='Official flood-zone boundary'),Patch(facecolor='#f0f0f0',label='No model score')],loc='lower center',bbox_to_anchor=(.51,.012),ncol=2,frameon=False,fontsize=10)
    for fmt in ['png','svg']:fig.savefig(path.with_suffix('.'+fmt),dpi=180)
    plt.close(fig)


def report(out,inventory,rows,cases,drivers):
    def get(pid,metric,zone,radius=1000,inclusion='center'):
        return next(r for r in rows if r['product_id']==pid and r['metric']==metric and r['zone']==zone and r['radius_m']==radius and r['inclusion']==inclusion)
    def number(x):return '—' if x is None else f'{x:.3f}'
    text='# Multi-river comparison results\n\nSuperseded by goslar_multiriver_full_extent.\n\nThis round compares only areas already covered by the original model. Announcement dates are not flood-event dates. In the main maps, the left panel shows the flood sub-indicator and the right panel the composite PIM; original inputs, weights, scales and thresholds are all kept unchanged. Interpretation is given outside the figures.\n\n'
    text+='Official designated extents are labelled regulatory_extent; not every regulatory layer is automatically treated as a feature-by-feature verified HQ100. The existing Abzucht HQ100 comparison basis is retained; the supplementary HWRM data use an explicit return-period field. Two self-intersecting Oker HQ20 geometries were repaired with make_valid; the area changes are recorded in manifest.json, and the original data were not modified.\n\n## Results by river\n\n| River/source | Valid cells | Source-area coverage | Flood indicator inside/outside | PIM inside/outside | Share PIM≥0.6 (inside) |\n|---|---:|---:|---|---|---:|\n'
    summary=[]
    for inv in inventory:
        pid=inv['product_id'];label=f"{inv['river']} / {inv['family']} / {inv['scenario']}"
        if pid is None:
            text+=f'| {label} | — | — | missing spatial data | — | — |\n';continue
        fi=get(pid,'Flood indicator','inside');fo=get(pid,'Flood indicator','ring');pi=get(pid,'PIM','inside');po=get(pid,'PIM','ring')
        share='—' if pi['high_share'] is None else f"{100*pi['high_share']:.2f}%"
        text+=f"| {label} | {pi['valid_cells']} | {100*inv['boundary_coverage_fraction']:.2f}% | {number(fi['mean'])}/{number(fo['mean'])} | {number(pi['mean'])}/{number(po['mean'])} | {share} |\n"
        summary.append(dict(product_id=pid,river=inv['river'],family=inv['family'],scenario=inv['scenario'],status=inv['status'],
                            inside_cells=pi['valid_cells'],ring_cells=po['valid_cells'],boundary_coverage_fraction=inv['boundary_coverage_fraction'],
                            flood_inside_mean=fi['mean'],flood_ring_mean=fo['mean'],pim_inside_mean=pi['mean'],pim_ring_mean=po['mean'],
                            pim_inside_high_share=pi['high_share']))
    text+='\n"Outside" means the 1 km ring left after removing all acquired official flood areas, restricted to the valid model extent. The removed areas include the extents of other return periods of the same river; they are used only to exclude cells from the reference ring, and target flood scenarios are not merged. Coverage uses the retained source polygon area as the denominator; it is not coverage of the whole river. Detailed medians, sample sizes, NoData counts and ring areas are in statistics.csv.\n\n## Robustness and interpretation\n\n'
    for inv in inventory:
        pid=inv['product_id']
        if not pid or not inv['center_valid_cells']:continue
        findings=[]
        for metric in ['Flood indicator','PIM']:
            differences=[]
            for radius in [500,1000,2000]:
                for inclusion in ['center','all_touched']:
                    i=get(pid,metric,'inside',radius,inclusion);r=get(pid,metric,'ring',radius,inclusion)
                    if i['mean'] is not None and r['mean'] is not None:differences.append(i['mean']-r['mean'])
            if differences:
                direction='all positive' if min(differences)>0 else ('all negative' if max(differences)<0 else 'direction varies with settings')
                findings.append(f'{metric} inside-minus-outside mean difference {min(differences):.3f} to {max(differences):.3f}, {direction}')
        text+=f"- {inv['river']} / {inv['family']} / {inv['scenario']}: "+'; '.join(findings)+'.\n'
    text+='\nCross-river summary: for all 10 covered sources/scenarios, the inside-minus-outside mean difference of the flood sub-indicator is positive under all six settings. For the composite PIM, only Abzucht is consistently positive; Grane and Innerste are consistently negative; some Oker versions change direction depending on the setting. The flood sub-indicator has a weight of 0.34 in the PIM and the other four criteria together have 0.66, so a higher flood indicator does not guarantee a higher composite priority. For Grane, the negative difference in the erosion factor offsets the positive flood difference; Oker is additionally affected by a negative difference in the land-use pressure term; for Innerste, the erosion, land-use and socioeconomic terms together offset the flood advantage. The specific weighted differences are listed below and in criterion_contributions.csv.\n\nInnerste is covered only in a small part of its extent. The flood scenarios and the model may share terrain or river-network information.\n\n## Example cells and contributions\n\nC is a high-scoring cell inside the extent, A is a cell inside the extent below 0.6, and B is a high-scoring cell in the cleaned 1 km outside ring. In each group the cell closest to the median PIM of the group is chosen; groups with no cells are not forced.\n\n'
    names={'flood_hazard':'flood sub-indicator','sediment':'erosion factor','landuse_asm':'land-use pressure','environmental':'environmental indicator','socioeconomic':'socioeconomic indicator'}
    text+='Decomposition of the PIM inside-minus-outside mean difference over the whole comparison area (weighted contributions, not causal effects):\n\n'
    for inv in inventory:
        pid=inv['product_id']
        if not pid or not inv['center_valid_cells']:continue
        d={key:next(x['mean_contribution'] for x in drivers if x['product_id']==pid and x['zone']=='inside' and x['criterion']==key)-next(x['mean_contribution'] for x in drivers if x['product_id']==pid and x['zone']=='ring' and x['criterion']==key) for key in names if any(x['product_id']==pid and x['zone']=='ring' and x['criterion']==key and x['mean_contribution'] is not None for x in drivers)}
        text+=f"- {inv['river']} / {inv['family']} / {inv['scenario']}: "+'; '.join(f'{names[k]} {v:+.3f}' for k,v in d.items())+'.\n'
    text+='\nMissing components cause the original pipeline to use the remaining components and redistribute their weights; for example, when K and LS are missing the erosion term is supported by C alone. Cell coordinates, full contributions and missing components are in cases.json and in the cases layer of the GeoPackage.\n\nWhether the indicators should be changed in a next step should first be decided in light of cross-river consistency and the missing components.\n\nReproduce: `.venv/bin/python bin/analysis/compare_goslar_multiriver.py`. Sources, scripts and output checksums are recorded in manifest.json.\n'
    (out/'READING_NOTE.md').write_text(text)
    write_csv(out/'comparison_summary.csv',summary)


if __name__=='__main__':main()
