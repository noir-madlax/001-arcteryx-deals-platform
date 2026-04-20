#!/usr/bin/env python3
"""
notify_telegram.py
────────────────
Build a post-scrape stats report and send it to Telegram.

Run AFTER supabase_sync.py in server_run_update.sh. It reads:
  - arcteryx_skus.json (for current scrape snapshot)
  - Supabase price_history (for price-change stats)
  - .last_run_start  (optional: plain-text UTC timestamp of the run start,
                      written at the beginning of server_run_update.sh)

Env:
  TELEGRAM_BOT_TOKEN     bot token from @BotFather
  TELEGRAM_CHAT_ID       numeric chat id (personal chat or group)
  SUPABASE_URL           already set by server_run_update.sh
  SUPABASE_KEY           already set by server_run_update.sh
"""

import json
import os
import sys
import ssl
import urllib.request
import urllib.parse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR      = Path(__file__).parent
SKUS_FILE     = BASE_DIR / "arcteryx_skus.json"
RUN_START_FILE = BASE_DIR / ".last_run_start"

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def _sb_get(path: str, params: dict = None, range_hdr: str = None) -> tuple:
    """GET from Supabase REST, returns (json_body, content_range header)."""
    qs = f"?{urllib.parse.urlencode(params)}" if params else ""
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/{path}{qs}",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            **({"Range": range_hdr} if range_hdr else {}),
            **({"Prefer": "count=exact"} if range_hdr else {}),
        },
    )
    resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=30)
    body = json.loads(resp.read())
    return body, resp.headers.get("content-range", "")


def _count(path: str, extra_filter: str = "") -> int:
    _, cr = _sb_get(
        f"{path}{'&' + extra_filter if '?' in path else '?' + extra_filter}" if extra_filter else path,
        params={"select": "id"} if "?" not in path else None,
        range_hdr="0-0",
    )
    # content-range looks like "0-0/12345"
    try:
        return int(cr.split("/")[-1])
    except (ValueError, IndexError):
        return 0


def build_report() -> str:
    if not SKUS_FILE.exists():
        return "⚠️ <b>Arc'teryx scrape notification</b>\n\narcteryx_skus.json missing — did the scrape fail?"

    skus = json.loads(SKUS_FILE.read_text())
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Run duration
    duration_txt = "?"
    if RUN_START_FILE.exists():
        try:
            start = datetime.strptime(RUN_START_FILE.read_text().strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            mins = int((datetime.now(timezone.utc) - start).total_seconds() / 60)
            duration_txt = f"{mins} min"
        except Exception:
            pass

    # ── Scrape aggregates ─────────────────────────────────────────────────
    total = len(skus)
    by_region  = Counter(s.get("region", "?") for s in skus)
    by_gender  = Counter(s.get("gender", "?") for s in skus)
    discounts  = [s.get("discount_pct") or 0 for s in skus if s.get("sale_price")]
    avg_disc   = sum(discounts) / len(discounts) if discounts else 0
    deep_disc  = sum(1 for d in discounts if d >= 50)

    # Top discounts (by pct, in-stock preferred)
    top = sorted(
        [s for s in skus if (s.get("discount_pct") or 0) >= 30],
        key=lambda s: -(s.get("discount_pct") or 0),
    )[:5]

    # ── Price-change delta from price_history ─────────────────────────────
    price_changes_today = 0
    drops = 0
    hikes = 0
    try:
        # rows inserted in the last 4 hours (this run's window)
        body, _ = _sb_get(
            "price_history",
            params={
                "select": "sku_id,original_price,sale_price,recorded_at",
                "recorded_at": f"gte.{(datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z'))[:10]}T00:00:00Z",
                "order": "recorded_at.desc",
            },
            range_hdr="0-4999",
        )
        price_changes_today = len(body)

        # Per-sku, compare this run's price to the previous recorded price
        latest_by_sku = {}
        for r in body:
            sid = r["sku_id"]
            latest_by_sku.setdefault(sid, []).append(r)

        for sid, rows in latest_by_sku.items():
            if len(rows) < 2:
                continue
            new_sp = rows[0].get("sale_price") or 0
            old_sp = rows[1].get("sale_price") or 0
            if new_sp < old_sp:
                drops += 1
            elif new_sp > old_sp:
                hikes += 1
    except Exception as e:
        price_changes_today = -1  # signal "unknown"

    # ── Supabase totals (post-sync) ───────────────────────────────────────
    try:
        db_products = _count("products", "select=id")
        db_history  = _count("price_history", "select=id")
    except Exception:
        db_products = db_history = -1

    # ── Build HTML message ────────────────────────────────────────────────
    lines = [
        f"✅ <b>Arc'teryx scrape — {now_iso}</b>",
        f"⏱  Duration: {duration_txt}",
        "",
        f"📦 <b>SKUs scraped:</b> {total}  |  avg discount <b>{avg_disc:.0f}%</b>  |  ≥50% off: <b>{deep_disc}</b>",
        f"🗄  DB now: <b>{db_products}</b> products, <b>{db_history}</b> price-history rows",
    ]
    if price_changes_today >= 0:
        lines.append(f"💹 Price snapshots this run: <b>{price_changes_today}</b>  (↓{drops}  ↑{hikes})")

    lines.append("")
    lines.append("<b>By region</b>")
    for region, n in by_region.most_common():
        lines.append(f"  • {region}: {n}")

    if top:
        lines.append("")
        lines.append("<b>🔥 Top discounts this run</b>")
        for s in top:
            name = (s.get("full_name") or s.get("model") or "?")[:50]
            sym  = s.get("symbol") or s.get("currency") or ""
            disc = s.get("discount_pct") or 0
            op   = s.get("original_price") or 0
            sp   = s.get("sale_price") or 0
            region = s.get("region", "")
            lines.append(f"  • <b>{disc}%</b> {name} ({region}) — {sym}{sp:g} <s>{sym}{op:g}</s>")

    lines.append("")
    lines.append("🔗 https://001.100app.dev")
    return "\n".join(lines)


def send(text: str) -> bool:
    if not BOT_TOKEN or not CHAT_ID:
        print("[telegram] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set — skipping", file=sys.stderr)
        print(text)
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    req = urllib.request.Request(url, data=data)
    try:
        resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=15)
        body = json.loads(resp.read())
        if body.get("ok"):
            print("[telegram] sent")
            return True
        print(f"[telegram] API error: {body}", file=sys.stderr)
    except Exception as e:
        print(f"[telegram] send failed: {e}", file=sys.stderr)
    return False


if __name__ == "__main__":
    try:
        msg = build_report()
    except Exception as e:
        msg = f"⚠️ <b>Arc'teryx scrape notification build failed</b>\n<code>{e}</code>"
    send(msg)
