#!/usr/bin/env python3
"""TOOLING: recover published census records and diagnose remaining Abzucht gaps.

Writes only OUTPUT under the existing boundary's gap_repair directory.
Original scores, sources, weights and normalization anchors remain unchanged.
Flat-slope TWI is a numerical sensitivity scenario, never a new observation.
"""
from pathlib import Path
import sys
import csv
import hashlib
import json
import zipfile
import importlib.metadata

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling, transform_bounds
from shapely.geometry import box
from shapely.geometry import Polygon
from rasterio.warp import transform as transform_coordinates

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'bin'), str(Path(__file__).parent)]
from abzucht_fixed_scale_normalization import apply
from compare_abzucht_hq100 import read_grid

BASE = ROOT / 'outputs/goslar_abzucht_diagnostics/fixed_scale'
OUT = BASE.parent / 'gap_repair'
ARCHIVE = ROOT / 'data/tmp/zensus2022_goslar/Zensus2022_Bevoelkerungszahl.zip'
LOCAL_CSV = ROOT / 'data/raw/zensus2022_goslar_official_basin/Zensus2022_Bevoelkerungszahl_100m-Gitter_official_basin.csv'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_pinned_file(path, record):
    if path.stat().st_size != record['bytes'] or sha(path) != record['sha256']:
        raise ValueError(f'File differs from pinned acquisition manifest: {path.name}')


def finite_average(parts, weights, mask):
    numerator = np.zeros(mask.shape, dtype='float32')
    denominator = np.zeros(mask.shape, dtype='float32')
    for k, w in weights.items():
        valid = mask & np.isfinite(parts[k])
        numerator[valid] += parts[k][valid] * w
        denominator[valid] += w
    return np.divide(numerator, denominator, out=np.full(mask.shape, np.nan, 'float32'), where=denominator > 0)


def score(parts, manifest, mask):
    criteria = {k: finite_average(parts, weights, mask) for k, weights in manifest['component_weights'].items()}
    common = mask & np.all([np.isfinite(a) for a in criteria.values()], axis=0)
    pim = np.zeros(mask.shape, dtype='float32')
    for k, w in manifest['main_weights'].items():
        pim += criteria[k] * w
    return np.where(common, pim, np.nan), criteria


def regularize_flat_twi(raw, slope, sca, mask, floor_degrees):
    if not 0 < floor_degrees <= 1:
        raise ValueError('Declare a small positive slope floor, at most one degree')
    recover = mask & ~np.isfinite(raw) & (slope == 0) & np.isfinite(sca) & (sca > 0)
    result = raw.copy()
    result[recover] = np.log(sca[recover] / np.tan(np.radians(floor_degrees)))
    return result, recover


def write(path, data, ref, **tags):
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = dict(ref, driver='GTiff', count=1, dtype='float32', nodata=-9999.0, compress='deflate')
    with rasterio.open(path, 'w', **profile) as d:
        d.write(np.where(np.isfinite(data), data, -9999).astype('float32'), 1)
        d.update_tags(**tags)


def census_grid(frame, bounds):
    left = np.floor(bounds[0] / 100) * 100
    bottom = np.floor(bounds[1] / 100) * 100
    right = np.ceil(bounds[2] / 100) * 100
    top = np.ceil(bounds[3] / 100) * 100
    selected = frame[(frame.x_mp_100m >= left) & (frame.x_mp_100m < right) &
                     (frame.y_mp_100m >= bottom) & (frame.y_mp_100m < top)].copy()
    counts = pd.to_numeric(selected.Einwohner, errors='raise').to_numpy(dtype='float32')
    if not np.isfinite(counts).all() or (counts < 0).any() or selected.GITTER_ID_100m.duplicated().any():
        raise ValueError('Unexpected census counts or duplicate cells; review source coding')
    array = np.full((round((top-bottom)/100), round((right-left)/100)), np.nan, dtype='float32')
    rows = ((top-selected.y_mp_100m.to_numpy()) / 100).astype(int)
    cols = ((selected.x_mp_100m.to_numpy()-left) / 100).astype(int)
    array[rows, cols] = counts
    profile = dict(height=array.shape[0], width=array.shape[1], crs='EPSG:3035', transform=from_origin(left, top, 100, 100))
    return selected, array, profile


def warp_population(source, ref):
    """Allocate counts by overlap; verify mass against exact native intersections."""
    import shapely
    with rasterio.open(source) as ds:
        if ds.transform.b != 0 or ds.transform.d != 0 or ds.transform.a != 100 or ds.transform.e != -100:
            raise ValueError('Expected north-up native 100 m population grid')
        native = ds.read(1, masked=True).astype('float64').filled(np.nan)
        if np.any(native[np.isfinite(native)] < 0): raise ValueError('Negative population')
        destination = np.full((ref['height'], ref['width']), np.nan, dtype='float32')
        reproject(native, destination, src_transform=ds.transform, src_crs=ds.crs, src_nodata=np.nan,
                  dst_transform=ref['transform'], dst_crs=ref['crs'], dst_nodata=np.nan, resampling=Resampling.sum)
        left, bottom, right, top = rasterio.transform.array_bounds(ref['height'], ref['width'], ref['transform'])
        perimeter = [(x,top) for x in np.linspace(left,right,101)] + [(right,y) for y in np.linspace(top,bottom,101)]
        perimeter += [(x,bottom) for x in np.linspace(right,left,101)] + [(left,y) for y in np.linspace(bottom,top,101)]
        xx, yy = transform_coordinates(ref['crs'], ds.crs, *zip(*perimeter))
        footprint = Polygon(zip(xx,yy))
        rows, cols = np.where(np.isfinite(native))
        x = ds.transform.c + cols * ds.transform.a
        y = ds.transform.f + rows * ds.transform.e
        cells = shapely.box(x, y+ds.transform.e, x+ds.transform.a, y)
        fraction = shapely.area(shapely.intersection(cells, footprint)) / abs(ds.transform.a*ds.transform.e)
        expected = float(np.sum(native[rows,cols]*fraction))
        actual = float(np.nansum(destination,dtype='float64'))
        relative = abs(actual-expected)/max(expected,1)
        if relative > .005: raise ValueError(f'Population mass discrepancy exceeds 0.5%: {relative}')
        return destination, dict(expected_native_overlap_count=expected, projected_grid_count=actual,
                                 relative_error=relative, method='Sum-resample counts; reference-grid footprint intersected with native cell polygons',
                                 native_resolution=list(ds.res), native_crs=str(ds.crs), effective_resolution_m=100)


def main():
    inputs = {}
    def remember(path):
        inputs[str(path.relative_to(ROOT))] = sha(path)
        return path
    def read(path, ref=None):
        return read_grid(remember(path), ref)
    m = json.loads(remember(BASE/'chain/priority_scenarios/run_manifest.json').read_text())
    for path in [Path(__file__), ROOT/'bin/analysis/abzucht_fixed_scale_normalization.py',
                 ROOT/'bin/_lib/standardization.py', ROOT/'bin/analysis/compare_abzucht_hq100.py',
                 ROOT/'bin/acquire/pull_abzucht_ghsl_population.py']:
        remember(path)
    anchors = json.loads(remember(BASE/'frozen_normalization.json').read_text())
    expansion = json.loads(remember(BASE/'expansion_manifest.json').read_text())
    old, ref = read(ROOT/m['priority_raster_lineage']['path'])
    mask = np.isfinite(old)
    parts = {}
    for weights in m['component_weights'].values():
        for key in weights:
            if key == 'water_wetland_context': path = 'environmental_sensitivity/water_wetland_context_0_1.tif'
            elif key == 'protected_ecological_context': path = 'environmental_sensitivity/protected_area_context_0_1.tif'
            elif key == 'settlement_population': path = 'exposure_indicators/population_exposure_0_1.tif'
            elif key == 'critical_infrastructure': path = 'exposure_indicators/built_infrastructure_exposure_0_1.tif'
            else: path = f'criteria_stack/criteria/{key}_0_1.tif'
            parts[key] = read(BASE/'chain'/path, ref)[0]
    reconstructed, _ = score(parts, m, mask)
    error = float(np.max(np.abs(reconstructed[mask]-old[mask])))
    if error > 1e-6: raise ValueError(f'Baseline reconstruction mismatch {error}')
    bounds = expansion['display_rectangle']['bounds_utm32n']
    rectangle = geometry_mask([box(*bounds)], out_shape=mask.shape, transform=ref['transform'], invert=True)
    hqpath = remember(BASE/'overlay/abzucht_hq100.gpkg')
    hq = gpd.read_file(hqpath).to_crs(ref['crs']).geometry.union_all()
    hmask = geometry_mask([hq], out_shape=mask.shape, transform=ref['transform'], invert=True)
    ring = geometry_mask([hq.buffer(1000)], out_shape=mask.shape, transform=ref['transform'], invert=True) & ~hmask & mask
    zones = {'Rectangle': rectangle & mask, 'HQ100': hmask & mask, 'Full outside 1 km ring': ring, 'Whole model domain': mask}
    OUT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(remember(ARCHIVE)) as z:
        frame = pd.read_csv(z.open('Zensus2022_Bevoelkerungszahl_100m-Gitter.csv'), sep=';')
        description_hash = hashlib.sha256(z.read('Datensatzbeschreibung_Bevoelkerungszahl_Gitterzellen.xlsx')).hexdigest()
    rb = rasterio.transform.array_bounds(ref['height'], ref['width'], ref['transform'])
    cb = transform_bounds(ref['crs'], 'EPSG:3035', *rb, densify_pts=21)
    source = remember(LOCAL_CSV.parent/'goslar_official_basin_population_100m_3035.tif')
    with rasterio.open(source) as ds:
        native_bounds = ds.bounds
    if not (native_bounds.left <= cb[0] and native_bounds.bottom <= cb[1] and native_bounds.right >= cb[2] and native_bounds.top >= cb[3]):
        raise ValueError('Existing native canvas does not cover target; review extraction bounds')
    selected, pop_native, npref = census_grid(frame, native_bounds)
    local = pd.read_csv(remember(LOCAL_CSV), sep=';')
    recovered = selected[~selected.GITTER_ID_100m.isin(local.GITTER_ID_100m)]
    recovered.to_csv(OUT/'recovered_published_population_records.csv', index=False)
    selected.to_csv(OUT/'population_full_window.csv', index=False)
    write(OUT/'population_published_native_100m.tif', pop_native, npref,
          meaning='Published CKM-perturbed counts; unpublished cells remain NoData', effective_resolution='100 m')
    pop = np.full(mask.shape, np.nan, dtype='float32')
    # Match the baseline sum/NaN propagation so extraction is the sole change.
    # Do not ignore NaN source cells, which would make partial counts look complete.
    reproject(pop_native, pop, src_transform=npref['transform'], src_crs=npref['crs'],
              dst_transform=ref['transform'], dst_crs=ref['crs'], resampling=Resampling.sum)
    pop[~mask] = np.nan
    pop_std = apply(pop, anchors['exposure_indicators:0'], mask)
    # Native grid origin may enlarge by whole cells only; published existing values
    # must agree numerically before adopting any new supported cells.
    both = mask & np.isfinite(parts['settlement_population']) & np.isfinite(pop_std)
    pop_error = float(np.max(np.abs(pop_std[both]-parts['settlement_population'][both])))
    if pop_error > 1e-4: raise ValueError(f'Census replay changed existing scores: {pop_error}')
    newly = mask & ~np.isfinite(parts['settlement_population']) & np.isfinite(pop_std)
    corrected = dict(parts)
    corrected['settlement_population'] = parts['settlement_population'].copy()
    corrected['settlement_population'][newly] = pop_std[newly]
    raw_twi = read(BASE/'chain/hydrology_derivatives/goslar_focus_twi.tif', ref)[0]
    slope = read(BASE/'chain/terrain_preprocessing/goslar_focus_slope_degrees_utm32n_30m.tif', ref)[0]
    sca = read(BASE/'chain/hydrology_derivatives/goslar_focus_flow_accumulation_sca.tif', ref)[0]
    scenarios = {'baseline': parts, 'census_recovered': corrected}
    for floor in [.01, .1, 1.0]:
        twi, recovered_flat = regularize_flat_twi(raw_twi, slope, sca, mask, floor)
        candidate = dict(corrected)
        candidate['twi_wetness'] = apply(twi, anchors['criteria_stack:0'], mask)
        scenarios[f'flat_slope_{floor:g}deg'] = candidate
    ghsl_path = remember(ROOT/'data/raw/ghsl2020_abzucht_population/ghsl2020_population_native_100m.tif')
    ghsl_source_manifest = json.loads(remember(ghsl_path.parent/'source_manifest.json').read_text())
    pinned = ghsl_source_manifest['files'][ghsl_path.name]
    verify_pinned_file(ghsl_path, pinned)
    terrain_reference = BASE/'chain/terrain_preprocessing/goslar_focus_dem_utm32n_30m.tif'
    remember(terrain_reference)
    if sha(terrain_reference) != ghsl_source_manifest['reference_grid_sha256']:
        raise ValueError('GHSL acquisition used a different reference grid')
    ghsl, mass_check = warp_population(ghsl_path, ref)
    ghsl[~mask] = np.nan
    if not np.isfinite(ghsl[mask]).all(): raise ValueError('GHSL has source gaps in model domain; review before replacing')
    write(OUT/'ghsl2020_population_count_30m.tif', ghsl, ref, effective_resolution='100 m',
          meaning='Modelled 2020 population allocated to 30 m grid; not native 30 m evidence')
    ghsl_parts = dict(parts)
    ghsl_parts['settlement_population'] = apply(ghsl, anchors['exposure_indicators:0'], mask)
    scenarios['ghsl_population'] = ghsl_parts
    for floor in [.01,.1,1.0]:
        candidate = dict(ghsl_parts)
        candidate['twi_wetness'] = scenarios[f'flat_slope_{floor:g}deg']['twi_wetness']
        scenarios[f'ghsl_flat_{floor:g}deg'] = candidate
    rows, coverage, arrays = [], [], {}
    for name, components in scenarios.items():
        pim, criteria = score(components, m, mask)
        count = np.isfinite(np.stack(list(components.values()))).sum(axis=0)
        arrays[name] = (pim, count)
        for zone, zm in zones.items():
            rows.append(dict(scenario=name, zone=zone, pixels=int(zm.sum()),
                             pim_mean=float(pim[zm].mean()), flood_mean=float(criteria['flood_hazard'][zm].mean()),
                             mean_abs_change=float(np.abs(pim[zm]-old[zm]).mean()),
                             all_14_percent=float(100*np.mean(count[zm] == 14))))
            for key, a in components.items():
                coverage.append(dict(scenario=name, zone=zone, component=key, valid=int(np.isfinite(a[zm]).sum()), total=int(zm.sum())))
        if name != 'baseline':
            folder = OUT/name
            write(folder/'priority.tif', pim, ref, claim_level='diagnostic_only' if name == 'census_recovered' else 'sensitivity_scenario')
            write(folder/'component_count.tif', np.where(mask, count, np.nan), ref, meaning='Finite components, not verified observations')
            for key in ['settlement_population', 'twi_wetness']:
                write(folder/f'{key}.tif', components[key], ref)
    for filename, items in [('comparison.csv', rows), ('coverage.csv', coverage)]:
        with (OUT/filename).open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(items[0])); w.writeheader(); w.writerows(items)
    write(OUT/'published_population_recovered_mask.tif', np.where(mask, newly, np.nan), ref)
    write(OUT/'flat_slope_twi_mask.tif', np.where(mask, recovered_flat, np.nan), ref)
    manifest = dict(boundary_id='goslar_abzucht_display_rectangle', experiment_id='gap_repair',
                    claim_level='diagnostic_only', command='.venv/bin/python bin/analysis/repair_abzucht_gaps.py',
                    main_weights=m['main_weights'], component_weights=m['component_weights'], weights_changed=False,
                    normalization='Original anchors frozen', inputs=inputs, baseline_reconstruction_error=error,
                    census_replay_max_error=pop_error, recovered_csv_records=len(recovered),
                    recovered_population_pixels={k:int((newly & zm).sum()) for k,zm in zones.items()},
                    flat_twi_pixels={k:int((recovered_flat & zm).sum()) for k,zm in zones.items()},
                    census_description_sha256=description_hash,
                    runtime={k:importlib.metadata.version(k) for k in ['numpy','rasterio','shapely','pandas','geopandas','matplotlib']},
                    gdal_version=rasterio.__gdal_version__,
                    ghsl_source_manifest=ghsl_source_manifest, population_mass_check=mass_check,
                    population_replacement='Entire component uses GHSL2020 modelled population; not a mosaic with Zensus2022; frozen count-per-target-cell anchors',
                    census_omissions='Not published, not proven zero: CKM and unallocated addresses are possible',
                    twi_method='Only missing zero-slope cells: ln(specific contributing area / tan(candidate slope)); floor 0.01/0.1/1 degrees',
                    unfilled=['SoilGrids K source gaps; tested LBEG services did not expose a compatible numeric replacement',
                              'Hillslope LS channel exclusion retained', 'Unpublished census records remain missing'], statistics=rows)
    for name, digest in inputs.items():
        if sha(ROOT/name) != digest: raise ValueError(f'Input mutated: {name}')
    make_figures(arrays, rows, coverage, rectangle & mask, bounds, hq, ref)
    census_note = 'Rechecking the national population CSV found 937 additional records outside the old clipping extent; these records add no valid cells inside the current model domain. The original population gaps are retained.'
    note = f'''# Abzucht gap handling results

The added population estimate raises the share of the display rectangle with all 14 components complete from 5.78% to 59.77%. This is a sensitivity scenario based on replacement data and numerical treatment; the original results were not overwritten.

- Population: the original Zensus2022 covered 26.05%; the GHSL2020 modeled population covers 100%. The whole layer was replaced; the two years were not mixed. The 100 m population counts were distributed to the 30 m grid by area, so the effective resolution is still 100 m.
- Wetness TWI: the 67 originally missing cells all have zero slope; only these cells were computed with three small candidate slopes of 0.01°, 0.1° and 1°. The 0.1° variant is shown; all results are in comparison.csv.
- Soil K: coverage remains 61.44%. The existing SoilGrids data cover the geographic extent, but the source data have missing values; the LBEG interfaces checked returned no usable numeric values.
- Hillslope LS: coverage remains 96.57%; the original workflow deliberately excludes channels, which stay not applicable/missing.

{census_note}

Mean combined PIM: rectangle 0.425→0.397; inside HQ100 0.470→0.445; full outer 1 km ring 0.419→0.390. The population replacement did not change the flood sub-indicator, and the flat-terrain treatment has very little effect on the overall flood sub-indicator. The drop in scores comes from differences in population source and year and in how component weights were redistributed where components were originally missing. The main weights, component weights, normalization anchors and classification thresholds are all unchanged.

Relative error of the population-allocation conservation check: {mass_check['relative_error']*100:.5f}%; maximum baseline reconstruction error: {error:.3g}. Input and output hashes are in manifest.json.

Figures: coverage_before_after.png; population_replacement_comparison.png.
QGIS rasters: ghsl_flat_0.1deg/priority.tif; ghsl_flat_0.1deg/component_count.tif. The original population scenario can continue to use the original project; the new scenario must be loaded separately.

Reproduce:
```
.venv/bin/python bin/acquire/pull_abzucht_ghsl_population.py
.venv/bin/python bin/analysis/repair_abzucht_gaps.py
.venv/bin/python -m unittest discover -s tests -p 'test_abzucht*.py'
```

Sources:
- GHSL product: https://data.jrc.ec.europa.eu/dataset/2ff68a52-5b5b-4a22-8f40-c41da8332cfe
- Census notes: Datensatzbeschreibung_Bevoelkerungszahl_Gitterzellen.xlsx in the original ZIP, Version2 (2024-09-30).
- SoilGrids mask: https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html
- LBEG test: BK50KFAKTOR, https://nibis.lbeg.de/net3/public/ikxcms/?pgid=2603 ; the WMS layer L2131 of PkgId24 returned only coverage metadata; WFS is not configured.
'''
    (OUT/'READING_NOTE.md').write_text(note)
    manifest['outputs'] = {str(p.relative_to(OUT)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({k:manifest[k] for k in ['recovered_csv_records','recovered_population_pixels','flat_twi_pixels','census_replay_max_error']},indent=2))


def make_figures(arrays, rows, coverage, rectangle, bounds, hq, ref):
    """One claim: population replacement expands support but soil/channel gaps remain."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, BoundaryNorm
    from compare_abzucht_hq100 import COLORS
    old = arrays['baseline'][0]
    new, count = arrays['ghsl_flat_0.1deg']
    t = ref['transform']
    extent = [t.c/1000,(t.c+t.a*ref['width'])/1000,(t.f+t.e*ref['height'])/1000,t.f/1000]
    outline = gpd.GeoSeries([hq],crs=ref['crs']).scale(.001,.001,origin=(0,0))
    fig, axes = plt.subplots(1,3,figsize=(15,6.1))
    fig.subplots_adjust(left=.06,right=.97,top=.78,bottom=.22,wspace=.25)
    delta = new-old
    norm = BoundaryNorm([0,.2,.4,.6,.8,1.000001],5)
    for i,(a,title) in enumerate([(old,'Original: census population'),(new,'GHSL population + flat-slope scenario'),(delta,'Change in composite priority')]):
        im = axes[i].imshow(np.ma.masked_invalid(a),extent=extent,origin='upper',interpolation='nearest',
                            cmap=ListedColormap(COLORS) if i<2 else 'RdBu_r',norm=norm if i<2 else None,
                            **({} if i<2 else dict(vmin=-.15,vmax=.15)))
        outline.boundary.plot(ax=axes[i],color='#005da8',linewidth=.7)
        axes[i].set_xlim(bounds[0]/1000,bounds[2]/1000);axes[i].set_ylim(bounds[1]/1000,bounds[3]/1000)
        axes[i].set_title(title,fontsize=11,loc='left');axes[i].set_xlabel('UTM easting (km)')
        axes[i].tick_params(labelsize=8);axes[i].ticklabel_format(useOffset=False,style='plain')
        cb = fig.colorbar(im,ax=axes[i],orientation='horizontal',fraction=.04,pad=.18)
        cb.ax.tick_params(labelsize=8)
    axes[0].set_ylabel('UTM northing (km)')
    fig.suptitle('Goslar / Abzucht: more complete population estimates',fontsize=20,y=.97)
    oldfull = next(r['all_14_percent'] for r in rows if r['scenario']=='baseline' and r['zone']=='Rectangle')
    newfull = next(r['all_14_percent'] for r in rows if r['scenario']=='ghsl_flat_0.1deg' and r['zone']=='Rectangle')
    fig.text(.06,.86,f'All 14 components available: {oldfull:.1f}% → {newfull:.1f}% | Remaining soil and channel gaps stay visible in coverage results',fontsize=11)
    fig.text(.06,.075,'Sensitivity scenario: modelled 2020 population replaces 2022 census; zero-slope TWI uses 0.1° | Weights and scaling unchanged',fontsize=10)
    fig.text(.06,.035,'Blue: official HQ100 outline | Counts have 100 m effective resolution | Finite values do not establish accuracy',fontsize=10)
    for fmt in ['png','svg']:fig.savefig(OUT/f'population_replacement_comparison.{fmt}',dpi=180)
    plt.close(fig)
    keys=['settlement_population','twi_wetness','soil_k_factor','ls_factor']
    labels=['Population','Wetness (TWI)','Soil K','Hillslope LS']
    fig,ax=plt.subplots(figsize=(9,4.7));fig.subplots_adjust(left=.21,right=.96,top=.72,bottom=.18)
    for offset,name,label,color in [(-.18,'baseline','Original','#b9b6af'),(.18,'ghsl_flat_0.1deg','Replacement scenario','#377c8c')]:
        values=[next(100*r['valid']/r['total'] for r in coverage if r['scenario']==name and r['zone']=='Rectangle' and r['component']==key) for key in keys]
        bars=ax.barh(np.arange(4)+offset,values,height=.33,label=label,color=color)
        ax.bar_label(bars,fmt='%.1f%%',padding=3,fontsize=10)
    ax.set_yticks(np.arange(4),labels);ax.invert_yaxis();ax.set_xlim(0,114);ax.set_xticks([0,25,50,75,100]);ax.set_xlabel('Available in the display rectangle (%)')
    fig.legend(*ax.get_legend_handles_labels(),loc='upper left',bbox_to_anchor=(.21,.82),ncol=2,frameon=False)
    fig.suptitle('Population and wetness gaps can be addressed; soil gaps remain',fontsize=15,y=.96)
    fig.text(.05,.86,'Goslar / Abzucht | Population is model-derived; flat-slope wetness is a calculation scenario',fontsize=10)
    fig.text(.05,.04,'Soil NoData and channel-excluded hillslope LS are preserved. No missing source value was filled with zero.',fontsize=10)
    for fmt in ['png','svg']:fig.savefig(OUT/f'coverage_before_after.{fmt}',dpi=180)
    plt.close(fig)


if __name__ == '__main__':
    main()
