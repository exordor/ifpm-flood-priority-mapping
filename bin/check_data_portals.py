#!/usr/bin/env python3
"""Check data portal reachability, login requirements, and download mechanisms via CDP.

Local TOOLING script. Drives the system Chrome through Playwright (CDP) to inspect each data
portal URL that appears in the IFPM dataset registries / preflight scaffolding. Captures status,
final URL, title, login-wall detection, download/API link detection, licence keywords, and a
screenshot. Outputs a JSON report and PNG screenshots under outputs/data_portal_check/.

Usage:
    .venv/bin/python bin/check_data_portals.py

This is a pre-download verification tool. It does not download any dataset.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path("outputs/data_portal_check")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Portals to verify. Grouped by the dataset family they relate to.
PORTALS = [
    # P2/R2.1 SoilGrids (sediment K-factor candidate)
    {"group": "SoilGrids", "url": "https://soilgrids.org/"},
    {"group": "SoilGrids", "url": "https://www.isric.org/explore/soilgrids"},
    {"group": "SoilGrids", "url": "https://www.isric.org/explore/soilgrids/soilgrids-access"},
    # SoilGrids direct file index (discovered 2026-06-15: redirects to an Apache directory listing)
    {"group": "SoilGrids", "url": "https://files.isric.org/soilgrids/latest/data/"},
    # P1/R1.1 EM-DAT (validation candidate)
    {"group": "EM-DAT", "url": "https://www.emdat.be/"},
    {"group": "EM-DAT", "url": "https://data.humdata.org/dataset/emdat-international-disaster-database"},
    # P1/R1.1 GloFAS (validation candidate) - search page works; specific dataset id changed
    {"group": "GloFAS-CDS", "url": "https://cds.climate.copernicus.eu/datasets?keywords=glofas"},
    # Existing sources to re-verify
    {"group": "CHIRPS", "url": "https://www.chc.ucsb.edu/data/chirps"},
    {"group": "HydroSHEDS", "url": "https://www.hydrosheds.org/products"},
    {"group": "ESA-WorldCover", "url": "https://esa-worldcover.org/en"},
    {"group": "WorldPop", "url": "https://hub.worldpop.org/"},
    {"group": "HDX", "url": "https://data.humdata.org/"},
]

LOGIN_KEYWORDS = ["sign in", "log in", "login", "create an account", "register", "sign-in"]
LOGIN_URL_HINTS = ["/login", "/signin", "/sign-in", "/account/login", "/register"]
LICENCE_KEYWORDS = ["licence", "license", "cc by", "creative commons", "attribution", "open data"]
DIRECT_FILE_EXT = (".zip", ".tif", ".tiff", ".nc", ".csv", ".geotiff", ".shp", ".gpkg", ".tar.gz")
API_HINTS = ["/api/", "/wcs", "/wms", "/odata", "/services/", "download"]


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:80]


def check_page(page, url: str) -> dict:
    result: dict = {"requested_url": url}
    try:
        response = page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(2500)  # allow JS renders / redirects
        result["status"] = response.status if response else None
        result["final_url"] = page.url
        result["title"] = (page.title() or "").strip()[:200]
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"[:300]
        result["status"] = None
        result["final_url"] = url
        result["title"] = ""
        return result

    body_text = ""
    try:
        body_text = (page.inner_text("body") or "").lower()[:8000]
    except Exception:
        body_text = ""

    parsed = urlparse(page.url)
    path_lower = (parsed.path or "").lower()
    result["login_url_hint"] = any(hint in path_lower for hint in LOGIN_URL_HINTS)
    result["login_text_hint"] = any(kw in body_text for kw in LOGIN_KEYWORDS)
    result["login_required_likely"] = bool(result["login_url_hint"] or result["login_text_hint"])
    result["licence_seen"] = [kw for kw in LICENCE_KEYWORDS if kw in body_text]

    # Collect candidate download / API links from the DOM.
    links: list[dict] = []
    try:
        anchors = page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => ({href: e.href, text: (e.textContent||'').trim().slice(0,80)}))",
        )
    except Exception:
        anchors = []
    seen = set()
    for a in anchors:
        href = (a.get("href") or "").strip()
        if not href or href.startswith("javascript:") or href in seen:
            continue
        href_lower = href.lower()
        reason = None
        if href_lower.endswith(DIRECT_FILE_EXT):
            reason = "direct-file"
        elif any(hint in href_lower for hint in API_HINTS):
            reason = "api-or-download"
        elif href_lower.endswith("/") and ("data" in href_lower or "download" in href_lower):
            reason = "directory-listing"
        if reason:
            seen.add(href)
            links.append({"href": href[:200], "text": a.get("text", ""), "kind": reason})
    result["candidate_download_links"] = links[:25]
    result["download_link_count"] = len(links)

    # Buttons with download-related text (JS-driven downloads).
    try:
        buttons = page.eval_on_selector_all(
            "button, [role='button'], input[type='submit']",
            "els => els.map(e => (e.textContent||e.value||'').trim().slice(0,60))",
        )
    except Exception:
        buttons = []
    dl_buttons = [b for b in buttons if b and any(k in b.lower() for k in ("download", "export", "request", "order", "get data", "submit"))]
    result["download_buttons"] = dl_buttons[:10]

    # File-extension / API patterns mentioned in page text (e.g. in docs or tables).
    text_patterns = sorted(set(re.findall(r"[\w./-]+\.(?:tif|tiff|nc|csv|zip|geotiff|shp|gpkg)\b", body_text)))
    result["text_file_mentions"] = text_patterns[:15]

    # Screenshot.
    slug = slugify(url)
    shot_path = OUTPUT_DIR / f"{slug}.png"
    try:
        page.screenshot(path=str(shot_path), full_page=False, timeout=15000)
        result["screenshot"] = str(shot_path)
    except Exception as exc:
        result["screenshot_error"] = f"{type(exc).__name__}: {exc}"[:150]

    return result


def main() -> None:
    report: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": "bin/check_data_portals.py (Playwright connect_over_cdp to localhost:9222)",
        "note": "Pre-download portal verification via the user's running Chrome. No dataset downloaded.",
        "results": [],
    }
    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()
        for portal in PORTALS:
            print(f"[check] {portal['group']}: {portal['url']}")
            res = check_page(page, portal["url"])
            res["group"] = portal["group"]
            report["results"].append(res)
            status = res.get("status")
            login = res.get("login_required_likely")
            print(f"   -> status={status} login_likely={login} links={res.get('download_link_count',0)} buttons={len(res.get('download_buttons',[]))}")
        # Close only our page; do NOT close the user's browser.
        try:
            page.close()
        except Exception:
            pass

    report_path = OUTPUT_DIR / "portal_check_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nreport: {report_path}")
    print(f"screenshots: {OUTPUT_DIR}")

    # Console summary table.
    print("\n=== SUMMARY ===")
    print(f"{'GROUP':<16} {'STATUS':<7} {'LOGIN':<6} {'LINKS':<6} URL")
    for r in report["results"]:
        print(
            f"{r.get('group',''):<16} "
            f"{str(r.get('status','')):<7} "
            f"{str(r.get('login_required_likely','')):<6} "
            f"{str(r.get('download_link_count',0)):<6} "
            f"{r.get('requested_url','')}"
        )


if __name__ == "__main__":
    main()
