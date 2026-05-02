"""SSENSE — Arc'teryx 男女款，纯 HTTP 即可。"""
from __future__ import annotations
import re, json
from .base import DealerScraper, normalize_price, discount_pct

HOST = "https://www.ssense.com"

class Scraper(DealerScraper):
    KEY    = "ssense"
    NAME   = "SSENSE"
    REGION = "US"          # 默认 US 站，价格 USD
    TIER   = "fetcher"
    LIST_URLS = [
        "https://www.ssense.com/en-us/men/designers/arcteryx",
        "https://www.ssense.com/en-us/women/designers/arcteryx",
    ]

    # SSENSE 把每个产品包成 <a class="flex flex-col" href="/en-us/men/product/arcteryx/..."> ...
    # 内含 <h3> 品牌+名字, 价格在 data-test="regularPriceText"/"salePriceText".
    # 同时每条都有一个 JSON-LD <script type="application/ld+json">，里面是 schema.org/Product 完整数据。
    def parse_list(self, body: str, page_url: str) -> list[dict]:
        items = []
        gender = "men" if "/men/" in page_url else "women"
        # 抓取所有 JSON-LD Product 块（每个商品一块）
        for m in re.finditer(r'<script type="application/ld\+json">(\{[^<]*?\})</script>', body):
            try:
                d = json.loads(m.group(1))
            except Exception:
                continue
            if d.get("@type") != "Product":
                continue
            # 只要 Arc'teryx
            brand = (d.get("brand") or {}).get("name", "") if isinstance(d.get("brand"), dict) else d.get("brand", "")
            if "arc" not in brand.lower().replace("'", "").replace("`", ""):
                continue
            offer = d.get("offers") or {}
            sale = float(offer.get("price")) if offer.get("price") else None
            # SSENSE JSON-LD 不含 listPrice — 从 HTML 单独抓 line-through 价格
            currency = offer.get("priceCurrency", "USD")
            url = d.get("url") or d.get("@id") or ""
            if url and not url.startswith("http"):
                url = HOST + url
            items.append({
                "url": url,
                "name": d.get("name", ""),
                "image": (d.get("image") or [None])[0] if isinstance(d.get("image"), list) else d.get("image"),
                "original_price": None,    # SSENSE JSON-LD 不暴露原价；后续从 HTML 兜底
                "sale_price": sale,
                "currency": currency,
                "in_stock": (offer.get("availability", "").endswith("InStock")),
                "gender": gender,
            })
        # HTML 兜底：扫 line-through 原价 → 配对到同一商品
        # SSENSE 商品锚 + 价格区块
        anchor_pat = re.compile(
            r'<a[^>]+href="(/en-us/(?:men|women)/product/arc[^"]+)"[^>]*>(.*?)</a>',
            re.S
        )
        url_to_html = {}
        for m in anchor_pat.finditer(body):
            url_to_html[HOST + m.group(1).rstrip("/")] = m.group(2)
        for it in items:
            html = url_to_html.get(it["url"].rstrip("/"))
            if not html:
                continue
            # line-through 原价
            mo = re.search(r'line-through[^>]*>\s*([^<]+?)\s*</span>', html)
            if mo:
                it["original_price"] = normalize_price(mo.group(1))
            it["discount_pct"] = discount_pct(it.get("original_price"), it.get("sale_price"))
        # 全部 Arc'teryx 商品（含原价款）；非打折款 original_price=sale_price, discount_pct=0
        for it in items:
            if not it.get("original_price"):
                it["original_price"] = it.get("sale_price")
                it["discount_pct"] = 0
        return [it for it in items if it.get("sale_price")]


if __name__ == "__main__":
    s = Scraper()
    items = s.scrape()
    print(f"\n=== SSENSE 抓取完毕：{len(items)} 件 ===")
    for it in items[:8]:
        print(f"  {it.get('discount_pct')}% off  ${it.get('sale_price')} ({it.get('original_price')}) {it.get('name')[:50]}")
        print(f"    {it.get('url')}")
