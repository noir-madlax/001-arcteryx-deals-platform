import unittest
from pathlib import Path

from dealers.run_all import DEALER_KEYS
from dealers.ssense import RetiredSourceError, Scraper as RetiredSsenseScraper
from dealers.source_registry import (
    ACTIVE_DEALERS,
    PRICE_AUDIT_TARGETS,
    PRIMARY_DEALERS,
    RETIRED_DEALERS,
    REVALIDATION_DEALERS,
)
from tools.retire_dealer import retire_dealer


ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, payload=None, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError(f"unexpected HTTP {self.status_code}")

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, rows):
        self.rows = [dict(row) for row in rows]
        self.requests = []

    def request(self, method, url, **kwargs):
        self.requests.append((method, url, kwargs))
        if method == "GET":
            return FakeResponse([dict(row) for row in self.rows])
        if method == "PATCH":
            for row in self.rows:
                if (row.get("status") or "active") != "inactive":
                    row.update(kwargs["json"])
            return FakeResponse(None, 204)
        raise AssertionError(f"unexpected method {method}")


class SourceRetirementTests(unittest.TestCase):
    def test_ssense_is_retired_from_all_operational_contracts(self):
        self.assertEqual(RETIRED_DEALERS, {"ssense"})
        self.assertNotIn("ssense", ACTIVE_DEALERS)
        self.assertNotIn("ssense", PRIMARY_DEALERS)
        self.assertNotIn("ssense", REVALIDATION_DEALERS)
        self.assertNotIn("ssense", PRICE_AUDIT_TARGETS)
        self.assertNotIn("ssense", DEALER_KEYS)
        self.assertEqual(sum(PRICE_AUDIT_TARGETS.values()), 100)
        self.assertEqual(PRICE_AUDIT_TARGETS["arcteryx_outlet"], 70)

    def test_legacy_ssense_scraper_entry_point_fails_closed(self):
        with self.assertRaisesRegex(RetiredSourceError, "source retired"):
            RetiredSsenseScraper().scrape()

    def test_ssense_network_paths_are_removed(self):
        scraper = (ROOT / "dealers" / "ssense.py").read_text(encoding="utf-8")
        revalidator = (ROOT / "dealers" / "revalidate.py").read_text(encoding="utf-8")
        audit = (ROOT / "tools" / "audit_price_accuracy.py").read_text(encoding="utf-8")

        self.assertNotIn("https://www.ssense.com", scraper)
        self.assertNotIn("fetch_ssense", revalidator)
        self.assertNotIn("read_ssense", audit)

    def test_retirement_marks_rows_inactive_and_preserves_them(self):
        session = FakeSession(
            [
                {"sku_id": "ssense:1", "status": "active", "missing_runs": 0},
                {"sku_id": "ssense:2", "status": "missing", "missing_runs": 1},
                {"sku_id": "ssense:3", "status": "inactive", "missing_runs": 2},
            ]
        )

        counts = retire_dealer(
            session,
            "https://supabase.example",
            {"apikey": "redacted", "Authorization": "Bearer redacted"},
            "ssense",
        )

        self.assertEqual(counts, {"inactive": 3})
        self.assertEqual(len(session.rows), 3)
        self.assertTrue(all(row["status"] == "inactive" for row in session.rows))
        self.assertTrue(all(row["missing_runs"] >= 2 for row in session.rows))
        patches = [request for request in session.requests if request[0] == "PATCH"]
        self.assertEqual(len(patches), 1)
        self.assertEqual(patches[0][2]["params"], {"dealer": "eq.ssense"})

    def test_retirement_dry_run_does_not_patch(self):
        session = FakeSession(
            [{"sku_id": "ssense:1", "status": "active", "missing_runs": 0}]
        )

        counts = retire_dealer(
            session,
            "https://supabase.example",
            {"apikey": "redacted", "Authorization": "Bearer redacted"},
            "ssense",
            dry_run=True,
        )

        self.assertEqual(counts, {"active": 1})
        self.assertFalse(any(request[0] == "PATCH" for request in session.requests))


if __name__ == "__main__":
    unittest.main()
