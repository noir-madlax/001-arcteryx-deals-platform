import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class WorkflowGuardTests(unittest.TestCase):
    def test_monitor_runs_independent_checks_then_aggregates(self):
        workflow = (ROOT / ".github/workflows/freshness-monitor.yml").read_text(encoding="utf-8")
        for step_id in ("outlet_quality", "dealer_quality", "static_fallbacks"):
            self.assertIn(f"id: {step_id}", workflow)
        self.assertEqual(workflow.count("continue-on-error: true"), 3)
        self.assertIn("name: Aggregate production quality gate", workflow)
        self.assertIn("if: always()", workflow)
        self.assertIn('if [ "$failed" -ne 0 ]', workflow)

    def test_outlet_rechecks_active_terminal_url_results(self):
        workflow = (ROOT / ".github/workflows/refresh-outlet.yml").read_text(encoding="utf-8")
        self.assertIn(
            "--status active --stored-http-status 404 --stored-http-status 410",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
