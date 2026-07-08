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
    ROOT / "bin/criteria/build_boundary_v1_criteria_stack.py",
    ROOT / "bin/criteria/build_pe1_criteria_stack.py",
    ROOT / "bin/criteria/build_boundary_v1_rainfall_criterion.py",
    ROOT / "bin/criteria/build_pe1_rainfall_criterion.py",
    ROOT / "bin/scenarios/run_boundary_v1_priority_scenarios.py",
    ROOT / "bin/scenarios/run_boundary_v1_rainfall_sensitivity.py",
    ROOT / "bin/scenarios/run_boundary_v1_rainfall_exposure.py",
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

# Active research-map governance docs. These are active and scanned, but a line
# that cites a deprecated term is allowed when the SAME line carries historical
# context (deprecated / legacy / historical / superseded / coined / shorthand /
# was renamed). This is a line-level allowlist, not a whole-file allowlist: a
# future contributor who adds a real `flood_hazard_proxy` identifier in a normal
# prose sentence in RESULTS.md will still be flagged.
ACTIVE_RESEARCH_MAP_DIR = ROOT / "context/docs/research-map"

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
    "Mining-proxy",
    "R-invariant",
    "sediment_risk_lowR_provisional",
    "rainfail",
]

# The bare words "proxy"/"Proxy" are flagged to catch newly-coined *_proxy
# identifier leaks in mentor-facing outputs, but they are normal English in
# internal governance prose ("OSM quarry/industrial proxy"). The terminology
# audit already reclassified 185/226 such hits as benign English usage. Internal
# research-map docs are scanned for the deprecated identifiers above; the bare
# word check is skipped for them.
GENERIC_TERMS = ["proxy", "Proxy"]

# Historical-context markers that mark a deprecated-term citation as legitimate
# documentation of the deprecation/renaming itself. Must appear on the SAME line
# as the deprecated term for the line to be allowed.
HISTORICAL_CONTEXT_MARKERS = (
    "deprecated",
    "deprecation",
    "legacy",
    "historical",
    "superseded",
    "coined",
    "shorthand",
    "was renamed",
    "old name",
    "renamed",
)


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def is_historical_context_line(line: str) -> bool:
    """True if the line carries historical/renaming context. A deprecated-term
    hit on such a line is a legitimate citation of the deprecation, not a live
    use."""
    lowered = line.lower()
    return any(marker in lowered for marker in HISTORICAL_CONTEXT_MARKERS)


def is_glossary_file(path: Path) -> bool:
    """The glossary legitimately quotes deprecated terms across many lines while
    defining them; it is the one file-level exception."""
    return path.resolve().relative_to(ROOT).parts == ("context", "docs", "glossary.md")


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
    # Active research-map governance docs (filenames always checked; content
    # hits allowed in the reference-history subset).
    if ACTIVE_RESEARCH_MAP_DIR.exists():
        for path in ACTIVE_RESEARCH_MAP_DIR.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                paths.append(path)
    return sorted(set(paths))


def is_research_map_doc(path: Path) -> bool:
    """True for files inside context/docs/research-map/. The bare-word generic
    'proxy' check is skipped for these internal governance docs (the deprecated
    *_proxy identifiers are still checked)."""
    rel_parts = path.resolve().relative_to(ROOT).parts
    return rel_parts[:3] == ("context", "docs", "research-map")


def scan_path(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    name = path.name
    for term in FORBIDDEN_TERMS:
        if term in name:
            rows.append({"path": rel(path), "where": "filename", "term": term, "line": "", "excerpt": name})
    # Filenames inside research-map are governance docs, not mentor-facing; do
    # not flag the bare word "proxy" in their filenames.
    if not is_research_map_doc(path):
        for term in GENERIC_TERMS:
            if term in name:
                rows.append({"path": rel(path), "where": "filename", "term": term, "line": "", "excerpt": name})

    if path.suffix.lower() not in TEXT_SUFFIXES:
        return rows
    # The glossary legitimately quotes deprecated terms across many lines while
    # defining them; it is the one whole-file exception.
    if is_glossary_file(path):
        return rows
    skip_generic = is_research_map_doc(path)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return rows
    for line_no, line in enumerate(text.splitlines(), start=1):
        # Line-level allowlist: a deprecated-term citation on a line that
        # carries historical/renaming context is documenting the deprecation,
        # not a live use. This catches future real violations in any file
        # (including research-map) while allowing the existing audit records.
        if is_historical_context_line(line):
            continue
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
        if skip_generic:
            continue
        for term in GENERIC_TERMS:
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
