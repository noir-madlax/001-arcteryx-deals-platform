"""MEC (mec.ca) — Arc'teryx 品牌过滤页，全 SSR HTML，结构清晰。
列表页拿到 url/name/price 后，再访问每个详情页拿 size×color×availability 矩阵。
"""
from __future__ import annotations
from .base import DealerScraper, normalize_price, discount_pct
from scrapling.fetchers import StealthyFetcher
import re, json, time

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

    # ---- Detail page enrichment ----
    # MEC PDP 内嵌 JSON-LD: hasVariant 数组 包含 size + color + availability
    def parse_detail(self, body: str) -> dict:
        """从 PDP 提取 sizes、colors、size_stock 矩阵"""
        ldjson_blocks = re.findall(r'<script[^>]+type="application/ld\+json"[^>]*>(.+?)</script>', body, re.S)
        for raw in ldjson_blocks:
            try:
                d = json.loads(raw)
            except Exception:
                continue
            if not (isinstance(d, dict) and d.get("@type") in ("Product", "ProductGroup")):
                continue
            variants = d.get("hasVariant", [])
            if not variants:
                continue   # try next ld+json block
            sizes_set = set()
            colors_set = set()
            stock = {}   # size → "in_stock" / "out_of_stock"
            for v in variants:
                sz = (v.get("size") or "").strip()
                cl = (v.get("color") or "").strip()
                if sz: sizes_set.add(sz)
                if cl: colors_set.add(cl)
                offers = v.get("offers", {})
                avail = offers.get("availability","") if isinstance(offers, dict) else ""
                in_stock = avail.endswith("InStock")
                if sz:
                    # 任一颜色有库存就算 in_stock
                    if in_stock or stock.get(sz) != "in_stock":
                        stock[sz] = "in_stock" if in_stock else "out_of_stock"
            return {
                "sizes": sorted(sizes_set, key=_size_sort_key),
                "colors": sorted(colors_set),
                "color": ", ".join(sorted(colors_set))[:120],
                "size_stock": stock,
            }
        return {}

    # 重写 scrape：列表 + 详情两阶段
    def scrape(self) -> list[dict]:
        items = []
        seen = set()
        # 阶段 1：list pages
        for tmpl in self.LIST_URLS:
            for page in range(1, self.MAX_PAGES + 1):
                url = tmpl.format(page=page)
                try:
                    p = self.fetch(url)
                    body = p.body.decode("utf-8","ignore")
                except Exception as e:
                    print(f"[mec] LIST ERR {url}: {e}")
                    break
                page_items = self.parse_list(body, url)
                if not page_items:
                    break
                new = 0
                for it in page_items:
                    if not it.get("url") or it["url"] in seen:
                        continue
                    seen.add(it["url"])
                    it["dealer"] = self.KEY
                    it["dealer_name"] = self.NAME
                    it["region"] = self.REGION
                    it["discount_pct"] = discount_pct(it.get("original_price"), it.get("sale_price"))
                    items.append(it)
                    new += 1
                print(f"[mec] list page {page} +{new} (total {len(items)})")
                if new == 0:
                    break
                time.sleep(0.5)
        # 阶段 2：每个商品的详情页
        print(f"[mec] enriching {len(items)} items via detail pages...")
        for i, it in enumerate(items, 1):
            try:
                p = self.fetch(it["url"])
                body = p.body.decode("utf-8","ignore")
                detail = self.parse_detail(body)
                it.update(detail)
                if i % 10 == 0:
                    print(f"[mec] enriched {i}/{len(items)}")
            except Exception as e:
                print(f"[mec] DETAIL ERR {it['url']}: {str(e)[:80]}")
            time.sleep(0.4)
        return items


# ---- size 排序 helper ----
_SIZE_ORDER = {"XXS":0,"XS":1,"S":2,"Small":2,"M":3,"Medium":3,"L":4,"Large":4,
               "XL":5,"X-Large":5,"XXL":6,"XX-Large":6,"XXXL":7}
def _size_sort_key(s: str):
    if s in _SIZE_ORDER: return (0, _SIZE_ORDER[s], s)
    # numeric sizes (e.g. shoe 8, 9.5)
    m = re.match(r'^(\d+(?:\.\d+)?)', s)
    if m: return (1, float(m.group(1)), s)
    return (2, 0, s)


if __name__ == "__main__":
    s = Scraper()
    items = s.scrape()
    print(f"\n=== MEC：{len(items)} 件 ===")
    for it in items[:8]:
        d = discount_pct(it.get("original_price"), it.get("sale_price"))
        print(f"  -{d}% C${it.get('sale_price')}/{it.get('original_price')}  {it.get('name')[:60]}")
    # save standalone for run_all merge
    import json as _json, os as _os, time as _time
    _os.makedirs("dealers/_partial", exist_ok=True)
    _json.dump({"name":"MEC","region":"CA","count":len(items),"items":items,"saved_at":_time.strftime("%Y-%m-%d %H:%M:%S")},
               open("dealers/_partial/mec.json","w"), indent=2, ensure_ascii=False)
    print(f"→ dealers/_partial/mec.json")
