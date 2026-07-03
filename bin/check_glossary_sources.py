#!/usr/bin/env python3
"""Check that glossary source IDs are defined and source-backed."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GLOSSARY = ROOT / "context/docs/glossary.md"
DEFAULT_OUTPUT = ROOT / "outputs/zimbabwe_peru_prototype_comparison/glossary_source_check.csv"

SOURCE_REF_RE = re.compile(r"\[S(\d+)(?:,\s*S\d+)*\]")
SOURCE_ID_RE = re.compile(r"^- \*\*S(\d+)\*\*\s+(.*)$")
URL_RE = re.compile(r"https?://\S+")


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def referenced_sources(text: str) -> set[str]:
    refs: set[str] = set()
    for match in SOURCE_REF_RE.finditer(text):
        for source_id in re.findall(r"S\d+", match.group(0)):
            refs.add(source_id)
    return refs


def defined_sources(text: str) -> dict[str, str]:
    sources: dict[str, str] = {}
    for line in text.splitlines():
        match = SOURCE_ID_RE.match(line.strip())
        if not match:
            continue
        source_id = f"S{match.group(1)}"
        sources[source_id] = match.group(2).strip()
    return sources


def build_rows(text: str) -> list[dict[str, str]]:
    refs = referenced_sources(text)
    sources = defined_sources(text)
    rows: list[dict[str, str]] = []
    for source_id in sorted(refs | set(sources), key=lambda item: int(item[1:])):
        description = sources.get(source_id, "")
        issues: list[str] = []
        if source_id in refs and source_id not in sources:
            issues.append("referenced_but_not_defined")
        if source_id in sources and source_id not in refs:
            issues.append("defined_but_not_referenced")
        if source_id in sources and not URL_RE.search(description):
            issues.append("missing_url_or_doi_url")
        rows.append(
            {
                "source_id": source_id,
                "referenced": str(source_id in refs).lower(),
                "defined": str(source_id in sources).lower(),
                "has_url": str(bool(URL_RE.search(description))).lower(),
                "issues": ";".join(issues),
                "description": description,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source_id", "referenced", "defined", "has_url", "issues", "description"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glossary", type=Path, default=DEFAULT_GLOSSARY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    text = args.glossary.read_text(encoding="utf-8")
    rows = build_rows(text)
    write_csv(args.output, rows)
    failures = [row for row in rows if row["issues"]]
    if failures:
        print(f"glossary source check failed: {len(failures)} issue(s)")
        print(f"details: {rel(args.output)}")
        return 1
    print(f"glossary source check passed: {rel(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
