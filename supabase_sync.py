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
import re
from datetime import datetime, timezone
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://bupqagkrcvrezjkdbald.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

BASE_DIR  = Path(__file__).parent
SKUS_FILE = BASE_DIR / "arcteryx_skus.json"
SKIPPED_REGIONS_FILE = BASE_DIR / ".skipped_regions.json"

BATCH_SIZE = 50   # upsert N rows at a time

def load_skipped_regions() -> set[str]:
    if not SKIPPED_REGIONS_FILE.exists():
        return set()
    try:
        raw = json.loads(SKIPPED_REGIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return set()
    return {
        str(item.get("region", "")).lower()
        for item in raw
        if isinstance(item, dict) and item.get("region")
    }

# ── Category inference (re-run on every sync so old "其他" rows get backfilled) ──
def infer_category(name: str, url: str) -> str:
    u = (url or "").lower()
    n = (name or "").lower()
    hay = u + " " + n
    if "veilance" in hay: return "Veilance商务系列"
    if any(x in hay for x in ["shell-jacket", "hardshell", "softshell"]): return "硬壳冲锋衣"
    if any(x in hay for x in ["insulated", "down-jacket", "down-coat", "atom", "cerium", "proton", "nuclei", "thorium", "macai", "andessa", "decca", "therme", "sorin"]): return "保暖夹克"
    # 抓绒/卫衣 — 先于通用 hoodie/jacket 匹配, 因为 hoodie 多数是 fleece/midlayer
    if any(x in hay for x in ["fleece", "polar", "fortrez", "kyanite", "covert", "delta", "rho-", "-rho", "rho ",
                              "hoody", "hoodie", "pullover", "crew", " 1/2 zip", "1-2-zip", "midlayer", "mid-layer",
                              "cardigan", "sweater"]): return "抓绒/摇粒绒"
    if any(x in hay for x in ["pants", "pant ", "-pant", "/pant", "bibs", "bib-", "bib ", "shorts", "short-",
                              "jogger", "legging", "tights"]): return "裤装"
    if any(x in hay for x in ["shoe", "boot", "footwear", "sandal", "sneaker"]): return "鞋类"
    if any(x in hay for x in ["/pack", "-pack ", "-pack-", "backpack", "tote", "sling", "waistpack",
                              "hip-pack", "duffel", "/bag", "-bag"]): return "背包"
    if any(x in hay for x in ["base-layer", "baselayer", "phase-", "merino", "rho-lt", "boxer", "brief"]): return "排汗内衣"
    if any(x in hay for x in ["vest", "gilet"]): return "背心"
    if any(x in hay for x in ["jacket", "anorak", "parka", "-coat", " coat"]): return "夹克/外套"
    if any(x in hay for x in ["blazer"]): return "西装/西服"
    if any(x in hay for x in ["shirt", "polo", "tee", "top-", "tank", "t-shirt", "/top "]): return "上衣/T恤"
    if any(x in hay for x in ["dress", "skirt"]): return "裙装"
    if any(x in hay for x in ["hat", " cap", "-cap", "headwear", "glove", "mitten", "mitt-", "sock",
                              "buff", "toque", "beanie", "headband", "scarf"]): return "配件"
    return "其他"

# ── Junk color guard ──────────────────────────────────────────────────────────
def is_junk_color(color: str) -> bool:
    c = (color or "").strip()
    if not c or c.lower() in ("unknown", "default"):
        return True
    if re.match(r"^size\d+$", c, re.IGNORECASE):
        return True
    return False

def calc_discount(original_price, sale_price) -> int:
    """Return an internally consistent integer discount percentage."""
    try:
        orig = float(original_price or 0)
        sale = float(sale_price or 0)
    except (TypeError, ValueError):
        return 0
    if orig <= 0 or sale <= 0 or sale > orig:
        return 0
    return round((1 - sale / orig) * 100)

def gender_from_url(url: str) -> str | None:
    u = (url or "").lower()
    if re.search(r"/womens?/", u):
        return "women"
    if re.search(r"/mens?/", u):
        return "men"
    return None

def is_blocked_outlet_url(url: str) -> bool:
    """True for known bad Arc'teryx Outlet PDP links that should not be shown."""
    u = (url or "").split("?", 1)[0].rstrip("/").lower()
    return bool(re.search(r"outlet\.arcteryx\.com/(?:[a-z]{2}/[a-z]{2}/)?shop/womens/rush-bib-pant$", u))

def _jsonish(value, default):
    if value is None or value == "":
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default

def all_sizes_out_of_stock(item: dict) -> bool:
    sizes = _jsonish(item.get("sizes"), [])
    stock = _jsonish(item.get("size_stock"), {})
    if not isinstance(stock, dict):
        return False
    keys = sizes if isinstance(sizes, list) and sizes else list(stock.keys())
    if not keys:
        return False
    return all(stock.get(str(size)) == "out_of_stock" for size in keys)

def _replace_gender_marker(text: str | None, gender: str | None) -> str | None:
    if not text or gender not in ("men", "women"):
        return text
    if gender == "women":
        return re.sub(r"(?<!Wo)Men'?s", "Women's", text, flags=re.IGNORECASE)
    return re.sub(r"Women'?s", "Men's", text, flags=re.IGNORECASE)

def normalize_outlet_sku(sku: dict) -> dict:
    """Normalize fields that should be determined by authoritative URL/price data."""
    out = dict(sku)
    url_gender = gender_from_url(out.get("url", ""))
    if url_gender:
        out["gender"] = url_gender
        out["full_name"] = _replace_gender_marker(out.get("full_name"), url_gender)
        out["model"] = _replace_gender_marker(out.get("model"), url_gender)
    out["discount_pct"] = calc_discount(out.get("original_price"), out.get("sale_price"))
    return out

# ── Row builder ───────────────────────────────────────────────────────────────
def sku_to_row(sku: dict) -> dict:
    """Convert a SKU dict (arcteryx_skus.json format) → Supabase row dict."""
    sku = normalize_outlet_sku(sku)
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
    blocked_sku_ids = [
        s.get("sku_id")
        for s in skus
        if s.get("sku_id") and (is_blocked_outlet_url(s.get("url", "")) or all_sizes_out_of_stock(s))
    ]
    rows = [
        sku_to_row(s)
        for s in skus
        if (
            not is_junk_color(s.get("color", ""))
            and not is_blocked_outlet_url(s.get("url", ""))
            and not all_sizes_out_of_stock(s)
        )
    ]
    print(f"[sync] {len(skus)} SKUs loaded → {len(rows)} valid rows")
    if blocked_sku_ids:
        print(f"[sync] blocked known-bad outlet rows: {len(blocked_sku_ids)}")

    # ── 数据完整性 guard: 拒绝 sale > orig 的行（scraper bug, 不写入 DB）
    bad = []
    for r in rows:
        o = r.get("original_price") or 0
        s = r.get("sale_price") or 0
        if o > 0 and s > 0 and s > o:
            bad.append(r)
    if bad:
        print(f"[sync] 拒绝 {len(bad)} 行 sale>orig (scraper bug, 详情见 stderr)")
        for r in bad[:8]:
            print(f"   ✗ {r['sku_id']} orig=${r.get('original_price')} sale=${r.get('sale_price')}", file=sys.stderr)
        rows = [r for r in rows if r not in bad]

    if args.dry_run:
        import pprint
        pprint.pprint(rows[:3])
        print("[dry-run] done, nothing uploaded")
        return

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[ERROR] Set SUPABASE_URL and SUPABASE_KEY env vars", file=sys.stderr)
        sys.exit(1)

    from supabase import create_client
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    try:
        existing_blocked = []
        page = 0
        while True:
            res = client.table("products").select("sku_id,url,dealer,sizes,size_stock").or_(
                "dealer.is.null,dealer.eq.arcteryx_outlet"
            ).range(
                page * 1000, page * 1000 + 999
            ).execute()
            data = res.data or []
            existing_blocked.extend(
                r["sku_id"]
                for r in data
                if r.get("sku_id") and (is_blocked_outlet_url(r.get("url", "")) or all_sizes_out_of_stock(r))
            )
            if len(data) < 1000:
                break
            page += 1
        blocked_delete_ids = sorted(set(blocked_sku_ids) | set(existing_blocked))
    except Exception as e:
        print(f"[WARN] could not load existing blocked rows: {e}", file=sys.stderr)
        blocked_delete_ids = sorted(set(blocked_sku_ids))

    if blocked_delete_ids:
        deleted_blocked = 0
        for i in range(0, len(blocked_delete_ids), BATCH_SIZE):
            batch = blocked_delete_ids[i : i + BATCH_SIZE]
            try:
                client.table("products").delete().in_("sku_id", batch).execute()
                deleted_blocked += len(batch)
            except Exception as e:
                print(f"[ERROR] blocked delete batch {i//BATCH_SIZE + 1}: {e}", file=sys.stderr)
        print(f"[sync] deleted {deleted_blocked} blocked rows")

    # ── Snapshot existing prices + first_seen BEFORE upsert
    # 关键: 把已有行的 first_seen 也加载，upsert 时塞回 row 里，
    # 否则下面的 stale-delete + 下轮 re-insert 会让 first_seen 被 DB DEFAULT now() 刷新，
    # 导致"今日上新"弹窗一炸 N 千件
    old_prices = {}     # sku_id -> (original_price, sale_price)
    first_seen_map = {} # sku_id -> first_seen (ISO str)
    try:
        page = 0
        while True:
            res = client.table("products").select(
                "sku_id,original_price,sale_price,first_seen"
            ).or_("dealer.is.null,dealer.eq.arcteryx_outlet") \
             .range(page * 1000, page * 1000 + 999).execute()
            data = res.data or []
            if not data:
                break
            for r in data:
                old_prices[r["sku_id"]] = (r.get("original_price"), r.get("sale_price"))
                if r.get("first_seen"):
                    first_seen_map[r["sku_id"]] = r["first_seen"]
            if len(data) < 1000:
                break
            page += 1
        print(f"[sync] loaded {len(old_prices)} existing rows ({len(first_seen_map)} with first_seen)")
    except Exception as e:
        print(f"[WARN] could not preload prices: {e}", file=sys.stderr)

    # 给每行注入 first_seen
    # 关键: 必须显式写, 不能依赖 DB DEFAULT now()
    # 因为 PostgREST 批量 upsert 时, 若 batch 内其他行有 first_seen 字段,
    # 没字段的行 INSERT 时填 NULL 而非触发 DEFAULT (PostgREST 把 batch 各 row 字段并集当列集)
    now_iso = datetime.now(timezone.utc).isoformat()
    for r in rows:
        sid = r.get("sku_id")
        if sid and sid in first_seen_map:
            r["first_seen"] = first_seen_map[sid]   # 已存在: 保留原值
        else:
            r["first_seen"] = now_iso                # 真新 SKU: 显式设今天

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

    # ── Stale-row cleanup (only if last_updated > 14 天) ──────────────────
    # 改:  原本"不在本次 scrape 里"立即删, 导致单次抓取失败的商品被删, 下次又被
    # 当新品 re-insert, 刷新 first_seen 弹窗误报. 现在需要 last_updated 老于
    # 14 天才删, 给抓取波动留缓冲, 真正下架 / 缺货长期不在的商品 14 天后才清掉
    from datetime import timedelta
    STALE_AFTER_DAYS = 14
    stale_cutoff = (datetime.now(timezone.utc) - timedelta(days=STALE_AFTER_DAYS)).isoformat()
    synced_ids = {r["sku_id"] for r in rows if r.get("sku_id")}
    skipped_regions = load_skipped_regions()
    if synced_ids:
        try:
            existing = []  # 待删候选: (sku_id, last_updated, region)
            page = 0
            while True:
                res = client.table("products").select("sku_id,dealer,last_updated,region").or_(
                    "dealer.is.null,dealer.eq.arcteryx_outlet"
                ).range(page * 1000, page * 1000 + 999).execute()
                data = res.data or []
                if not data:
                    break
                # 保留 (sku_id, last_updated, region) 三元组
                existing.extend((r["sku_id"], r.get("last_updated"), (r.get("region") or "").lower()) for r in data)
                if len(data) < 1000:
                    break
                page += 1

            # 满足两个条件才标 stale: (1) 不在本次 scrape (2) last_updated 老于 cutoff
            stale = [sid for sid, lu, _region in existing
                     if sid not in synced_ids and (lu is None or lu < stale_cutoff)]
            forced_region_delete = [
                sid for sid, _lu, region in existing
                if sid not in synced_ids and region in skipped_regions
            ]
            delete_ids = sorted(set(stale) | set(forced_region_delete))
            preserve = sum(1 for sid, lu, region in existing
                           if sid not in synced_ids and lu and lu >= stale_cutoff and region not in skipped_regions)
            print(
                "[sync] stale outlet rows to delete: "
                f"{len(delete_ids)} (existing={len(existing)}, synced={len(synced_ids)}, "
                f"preserve_recent={preserve}, redirected_region={len(forced_region_delete)})"
            )

            deleted = 0
            for i in range(0, len(delete_ids), BATCH_SIZE):
                batch = delete_ids[i : i + BATCH_SIZE]
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
