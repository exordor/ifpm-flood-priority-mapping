#!/usr/bin/env python3
"""Plot the exploratory R-factor method comparison board.

Local TOOLING script. Produces a mentor-facing board comparing source-traced R-factor methods
against Zimbabwe reference values, to support the R-method decision. The output is exploratory:
it shows that the candidate methods split into low and high value families, but it does not prove
which family is correct for the V1 catchment.

Usage:
    .venv/bin/python bin/visualize/plot_rfactor_exploration_board.py
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DIAG = ROOT / "outputs/chirps_v3_zimbabwe_prototype/r_factor_exploration/rfactor_method_exploration_diagnostics.json"
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
    "method_E_hurni",
    "method_F_epworth_merritt",
]
SHORT_LABELS = {
    "method_A_corrected_arnoldus": "A: Arnoldus-family\n(Nakil-Khire MFI law)",
    "method_B_rf_f_correct": "B: RF F-based correct\n(Eq 13/14, F=MFI)",
    "method_C_rf_p_correct": "C: RF P-based correct\n(Eq 11/12, P=P_annual)",
    "method_D_old_wrong": "D: OLD V1 method\n(WRONG, reference)",
    "method_E_hurni": "E: Hurni 1985\n(regional R-P, Ethiopia)",
    "method_F_epworth_merritt": "F: Epworth/Merritt\n(R=38.5+0.35M, Harare)",
}
# Elwell/Stocking 1976 Zimbabwe-native value (from Renard-Freimund 1994 table, ~400 per 100mm):
# at V1 P~583, R~2000. Shown as a reference line, not a method (it is a lookup table, not an eqn,
# and reaches us via secondary reproduction).
ELWELL_REF_R = 2000.0


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(DIAG) as f:
        d = json.load(f)

    r_means = {mid: d["methods"][mid]["r_zonal_MJ_mm_ha_h_yr"]["mean"] for mid in METHOD_ORDER}
    anchor = d["zimbabwe_measured_r_anchor"]
    zim_low, zim_high = anchor["southern_africa_semi_arid_lowlands_range"]
    epworth = anchor["epworth_harare_1984_2000"]

    fig, ax = plt.subplots(figsize=(11.8, 5.8), constrained_layout=False)
    fig.subplots_adjust(left=0.09, right=0.985, top=0.78, bottom=0.24)

    # Bar chart of R zonal means vs measured Zimbabwe range.
    x = np.arange(len(METHOD_ORDER))
    vals = [r_means[mid] for mid in METHOD_ORDER]
    # literature/regional methods blue, old-wrong method D red
    colors = ["#d73027" if mid == "method_D_old_wrong" else "#4575b4" for mid in METHOD_ORDER]
    bars = ax.bar(x, vals, color=colors, edgecolor="#333", linewidth=0.6)
    # measured range band
    ax.axhspan(zim_low, zim_high, color="#fee08b", alpha=0.5, zorder=0,
               label=f"Semi-arid measured range ({zim_low:.0f}-{zim_high:.0f})")
    ax.axhline(epworth, color="#d73027", linestyle="--", linewidth=1.4,
               label=f"Epworth Zimbabwe measured ({epworth:.0f})")
    ax.axhline(ELWELL_REF_R, color="#1a9850", linestyle=":", linewidth=1.6,
               label=f"Elwell/Stocking 1976 Zimbabwe-native (~{ELWELL_REF_R:.0f})")
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT_LABELS[mid] for mid in METHOD_ORDER], fontsize=8)
    ax.set_ylabel("R-factor zonal mean\n(MJ mm ha$^{-1}$ h$^{-1}$ yr$^{-1}$)")
    ax.set_title("R-factor by method vs measured Zimbabwe reference values", pad=10)
    for xi, v in zip(x, vals):
        ax.text(xi, v + max(vals) * 0.012, f"{v:.0f}", ha="center", va="bottom", fontsize=9, weight="bold")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
    ax.set_ylim(0, max(vals) * 1.15)
    ax.grid(axis="y", alpha=0.2)

    fig.suptitle(
        "Exploratory R-factor method comparison\n"
        "Two R families emerge; mentor decision needed",
        fontsize=13.0, weight="bold", y=0.955,
    )

    fig.text(
        0.5,
        0.065,
        "Exploratory only. See caption for source notes, units caveat, and method limitations.",
        ha="center",
        fontsize=8.2,
        style="italic",
        color="#333",
    )

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
        f"invented break, this board compares five R methods on the same V1 CHIRPS inputs, against "
        f"MEASURED Zimbabwe R-factor values.\n\n"
        f"**Key finding:** the source-traced transfer formulas split into two value families. "
        f"The high-family methods (A: Arnoldus-family / Nakil-Khire "
        f"{r_means['method_A_corrected_arnoldus']:.0f}; B: RF F-based {r_means['method_B_rf_f_correct']:.0f}; "
        f"C: RF P-based {r_means['method_C_rf_p_correct']:.0f}) are well above the lower Zimbabwe "
        f"reference values ({epworth:.0f} at Epworth/Harare; {zim_low:.0f}-{zim_high:.0f} semi-arid range). "
        f"The OLD WRONG V1 method (D, {r_means['method_D_old_wrong']:.0f}) falls near the range only "
        f"because its errors cancelled. Method E (Hurni 1985 regional R-P regression) gives "
        f"R~{r_means['method_E_hurni']:.0f}, very close to the Epworth measured {epworth:.0f}.\n\n"
        f"**Implication:** this board is evidence for a method decision, not a validated R result. "
        f"A regional R-P method, a Zimbabwe-specific calibration, or direct EI30 from sub-daily "
        f"rainfall are candidate routes to discuss with the mentor. Hurni and Epworth carry unit "
        f"and transferability caveats even though their magnitudes are close to the lower reference "
        f"range.\n\n"
        f"**Sources:** Renard & Freimund 1994 (J. Hydrology 157); Nakil & Khire 2023 (Catena "
        f"systematic review); Hurni 1985 (Erosion-Productivity-Conservation Systems in Ethiopia); "
        f"Epworth Zimbabwe RUSLE (MDPI Sustainability 12:8531).\n",
        encoding="utf-8",
    )
    print(f"wrote {CAPTION_MD}")


if __name__ == "__main__":
    main()
