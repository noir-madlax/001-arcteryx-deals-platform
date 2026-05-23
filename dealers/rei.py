"""REI (rei.com) — 2026-05 起切 curl_cffi (impersonate=chrome) 模拟 Chrome TLS 指纹
绕过 Akamai 反爬, 不再需要 Camoufox (省 ~600MB RAM, 30min → 3min).

必须流程:
1. GET / (warm)
2. sleep 2 秒
3. GET 任意业务 URL → 200 (search / PDP)

注: 同 SSENSE/MEC, 同 session 内复用 cookies."""
from __future__ import annotations
import re, time
from .base import normalize_price, discount_pct

HOST = "https://www.rei.com"

class Scraper:
    KEY    = "rei"
    NAME   = "REI"
    REGION = "US"

    LIST_URLS = [
        "https://www.rei.com/search?q=arcteryx",
    ]

    # Card 标志：
    # <a href="/product/<id>/<slug>"> ... <img alt="Arc'teryx <name> 0">
    # 后面：<span data-ui="sale-price">$XXX</span><span data-ui="full-price">- $YYY</span>
    URL_RE   = re.compile(r'/product/(\d+)/(arcteryx[a-z0-9-]+)')
    CARD_NAME_RE = re.compile(r'<img[^>]+alt="(Arc\'?teryx [^"]+?)\s*\d*"', re.I)
    SALE_RE  = re.compile(r'data-ui="sale-price">\s*\$([\d.,]+)')
    FULL_RE  = re.compile(r'data-ui="full-price">\s*[\-\s]*\$([\d.,]+)')
    REG_RE   = re.compile(r'data-ui="regular-price">\s*\$([\d.,]+)')
    IMG_RE   = re.compile(r'<img[^>]+id="image-(\d+)-0"[^>]+src="([^"]+)"')

    # PDP: <button class="size-selector__size-button" data-ui="size-selector-button:available|unavailable"><span aria-hidden="true">SIZE</span></button>
    SIZE_BUTTON_RE = re.compile(
        r'<button[^>]+class="size-selector__size-button"[^>]+data-ui="size-selector-button:(available|unavailable|sold-out)"[^>]*>.*?<span\s+aria-hidden="true"[^>]*>([^<]+)</span>',
        re.S
    )
    # color buttons: <button class="color-btn" data-color="BLACK" data-ui="available">
    COLOR_BUTTON_RE = re.compile(
        r'<button[^>]+class="color-btn[^"]*"[^>]+data-color="([^"]+)"[^>]+data-ui="(available|unavailable|sold-out)"',
    )
    # current selected color label
    SELECTED_COLOR_RE = re.compile(r'class="color-selector-wrapper__selected-color"[^>]*>([^<]+)</span>')

    def parse_detail(self, body: str) -> dict:
        """REI PDP: 抓 size buttons + color swatch"""
        sizes = []
        size_stock = {}
        for m in self.SIZE_BUTTON_RE.finditer(body):
            status, sz = m.group(1), m.group(2).strip()
            if not sz: continue
            sizes.append(sz)
            size_stock[sz] = 'in_stock' if status == 'available' else 'out_of_stock'
        colors = []
        for m in self.COLOR_BUTTON_RE.finditer(body):
            cl = m.group(1).strip().title()  # BLACK → Black
            if cl: colors.append(cl)
        sel = self.SELECTED_COLOR_RE.search(body)
        primary_color = sel.group(1).strip() if sel else (colors[0] if colors else "")
        return {
            "sizes": sizes,
            "size_stock": size_stock,
            "colors": colors,
            "color": primary_color,
        }

    def scrape(self) -> list[dict]:
        from curl_cffi import requests as cffi
        items = []
        seen = set()
        s = cffi.Session(impersonate="chrome")
        # warm: 必须先访问首页, Akamai 才下发 session cookies
        print("[rei] warm: home", flush=True)
        for _ in range(3):
            try:
                r = s.get(f"{HOST}/", timeout=25)
                if r.status_code == 200: break
            except Exception: pass
            time.sleep(2)
        time.sleep(2)
        # ── 阶段 1: list pages ──────────────────────────────────────────
        for list_url in self.LIST_URLS:
            print(f"[rei] {list_url}", flush=True)
            body = self._fetch(s, list_url)
            if not body:
                print(f"[rei] list FAIL {list_url}", flush=True)
                continue
            if True:
                # find all product anchor positions
                positions = [(m.start(), m.group(1), m.group(2)) for m in self.URL_RE.finditer(body)]
                # de-dup by id
                seen_ids = set()
                for start, pid, slug in positions:
                    if pid in seen_ids: continue
                    seen_ids.add(pid)
                    if pid in seen: continue
                    seen.add(pid)
                    # take next 2500 chars as card context
                    chunk = body[start:start+8000]
                    # name from img alt (first occurrence in chunk)
                    mname = self.CARD_NAME_RE.search(chunk)
                    name = mname.group(1).strip() if mname else slug.replace("arcteryx-","").replace("-"," ").title()
                    # cleanup name
                    name = re.sub(r"^Arc'?teryx\s+", "", name, flags=re.I)
                    # prices
                    # REI 5/18 后改了搜索结果 markup:
                    # - 在售商品: <sale-price>X</sale-price> + <full-price>Y</full-price>  → sale=X orig=Y
                    # - 满价商品: 只有 <full-price>Y</full-price>                          → sale=orig=Y, disc=0
                    # 之前逻辑 "if mfull: orig=Y else: sale=orig=full" 在满价场景把 Y 写成
                    # 一个无意义的 orig (无 sale), 然后 fall back 取整片 chunk min, 偶尔抓到
                    # 隔壁商品价格当 sale → 形成假折扣 (例: Kyanite 抓到 $99.83 -50%)
                    msale = self.SALE_RE.search(chunk)
                    mfull = self.FULL_RE.search(chunk)
                    mreg  = self.REG_RE.search(chunk)
                    sale = orig = None
                    if msale and mfull:
                        sale = normalize_price(msale.group(1))
                        orig = normalize_price(mfull.group(1))
                    elif mfull:
                        # 满价: full-price 即当前价, 不打折
                        sale = orig = normalize_price(mfull.group(1))
                    elif mreg:
                        sale = orig = normalize_price(mreg.group(1))
                    elif msale:
                        # 只有 sale 标签 (奇葩, 缺 full): 当成单一价
                        sale = orig = normalize_price(msale.group(1))
                    if not sale: continue
                    if not orig: orig = sale
                    # image
                    mimg = re.search(rf'<img[^>]+id="image-{pid}-0"[^>]+src="([^"]+)"', body)
                    img = (HOST + mimg.group(1)) if mimg and mimg.group(1).startswith("/") else (mimg.group(1) if mimg else None)
                    # gender from slug
                    g = "men" if "-mens" in slug else ("women" if "-womens" in slug else "unisex")
                    items.append({
                        "url":            f"{HOST}/product/{pid}/{slug}",
                        "name":           name,
                        "image":          img,
                        "original_price": orig,
                        "sale_price":     sale,
                        "currency":       "USD",
                        "in_stock":       True,
                        "gender":         g,
                        "discount_pct":   discount_pct(orig, sale),
                        "dealer":         self.KEY,
                        "dealer_name":    self.NAME,
                        "region":         self.REGION,
                    })
                print(f"[rei] list +{len(items)} (total)")
        # ── 阶段 2: PDP enrichment (curl_cffi 复用同 session, 不再启浏览器) ──
        print(f"[rei] enriching {len(items)} PDPs via curl_cffi...", flush=True)
        for i, it in enumerate(items, 1):
            body = self._fetch(s, it["url"])
            if body:
                detail = self.parse_detail(body)
                if detail: it.update(detail)
            if i % 10 == 0: print(f"[rei] enriched {i}/{len(items)}", flush=True)
            time.sleep(0.3)
        return items

    @staticmethod
    def _fetch(session, url: str, retries: int = 3) -> str:
        for i in range(retries):
            try:
                r = session.get(url, timeout=25)
                if r.status_code == 200 and len(r.text) > 5000:
                    return r.text
                time.sleep(1.5 + i)
            except Exception:
                time.sleep(1.5 + i)
        return ""


if __name__ == "__main__":
    items = Scraper().scrape()
    print(f"\n=== REI {len(items)} 件 ===")
    for it in items[:8]:
        d = it.get("discount_pct", 0)
        print(f"  -{d}%  ${it.get('sale_price')}/{it.get('original_price')}  {it.get('name')[:60]}")
    import json as _json, os as _os, time as _time
    _os.makedirs("dealers/_partial", exist_ok=True)
    _json.dump({"name":"REI","region":"US","count":len(items),"items":items,"saved_at":_time.strftime("%Y-%m-%d %H:%M:%S")},
               open("dealers/_partial/rei.json","w"), indent=2, ensure_ascii=False)
    print(f"→ dealers/_partial/rei.json")
