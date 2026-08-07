#!/usr/bin/env python3
"""Compose the governed Peru figures into one mentor-facing PNG board."""

from __future__ import annotations

import csv
import hashlib
import math
import os
from collections import OrderedDict
from pathlib import Path

import geopandas as gpd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
CHAIN = ROOT / "outputs/peru_report_figure_chain/current"
BASE = ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios"
OUT_DIR = ROOT / "outputs/peru_integrated_briefing_board"
OUT_PNG = OUT_DIR / "peru_integrated_briefing_board.png"
OUT_MANIFEST = OUT_DIR / "manifest.csv"
FIGURE_CHAIN_MANIFEST = ROOT / "outputs/peru_report_figure_chain/manifest.csv"
RAW_INPUT_INDEX = ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/index.csv"
SINPAD_RECORDS = ROOT / "outputs/peru_gap_closure_analysis/peru_hybas_l7_6070641200_sinpad_pim_colocation.csv"
BOUNDARY_FIGURE = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary_diagnostic.png"
BOUNDARY_MANIFEST = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary_manifest.csv"
BOUNDARY_GPKG = ROOT / "outputs/peru_pilot_boundary/peru_pilot_boundary.gpkg"
POPULATION_BY_CLASS = ROOT / "outputs/peru_gap_closure_analysis/peru_population_by_pim_class.csv"
MINING_MANIFEST = ROOT / "outputs/ingemmet_catastro_minero_peru_pilot/mining_pressure_manifest.csv"
MINING_POINTS = ROOT / "data/raw/ingemmet_catastro_minero_peru_pilot/peru_hybas_l7_6070641200_pequena_mineria.gpkg"

FIGURES = OrderedDict(
    [
        ("flood_hazard", CHAIN / "02_peru_flood_hazard_criterion.png"),
        ("sediment", CHAIN / "03_peru_sediment_criterion.png"),
        ("landuse_asm", CHAIN / "04_peru_landuse_asm_criterion.png"),
        ("environmental", CHAIN / "05_peru_environmental_criterion.png"),
        ("socioeconomic", CHAIN / "06_peru_socioeconomic_criterion.png"),
        ("priority", CHAIN / "07_peru_direct_weight_pim.png"),
        ("mining_population", CHAIN / "08_peru_priority_mining_population_overlay.png"),
        ("contribution", CHAIN / "09_peru_weighted_contribution.png"),
    ]
)
DATA_STRENGTH = BASE / "criterion_data_strength.csv"
CONTRIBUTION_SUMMARY = (
    ROOT / "outputs/slide_ready_figures/peru_pim_contribution_map/contribution_summary.csv"
)

INPUTS = [
    *FIGURES.values(),
    DATA_STRENGTH,
    CONTRIBUTION_SUMMARY,
    FIGURE_CHAIN_MANIFEST,
    RAW_INPUT_INDEX,
    SINPAD_RECORDS,
    BOUNDARY_FIGURE,
    BOUNDARY_MANIFEST,
    BOUNDARY_GPKG,
    POPULATION_BY_CLASS,
    MINING_MANIFEST,
    MINING_POINTS,
]
OUTPUTS = [OUT_PNG, OUT_MANIFEST]

CANVAS_SIZE = (3600, 2400)
PANEL_BOXES = OrderedDict(
    [
        ("header", (60, 40, 3480, 190)),
        ("inputs", (60, 260, 760, 1180)),
        ("priority", (850, 260, 1120, 1180)),
        ("diagnostics", (2000, 260, 1540, 1180)),
        ("criteria", (60, 1470, 3480, 400)),
        ("table", (60, 1900, 3480, 420)),
        ("footer", (60, 2330, 3480, 50)),
    ]
)

NAVY = "#0B2F5B"
BLUE = "#2E75B6"
GREEN = "#1F7A45"
AMBER = "#B35C00"
INK = "#172230"
MUTED = "#5D6978"
LINE = "#C8D1DC"
PALE = "#F3F6F9"
WHITE = "#FFFFFF"

CRITERION_ORDER = [
    "flood_hazard",
    "sediment",
    "landuse_asm",
    "environmental",
    "socioeconomic",
]
CRITERION_SHORT = {
    "flood_hazard": "Flood conditioning",
    "sediment": "Sediment / erosion",
    "landuse_asm": "General land use",
    "environmental": "Environmental context",
    "socioeconomic": "Socioeconomic exposure",
}
CRITERION_ABBREVIATION = {
    "flood_hazard": "FH",
    "sediment": "SE",
    "landuse_asm": "LU",
    "environmental": "ES",
    "socioeconomic": "SV",
}
PUBLIC_LIMITATION_SUMMARY = {
    "flood_hazard": (
        "Rainfall is a seasonal average (~5 km), not storm rainfall; no observed flood extent or depth."
    ),
    "sediment": (
        "Soil K is coarse (250 m); no measured erosion or sediment-transport observations."
    ),
    "landuse_asm": (
        "BV and BE use single-date test proxies; they do not measure change through time."
    ),
    "environmental": (
        "No national protected-area geometry occurs nearby; the pattern is mainly shaped by water and wetland data."
    ),
    "socioeconomic": (
        "Road proximity strongly shapes the pattern; no observed affected-population or damage data are available."
    ),
}
PUBLIC_DATA_SUMMARY = {
    "flood_hazard": "CHIRPS seasonal rainfall; SRTM terrain and drainage",
    "sediment": "SoilGrids K; SRTM LS; ESA WorldCover C",
    "landuse_asm": "WorldCover LC/BV/built/agriculture; OSM roads; mining external only",
    "environmental": "WorldCover and OSM water; SERNANP protected areas",
    "socioeconomic": "OSM roads and buildings; WorldPop 2020",
}


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


def compact_words(text: str, max_chars: int) -> str:
    normalized = " ".join(text.replace("Arequipa Region", "the study boundary").split())
    if len(normalized) <= max_chars:
        return normalized
    shortened = normalized[: max_chars - 3].rsplit(" ", 1)[0]
    return shortened.rstrip(" ,;") + "..."


def build_data_strength_rows(raw_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return five compact, ordered table rows without weakening source claims."""
    criterion_ids = [row.get("criterion_id", "") for row in raw_rows]
    duplicates = sorted({value for value in criterion_ids if criterion_ids.count(value) > 1})
    if duplicates:
        raise ValueError(f"duplicate data-strength criteria: {duplicates}")
    indexed = {row["criterion_id"]: row for row in raw_rows}
    missing = [criterion for criterion in CRITERION_ORDER if criterion not in indexed]
    if missing:
        raise ValueError(f"missing data-strength criteria: {missing}")
    rows: list[dict[str, str]] = []
    weights: list[float] = []
    for criterion_id in CRITERION_ORDER:
        source = indexed[criterion_id]
        weight = float(source["main_weight"])
        coverage = float(source["coverage_within_boundary"])
        if not math.isfinite(weight) or not 0.0 <= weight <= 1.0:
            raise ValueError(f"invalid weight for {criterion_id}: {source['main_weight']}")
        if not math.isfinite(coverage) or not 0.0 <= coverage <= 1.0:
            raise ValueError(
                f"invalid coverage for {criterion_id}: {source['coverage_within_boundary']}"
            )
        weights.append(weight)
        rows.append(
            {
                "criterion_id": criterion_id,
                "criterion": CRITERION_SHORT[criterion_id],
                "weight": f"{weight:.2f}",
                "implementation": compact_words(source["implementation"], 125),
                "evidence": PUBLIC_DATA_SUMMARY[criterion_id],
                "coverage": f"{100.0 * coverage:.2f}%",
                "limitation": PUBLIC_LIMITATION_SUMMARY[criterion_id],
            }
        )
    if not math.isclose(sum(weights), 1.0, abs_tol=1e-9):
        raise ValueError(f"main weights do not sum to 1.0: {sum(weights):.12g}")
    return rows


def rectangles_overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def validate_layout(
    boxes: OrderedDict[str, tuple[int, int, int, int]],
    canvas_size: tuple[int, int],
) -> None:
    width, height = canvas_size
    items = list(boxes.items())
    for name, (x, y, w, h) in items:
        if min(x, y, w, h) < 0 or x + w > width or y + h > height:
            raise ValueError(f"panel outside canvas: {name}")
    for index, (name, box) in enumerate(items):
        for other_name, other_box in items[index + 1 :]:
            if rectangles_overlap(box, other_box):
                raise ValueError(f"panel overlap: {name} and {other_name}")


def font_path(bold: bool = False) -> str | None:
    candidates = (
        [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        if bold
        else [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return None


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = font_path(bold)
    if path:
        return ImageFont.truetype(path, size=size)
    return ImageFont.load_default(size=size)


def fit_image(image: Image.Image, box: tuple[int, int, int, int]) -> tuple[Image.Image, tuple[int, int]]:
    x, y, width, height = box
    copy = image.copy()
    copy.thumbnail((width, height), Image.Resampling.LANCZOS)
    return copy, (x + (width - copy.width) // 2, y + (height - copy.height) // 2)


def map_crop(image: Image.Image) -> Image.Image:
    """Keep the GIS map and coordinate frame while dropping the separate legend block."""
    width, height = image.size
    return image.crop((int(width * 0.025), int(height * 0.01), int(width * 0.975), int(height * 0.755)))


def boundary_crop(image: Image.Image) -> Image.Image:
    """Retain the geographic frame and city labels while removing the old title and legend."""
    width, height = image.size
    return image.crop((int(width * 0.12), int(height * 0.13), int(width * 0.59), int(height * 0.56)))


def draw_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x, y, width, height = box
    draw.rounded_rectangle(
        (x, y, x + width, y + height),
        radius=8,
        fill=WHITE,
        outline=LINE,
        width=2,
    )


def wrapped_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    typeface: ImageFont.FreeTypeFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=typeface) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and " ".join(lines) != text:
        while lines[-1] and draw.textlength(lines[-1] + "...", font=typeface) > max_width:
            lines[-1] = lines[-1][:-1]
        lines[-1] = lines[-1].rstrip() + "..."
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    typeface: ImageFont.FreeTypeFont,
    fill: str,
    max_width: int,
    max_lines: int,
    line_gap: int = 4,
) -> int:
    x, y = xy
    lines = wrapped_lines(draw, text, typeface, max_width, max_lines)
    line_height = typeface.size + line_gap
    for line in lines:
        draw.text((x, y), line, font=typeface, fill=fill)
        y += line_height
    return y


def top_contribution() -> tuple[str, float]:
    rows = read_csv(CONTRIBUTION_SUMMARY)
    top = max(rows, key=lambda row: float(row["dominant_cell_share_scoreable"]))
    return top["criterion"], float(top["dominant_cell_share_scoreable"])


def site_and_factor_count() -> tuple[str, int]:
    rows = read_csv(RAW_INPUT_INDEX)
    panel_rows = [
        row
        for row in rows
        if row.get("panel") == "main_12" and row.get("figure_format") == "png"
    ]
    if len(panel_rows) != 1:
        raise ValueError(f"expected one main_12 PNG index row, found {len(panel_rows)}")
    row = panel_rows[0]
    factors = [value.strip() for value in row["factors"].split(",") if value.strip()]
    site = next((candidate["site"] for candidate in rows if candidate.get("site")), "")
    if not site:
        raise ValueError("raw input index does not declare a study site")
    return site.removeprefix("Peru "), len(factors)


def read_field_value(path: Path) -> dict[str, str]:
    rows = read_csv(path)
    return {row["field"]: row["value"] for row in rows}


def result_summary() -> dict[str, float | int]:
    boundary = read_field_value(BOUNDARY_MANIFEST)
    population_rows = [
        row
        for row in read_csv(POPULATION_BY_CLASS)
        if row["scenario"] == "mentor_peru_direct_pim"
        and row["classification"] == "equal_interval_0_1"
    ]
    by_class = {str(row["priority_class"]): row for row in population_rows}
    missing = [priority_class for priority_class in ("1", "2", "3", "4", "5") if priority_class not in by_class]
    if missing:
        raise ValueError(f"missing PIM population classes: {missing}")
    valid_cells = sum(int(row["pim_cells"]) for row in population_rows)
    high_cells = int(by_class["4"]["pim_cells"])
    very_high_cells = int(by_class["5"]["pim_cells"])
    mining_rows = read_csv(MINING_MANIFEST)
    if len(mining_rows) != 1:
        raise ValueError(f"expected one mining manifest row, found {len(mining_rows)}")
    mining_points = gpd.read_file(MINING_POINTS, layer="pequena_mineria")
    boundary_gdf = gpd.read_file(BOUNDARY_GPKG, layer="peru_pilot_boundary").to_crs(
        mining_points.crs
    )
    inside = mining_points[mining_points.geometry.intersects(boundary_gdf.geometry.iloc[0])]
    unique_inside = inside.geometry.apply(
        lambda geometry: (round(geometry.x, 8), round(geometry.y, 8))
    ).nunique()
    return {
        "study_area_km2": float(boundary["geo_area_km2"]),
        "high_area_km2": high_cells * 0.0009,
        "high_share": high_cells / valid_cells,
        "very_high_area_km2": very_high_cells * 0.0009,
        "high_population": float(by_class["4"]["population_sum"]),
        "mining_points_inside": int(unique_inside),
        "mining_records_nearby": int(mining_rows[0]["features_in_peru_hybas_l7_6070641200_envelope"]),
    }


def sinpad_counts() -> dict[str, int]:
    rows = read_csv(SINPAD_RECORDS)
    comparable = [row for row in rows if row["pim_class"] in {"1", "2", "3", "4", "5"}]
    flood = [row for row in comparable if row["is_flood_specific"].strip().lower() == "true"]
    high = [row for row in comparable if row["pim_class"] in {"4", "5"}]
    flood_high = [row for row in flood if row["pim_class"] in {"4", "5"}]
    return {
        "all_high": len(high),
        "all_comparable": len(comparable),
        "all_total": len(rows),
        "flood_high": len(flood_high),
        "flood_comparable": len(flood),
    }


def validate_figure_chain() -> None:
    rows = read_csv(FIGURE_CHAIN_MANIFEST)
    by_path = {row["packaged_png"]: row for row in rows}
    for path in FIGURES.values():
        key = rel(path)
        if key not in by_path:
            raise ValueError(f"figure missing from governed chain manifest: {key}")
        row = by_path[key]
        if row["status"] != "current":
            raise ValueError(f"figure is not current in governed chain: {key}")
        if row["packaged_png_sha256"] != sha256(path):
            raise ValueError(f"figure checksum differs from governed chain: {key}")


def load_image(path: Path) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(path)
    with Image.open(path) as image:
        return image.convert("RGB")


def draw_header(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    data_rows: list[dict[str, str]],
) -> None:
    x, y, width, height = PANEL_BOXES["header"]
    title_font = font(48, bold=True)
    subtitle_font = font(25)
    takeaway_font = font(29, bold=True)
    status_font = font(21, bold=True)

    draw.text(
        (x, y),
        "Integrated Flood Priority Map for the Vitor-La Joya-Siguas Catchment, Peru",
        font=title_font,
        fill=NAVY,
    )
    site, _ = site_and_factor_count()
    weights = " | ".join(
        f"{CRITERION_ABBREVIATION[row['criterion_id']]} {row['weight']}" for row in data_rows
    )
    draw.text(
        (x, y + 62),
        f"{site} | Five-criterion weighted model | Weights: {weights}",
        font=subtitle_font,
        fill=MUTED,
    )
    criterion_id, share = top_contribution()
    takeaway = (
        "Relative priority is highest in a concentrated north-central corridor; "
        f"{CRITERION_SHORT[criterion_id].lower()} is the largest weighted component across "
        f"{share:.1%} of the area where all five criteria are available."
    )
    draw_wrapped(draw, (x, y + 106), takeaway, takeaway_font, GREEN, 2780, 2, line_gap=2)

    status_text = "RELATIVE PRIORITY | NOT YET VALIDATED AGAINST OBSERVED FLOOD EXTENT OR DAMAGE"
    status_width = int(draw.textlength(status_text, font=status_font)) + 40
    status_box = (x + width - status_width, y + 142, x + width, y + height)
    draw.rounded_rectangle(status_box, radius=8, fill="#FFF3DD", outline="#D39B3A", width=2)
    draw.text((status_box[0] + 20, status_box[1] + 11), status_text, font=status_font, fill=AMBER)


def draw_section_title(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    note: str | None = None,
) -> None:
    x, y, width, _ = box
    draw.text((x + 22, y + 18), title, font=font(28, bold=True), fill=NAVY)
    if note:
        note_font = font(18)
        note_width = int(draw.textlength(note, font=note_font))
        draw.text((x + width - note_width - 22, y + 23), note, font=note_font, fill=MUTED)


def draw_input_panel(canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
    box = PANEL_BOXES["inputs"]
    draw_card(draw, box)
    draw_section_title(draw, box, "1. Study area and research question")
    x, y, width, height = box
    image = boundary_crop(load_image(BOUNDARY_FIGURE))
    fitted, position = fit_image(image, (x + 24, y + 66, width - 48, 500))
    canvas.paste(fitted, position)
    summary = result_summary()
    draw.text(
        (x + 28, y + 574),
        f"Area: {summary['study_area_km2']:,.0f} km²",
        font=font(25, bold=True),
        fill=INK,
    )
    draw_wrapped(
        draw,
        (x + 28, y + 614),
        "Vitor-La Joya-Santa Rita de Siguas, west of Arequipa city",
        font(21),
        MUTED,
        width - 56,
        2,
        line_gap=3,
    )
    draw.text((x + 28, y + 690), "Why this area matters", font=font(23, bold=True), fill=NAVY)
    statements = (
        "Semi-arid Pacific-slope catchment",
        "Steep terrain and concentrated drainage",
        "Mining, settlements and infrastructure within the area",
    )
    statement_y = y + 736
    for statement in statements:
        draw.ellipse((x + 30, statement_y + 7, x + 42, statement_y + 19), fill=GREEN)
        draw.text((x + 58, statement_y), statement, font=font(20), fill=INK)
        statement_y += 44
    draw.rounded_rectangle(
        (x + 28, y + 864, x + width - 28, y + 904),
        radius=6,
        fill="#E7EFF7",
        outline=BLUE,
        width=2,
    )
    draw.text(
        (x + 44, y + 873),
        "Where do flood-related pressures overlap most strongly?",
        font=font(19, bold=True),
        fill=NAVY,
    )


def draw_priority_panel(canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
    box = PANEL_BOXES["priority"]
    draw_card(draw, box)
    draw_section_title(
        draw,
        box,
        "2. Integrated priority map",
        "five relative-priority classes",
    )
    x, y, width, height = box
    image = load_image(FIGURES["priority"])
    fitted, position = fit_image(image, (x + 24, y + 66, width - 48, height - 86))
    canvas.paste(fitted, position)


def draw_metric_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    value: str,
    label: str,
    note: str,
) -> None:
    x, y, width, height = box
    draw.rounded_rectangle(
        (x, y, x + width, y + height),
        radius=7,
        fill=PALE,
        outline=LINE,
        width=2,
    )
    draw.text((x + 18, y + 12), value, font=font(34, bold=True), fill=GREEN)
    draw.text((x + 170, y + 18), label, font=font(22, bold=True), fill=INK)
    draw_wrapped(draw, (x + 18, y + 66), note, font(17), MUTED, width - 36, 2, line_gap=2)


def draw_diagnostic_panel(canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
    box = PANEL_BOXES["diagnostics"]
    draw_card(draw, box)
    draw_section_title(draw, box, "3. Key findings")
    x, y, width, height = box
    gap = 12
    inner_x = x + 18
    inner_width = width - 36
    metric_width = (inner_width - gap) // 2
    metric_height = 126
    summary = result_summary()
    metric_data = (
        (
            f"{summary['high_area_km2']:.1f} km²",
            "High class",
            f"Score 0.6-0.8 | {summary['high_share']:.1%} of the area covered by all five criteria",
        ),
        (
            f"{summary['very_high_area_km2']:.0f} km²",
            "Very high class",
            "Score 0.8-1.0 | no cells reach this class",
        ),
        (
            f"~{summary['high_population']:,.0f}",
            "Population",
            "WorldPop 2020 in High-class cells; also used in the socioeconomic criterion",
        ),
        (
            str(summary["mining_points_inside"]),
            "Mining locations",
            f"Inside the study area | {summary['mining_records_nearby']} nearby records inform the map",
        ),
    )
    metric_y = y + 68
    for index, metric in enumerate(metric_data):
        row = index // 2
        column = index % 2
        metric_box = (
            inner_x + column * (metric_width + gap),
            metric_y + row * (metric_height + gap),
            metric_width,
            metric_height,
        )
        draw_metric_card(draw, metric_box, *metric)

    contribution_y = metric_y + 2 * metric_height + 2 * gap
    contribution_box = (inner_x, contribution_y, inner_width, 270)
    cx, cy, cw, ch = contribution_box
    draw.rounded_rectangle((cx, cy, cx + cw, cy + ch), radius=8, fill=PALE, outline=LINE, width=2)
    draw.text((cx + 18, cy + 14), "What shapes the pattern", font=font(24, bold=True), fill=INK)
    image = map_crop(load_image(FIGURES["contribution"]))
    fitted, position = fit_image(image, (cx + 18, cy + 48, 390, ch - 62))
    canvas.paste(fitted, position)
    criterion_id, share = top_contribution()
    draw_wrapped(
        draw,
        (cx + 440, cy + 70),
        f"{CRITERION_SHORT[criterion_id]} is the largest weighted component across {share:.1%} "
        "of the area where all five criteria are available. This describes the index, not the "
        "physical cause of floods.",
        font(21),
        INK,
        cw - 470,
        5,
        line_gap=6,
    )

    context_y = contribution_y + 270 + gap
    context_box = (inner_x, context_y, inner_width, 270)
    cx, cy, cw, ch = context_box
    draw.rounded_rectangle((cx, cy, cx + cw, cy + ch), radius=8, fill=PALE, outline=LINE, width=2)
    draw.text((cx + 18, cy + 14), "Mining and population context", font=font(24, bold=True), fill=INK)
    image = map_crop(load_image(FIGURES["mining_population"]))
    fitted, position = fit_image(image, (cx + 18, cy + 48, 390, ch - 62))
    canvas.paste(fitted, position)
    draw_wrapped(
        draw,
        (cx + 440, cy + 70),
        "WorldPop and INGEMMET points show where people and mining coincide with the priority "
        "map. They describe local context rather than observed flood damage.",
        font(21),
        INK,
        cw - 470,
        5,
        line_gap=6,
    )

    evidence_y = context_y + 270 + gap
    evidence_height = y + height - evidence_y - 18
    draw.rounded_rectangle(
        (inner_x, evidence_y, inner_x + inner_width, evidence_y + evidence_height),
        radius=8,
        fill="#FFF7E8",
        outline="#D39B3A",
        width=2,
    )
    draw.text(
        (inner_x + 18, evidence_y + 14),
        "Comparison with reported events",
        font=font(24, bold=True),
        fill=AMBER,
    )
    counts = sinpad_counts()
    event_text = (
        "The map has not yet been validated against observed flood extent or damage. Of the "
        f"reported events that can be compared with the five map classes, {counts['all_high']} of "
        f"{counts['all_comparable']} fall in the High or Very High classes, including "
        f"{counts['flood_high']} of {counts['flood_comparable']} flood records."
    )
    draw_wrapped(
        draw,
        (inner_x + 18, evidence_y + 54),
        event_text,
        font(20),
        INK,
        inner_width - 36,
        5,
        line_gap=4,
    )


def draw_criteria_strip(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    data_rows: list[dict[str, str]],
) -> None:
    box = PANEL_BOXES["criteria"]
    draw_card(draw, box)
    draw_section_title(
        draw,
        box,
        "4. Five criteria and weights",
        "Darker colors indicate greater relative priority",
    )
    x, y, width, height = box
    gap = 12
    inner_width = width - 32
    card_width = (inner_width - gap * 4) // 5
    row_by_id = {row["criterion_id"]: row for row in data_rows}
    card_y = y + 62
    card_height = height - 76
    for index, criterion_id in enumerate(CRITERION_ORDER):
        cx = x + 16 + index * (card_width + gap)
        draw.rounded_rectangle(
            (cx, card_y, cx + card_width, card_y + card_height),
            radius=6,
            fill=PALE,
            outline=LINE,
            width=2,
        )
        row = row_by_id[criterion_id]
        draw.text(
            (cx + 14, card_y + 10),
            f"{CRITERION_SHORT[criterion_id]} | {float(row['weight']):.0%}",
            font=font(21, bold=True),
            fill=INK,
        )
        image = map_crop(load_image(FIGURES[criterion_id]))
        fitted, position = fit_image(image, (cx + 10, card_y + 48, 300, card_height - 60))
        canvas.paste(fitted, position)
        draw_wrapped(
            draw,
            (cx + 325, card_y + 76),
            row["evidence"],
            font(18),
            MUTED,
            card_width - 340,
            5,
            line_gap=5,
        )


def draw_table(
    draw: ImageDraw.ImageDraw,
    data_rows: list[dict[str, str]],
) -> None:
    box = PANEL_BOXES["table"]
    draw_card(draw, box)
    x, y, width, height = box
    draw.text((x + 20, y + 14), "5. Evidence behind the map", font=font(27, bold=True), fill=NAVY)
    draw.text(
        (x + 640, y + 20),
        "The map shows relative priority; it does not show flood depth, probability or emergency need",
        font=font(19),
        fill=AMBER,
    )
    table_x = x + 16
    table_y = y + 56
    columns = [420, 130, 1100, 1798]
    headers = ["Criterion", "Weight", "Data sources", "What this evidence cannot show"]
    row_height = 57
    header_font = font(19, bold=True)
    body_font = font(18)
    current_x = table_x
    for header, column_width in zip(headers, columns):
        draw.rectangle(
            (current_x, table_y, current_x + column_width, table_y + row_height),
            fill=NAVY,
            outline=WHITE,
            width=2,
        )
        draw.text((current_x + 10, table_y + 16), header, font=header_font, fill=WHITE)
        current_x += column_width
    for row_index, row in enumerate(data_rows):
        row_y = table_y + row_height * (row_index + 1)
        fill = WHITE if row_index % 2 == 0 else PALE
        values = [
            row["criterion"],
            row["weight"],
            row["evidence"],
            row["limitation"],
        ]
        current_x = table_x
        for column_index, (value, column_width) in enumerate(zip(values, columns)):
            draw.rectangle(
                (current_x, row_y, current_x + column_width, row_y + row_height),
                fill=fill,
                outline=LINE,
                width=1,
            )
            if column_index in {2, 3}:
                draw_wrapped(
                    draw,
                    (current_x + 10, row_y + 7),
                    value,
                    body_font,
                    INK,
                    column_width - 20,
                    2,
                    line_gap=1,
                )
            else:
                draw.text((current_x + 10, row_y + 17), value, font=body_font, fill=INK)
            current_x += column_width


def draw_footer(draw: ImageDraw.ImageDraw) -> None:
    x, y, width, _ = PANEL_BOXES["footer"]
    left = "Interpretation: higher values indicate stronger overlap of the five criteria; hatching marks data gaps"
    draw.text((x, y + 10), left, font=font(18), fill=MUTED)
    right = "Sources: CHIRPS, SRTM, SoilGrids, ESA WorldCover, INGEMMET, OSM, WorldPop, SERNANP"
    right_width = int(draw.textlength(right, font=font(18)))
    draw.text((x + width - right_width, y + 10), right, font=font(18), fill=MUTED)


def write_manifest(png_source: Path, destination: Path) -> None:
    rows: list[dict[str, str]] = []
    chain_rows = {row["packaged_png"]: row for row in read_csv(FIGURE_CHAIN_MANIFEST)}

    def record(
        record_type: str,
        role: str,
        path: Path,
        status: str,
        claim_level: str,
        checksum_path: Path | None = None,
    ) -> dict[str, str]:
        return {
            "record_type": record_type,
            "role": role,
            "path": rel(path),
            "sha256": sha256(checksum_path or path),
            "status": status,
            "claim_level": claim_level,
            "boundary_id": "srtm_1arcsec_peru_pilot",
            "experiment_id": "priority_scenarios",
        }

    roles = {key: f"governed_figure_{key}" for key in FIGURES}
    for key, path in FIGURES.items():
        chain_row = chain_rows[rel(path)]
        rows.append(
            record(
                "input",
                roles[key],
                path,
                chain_row["status"],
                chain_row["claim_level"],
            )
        )
    for role, path in (
        ("criterion_data_strength", DATA_STRENGTH),
        ("weighted_contribution_summary", CONTRIBUTION_SUMMARY),
        ("governed_figure_chain_manifest", FIGURE_CHAIN_MANIFEST),
        ("raw_input_factor_index", RAW_INPUT_INDEX),
        ("sinpad_event_records", SINPAD_RECORDS),
        ("study_area_figure", BOUNDARY_FIGURE),
        ("study_area_manifest", BOUNDARY_MANIFEST),
        ("study_area_geometry", BOUNDARY_GPKG),
        ("population_by_priority_class", POPULATION_BY_CLASS),
        ("mining_evidence_manifest", MINING_MANIFEST),
        ("mining_reference_points", MINING_POINTS),
    ):
        rows.append(record("input", role, path, "current", "lineage_or_diagnostic"))
    rows.append(
        record(
            "code",
            "integrated_briefing_board_builder",
            Path(__file__).resolve(),
            "current",
            "tooling",
        )
    )
    rows.append(
        record(
            "output",
            "integrated_briefing_board_png",
            OUT_PNG,
            "mentor_review_ready_prototype",
            "sensitivity_scenario",
            checksum_path=png_source,
        )
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def validate_output(path: Path) -> None:
    with Image.open(path) as image:
        if image.size != CANVAS_SIZE:
            raise ValueError(f"unexpected board size: {image.size}")
        extrema = image.convert("L").getextrema()
        if extrema is None or extrema[0] == extrema[1]:
            raise ValueError("board is visually blank")
    if path.stat().st_size < 500_000:
        raise ValueError(f"board file is unexpectedly small: {path.stat().st_size}")


def main() -> None:
    validate_layout(PANEL_BOXES, CANVAS_SIZE)
    missing = [path for path in INPUTS if not path.exists()]
    if missing:
        raise FileNotFoundError("missing board inputs:\n" + "\n".join(str(path) for path in missing))
    validate_figure_chain()
    data_rows = build_data_strength_rows(read_csv(DATA_STRENGTH))

    canvas = Image.new("RGB", CANVAS_SIZE, "#EEF2F6")
    draw = ImageDraw.Draw(canvas)
    draw_header(canvas, draw, data_rows)
    draw_input_panel(canvas, draw)
    draw_priority_panel(canvas, draw)
    draw_diagnostic_panel(canvas, draw)
    draw_criteria_strip(canvas, draw, data_rows)
    draw_table(draw, data_rows)
    draw_footer(draw)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    temp_png = OUT_DIR / f".{OUT_PNG.name}.tmp"
    temp_manifest = OUT_DIR / f".{OUT_MANIFEST.name}.tmp"
    try:
        canvas.save(temp_png, format="PNG", optimize=True)
        validate_output(temp_png)
        write_manifest(temp_png, temp_manifest)
        os.replace(temp_png, OUT_PNG)
        os.replace(temp_manifest, OUT_MANIFEST)
    finally:
        temp_png.unlink(missing_ok=True)
        temp_manifest.unlink(missing_ok=True)
    print(f"wrote: {rel(OUT_PNG)}")


if __name__ == "__main__":
    main()
