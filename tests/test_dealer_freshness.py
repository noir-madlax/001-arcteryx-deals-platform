import json
import os
import tempfile
import unittest
from pathlib import Path

from dealers import merge_partial
from dealers.supabase_sync import (
    fresh_dealer_keys,
    next_dealer_lifecycle,
    recovered_url_health,
)
from tools.check_mec_partial import validate_partial
from tools.check_data_quality import product_freshness_timestamp


class DealerFreshnessTests(unittest.TestCase):
    def test_dealer_product_freshness_uses_last_updated(self):
        ts = product_freshness_timestamp({
            "dealer": "rei",
            "last_seen_at": "2026-06-01T00:00:00+00:00",
            "last_updated": "2026-07-12T09:00:00+00:00",
        })
        self.assertEqual(ts.isoformat(), "2026-07-12T09:00:00+00:00")

    def test_outlet_product_freshness_uses_last_seen(self):
        ts = product_freshness_timestamp({
            "dealer": "arcteryx_outlet",
            "last_seen_at": "2026-07-11T09:00:00+00:00",
            "last_updated": "2026-07-12T09:00:00+00:00",
        })
        self.assertEqual(ts.isoformat(), "2026-07-11T09:00:00+00:00")

    def test_merge_marks_only_nonempty_partials_fresh(self):
        previous_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                Path("dealers/_partial").mkdir(parents=True)
                Path("dealers/results.json").write_text(json.dumps({
                    "generated_at": "2026-07-10 00:00:00",
                    "dealers": {
                        "mec": {"name": "MEC", "count": 1, "items": [{"url": "old-mec"}]},
                        "evo": {"name": "EVO", "count": 1, "items": [{"url": "old-evo"}]},
                    },
                }))
                Path("dealers/_partial/mec.json").write_text(json.dumps({
                    "name": "MEC",
                    "region": "CA",
                    "count": 1,
                    "items": [{"url": "new-mec"}],
                    "crawl_complete": True,
                    "saved_at": "2026-07-11 16:00:00",
                }))
                Path("dealers/_partial/evo.json").write_text(json.dumps({
                    "name": "EVO", "region": "US", "count": 0, "items": [],
                    "crawl_complete": False,
                    "saved_at": "2026-07-11 16:00:00",
                }))

                merge_partial.main()
                merged = json.loads(Path("dealers/results.json").read_text())
                self.assertEqual(merged["fresh_dealers"], ["mec"])
                self.assertEqual(merged["dealers"]["mec"]["items"][0]["url"], "new-mec")
                self.assertEqual(merged["dealers"]["mec"]["refreshed_at"], "2026-07-11 16:00:00")
                self.assertEqual(merged["dealers"]["evo"]["items"][0]["url"], "old-evo")
            finally:
                os.chdir(previous_cwd)

    def test_merge_rejects_nonempty_incomplete_partial(self):
        previous_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                Path("dealers/_partial").mkdir(parents=True)
                Path("dealers/results.json").write_text(json.dumps({
                    "dealers": {"ssense": {"name": "SSENSE", "count": 1, "items": [{"url": "old"}]}},
                }))
                Path("dealers/_partial/ssense.json").write_text(json.dumps({
                    "name": "SSENSE",
                    "count": 1,
                    "items": [{"url": "partial"}],
                    "crawl_complete": False,
                }))
                merge_partial.main()
                merged = json.loads(Path("dealers/results.json").read_text())
                self.assertEqual(merged["fresh_dealers"], [])
                self.assertEqual(merged["dealers"]["ssense"]["items"][0]["url"], "old")
            finally:
                os.chdir(previous_cwd)

    def test_fresh_dealer_keys_is_backward_compatible(self):
        self.assertIsNone(fresh_dealer_keys({"dealers": {"mec": {}}}))
        self.assertEqual(fresh_dealer_keys({"fresh_dealers": ["mec", "rei"]}), {"mec", "rei"})

    def test_dealer_two_trusted_misses_then_recovery(self):
        first = next_dealer_lifecycle(
            {"status": "active", "missing_runs": 0, "last_seen_at": "old"},
            present=False,
            observed_at="run-1",
        )
        second = next_dealer_lifecycle(first, present=False, observed_at="run-2")
        recovered = next_dealer_lifecycle(second, present=True, observed_at="run-3")
        self.assertEqual(first, {"status": "missing", "missing_runs": 1, "last_seen_at": "old"})
        self.assertEqual(second, {"status": "inactive", "missing_runs": 2, "last_seen_at": "old"})
        self.assertEqual(recovered, {"status": "active", "missing_runs": 0, "last_seen_at": "run-3"})

    def test_dealer_rediscovery_clears_terminal_url_health(self):
        self.assertEqual(
            recovered_url_health({"url_http_status": 404, "url_checked_at": "old"}),
            {"url_http_status": None, "url_checked_at": None},
        )
        self.assertEqual(
            recovered_url_health({"url_http_status": 503, "url_checked_at": "old"}),
            {"url_http_status": 503, "url_checked_at": "old"},
        )

    def test_mec_partial_requires_complete_expected_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mec.json"
            path.write_text(json.dumps({
                "items": [{"url": str(i)} for i in range(52)],
                "crawl_complete": False,
                "expected_count": 128,
            }))
            with self.assertRaisesRegex(ValueError, "crawl incomplete"):
                validate_partial(path)

            path.write_text(json.dumps({
                "items": [{"url": str(i)} for i in range(128)],
                "crawl_complete": True,
                "expected_count": 128,
            }))
            self.assertEqual(validate_partial(path), (128, 128))


if __name__ == "__main__":
    unittest.main()
