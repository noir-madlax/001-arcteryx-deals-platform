#!/usr/bin/env python3
"""Sync/check the shared Arc'teryx naming runtime used by Expo."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "arcteryx-names.js"
APP_COPY = ROOT / "app" / "lib" / "arcteryx-names.js"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when the Expo copy differs")
    args = parser.parse_args()

    source = SOURCE.read_bytes()
    if args.check:
        if not APP_COPY.exists() or APP_COPY.read_bytes() != source:
            print("[names] app/lib/arcteryx-names.js is out of sync", file=sys.stderr)
            print("[names] run: python3 tools/sync_arcteryx_names.py", file=sys.stderr)
            return 1
        print("[names] shared runtime copies are identical")
        return 0

    APP_COPY.write_bytes(source)
    print(f"[names] synced {APP_COPY.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
