"""Fit baseline-only percentile anchors and apply them to expanded support.

Local experiment tooling. Fit on the original *raw* layer and valid baseline
support, then persist the returned parameters in the experiment manifest. The
same units and preprocessing must be used for expanded inputs. Application
never estimates percentiles from the expanded area.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from _lib.standardization import percentile_minmax


def fit(
    data: Any,
    mask: Any = None,
    *,
    nodata: float | None = None,
    invert: bool = False,
    p_low: float = 2.0,
    p_high: float = 98.0,
    constant_policy: str = "error",
) -> dict:
    """Return JSON-safe anchors fitted exclusively on baseline valid cells.

    ``zeros`` deliberately returns zero even when inverted, matching the
    canonical legacy constant-layer contract. ``expand`` uses high=low+1.
    Input NoData is passed separately on application because expanded files
    can use a different sentinel.
    """
    normalized, low, high = percentile_minmax(
        data, mask, nodata=nodata, invert=invert, p_low=p_low,
        p_high=p_high, constant_policy=constant_policy,
    )
    return {
        "method": "baseline_frozen_percentile_minmax",
        "clip_low": low,
        "clip_high": high,
        "p_low": float(p_low),
        "p_high": float(p_high),
        "invert": bool(invert),
        "constant_policy": constant_policy,
        "baseline_valid_cells": int(np.isfinite(normalized).sum()),
    }


def apply(
    data: Any,
    parameters: dict,
    mask: Any = None,
    *,
    nodata: float | None = None,
    output_nodata: float | None = None,
) -> np.ndarray:
    """Apply stored anchors without refitting; preserve invalid/outside cells.

    Missing bounds fail explicitly instead of silently calculating new ones.
    An entirely invalid expanded support raises the canonical empty-data error.
    """
    if parameters.get("method") != "baseline_frozen_percentile_minmax":
        raise ValueError("unsupported frozen normalization method")
    low = float(parameters["clip_low"])
    high = float(parameters["clip_high"])
    if not np.isfinite(low) or not np.isfinite(high) or high < low:
        raise ValueError("frozen bounds must be finite and ordered")
    normalized, _, _ = percentile_minmax(
        data, mask, nodata=nodata,
        invert=parameters["invert"],
        p_low=parameters["p_low"], p_high=parameters["p_high"],
        constant_policy=parameters["constant_policy"],
        clip_low=low, clip_high=high, output_nodata=output_nodata,
    )
    return normalized
