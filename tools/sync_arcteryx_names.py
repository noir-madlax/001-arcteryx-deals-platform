#!/usr/bin/env python3
"""Sync/check the shared GearDrop naming and brand runtimes used by Expo."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "arcteryx-names.js"
APP_COPY = ROOT / "app" / "lib" / "arcteryx-names.js"
BRAND_SOURCE = ROOT / "gear-brands.js"
BRAND_APP_COPY = ROOT / "app" / "lib" / "gear-brands.js"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when the Expo copy differs")
    args = parser.parse_args()

    copies = ((SOURCE, APP_COPY), (BRAND_SOURCE, BRAND_APP_COPY))
    if args.check:
        stale = [target for source, target in copies if not target.exists() or target.read_bytes() != source.read_bytes()]
        if stale:
            print("[names] out of sync: " + ", ".join(str(path.relative_to(ROOT)) for path in stale), file=sys.stderr)
            print("[names] run: python3 tools/sync_arcteryx_names.py", file=sys.stderr)
            return 1
        print("[names] shared runtime copies are identical")
        return 0

    for source, target in copies:
        target.write_bytes(source.read_bytes())
        print(f"[names] synced {target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
