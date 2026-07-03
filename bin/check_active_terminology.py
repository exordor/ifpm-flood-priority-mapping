#!/usr/bin/env python3
"""Fail if deprecated internal criterion terms leak into active IFPM outputs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "outputs/zimbabwe_peru_prototype_comparison/active_terminology_check.csv"

ACTIVE_FILES = [
    ROOT / "context/configs/boundary_v1_criteria_stack_v0_2.csv",
    ROOT / "bin/criteria/build_boundary_v1_criteria_stack_v0_2.py",
    ROOT / "bin/criteria/build_pe1_criteria_stack.py",
    ROOT / "bin/criteria/build_boundary_v1_rainfall_criterion_v0_3.py",
    ROOT / "bin/criteria/build_pe1_rainfall_criterion.py",
    ROOT / "bin/criteria/build_boundary_v1_sediment_r_factor_scenarios.py",
    ROOT / "bin/scenarios/run_boundary_v1_priority_scenarios.py",
    ROOT / "bin/scenarios/run_boundary_v1_rainfall_sensitivity_v0_3.py",
    ROOT / "bin/scenarios/run_boundary_v1_rainfall_exposure_v0_4.py",
    ROOT / "bin/scenarios/run_pe1_priority_scenarios.py",
    ROOT / "bin/visualize/plot_july18_integrated_priority_board.py",
    ROOT / "bin/visualize/plot_mentor_boss_priority_explanation_package.py",
    ROOT / "bin/visualize/plot_zimbabwe_peru_prototype_comparison.py",
]

ACTIVE_OUTPUT_DIRS = [
    ROOT / "outputs/boundary_v1/criteria_stack_v0_2",
    ROOT / "outputs/boundary_v1/rainfall_sensitivity_v0_3",
    ROOT / "outputs/boundary_v1/rainfall_exposure_v0_4",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/criteria_stack",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/rainfall_criterion",
    ROOT / "outputs/srtm_1arcsec_peru_pilot/priority_scenarios",
    ROOT / "outputs/zimbabwe_peru_prototype_comparison",
    ROOT / "outputs/mentor_boss_priority_explanation",
]

TEXT_SUFFIXES = {".csv", ".md", ".txt", ".py", ".json", ".yaml", ".yml"}
GENERATED_CHECK_OUTPUT_NAMES = {
    "active_terminology_check.csv",
    "full_project_terminology_check.csv",
    "full_project_terminology_check.md",
    "glossary_source_check.csv",
}

FORBIDDEN_TERMS = [
    "flood_hazard_proxy",
    "erosion_structure_proxy",
    "road_accessibility_proxy",
    "rainfall_climatology_proxy",
    "river_proximity_proxy",
    "osm_mining_proxy",
    "socioeconomic_exposure",
    "closeness_to_mining_proxy",
    "proxy_0_1",
    "proxy",
    "Proxy",
    "Mining-proxy",
    "R-invariant",
    "rainfail",
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def iter_targets(skip: Path) -> list[Path]:
    paths = [path for path in ACTIVE_FILES if path.exists()]
    for directory in ACTIVE_OUTPUT_DIRS:
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if not path.is_file():
                continue
            if path.name in GENERATED_CHECK_OUTPUT_NAMES:
                continue
            if path.resolve() != skip.resolve():
                paths.append(path)
    return sorted(set(paths))


def scan_path(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    name = path.name
    for term in FORBIDDEN_TERMS:
        if term in name:
            rows.append({"path": rel(path), "where": "filename", "term": term, "line": "", "excerpt": name})

    if path.suffix.lower() not in TEXT_SUFFIXES:
        return rows
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return rows
    for line_no, line in enumerate(text.splitlines(), start=1):
        for term in FORBIDDEN_TERMS:
            if term in line:
                rows.append(
                    {
                        "path": rel(path),
                        "where": "content",
                        "term": term,
                        "line": str(line_no),
                        "excerpt": line.strip()[:220],
                    }
                )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "where", "term", "line", "excerpt"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    findings: list[dict[str, str]] = []
    for path in iter_targets(args.output):
        findings.extend(scan_path(path))
    write_csv(args.output, findings)
    if findings:
        print(f"active terminology check failed: {len(findings)} deprecated term hit(s)")
        print(f"details: {rel(args.output)}")
        return 1
    print(f"active terminology check passed: {rel(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
