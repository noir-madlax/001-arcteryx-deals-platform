"""MEC (mec.ca) — Arc'teryx 品牌过滤页，全 SSR HTML，结构清晰。"""
from __future__ import annotations
from .base import DealerScraper, normalize_price, discount_pct
import re

HOST = "https://www.mec.ca"

class Scraper(DealerScraper):
    KEY    = "mec"
    NAME   = "MEC"
    REGION = "CA"
    TIER   = "stealthy"
    LIST_URLS = [
        "https://www.mec.ca/en/products?brand=Arc%27teryx&page={page}",
    ]
    MAX_PAGES = 10  # MEC ~52/page

    HIT_RE   = re.compile(r'<article class="Hit_hit__[^"]*">(.*?)</article>', re.S)
    LINK_RE  = re.compile(r'<a[^>]+href="(/en/product/[^"#]+)"[^>]+class="Hit_hitTitle[^"]*"[^>]*>([^<]+)</a>')
    IMG_RE   = re.compile(r'<a[^>]+class="Hit_hitImageLink[^"]*"[^>]*>.*?<img[^>]+src="([^"]+)"', re.S)
    # MEC may show multiple prices: regular + sale (need both)
    PRICES_RE  = re.compile(r'<span class="Hit_hitPrices[^"]*">(.*?)</span>\s*<div', re.S)
    PRICE_NUM  = re.compile(r"\$[\d,]+(?:\.\d{2})?")

    def parse_list(self, body: str, page_url: str) -> list[dict]:
        items = []
        for hit in self.HIT_RE.finditer(body):
            html = hit.group(1)
            ml = self.LINK_RE.search(html)
            if not ml:
                continue
            slug, name = ml.group(1), ml.group(2).strip()
            url = HOST + slug
            mi = self.IMG_RE.search(html)
            img = mi.group(1) if mi else None
            # img is /_next/image proxied; pick the cdn url out
            if img and "/_next/image" in img:
                m2 = re.search(r'url=([^&]+)', img)
                if m2:
                    from urllib.parse import unquote
                    img = unquote(m2.group(1))
            mp = self.PRICES_RE.search(html)
            prices = []
            if mp:
                prices = [normalize_price(s) for s in self.PRICE_NUM.findall(mp.group(1))]
                prices = [p for p in prices if p]
            sale = orig = None
            if len(prices) >= 2:
                # Sale shown first then original (or reverse). Lower is sale.
                sale = min(prices)
                orig = max(prices)
            elif len(prices) == 1:
                sale = orig = prices[0]
            gender = "men" if "mens" in slug or "men" in name.lower() else ("women" if "women" in slug or "women" in name.lower() else "unisex")
            items.append({
                "url": url,
                "name": name,
                "image": img,
                "original_price": orig,
                "sale_price": sale,
                "currency": "CAD",
                "in_stock": True,
                "gender": gender,
            })
        return items


if __name__ == "__main__":
    s = Scraper()
    items = s.scrape()
    print(f"\n=== MEC：{len(items)} 件 ===")
    for it in items[:8]:
        d = discount_pct(it.get("original_price"), it.get("sale_price"))
        print(f"  -{d}% C${it.get('sale_price')}/{it.get('original_price')}  {it.get('name')[:60]}")
