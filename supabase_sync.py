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
        "category":       sku.get("category"),
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

    # ── Stale-row cleanup ─────────────────────────────────────────────────
    # Delete any row in Supabase whose sku_id is NOT in this scrape. This
    # garbage-collects products that went out of stock / were removed from
    # the outlet, and also cleans up rows left over from old sku_id schemas.
    # Only runs if the upsert phase was mostly successful.
    if errors == 0 and total > 0:
        synced_ids = {r["sku_id"] for r in rows if r.get("sku_id")}
        try:
            # Fetch all existing sku_ids (paginated; PostgREST caps at 1000/page)
            existing = []
            page = 0
            while True:
                res = client.table("products").select("sku_id").range(
                    page * 1000, page * 1000 + 999
                ).execute()
                data = res.data or []
                if not data:
                    break
                existing.extend(r["sku_id"] for r in data)
                if len(data) < 1000:
                    break
                page += 1

            stale = [sid for sid in existing if sid not in synced_ids]
            print(f"[sync] stale rows to delete: {len(stale)} (existing={len(existing)}, synced={len(synced_ids)})")

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
            print(f"[WARN] stale cleanup skipped: {e}", file=sys.stderr)
    else:
        print("[sync] skipping stale-row cleanup (upsert had errors or produced 0 rows)")

    # Also write a minimal last-sync marker
    marker = BASE_DIR / ".last_sync"
    marker.write_text(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    main()
