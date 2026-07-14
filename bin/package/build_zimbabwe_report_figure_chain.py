#!/usr/bin/env python3
"""Package the current Zimbabwe reporting figures with source hashes."""

from __future__ import annotations

import csv
import hashlib
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "outputs/slide_ready_figures/zimbabwe_reporting_maps"
EVIDENCE_DIR = ROOT / "outputs/slide_ready_figures/zimbabwe_input_evidence_maps"
OVERLAY_DIR = ROOT / "outputs/slide_ready_figures/zimbabwe_evidence_overlays"
OUTPUT_ROOT = ROOT / "outputs/zimbabwe_report_figure_chain"
CURRENT_DIR = OUTPUT_ROOT / "current"
MANIFEST = OUTPUT_ROOT / "manifest.csv"


@dataclass(frozen=True)
class Item:
    order: int
    item_id: str
    stage: str
    source_png: Path
    source_pdf: Path
    claim_level: str = "sensitivity_scenario"
    status: str = "current"


def source(stem: str, suffix: str) -> Path:
    return SOURCE_DIR / f"{stem}.{suffix}"


ITEMS = [
    Item(
        1,
        "zimbabwe_study_area",
        "study_area",
        source("zimbabwe_study_area_no_title_caption", "png"),
        source("zimbabwe_study_area_no_title_caption", "pdf"),
    ),
    Item(2, "zimbabwe_flood_conditioning", "pim_criteria", source("zimbabwe_flood_hazard_5class_paper_style_no_title_caption", "png"), source("zimbabwe_flood_hazard_5class_paper_style_no_title_caption", "pdf")),
    Item(3, "zimbabwe_sediment", "pim_criteria", source("zimbabwe_sediment_5class_paper_style_no_title_caption", "png"), source("zimbabwe_sediment_5class_paper_style_no_title_caption", "pdf")),
    Item(4, "zimbabwe_landuse_asm", "pim_criteria", source("zimbabwe_landuse_asm_5class_paper_style_no_title_caption", "png"), source("zimbabwe_landuse_asm_5class_paper_style_no_title_caption", "pdf")),
    Item(5, "zimbabwe_environmental", "pim_criteria", source("zimbabwe_environmental_5class_paper_style_no_title_caption", "png"), source("zimbabwe_environmental_5class_paper_style_no_title_caption", "pdf")),
    Item(6, "zimbabwe_socioeconomic", "pim_criteria", source("zimbabwe_socioeconomic_5class_paper_style_no_title_caption", "png"), source("zimbabwe_socioeconomic_5class_paper_style_no_title_caption", "pdf")),
    Item(7, "zimbabwe_direct_weight_pim", "weighted_pim", source("zimbabwe_direct_weight_priority_5class_paper_style_no_title_caption", "png"), source("zimbabwe_direct_weight_priority_5class_paper_style_no_title_caption", "pdf")),
    Item(
        8,
        "zimbabwe_priority_mining_population_overlay",
        "mining_population_overlay",
        OVERLAY_DIR / "zimbabwe_priority_mining_population_overlay_no_title_caption.png",
        OVERLAY_DIR / "zimbabwe_priority_mining_population_overlay_no_title_caption.pdf",
        claim_level="diagnostic_only",
    ),
    Item(9, "zimbabwe_weighted_contribution", "contribution_explanation", source("zimbabwe_largest_weighted_contribution_no_title_caption", "png"), source("zimbabwe_largest_weighted_contribution_no_title_caption", "pdf")),
    Item(
        10,
        "zimbabwe_twelve_factor_input_evidence",
        "input_evidence_overview",
        EVIDENCE_DIR / "zimbabwe_peru_aligned_main_12_evidence_panel_no_title_caption.png",
        EVIDENCE_DIR / "zimbabwe_peru_aligned_main_12_evidence_panel_no_title_caption.pdf",
        claim_level="diagnostic_only",
    ),
    Item(
        11,
        "zimbabwe_flood_sediment_input_evidence",
        "direct_input_evidence",
        EVIDENCE_DIR / "zimbabwe_flood_sediment_direct_evidence_panel_no_title_caption.png",
        EVIDENCE_DIR / "zimbabwe_flood_sediment_direct_evidence_panel_no_title_caption.pdf",
        claim_level="diagnostic_only",
    ),
    Item(
        12,
        "zimbabwe_land_environment_access_input_evidence",
        "direct_input_evidence",
        EVIDENCE_DIR / "zimbabwe_land_environment_access_direct_evidence_panel_no_title_caption.png",
        EVIDENCE_DIR / "zimbabwe_land_environment_access_direct_evidence_panel_no_title_caption.pdf",
        claim_level="diagnostic_only",
    ),
    Item(
        13,
        "zimbabwe_supporting_input_diagnostics",
        "supporting_diagnostics",
        EVIDENCE_DIR / "zimbabwe_supporting_diagnostics_evidence_panel_no_title_caption.png",
        EVIDENCE_DIR / "zimbabwe_supporting_diagnostics_evidence_panel_no_title_caption.pdf",
        claim_level="diagnostic_only",
    ),
]

INPUTS = [path for item in ITEMS for path in (item.source_png, item.source_pdf)]
OUTPUTS = [CURRENT_DIR / f"{item.order:02d}_{item.item_id}.{suffix}" for item in ITEMS for suffix in ("png", "pdf")]
OUTPUTS += [CURRENT_DIR / "README.md", MANIFEST]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def package_items() -> list[dict[str, object]]:
    CURRENT_DIR.mkdir(parents=True, exist_ok=True)
    expected = {"README.md"}
    rows: list[dict[str, object]] = []
    for item in ITEMS:
        row = asdict(item)
        row["source_png"] = rel(item.source_png)
        row["source_pdf"] = rel(item.source_pdf)
        for suffix, source_path in (("png", item.source_png), ("pdf", item.source_pdf)):
            if not source_path.exists():
                raise FileNotFoundError(source_path)
            destination = CURRENT_DIR / f"{item.order:02d}_{item.item_id}.{suffix}"
            expected.add(destination.name)
            temporary = destination.with_name(f".{destination.name}.tmp")
            shutil.copy2(source_path, temporary)
            temporary.replace(destination)
            row[f"packaged_{suffix}"] = rel(destination)
            row[f"source_{suffix}_sha256"] = sha256(source_path)
            row[f"packaged_{suffix}_sha256"] = sha256(destination)
            if row[f"source_{suffix}_sha256"] != row[f"packaged_{suffix}_sha256"]:
                raise RuntimeError(f"checksum mismatch after copying {source_path}")
        rows.append(row)
    for path in CURRENT_DIR.iterdir():
        if path.is_file() and path.name not in expected:
            path.unlink()
    return rows


def write_manifest(rows: list[dict[str, object]]) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    temporary = MANIFEST.with_name(f".{MANIFEST.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(MANIFEST)


def write_readme() -> None:
    lines = [
        "# Zimbabwe Current Report Figure Chain",
        "",
        "This is the current reporting entrypoint for the Upper Mzingwane working study area.",
        "It contains the study area, five PIM criteria, the direct-weight PIM, and the",
        "mining/population context, and largest weighted-contribution explanation, followed by a Peru-aligned 12-factor evidence overview,",
        "two direct-evidence panels, and one supporting-diagnostics panel.",
        "",
        "The main weights are FH 0.32, SE 0.23, LM 0.18, ES 0.12, and SV 0.15.",
        "They are direct recommended weights; no pairwise matrix or consistency ratio was supplied.",
        "",
        "Claim boundary: this is not a validated flood-risk map. Flood is a conditioning",
        "indicator, sediment uses independently normalized spatial K, LS, and C at 0.35/0.35/0.30, mining uses",
        "USGS mineral-reference proximity, Environmental is proximity-based context, and Socioeconomic is",
        "road/access proximity only. The separate mining/population overlay uses mapped mining land-use",
        "footprints and WorldPop as independent context. The PIM is calculated only where all five criteria are represented.",
        "",
        "See `../manifest.csv` for source paths and checksums and",
        "`../../slide_ready_figures/zimbabwe_reporting_maps/criterion_data_strength.csv`",
        "for the criterion-level evidence assessment.",
        "",
    ]
    destination = CURRENT_DIR / "README.md"
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.write_text("\n".join(lines), encoding="utf-8")
    temporary.replace(destination)


def main() -> None:
    rows = package_items()
    write_manifest(rows)
    write_readme()
    print(f"packaged {len(rows)} Zimbabwe figures to {rel(CURRENT_DIR)}")


if __name__ == "__main__":
    main()
