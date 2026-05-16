"""EVO (evo.com) — 2026 起换成 Shopify 后端，旧的 data-productid HTML 抓法
失效，直接打 Shopify 公开 JSON API: /collections/<slug>/products.json
无需 Cloudflare/Camoufox，纯 HTTP 即可。"""
from __future__ import annotations
from .base import normalize_price, discount_pct
import json, urllib.request, ssl, os
from collections import defaultdict

HOST = "https://www.evo.com"
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"


class Scraper:
    KEY    = "evo"
    NAME   = "EVO"
    REGION = "US"

    COLLECTIONS = [
        ("men",   "mens-arcteryx-clothing"),
        ("men",   "mens-arcteryx-footwear"),
        ("men",   "mens-arcteryx-accessories"),
        ("women", "womens-arcteryx-clothing"),
        ("women", "womens-arcteryx-footwear"),
        ("women", "womens-arcteryx-accessories"),
    ]

    def _fetch_json(self, url: str, retries: int = 2) -> dict | None:
        last = None
        for i in range(retries + 1):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": _UA, "Accept": "application/json"})
                with urllib.request.urlopen(req, context=_CTX, timeout=20) as r:
                    return json.loads(r.read())
            except Exception as e:
                last = e
        print(f"[evo] FETCH ERR {url}: {last}", flush=True)
        return None

    def scrape(self) -> list[dict]:
        out = []
        seen = set()
        for gender, slug in self.COLLECTIONS:
            for page in range(1, 6):  # max 5 pages = 1250 items per collection
                url = f"{HOST}/collections/{slug}/products.json?limit=250&page={page}"
                data = self._fetch_json(url)
                if not data: break
                products = data.get("products") or []
                if not products:
                    break
                print(f"[evo] {gender}/{slug} page {page}: {len(products)} products", flush=True)
                for p in products:
                    handle = p.get("handle")
                    if not handle or handle in seen:
                        continue
                    seen.add(handle)
                    variants = p.get("variants") or []
                    # 价格取所有 variants 的最低 (有时候不同颜色价不同, 用最低更适合 deal tracker)
                    prices = [normalize_price(v.get("price")) for v in variants if v.get("price")]
                    compares = [normalize_price(v.get("compare_at_price")) for v in variants if v.get("compare_at_price")]
                    sale = min([p for p in prices if p], default=None)
                    orig = max([c for c in compares if c], default=None)
                    if not sale:
                        continue  # 全部 variants 无价 (停产/下架), 跳过
                    if not orig or orig < sale: orig = sale
                    # 库存按 size 聚合: option2 才是尺码; option1 是颜色, 别 fallback
                    # 否则 single-size 商品 (e.g. 配件/包) 会把颜色字符串当尺码塞进 sizes 数组
                    by_size = defaultdict(bool)
                    colors = set()
                    for v in variants:
                        sz = (v.get("option2") or "").strip()
                        if v.get("option1"):
                            colors.add(v["option1"])
                        if sz and v.get("available"):
                            by_size[sz] = True
                        elif sz:
                            by_size[sz] = by_size[sz] or False
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
                        "in_stock":       any(by_size.values()),
                        "gender":         gender,
                        "sizes":          sizes,
                        "size_stock":     size_stock,
                        "color":          ", ".join(sorted(colors)[:3]),
                        "colors":         sorted(colors),
                        "discount_pct":   discount_pct(orig, sale),
                        "dealer":         self.KEY,
                        "dealer_name":    self.NAME,
                        "region":         self.REGION,
                        "category":       p.get("product_type") or "",
                    })
                if len(products) < 250: break
        return out


if __name__ == "__main__":
    items = Scraper().scrape()
    print(f"\n=== EVO {len(items)} 件 ===")
    for it in items[:8]:
        d = it.get("discount_pct", 0)
        print(f"  -{d}%  ${it.get('sale_price')}/{it.get('original_price')}  {it.get('name')[:60]}")
    import json as _json, os as _os, time as _time
    _os.makedirs("dealers/_partial", exist_ok=True)
    _json.dump({"name":"EVO","region":"US","count":len(items),"items":items,"saved_at":_time.strftime("%Y-%m-%d %H:%M:%S")},
               open("dealers/_partial/evo.json","w"), indent=2, ensure_ascii=False)
    print(f"→ dealers/_partial/evo.json")
