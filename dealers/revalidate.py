"""Dealer URL Revalidator
============================
列表 scraper 只能拿到当前在列表/搜索页的商品。商品掉出列表后,
DB 里旧价就僵在那里. 本脚本针对已知 dealer URL 重新拉 PDP 验价格.

策略 (按 dealer 分组, 复用浏览器 session):
- EVO    : Shopify /products/{handle}.json (纯 HTTP, 最快)
- MEC    : curl_cffi (impersonate=chrome), __NEXT_DATA__.product 价格
- REI    : curl_cffi (impersonate=chrome), data-ui="sale-price"/"full-price" 标签
- SSENSE : curl_cffi (impersonate=chrome), JSON-LD "@type":"Product" offers.price

更新逻辑:
- 成功拿到价格 → UPDATE sale/orig/disc/last_updated
- 失败 (404 / CF stub / 网络错) → 不更新 last_updated, 让 14 天 stale 兜底清理
- 价格变化 → 同步写一行 price_history

每日 06:30 UTC 跑一次, 错开 outlet 06:00 + dealer 03/09/15/21
"""
from __future__ import annotations
import os, sys, time, json, re, urllib.request, ssl
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path

SB_URL = os.environ.get("SUPABASE_URL", "https://bupqagkrcvrezjkdbald.supabase.co")
SB_KEY = os.environ.get("SUPABASE_KEY", "")
if not SB_KEY: sys.exit("SUPABASE_KEY required (service_role)")

# ── Shared helpers ────────────────────────────────────────────────────────
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"

def _num(s):
    if s is None: return None
    s = str(s).replace(",","").strip().lstrip("$€£")
    try: return float(s)
    except: return None

def _disc(orig, sale):
    if not orig or not sale or orig <= 0 or sale > orig: return 0
    return round((1 - sale/orig) * 100)

# ── Per-dealer PDP fetchers ──────────────────────────────────────────────
def fetch_evo_pdp(url: str) -> dict | None:
    """EVO Shopify, 用 /products/<handle>.js (注意 .js 不是 .json)
    它返回 variant.available 字段 + 顶层 available 标识. price 是 cents 单位."""
    m = re.search(r'/products/([^/?#]+)', url or "")
    if not m: return None
    handle = m.group(1)
    api = f"https://www.evo.com/products/{handle}.js"
    try:
        req = urllib.request.Request(api, headers={
            "User-Agent": _UA,
            "Accept": "application/javascript, application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.evo.com/",
        })
        with urllib.request.urlopen(req, context=_CTX, timeout=15) as r:
            p = json.loads(r.read().decode("utf-8","ignore"))
    except Exception as e:
        return {"_err": f"http {type(e).__name__}"}
    # 顶层 available=False 表示整品下架
    if p.get("available") is False:
        return {"_unavailable": True}
    variants = p.get("variants") or []
    avail = [v for v in variants if v.get("available")]
    if not avail:
        return {"_unavailable": True}
    # price 单位是 cents (e.g. 19120 = \$191.20). 除 100 转 dollars
    prices   = [(_num(v.get("price")) or 0) / 100 for v in avail if v.get("price")]
    compares = [(_num(v.get("compare_at_price")) or 0) / 100 for v in avail if v.get("compare_at_price")]
    prices   = [x for x in prices if x > 0]
    compares = [x for x in compares if x > 0]
    if not prices: return None
    sale = min(prices)
    orig = max(compares) if compares else sale
    if orig < sale: orig = sale
    return {"sale_price": round(sale, 2), "original_price": round(orig, 2), "discount_pct": _disc(orig, sale)}

def fetch_rei_pdp(session, url: str) -> dict | None:
    """REI curl_cffi (impersonate=chrome) PDP. data-ui="sale-price" + "full-price" 标签."""
    try:
        r = session.get(url, timeout=25)
        if r.status_code != 200:
            return {"_err": f"http {r.status_code}"}
        body = r.text
    except Exception as e:
        return {"_err": f"{type(e).__name__}"}
    if len(body) < 20000:  # Akamai stub
        return {"_err": "akamai_stub"}
    if "page-not-found" in body.lower() or "page not found" in body.lower():
        return {"_unavailable": True}
    msale = re.search(r'data-ui="sale-price">\s*\$?([0-9.,]+)', body)
    mfull = re.search(r'data-ui="full-price">\s*\$?([0-9.,]+)', body)
    mreg  = re.search(r'data-ui="regular-price">\s*\$?([0-9.,]+)', body)
    sale = orig = None
    if msale and mfull:
        sale = _num(msale.group(1)); orig = _num(mfull.group(1))
    elif mfull:
        sale = orig = _num(mfull.group(1))
    elif mreg:
        sale = orig = _num(mreg.group(1))
    elif msale:
        sale = orig = _num(msale.group(1))
    if not sale: return None
    if not orig: orig = sale
    return {"sale_price": sale, "original_price": orig, "discount_pct": _disc(orig, sale)}

def fetch_mec_pdp(session, url: str) -> dict | None:
    """MEC curl_cffi (impersonate=chrome). 解 __NEXT_DATA__.product 的 price.
    priceType=clearance → 有折扣; 否则满价 disc=0."""
    from dealers.mec import _get, _next_data, _parse_pdp_price
    r = _get(session, url)
    if not r: return {"_err": "http_failed"}
    d = _next_data(r.text)
    if not d: return {"_err": "no_next_data"}
    p = d.get("props",{}).get("pageProps",{}).get("product")
    if not p: return {"_err": "no_product"}
    if p.get("availabilityStatus") in ("Unavailable","SoldOut","Discontinued"):
        return {"_unavailable": True}
    sale, orig, disc = _parse_pdp_price(p)
    if not sale: return None
    return {"sale_price": float(sale), "original_price": float(orig or sale), "discount_pct": disc}

def fetch_ssense_pdp(session, url: str) -> dict | None:
    """SSENSE curl_cffi (impersonate=chrome) PDP. JSON-LD Product schema.
    URL 必须含 /en-us/ 前缀, 否则 SSENSE 返回 404 fallback (~400KB) 没价格."""
    # SSENSE JSON-LD url 历史漏 locale 前缀, 兜底注入
    if "/en-us/" not in url:
        url = url.replace("/men/product/", "/en-us/men/product/").replace("/women/product/", "/en-us/women/product/")
    try:
        r = session.get(url, timeout=25)
        if r.status_code != 200:
            return {"_err": f"http {r.status_code}"}
        body = r.text
    except Exception:
        return None
    if "Just a moment" in body[:5000] or len(body) < 50000:
        return {"_err": "cf_stub"}
    for m in re.finditer(r'<script[^>]+type="application/ld\+json"[^>]*>(\{[^<]+?\})</script>', body):
        try:
            d = json.loads(m.group(1))
            if d.get("@type") != "Product": continue
            offer = d.get("offers") or {}
            sale = _num(offer.get("price"))
            if not sale: continue
            # SSENSE JSON-LD 不含原价, 看 HTML line-through 兜底 (略复杂, 这里先保守保留原 orig)
            return {"sale_price": sale}   # 只更新 sale, 不动 orig
        except Exception:
            pass
    return None

# ── Main runner ──────────────────────────────────────────────────────────
def load_all_dealer_rows(client):
    rows = []
    page = 0
    while True:
        res = client.table("products").select(
            "sku_id,dealer,url,sale_price,original_price"
        ).neq("dealer", "arcteryx_outlet").range(page*1000, page*1000+999).execute()
        data = res.data or []
        rows.extend(data)
        if len(data) < 1000: break
        page += 1
    return rows

def update_row(client, sku_id, patch, old_row):
    """写 Supabase + 如果价格变了同时 insert price_history."""
    if not patch: return False
    now_iso = datetime.now(timezone.utc).isoformat()
    patch = dict(patch)
    patch["last_updated"] = now_iso
    try:
        client.table("products").update(patch).eq("sku_id", sku_id).execute()
    except Exception as e:
        print(f"  UPDATE ERR {sku_id}: {str(e)[:100]}", file=sys.stderr)
        return False
    # 价格变了, 记录历史
    new_sale = patch.get("sale_price")
    old_sale = old_row.get("sale_price")
    if new_sale is not None and old_sale is not None and abs(new_sale - old_sale) > 0.01:
        try:
            client.table("price_history").insert({
                "sku_id":         sku_id,
                "sale_price":     new_sale,
                "original_price": patch.get("original_price") or old_row.get("original_price"),
                "discount_pct":   patch.get("discount_pct"),
                "recorded_at":    now_iso,
            }).execute()
        except Exception:
            pass
    return True

def main():
    from supabase import create_client
    client = create_client(SB_URL, SB_KEY)
    rows = load_all_dealer_rows(client)
    print(f"[reval] loaded {len(rows)} dealer rows", flush=True)
    by_dealer = defaultdict(list)
    for r in rows:
        by_dealer[r.get("dealer")].append(r)
    for d, rs in by_dealer.items():
        print(f"  {d}: {len(rs)}", flush=True)

    stats = defaultdict(lambda: {"ok":0, "skip":0, "err":0, "unavail":0, "diff":0})

    # ── EVO: 纯 HTTP, 最快 ──
    print(f"\n[reval] EVO ({len(by_dealer.get('evo', []))})", flush=True)
    for i, r in enumerate(by_dealer.get("evo", []), 1):
        new = fetch_evo_pdp(r["url"])
        if not new:
            stats["evo"]["err"] += 1
        elif new.get("_unavailable"):
            stats["evo"]["unavail"] += 1
        elif new.get("_err"):
            stats["evo"]["err"] += 1
        else:
            if update_row(client, r["sku_id"], new, r):
                stats["evo"]["ok"] += 1
                if abs((new.get("sale_price") or 0) - (r.get("sale_price") or 0)) > 0.01:
                    stats["evo"]["diff"] += 1
            else:
                stats["evo"]["err"] += 1
        if i % 50 == 0: print(f"  evo {i}/{len(by_dealer['evo'])}", flush=True)
        time.sleep(0.1)

    # ── REI: curl_cffi (Chrome TLS 指纹, 不用浏览器) ──
    if by_dealer.get("rei"):
        print(f"\n[reval] REI ({len(by_dealer['rei'])}) — curl_cffi", flush=True)
        try:
            from curl_cffi import requests as _cffi
            rei_s = _cffi.Session(impersonate="chrome")
            # warm
            for _ in range(3):
                try:
                    if rei_s.get("https://www.rei.com/", timeout=25).status_code == 200: break
                except Exception: pass
                time.sleep(2)
            time.sleep(2)
            for i, r in enumerate(by_dealer["rei"], 1):
                new = fetch_rei_pdp(rei_s, r["url"])
                if not new: stats["rei"]["err"] += 1
                elif new.get("_unavailable"): stats["rei"]["unavail"] += 1
                elif new.get("_err"): stats["rei"]["err"] += 1
                else:
                    if update_row(client, r["sku_id"], new, r):
                        stats["rei"]["ok"] += 1
                        if abs((new.get("sale_price") or 0) - (r.get("sale_price") or 0)) > 0.01:
                            stats["rei"]["diff"] += 1
                if i % 10 == 0: print(f"  rei {i}/{len(by_dealer['rei'])}", flush=True)
                time.sleep(0.3)
        except Exception as e:
            print(f"  REI curl_cffi err: {e}", file=sys.stderr)

    # ── MEC: curl_cffi (Chrome TLS 指纹, 不用浏览器) ──
    if by_dealer.get("mec"):
        print(f"\n[reval] MEC ({len(by_dealer['mec'])}) — curl_cffi", flush=True)
        try:
            from dealers.mec import _make_session, _warm
            mec_s = _make_session()
            if not _warm(mec_s):
                print("  [mec] warm failed, skip", file=sys.stderr)
            else:
                for i, r in enumerate(by_dealer["mec"], 1):
                    new = fetch_mec_pdp(mec_s, r["url"])
                    if not new: stats["mec"]["err"] += 1
                    elif new.get("_unavailable"): stats["mec"]["unavail"] += 1
                    elif new.get("_err"): stats["mec"]["err"] += 1
                    else:
                        if update_row(client, r["sku_id"], new, r):
                            stats["mec"]["ok"] += 1
                            if abs((new.get("sale_price") or 0) - (r.get("sale_price") or 0)) > 0.01:
                                stats["mec"]["diff"] += 1
                    if i % 20 == 0: print(f"  mec {i}/{len(by_dealer['mec'])}", flush=True)
                    time.sleep(0.4)
        except Exception as e:
            print(f"  MEC fetch err: {e}", file=sys.stderr)

    # ── SSENSE: curl_cffi (Chrome TLS 指纹, 不用浏览器) ──
    if by_dealer.get("ssense"):
        print(f"\n[reval] SSENSE ({len(by_dealer['ssense'])}) — curl_cffi", flush=True)
        try:
            from curl_cffi import requests as _cffi
            sn_s = _cffi.Session(impersonate="chrome")
            for _ in range(3):
                try:
                    if sn_s.get("https://www.ssense.com/", timeout=25).status_code == 200: break
                except Exception: pass
                time.sleep(2)
            time.sleep(2)
            for i, r in enumerate(by_dealer["ssense"], 1):
                new = fetch_ssense_pdp(sn_s, r["url"])
                if not new: stats["ssense"]["err"] += 1
                elif new.get("_unavailable"): stats["ssense"]["unavail"] += 1
                elif new.get("_err"): stats["ssense"]["err"] += 1
                else:
                    if update_row(client, r["sku_id"], new, r):
                        stats["ssense"]["ok"] += 1
                        if abs((new.get("sale_price") or 0) - (r.get("sale_price") or 0)) > 0.01:
                            stats["ssense"]["diff"] += 1
                if i % 10 == 0: print(f"  ssense {i}/{len(by_dealer['ssense'])}", flush=True)
                time.sleep(0.4)
        except Exception as e:
            print(f"  SSENSE curl_cffi err: {e}", file=sys.stderr)

    print("\n=== REVAL DONE ===")
    for d, s in stats.items():
        print(f"  {d:8s} ok={s['ok']:4d}  价变={s['diff']:3d}  缺货={s['unavail']:3d}  错={s['err']:3d}")

if __name__ == "__main__":
    main()
