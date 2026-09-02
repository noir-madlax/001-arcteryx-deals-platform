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

    def test_all_refresh_workflows_publish_through_versioned_data_releases(self):
        root = Path(__file__).resolve().parent.parent
        for name in ("refresh-dealers.yml", "refresh-mec.yml", "refresh-outlet.yml"):
            workflow = (root / ".github" / "workflows" / name).read_text(encoding="utf-8")
            with self.subTest(workflow=name):
                self.assertIn("permissions:\n  contents: read", workflow)
                self.assertIn("tools/hydrate_runtime_snapshot.py", workflow)
                self.assertIn("tools/wait_for_data_release.py", workflow)
                self.assertIn("SYNC_COMPLETED_AT", workflow)
                self.assertNotIn("tools/write_publication_marker.py", workflow)
                self.assertNotIn("tools/wait_for_publication.py", workflow)
                self.assertNotIn("git push origin main", workflow)

        dealers_workflow = (
            root / ".github" / "workflows" / "refresh-dealers.yml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            'if [ "$dealer" = "evo" ] || [ "$dealer" = "rei" ]',
            dealers_workflow,
        )
        self.assertIn("dealer_timeout=3600", dealers_workflow)

    def test_all_primary_refresh_scripts_keep_data_out_of_git(self):
        root = Path(__file__).resolve().parent.parent
        cases = {
            "server_run_update.sh": "catalog",
            "server_run_dealers.sh": "dealers",
            "server_run_mec.sh": "dealers",
        }
        for name, dataset in cases.items():
            script = (root / name).read_text(encoding="utf-8")
            with self.subTest(script=name):
                self.assertIn('SITE_URL="${SITE_URL:-https://geardrop.100app.dev}"', script)
                self.assertIn(f"--dataset {dataset}", script)
                self.assertIn("tools/wait_for_data_release.py", script)
                self.assertIn("SYNC_COMPLETED_AT", script)
                self.assertNotIn("tools/write_publication_marker.py", script)
                self.assertNotIn("tools/wait_for_publication.py", script)
                self.assertNotIn("git commit", script)
                self.assertNotIn("git push origin main", script)


if __name__ == "__main__":
    unittest.main()
