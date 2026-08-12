"""IFPM bin/ shared tooling package.

Re-exports the public helpers from ifpm_tools so scripts can write
``from _lib.ifpm_tools import write_raster, raster_stats`` etc. after adding
``bin/`` to sys.path (the pipeline orchestrator handles this).
"""

from .ifpm_tools import (  # noqa: F401
    ROOT,
    NODATA,
    load_boundary,
    load_boundary_df,
    write_raster,
    raster_stats,
    standardize,
    run_grid_gate,
    write_manifest_csv,
)
from .standardization import (  # noqa: F401
    DEFAULT_NODATA,
    ensure_unit_interval,
    percentile_minmax,
    percentile_minmax_array,
    positive_density_scale,
    robust_upper_scale,
)
