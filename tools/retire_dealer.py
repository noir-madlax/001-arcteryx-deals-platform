#!/usr/bin/env python3
"""Retire configured dealer rows without deleting production history.

This is the formal source-retirement path. It only accepts dealer keys listed
in ``dealers.source_registry.RETIRED_DEALERS``, marks every matching product
inactive, and performs an independent readback before succeeding.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from collections import Counter
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dealers.source_registry import RETIRED_DEALERS  # noqa: E402


PAGE_SIZE = 1000
SELECT = "sku_id,status,missing_runs"


def request_with_retry(
    session: requests.Session,
    method: str,
    url: str,
    *,
    attempts: int = 3,
    **kwargs,
) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = session.request(method, url, timeout=45, **kwargs)
            if response.status_code == 429 or response.status_code >= 500:
                response.raise_for_status()
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(2**attempt)
    raise RuntimeError(
        f"retirement request failed after {attempts} attempts: "
        f"{type(last_error).__name__ if last_error else 'unknown'}"
    ) from last_error


def load_dealer_rows(
    session: requests.Session,
    base_url: str,
    headers: dict[str, str],
    dealer: str,
) -> list[dict]:
    rows: list[dict] = []
    for offset in range(0, 60000, PAGE_SIZE):
        response = request_with_retry(
            session,
            "GET",
            f"{base_url}/rest/v1/products",
            params={
                "select": SELECT,
                "dealer": f"eq.{dealer}",
                "order": "sku_id.asc",
            },
            headers={**headers, "Range": f"{offset}-{offset + PAGE_SIZE - 1}"},
        )
        batch = response.json()
        if not isinstance(batch, list):
            raise RuntimeError("retirement readback was not a JSON array")
        rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
    return rows


def retire_dealer(
    session: requests.Session,
    base_url: str,
    headers: dict[str, str],
    dealer: str,
    *,
    dry_run: bool = False,
) -> dict[str, int]:
    before = load_dealer_rows(session, base_url, headers, dealer)
    before_counts = Counter(str(row.get("status") or "active") for row in before)
    noninactive = sum(count for status, count in before_counts.items() if status != "inactive")
    print(
        f"[retire] dealer={dealer} total={len(before)} "
        f"noninactive={noninactive} before={dict(sorted(before_counts.items()))}",
        flush=True,
    )

    if dry_run:
        return dict(before_counts)

    if noninactive:
        request_with_retry(
            session,
            "PATCH",
            f"{base_url}/rest/v1/products",
            params={"dealer": f"eq.{dealer}"},
            headers={
                **headers,
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json={"status": "inactive", "missing_runs": 2},
        )

    after = load_dealer_rows(session, base_url, headers, dealer)
    after_counts = Counter(str(row.get("status") or "active") for row in after)
    remaining = [row for row in after if (row.get("status") or "active") != "inactive"]
    print(
        f"[retire] dealer={dealer} readback={dict(sorted(after_counts.items()))} "
        f"remaining_noninactive={len(remaining)}",
        flush=True,
    )
    if remaining:
        sample = ", ".join(str(row.get("sku_id")) for row in remaining[:10])
        raise RuntimeError(
            f"retirement readback failed for {dealer}: "
            f"{len(remaining)} noninactive row(s), sample={sample}"
        )
    return dict(after_counts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dealer", action="append", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    requested = {str(dealer).strip().lower() for dealer in args.dealer if str(dealer).strip()}
    unsupported = sorted(requested - RETIRED_DEALERS)
    if unsupported:
        raise SystemExit(
            "refusing to retire dealer(s) not configured as retired: "
            + ", ".join(unsupported)
        )

    base_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_KEY", "")
    if not base_url or not key:
        raise SystemExit("SUPABASE_URL and SUPABASE_KEY are required")
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json"}
    session = requests.Session()
    for dealer in sorted(requested):
        retire_dealer(session, base_url, headers, dealer, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
