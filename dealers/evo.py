"""EVO (evo.com) Shopify scraper with a Camoufox rendered-page fallback."""
from __future__ import annotations
from .base import normalize_price, discount_pct
from .brands import BRAND_LABELS, vendor_matches_brand
import json, urllib.request, ssl, os, re, time
from collections import Counter, defaultdict

try:
    from curl_cffi import requests as curl_requests
except Exception:  # pragma: no cover - runtime dependency fallback
    curl_requests = None

HOST = "https://www.evo.com"
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
_MONEY_RE = re.compile(r"\$([\d,]+(?:\.\d{1,2})?)")


class Scraper:
    KEY    = "evo"
    NAME   = "EVO"
    REGION = "US"

    COLLECTIONS = [
        ("arcteryx", "men",   "mens-arcteryx-clothing"),
        ("arcteryx", "men",   "mens-arcteryx-footwear"),
        ("arcteryx", "men",   "mens-arcteryx-accessories"),
        ("arcteryx", "women", "womens-arcteryx-clothing"),
        ("arcteryx", "women", "womens-arcteryx-footwear"),
        ("arcteryx", "women", "womens-arcteryx-accessories"),
        ("burton", "auto", "burton"),
        ("patagonia", "auto", "patagonia"),
    ]
    BROWSER_COLLECTIONS = [
        ("arcteryx", "auto", "arcteryx"),
        ("burton", "auto", "burton"),
        ("patagonia", "auto", "patagonia"),
    ]
    # A syntactically complete endpoint can still collapse one brand scope, so
    # completeness is enforced per brand before the snapshot is publishable.
    MIN_ITEMS_BY_BRAND = {"arcteryx": 100, "burton": 20, "patagonia": 20}

    def __init__(self):
        self.crawl_complete = False
        self.http_blocked = False

    @staticmethod
    def _product_image(product: dict, card: dict) -> str | None:
        def image_url(value) -> str | None:
            if isinstance(value, str):
                return value or None
            if isinstance(value, dict):
                return value.get("src") or value.get("url")
            if isinstance(value, list):
                for candidate in value:
                    if resolved := image_url(candidate):
                        return resolved
            return None

        if resolved := image_url(card.get("image")):
            return resolved
        for key in ("featured_image", "featuredImage", "image", "images"):
            if resolved := image_url(product.get(key)):
                return resolved
        for variant in product.get("variants") or []:
            for key in ("featured_image", "featuredImage", "image"):
                if resolved := image_url(variant.get(key)):
                    return resolved
        return None

    def _fetch_json(self, url: str, retries: int = 2) -> dict | None:
        last = None
        for i in range(retries + 1):
            try:
                if curl_requests is not None:
                    r = curl_requests.get(
                        url,
                        impersonate="chrome124",
                        timeout=30,
                        headers={
                            "accept": "application/json,text/plain,*/*",
                            "referer": "https://www.evo.com/shop/arcteryx",
                        },
                    )
                    if r.status_code == 200:
                        return r.json()
                    if r.status_code in {401, 403, 429}:
                        self.http_blocked = True
                        last = RuntimeError(f"HTTP {r.status_code}: {r.text[:120]}")
                        break
                    raise RuntimeError(f"HTTP {r.status_code}: {r.text[:120]}")
                req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
                with urllib.request.urlopen(req, context=_CTX, timeout=20) as r:
                    return json.loads(r.read())
            except Exception as e:
                last = e
                if getattr(e, "code", None) in {401, 403, 429}:
                    self.http_blocked = True
                    break
        print(f"[evo] FETCH ERR {url}: {last}", flush=True)
        return None

    @staticmethod
    def _money_values(label: str | None) -> list[float]:
        return [float(value.replace(",", "")) for value in _MONEY_RE.findall(label or "")]

    @staticmethod
    def _resolved_gender(gender: str, name: str) -> str:
        if gender != "auto":
            return gender
        lowered_name = name.lower()
        if "women's" in lowered_name or "womens" in lowered_name:
            return "women"
        if "men's" in lowered_name or "mens" in lowered_name:
            return "men"
        return "unisex"

    def parse_browser_snapshot(
        self,
        snapshot: dict,
        gender: str,
        brand: str = "arcteryx",
    ) -> list[dict]:
        """Normalize the rendered Shopify metadata and product-card fields."""
        expected_label = BRAND_LABELS[brand]
        cards = {}
        for card in snapshot.get("cards") or []:
            handle = (card.get("url") or "").split("/products/")[-1].split("?", 1)[0]
            if handle:
                cards[handle] = card

        inventory = snapshot.get("inventory") or {}
        products = list(snapshot.get("products") or [])
        known_handles = {product.get("handle") for product in products}
        for handle, card in cards.items():
            if handle not in known_handles:
                products.append({
                    "id": None,
                    "vendor": expected_label,
                    "type": "",
                    "handle": handle,
                    "variants": [],
                    "card_only": True,
                })
        out = []
        for product in products:
            if not vendor_matches_brand(product.get("vendor"), brand):
                continue
            handle = product.get("handle")
            variants = product.get("variants") or []
            if not handle or (not variants and not product.get("card_only")):
                continue
            card = cards.get(handle, {})
            public_title = (variants[0].get("public_title") or "") if variants else ""
            name = card.get("name") or (variants[0].get("name") if variants else "") or handle.replace("-", " ").title()
            if public_title and name.endswith(f" - {public_title}"):
                name = name[: -(len(public_title) + 3)]

            current_values = self._money_values(card.get("current_price"))
            original_values = self._money_values(card.get("original_price"))
            product_inventory = inventory.get(str(product.get("id"))) or inventory.get(product.get("id")) or {}
            fallback_price = product_inventory.get("lowestVariantPrice")
            variant_prices = [float(v["price"]) / 100 for v in variants if v.get("price") is not None]
            sale = min(current_values or ([float(fallback_price) / 100] if fallback_price else variant_prices), default=None)
            if not sale:
                continue
            orig = max(original_values or current_values or [sale])
            if orig < sale:
                orig = sale

            sizes = set()
            colors = set(card.get("colors") or [])
            for variant in variants:
                title = (variant.get("public_title") or "").strip()
                if " / " in title:
                    color, size = title.rsplit(" / ", 1)
                    if color:
                        colors.add(color)
                    if size:
                        sizes.add(size)
            sizes = sorted(sizes, key=lambda value: (len(value), value))
            in_stock = bool(card) if not product_inventory else int(product_inventory.get("inventory") or 0) > 0
            resolved_gender = self._resolved_gender(gender, name)
            out.append({
                "url": f"{HOST}/products/{handle}",
                "name": name,
                "image": self._product_image(product, card),
                "original_price": orig,
                "sale_price": sale,
                "currency": "USD",
                "in_stock": in_stock,
                "gender": resolved_gender,
                "sizes": sizes,
                "size_stock": {size: "in_stock" for size in sizes} if in_stock else {},
                "color": ", ".join(sorted(colors)[:3]),
                "colors": sorted(colors),
                "discount_pct": discount_pct(orig, sale),
                "dealer": self.KEY,
                "dealer_name": self.NAME,
                "brand": brand,
                "region": self.REGION,
                "category": product.get("type") or "",
                "price_source_quality": "list_fallback",
            })
        return out

    @staticmethod
    def _browser_snapshot(page, expected_label: str = "Arc'teryx") -> dict:
        return page.evaluate(r"""(expectedBrand) => {
          const products = window.ShopifyAnalytics?.meta?.products || [];
          const inventory = window.igProductData || {};
          const seen = new Set();
          const normalizedBrand = String(expectedBrand || '').trim().toLowerCase();
          const cards = [...document.querySelectorAll('a[href*="/products/"]')]
            .filter(a => (a.innerText || '').trim().toLowerCase().startsWith(normalizedBrand))
            .map(a => {
              const url = a.href.split('?')[0];
              if (seen.has(url)) return null;
              seen.add(url);
              let card = a.parentElement;
              for (let i = 0; i < 6 && card && !card.querySelector('img'); i++) card = card.parentElement;
              const current = card?.querySelector('[aria-label^="Current price"]');
              const original = card?.querySelector('[aria-label^="Original price"]');
              const image = card?.querySelector('img');
              const srcset = image?.getAttribute('srcset') || image?.getAttribute('data-srcset') || '';
              const srcsetUrl = srcset.split(',').map(value => value.trim().split(/\s+/)[0]).filter(Boolean).pop();
              const imageUrl = [
                image?.currentSrc,
                image?.getAttribute('src'),
                image?.getAttribute('data-src'),
                srcsetUrl,
              ].find(value => value && !value.startsWith('data:'));
              const colors = [...(card?.querySelectorAll('[aria-label^="Color option:"]') || [])]
                .map(node => (node.getAttribute('aria-label') || '').replace(/^Color option:\s*/, '').replace(/\s*\(selected\)$/, ''));
              return {
                url,
                name: (a.innerText || '').trim(),
                current_price: current?.getAttribute('aria-label') || '',
                original_price: original?.getAttribute('aria-label') || '',
                image: imageUrl ? new URL(imageUrl, window.location.href).href : null,
                colors,
              };
            }).filter(Boolean);
          return {products, inventory, cards};
        }""", expected_label)

    def _brand_counts(self, items: list[dict]) -> Counter:
        return Counter(item.get("brand") for item in items)

    def _meets_brand_minimums(self, items: list[dict]) -> bool:
        counts = self._brand_counts(items)
        missing = {
            brand: {"count": counts.get(brand, 0), "minimum": minimum}
            for brand, minimum in self.MIN_ITEMS_BY_BRAND.items()
            if counts.get(brand, 0) < minimum
        }
        if missing:
            print(f"[evo] brand floors not met: {missing}", flush=True)
            return False
        return True

    def _scrape_browser(self) -> tuple[list[dict], bool]:
        from camoufox.sync_api import Camoufox

        out = []
        seen = set()
        successful_pages = 0
        expected_pages = 0
        inter_page_delay = max(0, int(os.environ.get("EVO_BROWSER_INTER_PAGE_DELAY_MS", "5000"))) / 1000
        print("[evo] Shopify JSON blocked; using Camoufox collection fallback", flush=True)
        with Camoufox(headless=True, humanize=True, geoip=True) as browser:
            for brand, gender, slug in self.BROWSER_COLLECTIONS:
                base_url = f"{HOST}/collections/{slug}"
                page_number = 1
                max_page = 1
                page_count_discovered = False
                while page_number <= max_page:
                    try:
                        scope_items, discovered_max_page = self._fetch_browser_page(
                            browser=browser,
                            base_url=base_url,
                            slug=slug,
                            gender=gender,
                            brand=brand,
                            page_number=page_number,
                            max_page=max_page,
                        )
                        if page_number == 1:
                            max_page = discovered_max_page
                            expected_pages += max_page
                            page_count_discovered = True
                    except Exception as exc:
                        if page_number == 1 and not page_count_discovered:
                            expected_pages += 1
                        print(f"[evo] browser page failed {slug}/{page_number}: {str(exc)[:160]}", flush=True)
                        page_number += 1
                        continue
                    successful_pages += 1
                    added = 0
                    for item in scope_items:
                        if item["url"] in seen:
                            continue
                        seen.add(item["url"])
                        out.append(item)
                        added += 1
                    print(f"[evo] browser {slug} page {page_number}/{max_page}: +{added} ({len(scope_items)} parsed)", flush=True)
                    page_number += 1
                    if inter_page_delay:
                        time.sleep(inter_page_delay)
        complete = expected_pages > 0 and successful_pages == expected_pages
        return out, complete and self._meets_brand_minimums(out)

    @staticmethod
    def _close_page(page) -> None:
        try:
            page.close()
        except Exception:
            pass

    def _fetch_browser_page(
        self,
        browser,
        base_url: str,
        slug: str,
        gender: str,
        page_number: int,
        max_page: int,
        brand: str = "arcteryx",
    ) -> tuple[list[dict], int]:
        attempts = max(1, int(os.environ.get("EVO_BROWSER_PAGE_RETRIES", "3")))
        url = base_url if page_number == 1 else f"{base_url}?numResults=40&page={page_number}"
        last_error = RuntimeError("unknown browser page failure")
        for attempt in range(1, attempts + 1):
            page = browser.new_page()
            page.set_default_navigation_timeout(90000)
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=90000)
                page.wait_for_timeout(3500)
                if not response or response.status != 200:
                    raise RuntimeError(f"HTTP {response.status if response else 'unknown'}")
                snapshot = self._browser_snapshot(page, BRAND_LABELS[brand])
                scope_items = self.parse_browser_snapshot(snapshot, gender, brand)
                discovered_max_page = max_page
                if page_number == 1:
                    pagination_urls = page.locator(
                        f'a[href*="/collections/{slug}"][href*="page="]'
                    ).evaluate_all("els => [...new Set(els.map(a => a.href))]")
                    page_numbers = [
                        int(match.group(1))
                        for href in pagination_urls
                        if (match := re.search(r"[?&]page=(\d+)", href))
                    ]
                    discovered_max_page = max(page_numbers or [1])
                minimum_items = 40 if page_number < discovered_max_page else 1
                if len(scope_items) < minimum_items:
                    raise RuntimeError(
                        f"rendered page contained only {len(scope_items)} {BRAND_LABELS[brand]} products; expected at least {minimum_items}"
                    )
                return scope_items, discovered_max_page
            except Exception as exc:
                last_error = exc
                if attempt < attempts:
                    retry_delay = max(0, int(os.environ.get("EVO_BROWSER_RETRY_DELAY_MS", "10000"))) * attempt / 1000
                    print(
                        f"[evo] browser page retry {slug}/{page_number} attempt {attempt}/{attempts} "
                        f"after {retry_delay:.0f}s: {str(exc)[:160]}",
                        flush=True,
                    )
                    time.sleep(retry_delay)
            finally:
                self._close_page(page)
        raise last_error

    def _scrape_http(self) -> tuple[list[dict], bool]:
        out = []
        seen = set()
        successful_scopes = 0
        for brand, gender, slug in self.COLLECTIONS:
            scope_complete = False
            for page in range(1, 6):  # max 5 pages = 1250 items per collection
                url = f"{HOST}/collections/{slug}/products.json?limit=250&page={page}"
                data = self._fetch_json(url)
                if not data:
                    if self.http_blocked:
                        print("[evo] direct Shopify endpoint blocked; stopping HTTP retries", flush=True)
                        return [], False
                    break
                products = data.get("products") or []
                if not products:
                    scope_complete = True
                    break
                print(f"[evo] {gender}/{slug} page {page}: {len(products)} products", flush=True)
                for p in products:
                    if not vendor_matches_brand(p.get("vendor"), brand):
                        continue
                    handle = p.get("handle")
                    if not handle or handle in seen:
                        continue
                    seen.add(handle)
                    variants = p.get("variants") or []
                    # 关键: 只看 available=True 的 variants 取价。否则 EVO 会把
                    # 历史清仓色 (e.g. 7 个 $29.99 "Paradox" 已停产 variants)
                    # min 出来当成今日 -88% 假折扣
                    avail_variants = [v for v in variants if v.get("available")]
                    if not avail_variants:
                        continue  # 整品都缺货, 跳过 (不是 deal)
                    prices = [normalize_price(v.get("price")) for v in avail_variants if v.get("price")]
                    compares = [normalize_price(v.get("compare_at_price")) for v in avail_variants if v.get("compare_at_price")]
                    sale = min([x for x in prices if x], default=None)
                    orig = max([x for x in compares if x], default=None)
                    if not sale:
                        continue
                    if not orig or orig < sale: orig = sale
                    # 库存按 size 聚合: option2 才是尺码; option1 是颜色, 别 fallback
                    # sizes/colors 只统计在售 variants, 跟价格逻辑保持一致
                    by_size = defaultdict(bool)
                    colors = set()
                    for v in avail_variants:
                        sz = (v.get("option2") or "").strip()
                        if v.get("option1"):
                            colors.add(v["option1"])
                        if sz:
                            by_size[sz] = True
                    sizes = sorted([s for s in by_size if s], key=lambda x: (len(x), x))
                    size_stock = {s: ("in_stock" if by_size[s] else "out_of_stock") for s in sizes}
                    # 图片: 取第一个 variant 的 featured_image
                    img = None
                    for v in variants:
                        fi = v.get("featured_image")
                        if fi and fi.get("src"):
                            img = fi["src"]; break
                    if not img:
                        imgs = p.get("images") or []
                        if imgs: img = imgs[0].get("src")
                    out.append({
                        "url":            f"{HOST}/products/{handle}",
                        "name":           p.get("title") or "",
                        "image":          img,
                        "original_price": orig,
                        "sale_price":     sale,
                        "currency":       "USD",
                        "in_stock":       True,
                        "gender":         self._resolved_gender(gender, p.get("title") or ""),
                        "sizes":          sizes,
                        "size_stock":     size_stock,
                        "color":          ", ".join(sorted(colors)[:3]),
                        "colors":         sorted(colors),
                        "discount_pct":   discount_pct(orig, sale),
                        "dealer":         self.KEY,
                        "dealer_name":    self.NAME,
                        "brand":          brand,
                        "region":         self.REGION,
                        "category":       p.get("product_type") or "",
                        "price_source_quality": "api",
                    })
                if len(products) < 250:
                    scope_complete = True
                    break
            if scope_complete:
                successful_scopes += 1
        return out, successful_scopes == len(self.COLLECTIONS)

    def scrape(self) -> list[dict]:
        items, complete = self._scrape_http()
        if complete and self._meets_brand_minimums(items):
            self.crawl_complete = True
            return items
        if complete and items:
            print(
                f"[evo] direct snapshot returned {len(items)} items but missed a brand floor; "
                "using browser fallback",
                flush=True,
            )
        items, complete = self._scrape_browser()
        self.crawl_complete = complete and bool(items)
        return items


if __name__ == "__main__":
    scraper = Scraper()
    items = scraper.scrape()
    print(f"\n=== EVO {len(items)} 件 ===")
    for it in items[:8]:
        d = it.get("discount_pct", 0)
        print(f"  -{d}%  ${it.get('sale_price')}/{it.get('original_price')}  {it.get('name')[:60]}")
    import json as _json, os as _os, time as _time
    if not items:
        raise SystemExit("[evo] no items scraped; not writing dealers/_partial/evo.json")
    _os.makedirs("dealers/_partial", exist_ok=True)
    _json.dump({"name":"EVO","region":"US","count":len(items),"items":items,
                "crawl_complete":scraper.crawl_complete,"saved_at":_time.strftime("%Y-%m-%d %H:%M:%S")},
               open("dealers/_partial/evo.json","w"), indent=2, ensure_ascii=False)
    print(f"→ dealers/_partial/evo.json")
    if not scraper.crawl_complete:
        raise SystemExit("[evo] crawl incomplete; partial retained for diagnostics but will not be published")
