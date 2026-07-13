#!/usr/bin/env python3
"""Build the current Peru report figure chain and archive superseded entrypoints."""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "context/docs/research-map/peru_authoritative_figure_chain.csv"
OUTPUT_ROOT = ROOT / "outputs/peru_report_figure_chain"
CURRENT_DIR = OUTPUT_ROOT / "current"
MANIFEST = OUTPUT_ROOT / "manifest.csv"
ARCHIVE_DIR = ROOT / "outputs/_archive/2026-07-11_peru_figure_governance"

INPUTS = [
    ROOT / "context/docs/research-map/peru_authoritative_figure_chain.csv",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/peru_raw_main_12_input_factors_panel_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_raw_input_factor_maps/peru_raw_main_12_input_factors_panel_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_pim_criteria_maps/peru_flood_hazard_5class_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_pim_criteria_maps/peru_flood_hazard_5class_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_pim_criteria_maps/peru_sediment_5class_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_pim_criteria_maps/peru_sediment_5class_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_pim_criteria_maps/peru_landuse_asm_5class_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_pim_criteria_maps/peru_landuse_asm_5class_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_pim_criteria_maps/peru_environmental_5class_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_pim_criteria_maps/peru_environmental_5class_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_pim_criteria_maps/peru_socioeconomic_5class_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_pim_criteria_maps/peru_socioeconomic_5class_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_direct_weight_priority_maps/peru_direct_weight_priority_screening_5class_paper_style_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_direct_weight_priority_maps/peru_direct_weight_priority_screening_5class_paper_style_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_evidence_overlays/peru_priority_mining_population_overlay_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_evidence_overlays/peru_priority_mining_population_overlay_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_pim_contribution_map/peru_largest_weighted_contribution_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_pim_contribution_map/peru_largest_weighted_contribution_no_title_caption.pdf",
    ROOT / "outputs/slide_ready_figures/peru_evidence_overlays/peru_sinpad_colocation_diagnostic_no_title_caption.png",
    ROOT / "outputs/slide_ready_figures/peru_evidence_overlays/peru_sinpad_colocation_diagnostic_no_title_caption.pdf",
]

OUTPUTS = [
    ROOT / "outputs/peru_report_figure_chain/current/01_peru_raw_input_factors.png",
    ROOT / "outputs/peru_report_figure_chain/current/01_peru_raw_input_factors.pdf",
    ROOT / "outputs/peru_report_figure_chain/current/02_peru_flood_hazard_criterion.png",
    ROOT / "outputs/peru_report_figure_chain/current/02_peru_flood_hazard_criterion.pdf",
    ROOT / "outputs/peru_report_figure_chain/current/03_peru_sediment_criterion.png",
    ROOT / "outputs/peru_report_figure_chain/current/03_peru_sediment_criterion.pdf",
    ROOT / "outputs/peru_report_figure_chain/current/04_peru_landuse_asm_criterion.png",
    ROOT / "outputs/peru_report_figure_chain/current/04_peru_landuse_asm_criterion.pdf",
    ROOT / "outputs/peru_report_figure_chain/current/05_peru_environmental_criterion.png",
    ROOT / "outputs/peru_report_figure_chain/current/05_peru_environmental_criterion.pdf",
    ROOT / "outputs/peru_report_figure_chain/current/06_peru_socioeconomic_criterion.png",
    ROOT / "outputs/peru_report_figure_chain/current/06_peru_socioeconomic_criterion.pdf",
    ROOT / "outputs/peru_report_figure_chain/current/07_peru_direct_weight_pim.png",
    ROOT / "outputs/peru_report_figure_chain/current/07_peru_direct_weight_pim.pdf",
    ROOT / "outputs/peru_report_figure_chain/current/08_peru_priority_mining_population_overlay.png",
    ROOT / "outputs/peru_report_figure_chain/current/08_peru_priority_mining_population_overlay.pdf",
    ROOT / "outputs/peru_report_figure_chain/current/09_peru_weighted_contribution.png",
    ROOT / "outputs/peru_report_figure_chain/current/09_peru_weighted_contribution.pdf",
    ROOT / "outputs/peru_report_figure_chain/current/10_peru_sinpad_colocation_diagnostic.png",
    ROOT / "outputs/peru_report_figure_chain/current/10_peru_sinpad_colocation_diagnostic.pdf",
    ROOT / "outputs/peru_report_figure_chain/current/README.md",
    ROOT / "outputs/peru_report_figure_chain/manifest.csv",
]

EXPECTED_STAGES = [
    "raw_inputs",
    "pim_criteria",
    "ahp_pim",
    "mining_population_overlay",
    "contribution_explanation",
    "validation_diagnostic",
]

LEGACY_OUTPUTS = [
    Path("outputs/report_image_catalog_2026-07-06"),
    Path("outputs/mentor_boss_priority_explanation"),
    Path("outputs/zimbabwe_peru_prototype_comparison"),
    Path("outputs/sensitivity_figures"),
    Path("outputs/slide_ready_figures/peru_conditioning_factor_maps"),
    Path("outputs/slide_ready_figures/peru_exposure_context_maps"),
    Path("outputs/v1_full_methodology_evidence_sweep"),
    Path("outputs/v1_multicriteria_evidence_package"),
    Path("outputs/v1_terrain_mentor_package"),
    Path("outputs/study_area_location_map"),
    Path("outputs/mentor_boundary_decision"),
]

LEGACY_SLIDE_STEMS = [
    "equal_ahp_hotspot_overlay_no_title_caption",
    "equal_ahp_hotspot_overlay_site_labels_no_title_caption",
    "hotspot_frequency_maps_no_title_caption",
    "peru_equal_ahp_hotspot_overlay_no_title_caption",
    "peru_hotspot_map_no_title_caption",
    "peru_priority_map_no_title_caption",
    "priority_mean_maps_no_title_caption",
    "zimbabwe_equal_ahp_hotspot_overlay_no_title_caption",
    "zimbabwe_hotspot_map_no_title_caption",
    "zimbabwe_priority_map_no_title_caption",
]

LEGACY_SLIDE_FILES = [
    Path("outputs/slide_ready_figures/equal_ahp_hotspot_overlay_summary.csv"),
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_config() -> list[dict[str, str]]:
    if not CONFIG.exists():
        raise FileNotFoundError(CONFIG)
    with CONFIG.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("authoritative figure chain is empty")
    stages = list(dict.fromkeys(row["stage_id"] for row in rows))
    if stages != EXPECTED_STAGES:
        raise ValueError(f"unexpected figure-chain stages: {stages}")
    item_ids = [row["item_id"] for row in rows]
    if len(item_ids) != len(set(item_ids)):
        raise ValueError("duplicate item_id in authoritative figure chain")
    if any(row["status"] != "current" for row in rows):
        raise ValueError("only current rows may enter the authoritative figure chain")
    forbidden = ("zimbabwe", "report_image_catalog_2026-07-06", "mentor_boss_priority_explanation")
    for row in rows:
        source = row["source_png"].lower()
        if any(token in source for token in forbidden):
            raise ValueError(f"legacy or cross-site source in current chain: {source}")
    return rows


def copy_current(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    CURRENT_DIR.mkdir(parents=True, exist_ok=True)
    expected_names: set[str] = set()
    manifest_rows: list[dict[str, str]] = []
    for row in rows:
        order = int(row["order"])
        copied: dict[str, str] = dict(row)
        for fmt in ("png", "pdf"):
            source = ROOT / row[f"source_{fmt}"]
            if not source.exists():
                raise FileNotFoundError(f"current figure source is missing: {source}")
            destination = CURRENT_DIR / f"{order:02d}_{row['item_id']}.{fmt}"
            expected_names.add(destination.name)
            shutil.copy2(source, destination)
            copied[f"packaged_{fmt}"] = rel(destination)
            copied[f"source_{fmt}_sha256"] = sha256(source)
            copied[f"packaged_{fmt}_sha256"] = sha256(destination)
            if copied[f"source_{fmt}_sha256"] != copied[f"packaged_{fmt}_sha256"]:
                raise RuntimeError(f"checksum mismatch after copying {source}")
        manifest_rows.append(copied)

    for path in CURRENT_DIR.iterdir():
        if path.is_file() and path.name not in expected_names:
            path.unlink()
    return manifest_rows


def write_manifest(rows: list[dict[str, str]]) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_readme(rows: list[dict[str, str]]) -> None:
    stage_counts = {stage: sum(row["stage_id"] == stage for row in rows) for stage in EXPECTED_STAGES}
    lines = [
        "# Peru Current Report Figure Chain",
        "",
        "This directory is the only current reporting entrypoint for the Peru mainline.",
        "The numbered files follow this order:",
        "",
    ]
    for index, stage in enumerate(EXPECTED_STAGES, start=1):
        lines.append(f"{index}. `{stage}` ({stage_counts[stage]} figure(s))")
    lines.extend(
        [
            "",
            "Claim boundary: the AHP map is a sensitivity scenario. Mining and population",
            "overlays are model-input context. SINPAD is a co-location diagnostic, not",
            "independent model validation. Flood is a conditioning indicator, Environmental",
            "is water/wetland-led context, and Socioeconomic is an exposure indicator. The PIM",
            "covers 95.0998% of PE1 on strict five-criterion common support; the remaining",
            "4.9002% is hatched and unscored. It is not a catchment-wide rescue map. See",
            "`../manifest.csv` for source paths and checksums.",
            "",
        ]
    )
    (CURRENT_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")


def archive_path(source: Path, destination: Path) -> str:
    if source.exists() and destination.exists():
        raise FileExistsError(f"archive conflict: both source and destination exist: {source}")
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        return "archived"
    if destination.exists():
        return "already_archived"
    return "not_found"


def archive_legacy() -> list[dict[str, str]]:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    for relative in LEGACY_OUTPUTS:
        source = ROOT / relative
        destination = ARCHIVE_DIR / "report_surfaces" / source.name
        rows.append(
            {
                "source": str(relative),
                "destination": rel(destination),
                "status": archive_path(source, destination),
                "reason": "superseded reporting entrypoint; excluded from the Peru authoritative figure chain",
            }
        )

    slide_root = ROOT / "outputs/slide_ready_figures"
    for stem in LEGACY_SLIDE_STEMS:
        for suffix in (".png", ".pdf"):
            source = slide_root / f"{stem}{suffix}"
            destination = ARCHIVE_DIR / "legacy_slide_ready" / source.name
            rows.append(
                {
                    "source": rel(source),
                    "destination": rel(destination),
                    "status": archive_path(source, destination),
                    "reason": "legacy scenario or cross-site figure; excluded from the Peru authoritative figure chain",
                }
            )

    for relative in LEGACY_SLIDE_FILES:
        source = ROOT / relative
        destination = ARCHIVE_DIR / "legacy_slide_ready" / source.name
        rows.append(
            {
                "source": str(relative),
                "destination": rel(destination),
                "status": archive_path(source, destination),
                "reason": "legacy scenario summary; excluded from the Peru authoritative figure chain",
            }
        )

    fields = ["source", "destination", "status", "reason"]
    with (ARCHIVE_DIR / "ARCHIVE_MANIFEST.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (ARCHIVE_DIR / "README.md").write_text(
        "# Peru Figure Governance Archive\n\n"
        f"Created {date.today().isoformat()} by non-destructively moving superseded reporting "
        "entrypoints and legacy slide-ready figures. These artifacts remain available for "
        "traceability but are not part of the current Peru report figure chain.\n",
        encoding="utf-8",
    )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive-legacy",
        action="store_true",
        help="move known superseded report surfaces to the dated archive before packaging",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.archive_legacy:
        archive_rows = archive_legacy()
        archived = sum(row["status"] == "archived" for row in archive_rows)
        print(f"archived {archived} legacy report surfaces")
    rows = read_config()
    packaged = copy_current(rows)
    write_manifest(packaged)
    write_readme(packaged)
    print(f"packaged {len(packaged)} current figures to {rel(CURRENT_DIR)}")


if __name__ == "__main__":
    main()
