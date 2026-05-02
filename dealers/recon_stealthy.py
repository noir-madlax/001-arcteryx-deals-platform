"""
第二轮侦察：用 StealthyFetcher 处理 202/CF_BLOCKED/wrong-redirect 站点。
对 altitude/thelasthunt 走站内搜索；对 backcountry/moosejaw/mec 等走 Akamai bot challenge。
"""
from scrapling.fetchers import StealthyFetcher
import re, json, time

# (key, label, urls to try) — 用 stealthy 真浏览器
TARGETS = [
    ("evo",          "EVO",           ["https://www.evo.com/shop/brand/arc-teryx"]),
    ("backcountry",  "Backcountry",   ["https://www.backcountry.com/arcteryx-sale"]),
    ("moosejaw",     "Moosejaw",      ["https://www.moosejaw.com/search?q=arcteryx&filter=brand%3AArc%27teryx"]),
    ("rei_outlet",   "REI",           [
        "https://www.rei.com/search?q=arcteryx&r=outlet",
        "https://www.rei.com/c/mens-jackets/f/b-arc-teryx",
    ]),
    ("sierra",       "Sierra",        ["https://www.sierra.com/search.jsp?keyword=arcteryx"]),
    ("steepandcheap","S&C",           ["https://www.steepandcheap.com/arcteryx"]),
    ("mec",          "MEC",           ["https://www.mec.ca/en/products?brand=Arc%27teryx&filter=&page=1"]),
    ("thelasthunt",  "TheLastHunt",   [
        "https://www.thelasthunt.com/search?q=arcteryx",
        "https://www.thelasthunt.com/search?q=arc%27teryx",
    ]),
    ("altitude",     "Altitude",      [
        "https://www.altitude-sports.com/search?q=arcteryx",
        "https://www.altitude-sports.com/c/brand/arc-teryx",
    ]),
    ("zalando_lounge","ZalandoLounge",["https://www.zalando-lounge.de/marken/arcteryx",
                                        "https://www.zalando-lounge.de/marken/arc-teryx"]),
    ("sportsshoes",  "SportsShoes",   [
        "https://www.sportsshoes.com/search/?q=arcteryx",
        "https://www.sportsshoes.com/products?brands=Arc%27teryx",
    ]),
]

def probe_stealthy(url: str) -> dict:
    try:
        p = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=45000)
        body = (p.body or b"").decode("utf-8", errors="ignore")
        bl = body.lower()
        return {
            "url": url,
            "status": p.status,
            "final_url": getattr(p, "url", url),
            "len": len(body),
            "has_brand": ("arcteryx" in bl or "arc-teryx" in bl or "arc'teryx" in bl),
            "has_price": (body.count("$") + body.count("€") + body.count("£") + body.count("CHF")) > 5,
            "title": (re.search(r"<title>([^<]+)</title>", body, re.I).group(1)[:120] if re.search(r"<title>", body, re.I) else ""),
        }
    except Exception as e:
        return {"url": url, "error": f"{type(e).__name__}: {str(e)[:140]}"}

def run():
    out = {}
    for key, label, urls in TARGETS:
        print(f"\n>> {label} [{key}]")
        results = []
        for u in urls:
            print(f"   probing {u} ...")
            r = probe_stealthy(u)
            results.append(r)
            if "error" in r:
                print(f"     ERR {r['error']}")
            else:
                print(f"     status={r['status']} len={r['len']} brand={r['has_brand']} price={r['has_price']} final={r['final_url'][:80]}")
                print(f"     title={r['title']!r}")
            # if first probe succeeded, no need to try others
            if not r.get("error") and r.get("has_brand") and r.get("has_price"):
                break
        out[key] = {"label": label, "probes": results}
        time.sleep(1)
    with open("dealers/recon_stealthy_results.json", "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("\n\n=== SUMMARY ===")
    print(f"{'KEY':<16}{'VERDICT':<14}{'BEST URL'}")
    for k, v in out.items():
        good = next((p for p in v["probes"] if not p.get("error") and p.get("has_brand") and p.get("has_price")), None)
        if good:
            print(f"{k:<16}{'STEALTHY_OK':<14}{good['url']}")
        else:
            best = v["probes"][0]
            v_str = best.get("error", f"st={best.get('status')} brand={best.get('has_brand')}")[:60]
            print(f"{k:<16}{'NEEDS_WORK':<14}{v_str}")

if __name__ == "__main__":
    run()
