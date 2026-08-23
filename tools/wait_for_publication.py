#!/usr/bin/env python3
"""Wait until a static artifact is the exact customer-visible deployment."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def content_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def publication_match(local_content: bytes, remote_content: bytes) -> tuple[bool, str]:
    """Require both an exact byte match and the same non-empty marker id."""
    try:
        local = json.loads(local_content)
        remote = json.loads(remote_content)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        return False, f"invalid JSON: {exc}"

    expected_id = local.get("publication_id") if isinstance(local, dict) else None
    visible_id = remote.get("publication_id") if isinstance(remote, dict) else None
    if not isinstance(expected_id, str) or not expected_id:
        return False, "local artifact has no publication_id"
    if visible_id != expected_id:
        return False, f"visible publication_id={visible_id!r}, expected={expected_id!r}"

    local_hash = content_sha256(local_content)
    remote_hash = content_sha256(remote_content)
    if remote_hash != local_hash:
        return False, f"visible sha256={remote_hash}, expected={local_hash}"
    return True, f"publication_id={expected_id} sha256={local_hash}"


def cache_busted_url(url: str, publication_id: str, attempt: int) -> str:
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query.extend([
        ("publication_id", publication_id),
        ("attempt", str(attempt)),
    ])
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(query), parsed.fragment)
    )


def fetch_publication(url: str, publication_id: str, attempt: int) -> bytes:
    request = urllib.request.Request(
        cache_busted_url(url, publication_id, attempt),
        headers={
            "User-Agent": "GearDrop-publication-gate/1.0",
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        if getattr(response, "status", 200) != 200:
            raise RuntimeError(f"HTTP {getattr(response, 'status', 'unknown')}")
        return response.read()


def wait_for_publication(
    local_content: bytes,
    url: str,
    timeout_seconds: float,
    interval_seconds: float,
) -> tuple[bool, str]:
    local = json.loads(local_content)
    publication_id = local.get("publication_id") if isinstance(local, dict) else None
    if not isinstance(publication_id, str) or not publication_id:
        return False, "local artifact has no publication_id"

    deadline = time.monotonic() + timeout_seconds
    attempt = 0
    last_reason = "not requested"
    while True:
        attempt += 1
        try:
            remote_content = fetch_publication(url, publication_id, attempt)
            matched, last_reason = publication_match(local_content, remote_content)
            print(
                f"[publication] attempt={attempt} matched={str(matched).lower()} "
                f"{last_reason}",
                flush=True,
            )
            if matched:
                return True, last_reason
        except (OSError, RuntimeError, urllib.error.URLError) as exc:
            last_reason = f"fetch failed: {exc}"
            print(f"[publication] attempt={attempt} {last_reason}", flush=True)

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False, last_reason
        time.sleep(min(interval_seconds, remaining))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=900)
    parser.add_argument("--interval-seconds", type=float, default=10)
    args = parser.parse_args()

    if args.timeout_seconds < 0 or args.interval_seconds <= 0:
        parser.error("timeout must be >= 0 and interval must be > 0")
    local_content = args.file.read_bytes()
    matched, reason = wait_for_publication(
        local_content,
        args.url,
        args.timeout_seconds,
        args.interval_seconds,
    )
    if matched:
        print(f"PUBLICATION_GATE PASS {reason}", flush=True)
        return 0
    print(f"PUBLICATION_GATE FAIL {reason}", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
