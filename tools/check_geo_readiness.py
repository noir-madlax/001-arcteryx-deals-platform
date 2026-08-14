#!/usr/bin/env python3
"""Audit GearDrop GEO discovery, entity, schema, and truth-boundary contracts."""

from __future__ import annotations

import argparse
import datetime as dt
import http.client
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ORIGIN = "https://001.100app.dev"
STATIC_PAGES = {
    "/": {"Organization", "WebSite", "CollectionPage"},
    "/about.html": {"Organization", "WebSite", "AboutPage"},
    "/methodology.html": {"Organization", "WebSite", "TechArticle"},
    "/faq.html": {"Organization", "WebSite", "FAQPage"},
    "/guides/outdoor-deal-guide.html": {"Organization", "WebSite", "Article"},
    "/brands/arcteryx.html": {"Organization", "WebSite", "CollectionPage", "Brand"},
    "/brands/burton.html": {"Organization", "WebSite", "CollectionPage", "Brand"},
    "/brands/patagonia.html": {"Organization", "WebSite", "CollectionPage", "Brand"},
    "/catalog-status.html": {"Organization", "Dataset"},
    "/product-detail.html": {"WebPage"},
}


@dataclass
class Check:
    id: str
    status: str
    message: str


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang = ""
        self.title_parts: list[str] = []
        self.in_title = False
        self.h1_parts: list[str] = []
        self.current_h1: list[str] | None = None
        self.meta: dict[str, str] = {}
        self.canonical = ""
        self.links: set[str] = set()
        self.jsonld_texts: list[str] = []
        self.current_jsonld: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "html":
            self.lang = values.get("lang", "")
        elif tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.current_h1 = []
        elif tag == "meta":
            key = values.get("name") or values.get("property")
            if key:
                self.meta[key] = values.get("content", "")
        elif tag == "link" and values.get("rel") == "canonical":
            self.canonical = values.get("href", "")
        elif tag == "a" and values.get("href"):
            self.links.add(values["href"])
        elif tag == "script" and values.get("type") == "application/ld+json":
            self.current_jsonld = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        elif tag == "h1" and self.current_h1 is not None:
            self.h1_parts.append("".join(self.current_h1).strip())
            self.current_h1 = None
        elif tag == "script" and self.current_jsonld is not None:
            self.jsonld_texts.append("".join(self.current_jsonld).strip())
            self.current_jsonld = None

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.current_h1 is not None:
            self.current_h1.append(data)
        if self.current_jsonld is not None:
            self.current_jsonld.append(data)

    @property
    def title(self) -> str:
        return "".join(self.title_parts).strip()


def collect_schema_types(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        item_type = value.get("@type")
        if isinstance(item_type, str):
            found.add(item_type)
        elif isinstance(item_type, list):
            found.update(str(item) for item in item_type)
        for child in value.values():
            found.update(collect_schema_types(child))
    elif isinstance(value, list):
        for child in value:
            found.update(collect_schema_types(child))
    return found


class Auditor:
    def __init__(
        self,
        reader: Callable[[str], str],
        min_products: int,
        deployed: bool = False,
    ) -> None:
        self.reader = reader
        self.min_products = min_products
        self.deployed = deployed
        self.checks: list[Check] = []
        self.documents: dict[str, DocumentParser] = {}

    def add(self, check_id: str, condition: bool, success: str, failure: str) -> None:
        self.checks.append(Check(check_id, "pass" if condition else "fail", success if condition else failure))

    def read(self, path: str) -> str | None:
        try:
            return self.reader(path)
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, UnicodeDecodeError) as error:
            self.checks.append(Check(f"fetch:{path}", "fail", f"Could not read {path}: {error}"))
            return None

    def inspect_html(self) -> None:
        for path, expected_types in STATIC_PAGES.items():
            source = self.read(path)
            if source is None:
                continue
            parser = DocumentParser()
            parser.feed(source)
            self.documents[path] = parser
            slug = "home" if path == "/" else path.strip("/").replace("/", ":")
            self.add(
                f"html:{slug}:lang",
                parser.lang == "zh-CN",
                f"{path} declares zh-CN",
                f"{path} html lang was {parser.lang!r}",
            )
            self.add(
                f"html:{slug}:title",
                8 <= len(parser.title) <= 80,
                f"{path} title length={len(parser.title)}",
                f"{path} title missing or implausible: {parser.title!r}",
            )
            description = parser.meta.get("description", "")
            self.add(
                f"html:{slug}:description",
                35 <= len(description) <= 180,
                f"{path} description length={len(description)}",
                f"{path} description missing or implausible (length={len(description)})",
            )
            self.add(
                f"html:{slug}:canonical",
                parser.canonical.startswith(f"{CANONICAL_ORIGIN}/"),
                f"{path} canonical={parser.canonical}",
                f"{path} canonical missing or outside canonical origin: {parser.canonical!r}",
            )
            self.add(
                f"html:{slug}:h1",
                len(parser.h1_parts) == 1 and bool(parser.h1_parts[0]),
                f"{path} has one H1",
                f"{path} H1 count={len(parser.h1_parts)} values={parser.h1_parts}",
            )

            parsed_jsonld: list[Any] = []
            invalid_jsonld: list[str] = []
            for index, raw in enumerate(parser.jsonld_texts):
                try:
                    parsed_jsonld.append(json.loads(raw))
                except json.JSONDecodeError as error:
                    invalid_jsonld.append(f"script {index}: {error}")
            self.add(
                f"html:{slug}:jsonld-parse",
                bool(parsed_jsonld) and not invalid_jsonld,
                f"{path} JSON-LD scripts={len(parsed_jsonld)}",
                f"{path} invalid/missing JSON-LD: {invalid_jsonld}",
            )
            types = set().union(*(collect_schema_types(value) for value in parsed_jsonld)) if parsed_jsonld else set()
            missing_types = expected_types - types
            self.add(
                f"html:{slug}:schema-types",
                not missing_types,
                f"{path} schema types include {sorted(expected_types)}",
                f"{path} missing schema types {sorted(missing_types)}; found={sorted(types)}",
            )

    def inspect_home_links(self) -> None:
        home = self.documents.get("/")
        if not home:
            return
        expected = {
            "/about.html",
            "/methodology.html",
            "/faq.html",
            "/guides/outdoor-deal-guide.html",
            "/brands/arcteryx.html",
            "/brands/burton.html",
            "/brands/patagonia.html",
            "/catalog-status.html",
        }
        missing = expected - home.links
        self.add(
            "home:knowledge-links",
            not missing,
            f"Homepage links all {len(expected)} knowledge surfaces",
            f"Homepage missing knowledge links: {sorted(missing)}",
        )

    def inspect_product_template(self) -> None:
        source = self.read("/product-detail.html")
        if source is None:
            return
        required = [
            'id="product-canonical"',
            'id="product-jsonld"',
            "function updateProductMetadata(p)",
            "'@type': 'Product'",
            "'@type': 'Offer'",
            "function updateNotFoundMetadata()",
            "'noindex,follow'",
            "const PRODUCT_PAGE_BASE = 'https://001.100app.dev/p';",
        ]
        missing = [token for token in required if token not in source]
        self.add(
            "product:dynamic-metadata-contract",
            not missing,
            "Product template updates canonical, metadata, Product/Offer JSON-LD, and not-found state",
            f"Product template missing tokens: {missing}",
        )
        self.add(
            "product:no-fabricated-rating",
            "aggregateRating" not in source and "reviewCount" not in source,
            "Product schema does not fabricate ratings or reviews",
            "Product template contains rating/review schema without a verified source",
        )

    def inspect_server_product_surface(self) -> None:
        if not self.deployed:
            api_source = self.read("/api/product.mjs")
            config_source = self.read("/vercel.json")
            if api_source is None or config_source is None:
                return
            try:
                rewrites = json.loads(config_source).get("rewrites", [])
            except json.JSONDecodeError as error:
                self.checks.append(
                    Check("product:server-rendered-surface", "fail", f"Invalid vercel.json: {error}")
                )
                return
            required = [
                "function renderProductPage(product)",
                "function canonicalProductUrl(sku)",
                "'@type': 'Product'",
                "'@type': 'Offer'",
                "'@type': 'WebPage'",
                "<h1>${escapeHtml(name)}</h1>",
                "export default handler",
            ]
            missing = [token for token in required if token not in api_source]
            rewrite_exists = any(
                item.get("source") == "/p" and item.get("destination") == "/api/product"
                for item in rewrites
                if isinstance(item, dict)
            )
            truth_bounded = (
                "不是库存或结算价保证" in api_source
                and "aggregateRating" not in api_source
                and "reviewCount" not in api_source
            )
            self.add(
                "product:server-rendered-surface",
                not missing and rewrite_exists and truth_bounded,
                "Server product route renders specific Product/Offer facts with canonical and truth boundaries",
                (
                    "Server product route contract incomplete: "
                    f"missing={missing}, rewrite={rewrite_exists}, truth_bounded={truth_bounded}"
                ),
            )
            return

        try:
            sitemap_source = self.reader("/sitemap-products.xml")
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, UnicodeDecodeError) as error:
            self.checks.append(
                Check(
                    "product:server-rendered-surface",
                    "fail",
                    f"Could not select a product route from the deployed sitemap: {error}",
                )
            )
            return
        try:
            root = ET.fromstring(sitemap_source)
            namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            first_location = root.findtext("sm:url/sm:loc", namespaces=namespace) or ""
        except ET.ParseError as error:
            self.checks.append(
                Check("product:server-rendered-surface", "fail", f"Invalid product sitemap: {error}")
            )
            return

        parsed_location = urllib.parse.urlparse(first_location)
        product_path = urllib.parse.urlunparse(
            ("", "", parsed_location.path, "", parsed_location.query, "")
        )
        route_is_canonical = (
            f"{parsed_location.scheme}://{parsed_location.netloc}" == CANONICAL_ORIGIN
            and parsed_location.path == "/p"
            and bool(urllib.parse.parse_qs(parsed_location.query).get("sku"))
        )
        if not route_is_canonical:
            self.add(
                "product:server-rendered-surface",
                False,
                "",
                f"Product sitemap does not point to canonical /p routes: {first_location!r}",
            )
            return

        try:
            source = self.reader(product_path)
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, UnicodeDecodeError) as error:
            self.checks.append(
                Check(
                    "product:server-rendered-surface",
                    "fail",
                    f"Could not read the deployed server product route {product_path}: {error}",
                )
            )
            return
        parser = DocumentParser()
        parser.feed(source)
        parsed_jsonld: list[Any] = []
        for raw in parser.jsonld_texts:
            try:
                parsed_jsonld.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
        types = set().union(*(collect_schema_types(value) for value in parsed_jsonld)) if parsed_jsonld else set()
        expected_types = {"Product", "Offer", "WebPage", "BreadcrumbList"}
        valid = (
            len(parser.h1_parts) == 1
            and bool(parser.h1_parts[0])
            and parser.canonical == first_location
            and expected_types <= types
            and "不是库存或结算价保证" in source
            and "aggregateRating" not in source
            and "reviewCount" not in source
        )
        self.add(
            "product:server-rendered-surface",
            valid,
            f"Server-rendered product entity is readable at {first_location}",
            (
                "Server-rendered product entity incomplete: "
                f"h1={parser.h1_parts}, canonical={parser.canonical!r}, types={sorted(types)}"
            ),
        )

    def inspect_discovery_files(self) -> None:
        robots = self.read("/robots.txt")
        llms = self.read("/llms.txt")
        llms_full = self.read("/llms-full.txt")
        sitemap_index = self.read("/sitemap.xml")
        sitemap_static = self.read("/sitemap-static.xml")
        sitemap_products = self.read("/sitemap-products.xml")
        status_raw = self.read("/catalog-status.json")
        if robots:
            self.add(
                "discovery:robots",
                f"Sitemap: {CANONICAL_ORIGIN}/sitemap.xml" in robots and "Disallow: /data.js" in robots,
                "robots.txt points to the sitemap index and keeps the oversized fallback out of crawl",
                "robots.txt sitemap or fallback boundary is missing",
            )
        if llms and llms_full:
            required = [
                "not a retailer",
                "not an official site",
                "does not prove AI mention, citation, or recommendation",
                f"{CANONICAL_ORIGIN}/methodology.html",
                f"{CANONICAL_ORIGIN}/catalog-status.json",
            ]
            missing = [token for token in required if token not in llms]
            self.add(
                "discovery:llms-truth-boundary",
                not missing and len(llms_full) > len(llms),
                "llms files expose entity, source, and AI-measurement boundaries",
                f"llms discovery contract missing: {missing}",
            )

        if sitemap_index:
            try:
                root = ET.fromstring(sitemap_index)
                namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                locations = {node.text for node in root.findall("sm:sitemap/sm:loc", namespace)}
                expected = {
                    f"{CANONICAL_ORIGIN}/sitemap-static.xml",
                    f"{CANONICAL_ORIGIN}/sitemap-products.xml",
                }
                self.add(
                    "sitemap:index",
                    expected <= locations,
                    "Sitemap index references static and product maps",
                    f"Sitemap index locations={sorted(locations)}",
                )
            except ET.ParseError as error:
                self.checks.append(Check("sitemap:index", "fail", f"Invalid sitemap index: {error}"))

        if sitemap_static:
            try:
                root = ET.fromstring(sitemap_static)
                namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                locations = {node.text for node in root.findall("sm:url/sm:loc", namespace)}
                expected = {
                    f"{CANONICAL_ORIGIN}{path}" for path in STATIC_PAGES if path != "/product-detail.html"
                }
                missing = expected - locations
                self.add(
                    "sitemap:static",
                    not missing,
                    f"Static sitemap covers {len(expected)} required pages",
                    f"Static sitemap missing {sorted(missing)}",
                )
            except ET.ParseError as error:
                self.checks.append(Check("sitemap:static", "fail", f"Invalid static sitemap: {error}"))

        product_count: int | None = None
        if sitemap_products:
            try:
                root = ET.fromstring(sitemap_products)
                namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                locations = [node.text or "" for node in root.findall("sm:url/sm:loc", namespace)]
                product_count = len(locations)
                prefix = f"{CANONICAL_ORIGIN}/p?sku="
                valid = all(item.startswith(prefix) for item in locations)
                unique = len(set(locations)) == len(locations)
                self.add(
                    "sitemap:products",
                    product_count >= self.min_products and valid and unique,
                    f"Product sitemap URLs={product_count} unique={unique}",
                    f"Product sitemap URLs={product_count}, minimum={self.min_products}, valid={valid}, unique={unique}",
                )
            except ET.ParseError as error:
                self.checks.append(Check("sitemap:products", "fail", f"Invalid product sitemap: {error}"))

        if status_raw:
            try:
                status = json.loads(status_raw)
                declared = status.get("active_product_urls")
                boundary = status.get("measurement_boundary", "")
                self.add(
                    "catalog-status:count",
                    product_count is not None and declared == product_count,
                    f"Catalog status count matches sitemap ({declared})",
                    f"Catalog status count={declared}, product sitemap count={product_count}",
                )
                self.add(
                    "catalog-status:boundary",
                    "do not prove" in boundary and "AI mention" in boundary,
                    "Catalog status keeps visibility and inventory claims bounded",
                    "Catalog status measurement boundary is incomplete",
                )
            except json.JSONDecodeError as error:
                self.checks.append(Check("catalog-status:json", "fail", f"Invalid catalog status JSON: {error}"))

    def run(self) -> list[Check]:
        self.inspect_html()
        self.inspect_home_links()
        self.inspect_product_template()
        self.inspect_server_product_surface()
        self.inspect_discovery_files()
        return self.checks


def local_reader(root: Path) -> Callable[[str], str]:
    def read(path: str) -> str:
        relative = "index.html" if path == "/" else path.lstrip("/")
        return (root / relative).read_text(encoding="utf-8")

    return read


def url_reader(base_url: str) -> Callable[[str], str]:
    origin = base_url.rstrip("/")

    def read(path: str) -> str:
        url = f"{origin}{path}"
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "GearDrop-GEO-Audit/1.0",
                "Accept-Encoding": "identity",
                "Connection": "close",
            },
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    return response.read().decode("utf-8")
            except http.client.IncompleteRead:
                if attempt == 2:
                    raise
                time.sleep(2**attempt)
        raise AssertionError("unreachable")

    return read


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--root", type=Path, default=None, help="Audit a local site root")
    source.add_argument("--base-url", help="Audit a deployed HTTP origin")
    parser.add_argument("--min-products", type=int, default=5000)
    parser.add_argument("--output", type=Path, help="Write the structured audit report")
    args = parser.parse_args()

    root = (args.root or ROOT).resolve()
    reader = url_reader(args.base_url) if args.base_url else local_reader(root)
    checks = Auditor(reader, args.min_products, deployed=bool(args.base_url)).run()
    failed = [check for check in checks if check.status == "fail"]
    report = {
        "schema_version": "1.0.0",
        "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "target": args.base_url or str(root),
        "measurement": "owned_surface_geo_readiness",
        "observed_ai_visibility": "not_measured",
        "summary": {"passed": len(checks) - len(failed), "failed": len(failed), "total": len(checks)},
        "checks": [asdict(check) for check in checks],
    }
    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
