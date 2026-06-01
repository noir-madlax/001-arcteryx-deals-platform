"""MEC (mec.ca) — 2026-05-22 起改用 curl_cffi 模拟 Chrome TLS 指纹绕过 Cloudflare,
彻底扔掉 Camoufox (省 ~600MB RAM, 跑 30 min → 3 min).

数据来源:
- 列表页 https://www.mec.ca/en/products?brand=Arc%27teryx&page={N}
  解析 <__NEXT_DATA__> 里 serverState.initialResults.products_en.results[0].hits
- 详情页 https://www.mec.ca/en/product/<code>/<slug>
  解析 <__NEXT_DATA__> 里 props.pageProps.product (有完整 price/sizes/colours)

必须流程:
1. GET /en/ (warm CF cookies)
2. sleep 2-3 秒
3. GET 任意业务 URL → 200

注: 直接打 PDP 不预热会 403; 预热后 session 内复用 CF cookies.
"""
from __future__ import annotations
from .base import discount_pct
import re, json, time, sys

HOST = "https://www.mec.ca"
NEXT_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(\{.+?\})</script>', re.S)


def _make_session(impersonate="chrome"):
    from curl_cffi import requests
    return requests.Session(impersonate=impersonate)


def _warm(session, retries=4):
    """先访问首页过 CF. 偶发 403, 多试几次."""
    for i in range(retries):
        try:
            r = session.get(f"{HOST}/en/", timeout=25)
            if r.status_code == 200:
                time.sleep(2)
                return True
            time.sleep(2 + i)
        except Exception:
            time.sleep(2 + i)
    return False


def _get(session, url, retries=3):
    """同 session 复用 CF cookies, 失败重试."""
    last_status = "?"
    for i in range(retries):
        try:
            r = session.get(url, timeout=25)
            last_status = r.status_code
            if r.status_code == 200:
                return r
            # 403 / 503 / etc - 等会儿再试
            time.sleep(1.5 + i)
        except Exception as e:
            last_status = type(e).__name__
            time.sleep(1.5 + i)
    return None


class _ScraplingShim:
    """让 scrapling.StealthySession 暴露成 curl_cffi.Session 同接口 —
    避免 scrape() 主逻辑 fork. fetch(url) → r-like 对象 (有 .text/.status_code).

    背景: 2026-06 起 EC2 (AWS Lightsail) IP 被 Cloudflare 加严, curl_cffi
    chrome impersonate 在 MEC 上直接 403. scrapling+solve_cloudflare 慢但能过."""
    def __init__(self, sess):
        self._s = sess
    def get(self, url, timeout=25):
        # scrapling 单位是 ms
        p = self._s.fetch(url, timeout=max(60000, int(timeout) * 1000))
        body = p.body.decode("utf-8", "ignore") if isinstance(p.body, (bytes, bytearray)) else (p.body or "")
        # status 在 scrapling 是 p.status, 兼容 200/3xx
        status = getattr(p, "status", 200) or 200
        class _R: pass
        r = _R(); r.text = body; r.status_code = status
        return r


def _next_data(html: str) -> dict | None:
    m = NEXT_RE.search(html)
    if not m: return None
    try: return json.loads(m.group(1))
    except: return None


def _parse_pdp_price(p: dict) -> tuple[float | None, float | None, int]:
    """从 PDP product.price 提取 (sale, orig, disc_pct)."""
    pr = p.get("price") or {}
    lo = (pr.get("lowPrice") or {}).get("value")
    hi = (pr.get("baseHighPrice") or pr.get("basePrice") or {}).get("value")
    pt = pr.get("priceType", "")
    if not lo and not hi: return None, None, 0
    sale = lo if lo else hi
    orig = hi if hi else sale
    # 非 clearance 类型 = 满价, 强制 disc=0
    if pt not in ("clearance", "sale", "onSale", "discount") and orig and abs(orig - sale) < 0.01:
        return sale, orig, 0
    return sale, orig, discount_pct(orig, sale)


def parse_hit_to_item(hit: dict) -> dict | None:
    """list page hit → 统一 item dict (url/name/price/image/color)."""
    url = hit.get("url")
    title = hit.get("title")
    price = hit.get("price")
    if not url or not title or price is None: return None
    return {
        "url":            HOST + url if url.startswith("/") else url,
        "name":           title,
        "image":          hit.get("image"),
        "color":          hit.get("colour") or "",
        "sale_price":     float(price),
        "original_price": float(price),
        "discount_pct":   0,                # 暂用 list 价, PDP 阶段细化
        "_hit":           hit,              # 后面 enrich 用
    }


def fetch_pdp(session, url: str) -> dict | None:
    """单 PDP, 返回 {sale_price, original_price, discount_pct, sizes, size_stock, color}."""
    r = _get(session, url)
    if not r: return {"_err": "http_failed"}
    d = _next_data(r.text)
    if not d: return {"_err": "no_next_data"}
    p = d.get("props", {}).get("pageProps", {}).get("product")
    if not p: return {"_err": "no_product"}
    avail = p.get("availabilityStatus", "")
    if avail in ("Unavailable", "SoldOut", "Discontinued"):
        return {"_unavailable": True}
    sale, orig, disc = _parse_pdp_price(p)
    if sale is None: return None
    # sizes
    sizes_set = set()
    stock = {}
    for sz in (p.get("sizes") or []):
        lbl = sz.get("label") or sz.get("name")
        if not lbl: continue
        sizes_set.add(lbl)
        avail_s = sz.get("availabilityStatus") or sz.get("inventoryStatus") or ""
        stock[lbl] = "out_of_stock" if avail_s in ("OutOfStock", "Unavailable") else "in_stock"
    colours_set = set(c.get("name") for c in (p.get("colours") or []) if c.get("name"))
    return {
        "sale_price":     float(sale),
        "original_price": float(orig) if orig else float(sale),
        "discount_pct":   disc,
        "sizes":          sorted(sizes_set, key=_size_sort_key),
        "size_stock":     stock,
        "colors":         sorted(colours_set),
        "color":          ", ".join(sorted(colours_set))[:120],
    }


class Scraper:
    KEY    = "mec"
    NAME   = "MEC"
    REGION = "CA"

    LIST_TEMPLATES = [
        "https://www.mec.ca/en/products?brand=Arc%27teryx&page={page}",
    ]
    MAX_PAGES = 10   # MEC ~52/page, 3 页够覆盖

    def scrape(self) -> list[dict]:
        s = _make_session()
        scrapling_ctx = None  # 持有 StealthySession context 防 GC
        using_scrapling = False
        if not _warm(s):
            print("[mec] curl_cffi warm 失败 → 切 scrapling+solve_cloudflare", file=sys.stderr)
            try:
                from scrapling.fetchers import StealthySession
                scrapling_ctx = StealthySession(headless=True, network_idle=True, solve_cloudflare=True)
                ss = scrapling_ctx.__enter__()
                ss.fetch(f"{HOST}/en/", timeout=90000)  # warm + solve turnstile
                s = _ScraplingShim(ss)
                using_scrapling = True
                print("[mec] scrapling 已就绪 (注意: PDP enrich 会跳过,"
                      " 因为 scrapling 每次 fetch 重解 CF 太慢, list 数据足够)", flush=True)
            except Exception as e:
                print(f"[mec] scrapling fallback 也挂: {type(e).__name__} {str(e)[:100]}", file=sys.stderr)
                if scrapling_ctx:
                    try: scrapling_ctx.__exit__(None, None, None)
                    except Exception: pass
                return []
        # ── 阶段 1: list pages
        items = []
        seen = set()
        for tmpl in self.LIST_TEMPLATES:
            for pg in range(1, self.MAX_PAGES + 1):
                url = tmpl.format(page=pg)
                r = _get(s, url)
                if not r:
                    print(f"[mec] LIST FAIL {url} (3x), abort", file=sys.stderr)
                    break
                d = _next_data(r.text)
                if not d:
                    print(f"[mec] page {pg} no NEXT_DATA, stop", file=sys.stderr)
                    break
                hits = (d.get("props", {}).get("pageProps", {})
                         .get("serverState", {}).get("initialResults", {})
                         .get("products_en", {}).get("results", [{}])[0].get("hits") or [])
                if not hits:
                    break
                new = 0
                for h in hits:
                    it = parse_hit_to_item(h)
                    if not it or it["url"] in seen: continue
                    seen.add(it["url"])
                    it["dealer"] = self.KEY
                    it["dealer_name"] = self.NAME
                    it["region"] = self.REGION
                    items.append(it)
                    new += 1
                print(f"[mec] list page {pg} +{new} (total {len(items)})", flush=True)
                if new == 0: break
                time.sleep(1)
        # ── 阶段 2: PDP enrich (sizes / 精确 sale vs orig 区分)
        # scrapling 模式跳过: 每次 fetch 重解 CF turnstile ~5min/PDP, 不可行.
        # list 数据已经够 (url/model/price/image/color), sizes 由 sync 的
        # preserve-existing 逻辑保留 DB 老值.
        if using_scrapling:
            print(f"[mec] scrapling 模式跳过 PDP enrich, 仅用 list 数据 ({len(items)} 件)", flush=True)
            for it in items: it.pop("_hit", None)
        else:
            print(f"[mec] enriching {len(items)} PDPs via curl_cffi...", flush=True)
            for i, it in enumerate(items, 1):
                detail = fetch_pdp(s, it["url"])
                if detail and not detail.get("_err") and not detail.get("_unavailable"):
                    it.pop("_hit", None)
                    it.update(detail)
                elif detail and detail.get("_unavailable"):
                    # 整品下架, 跳过 (不写入 items? 还是保留含 list 价?)
                    # 保留, 让 14 天 stale 兜底; 但移除 _hit
                    it.pop("_hit", None)
                else:
                    it.pop("_hit", None)
                if i % 20 == 0:
                    print(f"[mec] enriched {i}/{len(items)}", flush=True)
                time.sleep(0.3)
        # 主动关掉 scrapling (StealthySession 持有 Camoufox 进程, 不关浪费 RAM)
        if scrapling_ctx is not None:
            try: scrapling_ctx.__exit__(None, None, None)
            except Exception: pass
        return items


# ── size 排序 helper (保留旧逻辑) ──────────────────────────────────────────
_SIZE_ORDER = {"XXS":0,"XS":1,"S":2,"Small":2,"M":3,"Medium":3,"L":4,"Large":4,
               "XL":5,"X-Large":5,"XXL":6,"XX-Large":6,"XXXL":7}
def _size_sort_key(sz: str):
    if sz in _SIZE_ORDER: return (0, _SIZE_ORDER[sz], sz)
    m = re.match(r'^(\d+(?:\.\d+)?)', sz)
    if m: return (1, float(m.group(1)), sz)
    return (2, 0, sz)


if __name__ == "__main__":
    items = Scraper().scrape()
    print(f"\n=== MEC: {len(items)} 件 ===")
    for it in items[:8]:
        d = it.get("discount_pct", 0)
        print(f"  -{d}% C${it.get('sale_price')}/{it.get('original_price')}  {it.get('name','')[:60]}")
    import json as _json, os as _os, time as _time
    _os.makedirs("dealers/_partial", exist_ok=True)
    _json.dump({"name":"MEC","region":"CA","count":len(items),"items":items,"saved_at":_time.strftime("%Y-%m-%d %H:%M:%S")},
               open("dealers/_partial/mec.json","w"), indent=2, ensure_ascii=False)
    print("→ dealers/_partial/mec.json")
