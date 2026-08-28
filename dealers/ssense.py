"""Fail-closed guard for the retired SSENSE source.

SSENSE collection was retired on 2026-08-28. The module remains only so an
old manual command or external import cannot silently resume network access.
"""

from __future__ import annotations


class RetiredSourceError(RuntimeError):
    """Raised whenever an obsolete SSENSE scraper entry point is invoked."""


class Scraper:
    KEY = "ssense"
    NAME = "SSENSE"
    REGION = "US"
    TIER = "retired"

    def scrape(self) -> list[dict]:
        raise RetiredSourceError(
            "SSENSE source retired; collection and price reads are disabled"
        )


if __name__ == "__main__":
    raise SystemExit(
        "[ssense] source retired; production and manual scraper entry points are disabled"
    )
