"""通用 Camoufox 网络拦截工具。打开真 Firefox，访问 URL，
监听所有 application/json 响应，回传给调用方解析。

工作原理（关键）：
- Camoufox 用 BrowserForge 生成的真实指纹，比 patchright 更难被识破
- 用 page.on('response', ...) 拦截所有 XHR/fetch
- network_idle 之后再多等几秒，让客户端 GraphQL 完成
"""
from camoufox.sync_api import Camoufox
import time, json
from typing import Callable, Iterable

def fetch_with_intercept(
    url_to_visit: str,
    warm_url: str | None = None,
    response_filter: Callable[[str, str], bool] = lambda url, ctype: ("graphql" in url.lower()) or ("/api/" in url.lower()),
    extra_wait_seconds: float = 6.0,
    timeout_ms: int = 60000,
    max_responses: int = 200,
    proxy: dict | None = None,
) -> dict:
    """
    返回 {"final_status": int, "final_url": str, "html": str,
          "responses": [(url, status, body), ...]}
    """
    captured: list[tuple[str, int, str]] = []

    with Camoufox(headless=True, humanize=True, geoip=True) as browser:
        page = browser.new_page()

        def on_response(resp):
            if len(captured) >= max_responses:
                return
            try:
                ct = resp.headers.get("content-type", "")
            except Exception:
                ct = ""
            if not response_filter(resp.url, ct):
                return
            try:
                body = resp.text()
            except Exception:
                body = ""
            captured.append((resp.url, resp.status, body))

        page.on("response", on_response)

        if warm_url:
            try:
                page.goto(warm_url, wait_until="networkidle", timeout=timeout_ms)
                time.sleep(1.5)
            except Exception as e:
                print(f"[camoufox] warm-up err: {e}")

        page.goto(url_to_visit, wait_until="networkidle", timeout=timeout_ms)
        # extra wait for client-side GraphQL fetches
        time.sleep(extra_wait_seconds)

        html = page.content()
        final_url = page.url

    return {
        "final_status": 200,  # camoufox doesn't expose http status here easily
        "final_url": final_url,
        "html": html,
        "responses": captured,
    }


if __name__ == "__main__":
    import sys, os
    URL = sys.argv[1] if len(sys.argv) > 1 else "https://www.backcountry.com/cat/mens-clothing?ftxt=arc%27teryx"
    WARM = "https://www.backcountry.com/" if ("backcountry" in URL or "steepandcheap" in URL) else (
        "https://www.rei.com/" if "rei.com" in URL else None
    )
    # capture EVERY json response (not just /api/, /graphql)
    rf = lambda url, ctype: ("json" in (ctype or "").lower()) or any(s in url.lower() for s in ("graphql","/api/","search","catalog","plp","product"))
    print(f"camoufox visiting {URL}")
    r = fetch_with_intercept(URL, warm_url=WARM, response_filter=rf)
    print(f"final_url: {r['final_url']}")
    print(f"html len: {len(r['html'])}")
    print(f"responses captured: {len(r['responses'])}")
    # Save html + responses
    os.makedirs("/tmp/dealer_html", exist_ok=True)
    slug = URL.replace("https://","").replace("/","_").replace("?","_").replace("=","_").replace("%","").replace("&","_")[:80]
    with open(f"/tmp/dealer_html/cf_{slug}.html","w") as f:
        f.write(r["html"])
    with open(f"/tmp/dealer_html/cf_{slug}_responses.json","w") as f:
        json.dump([{"url": u, "status": s, "body": b[:200000]} for u,s,b in r["responses"]], f, indent=2)
    for url, st, body in r["responses"][:50]:
        sample = ""
        if body and len(body) > 50:
            try:
                d = json.loads(body)
                txt = json.dumps(d)
                arc = txt.lower().count("arc'teryx") + txt.lower().count("arc-teryx") + txt.lower().count("arcteryx")
                sample = f"json {len(txt)}c arc={arc}"
            except:
                sample = f"non-json {len(body)}c"
        print(f"  {st} {url[:140]}  {sample}")
