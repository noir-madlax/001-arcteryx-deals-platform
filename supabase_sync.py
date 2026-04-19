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
SUPABASE_URL = os.environ.get("SUPABASE_URL", "YOUR_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "YOUR_SUPABASE_SERVICE_ROLE_KEY")

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

    # Also write a minimal last-sync marker
    marker = BASE_DIR / ".last_sync"
    marker.write_text(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    main()
