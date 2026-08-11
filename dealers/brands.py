"""Canonical brand contract shared by dealer ingestion and quality gates."""
from __future__ import annotations

import re


BRAND_LABELS = {
    "arcteryx": "Arc'teryx",
    "burton": "Burton",
    "patagonia": "Patagonia",
}
SUPPORTED_BRANDS = frozenset(BRAND_LABELS)


def normalize_brand(value: object) -> str | None:
    """Return a supported canonical key without accepting substring matches."""
    normalized = re.sub(r"[^a-z0-9]+", "", str(value or "").lower())
    if normalized in {"arcteryx", "arcteryxoutlet"}:
        return "arcteryx"
    if normalized == "burton":
        return "burton"
    if normalized == "patagonia":
        return "patagonia"
    return None


def _inferred_brand(item: dict) -> str | None:
    """Resolve only strong URL/name signals, never a legacy default."""
    url = str(item.get("url") or "").lower()
    if re.search(r"(?:^|\.)burton\.com(?:/|$)", url.replace("https://", "").replace("http://", "")):
        return "burton"
    if re.search(r"(?:^|\.)patagonia\.com(?:/|$)", url.replace("https://", "").replace("http://", "")):
        return "patagonia"
    if "arcteryx.com" in url or "/product/arcteryx/" in url:
        return "arcteryx"

    name = str(item.get("name") or item.get("full_name") or item.get("model") or "").strip()
    for key, label in BRAND_LABELS.items():
        if re.match(rf"^{re.escape(label)}(?:\s|$)", name, re.IGNORECASE):
            return key
    if re.match(r"^arc[\s-]*[’'`]?teryx(?:\s|$)", name, re.IGNORECASE):
        return "arcteryx"
    return None


def canonical_brand(item: dict, *, legacy_default: bool = True) -> str | None:
    """Resolve explicit metadata first, then strong URL/name signals.

    Existing GearDrop rows predate the brand column and are all Arc'teryx, so
    an entirely absent brand signal keeps that legacy interpretation. An
    explicit but unsupported value always fails closed.
    """
    explicit = item.get("brand")
    if explicit is not None and str(explicit).strip():
        return normalize_brand(explicit)

    inferred = _inferred_brand(item)
    return inferred or ("arcteryx" if legacy_default else None)


def brand_label(value: object) -> str | None:
    key = normalize_brand(value)
    return BRAND_LABELS.get(key) if key else None


def vendor_matches_brand(vendor: object, expected_brand: str) -> bool:
    return normalize_brand(vendor) == normalize_brand(expected_brand)


def source_contract_valid(item: dict, dealer: str) -> bool:
    """Validate a supported brand and any dealer-specific brand URL scope."""
    brand = canonical_brand(item)
    if brand not in SUPPORTED_BRANDS:
        return False
    inferred = _inferred_brand(item)
    if inferred and inferred != brand:
        return False
    url = str(item.get("url") or "")
    if dealer == "ssense":
        return brand == "arcteryx" and bool(re.search(
            r"^https://(?:www\.)?ssense\.com/(?:[a-z]{2}-[a-z]{2}/)?(?:men|women)/product/arcteryx/",
            url,
            re.IGNORECASE,
        ))
    if dealer == "arcteryx_outlet":
        return brand == "arcteryx"
    return True
