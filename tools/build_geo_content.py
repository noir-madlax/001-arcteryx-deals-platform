#!/usr/bin/env python3
"""Build GearDrop's public, answer-ready GEO knowledge pages.

The source of truth lives in geo/site-content.json. Generated HTML and discovery
files are committed so crawlers can read them without JavaScript or a build
runtime. Use --check in CI to fail when generated files drift from the source.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTENT_PATH = ROOT / "geo" / "site-content.json"


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def public_url(base_url: str, path: str) -> str:
    normalized = path if path.startswith("/") else f"/{path}"
    return f"{base_url.rstrip('/')}{normalized}"


def organization_node(site: dict[str, Any]) -> dict[str, Any]:
    base_url = site["base_url"].rstrip("/")
    return {
        "@type": "Organization",
        "@id": f"{base_url}/#organization",
        "name": site["name"],
        "alternateName": site["alternate_name"],
        "url": f"{base_url}/",
        "logo": {"@type": "ImageObject", "url": site["logo"]},
        "description": site["description"],
        "disambiguatingDescription": (
            "Independent outdoor deal discovery and price-tracking service at "
            "001.100app.dev; not a retailer, rental marketplace, giveaway game, "
            "or an official site of the tracked brands."
        ),
        "publishingPrinciples": f"{base_url}/methodology.html",
    }


def website_node(site: dict[str, Any]) -> dict[str, Any]:
    base_url = site["base_url"].rstrip("/")
    return {
        "@type": "WebSite",
        "@id": f"{base_url}/#website",
        "url": f"{base_url}/",
        "name": site["name"],
        "alternateName": site["alternate_name"],
        "description": site["description"],
        "inLanguage": site["primary_language"],
        "publisher": {"@id": f"{base_url}/#organization"},
    }


def page_jsonld(site: dict[str, Any], page: dict[str, Any]) -> dict[str, Any]:
    base_url = site["base_url"].rstrip("/")
    canonical = public_url(base_url, page["path"])
    breadcrumb_id = f"{canonical}#breadcrumb"
    page_id = f"{canonical}#webpage"
    page_type = page["schema_type"]
    page_node: dict[str, Any] = {
        "@type": page_type,
        "@id": page_id,
        "url": canonical,
        "name": page["title"],
        "description": page["description"],
        "inLanguage": site["primary_language"],
        "isPartOf": {"@id": f"{base_url}/#website"},
        "publisher": {"@id": f"{base_url}/#organization"},
        "breadcrumb": {"@id": breadcrumb_id},
        "dateModified": site["date_modified"],
    }

    if page_type in {"Article", "TechArticle"}:
        page_node.update(
            {
                "headline": page["h1"],
                "datePublished": site["date_modified"],
                "author": {"@id": f"{base_url}/#organization"},
                "mainEntityOfPage": {"@id": page_id},
            }
        )

    if page.get("schema_about"):
        about = page["schema_about"]
        page_node["about"] = {
            "@type": about["type"],
            "name": about["name"],
            "url": about["url"],
        }

    if page.get("faqs"):
        page_node["mainEntity"] = [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
            }
            for item in page["faqs"]
        ]

    breadcrumb = {
        "@type": "BreadcrumbList",
        "@id": breadcrumb_id,
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "GearDrop",
                "item": f"{base_url}/",
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": page["h1"],
                "item": canonical,
            },
        ],
    }

    return {
        "@context": "https://schema.org",
        "@graph": [organization_node(site), website_node(site), page_node, breadcrumb],
    }


def render_navigation(navigation: list[dict[str, str]], current_path: str) -> str:
    items = []
    current_href = f"/{current_path}"
    for item in navigation:
        current = ' aria-current="page"' if item["href"] == current_href else ""
        items.append(
            f'<a href="{esc(item["href"])}"{current}>{esc(item["label"])}</a>'
        )
    return "\n                ".join(items)


def render_links(items: list[dict[str, str]]) -> str:
    if not items:
        return ""
    cards = []
    for item in items:
        cards.append(
            "\n".join(
                [
                    f'<a class="link-card" href="{esc(item["href"])}">',
                    f"    <strong>{esc(item['label'])} →</strong>",
                    f"    <span>{esc(item['description'])}</span>",
                    "</a>",
                ]
            )
        )
    return '<div class="link-list">\n' + "\n".join(cards) + "\n</div>"


def render_section(section: dict[str, Any]) -> str:
    classes = "content-section full" if section.get("full") else "content-section"
    chunks = [f'<section class="{classes}">', f"<h2>{esc(section['heading'])}</h2>"]

    for paragraph in section.get("paragraphs", []):
        chunks.append(f"<p>{esc(paragraph)}</p>")

    if section.get("bullets"):
        chunks.append("<ul>")
        chunks.extend(f"<li>{esc(item)}</li>" for item in section["bullets"])
        chunks.append("</ul>")

    if section.get("steps"):
        chunks.append("<ol>")
        for step in section["steps"]:
            chunks.append(
                f"<li><strong>{esc(step['title'])}</strong><br>{esc(step['body'])}</li>"
            )
        chunks.append("</ol>")

    if section.get("facts"):
        chunks.append('<dl class="fact-list">')
        for fact in section["facts"]:
            chunks.append(f"<dt>{esc(fact['term'])}</dt><dd>{esc(fact['value'])}</dd>")
        chunks.append("</dl>")

    if section.get("links"):
        chunks.append(render_links(section["links"]))

    if section.get("note"):
        chunks.append(f'<div class="note">{esc(section["note"])}</div>')

    chunks.append("</section>")
    return "\n".join(chunks)


def render_faqs(faqs: list[dict[str, str]]) -> str:
    if not faqs:
        return ""
    items = []
    for index, item in enumerate(faqs):
        open_attr = " open" if index == 0 else ""
        items.append(
            "\n".join(
                [
                    f'<details class="faq-item"{open_attr}>',
                    f"<summary>{esc(item['question'])}</summary>",
                    f'<div class="faq-answer"><p>{esc(item["answer"])}</p></div>',
                    "</details>",
                ]
            )
        )
    return (
        '<section class="content-section full" aria-labelledby="faq-heading">\n'
        '<h2 id="faq-heading">问题与回答</h2>\n'
        '<div class="faq-list">\n'
        + "\n".join(items)
        + "\n</div>\n</section>"
    )


def render_page(
    site: dict[str, Any], navigation: list[dict[str, str]], page: dict[str, Any]
) -> str:
    base_url = site["base_url"].rstrip("/")
    canonical = public_url(base_url, page["path"])
    jsonld = json.dumps(page_jsonld(site, page), ensure_ascii=False, indent=2)
    nav = render_navigation(navigation, page["path"])
    sections = [render_faqs(page.get("faqs", []))]
    sections.extend(render_section(section) for section in page.get("sections", []))
    rendered_sections = "\n".join(item for item in sections if item)
    cta = page.get("cta")
    cta_html = ""
    if cta:
        cta_html = f"""
        <section class="cta-band" aria-labelledby="cta-heading">
            <div>
                <h2 id="cta-heading">{esc(cta['title'])}</h2>
                <p>{esc(cta['body'])}</p>
            </div>
            <a class="button" href="{esc(cta['href'])}">{esc(cta['label'])} →</a>
        </section>"""

    return f"""<!DOCTYPE html>
<html lang="{esc(site['primary_language'])}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <meta name="theme-color" content="#17372F">
    <title>{esc(page['title'])}</title>
    <meta name="description" content="{esc(page['description'])}">
    <meta name="author" content="GearDrop">
    <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
    <link rel="canonical" href="{esc(canonical)}">
    <link rel="alternate" hreflang="zh-CN" href="{esc(canonical)}">
    <link rel="alternate" hreflang="x-default" href="{esc(canonical)}">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="GearDrop">
    <meta property="og:title" content="{esc(page['title'])}">
    <meta property="og:description" content="{esc(page['description'])}">
    <meta property="og:url" content="{esc(canonical)}">
    <meta property="og:locale" content="zh_CN">
    <meta property="og:image" content="{esc(base_url)}/assets/brand/geardrop-og.png">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{esc(page['title'])}">
    <meta name="twitter:description" content="{esc(page['description'])}">
    <meta name="twitter:image" content="{esc(base_url)}/assets/brand/geardrop-og.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/assets/brand/favicon-32.png">
    <link rel="apple-touch-icon" sizes="180x180" href="/assets/brand/apple-touch-icon.png">
    <link rel="manifest" href="/site.webmanifest">
    <link rel="stylesheet" href="/assets/geo.css">
    <script type="application/ld+json">
{jsonld}
    </script>
</head>
<body>
    <a class="skip-link" href="#main-content">跳到主要内容</a>
    <header class="site-header">
        <div class="header-inner">
            <a class="brand-link" href="/" aria-label="GearDrop 首页">
                <img class="brand-logo" src="/assets/brand/geardrop-logo.png" alt="GearDrop" width="355" height="76">
            </a>
            <nav class="site-nav" aria-label="主要导航">
                {nav}
            </nav>
        </div>
    </header>
    <main class="page-shell" id="main-content">
        <nav class="breadcrumb" aria-label="面包屑">
            <a href="/">GearDrop</a><span aria-hidden="true">/</span><span>{esc(page['h1'])}</span>
        </nav>
        <header class="hero">
            <div class="eyebrow">{esc(page['eyebrow'])}</div>
            <h1>{esc(page['h1'])}</h1>
            <p class="lead">{esc(page['lead'])}</p>
            <div class="updated">内容更新：{esc(site['date_modified'])}</div>
        </header>
        <section class="answer-box" aria-label="直接回答">
            <strong>直接回答</strong>
            <p>{esc(page['answer'])}</p>
        </section>
        <div class="content-grid">
{rendered_sections}
        </div>
{cta_html}
    </main>
    <footer class="site-footer">
        <nav class="footer-links" aria-label="页脚导航">
            <a href="/about.html">关于 GearDrop</a>
            <a href="/methodology.html">数据方法</a>
            <a href="/faq.html">常见问题</a>
            <a href="/support.html">Support</a>
            <a href="/privacy.html">Privacy</a>
        </nav>
        <div>GearDrop 是独立折扣追踪服务，不销售商品，也不代表所列品牌或销售平台。</div>
    </footer>
</body>
</html>
"""


def render_llms_txt(site: dict[str, Any], pages: list[dict[str, Any]]) -> str:
    base_url = site["base_url"].rstrip("/")
    page_lines = "\n".join(
        f"- [{page['h1']}]({public_url(base_url, page['path'])}): {page['description']}"
        for page in pages
    )
    return f"""# GearDrop Outdoor Deals

> GearDrop at {base_url}/ is an independent outdoor deal discovery and price-tracking service for public Arc'teryx, Burton, and Patagonia listings.

Canonical entity: {base_url}/
Primary language: zh-CN
Publisher name: GearDrop
Alternate description: GearDrop Outdoor Deals

## Essential identity and limits

- GearDrop is not a retailer and does not process orders, payments, shipping, or returns.
- GearDrop is not an official site of Arc'teryx, Burton, Patagonia, or any listed retailer.
- GearDrop is not a rental marketplace, giveaway, or map game.
- Prices, stock, sizes, shipping, taxes, memberships, and return terms must be confirmed on the linked retailer page.
- A timestamp describes the latest successful observation, not a future price guarantee.
- This file helps discovery and citation hygiene; it does not prove AI mention, citation, or recommendation.

## Core pages

{page_lines}
- [Current catalog status]({base_url}/catalog-status.html): timestamped brand, source, and region coverage.
- [Machine-readable catalog status]({base_url}/catalog-status.json): the same snapshot as JSON.

## Product discovery

- [Live deal catalog]({base_url}/)
- [Product URL sitemap]({base_url}/sitemap-products.xml)
- [Full site sitemap]({base_url}/sitemap.xml)

For a specific price claim, retain the GearDrop observation time and the original retailer URL. Prefer the retailer checkout and policy pages for final transaction facts.
"""


def render_llms_full(site: dict[str, Any], pages: list[dict[str, Any]]) -> str:
    base = render_llms_txt(site, pages).rstrip()
    blocks = [base, "\n## Answer-ready site knowledge"]
    for page in pages:
        blocks.extend([f"\n### {page['h1']}", page["answer"]])
        for section in page.get("sections", []):
            blocks.append(f"\n#### {section['heading']}")
            blocks.extend(section.get("paragraphs", []))
            blocks.extend(f"- {item}" for item in section.get("bullets", []))
            blocks.extend(
                f"- {step['title']}: {step['body']}" for step in section.get("steps", [])
            )
        for faq in page.get("faqs", []):
            blocks.extend([f"\nQ: {faq['question']}", f"A: {faq['answer']}"])
    blocks.append(
        f"\nLast content review: {site['date_modified']}\nMethodology: {site['base_url'].rstrip('/')}/methodology.html\n"
    )
    return "\n".join(blocks)


def render_sitemap_static(site: dict[str, Any], pages: list[dict[str, Any]]) -> str:
    base_url = site["base_url"].rstrip("/")
    lastmod = site["date_modified"]
    entries = [(f"{base_url}/", "daily", "1.0", lastmod)]
    entries.extend(
        (public_url(base_url, page["path"]), "monthly", "0.8", lastmod)
        for page in pages
    )
    entries.extend(
        [
            (f"{base_url}/catalog-status.html", "daily", "0.8", lastmod),
            (f"{base_url}/support.html", "monthly", "0.5", ""),
            (f"{base_url}/privacy.html", "yearly", "0.3", ""),
        ]
    )
    rows = []
    for loc, changefreq, priority, modified in entries:
        lastmod_row = f"\n    <lastmod>{esc(modified)}</lastmod>" if modified else ""
        rows.append(
            "  <url>\n"
            f"    <loc>{esc(loc)}</loc>{lastmod_row}\n"
            f"    <changefreq>{changefreq}</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            "  </url>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(rows)
        + "\n</urlset>\n"
    )


def render_sitemap_index(site: dict[str, Any]) -> str:
    base_url = site["base_url"].rstrip("/")
    lastmod = site["date_modified"]
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>{esc(base_url)}/sitemap-static.xml</loc>
    <lastmod>{esc(lastmod)}</lastmod>
  </sitemap>
  <sitemap>
    <loc>{esc(base_url)}/sitemap-products.xml</loc>
    <lastmod>{esc(lastmod)}</lastmod>
  </sitemap>
</sitemapindex>
"""


def render_robots(site: dict[str, Any]) -> str:
    base_url = site["base_url"].rstrip("/")
    return f"""User-agent: *
Allow: /
Disallow: /data.js

# Search and answer systems may crawl the same public pages. Access does not
# grant permission to bypass authentication, submit forms, or ignore copyright.
Sitemap: {base_url}/sitemap.xml
"""


def build_outputs(content: dict[str, Any]) -> dict[Path, str]:
    site = content["site"]
    pages = content["pages"]
    navigation = content["navigation"]
    outputs: dict[Path, str] = {}
    for page in pages:
        outputs[ROOT / page["path"]] = render_page(site, navigation, page)
    outputs[ROOT / "llms.txt"] = render_llms_txt(site, pages)
    outputs[ROOT / "llms-full.txt"] = render_llms_full(site, pages)
    outputs[ROOT / "sitemap-static.xml"] = render_sitemap_static(site, pages)
    outputs[ROOT / "sitemap.xml"] = render_sitemap_index(site)
    outputs[ROOT / "robots.txt"] = render_robots(site)
    return outputs


def write_or_check(outputs: dict[Path, str], check: bool) -> int:
    drift: list[str] = []
    for path, expected in outputs.items():
        if check:
            actual = path.read_text(encoding="utf-8") if path.exists() else None
            if actual != expected:
                drift.append(str(path.relative_to(ROOT)))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expected, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")

    if drift:
        print("Generated GEO content is stale:", file=sys.stderr)
        for path in drift:
            print(f"- {path}", file=sys.stderr)
        return 1
    if check:
        print(f"GEO content is current ({len(outputs)} generated files).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if outputs differ")
    args = parser.parse_args()
    content = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    return write_or_check(build_outputs(content), args.check)


if __name__ == "__main__":
    raise SystemExit(main())
