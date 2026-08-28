import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRIMARY_ORIGIN = "https://geardrop.100app.dev"
LEGACY_HOST = "001." + "100app.dev"


class PrimaryDomainTests(unittest.TestCase):
    def test_active_surfaces_do_not_publish_the_legacy_host(self):
        result = subprocess.run(
            [
                "git",
                "grep",
                "-F",
                "-n",
                "-e",
                LEGACY_HOST,
                "-e",
                LEGACY_HOST.replace(".", "\\."),
                "--",
                ":!.agent/**",
                ":!geo/audits/**",
                ":!app/RELEASE_READINESS.md",
                ":!docs/DIRECT_SERVER_DEPLOYMENT.md",
                f":!ops/web/nginx/{LEGACY_HOST}-http.conf",
                f":!ops/web/nginx/{LEGACY_HOST}-tls.conf",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1, result.stdout or result.stderr)

    def test_primary_origin_is_consistent_across_runtime_sources(self):
        expected = {
            "api/product.mjs": f"const SITE_URL = '{PRIMARY_ORIGIN}';",
            "geo/site-content.json": f'"base_url": "{PRIMARY_ORIGIN}"',
            "tools/generate_geo_catalog.py": f'SITE_URL = "{PRIMARY_ORIGIN}"',
            "tools/notify_indexnow.py": f'SITE_URL = "{PRIMARY_ORIGIN}"',
            "tools/check_geo_readiness.py": f'CANONICAL_ORIGIN = "{PRIMARY_ORIGIN}"',
        }
        for relative_path, token in expected.items():
            source = (ROOT / relative_path).read_text(encoding="utf-8")
            self.assertIn(token, source, relative_path)


if __name__ == "__main__":
    unittest.main()
