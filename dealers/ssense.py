"""SSENSE — Arc'teryx 男女款；
试过双引擎 (StealthySession 列表 + Camoufox PDP)，Camoufox 也过不了
SSENSE 每页 Cloudflare Turnstile，详情页全返 CF stub。

最终采用：StealthySession + solve_cloudflare 跑列表页（提取 color +
基本信息）；详情页放弃，sizes 留空。"""
from __future__ import annotations
import re, json, time
from .base import DealerScraper, normalize_price, discount_pct
from scrapling.fetchers import StealthySession

HOST = "https://www.ssense.com"

class Scraper(DealerScraper):
    KEY    = "ssense"
    NAME   = "SSENSE"
    REGION = "US"
    TIER   = "stealthy_cf"
    LIST_URLS = [
        "https://www.ssense.com/en-us/men/designers/arcteryx",
        "https://www.ssense.com/en-us/women/designers/arcteryx",
    ]

    # SSENSE PDP: <select id="pdpSizeDropdown"><option value="XS_..." [disabled]>XS - Only N remaining</option> ...
    SIZE_OPT_RE = re.compile(
        r'<option\s+[^>]*value="([A-Za-z0-9-]+)_[^"]*"\s*([^>]*)>(.*?)</option>',
        re.S
    )

    # SSENSE 在商品名里塞颜色作首词（"Black Alpha SV Jacket"）
    _COLOR_PREFIX = re.compile(
        r"^(black|white|beige|brown|green|blue|red|yellow|orange|purple|pink|gr[ae]y|"
        r"off-white|olive|khaki|navy|gold|silver|tan|cream|charcoal|burgundy|teal|sage|"
        r"sand|coral|mint|rust|stone|cobalt|ivory|forest|graphite|peach|lavender|"
        r"taupe|mauve|crimson|emerald|amber|bronze|maroon|fuchsia)\b",
        re.I
    )

    def parse_detail(self, body: str, name_hint: str = "") -> dict:
        """SSENSE PDP 把 sizes 嵌在 inline GraphQL 状态里的 "variants":[...]
        每个 variant 含 {"size":{"name":"S",...}, "inStock":true, "lowStock":n} —
        从这里提取 sizes/库存。color 从 JSON-LD name 首词。"""
        sizes, size_stock = [], {}
        # 1) 找 "variants":[ 数组（手动平衡 [ ] 解 JSON）
        idx = body.find('"variants":[')
        if idx >= 0:
            start = idx + len('"variants":')
            depth = 0
            end = -1
            for i in range(start, min(len(body), start + 50000)):
                c = body[i]
                if c == '[': depth += 1
                elif c == ']':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            if end > 0:
                try:
                    variants = json.loads(body[start:end])
                    for v in variants:
                        sz = (v.get("size") or {}).get("name")
                        if not sz: continue
                        sizes.append(sz)
                        size_stock[sz] = "in_stock" if v.get("inStock") else "out_of_stock"
                except Exception:
                    pass
        # 2) 兜底：旧版 SSENSE 的 <select id=pdpSizeDropdown>（少见）
        if not sizes:
            i = body.find('id="pdpSizeDropdown"')
            if i >= 0:
                end = body.find('</select>', i)
                if end >= 0:
                    block = body[i:end]
                    for m in self.SIZE_OPT_RE.finditer(block):
                        attrs = m.group(2) or ""
                        label = re.sub(r'\s+', ' ', m.group(3)).strip()
                        if not label or 'SELECT A SIZE' in label.upper():
                            continue
                        sz = label.split(' - ')[0].strip()
                        if not sz: continue
                        disabled = 'disabled' in attrs.lower()
                        sizes.append(sz)
                        size_stock[sz] = 'out_of_stock' if disabled else 'in_stock'
        # 3) color from JSON-LD product name 首词（lazy match 避免吃到 brand.name）
        name = name_hint
        m_name = re.search(r'"@type":"Product",[^}]*?"name":"([^"]+)"', body)
        if m_name: name = m_name.group(1)
        color = ""
        m = self._COLOR_PREFIX.match(name or "")
        if m: color = m.group(1).title()
        return {"sizes": sizes, "size_stock": size_stock, "color": color, "colors": [color] if color else []}

    def scrape(self) -> list[dict]:
        items = []
        seen = set()
        with StealthySession(headless=True, network_idle=True, solve_cloudflare=True) as s:
            print("[ssense] warm: home", flush=True)
            s.fetch(f"{HOST}/", timeout=45000)
            # Stage 1: list pages
            for url in self.LIST_URLS:
                print(f"[ssense] list {url}", flush=True)
                try:
                    p = s.fetch(url, timeout=60000)
                    body = p.body.decode("utf-8","ignore")
                except Exception as e:
                    print(f"[ssense] list fetch err: {str(e)[:80]}", flush=True)
                    continue
                if "Just a moment" in body[:5000]:
                    print("[ssense] CF still blocking — skip", flush=True)
                    continue
                page_items = self.parse_list(body, url)
                new = 0
                for it in page_items:
                    if not it.get("url") or it["url"] in seen:
                        continue
                    seen.add(it["url"])
                    it["dealer"] = self.KEY
                    it["dealer_name"] = self.NAME
                    it["region"] = self.REGION
                    if "discount_pct" not in it:
                        it["discount_pct"] = discount_pct(it.get("original_price"), it.get("sale_price"))
                    items.append(it)
                    new += 1
                print(f"[ssense] list +{new} (total {len(items)})", flush=True)
        # 详情页 enrichment 已放弃: SSENSE PDP 全部被 Cloudflare 拦回 stub HTML，
        # Camoufox/StealthySession 都解不开。color 已从列表页 line-through HTML 拿到，
        # sizes 留空（前端 cardHTML 会显示 "尺码见 SSENSE" 占位）。
        return items

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
    import json as _json, os as _os, time as _time
    _os.makedirs("dealers/_partial", exist_ok=True)
    _json.dump({"name":"SSENSE","region":"US","count":len(items),"items":items,"saved_at":_time.strftime("%Y-%m-%d %H:%M:%S")},
               open("dealers/_partial/ssense.json","w"), indent=2, ensure_ascii=False)
    print(f"→ dealers/_partial/ssense.json")
