#!/usr/bin/env python3
"""Materialize a hash-bound, non-sensitive price-audit sample payload."""
from __future__ import annotations

import argparse
import base64
import binascii
import gzip
import hashlib
import io
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dealers.source_registry import PRICE_AUDIT_TARGETS


MAX_ENCODED_CHARS = 20_000
MAX_JSON_BYTES = 1_000_000
EXPECTED_DEALERS = Counter(PRICE_AUDIT_TARGETS)


class SamplePayloadError(ValueError):
    """The supplied exact-sample payload is invalid or not hash-bound."""


def decode_sample_payload(payload: str, expected_sha256: str) -> bytes:
    if not payload:
        raise SamplePayloadError("sample payload is empty")
    if len(payload) > MAX_ENCODED_CHARS:
        raise SamplePayloadError("sample payload exceeds the encoded size limit")
    expected = expected_sha256.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise SamplePayloadError("expected sha256 must contain 64 hex characters")
    try:
        compressed = base64.b64decode(payload, validate=True)
        with gzip.GzipFile(fileobj=io.BytesIO(compressed), mode="rb") as handle:
            raw = handle.read(MAX_JSON_BYTES + 1)
    except (binascii.Error, gzip.BadGzipFile, EOFError, OSError) as exc:
        raise SamplePayloadError(
            f"sample payload decode failed: {type(exc).__name__}"
        ) from exc
    if len(raw) > MAX_JSON_BYTES:
        raise SamplePayloadError("sample JSON exceeds the decoded size limit")
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise SamplePayloadError(
            f"sample sha256 mismatch: expected {expected}, got {actual}"
        )
    try:
        source = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SamplePayloadError("sample payload is not valid UTF-8 JSON") from exc
    audits = source.get("audits") if isinstance(source, dict) else None
    if not isinstance(audits, list) or len(audits) != 100:
        raise SamplePayloadError("sample artifact must contain exactly 100 audits")
    sku_ids = [
        str(item.get("sku_id") or "")
        for item in audits
        if isinstance(item, dict)
    ]
    if (
        len(sku_ids) != 100
        or len(set(sku_ids)) != 100
        or any(not value for value in sku_ids)
    ):
        raise SamplePayloadError("sample artifact contains missing or duplicate sku_id values")
    counts = Counter(str(item.get("dealer") or "") for item in audits)
    if counts != EXPECTED_DEALERS:
        raise SamplePayloadError(
            f"sample artifact dealer counts do not match contract: {dict(counts)}"
        )
    return raw


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = os.environ.get("PRICE_AUDIT_SAMPLE_GZIP_BASE64", "")
    raw = decode_sample_payload(payload, args.expected_sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(raw)
    print(
        f"[sample] exact artifact materialized: audits=100 "
        f"sha256={hashlib.sha256(raw).hexdigest()}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
