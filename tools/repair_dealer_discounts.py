#!/usr/bin/env python3
"""Repair derived dealer discount_pct values in production Supabase."""
from __future__ import annotations

import argparse
import os
import sys
from typing import Any

import requests

SELECT = "sku_id,dealer,original_price,sale_price,discount_pct"
DEFAULT_DEALERS = ("mec", "evo", "rei", "ssense")


def num(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def calc_discount(original: Any, sale: Any) -> int:
    o = num(original)
    s = num(sale)
    if o is None or s is None or o <= 0 or s <= 0 or s > o:
        return 0
    return round((1 - s / o) * 100)


def needs_repair(row: dict) -> tuple[bool, int]:
    expected = calc_discount(row.get("original_price"), row.get("sale_price"))
    try:
        actual = int(row.get("discount_pct"))
    except (TypeError, ValueError):
        return True, expected
    return abs(actual - expected) > 1, expected


def load_rows(base_url: str, headers: dict, dealers: list[str]) -> list[dict]:
    rows: list[dict] = []
    page_size = 1000
    dealer_filter = "in.(" + ",".join(dealers) + ")"
    for offset in range(0, 60000, page_size):
        response = requests.get(
            f"{base_url}/rest/v1/products",
            params={"select": SELECT, "dealer": dealer_filter, "order": "sku_id.asc"},
            headers={**headers, "Range": f"{offset}-{offset + page_size - 1}"},
            timeout=45,
        )
        response.raise_for_status()
        data = response.json()
        rows.extend(data)
        if len(data) < page_size:
            break
    return rows


def patch_discount(base_url: str, headers: dict, sku_id: str, discount_pct: int) -> None:
    response = requests.patch(
        f"{base_url}/rest/v1/products",
        params={"sku_id": f"eq.{sku_id}"},
        headers={**headers, "Content-Type": "application/json", "Prefer": "return=minimal"},
        json={"discount_pct": discount_pct},
        timeout=45,
    )
    response.raise_for_status()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dealer", action="append", default=[], help="Dealer key to repair")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    base_url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not base_url or not key:
        raise SystemExit("SUPABASE_URL and SUPABASE_KEY are required")

    dealers = args.dealer or list(DEFAULT_DEALERS)
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json"}
    rows = load_rows(base_url.rstrip("/"), headers, dealers)

    repairs: list[tuple[dict, int]] = []
    for row in rows:
        repair, expected = needs_repair(row)
        if repair:
            repairs.append((row, expected))

    print(f"[repair-discounts] rows={len(rows)} mismatches={len(repairs)}")
    for row, expected in repairs[:20]:
        print(
            "[repair-discounts] "
            f"{row.get('sku_id')} dealer={row.get('dealer')} "
            f"discount_pct={row.get('discount_pct')} expected={expected} "
            f"original={row.get('original_price')} sale={row.get('sale_price')}"
        )

    if args.dry_run:
        return 1 if repairs else 0

    failed = 0
    for row, expected in repairs:
        try:
            patch_discount(base_url.rstrip("/"), headers, row["sku_id"], expected)
        except Exception as exc:
            failed += 1
            print(f"[repair-discounts] update failed {row.get('sku_id')}: {exc}", file=sys.stderr)

    print(f"[repair-discounts] repaired={len(repairs) - failed} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
