import unittest
from unittest.mock import Mock, patch

import tools.fetch_camoufox as fetch_camoufox


class CamoufoxFetchTests(unittest.TestCase):
    def test_github_api_metadata_request_uses_token(self):
        original_get = Mock(return_value="response")
        wrapped_get = fetch_camoufox.github_authenticated_get(original_get, "token-value")

        result = wrapped_get(
            "https://api.github.com/repos/daijro/camoufox/releases",
            timeout=20,
            headers={"User-Agent": "test"},
        )

        self.assertEqual(result, "response")
        original_get.assert_called_once_with(
            "https://api.github.com/repos/daijro/camoufox/releases",
            timeout=20,
            headers={
                "User-Agent": "test",
                "Authorization": "Bearer token-value",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

    def test_release_asset_download_is_not_given_api_token(self):
        original_get = Mock(return_value="response")
        wrapped_get = fetch_camoufox.github_authenticated_get(original_get, "token-value")

        wrapped_get(
            "https://github.com/daijro/camoufox/releases/download/v1/camoufox.zip",
            stream=True,
        )

        original_get.assert_called_once_with(
            "https://github.com/daijro/camoufox/releases/download/v1/camoufox.zip",
            stream=True,
        )

    def test_existing_authorization_header_is_preserved(self):
        original_get = Mock(return_value="response")
        wrapped_get = fetch_camoufox.github_authenticated_get(original_get, "token-value")

        wrapped_get(
            "https://api.github.com/repos/daijro/camoufox/releases",
            headers={"Authorization": "Bearer caller-token"},
        )

        headers = original_get.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer caller-token")

    def test_main_requires_github_token_before_fetch(self):
        with patch.dict(fetch_camoufox.os.environ, {}, clear=True):
            with patch.object(fetch_camoufox, "CamoufoxUpdate") as update:
                with self.assertRaisesRegex(SystemExit, "GITHUB_TOKEN is required"):
                    fetch_camoufox.main()
        update.assert_not_called()


if __name__ == "__main__":
    unittest.main()
