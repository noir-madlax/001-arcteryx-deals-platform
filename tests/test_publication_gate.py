import json
import unittest
from pathlib import Path

from tools.wait_for_publication import cache_busted_url, publication_match
from tools.write_publication_marker import build_marker


class PublicationGateTests(unittest.TestCase):
    def test_exact_marker_is_customer_visible_match(self):
        content = json.dumps({"publication_id": "run-123", "scope": "dealers"}).encode()

        matched, reason = publication_match(content, content)

        self.assertTrue(matched)
        self.assertIn("publication_id=run-123", reason)

    def test_same_id_with_different_bytes_is_not_a_match(self):
        local = b'{"publication_id":"run-123","scope":"dealers"}'
        remote = b'{"publication_id":"run-123","scope":"mec"}'

        matched, reason = publication_match(local, remote)

        self.assertFalse(matched)
        self.assertIn("sha256", reason)

    def test_stale_visible_marker_is_not_a_match(self):
        local = b'{"publication_id":"run-123"}'
        remote = b'{"publication_id":"run-122"}'

        matched, reason = publication_match(local, remote)

        self.assertFalse(matched)
        self.assertIn("visible publication_id", reason)

    def test_cache_buster_preserves_existing_query(self):
        url = cache_busted_url("https://example.test/publication.json?x=1", "run 123", 2)

        self.assertIn("x=1", url)
        self.assertIn("publication_id=run+123", url)
        self.assertIn("attempt=2", url)

    def test_marker_builder_requires_exact_identity_and_scope(self):
        marker = build_marker("run-123", "dealers")

        self.assertEqual(marker["publication_id"], "run-123")
        self.assertEqual(marker["scope"], "dealers")
        with self.assertRaises(ValueError):
            build_marker("", "dealers")

    def test_all_static_refresh_workflows_wait_for_exact_publication(self):
        root = Path(__file__).resolve().parent.parent
        for name in ("refresh-dealers.yml", "refresh-mec.yml", "refresh-outlet.yml"):
            workflow = (root / ".github" / "workflows" / name).read_text(encoding="utf-8")
            with self.subTest(workflow=name):
                self.assertIn("PUBLICATION_ID:", workflow)
                self.assertIn("tools/write_publication_marker.py", workflow)
                self.assertIn("publication.json", workflow)
                self.assertIn("tools/wait_for_publication.py", workflow)

        dealers_workflow = (
            root / ".github" / "workflows" / "refresh-dealers.yml"
        ).read_text(encoding="utf-8")
        self.assertIn('if [ "$dealer" = "evo" ]', dealers_workflow)
        self.assertIn("dealer_timeout=3600", dealers_workflow)

    def test_all_primary_static_refresh_scripts_wait_for_exact_publication(self):
        root = Path(__file__).resolve().parent.parent
        cases = {
            "server_run_update.sh": ("outlet", "data.js"),
            "server_run_dealers.sh": ("dealers", "dealers/results.json"),
            "server_run_mec.sh": ("mec", "dealers/results.json"),
        }
        for name, (scope, static_file) in cases.items():
            script = (root / name).read_text(encoding="utf-8")
            with self.subTest(script=name):
                marker = f"tools/write_publication_marker.py --scope {scope}"
                wait = "tools/wait_for_publication.py --file publication.json"
                self.assertIn('SITE_URL="${SITE_URL:-https://001.100app.dev}"', script)
                self.assertIn(marker, script)
                self.assertIn(static_file, script)
                self.assertIn("publication.json", script)
                self.assertIn(wait, script)

                marker_pos = script.index(marker)
                commit_pos = script.index("git commit", marker_pos)
                push_pos = script.index("git push origin main", commit_pos)
                wait_pos = script.index(wait, push_pos)
                self.assertLess(marker_pos, commit_pos)
                self.assertLess(commit_pos, push_pos)
                self.assertLess(push_pos, wait_pos)


if __name__ == "__main__":
    unittest.main()
