"""Single source of truth for active and retired dealer integrations."""

from __future__ import annotations


ACTIVE_DEALERS = (
    "burton",
    "backcountry",
    "mec",
    "evo",
    "rei",
)

# MEC runs on its own node. The remaining sources share the primary dealer job.
PRIMARY_DEALERS = (
    "burton",
    "backcountry",
    "evo",
    "rei",
)

REVALIDATION_DEALERS = frozenset({"evo", "mec", "rei"})
RETIRED_DEALERS = frozenset({"ssense"})

# Keep the audit at exactly 100 SKUs after retiring SSENSE. The removed
# retailer quota is reassigned to the official Outlet source.
PRICE_AUDIT_TARGETS = {
    "arcteryx_outlet": 70,
    "evo": 10,
    "mec": 10,
    "rei": 10,
}
