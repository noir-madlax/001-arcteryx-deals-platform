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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dealers.source_registry import RETIRED_DEALERS  # noqa: E402

SITE_URL = "https://001.100app.dev"
APP_STORE_URL = "https://apps.apple.com/us/app/geardrop-outdoor-deals/id6790165332"
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

REGION_LABELS_EN = {
    "at": "Austria",
    "au": "Australia",
    "be": "Belgium",
    "ca": "Canada",
    "ch": "Switzerland",
    "de": "Germany",
    "dk": "Denmark",
    "es": "Spain",
    "fi": "Finland",
    "fr": "France",
    "gb": "United Kingdom",
    "ie": "Ireland",
    "it": "Italy",
    "jp": "Japan",
    "nl": "Netherlands",
    "se": "Sweden",
    "us": "United States",
}

DATA_PAGE_PATHS = (
    "catalog-status.html",
    "en/catalog-status.html",
    "insights/catalog-coverage.html",
    "en/insights/catalog-coverage.html",
    "insights/brand-source-matrix.html",
    "en/insights/brand-source-matrix.html",
    "insights/regional-coverage.html",
    "en/insights/regional-coverage.html",
)


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
        dealer = str(row.get("dealer") or "arcteryx_outlet").lower()
        if dealer in RETIRED_DEALERS:
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
    brand_counts = Counter(str(row.get("brand") or "unknown").lower() for row in rows)
    platform_counts = Counter(
        str(row.get("dealer") or "arcteryx_outlet").lower() for row in rows
    )
    region_counts = Counter(str(row.get("region") or "unknown").lower() for row in rows)
    brand_platform_counts = Counter(
        (
            str(row.get("brand") or "unknown").lower(),
            str(row.get("dealer") or "arcteryx_outlet").lower(),
        )
        for row in rows
    )
    region_brand_counts = Counter(
        (
            str(row.get("region") or "unknown").lower(),
            str(row.get("brand") or "unknown").lower(),
        )
        for row in rows
    )
    brand_ids = sorted(brand_counts, key=lambda item: (-brand_counts[item], item))
    platform_ids = sorted(platform_counts, key=lambda item: (-platform_counts[item], item))
    region_ids = sorted(region_counts, key=lambda item: (-region_counts[item], item))
    return {
        "schema_version": "1.1.0",
        "entity": "GearDrop Outdoor Deals",
        "canonical_url": f"{SITE_URL}/",
        "official_ios_app_url": APP_STORE_URL,
        "snapshot_observed_at": latest_observation,
        "active_product_urls": len(rows),
        "brands": labeled_counts(brand_counts, BRAND_LABELS),
        "platforms": labeled_counts(platform_counts, PLATFORM_LABELS),
        "regions": labeled_counts(region_counts, REGION_LABELS),
        "brand_platform_matrix": [
            {
                "brand_id": brand_id,
                "brand": BRAND_LABELS.get(brand_id, brand_id or "unknown"),
                "total": brand_counts[brand_id],
                "platform_counts": {
                    platform_id: brand_platform_counts[(brand_id, platform_id)]
                    for platform_id in platform_ids
                },
            }
            for brand_id in brand_ids
        ],
        "region_brand_matrix": [
            {
                "region_id": region_id,
                "region": REGION_LABELS_EN.get(region_id, region_id or "unknown"),
                "total": region_counts[region_id],
                "brand_counts": {
                    brand_id: region_brand_counts[(region_id, brand_id)]
                    for brand_id in brand_ids
                },
            }
            for region_id in region_ids
        ],
        "matrix_dimensions": {
            "brand_ids": brand_ids,
            "platform_ids": platform_ids,
            "region_ids": region_ids,
        },
        "analysis_urls": [f"{SITE_URL}/{path}" for path in DATA_PAGE_PATHS],
        "measurement_boundary": (
            "Counts describe active GearDrop product URLs at the recorded observation time. "
            "They do not prove retailer stock, search indexing, AI mention, citation, or recommendation."
        ),
        "methodology_url": f"{SITE_URL}/methodology.html",
        "product_sitemap_url": f"{SITE_URL}/sitemap-products.xml",
    }


def data_label(item_id: str, kind: str, language: str) -> str:
    if kind == "brand":
        return BRAND_LABELS.get(item_id, item_id or "unknown")
    if kind == "platform":
        return PLATFORM_LABELS.get(item_id, item_id or "unknown")
    labels = REGION_LABELS_EN if language == "en-US" else REGION_LABELS
    return labels.get(item_id, item_id or ("unknown" if language == "en-US" else "未标记"))


def render_fact_rows(items: list[dict[str, Any]], kind: str = "brand", language: str = "zh-CN") -> str:
    suffix = " product URLs" if language == "en-US" else " 个商品 URL"
    return "\n".join(
        "<dt>"
        f"{html.escape(data_label(str(item['id']), kind, language))}"
        "</dt><dd>"
        f"{int(item['count']):,}{suffix}</dd>"
        for item in items
    )


def render_metric_strip(summary: dict[str, Any], language: str) -> str:
    labels = (
        ("Active product URLs", "Tracked brands", "Retailer sources", "Observed markets")
        if language == "en-US"
        else ("活跃商品 URL", "追踪品牌", "销售来源", "观察地区")
    )
    values = (
        summary["active_product_urls"],
        len(summary["brands"]),
        len(summary["platforms"]),
        len(summary["regions"]),
    )
    return '<dl class="metric-strip">' + "".join(
        f"<div><dt>{html.escape(label)}</dt><dd>{value:,}</dd></div>"
        for label, value in zip(labels, values)
    ) + "</dl>"


def render_matrix_table(
    summary: dict[str, Any], matrix_key: str, column_kind: str, language: str
) -> str:
    if matrix_key == "brand_platform_matrix":
        rows = summary[matrix_key]
        columns = summary["matrix_dimensions"]["platform_ids"]
        row_label = "Brand" if language == "en-US" else "品牌"
        row_name = lambda row: row["brand"]
        values_key = "platform_counts"
    else:
        rows = summary[matrix_key]
        columns = summary["matrix_dimensions"]["brand_ids"]
        row_label = "Market" if language == "en-US" else "地区"
        row_name = lambda row: data_label(row["region_id"], "region", language)
        values_key = "brand_counts"
    total_label = "Total" if language == "en-US" else "合计"
    headers = "".join(
        f'<th scope="col">{html.escape(data_label(item, column_kind, language))}</th>'
        for item in columns
    )
    body_rows = []
    for row in rows:
        values = "".join(
            f"<td>{int(row[values_key].get(item, 0)):,}</td>" for item in columns
        )
        body_rows.append(
            f'<tr><th scope="row">{html.escape(str(row_name(row)))}</th>'
            f"{values}<td>{int(row['total']):,}</td></tr>"
        )
    return (
        '<div class="data-table-wrap"><table class="data-table">'
        f"<thead><tr><th scope=\"col\">{row_label}</th>{headers}"
        f"<th scope=\"col\">{total_label}</th></tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody></table></div>"
    )


def data_page_jsonld(
    summary: dict[str, Any], canonical: str, title: str, description: str, language: str
) -> dict[str, Any]:
    modified = valid_date(summary["snapshot_observed_at"]) or "2026-08-28"
    return {
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
                "sameAs": [APP_STORE_URL],
            },
            {
                "@type": "SoftwareApplication",
                "@id": f"{SITE_URL}/#ios-app",
                "name": "GearDrop: Outdoor Deals",
                "operatingSystem": "iOS",
                "applicationCategory": "ShoppingApplication",
                "url": APP_STORE_URL,
                "downloadUrl": APP_STORE_URL,
                "publisher": {"@id": f"{SITE_URL}/#organization"},
            },
            {
                "@type": "WebPage",
                "@id": f"{canonical}#webpage",
                "url": canonical,
                "name": title,
                "description": description,
                "inLanguage": language,
                "dateModified": modified,
                "publisher": {"@id": f"{SITE_URL}/#organization"},
                "mainEntity": {"@id": f"{canonical}#dataset"},
            },
            {
                "@type": "Dataset",
                "@id": f"{canonical}#dataset",
                "name": title,
                "description": summary["measurement_boundary"],
                "url": canonical,
                "dateModified": modified,
                "creator": {"@id": f"{SITE_URL}/#organization"},
                "measurementTechnique": "Public product-page observation followed by normalized catalog quality gates and deterministic grouping",
                "variableMeasured": [
                    "active product URLs",
                    "brand coverage",
                    "retailer-source coverage",
                    "market coverage",
                ],
                "distribution": {
                    "@type": "DataDownload",
                    "contentUrl": f"{SITE_URL}/catalog-status.json",
                    "encodingFormat": "application/json",
                },
            },
        ],
    }


def render_data_shell(
    summary: dict[str, Any], language: str, zh_path: str, en_path: str,
    title: str, description: str, eyebrow: str, h1: str, lead: str,
    answer: str, body: str,
) -> str:
    is_english = language == "en-US"
    path = en_path if is_english else zh_path
    canonical = f"{SITE_URL}/{path}"
    observed = summary["snapshot_observed_at"] or (
        "No observation time available" if is_english else "无可用时间"
    )
    jsonld_text = json.dumps(
        data_page_jsonld(summary, canonical, title, description, language),
        ensure_ascii=False,
        indent=2,
    )
    if is_english:
        skip, home_label, nav_label = "Skip to main content", "GearDrop home", "Primary navigation"
        breadcrumb_label, updated_label, answer_label = "Breadcrumb", "Latest product observation", "Short answer"
        nav = '<a href="/">Deal catalog</a><a href="/en/about.html">About</a><a href="/en/methodology.html">Methodology</a><a href="/en/faq.html">FAQ</a><a href="/en/insights/catalog-coverage.html">Data insights</a><a href="/">中文</a>'
        footer = '<a href="/en/about.html">About GearDrop</a><a href="/en/methodology.html">Methodology</a><a href="/en/faq.html">FAQ</a><a href="/support.html">Support</a><a href="/privacy.html">Privacy</a>'
        footer_text = "GearDrop is an independent deal tracker. Counts describe observed catalog records, not guaranteed retailer stock or AI visibility."
    else:
        skip, home_label, nav_label = "跳到主要内容", "GearDrop 首页", "主要导航"
        breadcrumb_label, updated_label, answer_label = "面包屑", "最近商品观察", "直接回答"
        nav = '<a href="/">折扣目录</a><a href="/about.html">关于</a><a href="/methodology.html">数据方法</a><a href="/faq.html">常见问题</a><a href="/insights/catalog-coverage.html">数据洞察</a><a href="/en/">English</a>'
        footer = '<a href="/about.html">关于 GearDrop</a><a href="/methodology.html">数据方法</a><a href="/faq.html">常见问题</a><a href="/support.html">Support</a><a href="/privacy.html">Privacy</a>'
        footer_text = "GearDrop 是独立折扣追踪服务；数量描述已观察目录记录，不保证销售平台库存或 AI 可见度。"
    return f"""<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <meta name="theme-color" content="#17372F">
    <title>{html.escape(title)}</title>
    <meta name="description" content="{html.escape(description, quote=True)}">
    <meta name="author" content="GearDrop">
    <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
    <link rel="canonical" href="{canonical}">
    <link rel="alternate" hreflang="zh-CN" href="{SITE_URL}/{zh_path}">
    <link rel="alternate" hreflang="en-US" href="{SITE_URL}/{en_path}">
    <link rel="alternate" hreflang="x-default" href="{SITE_URL}/{zh_path}">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="GearDrop">
    <meta property="og:title" content="{html.escape(title, quote=True)}">
    <meta property="og:description" content="{html.escape(description, quote=True)}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:locale" content="{language.replace('-', '_')}">
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
    <a class="skip-link" href="#main-content">{skip}</a>
    <header class="site-header"><div class="header-inner">
        <a class="brand-link" href="/" aria-label="{home_label}"><img class="brand-logo" src="/assets/brand/geardrop-logo.png" alt="GearDrop" width="355" height="76"></a>
        <nav class="site-nav" aria-label="{nav_label}">{nav}</nav>
    </div></header>
    <main class="page-shell" id="main-content">
        <nav class="breadcrumb" aria-label="{breadcrumb_label}"><a href="/">GearDrop</a><span aria-hidden="true">/</span><span>{html.escape(h1)}</span></nav>
        <header class="hero"><div class="eyebrow">{html.escape(eyebrow)}</div><h1>{html.escape(h1)}</h1><p class="lead">{html.escape(lead)}</p><div class="updated">{updated_label}: {html.escape(observed)}</div></header>
        <section class="answer-box" aria-label="{answer_label}"><strong>{answer_label}</strong><p>{html.escape(answer)}</p></section>
        {body}
    </main>
    <footer class="site-footer"><nav class="footer-links" aria-label="Footer">{footer}<a href="{APP_STORE_URL}" rel="noopener">App Store</a></nav><div>{footer_text}</div></footer>
</body>
</html>
"""


def render_status_html(summary: dict[str, Any], language: str = "zh-CN") -> str:
    is_english = language == "en-US"
    brand_rows = render_fact_rows(summary["brands"], "brand", language)
    platform_rows = render_fact_rows(summary["platforms"], "platform", language)
    region_rows = render_fact_rows(summary["regions"], "region", language)
    if is_english:
        meta = (
            "GearDrop catalog status | Timestamped coverage snapshot",
            "Timestamped GearDrop counts for active product URLs, brands, retailer sources, and observed markets, with explicit measurement limits.",
            "Reproducible status snapshot",
            "GearDrop catalog status",
            f"The product sitemap contains {summary['active_product_urls']:,} active product URLs from the same normalized snapshot.",
            "These counts describe discoverable GearDrop catalog coverage. They do not prove retailer stock, search indexing, or mention, citation, or recommendation by an AI system.",
        )
        headings = ("Brand coverage", "Retailer-source coverage", "Market coverage", "How to use this snapshot")
        use_text = "Keep the observation time with aggregate counts. For a specific price, also retain the product identity, retailer URL, currency, and product observation time."
        method_href = "/en/methodology.html"
    else:
        meta = (
            "GearDrop 目录状态｜品牌、来源与地区覆盖快照",
            "GearDrop 当前活跃商品 URL、品牌、销售来源和地区覆盖的带时间戳快照，以及这些数字不能证明的事项。",
            "可复现状态快照",
            "GearDrop 目录状态",
            f"当前商品 sitemap 有 {summary['active_product_urls']:,} 个活跃商品 URL，以下数字来自同一批标准化记录。",
            "这些数字说明 GearDrop 当前可发现的目录覆盖，不说明销售平台仍有库存，也不说明搜索引擎已收录或 AI 平台已提及、引用、推荐 GearDrop。",
        )
        headings = ("品牌覆盖", "销售来源覆盖", "地区覆盖", "如何使用这份快照")
        use_text = "引用汇总数量时请同时保留观察时间。引用具体价格时，还应保留商品身份、销售平台 URL、币种与该商品的更新时间。"
        method_href = "/methodology.html"
    body = f'''<div class="content-grid">
        <section class="content-section"><h2>{headings[0]}</h2><dl class="fact-list">{brand_rows}</dl></section>
        <section class="content-section"><h2>{headings[1]}</h2><dl class="fact-list">{platform_rows}</dl></section>
        <section class="content-section full"><h2>{headings[2]}</h2><dl class="fact-list">{region_rows}</dl></section>
        <section class="content-section full"><h2>{headings[3]}</h2><p>{use_text}</p><div class="link-list"><a class="link-card" href="/catalog-status.json"><strong>JSON →</strong><span>Machine-readable counts, matrices, and boundaries</span></a><a class="link-card" href="/sitemap-products.xml"><strong>Product sitemap →</strong><span>Canonical product-detail URL list</span></a><a class="link-card" href="{method_href}"><strong>Methodology →</strong><span>Collection, freshness, and comparison limits</span></a></div></section>
    </div>'''
    return render_data_shell(
        summary, language, "catalog-status.html", "en/catalog-status.html", *meta, body
    )


def render_catalog_coverage_html(summary: dict[str, Any], language: str) -> str:
    is_english = language == "en-US"
    metrics = render_metric_strip(summary, language)
    top_brand = summary["brands"][0]
    top_platform = summary["platforms"][0]
    top_region = summary["regions"][0]
    if is_english:
        meta = (
            "GearDrop current catalog coverage | First-party data snapshot",
            "First-party analysis of GearDrop active product URL coverage across tracked brands, retailer sources, and observed markets at a stated time.",
            "First-party catalog analysis",
            "What does the current GearDrop catalog cover?",
            "This page summarizes the breadth of GearDrop's active product URL set using the same records that produce the public product sitemap.",
            f"At the recorded observation time, GearDrop exposed {summary['active_product_urls']:,} active product URLs across {len(summary['brands'])} tracked brands, {len(summary['platforms'])} retailer sources, and {len(summary['regions'])} observed markets.",
        )
        interpretation = f"The largest recorded brand group is {data_label(top_brand['id'], 'brand', language)} with {top_brand['count']:,} URLs. The largest retailer-source group is {data_label(top_platform['id'], 'platform', language)} with {top_platform['count']:,}; the largest market group is {data_label(top_region['id'], 'region', language)} with {top_region['count']:,}. These are URL counts, not unique physical products or guaranteed inventory."
        headings = ("Snapshot dimensions", "Interpretation", "Evidence and limits")
        links = '<a class="link-card" href="/catalog-status.json"><strong>Download the snapshot JSON →</strong><span>Counts, matrix dimensions, and measurement boundary</span></a><a class="link-card" href="/en/methodology.html"><strong>Read the methodology →</strong><span>Collection, freshness, and identity rules</span></a>'
    else:
        meta = (
            "GearDrop 当前目录覆盖｜原创数据快照",
            "基于 GearDrop 当前活跃商品记录的第一方分析，展示追踪品牌、销售来源和观察地区的覆盖规模与明确时间边界。",
            "第一方目录分析",
            "当前 GearDrop 目录覆盖了什么？",
            "本页使用生成公开商品 sitemap 的同一批标准化记录，解释 GearDrop 当前活跃商品 URL 集合的覆盖广度。",
            f"在记录的观察时间，GearDrop 有 {summary['active_product_urls']:,} 个活跃商品 URL，覆盖 {len(summary['brands'])} 个追踪品牌、{len(summary['platforms'])} 个销售来源和 {len(summary['regions'])} 个观察地区。",
        )
        interpretation = f"当前记录最多的品牌组是 {data_label(top_brand['id'], 'brand', language)}（{top_brand['count']:,} 个 URL）；最大销售来源组是 {data_label(top_platform['id'], 'platform', language)}（{top_platform['count']:,} 个）；最大地区组是 {data_label(top_region['id'], 'region', language)}（{top_region['count']:,} 个）。这些是 URL 数量，不等于唯一实物商品数，也不保证库存。"
        headings = ("快照维度", "怎样解读", "证据与限制")
        links = '<a class="link-card" href="/catalog-status.json"><strong>下载快照 JSON →</strong><span>计数、矩阵维度与测量边界</span></a><a class="link-card" href="/methodology.html"><strong>阅读数据方法 →</strong><span>采集、新鲜度与商品身份规则</span></a>'
    body = f'''<div class="content-grid"><section class="content-section full"><h2>{headings[0]}</h2>{metrics}</section><section class="content-section full"><h2>{headings[1]}</h2><p>{html.escape(interpretation)}</p></section><section class="content-section full"><h2>{headings[2]}</h2><p>{html.escape(summary["measurement_boundary"])}</p><div class="link-list">{links}</div></section></div>'''
    return render_data_shell(summary, language, "insights/catalog-coverage.html", "en/insights/catalog-coverage.html", *meta, body)


def render_brand_source_matrix_html(summary: dict[str, Any], language: str) -> str:
    table = render_matrix_table(summary, "brand_platform_matrix", "platform", language)
    if language == "en-US":
        meta = (
            "GearDrop brand by retailer-source matrix | First-party data",
            "A timestamped first-party matrix showing how active GearDrop product URLs are distributed across tracked brands and retailer sources.",
            "First-party source analysis",
            "Which retailer sources contribute to each tracked brand?",
            "The matrix counts active GearDrop product URLs by normalized brand and retailer source from one reproducible catalog snapshot.",
            "A non-zero cell means GearDrop observed active URLs for that brand-source pair. It does not mean the retailer is authorized for every market, has current stock, or endorses GearDrop.",
        )
        headings = ("Brand × retailer-source matrix", "How to cite the matrix")
        explanation = "Retain the snapshot time and use the JSON matrix IDs when reproducing a count. Source volume can reflect market coverage, product duplication, or collector scope; it is not a retailer-quality ranking."
        methodology = "/en/methodology.html"
        scroll_hint = "On smaller screens, swipe horizontally to see every source."
    else:
        meta = (
            "GearDrop 品牌×销售来源矩阵｜原创数据",
            "带时间戳的第一方矩阵，展示 GearDrop 当前活跃商品 URL 在追踪品牌与销售来源之间的分布。",
            "第一方来源分析",
            "每个追踪品牌来自哪些销售来源？",
            "本矩阵从同一份可复现目录快照，按标准化品牌和销售来源统计当前活跃商品 URL。",
            "单元格非零只说明 GearDrop 观察到该品牌×来源组合的活跃 URL；不说明该来源在所有地区均获授权、仍有库存或背书 GearDrop。",
        )
        headings = ("品牌 × 销售来源矩阵", "如何引用矩阵")
        explanation = "复现计数时请保留快照时间并使用 JSON 中的矩阵 ID。来源数量会受市场覆盖、商品重复和采集范围影响，不是销售平台质量排名。"
        methodology = "/methodology.html"
        scroll_hint = "小屏幕可左右滑动，查看全部销售来源。"
    body = f'''<div class="content-grid"><section class="content-section full"><h2>{headings[0]}</h2><p class="table-scroll-hint">{scroll_hint}</p>{table}</section><section class="content-section full"><h2>{headings[1]}</h2><p>{html.escape(explanation)}</p><div class="link-list"><a class="link-card" href="/catalog-status.json"><strong>JSON matrix →</strong><span>brand_platform_matrix</span></a><a class="link-card" href="{methodology}"><strong>Methodology →</strong><span>Source normalization and quality gates</span></a></div></section></div>'''
    return render_data_shell(summary, language, "insights/brand-source-matrix.html", "en/insights/brand-source-matrix.html", *meta, body)


def render_regional_coverage_html(summary: dict[str, Any], language: str) -> str:
    table = render_matrix_table(summary, "region_brand_matrix", "brand", language)
    if language == "en-US":
        meta = (
            "GearDrop market by brand coverage | First-party data",
            "A timestamped first-party matrix of active GearDrop product URLs grouped by observed sales market and tracked outdoor brand.",
            "First-party market analysis",
            "Where does GearDrop observe active brand listings?",
            "The matrix groups current catalog URLs by normalized sales market and brand without converting prices across currencies.",
            "A regional count describes where a source listing was observed. It does not prove shipping eligibility, identical SKUs, tax treatment, stock, or a directly comparable checkout price.",
        )
        headings = ("Market × brand matrix", "Why this is not a price comparison")
        explanation = "Cross-market prices cannot be compared responsibly from these counts alone. Currency, taxes, shipping, duties, memberships, return costs, and product variants must be normalized first."
        guide = "/en/guides/outdoor-deal-guide.html"
        scroll_hint = "On smaller screens, swipe horizontally to see every brand."
    else:
        meta = (
            "GearDrop 地区×品牌覆盖｜原创数据",
            "带时间戳的第一方矩阵，按观察销售地区和追踪户外品牌汇总 GearDrop 当前活跃商品 URL。",
            "第一方地区分析",
            "GearDrop 在哪些地区观察到品牌商品？",
            "本矩阵按标准化销售地区和品牌汇总当前目录 URL，不对不同币种价格做直接换算比较。",
            "地区计数说明来源商品在哪个销售市场被观察到；不证明可配送、SKU 完全相同、税制一致、仍有库存或结算价可直接比较。",
        )
        headings = ("地区 × 品牌矩阵", "为什么这不是价格比较")
        explanation = "仅凭这些计数不能负责任地比较跨地区价格。还需要统一币种、税费、运费、关税、会员条件、退货成本和商品版本。"
        guide = "/guides/outdoor-deal-guide.html"
        scroll_hint = "小屏幕可左右滑动，查看全部品牌。"
    body = f'''<div class="content-grid"><section class="content-section full"><h2>{headings[0]}</h2><p class="table-scroll-hint">{scroll_hint}</p>{table}</section><section class="content-section full"><h2>{headings[1]}</h2><p>{html.escape(explanation)}</p><div class="link-list"><a class="link-card" href="/catalog-status.json"><strong>JSON matrix →</strong><span>region_brand_matrix</span></a><a class="link-card" href="{guide}"><strong>Buying guide →</strong><span>Identity, market, and landed-cost checks</span></a></div></section></div>'''
    return render_data_shell(summary, language, "insights/regional-coverage.html", "en/insights/regional-coverage.html", *meta, body)


def render_insight_sitemap(summary: dict[str, Any]) -> str:
    lastmod = valid_date(summary["snapshot_observed_at"]) or "2026-08-28"
    entries = "\n".join(
        "  <url>\n"
        f"    <loc>{SITE_URL}/{html.escape(path)}</loc>\n"
        f"    <lastmod>{lastmod}</lastmod>\n"
        "    <changefreq>daily</changefreq>\n"
        "    <priority>0.8</priority>\n"
        "  </url>"
        for path in DATA_PAGE_PATHS
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n</urlset>\n"
    )


def build_outputs(rows: list[dict[str, Any]]) -> dict[Path, str]:
    normalized = normalize_rows(rows)
    if not normalized:
        raise ValueError("Refusing to generate an empty product sitemap")
    summary = build_summary(normalized)
    return {
        ROOT / "sitemap-products.xml": render_product_sitemap(normalized),
        ROOT / "sitemap-insights.xml": render_insight_sitemap(summary),
        ROOT / "catalog-status.json": json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        ROOT / "catalog-status.html": render_status_html(summary),
        ROOT / "en" / "catalog-status.html": render_status_html(summary, "en-US"),
        ROOT / "insights" / "catalog-coverage.html": render_catalog_coverage_html(summary, "zh-CN"),
        ROOT / "en" / "insights" / "catalog-coverage.html": render_catalog_coverage_html(summary, "en-US"),
        ROOT / "insights" / "brand-source-matrix.html": render_brand_source_matrix_html(summary, "zh-CN"),
        ROOT / "en" / "insights" / "brand-source-matrix.html": render_brand_source_matrix_html(summary, "en-US"),
        ROOT / "insights" / "regional-coverage.html": render_regional_coverage_html(summary, "zh-CN"),
        ROOT / "en" / "insights" / "regional-coverage.html": render_regional_coverage_html(summary, "en-US"),
    }


def write_or_check(outputs: dict[Path, str], check: bool) -> int:
    stale: list[str] = []
    for path, expected in outputs.items():
        if check:
            actual = path.read_text(encoding="utf-8") if path.exists() else None
            if actual != expected:
                stale.append(str(path.relative_to(ROOT)))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
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
