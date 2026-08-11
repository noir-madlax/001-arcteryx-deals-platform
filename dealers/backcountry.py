"""Backcountry Burton-sale scraper backed by its public product GraphQL API."""
from __future__ import annotations

import base64
import json
import math
import os
import ssl
import time
import urllib.request

from .base import discount_pct
from .brands import vendor_matches_brand

try:
    from curl_cffi import requests as curl_requests
except Exception:  # pragma: no cover - runtime dependency fallback
    curl_requests = None


HOST = "https://www.backcountry.com"
COLLECTION_ID = "burton-on-sale"
COLLECTION_URL = f"{HOST}/rc/{COLLECTION_ID}"
GRAPHQL_URL = f"{HOST}/api/public/ux/graphql"
IMAGE_HOST = "https://content.backcountry.com"
PAGE_SIZE = 42
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"

COLLECTION_QUERY = """
query collectionPLP(
  $collectionId: String!
  $first: Int!
  $after: String
  $catalog: String!
  $filter: JSON
) {
  collection(
    catalog: $catalog
    first: $first
    collectionId: $collectionId
    filter: $filter
    after: $after
  ) {
    collection { id name url }
    totalCount
    edges {
      node {
        id
        name
        url
        stockStatus
        brand { name }
        aggregates { minSalePrice minListPrice maxListPrice }
        colors { name pliImage tileImage }
      }
    }
    pageInfo {
      hasNextPage
      hasPreviousPage
      pages { value cursor }
      firstPage { value cursor hasGap }
      lastPage { value cursor hasGap }
    }
  }
}
"""


class Scraper:
    KEY = "backcountry"
    NAME = "Backcountry"
    REGION = "US"
    BRAND = "burton"
    MIN_ITEMS = 40
    MAX_PAGES = 20

    def __init__(self):
        self.crawl_complete = False
        self.http_blocked = False

    @staticmethod
    def _resolved_gender(name: str) -> str:
        lowered = name.lower().replace("’", "'")
        if "women's" in lowered or "womens" in lowered:
            return "women"
        if "men's" in lowered or "mens" in lowered:
            return "men"
        return "unisex"

    @staticmethod
    def _image_url(path: object) -> str | None:
        value = str(path or "").strip()
        if not value:
            return None
        if value.startswith("//"):
            return "https:" + value
        if value.startswith("/"):
            return IMAGE_HOST + value
        return value

    @staticmethod
    def _cursor_for_page(page_number: int) -> str:
        # Backcountry's cursor is base64(last zero-based item index). Page one
        # therefore starts after -1, then page two starts after item 41.
        offset = (page_number - 1) * PAGE_SIZE - 1
        return base64.b64encode(str(offset).encode()).decode()

    def _fetch_json(self, payload: dict, retries: int = 2) -> dict | None:
        last = None
        for attempt in range(retries + 1):
            try:
                headers = {
                    "accept": "application/json",
                    "content-type": "application/json",
                    "origin": HOST,
                    "referer": COLLECTION_URL,
                    "user-agent": _UA,
                }
                if curl_requests is not None:
                    response = curl_requests.post(
                        GRAPHQL_URL,
                        json=payload,
                        impersonate="chrome124",
                        timeout=45,
                        headers=headers,
                    )
                    if response.status_code == 200:
                        return response.json()
                    if response.status_code in {401, 403, 429}:
                        self.http_blocked = True
                        last = RuntimeError(f"HTTP {response.status_code}: {response.text[:120]}")
                        break
                    raise RuntimeError(f"HTTP {response.status_code}: {response.text[:120]}")

                request = urllib.request.Request(
                    GRAPHQL_URL,
                    data=json.dumps(payload).encode(),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(request, context=_CTX, timeout=45) as response:
                    return json.loads(response.read())
            except Exception as exc:
                last = exc
                if getattr(exc, "code", None) in {401, 403, 429}:
                    self.http_blocked = True
                    break
                if attempt < retries:
                    time.sleep(attempt + 1)
        print(f"[backcountry] FETCH ERR {GRAPHQL_URL}: {last}", flush=True)
        return None

    def parse_graphql_response(self, payload: str | dict) -> tuple[list[dict], dict]:
        data = json.loads(payload) if isinstance(payload, str) else payload
        errors = data.get("errors")
        if errors:
            raise ValueError(f"Backcountry GraphQL errors: {str(errors)[:240]}")
        collection = data.get("data", {}).get("collection")
        if not isinstance(collection, dict):
            raise ValueError("missing Backcountry collection payload")
        identity = collection.get("collection") or {}
        if identity.get("id") != COLLECTION_ID:
            raise ValueError(f"unexpected collection id: {identity.get('id')!r}")
        edges = collection.get("edges")
        if not isinstance(edges, list):
            raise ValueError("missing Backcountry collection edges")

        total_count = int(collection.get("totalCount") or 0)
        total_pages = math.ceil(total_count / PAGE_SIZE) if total_count else 0
        if total_pages < 1 or total_pages > self.MAX_PAGES:
            raise ValueError(f"invalid Backcountry pagination: pages={total_pages} count={total_count}")
        page_info = collection.get("pageInfo") or {}
        if not isinstance(page_info.get("hasNextPage"), bool):
            raise ValueError("missing Backcountry pageInfo.hasNextPage")

        items = []
        for edge in edges:
            node = edge.get("node") if isinstance(edge, dict) else None
            if not isinstance(node, dict):
                raise ValueError("Backcountry edge is missing a product node")
            brand_name = (node.get("brand") or {}).get("name")
            if not vendor_matches_brand(brand_name, self.BRAND):
                raise ValueError(f"unexpected Backcountry brand: {brand_name!r}")

            source_id = str(node.get("id") or "").strip()
            path = str(node.get("url") or "").strip()
            if not source_id or not path.startswith("/burton-"):
                raise ValueError("Backcountry product is missing a stable Burton id or URL")
            if node.get("stockStatus") != "IN_STOCK":
                continue

            aggregates = node.get("aggregates") or {}
            try:
                sale = float(aggregates.get("minSalePrice"))
                original = float(aggregates.get("minListPrice"))
            except (TypeError, ValueError):
                continue
            # Keep the price pair conservative. Mixing min sale with max list can
            # manufacture a discount that no single listed variation offers.
            if sale <= 0 or original <= sale + 0.01:
                continue

            colors = []
            image = None
            for color in node.get("colors") or []:
                name = str(color.get("name") or "").strip()
                if name and name not in colors:
                    colors.append(name)
                if image is None:
                    image = self._image_url(color.get("pliImage") or color.get("tileImage"))
            name = str(node.get("name") or "").strip()
            items.append({
                "source_id": source_id,
                "url": HOST + path,
                "name": name,
                "image": image,
                "original_price": original,
                "sale_price": sale,
                "currency": "USD",
                "in_stock": True,
                "gender": self._resolved_gender(name),
                "sizes": [],
                "size_stock": {},
                "color": ", ".join(colors[:3]),
                "colors": colors,
                "discount_pct": discount_pct(original, sale),
                "dealer": self.KEY,
                "dealer_name": self.NAME,
                "brand": self.BRAND,
                "region": self.REGION,
                "category": "",
                "price_source_quality": "list_fallback",
            })
        return items, {
            "edge_count": len(edges),
            "has_next_page": page_info["hasNextPage"],
            "total_count": total_count,
            "total_pages": total_pages,
        }

    def _fetch_page(self, page_number: int) -> tuple[list[dict], dict]:
        payload = {
            "operationName": "collectionPLP",
            "variables": {
                "collectionId": COLLECTION_ID,
                "first": PAGE_SIZE,
                "after": self._cursor_for_page(page_number),
                "catalog": "BC",
                "filter": {},
            },
            "query": COLLECTION_QUERY,
        }
        data = self._fetch_json(payload)
        if not isinstance(data, dict):
            raise RuntimeError("missing Backcountry GraphQL response")
        return self.parse_graphql_response(data)

    def _scrape_api(self) -> tuple[list[dict], bool]:
        items = []
        seen = set()
        successful_pages = 0
        raw_edges = 0
        total_pages = 1
        expected_total = None
        inter_page_delay = max(0, int(os.environ.get("BACKCOUNTRY_INTER_PAGE_DELAY_MS", "1000"))) / 1000

        page_number = 1
        while page_number <= total_pages:
            try:
                page_items, metadata = self._fetch_page(page_number)
                if page_number == 1:
                    total_pages = metadata["total_pages"]
                    expected_total = metadata["total_count"]
                elif (
                    metadata["total_pages"] != total_pages
                    or metadata["total_count"] != expected_total
                ):
                    raise RuntimeError("Backcountry pagination metadata changed during crawl")

                expected_edges = min(PAGE_SIZE, expected_total - (page_number - 1) * PAGE_SIZE)
                if metadata["edge_count"] != expected_edges:
                    raise RuntimeError(
                        f"Backcountry page {page_number} edge mismatch: "
                        f"{metadata['edge_count']} != {expected_edges}"
                    )
                if metadata["has_next_page"] != (page_number < total_pages):
                    raise RuntimeError(f"Backcountry page {page_number} hasNextPage mismatch")
            except Exception as exc:
                print(f"[backcountry] page {page_number} failed: {str(exc)[:200]}", flush=True)
                break

            successful_pages += 1
            raw_edges += metadata["edge_count"]
            added = 0
            for item in page_items:
                identity = item["source_id"]
                if identity in seen:
                    continue
                seen.add(identity)
                items.append(item)
                added += 1
            print(
                f"[backcountry] page {page_number}/{total_pages}: "
                f"{metadata['edge_count']} products, +{added} discounted Burton items",
                flush=True,
            )
            page_number += 1
            if page_number <= total_pages and inter_page_delay:
                time.sleep(inter_page_delay)

        complete = (
            expected_total is not None
            and successful_pages == total_pages
            and raw_edges == expected_total
            and len(items) >= self.MIN_ITEMS
        )
        if not complete:
            print(
                f"[backcountry] incomplete snapshot: pages={successful_pages}/{total_pages} "
                f"raw={raw_edges}/{expected_total} items={len(items)}/{self.MIN_ITEMS}",
                flush=True,
            )
        return items, complete

    def scrape(self) -> list[dict]:
        items, complete = self._scrape_api()
        self.crawl_complete = complete and bool(items)
        return items


if __name__ == "__main__":
    scraper = Scraper()
    products = scraper.scrape()
    print(f"\n=== BACKCOUNTRY {len(products)} 件 ===")
    for product in products[:8]:
        print(
            f"  -{product.get('discount_pct', 0)}%  "
            f"${product.get('sale_price')}/{product.get('original_price')}  "
            f"{product.get('name', '')[:60]}"
        )
    if not products:
        raise SystemExit("[backcountry] no items scraped; not writing dealers/_partial/backcountry.json")
    os.makedirs("dealers/_partial", exist_ok=True)
    with open("dealers/_partial/backcountry.json", "w", encoding="utf-8") as handle:
        json.dump({
            "name": scraper.NAME,
            "region": scraper.REGION,
            "count": len(products),
            "items": products,
            "crawl_complete": scraper.crawl_complete,
            "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, handle, indent=2, ensure_ascii=False)
    print("→ dealers/_partial/backcountry.json")
    if not scraper.crawl_complete:
        raise SystemExit("[backcountry] crawl incomplete; partial retained for diagnostics but will not be published")
