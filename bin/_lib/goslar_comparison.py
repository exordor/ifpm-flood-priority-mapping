"""Goslar comparison helpers used by the final multi-river chain.

Moved on 2026-10-11 from diagnostic scripts so that the Goslar full-extent run
(`bin/analysis/run_goslar_multiriver_full.py`) and the multi-river comparison no
longer import one-off diagnostics:

- ``digest``, ``read_grid``, ``summarize``, ``LABELS``, ``COLORS`` from
  ``bin/analysis/compare_abzucht_hq100.py``
- ``representative`` from ``bin/analysis/explain_abzucht_comparison.py`` (removed)
- ``weights_at``, ``score_at`` from ``bin/analysis/tune_abzucht_weights.py`` (removed)
- ``census_grid`` from ``bin/analysis/repair_abzucht_gaps.py`` (removed)
- ``load_module`` (was ``load``) from ``bin/analysis/run_abzucht_expanded.py``

Function bodies are unchanged.
"""
from __future__ import annotations

import hashlib
import importlib.util

import numpy as np

LABELS = {'flood_hazard': 'Flood indicators', 'sediment': 'Erosion factors', 'landuse_asm': 'Land cover', 'environmental': 'Water / ecology', 'socioeconomic': 'Access / exposure'}
COLORS = ['#ffffcc', '#ffeda0', '#feb24c', '#f03b20', '#bd0026']


def load_module(name, path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_grid(path, ref=None):
    import rasterio
    with rasterio.open(path) as ds:
        if ref is not None and (ds.crs != ref['crs'] or ds.transform != ref['transform'] or ds.shape != (ref['height'], ref['width'])):
            raise ValueError(f'Incompatible reference grid: {path.name}')
        arr = ds.read(1, masked=True).astype('float64').filled(np.nan)
        arr[~np.isfinite(arr)] = np.nan
        return arr, ds.profile


def summarize(arr, zone):
    vals = arr[zone & np.isfinite(arr)]
    counts = np.histogram(vals, bins=[0, .2, .4, .6, .8, 1.000001])[0]
    return {'valid_cells': int(vals.size), 'mean': float(vals.mean()) if vals.size else None,
            'median': float(np.median(vals)) if vals.size else None,
            'high_share': float((vals >= .6).mean()) if vals.size else None,
            'class_counts': counts.tolist()}


def representative(mask,score):
    """Nearest median score; ties resolved by distance to candidate centroid."""
    rr,cc=np.where(mask & np.isfinite(score))
    if not len(rr):raise ValueError('No candidate for declared case type')
    vals=score[rr,cc]; diff=np.abs(vals-np.median(vals))
    distance=(rr-rr.mean())**2+(cc-cc.mean())**2
    idx=np.lexsort((cc,rr,distance,diff))[0]
    return int(rr[idx]),int(cc[idx])


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


def census_grid(frame, bounds):
    import pandas as pd
    from rasterio.transform import from_origin
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
