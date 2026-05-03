"""REI (rei.com) — 用 Camoufox 才能进，普通 search 直接 403。"""
from __future__ import annotations
from camoufox.sync_api import Camoufox
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

    def scrape(self) -> list[dict]:
        items = []
        seen = set()
        with Camoufox(headless=True, humanize=True, geoip=True) as browser:
            page = browser.new_page()
            print("[rei] warm: home")
            page.goto(f"{HOST}/", wait_until="networkidle", timeout=60000)
            time.sleep(2)
            for list_url in self.LIST_URLS:
                print(f"[rei] {list_url}")
                page.goto(list_url, wait_until="networkidle", timeout=60000)
                time.sleep(8)  # let products render
                body = page.content()
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
                    msale = self.SALE_RE.search(chunk)
                    mfull = self.FULL_RE.search(chunk)
                    mreg  = self.REG_RE.search(chunk)
                    sale = orig = None
                    if msale:
                        sale = normalize_price(msale.group(1))
                    if mfull:
                        orig = normalize_price(mfull.group(1))
                    elif mreg:
                        orig = sale = normalize_price(mreg.group(1))
                    if not sale and not orig:
                        # try any $XXX in chunk
                        ps = [normalize_price(x) for x in re.findall(r'\$([\d,]+\.\d{2})', chunk)][:2]
                        ps = [x for x in ps if x]
                        if ps: sale = orig = min(ps)
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
                print(f"[rei] +{len(items)} (total)")
        return items


if __name__ == "__main__":
    items = Scraper().scrape()
    print(f"\n=== REI {len(items)} 件 ===")
    for it in items[:8]:
        d = it.get("discount_pct", 0)
        print(f"  -{d}%  ${it.get('sale_price')}/{it.get('original_price')}  {it.get('name')[:60]}")
