"""Burton official Outlet scraper using rendered, dynamically discounted prices."""
from __future__ import annotations

import json
import math
import os
import re
import ssl
import time
import urllib.request

from .base import discount_pct, normalize_price
from .brands import vendor_matches_brand

try:
    from curl_cffi import requests as curl_requests
except Exception:  # pragma: no cover - runtime dependency fallback
    curl_requests = None


HOST = "https://www.burton.com"
COLLECTION_URL = f"{HOST}/en-us/collections/outlet"
PAGE_SIZE = 250
RENDERED_PAGE_SIZE = 24
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"


class Scraper:
    KEY = "burton"
    NAME = "Burton"
    REGION = "US"
    BRAND = "burton"
    MIN_ITEMS = 100
    MAX_PAGES = 20

    def __init__(self):
        self.crawl_complete = False
        self.http_blocked = False

    def _fetch_json(self, url: str, retries: int = 2) -> dict | None:
        last = None
        for attempt in range(retries + 1):
            try:
                if curl_requests is not None:
                    response = curl_requests.get(
                        url,
                        impersonate="chrome124",
                        timeout=45,
                        headers={
                            "accept": "application/json,text/plain,*/*",
                            "referer": COLLECTION_URL,
                        },
                    )
                    if response.status_code == 200:
                        return response.json()
                    if response.status_code in {401, 403, 429}:
                        self.http_blocked = True
                        last = RuntimeError(f"HTTP {response.status_code}: {response.text[:120]}")
                        break
                    raise RuntimeError(f"HTTP {response.status_code}: {response.text[:120]}")

                request = urllib.request.Request(
                    url,
                    headers={"User-Agent": _UA, "Accept": "application/json"},
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
        print(f"[burton] FETCH ERR {url}: {last}", flush=True)
        return None

    @staticmethod
    def _resolved_gender(name: str) -> str:
        lowered = name.lower().replace("’", "'")
        if "women's" in lowered or "womens" in lowered:
            return "women"
        if "men's" in lowered or "mens" in lowered:
            return "men"
        return "unisex"

    @staticmethod
    def _option_position(product: dict, *needles: str) -> int | None:
        for option in product.get("options") or []:
            name = str(option.get("name") or "").lower()
            if any(needle in name for needle in needles):
                try:
                    return int(option.get("position"))
                except (TypeError, ValueError):
                    return None
        return None

    @staticmethod
    def _variant_option(variant: dict, position: int | None) -> str:
        if not position:
            return ""
        return str(variant.get(f"option{position}") or "").strip()

    @staticmethod
    def _image_url(value: object) -> str | None:
        image = str(value or "").strip()
        if not image:
            return None
        if image.startswith("//"):
            return "https:" + image
        if image.startswith("/"):
            return HOST + image
        return image

    def _fetch_catalog_products(self) -> tuple[dict[str, dict], bool]:
        products_by_id = {}
        terminated = False
        max_api_pages = math.ceil(self.MAX_PAGES * RENDERED_PAGE_SIZE / PAGE_SIZE) + 1
        for page_number in range(1, max_api_pages + 1):
            url = f"{COLLECTION_URL}/products.json?limit={PAGE_SIZE}&page={page_number}"
            data = self._fetch_json(url)
            if not isinstance(data, dict) or not isinstance(data.get("products"), list):
                break
            products = data["products"]
            for product in products:
                source_id = str(product.get("id") or "").strip()
                if not source_id or source_id in products_by_id:
                    raise ValueError("Burton catalog contains a missing or duplicate product id")
                products_by_id[source_id] = product
            print(f"[burton] catalog page {page_number}: {len(products)} products", flush=True)
            if len(products) < PAGE_SIZE:
                terminated = True
                break
        return products_by_id, terminated and bool(products_by_id)

    def parse_rendered_cards(self, cards: list[dict], products_by_id: dict[str, dict]) -> list[dict]:
        items = []
        for card in cards:
            source_id = str(card.get("source_id") or "").strip()
            product = products_by_id.get(source_id)
            if product is None:
                raise ValueError(f"rendered Burton product is absent from catalog: {source_id!r}")
            if not vendor_matches_brand(product.get("vendor"), self.BRAND):
                continue

            available = [variant for variant in product.get("variants") or [] if variant.get("available")]
            if not available:
                continue
            path = str(card.get("url") or "").strip()
            if not path.startswith("/en-us/products/"):
                raise ValueError(f"unexpected Burton product URL: {path!r}")
            sale = normalize_price(card.get("sale_text"))
            original = normalize_price(card.get("original_text"))
            if not sale or not original:
                raise ValueError(f"invalid rendered Burton price pair for {source_id}")
            if original <= sale + 0.01:
                continue

            name = str(card.get("name") or product.get("title") or "").strip()
            colors = []
            for value in card.get("colors") or []:
                color = str(value or "").strip()
                if color and color not in colors:
                    colors.append(color)
            size_position = self._option_position(product, "size")
            sizes = sorted({
                value
                for variant in available
                if (value := self._variant_option(variant, size_position))
            }, key=lambda value: (len(value), value))
            items.append({
                "source_id": source_id,
                "url": HOST + path,
                "name": name,
                "image": self._image_url(card.get("image")),
                "original_price": original,
                "sale_price": sale,
                "currency": "USD",
                "in_stock": True,
                "gender": self._resolved_gender(name),
                "sizes": sizes,
                "size_stock": {size: "in_stock" for size in sizes},
                "color": ", ".join(colors[:3]),
                "colors": colors,
                "discount_pct": discount_pct(original, sale),
                "dealer": self.KEY,
                "dealer_name": self.NAME,
                "brand": self.BRAND,
                "region": self.REGION,
                "category": product.get("product_type") or "",
                "price_source_quality": "rendered",
            })
        return items

    @staticmethod
    def _close_page(page) -> None:
        try:
            page.close()
        except Exception:
            pass

    def _fetch_browser_page(self, browser, page_number: int) -> tuple[list[dict], dict]:
        attempts = max(1, int(os.environ.get("BURTON_PAGE_RETRIES", "3")))
        url = COLLECTION_URL if page_number == 1 else f"{COLLECTION_URL}?page={page_number}"
        last_error = RuntimeError("unknown Burton page failure")
        for attempt in range(1, attempts + 1):
            page = browser.new_page()
            page.set_default_navigation_timeout(90000)
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=90000)
                if not response or response.status != 200:
                    raise RuntimeError(f"HTTP {response.status if response else 'unknown'}")
                page.wait_for_function(
                    """() => {
                      const cards = [...document.querySelectorAll('li.prd-List_Item')];
                      return cards.length > 0 && cards.every((node) => {
                        const card = node.querySelector('article.prd-Card');
                        return card?.dataset.hasBeenProcessedByRegiosDopp === 'true'
                          && card.querySelector('.regios-dopp-generic-price-item--sale')
                          && card.querySelector('.regios-dopp-generic-price-item--regular');
                      });
                    }""",
                    timeout=45000,
                )
                cards = page.locator("li.prd-List_Item").evaluate_all(
                    """nodes => nodes.map((node) => {
                      const card = node.querySelector('article.prd-Card');
                      const url = card?.querySelector('[data-product-card-el="url"]');
                      const name = url?.querySelector('.util-ScreenReaderOnly')?.textContent?.trim()
                        || card?.querySelector('[data-product-card-el="quick"]')?.getAttribute('aria-label')?.replace(/^Quick view:\\s*/, '')
                        || '';
                      return {
                        source_id: card?.dataset.regiosDoppGenericProductId || '',
                        page: node.dataset.page || '',
                        url: url?.getAttribute('href') || '',
                        name,
                        image: card?.querySelector('.prd-Card_Image img')?.getAttribute('src') || '',
                        sale_text: card?.querySelector('.regios-dopp-generic-price-item--sale')?.textContent?.trim() || '',
                        original_text: card?.querySelector('.regios-dopp-generic-price-item--regular')?.textContent?.trim() || '',
                        colors: [...card.querySelectorAll('[data-product-card-el="swatch"]')]
                          .map((swatch) => swatch.getAttribute('aria-label')?.trim())
                          .filter(Boolean),
                      };
                    })"""
                )
                if any(str(card.get("page")) != str(page_number) for card in cards):
                    raise RuntimeError(f"Burton page marker mismatch on page {page_number}")
                count_text = page.locator('[data-collection-filters-el="product-count"]').inner_text()
                numbers = [int(value) for value in re.findall(r"\d+", count_text)]
                if not numbers:
                    raise RuntimeError("missing Burton collection total")
                next_locator = page.locator('[data-collection-filters-el="load-more-trigger"]')
                next_href = next_locator.get_attribute("href") if next_locator.count() else None
                return cards, {"total_count": numbers[-1], "next_href": next_href}
            except Exception as exc:
                last_error = exc
                if attempt < attempts:
                    delay = max(0, int(os.environ.get("BURTON_RETRY_DELAY_MS", "5000"))) * attempt / 1000
                    print(
                        f"[burton] page {page_number} retry {attempt}/{attempts} "
                        f"after {delay:.0f}s: {str(exc)[:180]}",
                        flush=True,
                    )
                    time.sleep(delay)
            finally:
                self._close_page(page)
        raise last_error

    def scrape(self) -> list[dict]:
        from camoufox.sync_api import Camoufox

        products_by_id, catalog_complete = self._fetch_catalog_products()
        if not catalog_complete:
            print("[burton] incomplete Shopify catalog; rendered crawl skipped", flush=True)
            return []

        items = []
        seen_items = set()
        raw_ids = []
        expected_total = None
        terminated = False
        successful_pages = 0
        inter_page_delay = max(0, int(os.environ.get("BURTON_INTER_PAGE_DELAY_MS", "1000"))) / 1000

        with Camoufox(headless=True, humanize=True, geoip=True) as browser:
            for page_number in range(1, self.MAX_PAGES + 1):
                try:
                    cards, metadata = self._fetch_browser_page(browser, page_number)
                    if expected_total is None:
                        expected_total = metadata["total_count"]
                    elif metadata["total_count"] != expected_total:
                        raise RuntimeError("Burton collection total changed during crawl")
                    if expected_total != len(products_by_id):
                        raise RuntimeError(
                            f"Burton rendered/catalog total mismatch: {expected_total} != {len(products_by_id)}"
                        )
                    next_href = metadata["next_href"]
                    if next_href and not next_href.endswith(f"?page={page_number + 1}"):
                        raise RuntimeError(f"unexpected Burton next page: {next_href!r}")
                    page_items = self.parse_rendered_cards(cards, products_by_id)
                except Exception as exc:
                    print(f"[burton] page {page_number} failed: {str(exc)[:200]}", flush=True)
                    break

                successful_pages += 1
                raw_ids.extend(str(card.get("source_id") or "") for card in cards)
                added = 0
                for item in page_items:
                    identity = item["source_id"]
                    if identity in seen_items:
                        continue
                    seen_items.add(identity)
                    items.append(item)
                    added += 1
                print(
                    f"[burton] outlet page {page_number}: "
                    f"{len(cards)} products, +{added} discounted Burton items",
                    flush=True,
                )
                if not next_href:
                    terminated = True
                    break
                if inter_page_delay:
                    time.sleep(inter_page_delay)

        expected_pages = math.ceil(expected_total / RENDERED_PAGE_SIZE) if expected_total else 0
        self.crawl_complete = (
            catalog_complete
            and terminated
            and successful_pages == expected_pages
            and len(raw_ids) == expected_total
            and len(set(raw_ids)) == expected_total
            and set(raw_ids) == set(products_by_id)
            and len(items) >= self.MIN_ITEMS
        )
        if not self.crawl_complete:
            print(
                f"[burton] incomplete snapshot: pages={successful_pages}/{expected_pages} "
                f"raw={len(raw_ids)}/{expected_total} items={len(items)}/{self.MIN_ITEMS}",
                flush=True,
            )
        return items


if __name__ == "__main__":
    scraper = Scraper()
    products = scraper.scrape()
    print(f"\n=== BURTON {len(products)} 件 ===")
    for product in products[:8]:
        print(
            f"  -{product.get('discount_pct', 0)}%  "
            f"${product.get('sale_price')}/{product.get('original_price')}  "
            f"{product.get('name', '')[:60]}"
        )
    if not products:
        raise SystemExit("[burton] no items scraped; not writing dealers/_partial/burton.json")
    os.makedirs("dealers/_partial", exist_ok=True)
    with open("dealers/_partial/burton.json", "w", encoding="utf-8") as handle:
        json.dump({
            "name": scraper.NAME,
            "region": scraper.REGION,
            "count": len(products),
            "items": products,
            "crawl_complete": scraper.crawl_complete,
            "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, handle, indent=2, ensure_ascii=False)
    print("→ dealers/_partial/burton.json")
    if not scraper.crawl_complete:
        raise SystemExit("[burton] crawl incomplete; partial retained for diagnostics but will not be published")
