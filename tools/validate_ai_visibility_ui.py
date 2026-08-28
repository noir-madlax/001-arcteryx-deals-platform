#!/usr/bin/env python3
"""Browser acceptance for GearDrop's localized AI-visibility surfaces."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright


APP_STORE_URL = "https://apps.apple.com/us/app/geardrop-outdoor-deals/id6790165332"
CANONICAL_ORIGIN = "https://geardrop.100app.dev/"
PATHS = (
    "/",
    "/en/",
    "/insights/catalog-coverage.html",
    "/insights/brand-source-matrix.html",
    "/insights/regional-coverage.html",
    "/en/insights/brand-source-matrix.html",
)
VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "mobile": {"width": 390, "height": 844},
}


def expected_language(path: str) -> str:
    return "en-US" if path == "/en/" or path.startswith("/en/") else "zh-CN"


def expected_alternates(base_url: str, path: str) -> dict[str, str]:
    if path in {"/", "/en/"}:
        zh_path, en_path = "/", "/en/"
    elif path.startswith("/en/"):
        zh_path, en_path = path.removeprefix("/en"), path
    else:
        zh_path, en_path = path, f"/en{path}"
    return {
        "zh-CN": urljoin(base_url, zh_path.lstrip("/")),
        "en-US": urljoin(base_url, en_path.lstrip("/")),
        "x-default": urljoin(base_url, zh_path.lstrip("/")),
    }


def safe_slug(path: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-") or "home"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8765/")
    parser.add_argument("--screenshot-dir", type=Path)
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/") + "/"
    if args.screenshot_dir:
        args.screenshot_dir.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, object]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for viewport_name, viewport in VIEWPORTS.items():
            context = browser.new_context(viewport=viewport)
            for path in PATHS:
                page = context.new_page()
                console_errors: list[str] = []
                page_errors: list[str] = []
                page.on(
                    "console",
                    lambda message, errors=console_errors: errors.append(message.text)
                    if message.type == "error"
                    else None,
                )
                page.on("pageerror", lambda error, errors=page_errors: errors.append(str(error)))
                response = page.goto(urljoin(base_url, path.lstrip("/")), wait_until="domcontentloaded")
                page.locator("h1").first.wait_for(state="visible")
                if path == "/":
                    page.wait_for_function(
                        "document.documentElement.dataset.catalogPhase === 'complete'",
                        timeout=30_000,
                    )
                page.wait_for_timeout(400)
                result = page.evaluate(
                    """({appStoreUrl}) => {
                        const alternates = {};
                        document.querySelectorAll('link[rel="alternate"][hreflang]').forEach(link => {
                            alternates[link.hreflang] = link.href;
                        });
                        const appTargets = [...document.querySelectorAll('.header-app-link, .app-store-status')]
                            .filter(node => node.href === appStoreUrl)
                            .filter(node => {
                                const rect = node.getBoundingClientRect();
                                const style = getComputedStyle(node);
                                return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden';
                            })
                            .map(node => {
                                const rect = node.getBoundingClientRect();
                                return {width: rect.width, height: rect.height, text: node.textContent.trim()};
                            });
                        const tableWrap = document.querySelector('.data-table-wrap');
                        return {
                            lang: document.documentElement.lang,
                            h1Count: document.querySelectorAll('h1').length,
                            canonical: document.querySelector('link[rel="canonical"]')?.href || '',
                            alternates,
                            documentWidth: document.documentElement.scrollWidth,
                            viewportWidth: document.documentElement.clientWidth,
                            appTargets,
                            tableRows: document.querySelectorAll('.data-table tbody tr').length,
                            tableScrolls: tableWrap ? tableWrap.scrollWidth > tableWrap.clientWidth : false,
                            tableOverflow: tableWrap ? getComputedStyle(tableWrap).overflowX : '',
                            catalogPhase: document.documentElement.dataset.catalogPhase || '',
                            productCards: document.querySelectorAll('.card').length,
                        };
                    }""",
                    {"appStoreUrl": APP_STORE_URL},
                )
                expected_canonical = urljoin(CANONICAL_ORIGIN, path.lstrip("/"))
                expected_alt = expected_alternates(CANONICAL_ORIGIN, path)
                failures = []
                if not response or response.status >= 400:
                    failures.append(f"http_status={response.status if response else 'none'}")
                if result["lang"] != expected_language(path):
                    failures.append(f"lang={result['lang']}")
                if result["h1Count"] != 1:
                    failures.append(f"h1_count={result['h1Count']}")
                if result["canonical"] != expected_canonical:
                    failures.append(f"canonical={result['canonical']}")
                if result["alternates"] != expected_alt:
                    failures.append("hreflang_mismatch")
                if result["documentWidth"] > result["viewportWidth"] + 1:
                    failures.append(
                        f"document_overflow={result['documentWidth'] - result['viewportWidth']}px"
                    )
                if path == "/":
                    if not result["appTargets"]:
                        failures.append("official_app_link_not_visible")
                    if viewport_name == "mobile" and any(
                        target["height"] < 44 for target in result["appTargets"]
                    ):
                        failures.append("official_app_touch_target_below_44px")
                    if result["catalogPhase"] != "complete" or result["productCards"] < 1:
                        failures.append(
                            f"catalog_runtime={result['catalogPhase']} cards={result['productCards']}"
                        )
                if "matrix" in path:
                    if result["tableRows"] < 1:
                        failures.append("matrix_has_no_rows")
                    if viewport_name == "mobile" and not (
                        result["tableScrolls"] and result["tableOverflow"] == "auto"
                    ):
                        failures.append("matrix_mobile_scroll_contract_missing")
                if console_errors:
                    failures.append(f"console_errors={len(console_errors)}")
                if page_errors:
                    failures.append(f"page_errors={len(page_errors)}")
                checks.append(
                    {
                        "viewport": viewport_name,
                        "path": path,
                        "status": "pass" if not failures else "fail",
                        "failures": failures,
                        "geometry": {
                            "document_width": result["documentWidth"],
                            "viewport_width": result["viewportWidth"],
                            "app_target_heights": [round(item["height"], 1) for item in result["appTargets"]],
                            "table_rows": result["tableRows"],
                            "table_scrolls": result["tableScrolls"],
                            "catalog_phase": result["catalogPhase"],
                            "product_cards": result["productCards"],
                        },
                        "console_errors": console_errors,
                        "page_errors": page_errors,
                    }
                )
                if args.screenshot_dir and (
                    (path == "/" and viewport_name == "mobile")
                    or "brand-source-matrix" in path
                ):
                    page.screenshot(
                        path=args.screenshot_dir / f"{viewport_name}-{safe_slug(path)}.png",
                        full_page=path != "/",
                    )
                page.close()
            context.close()
        browser.close()

    failed = [check for check in checks if check["status"] == "fail"]
    print(
        json.dumps(
            {
                "base_url": base_url,
                "summary": {"passed": len(checks) - len(failed), "failed": len(failed), "total": len(checks)},
                "checks": checks,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
