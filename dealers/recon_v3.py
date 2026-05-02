"""
第三轮侦察：针对 NEEDS_WORK 站点定点突破
- evo: solve_cloudflare=True
- backcountry / steepandcheap: 试不同 URL 模式
- sierra: real_chrome=True 强化指纹
- moosejaw: 知道已被 publiclands.com 收购，直接探 publiclands
- zalando_lounge: 需登录态，先看公开首页能否拿到 Arc'teryx 列表
"""
from scrapling.fetchers import StealthyFetcher
import re, json, time

TARGETS = [
    ("evo",          [("https://www.evo.com/shop/brand/arc-teryx", {"solve_cloudflare": True})]),
    ("backcountry",  [
        ("https://www.backcountry.com/c/arc-teryx", {}),
        ("https://www.backcountry.com/Store/catalog/results.jsp?bcb=arc-teryx", {}),
        ("https://www.backcountry.com/store/catalog/categoryResults.jsp?CATEGORY=DEFAULT&BRAND=ARCT", {}),
    ]),
    ("steepandcheap",[
        ("https://www.steepandcheap.com/c/arc-teryx", {}),
        ("https://www.steepandcheap.com/sale", {}),
        ("https://www.steepandcheap.com/search?q=arcteryx", {}),
    ]),
    ("sierra",       [
        ("https://www.sierra.com/", {"real_chrome": True}),
        ("https://www.sierra.com/keyword?keyword=arcteryx", {"real_chrome": True}),
    ]),
    ("moosejaw",     [
        ("https://www.publiclands.com/search?q=arcteryx", {}),  # acquired by Public Lands
        ("https://www.publiclands.com/c/arcteryx", {}),
    ]),
    ("zalando_lounge",[
        ("https://www.zalando-lounge.de/marken/arc-teryx-1", {}),
        ("https://www.zalando-lounge.de/sport/marken/arcteryx", {}),
    ]),
]

def probe(url, opts):
    try:
        p = StealthyFetcher.fetch(url, headless=True, network_idle=True, timeout=60000, **opts)
        body = (p.body or b"").decode("utf-8", errors="ignore")
        bl = body.lower()
        return {
            "url": url,
            "status": p.status,
            "final_url": getattr(p, "url", url),
            "len": len(body),
            "has_brand": ("arcteryx" in bl or "arc-teryx" in bl or "arc'teryx" in bl),
            "has_price": (body.count("$") + body.count("€") + body.count("£")) > 5,
            "title": (re.search(r"<title>([^<]+)</title>", body, re.I).group(1)[:120] if re.search(r"<title>", body, re.I) else ""),
        }
    except Exception as e:
        return {"url": url, "error": f"{type(e).__name__}: {str(e)[:140]}"}

def main():
    out = {}
    for key, urls_opts in TARGETS:
        print(f"\n>> {key}")
        rs = []
        for u, opts in urls_opts:
            print(f"   probing {u} (opts={opts}) ...")
            r = probe(u, opts)
            rs.append(r)
            if "error" in r:
                print(f"     ERR {r['error']}")
            else:
                print(f"     status={r['status']} len={r['len']} brand={r['has_brand']} price={r['has_price']} title={r['title'][:80]!r}")
                print(f"     final={r['final_url'][:100]}")
            if not r.get("error") and r.get("has_brand") and r.get("has_price") and r.get("status") in (200, 404):
                break
        out[key] = rs
    with open("dealers/recon_v3_results.json", "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("\n=== V3 SUMMARY ===")
    for k, rs in out.items():
        good = next((r for r in rs if not r.get("error") and r.get("has_brand") and r.get("has_price")), None)
        if good:
            print(f"{k:<16} OK  {good['url']}")
        else:
            print(f"{k:<16} XX  {rs[0].get('error', 'no good probe')[:80]}")

if __name__ == "__main__":
    main()
