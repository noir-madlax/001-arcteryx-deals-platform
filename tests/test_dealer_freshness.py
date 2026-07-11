import json
import os
import tempfile
import unittest
from pathlib import Path

from dealers import merge_partial
from dealers.supabase_sync import fresh_dealer_keys


class DealerFreshnessTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
