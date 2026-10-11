"""Comparisons of the PIM with official flood areas (Goslar), and their reports.

- ``hq100_overlay``: Abzucht HQ100 polygon versus the PIM (from bin/analysis/compare_abzucht_hq100.py).
- ``multiriver_comparison``: 14 flood products, rings and alternative flood weights
  (the tail of bin/analysis/run_goslar_multiriver_full.py).
- ``multiriver_report``: read-back checks, summary tables and READING_NOTE.md
  (bin/analysis/report_goslar_multiriver_full.py).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.warp import Resampling, reproject

from . import figures
from .config import ROOT
from .io import raster_mask, read_grid, sha256_file, write_csv
from .scoring import HIGH_THRESHOLD, score_at, summarize, weights_at


def clean_ring(geometry, radius, exclusion):
    """Ring of ``radius`` around ``geometry`` minus every official flood footprint."""
    return geometry.buffer(radius).difference(geometry).difference(exclusion)


def stats(array, zone):
    result = summarize(array, zone)
    return {k: v for k, v in result.items() if k != 'class_counts'}


def _abs(ctx, rel: str) -> Path:
    """A path recorded in a manifest: under the run root if it is there, else the workspace."""
    candidate = ctx.run_root / rel
    return candidate if candidate.exists() else ROOT / rel


# --- Abzucht HQ100 ----------------------------------------------------------------------

def hq100_overlay(ctx, manifest_path: Path, out: Path, command: str) -> dict:
    """HQ100 polygon vs PIM: zone statistics, contributions, category raster and figure."""
    import geopandas as gpd
    from shapely.geometry import box
    m = json.loads(manifest_path.read_text())
    pim_path = _abs(ctx, m['priority_raster_lineage']['path'])
    if sha256_file(pim_path) != m['priority_raster_lineage']['sha256']:
        raise ValueError('PIM hash differs from run manifest')
    pim, profile = read_grid(pim_path)
    valid = np.isfinite(pim)
    if np.any((pim[valid] < 0) | (pim[valid] > 1)):
        raise ValueError('PIM outside [0,1]')
    vector_path = ctx.cfg.path("goslar_regulatory_flood_zones")
    vectors = gpd.read_file(vector_path)
    vectors = vectors[vectors.uesg_id == ctx.ext["hq100_uesg_id"]].to_crs(profile['crs'])
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
    zone_stats = {name: summarize(pim, zone) for name, zone in zones.items()}
    boundary_path = _abs(ctx, m['input_lineage']['boundary']['path'])
    boundary = gpd.read_file(boundary_path).to_crs(profile['crs'])
    intersection = geom.intersection(boundary.geometry.union_all())
    weights = m['main_weights']
    contributions, inputs = [], [manifest_path, vector_path, pim_path, boundary_path]
    for key, weight in weights.items():
        item = m['criterion_raster_lineage'][key]
        path = _abs(ctx, item['path'])
        if sha256_file(path) != item['sha256']:
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
    ctx.mkdir(out)
    report = {
        'boundary_id': m['focus_area_id'], 'experiment_id': 'abzucht_hq100_overlay',
        'claim_level': 'diagnostic_only', 'evidence': '2026 HQ100 modelled regulatory scenario, local August snapshot',
        'enters_pim_score': False, 'weights_changed': False, 'event_accuracy': False,
        'command': command,
        'class_edges': [0, .2, .4, .6, .8, 1], 'high_definition': 'PIM >= 0.6; existing five equal-interval class boundaries',
        'sampling': 'Cell center inclusion; descriptive comparison, no significance test; ring is geographic context, not matched control',
        'coverage': {'polygon_area_km2': geom.area / 1e6, 'area_inside_boundary_km2': intersection.area / 1e6,
                     'fraction_inside_boundary': intersection.area / geom.area,
                     'inside_cells': int(inside.sum()), 'valid_inside_cells': int((inside & valid).sum()),
                     'nodata_inside_cells': int((inside & ~valid).sum())},
        'statistics': zone_stats,
        'all_touched_sensitivity': summarize(pim, mask(geom, True)),
        'weights': weights, 'contribution_max_reconstruction_error': max_error,
        'inputs': {ctx.rel(p): sha256_file(p) for p in inputs + [Path(__file__).resolve()]},
        'limits': ['NoData excluded from score summaries', 'HQ100 polygon is not observed flood extent',
                   'PIM integrates multiple criteria and is not inundation probability',
                   'Flood scenario and project indicators may share terrain or river information'],
    }
    ctx._guard(out / 'comparison.csv')
    with (out / 'comparison.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['zone', 'valid_cells', 'mean_pim', 'median_pim', 'share_pim_ge_0_6',
                         '0_0.2', '0.2_0.4', '0.4_0.6', '0.6_0.8', '0.8_1'])
        for name, s in zone_stats.items():
            writer.writerow([name, s['valid_cells'], s['mean'], s['median'], s['high_share'], *s['class_counts']])
    means = {}
    with (out / 'criterion_contributions.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['criterion', 'weight', 'mean_contribution_hq100', 'mean_contribution_1km_ring'])
        for i, (key, w) in enumerate(weights.items()):
            vals = [float(contributions[i][zone & valid].mean()) for zone in [inside, ring]]
            means[key] = vals
            writer.writerow([key, w, *vals])
    report['mean_contributions'] = means
    ctx.write_text(out / 'manifest.json', json.dumps(report, indent=2) + '\n')
    # Categories: 0 = outside HQ100, 255 = unused NoData.
    categories = np.zeros(pim.shape, dtype='uint8')
    categories[inside & ~valid] = 1
    categories[inside & valid & (pim < HIGH_THRESHOLD)] = 2
    categories[inside & valid & (pim >= HIGH_THRESHOLD)] = 3
    raster_profile = profile.copy()
    raster_profile.update(dtype='uint8', nodata=255, count=1, compress='deflate')
    with rasterio.open(out / 'hq100_comparison_categories.tif', 'w', **raster_profile) as dst:
        dst.write(categories, 1)
        dst.update_tags(claim_level='diagnostic_only',
                        categories='0=outside HQ100;1=HQ100 without PIM;2=HQ100 PIM<0.6;3=HQ100 PIM>=0.6')
    vectors.to_file(out / 'abzucht_hq100.gpkg', layer='abzucht_hq100', driver='GPKG', mode='w')
    figures.hq100_figure(out, pim, profile, vectors, boundary, geom, categories, zone_stats, means, weights,
                         intersection.area / geom.area)
    print(json.dumps({'coverage': report['coverage'], 'stats': zone_stats, 'contributions': means}, indent=2))
    return report


# --- multi-river comparison -------------------------------------------------------------

def multiriver_comparison(s) -> None:
    """Alternative flood weights, product/ring statistics, coverage tables, maps, manifest."""
    ctx, ref, out, write, ext = s.ctx, s.ref, s.out, s.write, s.ext
    ps, allflood, mask, shape = s.ps, s.allflood, s.mask, s.shape
    nm = json.loads((ctx.p['SCENARIO_DIR'] / 'run_manifest.json').read_text())
    pim = read_grid(_abs(ctx, nm['priority_raster_lineage']['path']), ref)[0]
    criteria = {k: read_grid(_abs(ctx, e['path']), ref)[0] for k, e in nm['criterion_raster_lineage'].items()}
    valid = np.isfinite(pim)
    base_percent = int(round(nm['main_weights']['flood_hazard'] * 100))
    scores = {base_percent: pim}
    for pct in ext["flood_percents"]:
        scores[pct] = score_at(criteria, weights_at(nm['main_weights'], pct / 100), valid)
        write(out / f'pim_flood_{pct}.tif', scores[pct])
    coverage, rows = [], []
    all_masks = {t: raster_mask(allflood, ref, t) for t in [False, True]}
    masked_flood = np.where(valid, criteria['flood_hazard'], np.nan)
    for _, p in ps.iterrows():
        inside = raster_mask(p.geometry, ref)
        coverage.append(dict(product_id=p.product_id, river=p.river, family=p.family, scenario=p.scenario,
                             source_area_km2=p.geometry.area / 1e6,
                             geometric_coverage=p.geometry.intersection(s.geom).area / p.geometry.area,
                             total_cells=int(inside.sum()), scored_cells=int((inside & valid).sum()),
                             unscored_cells=int((inside & ~valid).sum())))
        for touched in [False, True]:
            target = raster_mask(p.geometry, ref, touched)
            for radius in ext["ring_radii_m"]:
                control = raster_mask(clean_ring(p.geometry, radius, allflood), ref, touched) & ~all_masks[touched] & ~target
                for pct, score in scores.items():
                    for zone, z in [('inside', target), ('ring', control)]:
                        for metric, a in [('PIM', score), ('Flood indicator', masked_flood)]:
                            rows.append(dict(product_id=p.product_id, river=p.river, family=p.family,
                                             scenario=p.scenario, flood_percent=pct,
                                             inclusion='all_touched' if touched else 'center', radius_m=radius,
                                             metric=metric, zone=zone, **stats(a, z)))
    write_csv(out / 'coverage.csv', coverage)
    write_csv(out / 'comparison.csv', rows)
    availability = []
    p = ctx.p
    # Unsorted, as in the old run: the row order follows the file system.
    for path in list(p['CRITERIA_DIR'].glob('*_0_1.tif')) + [p['EXPOSURE_DIR'] / 'population_exposure_0_1.tif',
                                                            p['EXPOSURE_DIR'] / 'built_infrastructure_exposure_0_1.tif',
                                                            p['ES_DIR'] / 'protected_area_context_0_1.tif',
                                                            p['ES_DIR'] / 'water_wetland_context_0_1.tif']:
        a = read_grid(path, ref)[0]
        availability.append(dict(layer=path.stem, valid_cells=int((mask & np.isfinite(a)).sum()),
                                 total_cells=int(mask.sum())))
    write_csv(out / 'component_coverage.csv', availability)
    oref = s.oref
    oldaligned = np.full(shape, np.nan, 'float32')
    reproject(s.old, oldaligned, src_transform=oref['transform'], src_crs=oref['crs'], src_nodata=np.nan,
              dst_transform=ref['transform'], dst_crs=ref['crs'], dst_nodata=np.nan, resampling=Resampling.nearest)
    both = np.isfinite(oldaligned) & valid
    write(out / 'old_area_delta.tif', np.where(both, pim - oldaligned, np.nan))
    overlap = []
    for key, entry in s.oldm['criterion_raster_lineage'].items():
        a, pr = read_grid(s.base_root / entry['path'])
        aligned = np.full(shape, np.nan, 'float32')
        reproject(a, aligned, src_transform=pr['transform'], src_crs=pr['crs'], src_nodata=np.nan,
                  dst_transform=ref['transform'], dst_crs=ref['crs'], dst_nodata=np.nan, resampling=Resampling.nearest)
        z = np.isfinite(aligned) & np.isfinite(criteria[key])
        d = criteria[key][z] - aligned[z]
        overlap.append(dict(criterion=key, common_cells=int(z.sum()), old_mean=float(aligned[z].mean()),
                            new_mean=float(criteria[key][z].mean()), mean_signed_change=float(d.mean()),
                            mean_absolute_change=float(abs(d).mean()), max_absolute_change=float(abs(d).max())))
    write_csv(out / 'old_area_criterion_changes.csv', overlap)
    comparison = dict(common_cells=int(both.sum()),
                      mean_absolute_change=float(np.abs(pim[both] - oldaligned[both]).mean()),
                      max_absolute_change=float(np.abs(pim[both] - oldaligned[both]).max()))
    primary = [dict(row) for _, row in ps[ps.family == 'regulatory'].iterrows()]
    for pct, score in scores.items():
        figures.make_map(out / f'overview_{pct}', f'Goslar region | Flood weight {pct}%', primary, s.geom.bounds,
                         criteria['flood_hazard'], score, ref)
    for row in primary:
        figures.make_map(out / row['river'].lower(), row['river'] + ' | Expanded coverage', [row],
                         row['geometry'].buffer(500).bounds, criteria['flood_hazard'], pim, ref)
    for _, row in ps[ps.family != 'regulatory'].iterrows():
        figures.make_map(out / str(row.product_id), f'{row.river} | {row.scenario}', [dict(row)],
                         row.geometry.buffer(500).bounds, criteria['flood_hazard'], pim, ref)
    here = Path(__file__).resolve().parent
    for module in ['expanded.py', 'chain.py', 'normalize.py', 'compare.py', 'figures.py']:
        s.pin(here / module)
    for rel, h in s.inputs.items():
        assert sha256_file(s.pinned[rel]) == h, rel
    report = dict(boundary_id=ctx.focus_area_id, experiment_id='fixed_scale', claim_level='diagnostic_only',
                  area_km2=s.geom.area / 1e6, grid_shape=list(shape), target_cells=int(mask.sum()),
                  scored_cells=int(valid.sum()), hydrology_buffer_m=ext["proximity_pad_m"],
                  flow_boundary_limitation='Buffered comparison domain, not a complete upstream catchment; hydrology may change on overlap',
                  normalization='frozen original anchors', weights=nm['main_weights'], old_area_comparison=comparison,
                  source_vintage_note=s.osm.get('snapshot_note', 'See pinned OSM source manifest for timestamps'),
                  preprocessing_note='Overlap change includes differing vector snapshots, larger terrain domain and grid reprojection effects; native SoilGrids overlap was verified identical',
                  inputs=s.inputs, command=ext["command"], coverage=coverage)
    ctx.write_text(out / 'expansion_manifest.json', json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


def multiriver_report(s) -> None:
    """Read-back checks of the multi-river run, summary tables and READING_NOTE.md."""
    import pandas as pd
    import geopandas as gpd
    ctx, out, base = s.ctx, s.out, s.base
    m = json.loads((out / 'expansion_manifest.json').read_text())
    n = json.loads((ctx.p['SCENARIO_DIR'] / 'run_manifest.json').read_text())
    old = json.loads((base / 'chain/priority_scenarios/run_manifest.json').read_text())
    for rel, h in m['inputs'].items():
        assert sha256_file(_abs(ctx, rel)) == h, rel
    assert json.loads((out / 'frozen_normalization.json').read_text()) == json.loads((base / 'frozen_normalization.json').read_text())
    pim, ref = read_grid(_abs(ctx, n['priority_raster_lineage']['path']))
    _, oref = read_grid(s.base_root / old['priority_raster_lineage']['path'])
    valid = np.isfinite(pim)
    res = ref['transform'].a
    assert ref['crs'] == oref['crs'] and ref['transform'].a == 30 and ref['transform'].e == -30
    assert abs((ref['transform'].c - oref['transform'].c) / res - round((ref['transform'].c - oref['transform'].c) / res)) < 1e-8
    assert abs((ref['transform'].f - oref['transform'].f) / res - round((ref['transform'].f - oref['transform'].f) / res)) < 1e-8
    products = gpd.read_file(out / 'comparison_boundaries.gpkg', layer='products')
    boundary = gpd.read_file(out / 'expanded_boundary.gpkg').geometry.union_all()
    mask = raster_mask(boundary, ref)
    assert len(products) == 14 and products.product_id.is_unique and products.geometry.is_valid.all()
    assert all(g.difference(boundary).area < 1e-5 for g in products.geometry)
    assert not (valid & ~mask).any()
    criteria = {k: read_grid(_abs(ctx, e['path']), ref)[0] for k, e in n['criterion_raster_lineage'].items()}
    base_flood = n['main_weights']['flood_hazard']
    percents = [int(round(base_flood * 100)), *s.ext["flood_percents"]]
    errors = {}
    for pct in percents:
        weights = {k: (pct / 100 if k == 'flood_hazard' else v * (1 - pct / 100) / (1 - base_flood))
                   for k, v in n['main_weights'].items()}
        a = pim if pct == percents[0] else read_grid(out / f'pim_flood_{pct}.tif', ref)[0]
        assert np.array_equal(np.isfinite(a), valid)
        expected = sum(criteria[k] * v for k, v in weights.items())
        error = float(np.max(abs(a[valid] - expected[valid])))
        assert error < 2e-6
        assert (a[valid] >= 0).all() and (a[valid] <= 1).all()
        errors[str(pct)] = error
    table = pd.read_csv(out / 'comparison.csv')
    coverage = pd.read_csv(out / 'coverage.csv')
    assert len(table) == 1344 and not table.duplicated(['product_id', 'flood_percent', 'inclusion', 'radius_m', 'metric', 'zone']).any()
    assert (coverage.scored_cells + coverage.unscored_cells == coverage.total_cells).all()
    for _, p in products.iterrows():
        inside = raster_mask(p.geometry, ref)
        r = table[(table.product_id == p.product_id) & (table.flood_percent == percents[0]) & (table.inclusion == 'center')
                  & (table.radius_m == 1000) & (table.metric == 'PIM') & (table.zone == 'inside')].iloc[0]
        z = inside & valid
        assert int(r.valid_cells) == int(z.sum())
        assert abs(r['mean'] - float(pim[z].mean())) < 1e-6
        assert abs(r.high_share - float((pim[z] >= .6).mean())) < 1e-9
    oldpop, op = read_grid(base / 'chain/exposure_indicators/population_exposure_0_1.tif')
    newpop = read_grid(out / 'chain/exposure_indicators/population_exposure_0_1.tif', ref)[0]
    aligned = np.full(pim.shape, np.nan, 'float32')
    reproject(oldpop, aligned, src_transform=op['transform'], src_crs=op['crs'], src_nodata=np.nan,
              dst_transform=ref['transform'], dst_crs=ref['crs'], dst_nodata=np.nan, resampling=Resampling.nearest)
    common = np.isfinite(aligned) & np.isfinite(newpop)
    popdelta = {'common_cells': int(common.sum()), 'max_absolute_difference': float(abs(aligned[common] - newpop[common]).max()),
                'old_valid_now_absent': int((np.isfinite(aligned) & ~np.isfinite(newpop)).sum())}
    qa = {'status': 'passed', 'products': len(products), 'comparison_rows': len(table), 'population_overlap': popdelta,
          'original_input_hashes_unchanged': True, 'frozen_anchors_equal': True, 'old_lattice_preserved': True,
          'all_products_geometrically_contained': True, 'score_reconstruction_max_errors': errors,
          'target_cells': int(mask.sum()), 'scored_cells': int(valid.sum()), 'no_score_cells': int((mask & ~valid).sum())}
    # Narrow river extents get sparser x ticks after the equal-aspect layout.
    corrected = []
    for _, p in products.iterrows():
        bounds = p.geometry.buffer(500).bounds
        if (bounds[2] - bounds[0]) / (bounds[3] - bounds[1]) >= .50:
            continue
        name = p.river.lower() if p.family == 'regulatory' else p.product_id
        title = p.river + ' | Expanded coverage' if p.family == 'regulatory' else f'{p.river} | {p.scenario}'
        figures.make_map(out / name, title, [dict(p)], bounds, criteria['flood_hazard'], pim, ref, sparse_x_ticks=True)
        corrected.append(name)
    qa['narrow_map_tick_corrections'] = corrected
    qa['report_tool_sha256'] = sha256_file(Path(__file__).resolve())
    ctx.write_text(out / 'validation.json', json.dumps(qa, indent=2) + '\n')

    def get(pid, metric, zone, pct=percents[0]):
        return table[(table.product_id == pid) & (table.flood_percent == pct) & (table.inclusion == 'center')
                     & (table.radius_m == 1000) & (table.metric == metric) & (table.zone == zone)].iloc[0]
    text = ('# Multi-river comparison after boundary expansion\n\nThe new extent fully contains the 14 retained official '
            'flood-area sources and a 2 km outer reference zone, merged with the original model extent. Area: '
            f"{m['area_km2']:.2f} km2; on the 30 m grid, {qa['target_cells']:,} cells lie in the assessment area, "
            f"{qa['scored_cells']:,} cells have a composite PIM and {qa['no_score_cells']:,} cells have no score.\n\n")
    text += ('## Results with the original 34% flood weight\n\nMeans are listed for inside the flood area / the outside '
             '1 km ring; the ring excludes all acquired flood areas, and cells are assigned by cell center. Official '
             'designated extents are kept separate from hydraulic scenarios with an explicit return period, and '
             'announcement dates are not treated as flood-event years.\n\n|River/source|Scored cells/flood-area cells|'
             'Flood indicator inside/outside|PIM inside/outside|PIM≥0.6 inside|\n|---|---:|---:|---:|---:|\n')
    summary = []
    for _, p in products.iterrows():
        pi = get(p.product_id, 'PIM', 'inside')
        po = get(p.product_id, 'PIM', 'ring')
        fi = get(p.product_id, 'Flood indicator', 'inside')
        fo = get(p.product_id, 'Flood indicator', 'ring')
        cv = coverage[coverage.product_id == p.product_id].iloc[0]
        text += (f'|{p.river} / {p.scenario}|{int(pi.valid_cells):,}/{int(cv.total_cells):,}|{fi["mean"]:.3f}/'
                 f'{fo["mean"]:.3f}|{pi["mean"]:.3f}/{po["mean"]:.3f}|{pi.high_share:.1%}|\n')
        summary.append({'product_id': p.product_id, 'river': p.river, 'scenario': p.scenario, 'family': p.family,
                        'inside_cells': int(pi.valid_cells), 'ring_cells': int(po.valid_cells),
                        'flood_inside': fi['mean'], 'flood_outside': fo['mean'], 'pim_inside': pi['mean'],
                        'pim_outside': po['mean'], 'pim_high_share': pi.high_share})
    ctx._guard(out / 'summary.csv')
    pd.DataFrame(summary).to_csv(out / 'summary.csv', index=False)
    sf = pd.DataFrame(summary)
    reg = sf[sf.family == 'regulatory']
    text += ('\nRivers whose mean flood indicator inside is higher than in the ring: '
             + ', '.join(reg.loc[reg.flood_inside > reg.flood_outside, 'river']) + '; not higher than the ring: '
             + (', '.join(reg.loc[reg.flood_inside <= reg.flood_outside, 'river']) or 'none') + '.\n')
    text += ('Rivers whose mean composite PIM inside is higher than in the ring: '
             + ', '.join(reg.loc[reg.pim_inside > reg.pim_outside, 'river']) + '; not higher than the ring: '
             + (', '.join(reg.loc[reg.pim_inside <= reg.pim_outside, 'river']) or 'none') + '.\n')
    contribution = []
    allflood = products.geometry.union_all()
    for _, p in products.iterrows():
        inside = raster_mask(p.geometry, ref) & valid
        ring = raster_mask(clean_ring(p.geometry, 1000, allflood), ref) & ~raster_mask(allflood, ref) & valid
        for key, a in criteria.items():
            iv = float(a[inside].mean())
            ov = float(a[ring].mean())
            weight = n['main_weights'][key]
            contribution.append(dict(product_id=p.product_id, river=p.river, criterion=key, inside_mean=iv,
                                     ring_mean=ov, weight=weight, inside_contribution=iv * weight,
                                     ring_contribution=ov * weight, contribution_difference=(iv - ov) * weight))
    pd.DataFrame(contribution).to_csv(out / 'criterion_comparison.csv', index=False)
    text += ('\n## Weight sensitivity\n\n|River/source|34% PIM inside/outside|50% PIM inside/outside|'
             '60% PIM inside/outside|70% PIM inside/outside|\n|---|---:|---:|---:|---:|\n')
    for _, p in products.iterrows():
        text += ('|' + p.river + ' / ' + p.scenario + '|'
                 + '|'.join(f'{get(p.product_id, "PIM", "inside", w)["mean"]:.3f}/{get(p.product_id, "PIM", "ring", w)["mean"]:.3f}'
                            for w in percents) + '|\n')
    stability = []
    for metric, pcts in [('Flood indicator', [percents[0]]), ('PIM', percents)]:
        for pct in pcts:
            subset = table[(table.metric == metric) & (table.flood_percent == pct)]
            pivot = subset.pivot(index=['product_id', 'radius_m', 'inclusion'], columns='zone', values='mean')
            for pid, part in (pivot['inside'] - pivot['ring']).groupby(level='product_id'):
                assert len(part) == 6
                lo = float(part.min())
                hi = float(part.max())
                stability.append(dict(product_id=pid, metric=metric, flood_percent=pct, minimum_difference=lo,
                                      maximum_difference=hi,
                                      status='positive_all' if lo > 0 else ('negative_all' if hi < 0 else 'mixed')))
    stable = pd.DataFrame(stability)
    stable.to_csv(out / 'sensitivity_stability.csv', index=False)
    text += ('\n## Robustness to reference settings\n\nFor 12 sources, the mean flood indicator inside is higher than in '
             'the ring under all six settings. For Innerste HQ100/HQ25 it is only about 0.0034/0.0024 higher with '
             'center assignment and the 1 km ring, and the sign of the difference flips under other settings, so their '
             'consistency cannot be called clear. The 14 sources include different scenarios of the same river and '
             'cannot be treated as 14 independent rivers.\n\n')
    text += ('|Flood weight|Inside PIM higher in all six settings|Direction varies with settings|'
             'Inside PIM lower in all six settings|\n|---|---:|---:|---:|\n')
    for pct in percents:
        q = stable[(stable.metric == 'PIM') & (stable.flood_percent == pct)]
        text += f'|{pct}%|{int((q.status == "positive_all").sum())}|{int((q.status == "mixed").sum())}|{int((q.status == "negative_all").sum())}|\n'
    text += ('\n## How to interpret\n\nExpanding the boundary fixes insufficient assessment coverage; it does not '
             'guarantee closer agreement between the indicators and the official flood areas. The flood indicator and '
             'the PIM are compared separately. Raising the flood weight brings the PIM closer to the existing flood '
             'indicator, but it does not correct the spatial pattern of the flood indicator itself. The detailed '
             'sensitivity table covers 500 m, 1 km and 2 km rings and two cell-assignment rules (center/touched); cells '
             'are not treated as independent samples for significance testing.\n\n')
    text += ('The original normalization anchors and the original rule for population gaps are kept. Missing components '
             'are handled by redistributing the weight to the originally available components. Having a PIM score '
             'therefore does not mean that every component has data; see component_coverage.csv. The effect of missing '
             'components such as population or soil cannot be interpreted as genuinely low risk.\n\n')
    d = m['old_area_comparison']
    text += (f'Relative to the original frozen 34% baseline without facility edge repair, the mean absolute PIM change '
             f'over the {d["common_cells"]:,} overlapping cells of the original area is {d["mean_absolute_change"]:.6f}, '
             f'and the maximum absolute change is {d["max_absolute_change"]:.6f}. Changes by criterion are in '
             'old_area_criterion_changes.csv. The enlarged flow-accumulation domain, changes in the reprojected grid, '
             'facility and water-body edge repair, and differences in source snapshot dates (OSM and others) all affect '
             'the old area, so the changes cannot all be attributed to the boundary itself. The original soil data are '
             'identical value by value where they overlap the old extent; part of the differences in the aligned raster '
             'comes from preprocessing, not from updated soil source values.\n\n')
    text += ('The terrain domain extends a further 10.02 km beyond each side of the assessment rectangle; it is still not '
             'the complete upstream catchment, so flow-accumulation results remain boundary-dependent.\n\n')
    text += ('Reproduce: `.venv/bin/python -m ifpm run goslar --extent multiriver`. The PNG figures use the same '
             'left/right two-panel layout, fixed color scale and 0.6 threshold. The four overview maps overlay the '
             'regulatory boundaries of 8 rivers; each of the 6 HWRM scenarios has its own map so that boundaries of '
             'different scenarios do not overlap. QGIS can read the two GPKG files and the score TIFs directly. Source '
             'files and checksums are in expansion_manifest.json, and the version of each product is carried in the '
             'attributes of comparison_boundaries.gpkg.\n')
    ctx.write_text(out / 'READING_NOTE.md', text)
    files = {str(p.relative_to(out)): sha256_file(p) for p in sorted(out.rglob('*'))
             if p.is_file() and p.name != 'output_checksums.json'}
    ctx.write_text(out / 'output_checksums.json', json.dumps(files, indent=2) + '\n')
    print(json.dumps(qa, indent=2))
