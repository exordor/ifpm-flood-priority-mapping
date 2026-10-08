#!/usr/bin/env python3
"""Manage canonical IFPM QGIS package paths and split the legacy combined package."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_ROOT = ROOT / "exports/qgis_packages"
LEGACY_SOURCE = ROOT / "exports/IFPM_QGIS_Project_Package"

DEFAULT_CURRENT_PACKAGES = {
    "goslar_fullaudit": ROOT / "exports/IFPM_Goslar_QGIS_FullAudit_Package",
    "goslar_reviewmap": ROOT / "exports/IFPM_Goslar_QGIS_ReviewMap_Package",
    "secocha_fullaudit": ROOT / "exports/IFPM_Peru_Secocha_QGIS_FullAudit_Package",
    "secocha_reviewmap": ROOT / "exports/IFPM_Peru_Secocha_QGIS_ReviewMap_Package",
}

PACKAGE_PATHS = {
    "goslar_fullaudit": "goslar/FullAudit",
    "goslar_reviewmap": "goslar/ReviewMap",
    "secocha_fullaudit": "secocha/FullAudit",
    "secocha_reviewmap": "secocha/ReviewMap",
    "legacy_peru_fullaudit": "legacy_peru_vitor_la_joya_siguas/FullAudit",
    "legacy_zimbabwe_fullaudit": "legacy_zimbabwe_upper_mzingwane/FullAudit",
}

LEGACY_SITES = {
    "peru": {
        "package_key": "legacy_peru_fullaudit",
        "source_project": "IFPM_Peru.qgz",
        "project": "IFPM_Peru_Legacy_FullAudit.qgz",
        "display_name": "Legacy Peru Vitor-La Joya-Siguas FullAudit",
    },
    "zimbabwe": {
        "package_key": "legacy_zimbabwe_fullaudit",
        "source_project": "IFPM_Zimbabwe.qgz",
        "project": "IFPM_Zimbabwe_Legacy_FullAudit.qgz",
        "display_name": "Legacy Zimbabwe Upper Mzingwane FullAudit",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def catalog() -> dict[str, object]:
    return {
        "canonical_root": "exports/qgis_packages",
        "packages": PACKAGE_PATHS,
        "optional_legacy_combined_archive": "_archive/legacy_peru_zimbabwe_combined",
    }


def link_or_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def deterministic_zip(package: Path) -> Path:
    archive_path = package.with_suffix(".zip")
    temporary = archive_path.with_name(f".{archive_path.name}.tmp")
    if temporary.exists():
        temporary.unlink()
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(path for path in package.rglob("*") if path.is_file()):
            relative = source.relative_to(package)
            if any(part.startswith(".") for part in relative.parts):
                continue
            info = zipfile.ZipInfo(
                (Path(package.name) / relative).as_posix(),
                date_time=(1980, 1, 1, 0, 0, 0),
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes())
    temporary.replace(archive_path)
    return archive_path


def write_manifest(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def split_legacy_package(source: Path, destination_root: Path) -> dict[str, dict[str, object]]:
    manifest = source / "manifest.csv"
    if not manifest.exists():
        raise FileNotFoundError(manifest)
    with manifest.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    source_validation = json.loads((source / "validation.json").read_text(encoding="utf-8"))
    if source_validation.get("status") != "package_integrity_valid":
        raise RuntimeError("legacy combined source package is not integrity-valid")

    index: dict[str, dict[str, object]] = {}
    for site, site_config in LEGACY_SITES.items():
        site_rows = [row for row in rows if row["site"] == site]
        if not site_rows:
            raise RuntimeError(f"legacy package has no rows for {site}")
        package = destination_root / PACKAGE_PATHS[str(site_config["package_key"])]
        staging = package.with_name(f".{package.name}.tmp")
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)

        source_project = source / str(site_config["source_project"])
        target_project = staging / str(site_config["project"])
        link_or_copy(source_project, target_project)
        for row in site_rows:
            relative = Path(row["portable_source_path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise RuntimeError(f"unsafe portable source path: {relative}")
            input_layer = source / relative
            if not input_layer.exists():
                raise FileNotFoundError(input_layer)
            if sha256(input_layer) != row["portable_sha256"]:
                raise RuntimeError(f"checksum mismatch for {site}/{row['layer_key']}")
            link_or_copy(input_layer, staging / relative)
            style = source / "styles" / f"{site}_{row['layer_key']}.qml"
            if style.exists():
                link_or_copy(style, staging / "styles" / style.name)

        write_manifest(staging / "manifest.csv", site_rows, fieldnames)
        (staging / "README.txt").write_text(
            f"IFPM {site_config['display_name']} QGIS package\n\n"
            f"Open {site_config['project']}. This standalone legacy package was split from the "
            "previous Peru/Zimbabwe combined handoff. It preserves the original claim levels and "
            "does not upgrade the historical model evidence.\n",
            encoding="utf-8",
        )
        validation = {
            "status": "package_integrity_valid",
            "package_role": "standalone_legacy_fullaudit",
            "site": site,
            "project": str(site_config["project"]),
            "manifest_layer_count": len(site_rows),
            "source_combined_validation_status": source_validation["status"],
            "project_sha256": sha256(target_project),
            "all_layer_checksums_match": True,
        }
        (staging / "validation.json").write_text(
            json.dumps(validation, indent=2) + "\n", encoding="utf-8"
        )

        if package.exists():
            shutil.rmtree(package)
        package.parent.mkdir(parents=True, exist_ok=True)
        staging.replace(package)
        archive = deterministic_zip(package)
        package_key = str(site_config["package_key"])
        index[package_key] = {
            "path": str(package.relative_to(destination_root)),
            "project": str(site_config["project"]),
            "layer_count": len(site_rows),
            "claim_boundary": "legacy claim levels preserved; no scientific upgrade",
            "zip": str(archive.relative_to(destination_root)),
            "zip_sha256": sha256(archive),
        }

    write_index(destination_root, index)
    return index


def read_index(destination_root: Path) -> dict[str, dict[str, object]]:
    path = destination_root / "package_index.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_index(destination_root: Path, updates: dict[str, dict[str, object]]) -> None:
    destination_root.mkdir(parents=True, exist_ok=True)
    index = read_index(destination_root)
    index.update(updates)
    (destination_root / "package_index.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def refresh_index(destination_root: Path) -> dict[str, dict[str, object]]:
    """Recompute index metadata for every canonical package currently on disk."""
    current = read_index(destination_root)
    updates: dict[str, dict[str, object]] = {}
    for key, relative_path in PACKAGE_PATHS.items():
        package = destination_root / relative_path
        if not package.is_dir():
            continue
        manifest = package / "manifest.csv"
        archive = package.with_suffix(".zip")
        projects = sorted(package.glob("*.qgz"))
        if not manifest.is_file() or not archive.is_file() or len(projects) != 1:
            raise RuntimeError(f"incomplete canonical package: {package}")
        with manifest.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        record: dict[str, object] = {
            "path": relative_path,
            "project": projects[0].name,
            "layer_count": len(rows),
            "zip": str(archive.relative_to(destination_root)),
            "zip_sha256": sha256(archive),
        }
        if "claim_boundary" in current.get(key, {}):
            record["claim_boundary"] = current[key]["claim_boundary"]
        updates[key] = record

    archive_root = destination_root / "_archive/legacy_peru_zimbabwe_combined"
    combined_packages = sorted(archive_root.glob("*/manifest.csv")) if archive_root.exists() else []
    combined_zips = sorted(archive_root.glob("*.zip")) if archive_root.exists() else []
    if combined_packages or combined_zips:
        if len(combined_packages) != 1 or len(combined_zips) != 1:
            raise RuntimeError(f"ambiguous combined archive contents: {archive_root}")
        combined_dir = combined_packages[0].parent
        updates["legacy_combined_archive"] = {
            "path": str(combined_dir.relative_to(destination_root)),
            "zip": str(combined_zips[0].relative_to(destination_root)),
            "zip_sha256": sha256(combined_zips[0]),
            "role": "read_only_combined_source_archive",
        }

    destination_root.mkdir(parents=True, exist_ok=True)
    (destination_root / "package_index.json").write_text(
        json.dumps(updates, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return updates


def parse_current_package(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("current package must be KEY=PATH")
    key, raw_path = value.split("=", 1)
    if key not in DEFAULT_CURRENT_PACKAGES:
        raise argparse.ArgumentTypeError(f"unknown current package key: {key}")
    return key, Path(raw_path).expanduser().resolve()


def move_current_packages(
    destination_root: Path,
    packages: dict[str, Path],
) -> dict[str, dict[str, object]]:
    updates: dict[str, dict[str, object]] = {}
    for key, source in packages.items():
        if key not in DEFAULT_CURRENT_PACKAGES:
            raise ValueError(f"unsupported current package key: {key}")
        if not source.is_dir():
            raise FileNotFoundError(source)
        source_archive = source.with_suffix(".zip")
        if not source_archive.is_file():
            raise FileNotFoundError(source_archive)
        manifest = source / "manifest.csv"
        if not manifest.exists():
            raise FileNotFoundError(manifest)
        with manifest.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        target = destination_root / PACKAGE_PATHS[key]
        target_archive = target.with_suffix(".zip")
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            shutil.rmtree(target)
        if target_archive.exists():
            target_archive.unlink()
        source.replace(target)
        source_archive.replace(target_archive)
        updates[key] = {
            "path": str(target.relative_to(destination_root)),
            "project": next(path.name for path in target.glob("*.qgz")),
            "layer_count": len(rows),
            "zip": str(target_archive.relative_to(destination_root)),
            "zip_sha256": sha256(target_archive),
        }
    write_index(destination_root, updates)
    return updates


def archive_combined_package(source: Path, destination_root: Path) -> dict[str, object]:
    source_archive = source.with_suffix(".zip")
    if not source.is_dir():
        raise FileNotFoundError(source)
    if not source_archive.is_file():
        raise FileNotFoundError(source_archive)
    archive_root = destination_root / "_archive/legacy_peru_zimbabwe_combined"
    archive_root.mkdir(parents=True, exist_ok=True)
    target = archive_root / source.name
    target_archive = archive_root / source_archive.name
    if target.exists():
        shutil.rmtree(target)
    if target_archive.exists():
        target_archive.unlink()
    source.replace(target)
    source_archive.replace(target_archive)
    record = {
        "path": str(target.relative_to(destination_root)),
        "zip": str(target_archive.relative_to(destination_root)),
        "zip_sha256": sha256(target_archive),
        "role": "read_only_combined_source_archive",
    }
    write_index(destination_root, {"legacy_combined_archive": record})
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog-only", action="store_true")
    parser.add_argument("--source-dir", type=Path, default=LEGACY_SOURCE)
    parser.add_argument("--destination-root", type=Path, default=CANONICAL_ROOT)
    parser.add_argument("--split-only", action="store_true")
    parser.add_argument("--skip-split", action="store_true")
    parser.add_argument("--move-current", action="store_true")
    parser.add_argument("--current-package", action="append", type=parse_current_package, default=[])
    parser.add_argument("--archive-combined", action="store_true")
    parser.add_argument("--refresh-index", action="store_true")
    args = parser.parse_args()
    if args.catalog_only:
        print(json.dumps(catalog(), indent=2))
        return 0
    destination_root = args.destination_root.resolve()
    result: dict[str, dict[str, object]] = {}
    if not args.skip_split:
        result.update(split_legacy_package(args.source_dir.resolve(), destination_root))
    if args.move_current:
        packages = dict(args.current_package) if args.current_package else DEFAULT_CURRENT_PACKAGES
        result.update(move_current_packages(destination_root, packages))
    if args.archive_combined:
        result["legacy_combined_archive"] = archive_combined_package(
            args.source_dir.resolve(), destination_root
        )
    if args.refresh_index:
        result.update(refresh_index(destination_root))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
