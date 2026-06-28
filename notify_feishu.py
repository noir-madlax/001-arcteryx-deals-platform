#!/usr/bin/env python3
"""Send post-sync Arc'teryx crawler summaries to a Feishu chat.

Env:
  FEISHU_APP_ID
  FEISHU_APP_SECRET
  FEISHU_CHAT_ID       open chat id, e.g. oc_xxx
  SUPABASE_URL
  SUPABASE_KEY
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent
SKUS_FILE = BASE_DIR / "arcteryx_skus.json"
DEALERS_FILE = BASE_DIR / "dealers" / "results.json"
RUN_START_FILE = BASE_DIR / ".last_run_start"

FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "").strip()
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "").strip()
FEISHU_CHAT_ID = os.environ.get("FEISHU_CHAT_ID", "").strip()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://bupqagkrcvrezjkdbald.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def _request_json(url: str, payload: dict | None = None, headers: dict | None = None, timeout: int = 20) -> dict:
    data = None
    req_headers = headers or {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req_headers = {"Content-Type": "application/json; charset=utf-8", **req_headers}
    req = urllib.request.Request(url, data=data, headers=req_headers)
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _sb_get(path: str, params: dict | None = None, range_hdr: str | None = None) -> tuple[list | dict, str]:
    qs = f"?{urllib.parse.urlencode(params)}" if params else ""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    if range_hdr:
        headers["Range"] = range_hdr
        headers["Prefer"] = "count=exact"
    req = urllib.request.Request(f"{SUPABASE_URL}/rest/v1/{path}{qs}", headers=headers)
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8")), resp.headers.get("content-range", "")


def _count(path: str, params: dict | None = None) -> int:
    _, content_range = _sb_get(path, params=params or {"select": "sku_id"}, range_hdr="0-0")
    try:
        return int(content_range.split("/")[-1])
    except (IndexError, ValueError):
        return -1


def _duration_text() -> str:
    if not RUN_START_FILE.exists():
        return "unknown"
    try:
        start = datetime.strptime(RUN_START_FILE.read_text().strip(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        mins = int((datetime.now(timezone.utc) - start).total_seconds() / 60)
        return f"{mins} min"
    except Exception:
        return "unknown"


def _plain(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</?(?:b|strong|i|em|s|code)>", "", text, flags=re.I)
    return html.unescape(text)


def build_outlet_report() -> str:
    try:
        from notify_telegram import build_report
        return _plain(build_report())
    except Exception:
        pass

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if not SKUS_FILE.exists():
        return f"Arc'teryx outlet sync - {now}\narcteryx_skus.json missing."
    rows = json.loads(SKUS_FILE.read_text())
    by_region = Counter(r.get("region") or "?" for r in rows)
    discounts = [r.get("discount_pct") or 0 for r in rows if r.get("sale_price")]
    avg_discount = sum(discounts) / len(discounts) if discounts else 0
    lines = [
        f"Arc'teryx outlet sync - {now}",
        f"Duration: {_duration_text()}",
        f"SKUs scraped: {len(rows)}",
        f"Average discount: {avg_discount:.0f}%",
        "By region: " + ", ".join(f"{k}:{v}" for k, v in sorted(by_region.items())),
        "https://001.100app.dev",
    ]
    return "\n".join(lines)


def build_dealers_report() -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if not DEALERS_FILE.exists():
        return f"Arc'teryx dealer sync - {now}\ndealers/results.json missing."

    data = json.loads(DEALERS_FILE.read_text())
    dealers = data.get("dealers") or {}
    counts = {key: (info.get("count") or len(info.get("items") or [])) for key, info in dealers.items()}
    total = data.get("total") or sum(counts.values())

    db_count = -1
    try:
        db_count = _count("products", {"select": "sku_id", "dealer": "in.(mec,evo,rei,ssense)"})
    except Exception:
        pass

    top_items = []
    for key, info in dealers.items():
        for item in info.get("items") or []:
            top_items.append((item.get("discount_pct") or 0, key, item))
    top_items.sort(key=lambda row: row[0], reverse=True)

    lines = [
        f"Arc'teryx dealer sync - {now}",
        f"Duration: {_duration_text()}",
        f"Scraped total: {total}",
        "By dealer: " + ", ".join(f"{k}:{v}" for k, v in sorted(counts.items())),
    ]
    if db_count >= 0:
        lines.append(f"DB dealer products: {db_count}")
    if top_items:
        lines.append("")
        lines.append("Top discounts:")
        for disc, dealer, item in top_items[:5]:
            name = (item.get("name") or "?")[:58]
            sale = item.get("sale_price")
            orig = item.get("original_price")
            currency = item.get("currency") or ""
            lines.append(f"- {disc}% [{dealer}] {name} - {currency}{sale}/{orig}")
    lines.append("")
    lines.append("https://001.100app.dev")
    return "\n".join(lines)


def build_revalidate_report() -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    db_count = -1
    try:
        db_count = _count("products", {"select": "sku_id", "dealer": "in.(mec,evo,rei,ssense)"})
    except Exception:
        pass
    lines = [
        f"Arc'teryx dealer revalidate - {now}",
        "Dealer URL price revalidation completed.",
    ]
    if db_count >= 0:
        lines.append(f"DB dealer products: {db_count}")
    lines.append("https://001.100app.dev")
    return "\n".join(lines)


def get_tenant_access_token() -> str:
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        raise RuntimeError("FEISHU_APP_ID / FEISHU_APP_SECRET not set")
    body = _request_json(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        {"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
    )
    if body.get("code") != 0:
        raise RuntimeError(f"tenant_access_token error: {body}")
    token = body.get("tenant_access_token")
    if not token:
        raise RuntimeError("tenant_access_token missing")
    return token


def send(text: str) -> bool:
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET or not FEISHU_CHAT_ID:
        print("[feishu] FEISHU_APP_ID / FEISHU_APP_SECRET / FEISHU_CHAT_ID not set - skipping", file=sys.stderr)
        print(text)
        return False

    token = get_tenant_access_token()
    body = _request_json(
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
        {
            "receive_id": FEISHU_CHAT_ID,
            "msg_type": "text",
            "content": json.dumps({"text": text}, ensure_ascii=False),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    if body.get("code") == 0:
        print("[feishu] sent")
        return True
    print(f"[feishu] API error: {body}", file=sys.stderr)
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["outlet", "dealers", "revalidate"], default="outlet")
    parser.add_argument("--prefix", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.mode == "dealers":
        text = build_dealers_report()
    elif args.mode == "revalidate":
        text = build_revalidate_report()
    else:
        text = build_outlet_report()
    if args.prefix:
        text = f"{args.prefix}\n{text}"
    if args.dry_run:
        print(text)
        return 0
    return 0 if send(text) else 1


if __name__ == "__main__":
    raise SystemExit(main())
