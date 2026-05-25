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
REGION_NAME = {
    "us":"美国","ca":"加拿大","gb":"英国","de":"德国","fr":"法国","nl":"荷兰",
    "at":"奥地利","ch":"瑞士","it":"意大利","es":"西班牙","be":"比利时",
    "dk":"丹麦","se":"瑞典","no":"挪威","fi":"芬兰","ie":"爱尔兰","pl":"波兰",
    "jp":"日本","au":"澳大利亚","nz":"新西兰","kr":"韩国","hk":"香港",
}

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
        "region_name":    REGION_NAME.get((it.get("region") or "us").lower(), ""),
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

        # ── 加载已有 first_seen + sizes + size_stock + color，
        # 后续注入: first_seen 始终注入(防 stale-reset);
        # sizes/size_stock/color 仅当本轮抓到空时保留DB老值(防 detail enrichment 临时失败导致数据丢失)
        existing_map = {}
        try:
            page = 0
            while True:
                res = client.table("products").select(
                    "sku_id,first_seen,sizes,size_stock,color"
                ).eq("dealer", dkey).range(page*1000, page*1000+999).execute()
                data = res.data or []
                for r in data:
                    existing_map[r["sku_id"]] = r
                if len(data) < 1000: break
                page += 1
        except Exception:
            pass
        from datetime import datetime as _dt, timezone as _tz
        now_iso = _dt.now(_tz.utc).isoformat()
        for r in rows:
            old = existing_map.get(r["sku_id"])
            if old:
                # 存在: 保留 first_seen (若 DB 老值为空则补今天)
                r["first_seen"] = old.get("first_seen") or now_iso
                # 保留非空 detail enrichment 数据
                if not r.get("sizes") and old.get("sizes"):
                    r["sizes"] = old["sizes"]
                    r["size_stock"] = old.get("size_stock") or {}
                if not (r.get("color") or "").strip() and (old.get("color") or "").strip():
                    r["color"] = old["color"]
            else:
                # 真新 SKU: 显式设今天 (避免 PostgREST batch upsert 字段不齐 → NULL)
                r["first_seen"] = now_iso

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
            from datetime import datetime, timezone, timedelta
            stale_cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
            synced_ids = {r["sku_id"] for r in rows}
            existing = []   # (sku_id, last_updated)
            page = 0
            while True:
                res = client.table("products").select("sku_id,last_updated") \
                    .eq("dealer", dkey).range(page*1000, page*1000+999).execute()
                data = res.data or []
                existing.extend((r["sku_id"], r.get("last_updated")) for r in data)
                if len(data) < 1000: break
                page += 1
            # 同 outlet: 只删 14 天没刷新过的过期行, 给单次抓取波动留缓冲
            stale = [sid for sid, lu in existing
                     if sid not in synced_ids and (lu is None or lu < stale_cutoff)]
            preserve = sum(1 for sid, lu in existing
                           if sid not in synced_ids and lu and lu >= stale_cutoff)
            print(f"[sync:{dkey}] existing={len(existing)} stale={len(stale)} preserve_recent={preserve}")
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
