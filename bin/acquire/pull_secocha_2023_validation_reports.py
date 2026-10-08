#!/usr/bin/env python3
"""Acquire the two core official reports for the Secocha 2023 validation case."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import urllib.parse
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data/validation/secocha_2023_validation/official_reports"
TMP_DIR = ROOT / "data/tmp/secocha_2023_validation"
OUT_DIR = ROOT / "outputs/secocha_2023_validation"
TRANSPORT = {
    "executable": "curl",
    "arguments": ["--fail", "--location", "--show-error", "--silent"],
}

CATALOG: dict[str, Any] = {
    "event_id": "secocha_2023_historical_hazard_event",
    "event_date": "2023-02-05",
    "event_name": "Secocha 2023 debris-flow and flood-related disaster",
    "study_area": "Secocha and nearby localities, Mariano Nicolas Valcarcel, Camana, Arequipa, Peru",
    "claim_level": "validation_candidate",
    "enters_pim_score": False,
    "intended_use": (
        "External historical-event comparison with the current no-mining PIM and a separate "
        "mining co-location overlay; not a PIM input or weight source."
    ),
    "sources": [
        {
            "source_id": "ingemmet_a7367",
            "publisher": "INGEMMET",
            "title": (
                "Informe Tecnico N A7367: Evaluacion de peligros geologicos en el centro "
                "poblado Secocha y localidades cercanas"
            ),
            "report_date": "2023-03",
            "url": (
                "https://sigrid.cenepred.gob.pe/sigridv3/storage/biblioteca/"
                "16130_informe-tecnico-n0-a7367-evaluacion-de-peligros-geologicos-en-en-"
                "centro-poblado-secocha-y-las-localidades-la-poderosa-san-martin-posco-"
                "misky-y-pampayl.pdf"
            ),
            "filename": "ingemmet_a7367_secocha_hazard_assessment.pdf",
            "evidence_role": "field-assessed geological hazards, mapped channels and affected localities",
        },
        {
            "source_id": "indeci_emergency_report_1733",
            "publisher": "INDECI",
            "title": (
                "Informe de Emergencia N 1733, 20 May 2023: Lluvias intensas en el "
                "distrito de Mariano Nicolas Valcarcel"
            ),
            "report_date": "2023-05-20",
            "url": (
                "https://portal.indeci.gob.pe/wp-content/uploads/2023/05/"
                "INFORME-DE-EMERGENCIA-N%C2%BA-1733-20MAY2023-LLUVIAS-INTENSAS-EN-EL-"
                "DISTRITO-DE-MARIANO-NICOLAS-VALC%C3%81RCEL-AREQUIPA-13-DEE.pdf"
            ),
            "filename": "indeci_emergency_report_1733_2023-05-20.pdf",
            "evidence_role": "event chronology, affected places, impacts and response updates",
        },
    ],
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_pdf(source: dict[str, str]) -> dict[str, Any]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    destination = RAW_DIR / source["filename"]
    if not destination.exists():
        temporary = TMP_DIR / f"{source['filename']}.part"
        url = urllib.parse.quote(source["url"], safe=":/%?=&")
        subprocess.run(
            [
                TRANSPORT["executable"],
                *TRANSPORT["arguments"],
                "--max-time",
                "120",
                "--user-agent",
                "IFPM-data-acquisition/1.0",
                "--output",
                str(temporary),
                url,
            ],
            check=True,
        )
        if temporary.stat().st_size < 5 or temporary.read_bytes()[:5] != b"%PDF-":
            raise RuntimeError(f"downloaded content is not a PDF: {source['source_id']}")
        temporary.replace(destination)

    if destination.read_bytes()[:5] != b"%PDF-":
        raise RuntimeError(f"stored content is not a PDF: {destination}")
    return {
        **source,
        "path": str(destination.relative_to(ROOT)),
        "size_bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog-only", action="store_true")
    parser.add_argument("--transport-only", action="store_true")
    args = parser.parse_args()
    if args.transport_only:
        print(json.dumps(TRANSPORT, ensure_ascii=False, indent=2))
        return
    if args.catalog_only:
        print(json.dumps(CATALOG, ensure_ascii=False, indent=2))
        return

    records = [download_pdf(source) for source in CATALOG["sources"]]
    manifest = {
        **CATALOG,
        "access_date": date.today().isoformat(),
        "sources": records,
        "download_status": "complete",
        "next_stage": "extract mapped locations and report-dated impact observations",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT_DIR / "official_reports_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
