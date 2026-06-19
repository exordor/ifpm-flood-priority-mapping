#!/usr/bin/env python3
"""Plot the exploratory R-factor method comparison board.

Local TOOLING script. Produces a mentor-facing board comparing four literature-based R-factor
methods against the measured Zimbabwe R-factor range, to support the R-method decision. The
headline message (driven by the data): all three literature-correct methods over-estimate the
Zimbabwe measured R by 3-9x, indicating the US/Morocco-calibrated relations are not transferable
to semi-arid Zimbabwe.

Usage:
    .venv/bin/python bin/plot_rfactor_exploration_board.py
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/rfactor_method_exploration_diagnostics.json"
RASTER_DIR = ROOT / "outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/rasters"
OUT_DIR = ROOT / "outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration"
BOARD_PNG = OUT_DIR / "mentor_rfactor_exploration_board.png"
BOARD_PDF = OUT_DIR / "mentor_rfactor_exploration_board.pdf"
CAPTION_MD = OUT_DIR / "mentor_rfactor_exploration_caption.md"

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 9.5,
        "axes.titlesize": 10.5,
        "axes.labelsize": 9,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)

METHOD_ORDER = [
    "method_A_corrected_arnoldus",
    "method_B_rf_f_correct",
    "method_C_rf_p_correct",
    "method_D_old_wrong",
]
SHORT_LABELS = {
    "method_A_corrected_arnoldus": "A: Corrected Arnoldus\n(Nakil & Khire 2023)",
    "method_B_rf_f_correct": "B: RF F-based correct\n(Eq 13/14, F=MFI)",
    "method_C_rf_p_correct": "C: RF P-based correct\n(Eq 11/12, P=P_annual)",
    "method_D_old_wrong": "D: OLD V1 method\n(WRONG, reference)",
}


def read_array(path: Path):
    with rasterio.open(path) as ds:
        a = ds.read(1).astype("float64")
        a[a == ds.nodata] = np.nan
        return a, ds


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(DIAG) as f:
        d = json.load(f)

    r_means = {mid: d["methods"][mid]["r_zonal_MJ_mm_ha_h_yr"]["mean"] for mid in METHOD_ORDER}
    anchor = d["zimbabwe_measured_r_anchor"]
    zim_low, zim_high = anchor["southern_africa_semi_arid_lowlands_range"]
    epworth = anchor["epworth_harare_1984_2000"]

    fig = plt.figure(figsize=(14, 9), constrained_layout=True)
    gs = fig.add_gridspec(2, 4, height_ratios=[1.15, 1])

    # --- Top: bar chart of R zonal means vs measured Zimbabwe range ---
    ax = fig.add_subplot(gs[0, :])
    x = np.arange(len(METHOD_ORDER))
    vals = [r_means[mid] for mid in METHOD_ORDER]
    colors = ["#4575b4", "#4575b4", "#4575b4", "#d73027"]  # literature methods blue, old-wrong red
    bars = ax.bar(x, vals, color=colors, edgecolor="#333", linewidth=0.6)
    # measured range band
    ax.axhspan(zim_low, zim_high, color="#fee08b", alpha=0.5, zorder=0,
               label=f"Semi-arid measured range ({zim_low:.0f}-{zim_high:.0f})")
    ax.axhline(epworth, color="#d73027", linestyle="--", linewidth=1.4,
               label=f"Epworth Zimbabwe measured ({epworth:.0f})")
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT_LABELS[mid] for mid in METHOD_ORDER], fontsize=8)
    ax.set_ylabel("R-factor zonal mean\n(MJ mm ha$^{-1}$ h$^{-1}$ yr$^{-1}$)")
    ax.set_title("(a) R-factor by method vs measured Zimbabwe range\nAll three literature-correct methods over-estimate by 3-9x", pad=8)
    for xi, v in zip(x, vals):
        ax.text(xi, v + max(vals) * 0.012, f"{v:.0f}", ha="center", va="bottom", fontsize=9, weight="bold")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
    ax.set_ylim(0, max(vals) * 1.15)
    ax.grid(axis="y", alpha=0.2)

    # --- Bottom: four R rasters (0.05 deg) ---
    for i, mid in enumerate(METHOD_ORDER):
        ax = fig.add_subplot(gs[1, i])
        arr, src = read_array(RASTER_DIR / f"{mid}_0p05deg.tif")
        im = ax.imshow(arr, cmap="viridis", origin="upper",
                       extent=[src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top])
        ax.set_title(f"({chr(98 + i)}) {SHORT_LABELS[mid].split(':')[0]} mean={r_means[mid]:.0f}",
                     fontsize=8.5)
        ax.set_xlabel("lon" if i == 0 else "")
        ax.set_ylabel("lat" if i == 0 else "")
        fig.colorbar(im, ax=ax, shrink=0.8, label="R")

    fig.suptitle(
        "Exploratory R-factor method comparison for semi-arid Zimbabwe\n"
        "EXPLORATORY - informs the R-method decision; not a validated result",
        fontsize=12.5, weight="bold", y=1.0,
    )

    caveat = (
        "Methods A/B/C are literature-CORRECT forms (verified against Renard & Freimund 1994 and "
        "Nakil & Khire 2023). Method D is the old V1 method (P-based coeffs on MFI, invented break "
        "at 80) kept only as a reference baseline.   "
        f"Measured Zimbabwe R (Epworth/Harare RUSLE) ~{epworth:.0f}; semi-arid lowlands {zim_low:.0f}-{zim_high:.0f}.   "
        "All three correct methods give R~{:.0f}-{:.0f}, far above measured; only the WRONG method "
        "({:.0f}) is near the range. Conclusion: the US/Morocco-calibrated relations are NOT "
        "transferable to semi-arid Zimbabwe; a region-appropriate R method is needed.".format(
            r_means["method_C_rf_p_correct"], r_means["method_B_rf_f_correct"], r_means["method_D_old_wrong"]
        )
    )
    fig.text(0.5, -0.02, caveat, ha="center", va="top", fontsize=7.8, style="italic", color="#333")

    fig.savefig(BOARD_PNG)
    fig.savefig(BOARD_PDF)
    plt.close(fig)
    print(f"wrote {BOARD_PNG}")
    print(f"wrote {BOARD_PDF}")

    CAPTION_MD.write_text(
        f"# Exploratory R-factor method comparison\n\n"
        f"Date: {date.today().isoformat()}\n\n"
        f"**Status: EXPLORATORY - informs the mentor R-method decision; not a validated result.**\n\n"
        f"After the integrity audit found the V1 R-factor used wrong coefficients on MFI with an "
        f"invented break, this board compares four literature-based R methods on the same V1 CHIRPS "
        f"inputs, against MEASURED Zimbabwe R-factor values.\n\n"
        f"**Key finding:** all three literature-CORRECT methods (A: corrected Arnoldus {r_means['method_A_corrected_arnoldus']:.0f}; "
        f"B: RF F-based {r_means['method_B_rf_f_correct']:.0f}; C: RF P-based {r_means['method_C_rf_p_correct']:.0f}) "
        f"over-estimate the measured Zimbabwe R ({epworth:.0f} at Epworth/Harare; {zim_low:.0f}-{zim_high:.0f} "
        f"semi-arid range) by 3-9x. Only the OLD WRONG V1 method ({r_means['method_D_old_wrong']:.0f}) falls near the "
        f"measured range - and only because its errors happened to cancel the over-estimation.\n\n"
        f"**Implication:** the Renard-Freimund (US-calibrated) and Arnoldus (Morocco-calibrated) "
        f"relations are NOT transferable to semi-arid Zimbabwe. The project needs a region-"
        f"appropriate R-factor method - candidates include a Zimbabwe/southern-Africa-calibrated "
        f"R-P or R-MFI regression, direct EI30 computation from sub-daily CHIRPS if available, or "
        f"adoption of a published regional R value. This is the decision to put to the mentor.\n\n"
        f"**Sources:** Renard & Freimund 1994 (J. Hydrology 157); Nakil & Khire 2023 (Catena "
        f"systematic review); Epworth Zimbabwe RUSLE (MDPI Sustainability 12:8531).\n",
        encoding="utf-8",
    )
    print(f"wrote {CAPTION_MD}")


if __name__ == "__main__":
    main()
