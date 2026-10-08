#!/usr/bin/env python3
"""TOOLING: isolated boundary expansion, baseline-frozen scaling, no baseline writes."""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import sys
import numpy as np
import geopandas as gpd
import rasterio
from shapely.geometry import box
from rasterio.features import geometry_mask
from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.windows import from_bounds
from rasterio.transform import from_origin

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'bin'))
sys.path.insert(0,str(Path(__file__).parent))
from abzucht_frozen_normalization import fit, apply

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

OUT=ROOT/'outputs/goslar_abzucht_expanded_reference_v1/frozen_scale_v1'

def main():
    global OUT
    parser=argparse.ArgumentParser()
    parser.add_argument('--fill-display-rectangle',action='store_true',help='Include the HQ100 plot rectangle (polygon bounds plus 500 m on each side)')
    args=parser.parse_args()
    boundary_id='goslar_abzucht_display_rectangle_v1' if args.fill_display_rectangle else 'goslar_abzucht_expanded_reference_v1'
    OUT=ROOT/'outputs'/boundary_id/'frozen_scale_v1'
    command='.venv/bin/python bin/analysis/run_abzucht_expanded.py'+(' --fill-display-rectangle' if args.fill_display_rectangle else '')
    c=load('goslar_expanded_source',ROOT/'bin/factors/run_goslar_peru_style_chain.py')
    original_paths={k:v for k,v in vars(c).items() if isinstance(v,Path)}
    old_manifest=json.loads((c.SCENARIO_DIR/'run_manifest.json').read_text())
    baseline_inputs=[ROOT/x['path'] for x in old_manifest['criterion_raster_lineage'].values()]+[ROOT/old_manifest['priority_raster_lineage']['path'],c.BOUNDARY_GPKG]
    hashes={str(p.relative_to(ROOT)):c.sha256_file(p) for p in baseline_inputs}
    anchors={}; stage=''; index=0; mode='fit'
    def norm(data,mask=None,**kwargs):
        nonlocal index
        key=f'{stage}:{index}';index+=1
        if mode=='fit': anchors[key]=fit(data,mask,**kwargs)
        pars=anchors[key]
        return apply(data,pars,mask),pars['clip_low'],pars['clip_high']
    c.percentile_minmax=norm;c.normalize_2_98=norm
    original_write=c.write_raster
    # Reconstruct anchors on original input/grid/support without changing a file.
    def no_write(path,data,transform,crs,nodata=-9999):
        if not path.exists(): raise FileNotFoundError(f'Baseline replay target missing: {path}')
        if path.exists():
            with rasterio.open(path) as ds:
                old=ds.read(1)
                if ds.transform != transform or str(ds.crs) != str(crs) or old.shape != data.shape: raise ValueError('Baseline replay grid differs')
                old_valid=(old!=ds.nodata)&np.isfinite(old); new_valid=np.isfinite(data)&(data!=nodata)
                if not np.array_equal(old_valid,new_valid): raise ValueError(f'Baseline replay support differs: {path}')
                keep=old_valid
                if keep.any() and np.max(np.abs(old[keep]-data[keep]))>1e-5:
                    raise ValueError(f'Baseline replay differs: {path}')
    c.write_raster=no_write
    for stage in ['soilgrids_kfactor','rainfall','criteria_stack','exposure_indicators']:
        index=0;print('Capture baseline:',stage,flush=True);getattr(c,'stage_'+stage)()
    c.write_raster=original_write;mode='apply'
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'frozen_normalization.json').write_text(json.dumps(anchors,indent=2)+'\n')
    old_geom=c.load_boundary_geometry(c.METRIC_CRS)
    v=gpd.read_file(ROOT/'data/validation/goslar_2017_event_map_candidates_v1/nlwkn_current_regulatory_flood_zones_goslar.geojson').to_crs(c.METRIC_CRS)
    hq=v[v.uesg_id==917].geometry.union_all()
    geom=old_geom.union(hq.buffer(1000))
    xmin,ymin,xmax,ymax=hq.bounds
    display_rectangle=box(xmin-500,ymin-500,xmax+500,ymax+500)
    if args.fill_display_rectangle: geom=geom.union(display_rectangle)
    for key,path in original_paths.items():
        if path.is_relative_to(original_paths['OUT_BASE']):setattr(c,key,OUT/'chain'/path.relative_to(original_paths['OUT_BASE']))
        elif path.is_relative_to(original_paths['WC_DIR']):setattr(c,key,OUT/'landcover'/path.relative_to(original_paths['WC_DIR']))
    c.CLMS_BARE_SOIL=original_paths['CLMS_BARE_SOIL']  # Legacy manifest-only entry; TCD is the scored layer.
    c.FOCUS_AREA_ID=boundary_id
    c.BOUNDARY_GPKG=OUT/'expanded_boundary.gpkg';c.BOUNDARY_LAYER='expanded_boundary'
    gpd.GeoDataFrame({'boundary_id':[c.FOCUS_AREA_ID],'claim_level':['diagnostic_only']},geometry=[geom],crs=c.METRIC_CRS).to_file(c.BOUNDARY_GPKG,layer=c.BOUNDARY_LAYER,driver='GPKG')
    # Preserve baseline pixel lattice; enlarge only by whole cells.
    with rasterio.open(original_paths['DEM']) as ds: old_ref=ds.profile
    t=old_ref['transform'];minx,miny,maxx,maxy=geom.bounds
    x=t.c+math.floor((minx-t.c)/30)*30;y=t.f+math.ceil((maxy-t.f)/30)*30
    width=math.ceil((maxx-x)/30);height=math.ceil((y-miny)/30)
    ref=dict(old_ref,width=width,height=height,transform=from_origin(x,y,30,30))
    def warp(path,profile,resampling=Resampling.nearest,percent=False):
        with rasterio.open(path) as ds:
            bounds=rasterio.transform.array_bounds(profile['height'],profile['width'],profile['transform'])
            bb=transform_bounds(profile['crs'],ds.crs,*bounds,densify_pts=21)
            win=from_bounds(*bb,ds.transform).round_offsets().round_lengths()
            win=rasterio.windows.Window(win.col_off-3,win.row_off-3,win.width+6,win.height+6)
            data=ds.read(1,window=win,boundless=True,masked=True).astype('float32').filled(np.nan)
            if percent:data[(data<0)|(data>100)]=np.nan
            dst=np.full((profile['height'],profile['width']),np.nan,dtype='float32')
            reproject(data,dst,src_transform=ds.window_transform(win),src_crs=ds.crs,src_nodata=np.nan,dst_transform=profile['transform'],dst_crs=profile['crs'],dst_nodata=np.nan,resampling=resampling)
            return dst
    mask=geometry_mask([geom],out_shape=(height,width),transform=ref['transform'],invert=True)
    def write(path,arr,profile=ref):c.write_raster(path,np.where(np.isfinite(arr),arr,c.NODATA),profile['transform'],profile['crs'])
    buffer_cells=34
    bref=dict(ref,width=width+2*buffer_cells,height=height+2*buffer_cells,transform=from_origin(x-30*buffer_cells,y+30*buffer_cells,30,30))
    rawdem=c.COPERNICUS_DEM_RAW/'Copernicus_DSM_COG_10_N51_00_E010_00_DEM.tif'
    dem=warp(rawdem,bref,Resampling.bilinear)
    write(c.DEM_BUFFERED,dem,bref)
    crop=dem[buffer_cells:buffer_cells+height,buffer_cells:buffer_cells+width].copy();crop[~mask]=np.nan;write(c.DEM,crop)
    # Read WorldCover on the new reference once; nearest mapping commutes with LUTs.
    wc=warp(c.WORLDCOVER_FILE,ref)
    for lutname,path in [('WORLDCOVER_CFACTOR_LUT',c.CFACTOR),('LAND_USE_PRESSURE_LUT',c.LAND_USE_PRESSURE),('LAND_COVER_RUNOFF_LUT',c.LAND_COVER_RUNOFF),('BARE_SOIL_LOSS_LUT',c.BARE_SOIL_LOSS),('BUILT_UP_LUT',c.BUILT_UP_PRESSURE),('AGRICULTURAL_LUT',c.AGRICULTURAL_PRESSURE)]:
        a=np.full(wc.shape,np.nan,dtype='float32')
        for value,score in getattr(c,lutname).items():a[wc==value]=score
        a[~mask]=np.nan;write(path,a)
    # Reuse full local native vegetation sources, not old boundary-clipped outputs.
    tcd={yr:warp(ROOT/f'data/raw/clms_hrl_tcd_goslar_official_basin/{yr}/goslar_official_basin_tcd_{yr}_10m_mosaic.tif',ref,Resampling.average,True) for yr in [2018,2024]}
    loss=np.clip((tcd[2018]-tcd[2024])/100,0,1);loss[~mask]=np.nan;write(c.CLMS_TCD_LOSS,loss)
    # Reduced aligned WorldCover for environmental stage, retaining category NoData.
    aligned_wc=OUT/'landcover/worldcover_aligned.tif';write(aligned_wc,wc);c.WORLDCOVER_FILE=aligned_wc
    def expanded_slope():
        if not np.isfinite(dem).all(): raise ValueError('Buffered DEM gaps need explicit handling')
        gy,gx=np.gradient(dem.astype('float64'),30,30)
        sl=np.degrees(np.arctan(np.sqrt(gx*gx+gy*gy)))
        write(c.SLOPE_BUFFERED,sl,bref)
        a=sl[buffer_cells:buffer_cells+height,buffer_cells:buffer_cells+width].copy();a[~mask]=np.nan;write(c.SLOPE,a)
    c.stage_slope=expanded_slope
    for stage in ['slope','hydrology','ls_factor','soilgrids_kfactor','osm_roads','rainfall','protected_areas','criteria_stack','exposure_indicators','environmental_sensitivity','priority_scenarios']:
        index=0;print('Expanded run:',stage,flush=True);getattr(c,'stage_'+stage)()
    # Supplement legacy metadata with authoritative experimental contract.
    nm_path=c.SCENARIO_DIR/'run_manifest.json';nm=json.loads(nm_path.read_text())
    nm.update(boundary_id=c.FOCUS_AREA_ID,experiment_id='frozen_scale_v1',claim_level='diagnostic_only',focus_area_name=('Original project plus HQ100 buffer and display rectangle' if args.fill_display_rectangle else 'Original project plus HQ100 buffer')+'; comparison extent, not a catchment')
    nm['normalization']['method']='Baseline 2/98 anchors frozen; see frozen_normalization.json'
    nm['normalization']['frozen_parameters']=str((OUT/'frozen_normalization.json').relative_to(ROOT))
    nm['input_lineage'].pop('clms_bare_soil',None)
    nm_path.write_text(json.dumps(nm,indent=2)+'\n')
    with rasterio.open(c.SCENARIO_DIR/'scenarios'/c.PRIORITY_FILENAME) as ds:new=ds.read(1,masked=True).filled(np.nan)
    with rasterio.open(ROOT/old_manifest['priority_raster_lineage']['path']) as ds:
        old=np.full(new.shape,np.nan,dtype='float32');reproject(ds.read(1),old,src_transform=ds.transform,src_crs=ds.crs,src_nodata=ds.nodata,dst_transform=ref['transform'],dst_crs=ref['crs'],dst_nodata=np.nan,resampling=Resampling.nearest)
    both=np.isfinite(old)&np.isfinite(new);hmask=geometry_mask([hq],out_shape=new.shape,transform=ref['transform'],invert=True)
    report={'boundary_id':c.FOCUS_AREA_ID,'experiment_id':'frozen_scale_v1','claim_level':'diagnostic_only','command':command,'old_area_km2':old_geom.area/1e6,'expanded_area_km2':geom.area/1e6,'normalization':'baseline anchors frozen','weights_changed':False,'old_valid_cells':int(np.isfinite(old).sum()),'new_valid_cells':int(np.isfinite(new).sum()),'hq100_cells':int(hmask.sum()),'hq100_valid_old':int((hmask&np.isfinite(old)).sum()),'hq100_valid_new':int((hmask&np.isfinite(new)).sum()),'common_mean_abs_change':float(np.abs(new[both]-old[both]).mean()),'common_max_abs_change':float(np.abs(new[both]-old[both]).max()),'baseline_hashes':hashes,'limitations':['Expanded hydrology and proximity calculation can change old-area values despite frozen scales','Retains baseline within-criterion available-component averaging; inspect component coverage','Not hydrologic catchment or observed-event validation']}
    for key,path in [('soil_k',c.K_SCORED),('tcd',c.CLMS_TCD_LOSS),('population',c.EXPOSURE_DIR/'population_exposure_0_1.tif')]:
        a=c.read_band(path,ref);report[key+'_valid_cells']=int((mask&np.isfinite(a)).sum())
    report['common_changed_cells_gt_1e_5']=int((both & (np.abs(new-old)>1e-5)).sum())
    report['common_changed_cells_gt_0_01']=int((both & (np.abs(new-old)>.01)).sum())
    delta=np.where(both,new-old,np.nan);write(OUT/'old_area_score_change.tif',delta)
    report['old_hq_mean_new_score']=float(new[hmask & np.isfinite(old)].mean())
    report['added_hq_mean']=float(new[hmask & ~np.isfinite(old) & np.isfinite(new)].mean())
    support={}
    for key,path in [('soil_k',c.K_SCORED),('population',c.EXPOSURE_DIR/'population_exposure_0_1.tif'),('ls',c.LS_CAPPED),('tcd',c.CLMS_TCD_LOSS)]:
        a=c.read_band(path,ref);av=np.isfinite(a)
        write(OUT/f'{key}_availability.tif',np.where(mask,av.astype(float),np.nan))
        support[key]={'all_valid':int((av&mask).sum()),'hq100_valid':int((av&hmask).sum()),'hq100_total':int(hmask.sum()),'added_valid':int((av&mask&~np.isfinite(old)).sum())}
    report['component_support']=support
    rect_mask=geometry_mask([display_rectangle],out_shape=new.shape,transform=ref['transform'],invert=True)
    report['display_rectangle']={'bounds_utm32n':list(display_rectangle.bounds),'requested_fill':args.fill_display_rectangle,'cells':int(rect_mask.sum()),'scored_cells':int((rect_mask & np.isfinite(new)).sum())}
    if args.fill_display_rectangle and not np.isfinite(new[rect_mask]).all(): raise ValueError('Display rectangle still has unscored cells; inspect component coverage')
    if args.fill_display_rectangle:
        rows,cols=np.where(rect_mask)
        window=rasterio.windows.Window.from_slices((rows.min(),rows.max()+1),(cols.min(),cols.max()+1))
        arr=new[rows.min():rows.max()+1,cols.min():cols.max()+1]
        rect_ref=dict(ref,width=arr.shape[1],height=arr.shape[0],transform=rasterio.windows.transform(window,ref['transform']))
        write(OUT/'display_rectangle_priority.tif',arr,rect_ref)
    source_files=[Path(__file__),ROOT/'bin/analysis/abzucht_frozen_normalization.py',ROOT/'bin/_lib/standardization.py',ROOT/'bin/factors/run_goslar_peru_style_chain.py',original_paths['WORLDCOVER_FILE']]
    source_files += list((c.REGNIE_RAW_DIR/'raw').glob('*.asc.gz'))
    source_files += [ROOT/f'data/raw/clms_hrl_tcd_goslar_official_basin/{yr}/goslar_official_basin_tcd_{yr}_10m_mosaic.tif' for yr in [2018,2024]]
    source_files += [OUT/'frozen_normalization.json']
    report['additional_source_hashes']={str(p.relative_to(ROOT)):c.sha256_file(p) for p in source_files}
    for name,h in hashes.items():
        if c.sha256_file(ROOT/name)!=h:raise ValueError('Baseline modified: '+name)
    (OUT/'expansion_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    # Reuse comparison implementation against the expanded manifest and output tree.
    compare=load('expanded_overlay',ROOT/'bin/analysis/compare_abzucht_hq100.py');compare.MANIFEST=nm_path;compare.OUT=OUT/'overlay';compare.COMMAND=command;compare.main()
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
