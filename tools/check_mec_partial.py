#!/usr/bin/env python3
"""Reject incomplete MEC list output before merge or Supabase sync."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate_partial(path: Path, min_items: int = 50) -> tuple[int, int | None]:
    if not path.exists():
        raise ValueError("MEC partial missing")
    payload = json.loads(path.read_text())
    count = len(payload.get("items") or [])
    expected = payload.get("expected_count")
    if payload.get("crawl_complete") is not True:
        raise ValueError(f"MEC crawl incomplete: {count}/{expected or '?'}")
    if count < min_items:
        raise ValueError(f"MEC partial too small: {count} < {min_items}")
    if expected is not None and count < int(expected):
        raise ValueError(f"MEC parsed count below expected: {count} < {expected}")
    return count, int(expected) if expected is not None else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, default=Path("dealers/_partial/mec.json"))
    parser.add_argument("--min-items", type=int, default=50)
    args = parser.parse_args()
    try:
        count, expected = validate_partial(args.file, args.min_items)
    except (ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"[mec] partial gate OK: {count}/{expected or '?'} items")


if __name__ == "__main__":
    main()
