"""Canonical numeric standardization for the IFPM processing scripts.

The active root-pipeline scripts use a small number of intentionally different
scaling contracts.  They live here so that the mathematical implementation is
not copied into individual criteria, scenario, or presentation scripts:

* :func:`percentile_minmax` is the 2--98 percentile clip/min--max transform
  used by raster criteria and terrain/hydrology candidates.
* :func:`robust_upper_scale` is the optional log1p + upper-percentile transform
  used for population/building exposure.
* :func:`positive_density_scale` preserves real zero in focal change density
  while scaling only positive signal.
* :func:`ensure_unit_interval` is a compatibility transform for legacy layers
  that are either already 0--1 or still in a positive absolute range.  It is
  deliberately separate from percentile standardization because it does not
  infer distributional clip bounds.

All functions preserve finite-value masks as NaN by default.  Callers that
need a GeoTIFF NoData sentinel can request it explicitly.  The module imports
NumPy lazily so lightweight scripts can import the shared package without
requiring the GIS runtime at import time.
"""

from __future__ import annotations

from typing import Any


DEFAULT_NODATA = -9999.0


def _np():
    """Load NumPy only when a standardization operation is requested."""
    try:
        import numpy as np

        return np
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            "numpy is required for IFPM standardization. Install it in .venv."
        ) from exc


def _valid_mask(data: Any, mask: Any = None, nodata: float | None = None):
    """Build a finite, optional boundary, optional-NoData mask."""
    np = _np()
    array = np.asarray(data)
    valid = np.isfinite(array)
    if nodata is not None and not (isinstance(nodata, float) and np.isnan(nodata)):
        valid &= array != nodata
    if mask is not None:
        boundary = np.asarray(mask, dtype=bool)
        if boundary.shape != array.shape:
            raise ValueError(
                f"mask shape {boundary.shape} does not match data shape {array.shape}"
            )
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
    """Clip valid values to percentile bounds and scale them to ``[0, 1]``.

    Parameters are intentionally explicit because the same transform is used
    for flood, sediment, exposure, and hydrology indicators.  ``mask`` limits
    the statistics and output to the study-area support.  ``nodata`` excludes
    an input sentinel from the statistics; finite values are always required.
    ``clip_low``/``clip_high`` allow a caller to freeze one or both bounds while
    retaining the shared implementation.  ``constant_policy="expand"`` is the
    legacy proximity behaviour for constant rasters (``high = low + 1``), while
    ``constant_policy="zeros"`` preserves callers that intentionally emit zero
    for a constant valid support.

    Returns
    -------
    (array, low, high)
        A float32 array and the actual bounds used.  Invalid/outside cells are
        filled with ``output_nodata`` (NaN by default).
    """
    np = _np()
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
    # Promote the selected values before arithmetic.  Without this, NumPy can
    # perform the subtraction in float32 and turn the upper clipped endpoint
    # into 0.99999988 (or 1.0000001), which is undesirable for an advertised
    # closed [0, 1] score range and brittle in exact diagnostics.
    scaled = (np.clip(array[valid].astype("float64", copy=False), low, high) - low) / (high - low)
    if invert:
        scaled = 1.0 - scaled
    output[valid] = np.clip(scaled, 0.0, 1.0).astype("float32")
    return output, low, high


def percentile_minmax_array(
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
):
    """Array-only convenience wrapper around :func:`percentile_minmax`."""
    output, _, _ = percentile_minmax(
        data,
        mask,
        nodata=nodata,
        invert=invert,
        p_low=p_low,
        p_high=p_high,
        output_nodata=output_nodata,
        constant_policy=constant_policy,
        clip_low=clip_low,
        clip_high=clip_high,
    )
    return output


def standardize(
    data: Any,
    nodata: float = DEFAULT_NODATA,
    invert: bool = False,
    p_low: float = 2.0,
    p_high: float = 98.0,
) -> tuple[Any, float, float]:
    """Backwards-compatible full-array 2--98 standardization.

    This preserves the historical ``_lib.ifpm_tools.standardize`` signature
    while delegating all numeric work to :func:`percentile_minmax`.
    """
    return percentile_minmax(
        data,
        nodata=nodata,
        invert=invert,
        p_low=p_low,
        p_high=p_high,
        output_nodata=nodata,
    )


def robust_upper_scale(
    values: Any,
    *,
    upper_percentile: float = 99.0,
    log1p: bool = False,
) -> tuple[Any, float]:
    """Scale finite non-negative values by a robust upper percentile.

    Negative finite inputs are clipped to zero, matching the exposure-indicator
    contract.  If all transformed values are zero, the result is zero on the
    finite support and the returned scale is ``0`` rather than fabricating a
    positive range.
    """
    np = _np()
    if not 0.0 < upper_percentile <= 100.0:
        raise ValueError("upper_percentile must be in (0, 100]")
    source = np.asarray(values, dtype="float32")
    finite = np.isfinite(source)
    result = np.full(source.shape, np.nan, dtype="float32")
    if not finite.any():
        raise ValueError("cannot normalize a raster with no finite values")

    transformed = np.maximum(source[finite], 0.0).astype("float64")
    if log1p:
        transformed = np.log1p(transformed)
    upper = float(np.percentile(transformed, upper_percentile))
    if not np.isfinite(upper) or upper <= 0.0:
        result[finite] = 0.0
        return result, 0.0
    result[finite] = np.clip(transformed / upper, 0.0, 1.0).astype("float32")
    return result, upper


def positive_density_scale(
    density: Any,
    percentile: float = 95.0,
    *,
    epsilon: float = 1e-7,
) -> tuple[Any, float]:
    """Scale positive focal density while preserving true zero and NaN."""
    np = _np()
    if not 0.0 < percentile <= 100.0:
        raise ValueError("percentile must be in (0, 100]")
    source = np.asarray(density)
    finite = np.isfinite(source)
    signal = finite & (source > epsilon)
    positive = source[signal]
    result = np.full(source.shape, np.nan, dtype="float32")
    result[finite] = 0.0
    if positive.size == 0:
        return result, 0.0
    scale = float(np.percentile(positive, percentile))
    if scale <= 0.0:
        return result, scale
    result[signal] = np.clip(source[signal] / scale, 0.0, 1.0).astype("float32")
    return result, scale


def ensure_unit_interval(data: Any, name: str | None = None):
    """Keep a criterion in ``[0, 1]`` or max-scale a positive absolute layer.

    This is a compatibility conversion for legacy inputs and display helpers,
    not a replacement for :func:`percentile_minmax`.  ``name`` is used only to
    make existing error messages actionable.
    """
    np = _np()
    source = np.asarray(data)
    values = source[np.isfinite(source)]
    label = f": {name}" if name else ""
    if values.size == 0:
        raise ValueError(f"empty criterion{label}")
    if float(values.max()) <= 1.000001 and float(values.min()) >= -0.000001:
        return np.clip(source, 0.0, 1.0).astype("float32")
    max_value = float(values.max())
    if max_value <= 0.0:
        raise ValueError(f"non-positive criterion range{label}")
    return np.clip(source / max_value, 0.0, 1.0).astype("float32")


__all__ = [
    "DEFAULT_NODATA",
    "percentile_minmax",
    "percentile_minmax_array",
    "standardize",
    "robust_upper_scale",
    "positive_density_scale",
    "ensure_unit_interval",
]
