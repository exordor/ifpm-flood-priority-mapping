#!/usr/bin/env python3

"""Build the July 18 boss-facing process figure and mentor message draft.

Split out of ``plot_july18_integrated_priority_board.py`` so that script holds
only its single responsibility (the integrated priority board). This script
holds the two non-map deliverables that accompany the board:

- a short data-analysis process figure for the boss (goal header + 6 steps);
- a one-paragraph mentor message draft.

Both reuse the same output directory as the board so the 7/18 pack stays in
one place.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = [
    ROOT / "outputs/zimbabwe_peru_prototype_comparison/july18_boss_process_figure.png",
    ROOT / "outputs/zimbabwe_peru_prototype_comparison/july18_boss_process_figure.pdf",
    ROOT / "outputs/zimbabwe_peru_prototype_comparison/july18_boss_process_caption.md",
    ROOT / "outputs/zimbabwe_peru_prototype_comparison/july18_mentor_message_draft.txt",
]
OUT_DIR = ROOT / "outputs/zimbabwe_peru_prototype_comparison"


def plot_boss_process() -> None:
    fig, ax = plt.subplots(figsize=(8.6, 10.0))
    ax.set_axis_off()

    ax.add_patch(Rectangle((0.08, 0.885), 0.84, 0.09, facecolor="#264653", edgecolor="none"))
    ax.text(
        0.5, 0.93,
        "Goal: identify flood-priority drivers\nin two prototype catchments",
        ha="center", va="center", fontsize=13, fontweight="bold", color="white",
    )
    ax.text(
        0.5, 0.865,
        "Zimbabwe Upper Mzingwane prototype vs Peru engineering pilot",
        ha="center", va="center", fontsize=10.5, color="0.25",
    )

    steps = [
        ("1. Data inputs", "DEM, rivers, land cover, mining evidence, exposure, rainfall"),
        ("2. Common grid", "clip to each catchment, align raster grid, check NoData"),
        ("3. 0-1 criteria", "standardize each evidence layer with documented direction"),
        ("4. Scenario weights", "apply candidate AHP-style weights and sensitivity runs"),
        ("5. Priority outputs", "map priority score, stable hotspots, and dominant driver"),
        ("6. Mentor review", "check criteria, data gaps, Peru site, and Zimbabwe ASM request"),
    ]
    x, width, height = 0.08, 0.84, 0.095
    y0, gap = 0.75, 0.035
    for idx, (title, body) in enumerate(steps):
        y = y0 - idx * (height + gap)
        ax.add_patch(Rectangle((x, y), width, height, facecolor="#F7F7F5", edgecolor="0.72", linewidth=1.0))
        ax.add_patch(Rectangle((x, y), 0.012, height, facecolor="#2A9D8F", edgecolor="none"))
        ax.text(x + 0.035, y + height * 0.65, title, fontsize=12.2, fontweight="bold", ha="left", va="center")
        ax.text(x + 0.035, y + height * 0.32, body, fontsize=10.3, ha="left", va="center", color="0.25")
        if idx < len(steps) - 1:
            ax.annotate(
                "",
                xy=(x + width / 2, y - gap + 0.006),
                xytext=(x + width / 2, y),
                arrowprops={"arrowstyle": "->", "linewidth": 1.35, "color": "0.35"},
            )

    ax.text(
        0.08, 0.035,
        "Status: prototype / sensitivity scenario. This process explains map drivers; it is not a final flood-risk claim.",
        fontsize=9.5, color="0.25",
    )
    fig.savefig(OUT_DIR / "july18_boss_process_figure.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT_DIR / "july18_boss_process_figure.pdf", dpi=300, bbox_inches="tight")
    plt.close(fig)


def write_boss_process_caption(path: Path) -> None:
    lines = [
        "# Caption",
        "",
        "Fig. X. Data-analysis process for the 18 July mentor/boss preview. "
        "The workflow starts with existing GIS and rainfall inputs, prepares each prototype "
        "catchment on its own common grid, converts the evidence layers into 0-1 criteria, "
        "runs candidate weight scenarios, and produces priority maps, hotspot-frequency maps, "
        "and dominant-driver maps for mentor review.",
        "",
        "Status: prototype / sensitivity scenario. The figure explains the current workflow and "
        "data-request logic; it is not a final flood-risk model, not final AHP approval, and not "
        "a final Zimbabwe-Peru thesis comparison.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_mentor_message(path: Path) -> None:
    message = """Hi Supervisor, I prepared the pixel-colouring comparison for the Zimbabwe and Peru prototype sites.

Each pixel now shows which criterion is driving the prototype priority score most.

In this sensitivity run, Zimbabwe is mostly rainfall-driven, while Peru is mostly driven by flood conditioning factors.

This is not a final flood-risk map. I see it as a way to check the method and decide what data we still need before your trip.

The main data gaps are:
Zimbabwe ASM / mining mapping,
observed flood-impact evidence,
and confirmation whether the Peru pilot site is acceptable or should be replaced.
"""
    path.write_text(message, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plot_boss_process()
    write_boss_process_caption(OUT_DIR / "july18_boss_process_caption.md")
    write_mentor_message(OUT_DIR / "july18_mentor_message_draft.txt")
    print(f"Wrote July 18 boss figure + mentor message to {OUT_DIR}")


if __name__ == "__main__":
    main()
