#!/usr/bin/env python3
"""
supabase_sync.py
────────────────
Reads arcteryx_skus.json → upserts all records into Supabase `products` table.
Uses service_role key (bypasses RLS) for write access.

Usage:
    python3 supabase_sync.py                    # sync all
    python3 supabase_sync.py --dry-run          # print first 3 records, no upload
    SUPABASE_URL=... SUPABASE_KEY=... python3 supabase_sync.py
"""

import json
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://bupqagkrcvrezjkdbald.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ1cHFhZ2tyY3ZyZXpqa2RiYWxkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjQ0NTU1MywiZXhwIjoyMDkyMDIxNTUzfQ.QPg4iHNEix_uB1Dlo6ONz2fBq59XhV9NZdEIsXc95_k")

BASE_DIR  = Path(__file__).parent
SKUS_FILE = BASE_DIR / "arcteryx_skus.json"

BATCH_SIZE = 50   # upsert N rows at a time

# ── Category inference (re-run on every sync so old "其他" rows get backfilled) ──
def infer_category(name: str, url: str) -> str:
    u = (url or "").lower()
    n = (name or "").lower()
    if "veilance" in u or "veilance" in n: return "Veilance商务系列"
    if any(x in u for x in ["shell-jacket", "hardshell", "softshell"]): return "硬壳冲锋衣"
    if any(x in u for x in ["insulated", "down-jacket", "down-coat", "hoody", "atom", "cerium", "proton", "nuclei", "thorium"]): return "保暖夹克"
    if any(x in u for x in ["/pant", "-pant", "bib-", "short-"]): return "裤装"
    if any(x in u for x in ["shoe", "boot", "footwear", "sandal"]): return "鞋类"
    if any(x in u for x in ["/pack", "-pack", "backpack", "bag", "tote", "sling"]): return "背包"
    if any(x in u for x in ["base-layer", "rho-", "-rho", "phase-", "merino"]): return "排汗内衣"
    if any(x in u for x in ["fleece", "polar", "fortrez", "kyanite", "covert"]): return "抓绒/摇粒绒"
    if any(x in u for x in ["vest", "gilet"]): return "背心"
    if any(x in u for x in ["jacket", "-coat", "anorak", "parka"]): return "夹克/外套"
    if any(x in u for x in ["blazer"]): return "西装/西服"
    if any(x in u for x in ["shirt", "polo", "tee", "top-"]): return "上衣/T恤"
    if any(x in u for x in ["dress", "skirt"]): return "裙装"
    if any(x in u for x in ["hat", "cap", "headwear", "glove", "sock", "buff", "toque", "beanie"]): return "配件"
    return "其他"

# ── Junk color guard ──────────────────────────────────────────────────────────
def is_junk_color(color: str) -> bool:
    import re
    c = (color or "").strip()
    if not c or c.lower() in ("unknown", "default"):
        return True
    if re.match(r"^size\d+$", c, re.IGNORECASE):
        return True
    return False

# ── Row builder ───────────────────────────────────────────────────────────────
def sku_to_row(sku: dict) -> dict:
    """Convert a SKU dict (arcteryx_skus.json format) → Supabase row dict."""
    # Parse last_updated string → ISO timestamp
    lu_str = sku.get("last_updated", "")
    try:
        lu_dt = datetime.strptime(lu_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        lu_iso = lu_dt.isoformat()
    except Exception:
        lu_iso = None

    return {
        "sku_id":         sku.get("sku_id", ""),
        "dealer":         "arcteryx_outlet",   # 区分 outlet vs 各经销商
        "model":          sku.get("model"),
        "full_name":      sku.get("full_name"),
        "color":          sku.get("color"),
        "sizes":          sku.get("sizes", []),
        "size_stock":     sku.get("size_stock", {}),
        "original_price": sku.get("original_price"),
        "sale_price":     sku.get("sale_price"),
        "discount_pct":   sku.get("discount_pct"),
        "currency":       sku.get("currency"),
        "symbol":         sku.get("symbol"),
        "gender":         sku.get("gender"),
        "region":         sku.get("region"),
        "region_name":    sku.get("region_name"),
        # Always re-infer category so old "其他" rows get reclassified when sync runs.
        # If the scraper already picked a non-"其他" category, keep it.
        "category":       (sku.get("category") if sku.get("category") and sku.get("category") != "其他"
                           else infer_category(sku.get("full_name"), sku.get("url"))),
        "url":            sku.get("url"),
        "image_url":      sku.get("image_url"),
        "images":         sku.get("images", []),
        "description":    sku.get("description", ""),
        "last_updated":   lu_iso,
    }

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print sample rows, no upload")
    args = parser.parse_args()

    if not SKUS_FILE.exists():
        print(f"[ERROR] {SKUS_FILE} not found", file=sys.stderr)
        sys.exit(1)

    skus = json.loads(SKUS_FILE.read_text())
    rows = [sku_to_row(s) for s in skus if not is_junk_color(s.get("color", ""))]
    print(f"[sync] {len(skus)} SKUs loaded → {len(rows)} valid rows")

    if args.dry_run:
        import pprint
        pprint.pprint(rows[:3])
        print("[dry-run] done, nothing uploaded")
        return

    if SUPABASE_URL == "YOUR_SUPABASE_URL":
        print("[ERROR] Set SUPABASE_URL and SUPABASE_KEY env vars (or edit this file)", file=sys.stderr)
        sys.exit(1)

    from supabase import create_client
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # ── Snapshot existing prices BEFORE upsert, so we can diff & log changes
    old_prices = {}   # sku_id -> (original_price, sale_price)
    try:
        page = 0
        while True:
            res = client.table("products").select(
                "sku_id,original_price,sale_price"
            ).range(page * 1000, page * 1000 + 999).execute()
            data = res.data or []
            if not data:
                break
            for r in data:
                old_prices[r["sku_id"]] = (r.get("original_price"), r.get("sale_price"))
            if len(data) < 1000:
                break
            page += 1
        print(f"[sync] loaded {len(old_prices)} existing price snapshots")
    except Exception as e:
        print(f"[WARN] could not preload prices (price_history may be incomplete): {e}", file=sys.stderr)

    total, errors = 0, 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        try:
            res = client.table("products").upsert(
                batch,
                on_conflict="sku_id"
            ).execute()
            total += len(batch)
            print(f"[sync] upserted rows {i+1}–{i+len(batch)} ({total}/{len(rows)})")
        except Exception as e:
            errors += 1
            print(f"[ERROR] batch {i//BATCH_SIZE + 1}: {e}", file=sys.stderr)

    print(f"\n[sync] DONE — {total} upserted, {errors} batch errors")

    # ── Price history (append-only) ───────────────────────────────────────
    # Record a snapshot for every SKU whose price changed vs. last run, plus
    # brand-new SKUs. Preserved forever so we can chart price trends even
    # after the product is removed from the current products table.
    history_rows = []
    for r in rows:
        sid = r.get("sku_id")
        if not sid:
            continue
        new_op, new_sp = r.get("original_price"), r.get("sale_price")
        if new_sp is None:
            continue
        old = old_prices.get(sid)
        if old is None or old != (new_op, new_sp):
            history_rows.append({
                "sku_id":         sid,
                "original_price": new_op,
                "sale_price":     new_sp,
                "discount_pct":   r.get("discount_pct"),
                "currency":       r.get("currency"),
                "recorded_at":    r.get("last_updated"),
            })
    print(f"[sync] price_history: {len(history_rows)} changes to log")
    hist_inserted = 0
    for i in range(0, len(history_rows), BATCH_SIZE):
        batch = history_rows[i : i + BATCH_SIZE]
        try:
            client.table("price_history").insert(batch).execute()
            hist_inserted += len(batch)
        except Exception as e:
            print(f"[ERROR] price_history batch {i//BATCH_SIZE + 1}: {e}", file=sys.stderr)
    print(f"[sync] price_history: inserted {hist_inserted}")

    # ── Stale-row cleanup (unconditional) ─────────────────────────────────
    # The scrape (sku_scraper --reset) is a full re-crawl, so arcteryx_skus.json
    # IS the source of truth. Any row in Supabase not present here = product
    # went out of stock, was removed from outlet, or is a leftover from old
    # schema. On a deals site, showing expired/stale data is worse than
    # temporarily missing a product — upsert batch errors will be re-healed
    # on the next cron run (6h later) anyway.
    synced_ids = {r["sku_id"] for r in rows if r.get("sku_id")}
    if synced_ids:
        try:
            existing = []
            page = 0
            # 只选 outlet 的行（dealer='arcteryx_outlet' 或旧数据 NULL）
            # 避免把 dealer 经销商的行（ssense:/mec:/evo:/rei:）误删
            while True:
                res = client.table("products").select("sku_id,dealer").or_(
                    "dealer.is.null,dealer.eq.arcteryx_outlet"
                ).range(page * 1000, page * 1000 + 999).execute()
                data = res.data or []
                if not data:
                    break
                existing.extend(r["sku_id"] for r in data)
                if len(data) < 1000:
                    break
                page += 1

            stale = [sid for sid in existing if sid not in synced_ids]
            print(f"[sync] stale outlet rows to delete: {len(stale)} (existing={len(existing)}, synced={len(synced_ids)})")

            deleted = 0
            for i in range(0, len(stale), BATCH_SIZE):
                batch = stale[i : i + BATCH_SIZE]
                try:
                    client.table("products").delete().in_("sku_id", batch).execute()
                    deleted += len(batch)
                except Exception as e:
                    print(f"[ERROR] delete batch {i//BATCH_SIZE + 1}: {e}", file=sys.stderr)
            print(f"[sync] deleted {deleted} stale rows")
        except Exception as e:
            print(f"[WARN] stale cleanup failed: {e}", file=sys.stderr)
    else:
        print("[sync] no synced rows — skipping cleanup to avoid wiping table")

    # Also write a minimal last-sync marker
    marker = BASE_DIR / ".last_sync"
    marker.write_text(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    main()
