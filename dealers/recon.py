"""
经销商侦察脚本 — 对 13 个 Arc'teryx 经销商做一次性探测：
1. 用 Fetcher（纯 HTTP）尝试访问候选品牌页
2. 看 status / 是否被 Cloudflare 拦截 / 页面是否包含 'arcteryx' 字符串
3. 判定反爬等级：F (Fetcher OK) / S (需 Stealthy) / D (需 Dynamic / Cloudflare)
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from scrapling.fetchers import Fetcher
import re, sys, json

DEALERS = [
    # (key, name, country, candidate URLs to probe — will try in order)
    ("evo",          "EVO",            "US", [
        "https://www.evo.com/shop/brand/arc-teryx",
        "https://www.evo.com/brands/arcteryx",
        "https://www.evo.com/sale/arc-teryx",
    ]),
    ("backcountry",  "Backcountry",    "US", [
        "https://www.backcountry.com/arcteryx",
        "https://www.backcountry.com/arcteryx-sale",
        "https://www.backcountry.com/c/arcteryx",
    ]),
    ("moosejaw",     "Moosejaw",       "US", [
        "https://www.moosejaw.com/brand/arcteryx",
        "https://www.moosejaw.com/sale/brand-arcteryx",
        "https://www.moosejaw.com/search?q=arcteryx",
    ]),
    ("rei_outlet",   "REI Outlet",     "US", [
        "https://www.rei.com/b/arc-teryx?ir=brand%3AArc%27teryx&r=outlet",
        "https://www.rei.com/rei-garage/b/arc-teryx",
        "https://www.rei.com/b/arc-teryx",
    ]),
    ("sierra",       "Sierra",         "US", [
        "https://www.sierra.com/arcteryx~d~b/",
        "https://www.sierra.com/lp2/arcteryx-mens.jsp",
    ]),
    ("steepandcheap","Steep & Cheap",  "US", [
        "https://www.steepandcheap.com/arcteryx",
        "https://www.steepandcheap.com/arcteryx-sale",
    ]),
    ("thelasthunt",  "The Last Hunt",  "CA", [
        "https://www.thelasthunt.com/collections/arcteryx",
        "https://www.thelasthunt.com/collections/arc-teryx",
    ]),
    ("altitude",     "Altitude Sports","CA", [
        "https://www.altitude-sports.com/collections/arcteryx",
        "https://www.altitude-sports.com/collections/arc-teryx-sale",
    ]),
    ("mec",          "MEC",            "CA", [
        "https://www.mec.ca/en/brands/arcteryx",
        "https://www.mec.ca/en/products?brand=Arc%27teryx",
    ]),
    ("ssense",       "SSENSE",         "CA", [
        "https://www.ssense.com/en-us/men/designers/arcteryx",
        "https://www.ssense.com/en-us/men/designers/arc-teryx",
        "https://www.ssense.com/en-us/men/sale/designers/arcteryx",
    ]),
    ("sportsshoes",  "SportsShoes",    "UK", [
        "https://www.sportsshoes.com/brand/ARC/arcteryx",
        "https://www.sportsshoes.com/brand/arcteryx",
    ]),
    ("zalando_lounge","Zalando Lounge","DE", [
        "https://www.zalando-lounge.com/brands/arcteryx",
        "https://www.zalando-lounge.de/brands/arcteryx",
        "https://www.zalando-lounge.com/de-de/brands/arcteryx",
    ]),
    ("haoriz",       "好日子",          "CN", [
        "https://www.haoriz.com/search?q=arcteryx",
        "https://www.haoriz.com/brand/arcteryx",
        "https://haoriz.com/?s=arcteryx",
    ]),
]

def probe(url: str) -> dict:
    try:
        p = Fetcher.get(url, timeout=20, follow_redirects=True)
        body = (p.body or b"").decode("utf-8", errors="ignore")[:200000]
        has_brand   = bool(re.search(r"arc\W?teryx", body, re.I))
        cf_block    = bool(re.search(r"cloudflare|cf-ray|attention required|just a moment", body, re.I)) and p.status in (403, 503)
        # crude "looks like a product list" signal
        looks_listy = (body.count("$") + body.count("€") + body.count("£") + body.count("¥") + body.count("CHF")) > 5
        return {
            "url": url, "status": p.status, "len": len(body),
            "brand_str": has_brand, "cf_blocked": cf_block,
            "looks_listy": looks_listy,
        }
    except Exception as e:
        return {"url": url, "error": f"{type(e).__name__}: {e}"[:200]}

def assess(probes: list[dict]) -> str:
    # pick the best probe (highest score)
    def score(p):
        if "error" in p: return -1
        s = 0
        if p.get("status") == 200: s += 4
        if p.get("brand_str"): s += 3
        if p.get("looks_listy"): s += 2
        if p.get("cf_blocked"): s -= 5
        return s
    best = max(probes, key=score)
    if "error" in best: return f"ERR:{best['error'][:60]}"
    if best.get("cf_blocked"): return "CF_BLOCKED"
    if best.get("status") == 200 and best.get("brand_str") and best.get("looks_listy"):
        return "F_OK"   # plain Fetcher works
    if best.get("status") == 200 and best.get("brand_str"):
        return "F_THIN" # got page but content looks JS-rendered
    if best.get("status") in (403, 401):
        return "BLOCKED_HTTP"
    if best.get("status") in (404, 410):
        return "NOT_FOUND"
    return f"UNCLEAR({best.get('status')})"

def run():
    results = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = {}
        for key, name, country, urls in DEALERS:
            for u in urls:
                futs[ex.submit(probe, u)] = (key, name, country, u)
        per_dealer = {}
        for f in as_completed(futs):
            key, name, country, u = futs[f]
            r = f.result()
            per_dealer.setdefault(key, {"name": name, "country": country, "probes": []})["probes"].append(r)
        for key, info in per_dealer.items():
            info["verdict"] = assess(info["probes"])
            results[key] = info

    # nice console summary
    print(f"{'KEY':<16}{'COUNTRY':<8}{'VERDICT':<18}{'BEST URL'}")
    print("-" * 100)
    for key, info in results.items():
        # pick the probe with status 200 if any
        best_url = ""
        for p in info["probes"]:
            if p.get("status") == 200:
                best_url = p["url"]; break
        if not best_url:
            best_url = info["probes"][0].get("url", "")
        print(f"{key:<16}{info['country']:<8}{info['verdict']:<18}{best_url}")
    with open("dealers/recon_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\n→ dealers/recon_results.json")

if __name__ == "__main__":
    run()
