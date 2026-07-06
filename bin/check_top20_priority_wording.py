#!/usr/bin/env python3
"""Check that active report wording does not call top-20% priority areas hotspots.

The project still has internal filenames such as ``hotspot_stability_summary.csv``.
Those are not presentation wording. This checker targets human-facing text in
active scripts, docs, and current output notes.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CHECK_PATHS = [
    ROOT / "bin/scenarios/run_boundary_v1_rainfall_exposure_v0_4.py",
    ROOT / "bin/scenarios/run_pe1_priority_scenarios.py",
    ROOT / "bin/scenarios/run_boundary_v1_priority_scenarios.py",
    ROOT / "bin/scenarios/run_boundary_v1_rainfall_sensitivity_v0_3.py",
    ROOT / "bin/criteria/diagnose_boundary_v1_hotspot_exposure_v0_3.py",
    ROOT / "bin/factors/derive_peru_pilot_usle_soil_loss.py",
    ROOT / "bin/investigate/run_v1_mining_decay_priority_sensitivity.py",
    ROOT / "bin/package/prepare_boundary_v1_criteria_stack_v0_2_inventory.py",
    ROOT / "bin/visualize/plot_july18_integrated_priority_board.py",
    ROOT / "bin/visualize/plot_mentor_boss_priority_explanation_package.py",
    ROOT / "bin/visualize/plot_zimbabwe_peru_prototype_comparison.py",
    ROOT / "bin/visualize/plot_july18_boss_and_message.py",
    ROOT / "bin/visualize/export_paper_style_single_maps.py",
    ROOT / "bin/visualize/export_single_priority_maps.py",
    ROOT / "context/docs/research-map/RESEARCH_OVERVIEW.md",
    ROOT / "context/docs/research-map/RESEARCH_QUESTIONS.md",
    ROOT / "context/docs/research-map/HYPOTHESES.md",
    ROOT / "context/docs/research-map/RESULTS.md",
    ROOT / "context/docs/research-map/EXPERIMENTS.md",
    ROOT / "context/docs/research-map/DECISION_LOG.md",
    ROOT / "context/docs/research-map/TODO.md",
    ROOT / "context/docs/research-map/REPRODUCIBILITY.md",
    ROOT / "outputs/zimbabwe_peru_prototype_comparison/july18_board_caption.md",
    ROOT / "outputs/zimbabwe_peru_prototype_comparison/july18_boss_process_caption.md",
    ROOT / "outputs/zimbabwe_peru_prototype_comparison/zimbabwe_peru_summary.csv",
    ROOT / "outputs/zimbabwe_peru_prototype_comparison/zimbabwe_peru_comparison_caption.md",
    ROOT / "outputs/zimbabwe_peru_prototype_comparison/zimbabwe_peru_comparison_caption.txt",
    ROOT / "outputs/zimbabwe_peru_prototype_comparison/zimbabwe_peru_comparison_handoff.md",
    ROOT / "outputs/mentor_boss_priority_explanation/mentor_boss_priority_explanation_captions.md",
    ROOT / "outputs/mentor_boss_priority_explanation/mentor_boss_priority_explanation_handoff.md",
    ROOT / "outputs/report_image_catalog_2026-07-06/AUDIT.md",
    ROOT / "outputs/report_image_catalog_2026-07-06/README.md",
    ROOT / "outputs/report_image_catalog_2026-07-06/image_catalog.csv",
    ROOT / "outputs/slide_ready_figures/paper_style_single_maps/index.csv",
    ROOT / "outputs/slide_ready_figures/single_priority_maps/index.csv",
]

DISALLOWED_PHRASES = (
    "hotspot frequency",
    "hotspot stability",
    "hotspot area",
    "hotspot areas",
    "hotspot set",
    "hotspot pattern",
    "hotspot board",
    "stable hotspot",
    "stable hotspots",
    "priority hotspot",
    "priority hotspots",
    "candidate high-priority hotspots",
    "top-20% hotspot",
    "top 20% hotspot",
    "top-20% stable hotspot",
    "top 20% stable hotspot",
    "hotspots are",
    "hotspots reflect",
    "hotspots cannot",
    "hotspots as",
    "hotspots sit",
    "where stable hotspots",
    "hotspot_frequency",
    "hotspot rank",
    "hotspot_rank",
    "hotspot survival",
    "hotspot_survival",
    "hotspot-exposure",
    "hotspot exposure",
)

ALLOWED_SUBSTRINGS = (
    "hotspot_stability_summary",
    "hotspot_summary",
    "hotspot_exposure_diagnostic",
    "hotspot_exposure_summary",
    "hotspot_exposure_board",
    "hotspot_exposure_v0_3",
    "point_evidence_by_hotspot_band",
    "diagnose_boundary_v1_hotspot_exposure",
    "H-TOP20-R-INVARIANT",
)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def line_is_allowed(line: str) -> bool:
    return any(allowed in line for allowed in ALLOWED_SUBSTRINGS)


def main() -> int:
    failures: list[str] = []
    for path in CHECK_PATHS:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_no, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            if line_is_allowed(line):
                continue
            for phrase in DISALLOWED_PHRASES:
                if phrase in lowered:
                    failures.append(f"{rel(path)}:{line_no}: {phrase}: {line.strip()}")
                    break
    if failures:
        print("top-20% priority wording check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("top-20% priority wording check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
