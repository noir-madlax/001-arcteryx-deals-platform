"""把 dealers/results.json 同步到 Supabase products 表。
要求: 先在 Supabase Studio 执行 dealers/supabase_migration.sql 一次。

使用 service_role key（bypass RLS）。每个 dealer 单独 upsert，
stale-row 检测限定 dealer 范围（不会删掉 outlet 行，反之亦然）。
"""
from __future__ import annotations
import os, json, re, sys, hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
RESULTS_FILE = ROOT / "dealers" / "results.json"
BATCH_SIZE = 50
SYM = {"USD":"$", "CAD":"C$", "EUR":"€", "GBP":"£", "SEK":"kr", "CHF":"CHF"}

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://bupqagkrcvrezjkdbald.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")  # service_role
if not SUPABASE_KEY:
    sys.exit("SUPABASE_KEY env var required (service_role)")

# ── derive sku_id from dealer + URL (stable across runs) ──
def make_sku_id(dealer: str, url: str) -> str:
    if dealer == "ssense":
        m = re.search(r'/(\d{6,})$', url or "")
        if m: return f"ssense:{m.group(1)}"
    elif dealer == "mec":
        m = re.search(r'/product/([0-9-]+)/', url or "")
        if m: return f"mec:{m.group(1)}"
    elif dealer == "evo":
        # EVO 把同一商品挂多个分类，URL 末段会重复（shell-jackets/sabre vs
        # insulated-jackets/sabre），用整段 path 才能保证唯一
        m = re.search(r'evo\.com(/[a-z0-9/-]+)$', url or "")
        if m: return f"evo:{m.group(1).strip('/')}"
    elif dealer == "rei":
        m = re.search(r'/product/(\d+)/', url or "")
        if m: return f"rei:{m.group(1)}"
    # fallback hash
    return f"{dealer}:" + hashlib.sha1((url or "").encode()).hexdigest()[:12]

def _infer_cat(name: str, url: str) -> str:
    """Dealer 行也归类, 避免 100% 都是 '其他'。复用 outlet 的逻辑。"""
    try:
        from supabase_sync import infer_category   # parent module
        return infer_category(name, url)
    except Exception:
        return ""

def item_to_row(it: dict, dealer: str, generated_at: str) -> dict:
    name = it.get("name") or ""
    url = it.get("url","")
    sku_id = make_sku_id(dealer, url)
    return {
        "sku_id":         sku_id,
        "dealer":         dealer,
        "model":          name,
        "full_name":      name,
        "color":          it.get("color") or "",
        "sizes":          it.get("sizes") or [],
        "size_stock":     it.get("size_stock") or {},
        "original_price": it.get("original_price"),
        "sale_price":     it.get("sale_price"),
        "discount_pct":   it.get("discount_pct") or 0,
        "currency":       it.get("currency") or "USD",
        "symbol":         SYM.get(it.get("currency",""), "$"),
        "gender":         it.get("gender") or "unknown",
        "region":         (it.get("region") or "us").lower(),
        "region_name":    "",
        "category":       _infer_cat(name, url),
        "url":            url,
        "image_url":      it.get("image"),
        "images":         [it["image"]] if it.get("image") else [],
        "description":    "",
        "last_updated":   _to_iso(generated_at),
    }

def _to_iso(s: str) -> str | None:
    if not s: return None
    try:
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception:
        return None

def main():
    if not RESULTS_FILE.exists():
        sys.exit(f"{RESULTS_FILE} not found — run scrapers + merge_partial first")
    js = json.loads(RESULTS_FILE.read_text())
    dealers = js.get("dealers", {})
    generated_at = js.get("generated_at", "")

    from supabase import create_client
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    grand_total = 0
    for dkey, info in dealers.items():
        items = info.get("items", []) or []
        rows = [item_to_row(it, dkey, generated_at) for it in items]
        rows = [r for r in rows if r["sku_id"] and r["url"]]
        print(f"\n[sync:{dkey}] {len(rows)} rows to upsert")

        # ── 加载已有 first_seen，再注入到本轮 row，避免 delete+re-insert 刷新它
        first_seen_map = {}
        try:
            page = 0
            while True:
                res = client.table("products").select("sku_id,first_seen") \
                    .eq("dealer", dkey).range(page*1000, page*1000+999).execute()
                data = res.data or []
                for r in data:
                    if r.get("first_seen"):
                        first_seen_map[r["sku_id"]] = r["first_seen"]
                if len(data) < 1000: break
                page += 1
        except Exception:
            pass
        for r in rows:
            if r["sku_id"] in first_seen_map:
                r["first_seen"] = first_seen_map[r["sku_id"]]

        # ── upsert in batches
        ok, err = 0, 0
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i+BATCH_SIZE]
            try:
                client.table("products").upsert(batch, on_conflict="sku_id").execute()
                ok += len(batch)
            except Exception as e:
                err += 1
                print(f"  ERR batch {i//BATCH_SIZE+1}: {str(e)[:200]}", file=sys.stderr)
        print(f"[sync:{dkey}] upserted {ok}/{len(rows)} ({err} batch errors)")
        grand_total += ok

        # ── delete stale rows that are no longer in current scrape (scoped to this dealer)
        # 但：如果本轮抓到 0 件，几乎肯定是抓取失败而不是该 dealer 真的没货，
        # 跳过清理避免把 Supabase 里现存的几十~上百件全删光
        if not rows:
            print(f"[sync:{dkey}] 0 rows in scrape — skipping stale cleanup (likely scrape failure)")
            continue
        try:
            synced_ids = {r["sku_id"] for r in rows}
            existing = []
            page = 0
            while True:
                res = client.table("products").select("sku_id") \
                    .eq("dealer", dkey).range(page*1000, page*1000+999).execute()
                data = res.data or []
                existing.extend(r["sku_id"] for r in data)
                if len(data) < 1000: break
                page += 1
            stale = [s for s in existing if s not in synced_ids]
            print(f"[sync:{dkey}] existing={len(existing)} stale={len(stale)}")
            if stale:
                # batch delete
                for i in range(0, len(stale), 100):
                    client.table("products").delete().in_("sku_id", stale[i:i+100]).execute()
                print(f"[sync:{dkey}] deleted {len(stale)} stale rows")
        except Exception as e:
            print(f"[sync:{dkey}] stale-cleanup err: {str(e)[:200]}", file=sys.stderr)

    print(f"\n=== DEALERS SYNC DONE — {grand_total} rows total ===")

if __name__ == "__main__":
    main()
