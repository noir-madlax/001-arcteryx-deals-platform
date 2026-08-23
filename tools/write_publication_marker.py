#!/usr/bin/env python3
"""Write a unique static marker for one production publication attempt."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def build_marker(publication_id: str, scope: str) -> dict:
    publication_id = publication_id.strip()
    scope = scope.strip()
    if not publication_id:
        raise ValueError("publication_id must not be empty")
    if not scope:
        raise ValueError("scope must not be empty")
    return {
        "schema_version": 1,
        "publication_id": publication_id,
        "scope": scope,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publication-id", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--output", type=Path, default=Path("publication.json"))
    args = parser.parse_args()

    marker = build_marker(args.publication_id, args.scope)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(marker, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"PUBLICATION_MARKER {args.output.resolve()} "
        f"id={marker['publication_id']} scope={marker['scope']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
