#!/usr/bin/env python3
"""Hydrate crawler seed data from the current production data release."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


SITE_URL = "https://geardrop.100app.dev"
DATASETS = {
    "catalog": "global_data.json",
    "dealers": "dealers/results.json",
}
MAX_BYTES = 32 * 1024 * 1024


def validate_snapshot(dataset: str, value: Any) -> int:
    if dataset == "catalog":
        if not isinstance(value, list) or not value:
            raise ValueError("catalog snapshot must be a non-empty JSON array")
        if not all(isinstance(row, dict) and row.get("sku_id") for row in value):
            raise ValueError("catalog snapshot contains a row without sku_id")
        foreign_dealers = {
            str(row.get("dealer") or "")
            for row in value
            if str(row.get("dealer") or "") not in ("", "arcteryx_outlet")
        }
        if foreign_dealers:
            raise ValueError("catalog seed contains non-outlet dealer rows")
        return len(value)
    if dataset == "dealers":
        if not isinstance(value, dict) or not isinstance(value.get("dealers"), dict):
            raise ValueError("dealer snapshot must contain a dealers object")
        dealers = value["dealers"]
        if not dealers:
            raise ValueError("dealer snapshot must contain at least one dealer")
        item_count = sum(len(block.get("items") or []) for block in dealers.values())
        if item_count <= 0:
            raise ValueError("dealer snapshot must contain at least one item")
        return item_count
    raise ValueError(f"unsupported dataset: {dataset}")


def snapshot_url(site_url: str, dataset: str) -> str:
    parsed = urllib.parse.urlparse(site_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path not in ("", "/"):
        raise ValueError("site-url must be an HTTPS origin")
    if dataset not in DATASETS:
        raise ValueError(f"unsupported dataset: {dataset}")
    return f"{site_url.rstrip('/')}/{DATASETS[dataset]}"


def fetch_snapshot(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "User-Agent": "GearDrop-Crawler-Hydrator/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read(MAX_BYTES + 1)
    if not payload or len(payload) > MAX_BYTES:
        raise ValueError(f"snapshot size is outside the accepted range: {len(payload)}")
    return payload


def atomic_write(output: Path, payload: bytes) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-url", default=SITE_URL)
    parser.add_argument("--dataset", choices=sorted(DATASETS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    url = snapshot_url(args.site_url, args.dataset)
    payload = fetch_snapshot(url)
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("production snapshot is not valid JSON") from error
    records = validate_snapshot(args.dataset, value)
    atomic_write(args.output, payload)
    digest = hashlib.sha256(payload).hexdigest()
    print(
        f"hydrated={args.dataset} records={records} bytes={len(payload)} "
        f"sha256={digest} output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
