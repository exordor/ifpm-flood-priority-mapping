"""Goslar extent runs with frozen normalization: Abzucht (HQ100) and multi-river.

Ported from bin/analysis/run_abzucht_expanded.py and bin/analysis/run_goslar_multiriver_full.py.
Both enlarge the original basin onto the same 30 m pixel lattice and keep the 2-98
percentile anchors of the smaller run, so scores stay on the original scale:

- Abzucht: re-fits the basin anchors by replaying four basin stages against the basin
  outputs (every replayed raster must equal the existing file), then runs the chain on
  basin + HQ100 polygon buffer (+ display rectangle).
- Multi-river: Abzucht extent + all retained flood products buffered by 2 km, four DEM
  tiles and a 10 km terrain pad; anchors copied from the Abzucht run.

The two runs differ in many small preprocessing details (window reads, slope formula,
hydrology cropping, padded proximity). Those differences are kept exactly as they were,
because the goal is to reproduce the existing outputs.
"""

from __future__ import annotations

import json
import math
import shutil
import types
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import geometry_mask, rasterize
from rasterio.transform import from_origin
from rasterio.warp import Resampling, reproject, transform_bounds
from rasterio.windows import from_bounds
from scipy.ndimage import distance_transform_edt

from . import compare, landcover, terrain
from .chain import STAGES, Context, basin_context
from .config import ROOT, Config
from .io import raster_mask, read_grid, sha256_file
from .normalize import Normalizer


def _out_context(cfg: Config, extent: str, run_root: Path) -> Context:
    """Chain context for an extent: chain/ and landcover/ inside the extent folder."""
    ext = cfg.extent(extent)
    out = Path(run_root) / ext["out_dir"]
    ctx = Context(cfg, extent, run_root, chain_dir=out / "chain", landcover_dir=out / "landcover",
                  boundary_gpkg=out / "expanded_boundary.gpkg", boundary_layer="expanded_boundary",
                  focus_area_id=ext["focus_area_id"])
    # The CLMS tree-cover loss is recomputed for the larger extent; the bare-soil layer
    # keeps its original path (manifest only).
    ctx.p["CLMS_TCD_LOSS"] = out / "landcover" / ctx.p["CLMS_TCD_LOSS"].name
    ctx.out = out
    return ctx


def _write_gpkg(ctx, frame, path: Path, layer: str) -> None:
    ctx._guard(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_file(path, layer=layer, driver="GPKG")


def _source_root(run_root: Path, rel: str) -> Path:
    """Root holding an upstream run: the --out folder if that run is there, else the workspace."""
    return Path(run_root) if (Path(run_root) / rel).exists() else ROOT


# ======================================================================================
# Abzucht
# ======================================================================================

def replay_check(path: Path, data, transform, crs, nodata=-9999):
    """Writer used while re-fitting the basin anchors: compare instead of writing."""
    if not path.exists():
        raise FileNotFoundError(f'Baseline replay target missing: {path}')
    with rasterio.open(path) as ds:
        old = ds.read(1)
        if ds.transform != transform or str(ds.crs) != str(crs) or old.shape != data.shape:
            raise ValueError('Baseline replay grid differs')
        old_valid = (old != ds.nodata) & np.isfinite(old)
        new_valid = np.isfinite(data) & (data != nodata)
        if not np.array_equal(old_valid, new_valid):
            raise ValueError(f'Baseline replay support differs: {path}')
        keep = old_valid
        if keep.any() and np.max(np.abs(old[keep] - data[keep])) > 1e-5:
            raise ValueError(f'Baseline replay differs: {path}')


def warp_window(path: Path, profile: dict, resampling=Resampling.nearest, percent=False):
    """Windowed boundless read around ``profile`` (3-cell margin), then reproject to it."""
    with rasterio.open(path) as ds:
        bounds = rasterio.transform.array_bounds(profile['height'], profile['width'], profile['transform'])
        bb = transform_bounds(profile['crs'], ds.crs, *bounds, densify_pts=21)
        win = from_bounds(*bb, ds.transform).round_offsets().round_lengths()
        win = rasterio.windows.Window(win.col_off - 3, win.row_off - 3, win.width + 6, win.height + 6)
        data = ds.read(1, window=win, boundless=True, masked=True).astype('float32').filled(np.nan)
        if percent:
            data[(data < 0) | (data > 100)] = np.nan
        dst = np.full((profile['height'], profile['width']), np.nan, dtype='float32')
        reproject(data, dst, src_transform=ds.window_transform(win), src_crs=ds.crs, src_nodata=np.nan,
                  dst_transform=profile['transform'], dst_crs=profile['crs'], dst_nodata=np.nan,
                  resampling=resampling)
        return dst


def lattice_grid(old_profile: dict, bounds, res: float) -> dict:
    """Grid covering ``bounds`` on the pixel lattice of ``old_profile`` (whole cells only)."""
    t = old_profile['transform']
    minx, miny, maxx, maxy = bounds
    x = t.c + math.floor((minx - t.c) / res) * res
    y = t.f + math.ceil((maxy - t.f) / res) * res
    return dict(old_profile, width=math.ceil((maxx - x) / res), height=math.ceil((y - miny) / res),
                transform=from_origin(x, y, res, res))


def run_abzucht(cfg: Config, extent: str, run_root: Path, steps: list[str] | None = None) -> None:
    import geopandas as gpd
    from shapely.geometry import box
    ext = cfg.extent(extent)
    fill = ext["fill_display_rectangle"]
    res = float(cfg["res_m"])

    # 1. Re-fit the basin anchors: replay four basin stages; every output must match.
    base_ext = cfg.extent(ext["baseline_extent"])
    base_root = _source_root(run_root, base_ext["chain_dir"] + "/priority_scenarios/run_manifest.json")
    basin = basin_context(cfg, ext["baseline_extent"], base_root, read_only=True)
    old_manifest = json.loads((basin.p["SCENARIO_DIR"] / "run_manifest.json").read_text())
    baseline_inputs = ([base_root / x['path'] for x in old_manifest['criterion_raster_lineage'].values()]
                       + [base_root / old_manifest['priority_raster_lineage']['path'], basin.boundary_gpkg])
    ctx = _out_context(cfg, extent, run_root)
    out = ctx.out
    hashes = {ctx.rel(p): sha256_file(p) for p in baseline_inputs}
    hash_paths = dict(zip(hashes, baseline_inputs))
    anchors = {}
    basin.normalize = Normalizer("record", anchors)
    basin.raster_writer = replay_check
    for stage in ['soilgrids_kfactor', 'rainfall', 'criteria_stack', 'exposure_indicators']:
        print('Capture baseline:', stage, flush=True)
        basin.normalize.start(stage)
        STAGES[stage](basin)
    ctx.mkdir(out)
    ctx.write_text(out / 'frozen_normalization.json', json.dumps(anchors, indent=2) + '\n')
    ctx.normalize = Normalizer("frozen", anchors)

    # 2. Expanded boundary: basin + HQ100 polygon buffer (+ display rectangle).
    old_geom = basin.boundary_geometry(ctx.crs)
    zones = gpd.read_file(cfg.path("goslar_regulatory_flood_zones")).to_crs(ctx.crs)
    hq = zones[zones.uesg_id == ext["hq100_uesg_id"]].geometry.union_all()
    geom = old_geom.union(hq.buffer(ext["hq100_buffer_m"]))
    xmin, ymin, xmax, ymax = hq.bounds
    margin = ext["display_margin_m"]
    display_rectangle = box(xmin - margin, ymin - margin, xmax + margin, ymax + margin)
    if fill:
        geom = geom.union(display_rectangle)
    _write_gpkg(ctx, gpd.GeoDataFrame({'boundary_id': [ctx.focus_area_id], 'claim_level': ['diagnostic_only']},
                                      geometry=[geom], crs=ctx.crs), ctx.boundary_gpkg, ctx.boundary_layer)

    # 3. Grid on the basin pixel lattice, enlarged by whole cells; padded terrain grid.
    with rasterio.open(basin.p['DEM']) as ds:
        old_ref = ds.profile
    ref = lattice_grid(old_ref, geom.bounds, res)
    width, height = ref['width'], ref['height']
    x, y = ref['transform'].c, ref['transform'].f
    mask = geometry_mask([geom], out_shape=(height, width), transform=ref['transform'], invert=True)

    def write(path, arr, profile=ref):
        ctx.write_raster(path, np.where(np.isfinite(arr), arr, ctx.nodata), profile['transform'], profile['crs'])

    bc = ext["buffer_cells"]
    bref = dict(ref, width=width + 2 * bc, height=height + 2 * bc,
                transform=from_origin(x - res * bc, y + res * bc, res, res))
    dem = warp_window(cfg.path(cfg["inputs"]["dem"]), bref, Resampling.bilinear)
    write(ctx.p['DEM_BUFFERED'], dem, bref)
    crop = dem[bc:bc + height, bc:bc + width].copy()
    crop[~mask] = np.nan
    write(ctx.p['DEM'], crop)
    # WorldCover read once on the new grid; nearest mapping commutes with the lookups.
    worldcover = cfg.path(cfg["inputs"]["worldcover"])
    wc = warp_window(worldcover, ref)
    for key, lut_name in landcover.LUT_LAYERS.items():
        a = landcover.map_classes(wc, cfg["luts"][lut_name])
        a[~mask] = np.nan
        write(ctx.p[key], a)
    # Tree-cover loss from the full local native mosaics, not the basin-clipped layer.
    years = ext["tcd_years"]
    tcd = {yr: warp_window(cfg.path("goslar_clms_tcd_mosaic", year=yr), ref, Resampling.average, True) for yr in years}
    loss = landcover.tcd_loss(tcd[years[0]], tcd[years[1]])
    loss[~mask] = np.nan
    write(ctx.p['CLMS_TCD_LOSS'], loss)
    # The environmental stage reads WorldCover classes from this aligned copy.
    aligned_wc = out / 'landcover/worldcover_aligned.tif'
    write(aligned_wc, wc)
    ctx.p['WORLDCOVER_FILE'] = aligned_wc

    def expanded_slope(_ctx):
        if not np.isfinite(dem).all():
            raise ValueError('Buffered DEM gaps need explicit handling')
        gy, gx = np.gradient(dem.astype('float64'), res, res)
        sl = np.degrees(np.arctan(np.sqrt(gx * gx + gy * gy)))
        write(ctx.p['SLOPE_BUFFERED'], sl, bref)
        a = sl[bc:bc + height, bc:bc + width].copy()
        a[~mask] = np.nan
        write(ctx.p['SLOPE'], a)

    state = types.SimpleNamespace(cfg=cfg, ext=ext, ctx=ctx, out=out, ref=ref, mask=mask, geom=geom, hq=hq,
                                  old_geom=old_geom, display_rectangle=display_rectangle, fill=fill,
                                  old_manifest=old_manifest, base_root=base_root, hashes=hashes,
                                  hash_paths=hash_paths, write=write, worldcover=worldcover)
    stages = dict(STAGES, slope=expanded_slope, report=lambda _c: abzucht_report(state),
                  overlay=lambda _c: compare.hq100_overlay(
                      ctx, ctx.p['SCENARIO_DIR'] / 'run_manifest.json', out / 'overlay', ext["command"]))
    for name in ext["stages"]:
        if name == "prepare" or (steps is not None and name not in steps):
            continue
        print('Expanded run:', name, flush=True)
        ctx.normalize.start(name)
        stages[name](ctx)


def abzucht_report(s) -> None:
    """Manifest additions, old-vs-new comparison and availability rasters (expansion_manifest.json)."""
    ctx, ref, mask, out = s.ctx, s.ref, s.mask, s.out
    nm_path = ctx.p['SCENARIO_DIR'] / 'run_manifest.json'
    nm = json.loads(nm_path.read_text())
    nm.update(boundary_id=ctx.focus_area_id, experiment_id='fixed_scale', claim_level='diagnostic_only',
              focus_area_name=('Original project plus HQ100 buffer and display rectangle' if s.fill
                               else 'Original project plus HQ100 buffer') + '; comparison extent, not a catchment')
    nm['normalization']['method'] = 'Baseline 2/98 anchors frozen; see frozen_normalization.json'
    nm['normalization']['frozen_parameters'] = ctx.rel(out / 'frozen_normalization.json')
    nm['input_lineage'].pop('clms_bare_soil', None)
    ctx.write_text(nm_path, json.dumps(nm, indent=2) + '\n')
    with rasterio.open(ctx.p['SCENARIO_DIR'] / 'scenarios' / ctx.cfg["priority_filename"]) as ds:
        new = ds.read(1, masked=True).filled(np.nan)
    with rasterio.open(s.base_root / s.old_manifest['priority_raster_lineage']['path']) as ds:
        old = np.full(new.shape, np.nan, dtype='float32')
        reproject(ds.read(1), old, src_transform=ds.transform, src_crs=ds.crs, src_nodata=ds.nodata,
                  dst_transform=ref['transform'], dst_crs=ref['crs'], dst_nodata=np.nan,
                  resampling=Resampling.nearest)
    both = np.isfinite(old) & np.isfinite(new)
    hmask = geometry_mask([s.hq], out_shape=new.shape, transform=ref['transform'], invert=True)
    report = {'boundary_id': ctx.focus_area_id, 'experiment_id': 'fixed_scale', 'claim_level': 'diagnostic_only',
              'command': s.ext["command"], 'old_area_km2': s.old_geom.area / 1e6,
              'expanded_area_km2': s.geom.area / 1e6, 'normalization': 'baseline anchors frozen',
              'weights_changed': False, 'old_valid_cells': int(np.isfinite(old).sum()),
              'new_valid_cells': int(np.isfinite(new).sum()), 'hq100_cells': int(hmask.sum()),
              'hq100_valid_old': int((hmask & np.isfinite(old)).sum()),
              'hq100_valid_new': int((hmask & np.isfinite(new)).sum()),
              'common_mean_abs_change': float(np.abs(new[both] - old[both]).mean()),
              'common_max_abs_change': float(np.abs(new[both] - old[both]).max()),
              'baseline_hashes': s.hashes,
              'limitations': ['Expanded hydrology and proximity calculation can change old-area values despite frozen scales',
                              'Retains baseline within-criterion available-component averaging; inspect component coverage',
                              'Not hydrologic catchment or observed-event validation']}
    population = ctx.p['EXPOSURE_DIR'] / 'population_exposure_0_1.tif'
    for key, path in [('soil_k', ctx.p['K_SCORED']), ('tcd', ctx.p['CLMS_TCD_LOSS']), ('population', population)]:
        a = ctx.read_band(path, ref)
        report[key + '_valid_cells'] = int((mask & np.isfinite(a)).sum())
    report['common_changed_cells_gt_1e_5'] = int((both & (np.abs(new - old) > 1e-5)).sum())
    report['common_changed_cells_gt_0_01'] = int((both & (np.abs(new - old) > .01)).sum())
    delta = np.where(both, new - old, np.nan)
    s.write(out / 'old_area_score_change.tif', delta)
    report['old_hq_mean_new_score'] = float(new[hmask & np.isfinite(old)].mean())
    report['added_hq_mean'] = float(new[hmask & ~np.isfinite(old) & np.isfinite(new)].mean())
    support = {}
    for key, path in [('soil_k', ctx.p['K_SCORED']), ('population', population), ('ls', ctx.p['LS_CAPPED']),
                      ('tcd', ctx.p['CLMS_TCD_LOSS'])]:
        a = ctx.read_band(path, ref)
        av = np.isfinite(a)
        s.write(out / f'{key}_availability.tif', np.where(mask, av.astype(float), np.nan))
        support[key] = {'all_valid': int((av & mask).sum()), 'hq100_valid': int((av & hmask).sum()),
                        'hq100_total': int(hmask.sum()), 'added_valid': int((av & mask & ~np.isfinite(old)).sum())}
    report['component_support'] = support
    rect_mask = geometry_mask([s.display_rectangle], out_shape=new.shape, transform=ref['transform'], invert=True)
    report['display_rectangle'] = {'bounds_utm32n': list(s.display_rectangle.bounds), 'requested_fill': s.fill,
                                   'cells': int(rect_mask.sum()), 'scored_cells': int((rect_mask & np.isfinite(new)).sum())}
    if s.fill and not np.isfinite(new[rect_mask]).all():
        raise ValueError('Display rectangle still has unscored cells; inspect component coverage')
    if s.fill:
        rows, cols = np.where(rect_mask)
        window = rasterio.windows.Window.from_slices((rows.min(), rows.max() + 1), (cols.min(), cols.max() + 1))
        arr = new[rows.min():rows.max() + 1, cols.min():cols.max() + 1]
        rect_ref = dict(ref, width=arr.shape[1], height=arr.shape[0],
                        transform=rasterio.windows.transform(window, ref['transform']))
        s.write(out / 'display_rectangle_priority.tif', arr, rect_ref)
    here = Path(__file__).resolve().parent
    source_files = [here / 'expanded.py', here / 'normalize.py', here / 'chain.py', s.worldcover]
    source_files += sorted(s.cfg.path(s.cfg["rainfall"]["dataset"]).glob('*.asc.gz'))
    source_files += [s.cfg.path("goslar_clms_tcd_mosaic", year=yr) for yr in s.ext["tcd_years"]]
    source_files += [out / 'frozen_normalization.json']
    report['additional_source_hashes'] = {ctx.rel(p): sha256_file(p) for p in source_files}
    for name, h in s.hashes.items():
        if sha256_file(s.hash_paths[name]) != h:
            raise ValueError('Baseline modified: ' + name)
    ctx.write_text(out / 'expansion_manifest.json', json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


# ======================================================================================
# Multi-river
# ======================================================================================

def census_grid(frame, bounds):
    """Zensus 2022 100 m CSV rows inside ``bounds`` (EPSG:3035) as a raster."""
    import pandas as pd
    left = np.floor(bounds[0] / 100) * 100
    bottom = np.floor(bounds[1] / 100) * 100
    right = np.ceil(bounds[2] / 100) * 100
    top = np.ceil(bounds[3] / 100) * 100
    selected = frame[(frame.x_mp_100m >= left) & (frame.x_mp_100m < right) &
                     (frame.y_mp_100m >= bottom) & (frame.y_mp_100m < top)].copy()
    counts = pd.to_numeric(selected.Einwohner, errors='raise').to_numpy(dtype='float32')
    if not np.isfinite(counts).all() or (counts < 0).any() or selected.GITTER_ID_100m.duplicated().any():
        raise ValueError('Unexpected census counts or duplicate cells; review source coding')
    array = np.full((round((top - bottom) / 100), round((right - left) / 100)), np.nan, dtype='float32')
    rows = ((top - selected.y_mp_100m.to_numpy()) / 100).astype(int)
    cols = ((selected.x_mp_100m.to_numpy() - left) / 100).astype(int)
    array[rows, cols] = counts
    profile = dict(height=array.shape[0], width=array.shape[1], crs='EPSG:3035',
                   transform=from_origin(left, top, 100, 100))
    return selected, array, profile


def run_multiriver(cfg: Config, extent: str, run_root: Path, steps: list[str] | None = None) -> None:
    import geopandas as gpd
    ext = cfg.extent(extent)
    res = float(cfg["res_m"])
    ins = ext["inputs"]
    base_ext = cfg.extent(ext["baseline_extent"])
    base_rel = base_ext["out_dir"]
    base_root = _source_root(run_root, base_rel + "/chain/priority_scenarios/run_manifest.json")
    base = base_root / base_rel
    ctx = _out_context(cfg, extent, run_root)
    out = ctx.out
    ctx.mkdir(out)
    inputs, pinned = {}, {}

    def pin(path: Path) -> Path:
        """Record an input's hash; all of them are re-checked at the end of the run."""
        path = Path(path)
        inputs[ctx.rel(path)] = sha256_file(path)
        pinned[ctx.rel(path)] = path
        return path

    oldm = json.loads(pin(base / 'chain/priority_scenarios/run_manifest.json').read_text())
    for e in [oldm['priority_raster_lineage'], *oldm['criterion_raster_lineage'].values()]:
        assert sha256_file(pin(base_root / e['path'])) == e['sha256']
    old, oref = read_grid(base_root / oldm['priority_raster_lineage']['path'])
    oldgeom = gpd.read_file(pin(base / 'expanded_boundary.gpkg')).geometry.union_all()
    ps = gpd.read_file(pin(cfg.path(ext["products"])), layer=cfg.layer(ext["products"]))
    allflood = ps.geometry.union_all()
    geom = oldgeom.union(allflood.buffer(ext["product_buffer_m"]))
    ref = lattice_grid(oref, geom.bounds, res)
    shape = (ref['height'], ref['width'])
    mask = raster_mask(geom, ref)
    bc = ext["buffer_cells"]
    bref = dict(ref, width=ref['width'] + 2 * bc, height=ref['height'] + 2 * bc,
                transform=ref['transform'] * rasterio.Affine.translation(-bc, -bc))
    crop = (slice(bc, bc + shape[0]), slice(bc, bc + shape[1]))
    _write_gpkg(ctx, gpd.GeoDataFrame({'boundary_id': [ctx.focus_area_id]}, geometry=[geom], crs=ref['crs']),
                ctx.boundary_gpkg, ctx.boundary_layer)
    _write_gpkg(ctx, ps, out / 'comparison_boundaries.gpkg', 'products')
    ctx._guard(out / 'source_inventory.csv')
    ps.drop(columns='geometry').to_csv(out / 'source_inventory.csv', index=False)

    # Multi-river inputs.
    p = ctx.p
    basin_population = p["ZENSUS_TIF"]
    p["SOILGRIDS_K_SNAPSHOT"] = cfg.path(ins["soilgrids_k"])
    p["ROADS"] = cfg.path(ins["roads"])
    p["INFRASTRUCTURE"] = cfg.path(ins["facilities"])
    ctx.infrastructure_layer = cfg.layer(ins["facilities"])
    p["PROTECTED_RAW"] = cfg.path(ins["protected"])
    # Population is read below (clip or national zip); the basin file is not used here.
    p["ZENSUS_TIF"] = out / "sources" / basin_population.name
    worldcover = cfg.path(cfg["inputs"]["worldcover"])
    # Complete acquisition manifests are required before any expensive stage.
    osm = json.loads(pin(cfg.manifest_path(ins["roads"])).read_text())
    for name, key in [('roads', 'roads'), ('facilities', 'facilities')]:
        assert sha256_file(pin(cfg.path(ins[key]))) == osm['sources'][name]['gpkg_sha256']
    assert osm['sources']['roads'].get('acquisition_complete') is True, \
        'Road acquisition must be complete for required source support'
    for meta in [cfg.manifest_path(ins["protected"]), cfg.manifest_path(ins["dem_tiles"]),
                 cfg.manifest_path(ins["soilgrids_k"])]:
        pin(meta)
    anchors = json.loads(pin(base / 'frozen_normalization.json').read_text())
    ctx.write_text(out / 'frozen_normalization.json', json.dumps(anchors, indent=2) + '\n')
    ctx.normalize = Normalizer("frozen", anchors)

    def write(path, a, profile=ref, masked=True):
        a = a.copy()
        if masked:
            a[~mask] = np.nan
        ctx.write_raster(path, np.where(np.isfinite(a), a, ctx.nodata), profile['transform'], profile['crs'])

    def warp(path, profile=ref, resampling=Resampling.nearest, percent=False):
        """Full-band reproject; for percent layers a windowed read with 0-100 validity."""
        pin(path)
        with rasterio.open(path) as ds:
            dst = np.full((profile['height'], profile['width']), np.nan, 'float32')
            source = rasterio.band(ds, 1)
            source_transform = ds.transform
            source_nodata = ds.nodata
            if percent:
                bounds = transform_bounds(profile['crs'], ds.crs, *rasterio.transform.array_bounds(
                    profile['height'], profile['width'], profile['transform']), densify_pts=21)
                w = rasterio.windows.from_bounds(*bounds, ds.transform).round_offsets().round_lengths()
                w = rasterio.windows.Window(w.col_off - 3, w.row_off - 3, w.width + 6, w.height + 6)
                source = ds.read(1, window=w, boundless=True, masked=True).astype('float32').filled(np.nan)
                source[(source < 0) | (source > 100)] = np.nan
                source_transform = ds.window_transform(w)
                source_nodata = np.nan
            reproject(source, dst, src_transform=source_transform, src_crs=ds.crs, src_nodata=source_nodata,
                      dst_transform=profile['transform'], dst_crs=profile['crs'], dst_nodata=np.nan,
                      resampling=resampling)
        return dst

    def proximity(geometries, decay_m, buffer=ext["proximity_pad_m"]):
        """Distance computed on a padded grid so features just outside still count."""
        pad = math.ceil(buffer / res)
        prof = dict(ref, width=ref['width'] + 2 * pad, height=ref['height'] + 2 * pad,
                    transform=ref['transform'] * rasterio.Affine.translation(-pad, -pad))
        a = rasterize([(g, 1) for g in geometries], out_shape=(prof['height'], prof['width']),
                      transform=prof['transform'], fill=0, dtype='uint8')
        assert a.any()
        d = distance_transform_edt(a == 0, sampling=(res, res))[pad:pad + shape[0], pad:pad + shape[1]]
        return np.clip(1 - d / decay_m, 0, 1), d

    def terrain_stage(_ctx):
        files = [cfg.path(cfg["inputs"]["dem"]),
                 *sorted(cfg.path(ins["dem_tiles"]).glob(cfg.entry(ins["dem_tiles"])["pattern"]))]
        if len(files) != 4:
            raise ValueError('Four DEMtiles required')
        dem = np.full((bref['height'], bref['width']), np.nan, 'float32')
        for path in files:
            a = warp(path, bref, Resampling.bilinear)
            z = np.isfinite(a)
            dem[z] = a[z]
        if not np.isfinite(dem).all():
            raise ValueError('DEM canvas gaps')
        write(p['DEM_BUFFERED'], dem, bref, False)
        write(p['DEM'], dem[crop])
        gy, gx = np.gradient(dem.astype('float64'), res, res)
        s = np.degrees(np.arctan(np.hypot(gx, gy)))
        write(p['SLOPE_BUFFERED'], s, bref, False)
        write(p['SLOPE'], s[crop])

    def landcover_stage(_ctx):
        wc = warp(worldcover)
        assert np.isfinite(wc[mask]).all()
        for key, lut_name in landcover.LUT_LAYERS.items():
            a = np.full(shape, np.nan, 'float32')
            for k, v in cfg["luts"][lut_name].items():
                a[wc == k] = v
            write(p[key], a)
        years = ext["tcd_years"]
        tcd = {yr: warp(cfg.path("goslar_clms_tcd_mosaic", year=yr), resampling=Resampling.average, percent=True)
               for yr in years}
        for a in tcd.values():
            a[(a < 0) | (a > 100)] = np.nan
        write(p['CLMS_TCD_LOSS'], landcover.tcd_loss(tcd[years[0]], tcd[years[1]]))
        write(out / 'landcover/worldcover_aligned.tif', wc)

    def hydrology(_ctx):
        tmp = out / 'tmp_hydrology'
        ctx.mkdir(tmp)
        filled, pointer, acc, sca, twi = (tmp / n for n in ['filled.tif', 'pointer.tif', 'acc.tif', 'sca.tif', 'twi.tif'])
        terrain.run_wbt('fill_depressions_wang_and_liu', dem=str(p['DEM_BUFFERED']), output=str(filled), fix_flats=True)
        terrain.run_wbt('d8_pointer', dem=str(filled), output=str(pointer), esri_pntr=False)
        for output, kind in [(acc, 'cells'), (sca, 'specific contributing area')]:
            terrain.run_wbt('d8_flow_accumulation', i=str(pointer), output=str(output), out_type=kind,
                                  pntr=True, esri_pntr=False)
        terrain.run_wbt('wetness_index', sca=str(sca), slope=str(p['SLOPE_BUFFERED']), output=str(twi))
        for source, target in [(filled, p['FILLED']), (pointer, p['D8_PNTR']), (acc, p['FLOW_ACC_CELLS']),
                               (sca, p['FLOW_ACC_SCA']), (twi, p['TWI'])]:
            a = read_grid(source)[0]
            write(target, a[crop])
        flow = read_grid(acc)[0]
        streams = np.isfinite(flow) & (flow > cfg["stream_threshold"])
        distance = distance_transform_edt(~streams, sampling=(res, res))
        write(p['DISTANCE'], distance[crop])
        write(p['STREAMS_T500'], streams[crop].astype('float32'))
        shutil.rmtree(tmp)  # buffered WhiteboxTools grids; the cropped copies are kept above

    def soil(_ctx):
        pin(p['SOILGRIDS_K_SNAPSHOT'])
        STAGES['soilgrids_kfactor'](ctx)

    def roads(_ctx):
        frame = gpd.read_file(pin(p['ROADS'])).to_crs(ref['crs'])
        query = ext["road_query_buffer_m"]
        a, d = proximity(frame.geometry, cfg["decay_m"]["roads"], query)
        # The road query reaches at least 3 km beyond the target rectangle; if the nearest
        # road is closer than that, unseen roads beyond the query cannot be closer.
        if d[mask].max() >= query:
            raise ValueError('Road querybuffer insufficient for nearest-neighbour coverage')
        write(p['ROAD_ACCESS'], a)

    def rain(_ctx):
        for path in cfg.path(cfg["rainfall"]["dataset"]).glob('*.asc.gz'):
            pin(path)
        STAGES['rainfall'](ctx)

    def protected(_ctx):
        a, _ = proximity(gpd.read_file(pin(p['PROTECTED_RAW'])).to_crs(ref['crs']).geometry,
                         cfg["decay_m"]["protected"])
        write(p['ES_DIR'] / 'protected_area_context_0_1.tif', a)

    population_file = {}

    def exposure(_ctx):
        national_zip = cfg.path(ins["population_zip"])
        clip_id = ins["population_clip"]
        if national_zip.exists():
            member = cfg.entry(ins["population_zip"])["member"]
            import pandas as pd
            with zipfile.ZipFile(pin(national_zip)) as z:
                frame = pd.read_csv(z.open(member), sep=';')
            bounds = transform_bounds(ref['crs'], 3035, *rasterio.transform.array_bounds(*shape, ref['transform']),
                                      densify_pts=21)
            selected, a, prof = census_grid(frame, bounds)
            f = out / 'sources/population_native_100m.tif'
            write(f, a, prof, False)
        else:
            # The national zip is gone; read the 100 m clip this run derived from it.
            f = pin(cfg.path(clip_id))
            if inputs[ctx.rel(f)] != cfg.entry(clip_id)["sha256"]:
                raise ValueError('Promoted Zensus clip differs from the recorded derivation')
            with rasterio.open(f) as ds:
                if str(ds.crs) != 'EPSG:3035':
                    raise ValueError('Zensus clip must be EPSG:3035')
                a = ds.read(1, masked=True).astype('float32').filled(np.nan)
                prof = dict(height=ds.height, width=ds.width, crs=ds.crs, transform=ds.transform)
        dest = np.full(shape, np.nan, 'float32')
        reproject(a, dest, src_transform=prof['transform'], src_crs=prof['crs'], dst_transform=ref['transform'],
                  dst_crs=ref['crs'], resampling=Resampling.sum)
        pin(f)
        population_file['path'] = f
        dest[~mask] = np.nan
        if np.any(mask & (dest == 0)):
            raise ValueError('Unexpected zero population after legacy warp; inspect source-domain coverage')
        std, _, _ = ctx.normalize(dest, mask, constant_policy='zeros')
        write(p['EXPOSURE_DIR'] / 'population_exposure_0_1.tif', std)
        infra, _ = proximity(gpd.read_file(pin(p['INFRASTRUCTURE'])).to_crs(ref['crs']).geometry,
                             cfg["decay_m"]["facilities"], ext["facility_pad_m"])
        write(p['EXPOSURE_DIR'] / 'built_infrastructure_exposure_0_1.tif', infra)

    def environment(_ctx):
        wc = warp(worldcover, bref)
        assert np.isfinite(wc).all()
        a = np.isin(wc, cfg["water_wetland_classes"])
        distance = distance_transform_edt(~a, sampling=(res, res))
        water = np.clip(1 - distance[crop] / cfg["decay_m"]["water"], 0, 1)
        write(p['ES_DIR'] / 'water_wetland_context_0_1.tif', water)

    def priority(_ctx):
        # Files of the basin manifest that this extent does not use are listed as such.
        ctx.lineage_missing_ok = True
        STAGES['priority_scenarios'](ctx)
        ctx.lineage_missing_ok = False
        nmfile = p['SCENARIO_DIR'] / 'run_manifest.json'
        nm = json.loads(nmfile.read_text())
        nm.update(boundary_id=ctx.focus_area_id, experiment_id='fixed_scale', claim_level='diagnostic_only')
        nm['normalization']['method'] = 'Original frozen anchors; no refit'
        nm['focus_area_name'] = 'Original model union all retained official flood products plus 2km buffer'
        nm['boundary_contract'] = {'id': ctx.focus_area_id, 'source': 'old model union retained flood polygons plus 2km',
                                   'area_km2': geom.area / 1e6, 'claim': 'comparison domain, not hydrologic catchment'}
        nm['hydrology_buffer_m'] = ext["proximity_pad_m"]
        nm['data_sources']['dem'] = 'Four Copernicus GLO30 tiles N51/N52 E009/E010'
        if 'path' in population_file:
            nm['input_lineage']['population'] = ctx.lineage(population_file['path'])
        nm['input_lineage']['wrapper'] = ctx.lineage(Path(__file__).resolve())
        nm['input_lineage']['dem_tiles'] = [ctx.lineage(pinned[r]) for r in inputs if 'Copernicus_DSM_' in r]
        nm['normalization']['frozen_parameters'] = ctx.rel(out / 'frozen_normalization.json')
        nm['note'] = 'Expanded controlled comparison; data gaps retained; new source versions and larger hydrology can change overlap'
        nm['input_lineage'].pop('dem', None)
        nm['input_lineage'].pop('clms_bare_soil', None)
        nm['data_sources'].pop('clms_bare_soil', None)
        ctx.write_text(nmfile, json.dumps(nm, indent=2) + '\n')

    state = types.SimpleNamespace(cfg=cfg, ext=ext, ctx=ctx, out=out, ref=ref, oref=oref, old=old, oldm=oldm,
                                  mask=mask, geom=geom, ps=ps, allflood=allflood, shape=shape, write=write,
                                  pin=pin, inputs=inputs, pinned=pinned, osm=osm, base=base, base_root=base_root)
    stages = {'terrain': terrain_stage, 'landcover': landcover_stage, 'hydrology': hydrology,
              'ls_factor': STAGES['ls_factor'], 'soilgrids_kfactor': soil, 'osm_roads': roads, 'rainfall': rain,
              'protected_areas': protected, 'criteria_stack': STAGES['criteria_stack'],
              'exposure_indicators': exposure, 'environmental_sensitivity': environment,
              'priority_scenarios': priority,
              'comparison': lambda _c: compare.multiriver_comparison(state),
              'report': lambda _c: compare.multiriver_report(state)}
    for name in ext["stages"]:
        if name == "prepare" or (steps is not None and name not in steps):
            continue
        print('Run', name, flush=True)
        ctx.normalize.start(name)
        stages[name](ctx)
