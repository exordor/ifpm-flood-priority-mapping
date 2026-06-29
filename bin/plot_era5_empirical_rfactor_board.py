#!/usr/bin/env python3
"""Plot the empirical ERA5 R-factor against the two literature R-families.

Local TOOLING script. Produces a single board showing the empirical EI30 R (computed from ERA5
hourly) alongside the HIGH and LOW literature families, to visualise which family the data supports.

Usage:
    .venv/bin/python bin/plot_era5_empirical_rfactor_board.py
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "outputs/v1_usle_soil_loss/rfactor_empirical_era5/era5_empirical_rfactor_diagnostics.json"
OUT_DIR = ROOT / "outputs/v1_usle_soil_loss/rfactor_empirical_era5"
BOARD_PNG = OUT_DIR / "mentor_era5_empirical_rfactor_board.png"
BOARD_PDF = OUT_DIR / "mentor_era5_empirical_rfactor_board.pdf"
CAPTION_MD = OUT_DIR / "mentor_era5_empirical_rfactor_caption.md"

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(DIAG) as f:
        d = json.load(f)

    pts = d["points"]
    pt_ids = [p["point_id"] for p in pts]
    r_ws = [p["wischmeier"]["mean_annual_R_I60lowerbound"] for p in pts]
    r_bf = [p["brown_foster"]["mean_annual_R_I60lowerbound"] for p in pts]
    mean_ws = d["spatial_mean_R"]["wischmeier_I60lowerbound"]
    mean_bf = d["spatial_mean_R"]["brown_foster_I60lowerbound"]
    mean_ws_i30 = d["spatial_mean_R"]["wischmeier_I30est"]
    mean_bf_i30 = d["spatial_mean_R"]["brown_foster_I30est"]

    # Literature family bands (for reference lines/bands)
    low_lo, low_hi = 240, 320     # Hurni/Epworth
    high_lo, high_hi = 1380, 3719  # RF/Arnoldus/Elwell

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.8, 5.6), constrained_layout=False)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.80, bottom=0.20, wspace=0.18)

    # --- Left: per-point empirical R, with family bands ---
    x = np.arange(len(pt_ids))
    w = 0.38
    ax1.bar(x - w/2, r_ws, w, color="#4575b4", label="Wischmeier-Smith KE (I60 lower bound)")
    ax1.bar(x + w/2, r_bf, w, color="#91bfdb", label="Brown-Foster KE (I60 lower bound)")
    ax1.axhspan(low_lo, low_hi, color="#fee08b", alpha=0.45,
                label=f"LOW family (Hurni/Epworth) {low_lo}-{low_hi}")
    ax1.axhspan(high_lo, high_hi, color="#fc8d59", alpha=0.25,
                label=f"HIGH family (RF/Arnoldus/Elwell) {high_lo}-{high_hi}")
    ax1.set_xticks(x)
    ax1.set_xticklabels(pt_ids)
    ax1.set_xlabel("V1 catchment point")
    ax1.set_ylabel("Empirical annual R (MJ mm ha$^{-1}$ h$^{-1}$ yr$^{-1}$)")
    ax1.set_title("(a) ERA5 R by point vs literature families", fontsize=10.5, pad=8)
    ax1.legend(loc="upper left", fontsize=7.5, framealpha=0.9)
    ax1.grid(axis="y", alpha=0.2)

    # --- Right: summary - mean empirical vs family midpoints ---
    methods = ["LOW family\n(Hurni/Epworth)", "Empirical ERA5\n(Wisch, I60 LB)",
               "Empirical ERA5\n(BF, I60 LB)", "Empirical ERA5\n(Wisch, I30 est)",
               "Empirical ERA5\n(BF, I30 est)", "HIGH family\n(RF/Arnoldus/Elwell)"]
    # use family midpoints for the bands
    vals = [np.mean([low_lo, low_hi]), mean_ws, mean_bf, mean_ws_i30, mean_bf_i30,
            np.mean([high_lo, high_hi])]
    colors = ["#fee08b", "#4575b4", "#91bfdb", "#4575b4", "#91bfdb", "#fc8d59"]
    bars = ax2.bar(range(len(methods)), vals, color=colors, edgecolor="#333", linewidth=0.6)
    ax2.set_xticks(range(len(methods)))
    ax2.set_xticklabels(methods, fontsize=7.5)
    ax2.set_ylabel("Annual R (MJ mm ha$^{-1}$ h$^{-1}$ yr$^{-1}$)")
    ax2.set_title("(b) Mean R comparison", fontsize=10.5, pad=8)
    for xi, v in zip(range(len(methods)), vals):
        ax2.text(xi, v + max(vals)*0.015, f"{v:.0f}", ha="center", va="bottom", fontsize=8, weight="bold")
    ax2.set_ylim(0, max(vals)*1.12)
    ax2.grid(axis="y", alpha=0.2)

    fig.suptitle(
        "Exploratory ERA5 R-factor check\nERA5 lower-bound is near the lower R range; high formulas are much larger",
        fontsize=13.0, weight="bold", y=0.96,
    )
    fig.text(0.5, 0.045, "ERA5 hourly is a lower bound on true 30-min EI30. See caption for source and caveats.", ha="center", fontsize=8.0, style="italic", color="#333")

    fig.savefig(BOARD_PNG)
    fig.savefig(BOARD_PDF)
    plt.close(fig)
    print(f"wrote {BOARD_PNG}")
    print(f"wrote {BOARD_PDF}")

    CAPTION_MD.write_text(
        f"# Empirical ERA5 R-factor vs literature families\n\n"
        f"Date: {date.today().isoformat()}\n\n"
        f"**Status: EXPLORATORY - ERA5 hourly gives a lower bound on true 30-min EI30; not a validated R.**\n\n"
        f"An empirical USLE/RUSLE R-factor was computed from ERA5 hourly precipitation (open-meteo, "
        f"7 points across V1, {d['year_range'][0]}-{d['year_range'][1]}) using the standard EI30 "
        f"algorithm with Wischmeier-Smith and Brown-Foster kinetic-energy equations.\n\n"
        f"**Result:** empirical R (spatial mean) = {mean_ws:.0f} (Wischmeier, I60 LB), {mean_bf:.0f} "
        f"(Brown-Foster, I60 LB), {mean_ws_i30:.0f}/{mean_bf_i30:.0f} (I30 estimate). This sits in/near "
        f"the LOW literature family ({low_lo}-{low_hi}, Hurni/Epworth) and is ~4x BELOW the HIGH "
        f"family ({high_lo}-{high_hi}, RF/Arnoldus/Elwell-Zimbabwe-native).\n\n"
        f"**Interpretation:** the empirical data SUPPORTS the LOW family and contradicts the HIGH "
        f"family (including the Zimbabwe-native Elwell relation). Since ERA5 hourly is a lower bound "
        f"on true EI30, the real R is likely somewhat above the empirical values but still well below "
        f"the HIGH family. This is the first non-circular evidence in the family comparison (unlike "
        f"the Epworth 329, which was computed from the LOW-family equation itself).\n\n"
        f"**Caveats:** ERA5 reanalysis can under-estimate convective intensity; hourly != 30-min; "
        f"points are samples not a full grid. This is a family-arbitration result, not a validated R.\n\n"
        f"**Sources:** Wischmeier & Smith 1978; Brown & Foster 1987; ERA5 via open-meteo.\n",
        encoding="utf-8",
    )
    print(f"wrote {CAPTION_MD}")


if __name__ == "__main__":
    main()
