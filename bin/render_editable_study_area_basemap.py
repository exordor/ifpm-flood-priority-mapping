#!/usr/bin/env python3
"""Render the label-free regional locator basemap used on the study-area slide.

All human-readable labels are intentionally omitted so they can be added as
editable PowerPoint text boxes. The map is presentation context only.
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator


ROOT = Path(__file__).resolve().parents[1]
COUNTRIES_ZIP = ROOT / "data/raw/naturalearth_admin_boundaries/ne_10m_admin_0_countries.zip"
PERU_STUDY = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
ZIMBABWE_STUDY = ROOT / "outputs/v1_working_boundary/v1_working_boundary.gpkg"
OUTPUT = ROOT / "outputs/presentation_assets/study_areas_regional_basemap_no_text.png"


def main() -> None:
    required = [COUNTRIES_ZIP, PERU_STUDY, ZIMBABWE_STUDY]
    missing = [path for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing study-area map input(s): " + ", ".join(map(str, missing)))

    countries = gpd.read_file(f"zip://{COUNTRIES_ZIP}").to_crs(4326)
    name_col = "ADMIN" if "ADMIN" in countries.columns else "NAME"
    peru = countries[countries[name_col].eq("Peru")]
    zimbabwe = countries[countries[name_col].eq("Zimbabwe")]
    peru_study = gpd.read_file(PERU_STUDY, layer="peru_pilot_boundary").to_crs(4326)
    zimbabwe_study = gpd.read_file(
        ZIMBABWE_STUDY,
        layer="v1_working_boundary",
    ).to_crs(4326)

    if peru.empty or zimbabwe.empty:
        raise RuntimeError("Natural Earth country selection failed for Peru or Zimbabwe")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(13.2, 3.0), dpi=200, facecolor="white")
    ax = fig.add_axes([0.055, 0.105, 0.93, 0.86])
    ax.set_facecolor("#EAF3F8")

    countries.plot(ax=ax, color="#F2F2EF", edgecolor="#FFFFFF", linewidth=0.35, zorder=1)
    peru.plot(ax=ax, color="#F7C9A8", edgecolor="#D95F02", linewidth=1.8, zorder=3)
    zimbabwe.plot(ax=ax, color="#BFE7E1", edgecolor="#118C7E", linewidth=1.8, zorder=3)

    # Study-area geometry is visible but deliberately unlabelled.
    peru_study.plot(ax=ax, facecolor="#FFFFFF", edgecolor="#D95F02", linewidth=1.5, zorder=5)
    zimbabwe_study.plot(ax=ax, facecolor="#FFFFFF", edgecolor="#118C7E", linewidth=1.5, zorder=5)

    ax.set_xlim(-92, 44)
    ax.set_ylim(-36.5, 2.5)
    ax.set_aspect("auto")
    ax.xaxis.set_major_locator(FixedLocator([-80, -60, -40, -20, 0, 20, 40]))
    ax.yaxis.set_major_locator(FixedLocator([0, -10, -20, -30]))
    ax.grid(True, color="#FFFFFF", linewidth=0.8, alpha=0.95, zorder=2)

    # Keep the scientific-map frame and ticks, but no embedded text.
    ax.tick_params(
        axis="both",
        which="major",
        labelbottom=False,
        labelleft=False,
        length=4,
        width=0.7,
        color="#5C6670",
        direction="out",
    )
    for spine in ax.spines.values():
        spine.set_color("#5C6670")
        spine.set_linewidth(0.8)

    fig.savefig(OUTPUT, dpi=200, facecolor="white", transparent=False)
    plt.close(fig)
    print(OUTPUT)


if __name__ == "__main__":
    main()
