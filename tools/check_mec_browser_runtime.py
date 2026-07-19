#!/usr/bin/env python3
"""Fail fast when MEC's Scrapling fallback browser cannot start."""
from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any


def verify_runtime(session_factory: Callable[..., Any] | None = None) -> None:
    if session_factory is None:
        from scrapling.fetchers import StealthySession

        session_factory = StealthySession

    # Match the production fallback exactly; entering the context launches the browser.
    with session_factory(headless=True, network_idle=True, solve_cloudflare=True):
        pass


def main() -> int:
    try:
        verify_runtime()
    except Exception as exc:
        print(
            f"[mec] browser fallback preflight failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1
    print("[mec] browser fallback runtime OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
