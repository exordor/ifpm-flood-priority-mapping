"""Percentile normalization, plain or with frozen (baseline) anchors.

Pure NumPy: no GIS imports, so this module can be tested without rasterio.

- ``percentile_minmax`` is the 2-98 percentile clip then min-max to [0, 1] used for
  every percentile-scaled criterion (copied unchanged from bin/_lib/standardization.py).
- ``fit`` / ``apply`` freeze the clip bounds of a baseline run and reuse them on a larger
  extent (copied unchanged from bin/_lib/fixed_scale.py).
- ``Normalizer`` is what the chain stages call. It counts the calls in each stage so a
  frozen anchor can be looked up by the key ``"<stage>:<call index>"``, the key format of
  the existing frozen_normalization.json files.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def _valid_mask(data: Any, mask: Any = None, nodata: float | None = None):
    """Build a finite, optional boundary, optional-NoData mask."""
    array = np.asarray(data)
    valid = np.isfinite(array)
    if nodata is not None and not (isinstance(nodata, float) and np.isnan(nodata)):
        valid &= array != nodata
    if mask is not None:
        boundary = np.asarray(mask, dtype=bool)
        if boundary.shape != array.shape:
            raise ValueError(f"mask shape {boundary.shape} does not match data shape {array.shape}")
        valid &= boundary
    return array, valid


def percentile_minmax(
    data: Any,
    mask: Any = None,
    *,
    nodata: float | None = None,
    invert: bool = False,
    p_low: float = 2.0,
    p_high: float = 98.0,
    output_nodata: float | None = None,
    constant_policy: str = "error",
    clip_low: float | None = None,
    clip_high: float | None = None,
) -> tuple[Any, float, float]:
    """Clip valid values to percentile bounds and scale them to [0, 1].

    ``mask`` limits the statistics and the output to the study-area support.
    ``clip_low``/``clip_high`` freeze one or both bounds. For a constant raster,
    ``constant_policy`` is "error", "expand" (high = low + 1) or "zeros".
    Returns a float32 array (invalid cells NaN or ``output_nodata``) and the bounds used.
    """
    array, valid = _valid_mask(data, mask=mask, nodata=nodata)
    if not (0.0 <= p_low < p_high <= 100.0):
        raise ValueError(f"percentiles must satisfy 0 <= low < high <= 100: {p_low}, {p_high}")
    if constant_policy not in {"error", "expand", "zeros"}:
        raise ValueError("constant_policy must be 'error', 'expand', or 'zeros'")

    values = array[valid].astype("float64", copy=False)
    if values.size == 0:
        raise ValueError("cannot standardize without finite valid cells")

    low = float(clip_low) if clip_low is not None else float(np.percentile(values, p_low))
    high = float(clip_high) if clip_high is not None else float(np.percentile(values, p_high))
    if not np.isfinite(low) or not np.isfinite(high):
        raise ValueError(f"invalid standardization bounds: low={low}, high={high}")
    if high <= low:
        if constant_policy == "expand":
            high = low + 1.0
        elif constant_policy == "zeros":
            fill_value = float("nan") if output_nodata is None else output_nodata
            output = np.full(array.shape, fill_value, dtype="float32")
            output[valid] = 0.0
            return output, low, high
        else:
            raise ValueError(f"invalid standardization bounds: low={low}, high={high}")

    fill_value = float("nan") if output_nodata is None else output_nodata
    output = np.full(array.shape, fill_value, dtype="float32")
    # Scale in float64 so the clipped upper endpoint is exactly 1.0 after the cast.
    scaled = (np.clip(array[valid].astype("float64", copy=False), low, high) - low) / (high - low)
    if invert:
        scaled = 1.0 - scaled
    output[valid] = np.clip(scaled, 0.0, 1.0).astype("float32")
    return output, low, high


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
    """Return JSON-safe anchors fitted on the baseline valid cells only."""
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
    """Apply stored anchors without refitting; invalid/outside cells stay NaN."""
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


class Normalizer:
    """The normalization the chain stages call: ``normalize(data, mask, **options)``.

    Modes:
      "fit"    - plain percentile_minmax on the current data (the basin chains);
      "record" - fit anchors, keep them under "<stage>:<index>", return the anchored result
                 (used to capture the basin anchors before an extent run);
      "frozen" - look the anchors up and apply them; the options passed by the stage are
                 ignored because the stored anchors carry them (the extent runs).
    """

    def __init__(self, mode: str = "fit", anchors: dict | None = None):
        if mode not in {"fit", "record", "frozen"}:
            raise ValueError(f"unknown normalizer mode: {mode}")
        self.mode = mode
        self.anchors = {} if anchors is None else anchors
        self.stage = ""
        self.index = 0

    def start(self, stage: str) -> None:
        """Begin a stage: anchor keys count from 0 again."""
        self.stage = stage
        self.index = 0

    def __call__(self, data, mask=None, **options):
        key = f"{self.stage}:{self.index}"
        self.index += 1
        if self.mode == "fit":
            return percentile_minmax(data, mask, **options)
        if self.mode == "record":
            self.anchors[key] = fit(data, mask, **options)
        if key not in self.anchors:
            raise KeyError(f"no frozen anchor for {key}")
        parameters = self.anchors[key]
        return apply(data, parameters, mask), parameters["clip_low"], parameters["clip_high"]
