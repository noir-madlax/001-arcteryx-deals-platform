"""EVO (evo.com) — Cloudflare Turnstile, 必须用 StealthySession 暖首页才能进。"""
from __future__ import annotations
from .base import DealerScraper, normalize_price, discount_pct
from scrapling.fetchers import StealthySession
import re

HOST = "https://www.evo.com"

class Scraper(DealerScraper):
    KEY    = "evo"
    NAME   = "EVO"
    REGION = "US"
    TIER   = "session"   # 自定义 tier；不走 base.fetch
    LIST_URLS = [
        "https://www.evo.com/shop/clothing/arcteryx/mens?page={page}",
        "https://www.evo.com/shop/clothing/arcteryx/womens?page={page}",
    ]
    MAX_PAGES = 5

    # 商品卡结构（来自 mens/womens 页）：
    # <... data-productid="282426" ...>
    #   <a href="/bike-jackets/arcteryx-rhoam-hybrid-jacket" class="product-thumb-link" ...>
    #     <img src="..." alt="Arc'teryx Rhoam Hybrid Jacket">
    #     <span class="product-thumb-title">Arc'teryx Rhoam Hybrid Jacket</span>
    #     <span class="product-thumb-price">$450.00</span>
    #   </a>
    CARD_RE = re.compile(r'<div[^>]+data-productid="(\d+)"[^>]*>(.*?)</div>\s*(?=<div[^>]+data-productid|</main>|<footer)', re.S)
    # backup: simpler split
    LINK_RE  = re.compile(r'href="([^"]+)"[^>]+class="product-thumb-link', re.S)
    IMG_RE   = re.compile(r'<img\s+src="([^"]+)"\s+class="product-thumb-image', re.S)
    NAME_RE  = re.compile(r'<span class="product-thumb-title[^"]*">\s*([^<]+?)\s*</span>')
    # price block can have one price OR was/now markup
    PRICE_BLOCK = re.compile(r'<span class="product-thumb-price[^"]*">(.*?)</span>\s*(?:</a>|<div)', re.S)
    PRICE_NUM   = re.compile(r"\$[\d,]+(?:\.\d{2})?")
    WAS_RE      = re.compile(r'<span[^>]*class="[^"]*was[^"]*"[^>]*>\s*\$?([\d.,]+)\s*</span>')
    NOW_RE      = re.compile(r'<span[^>]*class="[^"]*now[^"]*"[^>]*>\s*\$?([\d.,]+)\s*</span>')

    # NOT using base.fetch — need session.
    def scrape(self) -> list[dict]:
        items = []
        seen = set()
        with StealthySession(headless=True, network_idle=True, solve_cloudflare=True) as s:
            print(f"[evo] warm: home")
            s.fetch(f"{HOST}/", timeout=45000)
            for tmpl in self.LIST_URLS:
                gender = "men" if "/mens" in tmpl else "women" if "/womens" in tmpl else "unisex"
                for page in range(1, self.MAX_PAGES + 1):
                    url = tmpl.format(page=page)
                    print(f"[evo] {url}")
                    try:
                        p = s.fetch(url, timeout=45000)
                        body = p.body.decode("utf-8","ignore")
                    except Exception as e:
                        print(f"[evo] FETCH ERR {e}")
                        break
                    new = 0
                    # split body by data-productid markers
                    pieces = re.split(r'(?=<div[^>]+data-productid="\d+")', body)
                    for piece in pieces:
                        m_pid = re.search(r'data-productid="(\d+)"', piece)
                        if not m_pid:
                            continue
                        pid = m_pid.group(1)
                        ml = self.LINK_RE.search(piece)
                        if not ml:
                            continue
                        url_p = HOST + ml.group(1)
                        if url_p in seen:
                            continue
                        seen.add(url_p)
                        mname = self.NAME_RE.search(piece)
                        name = mname.group(1).strip() if mname else ""
                        if "arc" not in name.lower():
                            continue
                        mimg = self.IMG_RE.search(piece)
                        img = mimg.group(1) if mimg else None
                        # price
                        sale = orig = None
                        was = self.WAS_RE.search(piece)
                        now = self.NOW_RE.search(piece)
                        if was and now:
                            orig = normalize_price(was.group(1))
                            sale = normalize_price(now.group(1))
                        else:
                            mp = self.PRICE_BLOCK.search(piece)
                            if mp:
                                prices = [normalize_price(x) for x in self.PRICE_NUM.findall(mp.group(1))]
                                prices = [x for x in prices if x]
                                if len(prices) >= 2:
                                    orig = max(prices); sale = min(prices)
                                elif prices:
                                    sale = orig = prices[0]
                        items.append({
                            "url": url_p,
                            "name": name,
                            "image": img,
                            "original_price": orig,
                            "sale_price": sale,
                            "currency": "USD",
                            "in_stock": True,
                            "gender": gender,
                            "discount_pct": discount_pct(orig, sale),
                            "dealer": self.KEY,
                            "dealer_name": self.NAME,
                            "region": self.REGION,
                        })
                        new += 1
                    print(f"[evo] page {page} +{new} (total {len(items)})")
                    if new == 0:
                        break
        return items


if __name__ == "__main__":
    items = Scraper().scrape()
    print(f"\n=== EVO {len(items)} 件 ===")
    for it in items[:8]:
        d = it.get("discount_pct", 0)
        print(f"  -{d}%  ${it.get('sale_price')}/{it.get('original_price')}  {it.get('name')[:60]}")
