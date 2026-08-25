import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class WorkflowGuardTests(unittest.TestCase):
    def test_monitor_runs_independent_checks_then_aggregates(self):
        workflow = (ROOT / ".github/workflows/freshness-monitor.yml").read_text(encoding="utf-8")
        for step_id in ("outlet_quality", "dealer_quality", "platform_region_quality", "static_fallbacks"):
            self.assertIn(f"id: {step_id}", workflow)
        self.assertEqual(workflow.count("continue-on-error: true"), 4)
        self.assertIn("name: Aggregate production quality gate", workflow)
        self.assertIn("if: always()", workflow)
        self.assertIn('if [ "$failed" -ne 0 ]', workflow)

    def test_outlet_rechecks_active_terminal_url_results(self):
        workflow = (ROOT / ".github/workflows/refresh-outlet.yml").read_text(encoding="utf-8")
        primary_runner = (ROOT / "server_run_update.sh").read_text(encoding="utf-8")
        self.assertIn(
            "--status active --stored-http-status 404 --stored-http-status 410",
            workflow,
        )
        self.assertIn(
            "--status active --stored-http-status 404 --stored-http-status 410",
            primary_runner,
        )

    def test_mec_fallback_installs_camoufox_runtime_before_preflight(self):
        workflow = (ROOT / ".github/workflows/refresh-mec.yml").read_text(encoding="utf-8")
        self.assertLess(
            workflow.index("python tools/fetch_camoufox.py"),
            workflow.index("python tools/check_mec_browser_runtime.py"),
        )

    def test_mec_fallback_allows_full_pdp_enrichment_window(self):
        workflow = (ROOT / ".github/workflows/refresh-mec.yml").read_text(encoding="utf-8")
        self.assertIn("timeout-minutes: 120", workflow)
        self.assertIn("timeout 3600 python -u -m dealers.mec", workflow)

    def test_workflows_fetch_camoufox_with_authenticated_helper(self):
        names = (
            "refresh-outlet.yml",
            "refresh-dealers.yml",
            "refresh-mec.yml",
            "revalidate-dealer-prices.yml",
            "audit-dealer-prices.yml",
        )
        for name in names:
            workflow = (ROOT / ".github/workflows" / name).read_text(encoding="utf-8")
            with self.subTest(workflow=name):
                self.assertIn("GITHUB_TOKEN: ${{ github.token }}", workflow)
                self.assertIn("python tools/fetch_camoufox.py", workflow)
                self.assertNotIn("python -m camoufox fetch", workflow)

    def test_burton_sources_are_in_primary_and_fallback_dealer_runs(self):
        workflow = (ROOT / ".github/workflows/refresh-dealers.yml").read_text(encoding="utf-8")
        primary_runner = (ROOT / "server_run_dealers.sh").read_text(encoding="utf-8")
        for source in (workflow, primary_runner):
            self.assertIn("burton backcountry evo rei ssense", source)
            self.assertIn("--dealer burton --dealer backcountry", source)


if __name__ == "__main__":
    unittest.main()
