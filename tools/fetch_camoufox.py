#!/usr/bin/env python3
"""Fetch the pinned Camoufox runtime with authenticated GitHub API reads."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

import requests
from camoufox.__main__ import CamoufoxUpdate


GITHUB_API_PREFIX = "https://api.github.com/"


def github_authenticated_get(
    original_get: Callable[..., Any], token: str
) -> Callable[..., Any]:
    """Wrap requests.get and authenticate only GitHub API metadata reads."""

    def authenticated_get(url: str, *args: Any, **kwargs: Any) -> Any:
        if str(url).startswith(GITHUB_API_PREFIX):
            headers = dict(kwargs.get("headers") or {})
            headers.setdefault("Authorization", f"Bearer {token}")
            headers.setdefault("Accept", "application/vnd.github+json")
            headers.setdefault("X-GitHub-Api-Version", "2022-11-28")
            kwargs["headers"] = headers
        return original_get(url, *args, **kwargs)

    return authenticated_get


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required for authenticated Camoufox metadata reads")

    original_get = requests.get
    requests.get = github_authenticated_get(original_get, token)
    try:
        CamoufoxUpdate().update()
    finally:
        requests.get = original_get
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
