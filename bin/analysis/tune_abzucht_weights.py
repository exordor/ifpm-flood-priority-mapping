#!/usr/bin/env python3
"""TOOLING: bounded, reproducible HQ100-guided weight sensitivity experiment."""
import csv
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import box

from compare_abzucht_hq100 import COLORS, LABELS, digest, read_grid

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'outputs/goslar_abzucht_display_rectangle_v1/frozen_scale_v1'
OUT = BASE.parent / 'weight_sensitivity_v1'
COMMAND = '.venv/bin/python bin/analysis/tune_abzucht_weights.py'
COARSE = [.34, .45, .55, .65, .75, .80]
CAP = .80  # Candidate policy: retain at least 20% for the other criteria.


def weights_at(base, flood):
    if not 0 <= flood <= 1 or not np.isclose(sum(base.values()), 1):
        raise ValueError('Invalid weights')
    if any(w < 0 for w in base.values()) or not 0 < base['flood_hazard'] < 1:
        raise ValueError('Invalid baseline')
    return {k: flood if k == 'flood_hazard' else w * (1-flood)/(1-base['flood_hazard'])
            for k, w in base.items()}


def score_at(criteria, weights, support):
    # Fixed five-criterion support even for the 100% endpoint; never zero-fill NoData.
    valid = support & np.all(np.isfinite(np.stack(list(criteria.values()))), axis=0)
    score = np.full(support.shape, np.nan)
    score[valid] = sum(criteria[k][valid] * w for k, w in weights.items())
    # Classify the same representable values that will be persisted in GeoTIFF.
    return score.astype('float32').astype('float64')


def metrics(score, inside, ring, threshold=.6):
    a, b = score[inside], score[ring]
    if not a.size or not b.size or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Empty or changing comparison support')
    ih, oh = float((a >= threshold).mean()), float((b >= threshold).mean())
    return dict(inside_mean=float(a.mean()), ring_mean=float(b.mean()),
                mean_gap=float(a.mean()-b.mean()), inside_high_share=ih,
                ring_high_share=oh, high_share_gap=ih-oh)


def best(rows):
    return max(rows, key=lambda r: (r['high_share_gap'], -r['flood_weight']))


def main():
    global OUT
    destination = OUT
    inputs = {}
    def remember(path):
        inputs[str(path.relative_to(ROOT))] = digest(path)
        return path
    m = json.loads(remember(BASE/'chain/priority_scenarios/run_manifest.json').read_text())
    weights = m['main_weights']
    if not np.isclose(weights['flood_hazard'], COARSE[0]):
        raise ValueError('Coarse baseline differs from source weights')
    lineage = m['priority_raster_lineage']
    p = remember(ROOT/lineage['path'])
    if digest(p) != lineage['sha256']:
        raise ValueError('Baseline hash mismatch')
    baseline, profile = read_grid(p)
    criteria = {}
    for k, item in m['criterion_raster_lineage'].items():
        p = remember(ROOT/item['path'])
        if digest(p) != item['sha256']:
            raise ValueError('Criterion hash mismatch: '+k)
        criteria[k] = read_grid(p, profile)[0]
        finite = criteria[k][np.isfinite(criteria[k])]
        if np.any((finite < 0) | (finite > 1)):
            raise ValueError('Criterion outside fixed 0-1 scale')
    support = np.isfinite(baseline) & np.all(np.isfinite(np.stack(list(criteria.values()))), axis=0)
    replay = score_at(criteria, weights, support)
    error = float(np.max(np.abs(replay[support]-baseline[support])))
    if error > 1e-5 or not np.array_equal(support, np.isfinite(baseline)):
        raise ValueError('Baseline reconstruction/support failure')
    hq = gpd.read_file(remember(BASE/'overlay/abzucht_hq100.gpkg')).to_crs(profile['crs'])
    if hq.empty or not hq.is_valid.all() or profile['crs'].to_epsg() != 32632:
        raise ValueError('Expected valid HQ100 geometry and UTM32N')
    geom = hq.geometry.union_all()
    bounds = json.loads(remember(BASE/'expansion_manifest.json').read_text())['display_rectangle']['bounds_utm32n']
    grid_box = box(*rasterio.transform.array_bounds(profile['height'], profile['width'], profile['transform']))
    if geom.buffer(1000).difference(grid_box).area > .01:
        raise ValueError('Full comparison ring extends outside raster grid')
    def mask(g):
        return geometry_mask([g], out_shape=baseline.shape, transform=profile['transform'], invert=True)
    raw_inside = mask(geom)
    raw_ring = mask(geom.buffer(1000)) & ~raw_inside
    inside, ring = raw_inside & support, raw_ring & support
    rectangle = mask(box(*bounds)) & support
    coverage = {name: dict(total_cells=int(z.sum()), scored_cells=int((z & support).sum()),
                           nodata_cells=int((z & ~support).sum()))
                for name, z in [('HQ100', raw_inside), ('full_1km_ring', raw_ring), ('rectangle', mask(box(*bounds)))]}
    support_source = json.loads(remember(BASE.parent/'explanation_v1/manifest.json').read_text())
    for name, sha in support_source['inputs'].items():
        if digest(ROOT/name) != sha:
            raise ValueError('Availability evidence changed: '+name)
        inputs[name] = sha
    rows, scores = [], {}
    def evaluate(f, stage):
        f = round(f, 2)
        s = score_at(criteria, weights_at(weights, f), support)
        row = dict(stage=stage, flood_weight=f, **metrics(s, inside, ring))
        rows.append(row)
        scores[f] = s
        return row
    coarse = [evaluate(f, 'coarse') for f in COARSE]
    seed = best(coarse)['flood_weight']
    # Second round: +/- five percentage points around the best coarse candidate.
    fine_values = [round(f/100, 2) for f in range(max(34, round(seed*100)-5), min(80, round(seed*100)+5)+1)]
    for f in fine_values:
        if f not in scores:
            evaluate(f, 'fine')
    selected = best(rows)
    chosen = selected['flood_weight']
    endpoint = evaluate(1., 'endpoint_only')
    # Fresh staging directory: incomplete runs never replace an existing completed run.
    OUT = Path(tempfile.mkdtemp(prefix='.weight_sensitivity_v1_incomplete_', dir=destination.parent))
    def table(name, data):
        with (OUT/name).open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0]))
            writer.writeheader(); writer.writerows(data)
    rows.sort(key=lambda r: r['flood_weight'])
    table('comparison.csv', rows)
    table('weights.csv', [dict(flood_weight=r['flood_weight'], stage=r['stage'],
                              **weights_at(weights, r['flood_weight'])) for r in rows])
    # Threshold sensitivity is reporting only: it cannot choose weights or alter map classes.
    threshold_rows = [dict(flood_weight=r['flood_weight'], threshold=t,
          **metrics(scores[r['flood_weight']], inside, ring, t)) for t in [.5, .6, .7] for r in rows]
    table('threshold_sensitivity.csv', threshold_rows)
    threshold_best = {str(t): best([r for r in threshold_rows if r['threshold']==t and r['flood_weight']<=CAP])
                      for t in [.5,.6,.7]}
    contributions = []
    for f in [COARSE[0], chosen]:
        for k, w in weights_at(weights, f).items():
            contributions.append(dict(flood_weight=f, criterion=k, weight=w,
                inside_contribution=float(criteria[k][inside].mean()*w),
                ring_contribution=float(criteria[k][ring].mean()*w)))
    table('contributions.csv', contributions)
    def raster(name, array, categorical=False):
        pr = profile.copy(); pr.update(count=1, dtype='uint8' if categorical else 'float32',
                                     nodata=255 if categorical else -9999, compress='deflate')
        with rasterio.open(OUT/name, 'w', **pr) as d:
            d.write(np.where(support, array, pr['nodata']).astype(pr['dtype']), 1)
            d.update_tags(claim_level='sensitivity_scenario', boundary_id='goslar_abzucht_display_rectangle_v1',
                          experiment_id='weight_sensitivity_v1', reference_role='HQ100-guided tuning, not independent validation')
    for f, score in scores.items():
        raster(f'priority_fh_{round(f*100):03d}.tif', score)
    raster('change_from_baseline.tif', scores[chosen]-scores[.34])
    stack = np.stack([criteria[k]*w for k,w in weights_at(weights, chosen).items()])
    drivers = np.argmax(np.where(np.isfinite(stack), stack, -np.inf), axis=0)
    raster('dominant_contribution.tif', drivers, True)
    with rasterio.open(OUT/'dominant_contribution.tif','r+') as d:
        d.update_tags(classes=json.dumps({i: LABELS[k] for i,k in enumerate(weights)}))
    t = profile['transform']
    extent = [t.c/1000, (t.c+t.a*baseline.shape[1])/1000,
              (t.f+t.e*baseline.shape[0])/1000, t.f/1000]
    hv = hq.copy(); hv.geometry = hv.geometry.scale(.001, .001, origin=(0,0))
    def draw(ax, a, title, cmap, norm=None, **kw):
        im = ax.imshow(np.ma.masked_invalid(np.where(rectangle, a, np.nan)), extent=extent,
                       cmap=cmap, norm=norm, interpolation='nearest', **kw)
        hv.boundary.plot(ax=ax, color='#1767aa', linewidth=.7)
        ax.set(xlim=(bounds[0]/1000,bounds[2]/1000), ylim=(bounds[1]/1000,bounds[3]/1000),
               xlabel='UTM easting (km)', ylabel='UTM northing (km)', title=title)
        ax.ticklabel_format(useOffset=False, style='plain'); ax.tick_params(labelsize=8)
        return im
    def save(fig, name):
        for fmt in ['png', 'svg', 'pdf']:
            fig.savefig(OUT/f'{name}.{fmt}', dpi=170)
        plt.close(fig)
    fig, axes = plt.subplots(2,3,figsize=(15,9))
    fig.subplots_adjust(top=.84,bottom=.15,hspace=.48,wspace=.25)
    for ax, f in zip(axes.flat, COARSE):
        im=draw(ax,scores[f],f'Flood weight {f:.0%}',ListedColormap(COLORS),BoundaryNorm([0,.2,.4,.6,.8,1.000001],5))
    fig.suptitle('Goslar / Abzucht: increasing flood weight strengthens HQ100 contrast',fontsize=17,y=.97)
    fig.text(.08,.91,'Six comparable scenarios | Other weights reduced proportionally | Fixed inputs, scale and high-score threshold',fontsize=11)
    cax=fig.add_axes([.32,.08,.36,.018]);fig.colorbar(im,cax=cax,orientation='horizontal',ticks=[0,.2,.4,.6,.8,1])
    fig.text(.08,.025,'Blue outline: official HQ100 scenario | Prototype weight comparison; not an observed-flood validation',fontsize=10)
    save(fig,'weight_comparison')
    fig, axes=plt.subplots(1,2,figsize=(12,5))
    fig.subplots_adjust(top=.79,bottom=.20,wspace=.30)
    candidate_rows=[r for r in rows if r['stage']!='endpoint_only']
    x=[100*r['flood_weight'] for r in candidate_rows]
    for key,label in [('inside_high_share','Inside HQ100'),('ring_high_share','Outside, within 1 km')]:
        axes[0].plot(x,[100*r[key] for r in candidate_rows],'o-',label=label)
    axes[0].set(xlabel='Flood weight (%)',ylabel='Cells with score ≥ 0.6 (%)');axes[0].legend()
    axes[1].plot(x,[100*r['high_share_gap'] for r in candidate_rows],'o-',color='#1767aa')
    axes[1].set(xlabel='Flood weight (%)',ylabel='Inside minus outside high share (pp)')
    for ax in axes: ax.axvline(100*chosen,color='#999999',ls='--');ax.grid(alpha=.2)
    fig.suptitle(f'At the fixed 0.6 cutoff: {chosen:.0%} is best within the tested 34-80% range',fontsize=15)
    fig.text(.09,.055,'Selection compares high-score shares, not accuracy. Search capped at 80% to retain 20% for other criteria.',fontsize=10)
    save(fig,'weight_response')
    fig,axes=plt.subplots(1,2,figsize=(13,6))
    fig.subplots_adjust(top=.80,bottom=.24,wspace=.30)
    im=draw(axes[0],scores[chosen]-scores[.34],'Change from current score','RdBu_r',vmin=-.3,vmax=.3)
    driver_colors=['#3274a1','#b88a58','#619853','#9385b8','#b96573']
    draw(axes[1],drivers,'Largest weighted contribution',ListedColormap(driver_colors),BoundaryNorm(np.arange(-.5,5.5),5))
    hv.boundary.plot(ax=axes[1],color='white',linewidth=.8)
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=c,label=LABELS[k]) for c,k in zip(driver_colors,weights)],
               loc='lower center',bbox_to_anchor=(.5,.025),ncol=5,fontsize=9,frameon=False)
    cax=fig.add_axes([.16,.17,.25,.02]);fig.colorbar(im,cax=cax,orientation='horizontal',label='Score change')
    fig.suptitle(f'Goslar / Abzucht: what changes at {chosen:.0%} flood weight',fontsize=17)
    fig.text(.09,.88,'Red: score increases; blue: decreases | HQ100 outline: blue at left, white at right',fontsize=11)
    save(fig,'change_and_drivers')
    remember(Path(__file__));remember(Path(__file__).with_name('compare_abzucht_hq100.py'))
    boundary_note = 'This candidate lies at the search upper bound; no interior optimum has been found yet.' if chosen==CAP else 'This candidate is only the best within the current discrete trials and does not represent the scientific optimum over continuous weights.'
    note=f'''# Goslar / Abzucht weight trials

Direction: the flood weight is raised step by step from 34%, and the other four criteria are scaled down in their original proportions. After two rounds of comparison, at the fixed 0.6 threshold, {chosen:.0%} is the best-performing candidate in this bounded search. {boundary_note}

The baseline, coarse trials and fine trials are in comparison.csv; all weights are in weights.csv. The coarse trials were 34/45/55/65/75/80%; the fine trials were {fine_values}. Candidates are ranked by "high-score share inside HQ100 minus high-score share in the full outer 1 km ring" at the fixed 0.6 threshold, with ties going to the smaller flood weight. The 80% cap is a working assumption that keeps at least 20% for the other indicators, not a scientifically optimal constraint.

The high-score share inside HQ100 rose from {coarse[0]['inside_high_share']:.2%} to {selected['inside_high_share']:.2%}, and in the outer ring from {coarse[0]['ring_high_share']:.2%} to {selected['ring_high_share']:.2%}; the inside-outside gap grew from {100*coarse[0]['high_share_gap']:.2f} to {100*selected['high_share_gap']:.2f} percentage points. Even the pure flood indicator (100%, used only as an endpoint reference) reaches a high-score share inside HQ100 of only {endpoint['inside_high_share']:.2%}, so weight tuning alone cannot make the whole HQ100 area high-scoring.

This round stopped after two bounded rounds of trials. {chosen:.0%} is the flood-dominated candidate for side-by-side comparison with the original 34%; 65% keeps a stronger combined-priority meaning. Moving further toward 100% gradually reduces the PIM to a single flood indicator.

The weight choice depends on the high-score threshold: at threshold 0.5, {threshold_best['0.5']['flood_weight']:.0%} has the largest inside-outside share gap among this round's candidates; at threshold 0.7, the share of HQ100 cells reaching the threshold {'is 0% in all runs' if max(r['inside_high_share'] for r in threshold_rows if r['threshold']==.7 and r['flood_weight']<=CAP)==0 else 'ranges from {:.2%} to {:.2%} across candidates'.format(min(r['inside_high_share'] for r in threshold_rows if r['threshold']==.7 and r['flood_weight']<=CAP),max(r['inside_high_share'] for r in threshold_rows if r['threshold']==.7 and r['flood_weight']<=CAP))}.

Status: sensitivity_scenario. The 0.5/0.7 thresholds serve only as a supplementary-table sensitivity check and do not change this round's ranking or map classes.

The original five indicators, normalization scales, grid and support domain are fixed; the GHSL replacement experiment is not mixed in, and component weights are not changed. The original indicators' limitation of redistributing weights over available components is inherited: a finite combined score does not mean that all soil/population components are present. Coverage and existing component-missingness statistics are in the manifest; NoData is not imputed in this round. The main map shows only the original rectangle, while the statistical ring includes parts outside the rectangle.

Reproduce: `{COMMAND}`. Input hashes, grid, baseline reconstruction, coverage and output reopen checks are all performed in the script. Output rasters, tables, figures and the manifest are in the same directory; the original baseline is unchanged.
'''
    (OUT/'READING_NOTE.md').write_text(note)
    # Reopen every score raster and check persisted values and fixed support.
    for f,s in scores.items():
        persisted,_=read_grid(OUT/f'priority_fh_{round(f*100):03d}.tif',profile)
        if not np.array_equal(np.isfinite(persisted), support) or not np.allclose(persisted[support],s[support],atol=1e-7,rtol=0):
            raise ValueError('Persisted raster mismatch')
        for cutoff in [.5,.6,.7]:
            if metrics(persisted,inside,ring,cutoff) != metrics(s,inside,ring,cutoff):
                raise ValueError('Persisted classification mismatch')
    for name,sha in inputs.items():
        if digest(ROOT/name)!=sha:raise ValueError('Input changed during run')
    manifest=dict(boundary_id='goslar_abzucht_display_rectangle_v1',experiment_id='weight_sensitivity_v1',
      claim_level='sensitivity_scenario',command=COMMAND,baseline='frozen_scale_v1',
      selection=dict(objective='maximize inside-minus-ring high-share at fixed 0.6; ties prefer smaller weight',
                     cap=CAP,cap_reason='candidate policy: retain >=20% non-flood weight',coarse=COARSE,fine=fine_values,
                     selected=chosen,at_search_boundary=chosen==CAP,independent_validation=False),
      weight_source='User-authorized local sensitivity, 2026-09-14; not approved AHP weights',
      ahp_consistency_ratio=None,ahp_note='Direct proportional scenarios; no pairwise matrix constructed',
      criterion_order=list(weights),component_weights=m['component_weights'],
      criterion_semantics={k:LABELS[k] for k in weights},normalization=m['normalization'],
      nodata_policy='fixed five-criterion support; inherit upstream available-component renormalization, no new imputation',
      inherited_component_support=support_source['support'],coverage=coverage,
      grid=dict(crs=str(profile['crs']),transform=list(profile['transform']),width=profile['width'],height=profile['height']),
      baseline_max_error=error,inputs=inputs,
      threshold_sensitivity_best=threshold_best,
      outputs={p.name:digest(p) for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json'})
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if destination.exists():
        backup = destination.with_name(destination.name+'_previous_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        destination.rename(backup)
        try:
            OUT.rename(destination)
        except Exception:
            backup.rename(destination)
            raise
    else:
        OUT.rename(destination)
    OUT = destination
    print(json.dumps(dict(selected=selected,endpoint=endpoint,coverage=coverage,baseline_max_error=error),indent=2))


if __name__=='__main__':
    main()
