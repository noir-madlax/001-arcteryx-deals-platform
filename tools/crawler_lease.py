#!/usr/bin/env python3
"""Acquire/release Supabase-backed leases for distributed crawler jobs."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import requests


def config() -> tuple[str, str]:
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        raise SystemExit("SUPABASE_URL and SUPABASE_KEY are required")
    return url, key


def headers(key: str) -> dict[str, str]:
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def rpc(name: str, payload: dict) -> bool:
    url, key = config()
    response = requests.post(
        f"{url}/rest/v1/rpc/{name}",
        headers=headers(key),
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return bool(response.json())


def read_scope(scope: str) -> dict | None:
    url, key = config()
    response = requests.get(
        f"{url}/rest/v1/crawler_leases",
        headers=headers(key),
        params={"scope": f"eq.{scope}", "select": "*", "limit": "1"},
        timeout=30,
    )
    response.raise_for_status()
    rows = response.json()
    return rows[0] if rows else None


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def needs_fallback(scope: str, stale_hours: float) -> bool:
    row = read_scope(scope)
    if not row:
        return True
    now = datetime.now(timezone.utc)
    lease_until = parse_ts(row.get("lease_until"))
    if row.get("status") == "running" and lease_until and lease_until > now:
        return False
    if row.get("status") != "success":
        return True
    completed = parse_ts(row.get("completed_at"))
    if not completed:
        return True
    return (now - completed).total_seconds() > stale_hours * 3600


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    acquire = sub.add_parser("acquire")
    acquire.add_argument("--scope", required=True)
    acquire.add_argument("--owner", required=True)
    acquire.add_argument("--ttl-minutes", type=int, default=240)

    finish = sub.add_parser("finish")
    finish.add_argument("--scope", required=True)
    finish.add_argument("--owner", required=True)
    finish.add_argument("--status", required=True, choices=["success", "failed"])
    finish.add_argument("--message", default="")

    fallback = sub.add_parser("needs-fallback")
    fallback.add_argument("--scope", required=True)
    fallback.add_argument("--stale-hours", type=float, default=4.5)

    status = sub.add_parser("status")
    status.add_argument("--scope", required=True)

    args = parser.parse_args()
    if args.command == "acquire":
        result = rpc("claim_crawler_lease", {
            "p_scope": args.scope,
            "p_owner": args.owner,
            "p_ttl_minutes": args.ttl_minutes,
        })
        print("true" if result else "false")
        return 0
    if args.command == "finish":
        result = rpc("finish_crawler_lease", {
            "p_scope": args.scope,
            "p_owner": args.owner,
            "p_status": args.status,
            "p_message": args.message,
        })
        print("true" if result else "false")
        return 0 if result else 1
    if args.command == "needs-fallback":
        print("true" if needs_fallback(args.scope, args.stale_hours) else "false")
        return 0
    print(json.dumps(read_scope(args.scope), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
