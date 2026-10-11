"""Weighted combination of criteria into the PIM score, and score classes.

Pure NumPy, so it can be tested without rasterio. The functions are copied from the
old chains (bin/factors/run_goslar_pim_chain.py, run_secocha_pim_chain.py and
bin/_lib/goslar_comparison.py) without changing the arithmetic: float32 accumulation in
the same order, the same NaN handling and the same clipping.
"""

from __future__ import annotations

import numpy as np

# Equal-interval PIM classes used in all reports (upper edge slightly above 1 so 1.0 counts).
CLASS_EDGES = [0, .2, .4, .6, .8, 1.000001]
CLASS_LABELS = ["very_low", "low", "moderate", "high", "very_high"]
HIGH_THRESHOLD = .6


def weighted_average(parts: list[tuple[np.ndarray, float]], mask: np.ndarray) -> np.ndarray:
    """Weighted mean of the components that are valid in each cell (weights renormalized).

    Used inside a criterion (e.g. FH from rainfall, TWI and drainage) in the Goslar chain.
    Cells outside ``mask`` or with no valid component are NaN.
    """
    numerator = np.zeros(mask.shape, dtype="float32")
    denominator = np.zeros(mask.shape, dtype="float32")
    for layer, weight in parts:
        valid = mask & np.isfinite(layer)
        numerator[valid] += layer[valid] * weight
        denominator[valid] += weight
    out = np.divide(numerator, denominator, out=np.full(mask.shape, np.nan, dtype="float32"),
                    where=denominator > 0)
    out[~mask] = np.nan
    return out.astype("float32")


def strict_sum(layers: dict[str, np.ndarray], weights: dict[str, float], mask: np.ndarray) -> np.ndarray:
    """Weighted sum only where every component is valid (Secocha: no renormalization)."""
    common = mask.copy()
    for name in weights:
        common &= np.isfinite(layers[name])
    out = np.full(mask.shape, np.nan, dtype="float32")
    out[common] = sum(layers[name][common] * weight for name, weight in weights.items())
    return np.clip(out, 0, 1)


def combine_common_support(criteria: dict, weights: dict, mask: np.ndarray):
    """PIM = weighted sum of the five criteria where all five are valid.

    Returns the clipped score, the available main weight per cell and the number of
    valid criteria per cell (the last two are written as coverage rasters).
    """
    first = next(iter(criteria.values()))
    numerator = np.zeros(first.shape, dtype="float32")
    available = np.zeros(first.shape, dtype="float32")
    count = np.zeros(first.shape, dtype="uint8")
    common = np.ones(first.shape, dtype=bool)
    for name, weight in weights.items():
        layer = criteria[name]
        valid = np.isfinite(layer)
        numerator[valid] += layer[valid] * weight
        available[valid] += weight
        count[valid] += 1
        common &= valid
    score = np.full(first.shape, np.nan, dtype="float32")
    score[common] = numerator[common]
    return np.clip(score, 0.0, 1.0).astype("float32"), available, count


def weights_at(base: dict, flood: float) -> dict:
    """Main weights with the flood weight set to ``flood``; the others keep their ratios."""
    if not 0 <= flood <= 1 or not np.isclose(sum(base.values()), 1):
        raise ValueError('Invalid weights')
    if any(w < 0 for w in base.values()) or not 0 < base['flood_hazard'] < 1:
        raise ValueError('Invalid baseline')
    return {k: flood if k == 'flood_hazard' else w * (1-flood)/(1-base['flood_hazard'])
            for k, w in base.items()}


def score_at(criteria: dict, weights: dict, support: np.ndarray) -> np.ndarray:
    """PIM for alternative weights on a fixed support; NoData is never filled with zero."""
    valid = support & np.all(np.isfinite(np.stack(list(criteria.values()))), axis=0)
    score = np.full(support.shape, np.nan)
    score[valid] = sum(criteria[k][valid] * w for k, w in weights.items())
    # Classify the same representable values that are written to the GeoTIFF.
    return score.astype('float32').astype('float64')


def summarize(arr: np.ndarray, zone: np.ndarray) -> dict:
    """Cell count, mean, median, share >= 0.6 and class counts of ``arr`` inside ``zone``."""
    vals = arr[zone & np.isfinite(arr)]
    counts = np.histogram(vals, bins=CLASS_EDGES)[0]
    return {'valid_cells': int(vals.size), 'mean': float(vals.mean()) if vals.size else None,
            'median': float(np.median(vals)) if vals.size else None,
            'high_share': float((vals >= HIGH_THRESHOLD).mean()) if vals.size else None,
            'class_counts': counts.tolist()}


def class_table(pim: np.ndarray, valid: np.ndarray, cell_area_km2: float) -> dict:
    """Cells, area and share of valid cells per PIM class (Secocha validation report)."""
    classes = {}
    bounds = [(label, CLASS_EDGES[i], CLASS_EDGES[i + 1]) for i, label in enumerate(CLASS_LABELS)]
    for label, low, high in bounds:
        count = int((valid & (pim >= low) & (pim < high)).sum())
        classes[label] = {"cells": count, "area_km2": count * cell_area_km2,
                          "fraction_of_valid": count / int(valid.sum())}
    return classes
