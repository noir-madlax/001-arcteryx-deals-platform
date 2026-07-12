import json
import os
import tempfile
import unittest
from pathlib import Path

from dealers import merge_partial
from dealers.supabase_sync import fresh_dealer_keys
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
                    "saved_at": "2026-07-11 16:00:00",
                }))
                Path("dealers/_partial/evo.json").write_text(json.dumps({
                    "name": "EVO", "region": "US", "count": 0, "items": [],
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

    def test_fresh_dealer_keys_is_backward_compatible(self):
        self.assertIsNone(fresh_dealer_keys({"dealers": {"mec": {}}}))
        self.assertEqual(fresh_dealer_keys({"fresh_dealers": ["mec", "rei"]}), {"mec", "rei"})

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
