import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from global_scraper import fetch_json, next_stable_bottom_rounds


class GlobalScraperScrollTests(unittest.TestCase):
    def test_stability_does_not_advance_before_bottom(self):
        rounds = next_stable_bottom_rounds(
            at_bottom=False,
            count=80,
            height=24000,
            previous_count=80,
            previous_height=24000,
            current_rounds=3,
        )
        self.assertEqual(rounds, 0)

    def test_stability_advances_only_for_same_bottom_state(self):
        rounds = next_stable_bottom_rounds(
            at_bottom=True,
            count=98,
            height=26000,
            previous_count=98,
            previous_height=26000,
            current_rounds=2,
        )
        self.assertEqual(rounds, 3)
        reset = next_stable_bottom_rounds(
            at_bottom=True,
            count=99,
            height=26100,
            previous_count=98,
            previous_height=26000,
            current_rounds=3,
        )
        self.assertEqual(reset, 0)


class OfficialJsonRetryTests(unittest.TestCase):
    @staticmethod
    def response(payload: bytes):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = payload
        return response

    @staticmethod
    def http_error(status: int, retry_after: str | None = None):
        headers = {"Retry-After": retry_after} if retry_after is not None else {}
        return urllib.error.HTTPError(
            "https://arcteryx.com.au/collections/sale/products.json",
            status,
            "test error",
            headers,
            None,
        )

    @patch("global_scraper.time.sleep")
    @patch("global_scraper.urllib.request.urlopen")
    def test_retries_429_then_returns_official_json(self, urlopen, sleep):
        urlopen.side_effect = [
            self.http_error(429, retry_after="7"),
            self.response(b'{"products": [{"id": 1}]}'),
        ]

        payload = fetch_json("https://example.test/products.json", attempts=2)

        self.assertEqual(payload, {"products": [{"id": 1}]})
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(7.0)

    @patch("global_scraper.time.sleep")
    @patch("global_scraper.urllib.request.urlopen")
    def test_uses_bounded_backoff_for_429_without_retry_after(self, urlopen, sleep):
        urlopen.side_effect = [
            self.http_error(429),
            self.http_error(429),
            self.http_error(429),
        ]

        with self.assertRaises(urllib.error.HTTPError):
            fetch_json(
                "https://example.test/products.json",
                attempts=3,
                base_retry_delay=20,
            )

        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [20, 40])

    @patch("global_scraper.time.sleep")
    @patch("global_scraper.urllib.request.urlopen")
    def test_does_not_retry_nontransient_http_error(self, urlopen, sleep):
        urlopen.side_effect = self.http_error(404)

        with self.assertRaises(urllib.error.HTTPError):
            fetch_json("https://example.test/products.json")

        self.assertEqual(urlopen.call_count, 1)
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
