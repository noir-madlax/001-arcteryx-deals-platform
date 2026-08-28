import pathlib
import shutil
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class DirectServerReleaseTests(unittest.TestCase):
    def test_release_is_allowlisted_and_runnable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            release = pathlib.Path(temp_dir) / "release"
            result = subprocess.run(
                ["bash", "ops/web/build-release.sh", str(release), "HEAD"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("release_commit=", result.stdout)
            self.assertTrue((release / "static/index.html").is_file())
            self.assertTrue((release / "static/en/index.html").is_file())
            self.assertTrue((release / "static/sitemap-products.xml").is_file())
            self.assertTrue((release / "api/product.mjs").is_file())
            self.assertTrue((release / "ops/web/product-server.mjs").is_file())
            self.assertFalse((release / "static/.agent").exists())
            self.assertFalse((release / "static/tests").exists())
            self.assertFalse((release / "static/supabase").exists())
            self.assertFalse(any((release / "static").rglob("*.py")))
            self.assertFalse(any((release / "static").rglob("*.sql")))
            self.assertEqual(
                (release / "REVISION").read_text(encoding="utf-8").strip(),
                subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
            )

    def test_operational_templates_keep_scopes_separate(self):
        common = (ROOT / "ops/web/nginx/geardrop-common.conf").read_text()
        product_unit = (ROOT / "ops/web/systemd/geardrop-product.service").read_text()
        deploy_unit = (ROOT / "ops/web/systemd/geardrop-deploy.service").read_text()
        self.assertIn("root /srv/geardrop/current/static;", common)
        self.assertIn("location = /p", common)
        self.assertIn("proxy_pass http://127.0.0.1:4181;", common)
        self.assertIn("DynamicUser=yes", product_unit)
        self.assertNotIn("WorkingDirectory=", product_unit)
        self.assertIn("GEARDROP_PRODUCT_PORT=4181", product_unit)
        self.assertIn("User=ec2-user", deploy_unit)
        self.assertNotIn("/home/ec2-user/arcteryx", common + product_unit + deploy_unit)


if __name__ == "__main__":
    unittest.main()
