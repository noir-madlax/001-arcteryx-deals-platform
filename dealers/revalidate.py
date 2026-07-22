"""Dealer URL Revalidator
============================
列表 scraper 只能拿到当前在列表/搜索页的商品。商品掉出列表后,
DB 里旧价就僵在那里. 本脚本针对已知 dealer URL 重新拉 PDP 验价格.

策略 (按 dealer 分组, 复用浏览器 session):
- EVO    : Shopify /products/{handle}.json (纯 HTTP, 最快)
- MEC    : curl_cffi (impersonate=chrome), __NEXT_DATA__.product 价格
- REI    : Camoufox (curl_cffi 在 AWS Lightsail 被 Akamai 拒), data-ui="sale-price"/"full-price"
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

# ── Shared helpers ────────────────────────────────────────────────────────
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"


def _env_float(name: str, default: float, minimum: float = 0.0) -> float:
    try:
        return max(minimum, float(os.environ.get(name, default)))
    except (TypeError, ValueError):
        return max(minimum, default)

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


def parse_evo_browser_snapshot(snapshot: dict, url: str) -> dict | None:
    product = (snapshot.get("ShopifyAnalytics") or {}).get("meta", {}).get("product") or {}
    regios = snapshot.get("RegiosDOPP_ProductPage") or {}
    inventory_blob = snapshot.get("igProductData") or {}
    inventory = inventory_blob.get(str(product.get("id"))) or inventory_blob.get(product.get("id")) or {}
    variants = regios.get("variants") or []
    available = [variant for variant in variants if not variant.get("isOutOfStock")]
    fallback_sale = (_num(inventory.get("lowestVariantPrice")) or 0) / 100
    fallback_orig = (_num(regios.get("compareAtPriceInCents")) or 0) / 100
    if available:
        prices = [(_num(variant.get("priceInCents")) or 0) / 100 for variant in available]
        compares = [(_num(variant.get("compareAtPriceInCents")) or 0) / 100 for variant in available]
        prices = [price for price in prices if price > 0]
        compares = [compare for compare in compares if compare > 0]
        if fallback_sale > 0:
            prices.append(fallback_sale)
        if fallback_orig > 0:
            compares.append(fallback_orig)
        if prices:
            sale = min(prices)
            orig = max(compares) if compares else sale
            if orig < sale:
                orig = sale
            return {
                "sale_price": round(sale, 2),
                "original_price": round(orig, 2),
                "discount_pct": _disc(orig, sale),
            }
    if fallback_sale > 0:
        orig = fallback_orig if fallback_orig >= fallback_sale else fallback_sale
        return {
            "sale_price": round(fallback_sale, 2),
            "original_price": round(orig, 2),
            "discount_pct": _disc(orig, fallback_sale),
        }
    return None


def fetch_evo_pdp_browser(page, url: str) -> dict | None:
    try:
        response = page.goto(url, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(3000)
    except Exception as e:
        return {"_err": f"goto {type(e).__name__}"}
    if not response or response.status != 200:
        return {"_err": f"http {response.status if response else 'unknown'}"}
    snapshot = page.evaluate(
        """() => ({
          ShopifyAnalytics: window.ShopifyAnalytics || null,
          igProductData: window.igProductData || null,
          RegiosDOPP_ProductPage: window.RegiosDOPP_ProductPage || null,
        })"""
    )
    parsed = parse_evo_browser_snapshot(snapshot, url)
    return parsed or {"_err": "no_browser_price"}


def _evo_needs_browser_fallback(result: dict | None) -> bool:
    if not result:
        return True
    if result.get("_unavailable"):
        return False
    return bool(result.get("_err"))


def _rei_variant_price(body: str, url: str) -> tuple[float, float] | None:
    """Return the cheapest available current-product SKU and its compare-at price."""
    product_match = re.search(r"/product/(\d+)/", url or "")
    if not product_match:
        return None
    product_id = product_match.group(1)
    decoder = json.JSONDecoder()
    marker = '"skus":'
    start = 0
    while True:
        marker_pos = body.find(marker, start)
        if marker_pos < 0:
            return None
        array_pos = marker_pos + len(marker)
        try:
            skus, _ = decoder.raw_decode(body[array_pos:])
        except (json.JSONDecodeError, TypeError):
            start = array_pos
            continue
        if not isinstance(skus, list) or not any(
            str(sku.get("skuId", "")).startswith(product_id)
            for sku in skus if isinstance(sku, dict)
        ):
            start = array_pos
            continue
        prices = []
        for sku in skus:
            if not isinstance(sku, dict) or sku.get("status") != "AVAILABLE":
                continue
            price = sku.get("price") or {}
            sale = _num((price.get("price") or {}).get("value"))
            original = _num((price.get("compareAt") or {}).get("value")) or sale
            if sale and str(sku.get("skuId", "")).startswith(product_id):
                prices.append((sale, max(original or sale, sale)))
        if not prices:
            return None
        lowest_sale = min(sale for sale, _ in prices)
        original = max(orig for sale, orig in prices if sale == lowest_sale)
        return lowest_sale, original

def fetch_rei_pdp(page, url: str) -> dict | None:
    """REI Camoufox PDP. Supports both legacy and current buy-box prices.
    注: curl_cffi 在 AWS Lightsail 上被 Akamai 拒 (全路径返 2.7KB stub),
    所以 REI 必须用 Camoufox; SSENSE/MEC 不受影响."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(2)
    except Exception as e:
        return {"_err": f"goto {type(e).__name__}"}
    body = ""
    for _ in range(6):
        try:
            body = page.content()
            if len(body) >= 20000:
                break
        except Exception:
            # REI frequently replaces the document after domcontentloaded.
            pass
        time.sleep(2)
    if not body:
        return {"_err": "unstable_document"}
    if len(body) < 20000:  # CF stub
        return {"_err": "cf_stub"}
    if "page-not-found" in body.lower() or "page not found" in body.lower():
        return {"_unavailable": True}
    msale = re.search(r'data-ui="sale-price">\s*\$?([0-9.,]+)', body)
    mfull = re.search(r'data-ui="full-price">\s*[-\s]*\$?([0-9.,]+)', body)
    mreg  = re.search(r'data-ui="regular-price">\s*\$?([0-9.,]+)', body)
    mbuy  = re.search(r'id="buy-box-product-price"[^>]*>\s*\$?([0-9.,]+)', body)
    mitem = re.search(r'data-cnstrc-item-price="([0-9.,]+)"', body)
    sale = orig = None
    variant_price = _rei_variant_price(body, url)
    if variant_price:
        sale, orig = variant_price
    elif msale and mfull:
        sale = _num(msale.group(1)); orig = _num(mfull.group(1))
    elif mfull:
        sale = orig = _num(mfull.group(1))
    elif mreg:
        sale = orig = _num(mreg.group(1))
    elif msale:
        sale = orig = _num(msale.group(1))
    elif mbuy:
        sale = orig = _num(mbuy.group(1))
    elif mitem:
        sale = orig = _num(mitem.group(1))
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
    return {
        "sale_price": float(sale),
        "original_price": float(orig or sale),
        "discount_pct": disc,
        "currency": "CAD",
        "symbol": "C$",
    }

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
    return parse_ssense_html(body)


def parse_ssense_html(body: str) -> dict | None:
    if "Just a moment" in body[:5000]:
        return {"_err": "cf_stub"}
    normalized = re.sub(r"\s+", " ", body)

    def _money_text(value: str | None) -> float | None:
        cleaned = re.sub(r"[^0-9.]", "", value or "")
        return _num(cleaned)

    for m in re.finditer(r'<script[^>]+type="application/ld\+json"[^>]*>\s*(\{[^<]+?\})\s*</script>', body):
        try:
            d = json.loads(m.group(1))
            if d.get("@type") != "Product": continue
            offer = d.get("offers") or {}
            sale = _num(offer.get("price"))
            if not sale: continue
            original = None
            mo = re.search(r'line-through[^>]*>\s*([^<]+?)\s*</span>', body)
            if mo:
                original = _money_text(mo.group(1))
            if not original:
                text_match = re.search(r'\$([0-9.,]+)\s*USD\s*\$([0-9.,]+)\s*USD', normalized)
                if text_match:
                    sale_candidate = _money_text(text_match.group(1))
                    original_candidate = _money_text(text_match.group(2))
                    if sale_candidate and original_candidate:
                        sale = sale_candidate
                        original = original_candidate
            original = max(original or sale, sale)
            return {
                "sale_price": round(sale, 2),
                "original_price": round(original, 2),
                "discount_pct": _disc(original, sale),
            }
        except Exception:
            pass
    return None


def fetch_ssense_pdp_browser(page, url: str) -> dict | None:
    try:
        response = page.goto(url, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(4000)
    except Exception as e:
        return {"_err": f"goto {type(e).__name__}"}
    if not response or response.status != 200:
        return {"_err": f"http {response.status if response else 'unknown'}"}
    html = page.content()
    parsed = parse_ssense_html(html)
    if parsed and parsed.get("original_price", 0) > parsed.get("sale_price", 0):
        return parsed
    text = page.evaluate("() => document.body ? document.body.innerText : ''")
    prices = re.findall(r"\$([0-9.,]+)\s*USD", text or "")
    if parsed and len(prices) >= 2:
        sale = _num(prices[0])
        original = _num(prices[1])
        if sale and original and original >= sale:
            return {
                "sale_price": round(sale, 2),
                "original_price": round(original, 2),
                "discount_pct": _disc(original, sale),
            }
    return parsed

# ── Main runner ──────────────────────────────────────────────────────────
def load_all_dealer_rows(client):
    rows = []
    page = 0
    while True:
        res = client.table("products").select(
            "sku_id,dealer,url,sale_price,original_price,last_updated"
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


def underperforming_dealers(by_dealer, stats, minimum_success_ratio: float = 0.70) -> list[str]:
    return sorted(
        d for d, dealer_rows in by_dealer.items()
        if dealer_rows and (
            stats[d]["ok"] + stats[d]["unavail"]
        ) / len(dealer_rows) < minimum_success_ratio
    )

def main():
    if not SB_KEY:
        sys.exit("SUPABASE_KEY required (service_role)")
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
    evo_rows = by_dealer.get("evo", [])
    evo_browser_cm = None
    evo_browser = None
    evo_page = None
    try:
        for i, r in enumerate(evo_rows, 1):
            new = fetch_evo_pdp(r["url"])
            if _evo_needs_browser_fallback(new):
                retry = fetch_evo_pdp(r["url"])
                if retry and not retry.get("_err"):
                    new = retry
                elif retry and retry.get("_unavailable"):
                    new = retry
                else:
                    if evo_browser is None:
                        from camoufox.sync_api import Camoufox
                        evo_browser_cm = Camoufox(headless=True, humanize=True, geoip=True)
                        evo_browser = evo_browser_cm.__enter__()
                        evo_page = evo_browser.new_page()
                        evo_page.set_default_navigation_timeout(90000)
                    new = fetch_evo_pdp_browser(evo_page, r["url"])
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
            if i % 50 == 0: print(f"  evo {i}/{len(evo_rows)}", flush=True)
            time.sleep(0.1)
    finally:
        if evo_browser_cm is not None:
            try:
                evo_browser_cm.__exit__(None, None, None)
            except Exception:
                pass

    # ── REI: Camoufox (curl_cffi 在 AWS Lightsail 上被 Akamai 拒) ──
    if by_dealer.get("rei"):
        # Oldest first ensures rate-limited tail rows are first on the next run.
        rei_rows = sorted(by_dealer["rei"], key=lambda row: row.get("last_updated") or "")
        rei_delay = _env_float("REI_REVALIDATE_DELAY_SECONDS", 3.0, 0.5)
        print(f"\n[reval] REI ({len(rei_rows)}) — Camoufox, delay={rei_delay}s", flush=True)
        try:
            from camoufox.sync_api import Camoufox
            with Camoufox(headless=True, humanize=True, geoip=True) as br:
                page = br.new_page()
                page.goto("https://www.rei.com/", wait_until="networkidle", timeout=60000)
                time.sleep(2)
                for i, r in enumerate(rei_rows, 1):
                    new = fetch_rei_pdp(page, r["url"])
                    if not new: stats["rei"]["err"] += 1
                    elif new.get("_unavailable"): stats["rei"]["unavail"] += 1
                    elif new.get("_err"): stats["rei"]["err"] += 1
                    else:
                        if update_row(client, r["sku_id"], new, r):
                            stats["rei"]["ok"] += 1
                            if abs((new.get("sale_price") or 0) - (r.get("sale_price") or 0)) > 0.01:
                                stats["rei"]["diff"] += 1
                    if i % 5 == 0: print(f"  rei {i}/{len(rei_rows)}", flush=True)
                    time.sleep(rei_delay)
        except Exception as e:
            print(f"  REI Camoufox launch err: {e}", file=sys.stderr)

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
            first_row = by_dealer["ssense"][0]
            probe = fetch_ssense_pdp(sn_s, first_row["url"])
            use_browser = bool(probe and probe.get("_err") in {"http 403", "cf_stub", "http 401", "http 429"})
            if use_browser:
                from camoufox.sync_api import Camoufox
                print("  [ssense] direct HTTP blocked; switching to Camoufox", flush=True)
                with Camoufox(headless=True, humanize=True, geoip=True) as browser:
                    page = browser.new_page()
                    page.set_default_navigation_timeout(90000)
                    for i, r in enumerate(by_dealer["ssense"], 1):
                        new = fetch_ssense_pdp_browser(page, r["url"])
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
            else:
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
    for d in sorted(by_dealer):
        s = stats[d]
        print(f"  {d:8s} ok={s['ok']:4d}  价变={s['diff']:3d}  缺货={s['unavail']:3d}  错={s['err']:3d}")

    failed_dealers = underperforming_dealers(by_dealer, stats)
    if failed_dealers:
        raise SystemExit(
            "[reval] successful validation ratio below 70% for: "
            + ", ".join(failed_dealers)
        )

if __name__ == "__main__":
    main()
