#!/usr/bin/env python3
"""One-off literature verification: Moore & Nieber (1989) LS-factor exponents.

Local TOOLING script. Verifies which exponents (0.4/1.2 vs 0.6/1.3 vs other) are actually stated
in the Moore & Nieber (1989) original and in the SAGA GIS implementation, to confirm or correct
the exponent pair used in bin/factors/derive_v1_ls_factor.py.

Uses Playwright connect_over_cdp to localhost:9222 (system Chrome must run with
--remote-debugging-port=9222). Captures the visible text of each source page and saves it under
outputs/literature_verification/ for the record.

Usage:
    .venv/bin/python bin/investigate/verify_ls_factor_exponents.py
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = ROOT / "outputs/literature_verification"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Authoritative-ish sources. Goal: find the explicit LS exponents (m, n) in the Moore & Nieber
# raster LS form (As/22.13)^m * (sin(theta)/0.0896)^n. The SAGA module doc lists the method but
# NOT the exponents (they live in source code), so we target papers/notes that print the formula.
SOURCES = [
    {
        "id": "moore_nieber_1989_umn",
        "url": "https://digitalcommons.morris.umn.edu/cgi/viewcontent.cgi?article=2606&context=jmas",
        "note": "Moore & Nieber 1989 ORIGINAL (UMN full text) - the primary source for the exponents",
    },
    {
        "id": "usda_ars_gisus_m",
        "url": "https://www.tucson.ars.ag.gov/unit/publications/PDFfiles/2279.pdf",
        "note": "USDA-ARS GISus-M - states LS = (As/22.13)^m(sin/0.0896)^n, m(0.4-0.56), n(1.2-1.3)",
    },
    {
        "id": "jrc_esdac_palazzi",
        "url": "https://esdac.jrc.ec.europa.eu/public_path/shared_folder/euso/workshop_soil_erosion/farm_field_scale/15_Francesco_Palazzi.pdf",
        "note": "JRC/ESDAC - compares Moore-Nieber MN vs Desmet-Govers DG procedures",
    },
    {
        "id": "mdpi_water_ls_exponents",
        "url": "https://www.mdpi.com/2073-4441/13/24/3511",
        "note": "Applied RUSLE paper quoting an LS variant inline (0.4/1.3 with 1.6 coeff)",
    },
]


def extract(page, url: str) -> str:
    """Grab the visible body text, or the PDF.js text layer for in-browser PDFs.

    Chrome renders PDFs with its built-in viewer; the text lives in <span>s inside .textLayer
    divs, not in <body> inner_text. If the URL is a PDF, wait for the text layer and collect it.
    """
    if url.lower().endswith(".pdf") or "viewcontent.cgi" in url:
        try:
            page.wait_for_selector(".textLayer", timeout=20000)
            page.wait_for_timeout(2000)  # let more pages render
            spans = page.query_selector_all(".textLayer span")
            return "\n".join((s.inner_text() or "") for s in spans)
        except Exception:
            pass  # fall through to body text
    try:
        return page.inner_text("body", timeout=15000)
    except Exception:
        return page.content()


def find_exponent_contexts(text: str) -> list[str]:
    """Return snippets mentioning LS exponents / the standard LS constants."""
    hits = []
    norm = re.sub(r"\s+", " ", text)
    # (a) lines/areas mentioning the standard normalising constants.
    for kw in ["22.13", "0.0896", "0.0896)", "(As/", "specific catchment"]:
        for m in re.finditer(re.escape(kw), norm):
            start = max(0, m.start() - 90)
            hits.append(norm[start:m.end() + 90].strip()[:300])
    # (b) explicit exponent pairs of interest.
    for pat in [r"0\.4[^0-9]{0,6}1\.2", r"0\.6[^0-9]{0,6}1\.3", r"\^0\.[46]", r"\^1\.[23]",
                r"\bm\s*=\s*0\.[46]", r"\bn\s*=\s*1\.[23]"]:
        for m in re.finditer(pat, norm):
            start = max(0, m.start() - 90)
            hits.append(norm[start:m.end() + 90].strip()[:300])
    # de-dup while preserving order
    seen = set()
    out = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def main() -> None:
    print(f"launching Chromium (CDP browser) ...")
    with sync_playwright() as pw:
        # Prefer the system Chrome CDP if it is running; otherwise launch a bundled Chromium so the
        # verification does not depend on an externally-started browser.
        browser = None
        try:
            import urllib.request
            urllib.request.urlopen("http://localhost:9222/json/version", timeout=3).read()
            browser = pw.chromium.connect_over_cdp("http://localhost:9222")
            print("connected via system Chrome CDP (localhost:9222)")
        except Exception:
            browser = pw.chromium.launch(headless=True)
            print("system Chrome CDP unavailable; launched headless Chromium")
        # IMPORTANT (workspace rule): use the EXISTING browser/context. Do NOT close the browser
        # and do NOT open a new window. Reuse the first existing browser context; navigate within
        # a new tab (context.new_page opens a tab, not a window) or reuse an existing tab.
        contexts = browser.contexts
        context = contexts[0] if contexts else browser.new_context()
        # Reuse an existing blank/newtab page if present; otherwise open one tab.
        page = None
        for p in context.pages:
            if p.url.startswith("chrome://") or p.url == "about:blank":
                page = p
                break
        if page is None:
            page = context.new_page()
        page = context.new_page()

        summary = []
        for src in SOURCES:
            sid = src["id"]
            print(f"\n=== {sid}: {src['url']}")
            try:
                resp = page.goto(src["url"], wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(2500)
                text = extract(page, src["url"])
            except Exception as exc:
                print(f"  ERROR fetching: {exc}")
                summary.append({"id": sid, "url": src["url"], "error": str(exc)})
                continue

            (OUTPUT_DIR / f"{sid}.txt").write_text(text, encoding="utf-8")
            try:
                page.screenshot(path=str(OUTPUT_DIR / f"{sid}.png"), full_page=False)
            except Exception:
                pass

            hits = find_exponent_contexts(text)
            print(f"  saved {OUTPUT_DIR / f'{sid}.txt'} ({len(text)} chars); exponent-context hits: {len(hits)}")
            for h in hits[:6]:
                print(f"    > {h}")
            summary.append({
                "id": sid,
                "url": src["url"],
                "note": src["note"],
                "text_chars": len(text),
                "exponent_context_hits": hits[:12],
                "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })

        (OUTPUT_DIR / "ls_exponent_verification_summary.json").write_text(
            __import__("json").dumps(summary, indent=2), encoding="utf-8"
        )
        print(f"\nwrote {OUTPUT_DIR / 'ls_exponent_verification_summary.json'}")


if __name__ == "__main__":
    main()
