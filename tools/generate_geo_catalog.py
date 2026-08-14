#!/usr/bin/env python3
"""Generate GearDrop's product sitemap and timestamped catalog coverage page."""

from __future__ import annotations

import argparse
import html
import http.client
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://001.100app.dev"
PAGE_SIZE = 1000
MAX_PAGES = 50

BRAND_LABELS = {
    "arcteryx": "Arc'teryx",
    "burton": "Burton",
    "patagonia": "Patagonia",
}

PLATFORM_LABELS = {
    "arcteryx_outlet": "Arc'teryx Outlet",
    "backcountry": "Backcountry",
    "burton": "Burton",
    "evo": "EVO",
    "mec": "MEC",
    "rei": "REI",
    "ssense": "SSENSE",
}

REGION_LABELS = {
    "at": "奥地利",
    "au": "澳大利亚",
    "be": "比利时",
    "ca": "加拿大",
    "ch": "瑞士",
    "de": "德国",
    "dk": "丹麦",
    "es": "西班牙",
    "fi": "芬兰",
    "fr": "法国",
    "gb": "英国",
    "ie": "爱尔兰",
    "it": "意大利",
    "jp": "日本",
    "nl": "荷兰",
    "se": "瑞典",
    "us": "美国",
}


def extract_supabase_config(template_path: Path) -> tuple[str, str]:
    source = template_path.read_text(encoding="utf-8")
    url_match = re.search(r"^const SUPABASE_URL\s*=\s*'([^']+)';", source, re.MULTILINE)
    key_match = re.search(r"^const SUPABASE_ANON\s*=\s*'([^']+)';", source, re.MULTILINE)
    if not url_match or not key_match:
        raise ValueError(f"Could not read public Supabase config from {template_path}")
    return url_match.group(1), key_match.group(1)


def fetch_json(url: str, headers: dict[str, str], retries: int = 3) -> Any:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            http.client.IncompleteRead,
            ConnectionError,
            OSError,
        ) as error:
            last_error = error
            if attempt + 1 < retries:
                print(
                    "catalog fetch retry "
                    f"{attempt + 1}/{retries} after {type(error).__name__}",
                    file=sys.stderr,
                )
                time.sleep(2**attempt)
    raise RuntimeError(f"Failed to fetch catalog after {retries} attempts: {last_error}")


def fetch_online_rows(template_path: Path) -> list[dict[str, Any]]:
    supabase_url, anon_key = extract_supabase_config(template_path)
    headers = {"apikey": anon_key, "Authorization": f"Bearer {anon_key}"}
    fields = "sku_id,brand,dealer,region,last_updated,status"
    rows: list[dict[str, Any]] = []
    for page in range(MAX_PAGES):
        params = urllib.parse.urlencode(
            {
                "select": fields,
                "status": "eq.active",
                "order": "sku_id.asc",
                "limit": PAGE_SIZE,
                "offset": page * PAGE_SIZE,
            },
            safe=",.",
        )
        url = f"{supabase_url.rstrip('/')}/rest/v1/products?{params}"
        batch = fetch_json(url, headers)
        if not isinstance(batch, list):
            raise ValueError(f"Catalog page {page} was not a JSON array")
        rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
    else:
        raise RuntimeError(f"Catalog exceeded safety limit of {PAGE_SIZE * MAX_PAGES} rows")
    return rows


def load_input_rows(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        return payload["rows"]
    raise ValueError("Input JSON must be an array or an object with a rows array")


def normalize_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    by_sku: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("status") not in {None, "active"}:
            continue
        sku = str(row.get("sku_id") or "").strip()
        if not sku:
            continue
        previous = by_sku.get(sku)
        if previous is None or str(row.get("last_updated") or "") > str(
            previous.get("last_updated") or ""
        ):
            by_sku[sku] = dict(row)
    return [by_sku[sku] for sku in sorted(by_sku)]


def product_url(sku_id: str) -> str:
    encoded = urllib.parse.quote(sku_id, safe="")
    return f"{SITE_URL}/p?sku={encoded}"


def valid_date(value: Any) -> str | None:
    text = str(value or "")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", text):
        return text[:10]
    return None


def render_product_sitemap(rows: list[dict[str, Any]]) -> str:
    entries = []
    for row in rows:
        loc = html.escape(product_url(str(row["sku_id"])), quote=True)
        lastmod = valid_date(row.get("last_updated"))
        modified = f"\n    <lastmod>{lastmod}</lastmod>" if lastmod else ""
        entries.append(
            "  <url>\n"
            f"    <loc>{loc}</loc>{modified}\n"
            "    <changefreq>daily</changefreq>\n"
            "    <priority>0.6</priority>\n"
            "  </url>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )


def labeled_counts(counter: Counter[str], labels: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {"id": key, "label": labels.get(key, key or "未标记"), "count": counter[key]}
        for key in sorted(counter, key=lambda item: (-counter[item], item))
    ]


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    timestamps = [str(row.get("last_updated") or "") for row in rows if row.get("last_updated")]
    latest_observation = max(timestamps) if timestamps else None
    return {
        "schema_version": "1.0.0",
        "entity": "GearDrop Outdoor Deals",
        "canonical_url": f"{SITE_URL}/",
        "snapshot_observed_at": latest_observation,
        "active_product_urls": len(rows),
        "brands": labeled_counts(
            Counter(str(row.get("brand") or "unknown").lower() for row in rows),
            BRAND_LABELS,
        ),
        "platforms": labeled_counts(
            Counter(str(row.get("dealer") or "arcteryx_outlet").lower() for row in rows),
            PLATFORM_LABELS,
        ),
        "regions": labeled_counts(
            Counter(str(row.get("region") or "unknown").lower() for row in rows),
            REGION_LABELS,
        ),
        "measurement_boundary": (
            "Counts describe active GearDrop product URLs at the recorded observation time. "
            "They do not prove retailer stock, search indexing, AI mention, citation, or recommendation."
        ),
        "methodology_url": f"{SITE_URL}/methodology.html",
        "product_sitemap_url": f"{SITE_URL}/sitemap-products.xml",
    }


def render_fact_rows(items: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"<dt>{html.escape(str(item['label']))}</dt><dd>{int(item['count']):,} 个商品 URL</dd>"
        for item in items
    )


def render_status_html(summary: dict[str, Any]) -> str:
    observed = summary["snapshot_observed_at"] or "无可用时间"
    modified = valid_date(observed) or "2026-08-14"
    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": f"{SITE_URL}/#organization",
                "name": "GearDrop",
                "alternateName": "GearDrop Outdoor Deals",
                "url": f"{SITE_URL}/",
                "logo": f"{SITE_URL}/assets/brand/icon-512.png",
                "publishingPrinciples": f"{SITE_URL}/methodology.html",
            },
            {
                "@type": "Dataset",
                "@id": f"{SITE_URL}/catalog-status.html#dataset",
                "name": "GearDrop active catalog coverage snapshot",
                "description": summary["measurement_boundary"],
                "url": f"{SITE_URL}/catalog-status.html",
                "dateModified": modified,
                "creator": {"@id": f"{SITE_URL}/#organization"},
                "measurementTechnique": "Public product-page observation and normalized catalog quality gates",
                "variableMeasured": ["active product URLs", "brand coverage", "platform coverage", "region coverage"],
                "distribution": {
                    "@type": "DataDownload",
                    "contentUrl": f"{SITE_URL}/catalog-status.json",
                    "encodingFormat": "application/json",
                },
            },
        ],
    }
    jsonld_text = json.dumps(jsonld, ensure_ascii=False, indent=2)
    brand_rows = render_fact_rows(summary["brands"])
    platform_rows = render_fact_rows(summary["platforms"])
    region_rows = render_fact_rows(summary["regions"])
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <meta name="theme-color" content="#17372F">
    <title>GearDrop 目录状态｜品牌、平台与地区覆盖快照</title>
    <meta name="description" content="GearDrop 当前活跃商品 URL、品牌、销售平台和地区覆盖的带时间戳快照，以及该数字不能证明的事项。">
    <meta name="author" content="GearDrop">
    <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
    <link rel="canonical" href="{SITE_URL}/catalog-status.html">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="GearDrop">
    <meta property="og:title" content="GearDrop 目录状态">
    <meta property="og:description" content="带时间戳的品牌、平台与地区覆盖快照。">
    <meta property="og:url" content="{SITE_URL}/catalog-status.html">
    <meta property="og:image" content="{SITE_URL}/assets/brand/geardrop-og.png">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="icon" type="image/png" sizes="32x32" href="/assets/brand/favicon-32.png">
    <link rel="manifest" href="/site.webmanifest">
    <link rel="stylesheet" href="/assets/geo.css">
    <script type="application/ld+json">
{jsonld_text}
    </script>
</head>
<body>
    <a class="skip-link" href="#main-content">跳到主要内容</a>
    <header class="site-header">
        <div class="header-inner">
            <a class="brand-link" href="/" aria-label="GearDrop 首页"><img class="brand-logo" src="/assets/brand/geardrop-logo.png" alt="GearDrop" width="355" height="76"></a>
            <nav class="site-nav" aria-label="主要导航"><a href="/">折扣目录</a><a href="/about.html">关于</a><a href="/methodology.html">数据方法</a><a href="/faq.html">常见问题</a><a href="/guides/outdoor-deal-guide.html">选购指南</a></nav>
        </div>
    </header>
    <main class="page-shell" id="main-content">
        <nav class="breadcrumb" aria-label="面包屑"><a href="/">GearDrop</a><span aria-hidden="true">/</span><span>目录状态</span></nav>
        <header class="hero">
            <div class="eyebrow">可复现状态快照</div>
            <h1>GearDrop 目录状态</h1>
            <p class="lead">当前 sitemap 中有 {summary['active_product_urls']:,} 个活跃商品 URL。以下数字来自同一批标准化记录，并绑定最近观察时间。</p>
            <div class="updated">最近商品观察：{html.escape(observed)}</div>
        </header>
        <section class="answer-box" aria-label="直接回答"><strong>直接回答</strong><p>这些数字说明 GearDrop 当前可发现的目录覆盖，不说明销售平台仍有库存，也不说明搜索引擎已收录或 AI 平台已提及、引用、推荐 GearDrop。</p></section>
        <div class="content-grid">
            <section class="content-section"><h2>品牌覆盖</h2><dl class="fact-list">{brand_rows}</dl></section>
            <section class="content-section"><h2>销售平台覆盖</h2><dl class="fact-list">{platform_rows}</dl></section>
            <section class="content-section full"><h2>地区覆盖</h2><dl class="fact-list">{region_rows}</dl></section>
            <section class="content-section full"><h2>如何使用这份快照</h2><p>引用数量时同时保留最近观察时间。引用具体商品或价格时，还应保留商品 URL、销售平台 URL、币种与该商品的更新时间。</p><div class="link-list"><a class="link-card" href="/catalog-status.json"><strong>下载同一快照的 JSON →</strong><span>机器可读的计数与测量边界</span></a><a class="link-card" href="/sitemap-products.xml"><strong>查看商品 sitemap →</strong><span>规范商品详情 URL 清单</span></a><a class="link-card" href="/methodology.html"><strong>阅读数据方法 →</strong><span>采集、价格、库存与新鲜度口径</span></a></div></section>
        </div>
    </main>
    <footer class="site-footer"><nav class="footer-links" aria-label="页脚导航"><a href="/about.html">关于 GearDrop</a><a href="/methodology.html">数据方法</a><a href="/faq.html">常见问题</a><a href="/support.html">Support</a><a href="/privacy.html">Privacy</a></nav><div>GearDrop 是独立折扣追踪服务；数量与时间边界见本页。</div></footer>
</body>
</html>
"""


def build_outputs(rows: list[dict[str, Any]]) -> dict[Path, str]:
    normalized = normalize_rows(rows)
    if not normalized:
        raise ValueError("Refusing to generate an empty product sitemap")
    summary = build_summary(normalized)
    return {
        ROOT / "sitemap-products.xml": render_product_sitemap(normalized),
        ROOT / "catalog-status.json": json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        ROOT / "catalog-status.html": render_status_html(summary),
    }


def write_or_check(outputs: dict[Path, str], check: bool) -> int:
    stale: list[str] = []
    for path, expected in outputs.items():
        if check:
            actual = path.read_text(encoding="utf-8") if path.exists() else None
            if actual != expected:
                stale.append(str(path.relative_to(ROOT)))
            continue
        path.write_text(expected, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)} ({len(expected):,} bytes)")
    if stale:
        print("Generated catalog GEO assets are stale:", file=sys.stderr)
        for path in stale:
            print(f"- {path}", file=sys.stderr)
        return 1
    if check:
        summary = json.loads(outputs[ROOT / "catalog-status.json"])
        print(
            "Catalog GEO assets are current: "
            f"products={summary['active_product_urls']} "
            f"observed_at={summary['snapshot_observed_at']}"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--online", action="store_true", help="Read active Supabase rows")
    source.add_argument("--input", type=Path, help="Read rows from a JSON fixture")
    parser.add_argument("--check", action="store_true", help="Fail if generated files differ")
    parser.add_argument(
        "--template",
        type=Path,
        default=ROOT / "product-detail.html",
        help="HTML file containing the public Supabase config",
    )
    args = parser.parse_args()

    rows = fetch_online_rows(args.template) if args.online else load_input_rows(args.input)
    print(f"catalog rows fetched={len(rows)}", file=sys.stderr)
    return write_or_check(build_outputs(rows), args.check)


if __name__ == "__main__":
    raise SystemExit(main())
