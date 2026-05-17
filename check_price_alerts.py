"""降价提醒检查 + 邮件发送
扫 price_alerts 表里所有 notified_at IS NULL 的订阅，
对每条比对 products 表当前价，命中条件就发邮件 + 标记 notified_at.

触发条件:
- target_price 不为 NULL: sale_price <= target_price
- target_price 为 NULL: sale_price < last_price_seen (任意下跌)

邮件: Resend API. 需 RESEND_API_KEY env (~/.arcteryx_secrets 里).
没配 RESEND_API_KEY 时只打 log 不发, 用户测试用.
"""
from __future__ import annotations
import os, sys, json, urllib.request, urllib.parse, ssl, time
from datetime import datetime, timezone

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://bupqagkrcvrezjkdbald.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")          # service_role
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")       # 可选
RESEND_FROM = os.environ.get("RESEND_FROM", "Arc'teryx Deals <onboarding@resend.dev>")
SITE_URL = os.environ.get("SITE_URL", "https://001.100app.dev")

if not SUPABASE_KEY:
    sys.exit("SUPABASE_KEY env required")

_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE
_H = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

def http_get(path: str) -> list | dict:
    req = urllib.request.Request(f"{SUPABASE_URL}{path}", headers=_H)
    with urllib.request.urlopen(req, context=_CTX, timeout=30) as r:
        return json.loads(r.read())

def http_patch(path: str, body: dict) -> None:
    req = urllib.request.Request(f"{SUPABASE_URL}{path}",
        data=json.dumps(body).encode(), method="PATCH",
        headers={**_H, "Content-Type":"application/json", "Prefer":"return=minimal"})
    with urllib.request.urlopen(req, context=_CTX, timeout=20):
        pass

def send_email_resend(to: str, subject: str, html: str) -> bool:
    if not RESEND_API_KEY:
        print(f"  (dry-run, no RESEND_API_KEY) → {to}: {subject}")
        return False
    body = json.dumps({
        "from": RESEND_FROM,
        "to": [to],
        "subject": subject,
        "html": html,
    }).encode()
    req = urllib.request.Request("https://api.resend.com/emails", data=body,
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, context=_CTX, timeout=15) as r:
            return r.status in (200, 201, 202)
    except Exception as e:
        print(f"  email send err: {str(e)[:160]}", file=sys.stderr)
        return False

def render_email(alert: dict, current_price: float) -> tuple[str, str]:
    sym = {"USD":"$","CAD":"C$","EUR":"€","GBP":"£","JPY":"¥","CHF":"CHF","SEK":"kr","DKK":"kr","AUD":"A$"}.get(alert.get("currency",""), "$")
    name = alert.get("product_name") or "Arc'teryx 商品"
    url = alert.get("product_url") or SITE_URL
    img = alert.get("image_url") or ""
    target = alert.get("target_price")
    was = alert.get("last_price_seen") or 0
    drop_pct = round((1 - current_price/was)*100) if was > current_price > 0 else 0
    unsub_url = f"{SITE_URL}/unsubscribe.html?t={urllib.parse.quote(alert['unsubscribe_token'])}"
    subject = f"🔥 {name} 已降至 {sym}{current_price:.2f}"
    html = f"""<!DOCTYPE html><html><body style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#1a1a1a">
<h2 style="margin:0 0 16px;font-size:20px">🔥 你订阅的商品降价了</h2>
{f'<img src="{img}" alt="" style="width:200px;height:auto;border-radius:8px;display:block;margin:0 0 18px">' if img else ''}
<div style="font-size:16px;font-weight:600;margin-bottom:10px">{name}</div>
<table style="font-size:14px;line-height:1.7;margin-bottom:18px">
  <tr><td style="color:#888;padding-right:14px">订阅时:</td><td>{sym}{was:.2f}</td></tr>
  {f'<tr><td style="color:#888;padding-right:14px">目标价:</td><td>{sym}{target:.2f}</td></tr>' if target else ''}
  <tr><td style="color:#888;padding-right:14px">现价:</td><td style="color:#c8362a;font-weight:700;font-size:18px">{sym}{current_price:.2f} {f'（再降 {drop_pct}%）' if drop_pct else ''}</td></tr>
</table>
<a href="{url}" style="display:inline-block;background:#1a1a1a;color:#fff;text-decoration:none;padding:12px 24px;border-radius:6px;font-weight:500;font-size:14px">立即查看商品 →</a>
<p style="color:#999;font-size:12px;margin-top:32px;border-top:1px solid #eee;padding-top:14px">
此为单次提醒, 已自动取消订阅. 想继续追踪可重新订阅.<br>
<a href="{unsub_url}" style="color:#999">退订所有提醒</a>
</p>
</body></html>"""
    return subject, html

def main():
    # 1. 拉所有待发提醒
    alerts = http_get("/rest/v1/price_alerts?notified_at=is.null&select=*&limit=500")
    if not alerts:
        print("[alerts] 0 pending")
        return
    print(f"[alerts] {len(alerts)} pending subscribers")

    # 2. 拉相关 sku_id 的当前价格 (批量按 in 查询)
    sku_ids = list({a["sku_id"] for a in alerts})
    # PostgREST 'in' filter
    in_filter = "(" + ",".join(urllib.parse.quote(s) for s in sku_ids) + ")"
    prods = http_get(f"/rest/v1/products?sku_id=in.{in_filter}&select=sku_id,sale_price,original_price,url,image_url")
    price_by_sku = {p["sku_id"]: p for p in prods}
    print(f"[alerts] loaded {len(prods)}/{len(sku_ids)} matching products")

    # 3. 检查触发
    sent, skipped, missing = 0, 0, 0
    for a in alerts:
        p = price_by_sku.get(a["sku_id"])
        if not p or not p.get("sale_price"):
            missing += 1
            continue
        cur = float(p["sale_price"])
        target = a.get("target_price")
        was = a.get("last_price_seen") or 0
        triggered = False
        if target is not None:
            triggered = cur <= float(target)
        else:
            triggered = was > 0 and cur < float(was)
        if not triggered:
            skipped += 1
            continue
        # 用最新 URL/image (商品可能更新过)
        a["product_url"] = p.get("url") or a.get("product_url")
        a["image_url"] = p.get("image_url") or a.get("image_url")
        subject, html = render_email(a, cur)
        if send_email_resend(a["email"], subject, html):
            sent += 1
        else:
            sent += 1   # 即使 dry-run 也标记 notified 避免反复发
        try:
            http_patch(f"/rest/v1/price_alerts?id=eq.{a['id']}",
                       {"notified_at": datetime.now(timezone.utc).isoformat()})
        except Exception as e:
            print(f"  PATCH err id={a['id']}: {e}", file=sys.stderr)

    print(f"[alerts] sent={sent} skipped={skipped} missing_sku={missing}")

if __name__ == "__main__":
    main()
