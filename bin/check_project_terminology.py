#!/usr/bin/env python3
"""Scan the whole IFPM workspace for terminology-rule violations."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "outputs/zimbabwe_peru_prototype_comparison/full_project_terminology_check.csv"
DEFAULT_SUMMARY = ROOT / "outputs/zimbabwe_peru_prototype_comparison/full_project_terminology_check.md"

TEXT_SUFFIXES = {".csv", ".md", ".py", ".txt", ".json", ".yaml", ".yml", ".toml", ".rst"}
SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    "data",
    "exports",
    "tmp",
}
GENERATED_CHECK_OUTPUT_NAMES = {
    "active_terminology_check.csv",
    "full_project_terminology_check.csv",
    "full_project_terminology_check.md",
    "glossary_source_check.csv",
}

DEPRECATED_TERMS = [
    "flood_hazard_proxy",
    "erosion_structure_proxy",
    "road_accessibility_proxy",
    "rainfall_climatology_proxy",
    "river_proximity_proxy",
    "osm_mining_proxy",
    "closeness_to_mining_proxy",
    "distance_to_mining_proxy",
    "rehabilitation_proxy",
    "exposure_mining_proxy",
    "proxy_0_1",
    "Mining-proxy",
    "socioeconomic_exposure",
    "R-invariant",
    "sediment_risk_lowR_provisional",
    "rainfail",
]

GENERIC_TERMS = [" proxy", " proxies", "_proxy", "-proxy", "Proxy"]

ALLOWED_REFERENCE_FILES = {
    "bin/check_active_terminology.py",
    "bin/check_project_terminology.py",
    "context/docs/glossary.md",
}

# Historical-context markers that mark a deprecated-term citation as legitimate
# documentation of the deprecation/renaming itself. Must appear on the SAME line
# as the deprecated term for the line to be allowed. This is a line-level
# allowlist: a future real violation in any active file (including research-map
# docs) is still caught.
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

ACTIVE_PREFIXES = (
    "context/configs/",
    "context/docs/research-map/",
    "outputs/boundary_v1/criteria_stack_v0_2/",
    "outputs/boundary_v1/rainfall_sensitivity_v0_3/",
    "outputs/boundary_v1/rainfall_exposure_v0_4/",
    "outputs/srtm_1arcsec_peru_pilot/criteria_stack/",
    "outputs/srtm_1arcsec_peru_pilot/rainfall_criterion/",
    "outputs/srtm_1arcsec_peru_pilot/priority_scenarios/",
    "outputs/zimbabwe_peru_prototype_comparison/",
    "outputs/mentor_boss_priority_explanation/",
)

ACTIVE_FILES = {
    "AGENTS.md",
    "bin/check_active_terminology.py",
    "bin/check_glossary_sources.py",
    "bin/check_project_terminology.py",
    "bin/criteria/build_boundary_v1_criteria_stack.py",
    "bin/criteria/build_pe1_criteria_stack.py",
    "bin/criteria/build_boundary_v1_rainfall_criterion.py",
    "bin/criteria/build_pe1_rainfall_criterion.py",
    "bin/scenarios/run_boundary_v1_priority_scenarios.py",
    "bin/scenarios/run_boundary_v1_rainfall_sensitivity.py",
    "bin/scenarios/run_boundary_v1_rainfall_exposure.py",
    "bin/scenarios/run_pe1_priority_scenarios.py",
    "bin/visualize/plot_july18_integrated_priority_board.py",
    "bin/visualize/plot_mentor_boss_priority_explanation_package.py",
    "bin/visualize/plot_zimbabwe_peru_prototype_comparison.py",
}

ARCHIVAL_MARKERS = (
    "_archive/",
    "archive",
    "archived",
    "DEPRECATED",
    "deprecated",
    "superseded",
    "v1_autonomous_prototype_v0_1",
    "v1_autonomous_prototype_v0_2",
    "v1_usle_soil_loss",
    "rfactor_investigation",
    "explore_rfactor",
)

MENTOR_FACING_PREFIX = "context/docs/mentor-explanation/"
RESEARCH_MAP_PREFIX = "context/docs/research-map/"


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def is_active(path: str) -> bool:
    return path in ACTIVE_FILES or any(path.startswith(prefix) for prefix in ACTIVE_PREFIXES)


def is_allowed_reference(path: str) -> bool:
    return path in ALLOWED_REFERENCE_FILES


def is_historical_context_line(line: str) -> bool:
    """True if the line carries historical/renaming context. A deprecated-term
    citation on such a line is documenting the deprecation, not a live use."""
    lowered = line.lower()
    return any(marker in lowered for marker in HISTORICAL_CONTEXT_MARKERS)


def is_archival(path: str, line: str) -> bool:
    haystack = f"{path} {line}"
    return any(marker in haystack for marker in ARCHIVAL_MARKERS)


def classify(path: str, term: str, line: str) -> tuple[str, str]:
    if is_allowed_reference(path):
        return "allowed_reference", "glossary_or_checker_may_quote_deprecated_terms"
    # Line-level allowlist: a deprecated-term citation on a line that carries
    # historical/renaming context is documenting the deprecation, not a live
    # use. This applies in EVERY file (including active research-map docs), so
    # a future real violation in any active file is still caught while the
    # existing audit/decision records pass.
    if is_historical_context_line(line):
        return "allowed_reference", "line_documents_deprecation_or_rename"
    # Research-map governance docs are active but internal. The bare English
    # word "proxy/proxies" is benign here (it describes what a layer is, e.g.
    # "OSM quarry/industrial proxy"); only deprecated *_proxy identifiers would
    # be a real violation, and those are FORBIDDEN_TERMS caught above. Generic
    # proxy usage in research-map is needs_review, not violation.
    if path.startswith(RESEARCH_MAP_PREFIX) and term in GENERIC_TERMS:
        return "needs_review", "generic_proxy_word_in_internal_governance_doc"
    if is_active(path):
        return "violation", "deprecated_or_generic_term_in_active_workflow"
    if path.startswith(MENTOR_FACING_PREFIX):
        return "violation", "deprecated_or_generic_term_in_mentor_facing_document"
    if is_archival(path, line):
        return "archival_reference", "historical_or_deprecated_record"
    if term in GENERIC_TERMS:
        return "needs_review", "generic_proxy_word_outside_active_scope"
    return "needs_review", "deprecated_term_outside_active_scope"


def iter_text_files() -> list[Path]:
    paths: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.name in GENERATED_CHECK_OUTPUT_NAMES:
            continue
        parts = set(path.relative_to(ROOT).parts)
        if parts & SKIP_DIRS:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        paths.append(path)
    return sorted(paths)


def scan_file(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    path_rel = rel(path)
    terms = DEPRECATED_TERMS + GENERIC_TERMS
    for term in terms:
        if term not in path.name:
            continue
        status, reason = classify(path_rel, term, path.name)
        rows.append(
            {
                "path": path_rel,
                "line": "",
                "term": term,
                "status": status,
                "reason": reason,
                "excerpt": path.name,
            }
        )
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return rows
    for line_no, line in enumerate(text.splitlines(), start=1):
        for term in terms:
            if term not in line:
                continue
            status, reason = classify(path_rel, term, line)
            rows.append(
                {
                    "path": path_rel,
                    "line": str(line_no),
                    "term": term,
                    "status": status,
                    "reason": reason,
                    "excerpt": line.strip()[:260],
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "line", "term", "status", "reason", "excerpt"])
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, rows: list[dict[str, str]]) -> None:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    violations = [row for row in rows if row["status"] == "violation"]
    review = [row for row in rows if row["status"] == "needs_review"]
    lines = [
        "# Full Project Terminology Check",
        "",
        "Status meanings:",
        "",
        "- `violation`: deprecated or generic terminology in active workflow or mentor-facing material.",
        "- `needs_review`: non-active, non-archival text that may need wording cleanup.",
        "- `allowed_reference`: glossary/audit text that intentionally quotes deprecated terms.",
        "- `archival_reference`: historical, deprecated, or superseded record.",
        "",
        "## Counts",
        "",
    ]
    for key in ["violation", "needs_review", "allowed_reference", "archival_reference"]:
        lines.append(f"- {key}: {counts.get(key, 0)}")
    lines.extend(["", "## Violations", ""])
    if violations:
        for row in violations[:40]:
            lines.append(f"- `{row['path']}:{row['line']}` `{row['term']}` - {row['excerpt']}")
    else:
        lines.append("- None")
    lines.extend(["", "## Needs Review", ""])
    if review:
        for row in review[:80]:
            lines.append(f"- `{row['path']}:{row['line']}` `{row['term']}` - {row['excerpt']}")
    else:
        lines.append("- None")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--fail-on-needs-review", action="store_true")
    args = parser.parse_args()

    rows: list[dict[str, str]] = []
    for path in iter_text_files():
        if path.resolve() in {args.output.resolve(), args.summary.resolve()}:
            continue
        rows.extend(scan_file(path))

    write_csv(args.output, rows)
    write_summary(args.summary, rows)

    violations = [row for row in rows if row["status"] == "violation"]
    review = [row for row in rows if row["status"] == "needs_review"]
    print(f"terminology full-project check: {len(violations)} violation(s), {len(review)} needs-review hit(s)")
    print(f"details: {rel(args.output)}")
    print(f"summary: {rel(args.summary)}")
    if violations or (args.fail_on_needs_review and review):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
