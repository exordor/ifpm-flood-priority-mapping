#!/usr/bin/env python3
"""Build a mentor-review Zimbabwe integrated result board from governed maps."""

from __future__ import annotations

import csv
import hashlib
import os
import sys
from collections import OrderedDict
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "bin/package"))

import build_peru_integrated_briefing_board as ui


CHAIN_ROOT = ROOT / "outputs/zimbabwe_report_figure_chain"
CHAIN = CHAIN_ROOT / "current"
CHAIN_MANIFEST = CHAIN_ROOT / "manifest.csv"
REPORTING = ROOT / "outputs/slide_ready_figures/zimbabwe_reporting_maps"
DATA_STRENGTH = REPORTING / "criterion_data_strength.csv"
RESULT_SUMMARY = REPORTING / "result_summary.csv"
CONTRIBUTION_SUMMARY = REPORTING / "contribution_summary.csv"
BOUNDARY_MANIFEST = ROOT / "outputs/v1_working_boundary/v1_working_boundary_manifest.csv"
OUT_DIR = ROOT / "outputs/zimbabwe_integrated_briefing_board"
OUT_PNG = OUT_DIR / "zimbabwe_integrated_briefing_board.png"
OUT_MANIFEST = OUT_DIR / "manifest.csv"

FIGURES = OrderedDict(
    [
        ("boundary", CHAIN / "01_zimbabwe_study_area.png"),
        ("flood_hazard", CHAIN / "02_zimbabwe_flood_conditioning.png"),
        ("sediment", CHAIN / "03_zimbabwe_sediment.png"),
        ("landuse_asm", CHAIN / "04_zimbabwe_landuse_asm.png"),
        ("environmental", CHAIN / "05_zimbabwe_environmental.png"),
        ("socioeconomic", CHAIN / "06_zimbabwe_socioeconomic.png"),
        ("priority", CHAIN / "08_zimbabwe_priority_mining_population_overlay.png"),
        ("contribution", CHAIN / "09_zimbabwe_weighted_contribution.png"),
    ]
)

INPUTS = [*FIGURES.values(), CHAIN_MANIFEST, DATA_STRENGTH, RESULT_SUMMARY, CONTRIBUTION_SUMMARY, BOUNDARY_MANIFEST]
OUTPUTS = [OUT_PNG, OUT_MANIFEST]

CRITERION_ORDER = ["flood_hazard", "sediment", "landuse_asm", "environmental", "socioeconomic"]
CRITERION_LABELS = {
    "flood_hazard": "Flood conditioning",
    "sediment": "Soil erosion factors",
    "landuse_asm": "Land use / mining reference",
    "environmental": "Environmental context",
    "socioeconomic": "Access exposure",
}
CONTRIBUTION_COLORS = ["#2b83ba", "#d95f0e", "#31a354", "#9e9ac8", "#636363"]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def summary_values() -> dict[str, float]:
    result = {row["metric"]: float(row["value"]) for row in read_csv(RESULT_SUMMARY)}
    contribution = {
        row["criterion"]: float(row["dominant_cell_share_scoreable"])
        for row in read_csv(CONTRIBUTION_SUMMARY)
    }
    boundary = read_csv(BOUNDARY_MANIFEST)[0]
    return {
        "study_area_km2": float(boundary["catchment_area_km2"]),
        "high_area_km2": result["high_class_area_km2"],
        "very_high_area_km2": result["very_high_class_area_km2"],
        "high_share": result["high_class_area_km2"] / result["five_criterion_scored_area_km2"],
        "very_high_share": result["very_high_class_area_km2"] / result["five_criterion_scored_area_km2"],
        "coverage_fraction": result["five_criterion_coverage_fraction"],
        "flood_dominant_share": contribution["flood_hazard"],
    }


def validate_chain() -> None:
    rows = read_csv(CHAIN_MANIFEST)
    packaged = {row["packaged_png"]: row for row in rows}
    for path in FIGURES.values():
        key = rel(path)
        if key not in packaged:
            raise ValueError(f"figure missing from Zimbabwe chain manifest: {key}")
        if sha256(path) != packaged[key]["packaged_png_sha256"]:
            raise ValueError(f"figure hash does not match Zimbabwe chain manifest: {key}")


def load(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def paste_map(canvas: Image.Image, path: Path, box: tuple[int, int, int, int], boundary: bool = False) -> None:
    image = load(path)
    if not boundary:
        image = ui.map_crop(image)
    fitted, position = ui.fit_image(image, box)
    canvas.paste(fitted, position)


def draw_header(draw: ImageDraw.ImageDraw, strength: list[dict[str, str]]) -> None:
    x, y, width, height = ui.PANEL_BOXES["header"]
    draw.text(
        (x, y),
        "Integrated Relative-Priority Index for the Upper Mzingwane Study Area, Zimbabwe",
        font=ui.font(48, bold=True),
        fill=ui.NAVY,
    )
    weights = " | ".join(f"{CRITERION_LABELS[row['criterion']]} {float(row['weight']):.2f}" for row in strength)
    draw.text(
        (x, y + 62),
        f"Matabeleland South | Five-criterion weighted model | Weights: {weights}",
        font=ui.font(25),
        fill=ui.MUTED,
    )
    summary = summary_values()
    takeaway = (
        f"High and Very High classes cover {summary['high_area_km2'] + summary['very_high_area_km2']:.1f} km²; "
        f"flood conditioning is the largest weighted component in {summary['flood_dominant_share']:.1%} "
        "of cells where all five criteria are available."
    )
    ui.draw_wrapped(draw, (x, y + 106), takeaway, ui.font(29, bold=True), ui.GREEN, 2780, 2, line_gap=2)
    status = "RELATIVE PRIORITY | NOT YET VALIDATED AGAINST OBSERVED FLOOD EXTENT OR DAMAGE"
    status_font = ui.font(21, bold=True)
    status_width = int(draw.textlength(status, font=status_font)) + 40
    box = (x + width - status_width, y + 142, x + width, y + height)
    draw.rounded_rectangle(box, radius=8, fill="#FFF3DD", outline="#D39B3A", width=2)
    draw.text((box[0] + 20, box[1] + 11), status, font=status_font, fill=ui.AMBER)


def draw_study_area(canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
    box = ui.PANEL_BOXES["inputs"]
    ui.draw_card(draw, box)
    ui.draw_section_title(draw, box, "1. Study area and research question")
    x, y, width, _ = box
    paste_map(canvas, FIGURES["boundary"], (x + 24, y + 66, width - 48, 500), boundary=True)
    summary = summary_values()
    draw.text((x + 28, y + 574), f"Area: {summary['study_area_km2']:,.0f} km²", font=ui.font(25, bold=True), fill=ui.INK)
    ui.draw_wrapped(
        draw,
        (x + 28, y + 614),
        "HydroBASINS-derived working study area around Esigodini and Mzingwane Dam, north of Gwanda",
        ui.font(21),
        ui.MUTED,
        width - 56,
        3,
        line_gap=3,
    )
    draw.text((x + 28, y + 704), "Why this area matters", font=ui.font(23, bold=True), fill=ui.NAVY)
    statements = (
        "Semi-arid catchment with variable seasonal rainfall",
        "Dense drainage network and erosion-prone terrain",
        "Mineral references, settlements, roads and reservoir infrastructure",
    )
    statement_y = y + 750
    for statement in statements:
        draw.ellipse((x + 30, statement_y + 7, x + 42, statement_y + 19), fill=ui.GREEN)
        ui.draw_wrapped(draw, (x + 58, statement_y), statement, ui.font(20), ui.INK, width - 90, 2)
        statement_y += 48
    draw.rounded_rectangle((x + 28, y + 925, x + width - 28, y + 965), radius=6, fill="#E7EFF7", outline=ui.BLUE, width=2)
    draw.text((x + 44, y + 934), "Where do the five mapped pressures overlap most strongly?", font=ui.font(19, bold=True), fill=ui.NAVY)


def draw_priority(canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
    box = ui.PANEL_BOXES["priority"]
    ui.draw_card(draw, box)
    ui.draw_section_title(draw, box, "2. Priority map with mining and population context", "five relative-priority classes")
    x, y, width, height = box
    image = load(FIGURES["priority"])
    fitted, position = ui.fit_image(image, (x + 24, y + 66, width - 48, height - 86))
    canvas.paste(fitted, position)


def metric_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], value: str, label: str, note: str) -> None:
    ui.draw_metric_card(draw, box, value, label, note)


def draw_findings(canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
    box = ui.PANEL_BOXES["diagnostics"]
    ui.draw_card(draw, box)
    ui.draw_section_title(draw, box, "3. Key findings")
    x, y, width, height = box
    summary = summary_values()
    gap = 12
    inner_x = x + 18
    inner_width = width - 36
    card_width = (inner_width - gap) // 2
    card_height = 126
    metrics = (
        (f"{summary['high_area_km2']:.1f} km²", "High class", f"Score 0.6-0.8; {summary['high_share']:.1%} of represented area"),
        (f"{summary['very_high_area_km2']:.1f} km²", "Very high class", f"Score 0.8-1.0; {summary['very_high_share']:.2%} of represented area"),
        (f"{summary['coverage_fraction']:.1%}", "Map coverage", "Share of the study area represented by all five criteria"),
        (f"{summary['flood_dominant_share']:.1%}", "Flood component", "Largest weighted component; not proof of physical causation"),
    )
    metric_y = y + 68
    for index, metric in enumerate(metrics):
        row, column = divmod(index, 2)
        metric_card(
            draw,
            (inner_x + column * (card_width + gap), metric_y + row * (card_height + gap), card_width, card_height),
            *metric,
        )

    cy = metric_y + 2 * card_height + 2 * gap
    ch = 360
    draw.rounded_rectangle((inner_x, cy, inner_x + inner_width, cy + ch), radius=8, fill=ui.PALE, outline=ui.LINE, width=2)
    draw.text((inner_x + 18, cy + 14), "What shapes the index", font=ui.font(24, bold=True), fill=ui.INK)
    paste_map(canvas, FIGURES["contribution"], (inner_x + 18, cy + 48, 470, ch - 62))
    ui.draw_wrapped(
        draw,
        (inner_x + 520, cy + 72),
        "Flood conditioning dominates most cells in the relative priority map. Soil erosion factors and access exposure shape narrower corridors. Land use / mining rarely becomes the largest component, which points to weak mining evidence rather than proof that mining is unimportant.",
        ui.font(21),
        ui.INK,
        inner_width - 550,
        8,
        line_gap=6,
    )
    legend_x = inner_x + 520
    legend_y = cy + ch - 78
    for index, (name, color) in enumerate(zip(CRITERION_ORDER, CONTRIBUTION_COLORS, strict=True)):
        row, column = divmod(index, 3)
        lx = legend_x + column * 280
        ly = legend_y + row * 30
        draw.rectangle((lx, ly, lx + 20, ly + 20), fill=color, outline=ui.MUTED, width=1)
        draw.text((lx + 28, ly - 2), CRITERION_LABELS[name], font=ui.font(15), fill=ui.MUTED)

    ey = cy + ch + gap
    eh = y + height - ey - 18
    draw.rounded_rectangle((inner_x, ey, inner_x + inner_width, ey + eh), radius=8, fill="#FFF7E8", outline="#D39B3A", width=2)
    draw.text((inner_x + 18, ey + 14), "Evidence limits", font=ui.font(24, bold=True), fill=ui.AMBER)
    ui.draw_wrapped(
        draw,
        (inner_x + 18, ey + 54),
        "The scored road-access indicator does not include population, buildings or infrastructure. WorldPop and mapped mining land-use footprints are shown separately as spatial context and do not change the PIM score. The mining footprints are non-exhaustive and do not identify official titles, ASM status or current operation. No local observed flood extent, damage or affected-population dataset is linked for validation.",
        ui.font(20),
        ui.INK,
        inner_width - 36,
        7,
        line_gap=4,
    )


def draw_criteria(canvas: Image.Image, draw: ImageDraw.ImageDraw, strength: list[dict[str, str]]) -> None:
    box = ui.PANEL_BOXES["criteria"]
    ui.draw_card(draw, box)
    ui.draw_section_title(draw, box, "4. Five criteria and weights", "Darker colors indicate greater relative priority")
    x, y, width, height = box
    gap = 12
    card_width = (width - 32 - gap * 4) // 5
    by_name = {row["criterion"]: row for row in strength}
    card_y = y + 62
    card_height = height - 76
    for index, name in enumerate(CRITERION_ORDER):
        cx = x + 16 + index * (card_width + gap)
        draw.rounded_rectangle((cx, card_y, cx + card_width, card_y + card_height), radius=6, fill=ui.PALE, outline=ui.LINE, width=2)
        row = by_name[name]
        draw.text((cx + 14, card_y + 10), f"{CRITERION_LABELS[name]} | {float(row['weight']):.0%}", font=ui.font(21, bold=True), fill=ui.INK)
        paste_map(canvas, FIGURES[name], (cx + 10, card_y + 48, 300, card_height - 60))
        ui.draw_wrapped(draw, (cx + 325, card_y + 70), row["data_sources"], ui.font(18), ui.MUTED, card_width - 340, 6, line_gap=5)


def draw_table(draw: ImageDraw.ImageDraw, strength: list[dict[str, str]]) -> None:
    box = ui.PANEL_BOXES["table"]
    ui.draw_card(draw, box)
    x, y, _, _ = box
    draw.text((x + 20, y + 14), "5. Evidence behind the map", font=ui.font(27, bold=True), fill=ui.NAVY)
    draw.text((x + 640, y + 20), "Relative priority only; not flood depth, probability, damage or emergency need", font=ui.font(19), fill=ui.AMBER)
    columns = [420, 130, 250, 1000, 1578]
    headers = ["Criterion", "Weight", "Strength", "Data sources", "What this evidence cannot show"]
    table_x, table_y, row_height = x + 16, y + 56, 57
    current_x = table_x
    for header, column_width in zip(headers, columns, strict=True):
        draw.rectangle((current_x, table_y, current_x + column_width, table_y + row_height), fill=ui.NAVY, outline=ui.WHITE, width=2)
        draw.text((current_x + 10, table_y + 16), header, font=ui.font(19, bold=True), fill=ui.WHITE)
        current_x += column_width
    for row_index, row in enumerate(strength):
        row_y = table_y + row_height * (row_index + 1)
        fill = ui.WHITE if row_index % 2 == 0 else ui.PALE
        values = [CRITERION_LABELS[row["criterion"]], f"{float(row['weight']):.2f}", row["evidence_strength"], row["data_sources"], row["main_limitation"]]
        current_x = table_x
        for index, (value, column_width) in enumerate(zip(values, columns, strict=True)):
            draw.rectangle((current_x, row_y, current_x + column_width, row_y + row_height), fill=fill, outline=ui.LINE, width=1)
            if index >= 3:
                ui.draw_wrapped(draw, (current_x + 10, row_y + 7), value, ui.font(18), ui.INK, column_width - 20, 2, line_gap=1)
            else:
                draw.text((current_x + 10, row_y + 17), value, font=ui.font(18), fill=ui.INK)
            current_x += column_width


def draw_footer(draw: ImageDraw.ImageDraw) -> None:
    x, y, width, _ = ui.PANEL_BOXES["footer"]
    draw.text((x, y + 8), "Interpretation: higher values indicate stronger overlap of the five mapped criteria; hatched cells are not represented by all five criteria", font=ui.font(18), fill=ui.MUTED)
    source_text = "Sources: CHIRPS, SRTM, SoilGrids, WorldCover, JRC, WDPA, USGS, OSM, WorldPop, PANGAEA"
    source_width = int(draw.textlength(source_text, font=ui.font(18)))
    draw.text((x + width - source_width, y + 8), source_text, font=ui.font(18), fill=ui.MUTED)


def write_manifest() -> None:
    rows: list[dict[str, object]] = []
    for key, path in FIGURES.items():
        rows.append({"role": f"governed_figure_{key}", "path": rel(path), "sha256": sha256(path), "claim_level": "sensitivity_scenario"})
    for role, path in (
        ("zimbabwe_figure_chain_manifest", CHAIN_MANIFEST),
        ("criterion_data_strength", DATA_STRENGTH),
        ("fixed_class_result_summary", RESULT_SUMMARY),
        ("weighted_contribution_summary", CONTRIBUTION_SUMMARY),
        ("study_area_manifest", BOUNDARY_MANIFEST),
    ):
        rows.append({"role": role, "path": rel(path), "sha256": sha256(path), "claim_level": "sensitivity_scenario"})
    rows.append({"role": "integrated_briefing_board_png", "path": rel(OUT_PNG), "sha256": sha256(OUT_PNG), "claim_level": "sensitivity_scenario"})
    write_csv(OUT_MANIFEST, rows)


def main() -> None:
    for path in INPUTS:
        if not path.exists():
            raise FileNotFoundError(path)
    validate_chain()
    strength = read_csv(DATA_STRENGTH)
    canvas = Image.new("RGB", ui.CANVAS_SIZE, "#EDF2F6")
    draw = ImageDraw.Draw(canvas)
    draw_header(draw, strength)
    draw_study_area(canvas, draw)
    draw_priority(canvas, draw)
    draw_findings(canvas, draw)
    draw_criteria(canvas, draw, strength)
    draw_table(draw, strength)
    draw_footer(draw)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    temp = OUT_PNG.with_suffix(".tmp.png")
    canvas.save(temp, dpi=(300, 300))
    os.replace(temp, OUT_PNG)
    write_manifest()
    print(f"wrote: {rel(OUT_PNG)}")


if __name__ == "__main__":
    main()
