import unittest
from collections import defaultdict
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from dealers.revalidate import (
    _camoufox_geoip_candidates,
    _chunks,
    _evo_choose_more_informative_price,
    _evo_needs_browser_fallback,
    _evo_should_confirm_with_browser,
    _format_error,
    fetch_evo_pdp_browser,
    fetch_evo_pdp_browser_with_retry,
    fetch_rei_pdp,
    fetch_ssense_pdp_browser_with_retry,
    open_camoufox_browser,
    open_mec_revalidation_session,
    parse_evo_browser_snapshot,
    parse_ssense_html,
    quarantine_invalid_price_row,
    requested_dealers,
    requested_sku_ids,
    underperforming_dealers,
    update_row,
)
from dealers.supabase_sync import should_preserve_previous_discount


class FakePage:
    def __init__(self, bodies, final_url=None):
        self.bodies = iter(bodies)
        self.final_url = final_url
        self.wait_until = None

    def goto(self, _url, *, wait_until, timeout):
        self.url = self.final_url or _url
        self.wait_until = wait_until
        self.timeout = timeout

    def content(self):
        value = next(self.bodies)
        if isinstance(value, Exception):
            raise value
        return value


class FakeBrowserSession:
    def __init__(self):
        self.fetch_calls = []

    def fetch(self, url, timeout=0):
        self.fetch_calls.append((url, timeout))
        return object()


class FakeBrowserContext:
    def __init__(self, session):
        self.session = session
        self.closed = False
        self.kwargs = None

    def __call__(self, **kwargs):
        self.kwargs = kwargs
        return self

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc, tb):
        self.closed = True


class FakeEvoPage:
    def __init__(self, snapshot=None):
        self.snapshot = snapshot or {}
        self.closed = False
        self.goto_url = None
        self.wait_ms = None

    def set_default_navigation_timeout(self, timeout):
        self.navigation_timeout = timeout

    def goto(self, url, *, wait_until, timeout):
        self.goto_url = url
        self.wait_until = wait_until
        self.timeout = timeout
        return SimpleNamespace(status=200)

    def wait_for_timeout(self, wait_ms):
        self.wait_ms = wait_ms

    def evaluate(self, _script):
        return self.snapshot

    def close(self):
        self.closed = True


class FakeEvoBrowser:
    def __init__(self, pages):
        self.pages = iter(pages)

    def new_page(self):
        return next(self.pages)


def rei_html(price_markup: str, skus: str = "") -> str:
    return "<html>" + ("x" * 20000) + price_markup + skus + "</html>"


class DealerRevalidationTests(unittest.TestCase):
    def test_successful_pdp_read_reactivates_lifecycle(self):
        client = MagicMock()
        old_row = {
            "sale_price": 80.0,
            "original_price": 80.0,
            "status": "inactive",
            "missing_runs": 2,
        }

        changed = update_row(
            client,
            "rei:249631",
            {"sale_price": 80.0, "original_price": 80.0, "discount_pct": 0},
            old_row,
        )

        self.assertTrue(changed)
        payload = client.table.return_value.update.call_args.args[0]
        self.assertEqual(payload["status"], "active")
        self.assertEqual(payload["missing_runs"], 0)
        self.assertEqual(payload["url_http_status"], 200)
        self.assertEqual(payload["last_seen_at"], payload["last_updated"])
        self.assertEqual(payload["url_checked_at"], payload["last_updated"])

    def test_invalid_price_order_is_never_persisted(self):
        client = MagicMock()

        changed = update_row(
            client,
            "rei:255689",
            {"sale_price": 186.93, "original_price": 180.0, "discount_pct": 0},
            {"sale_price": 186.93, "original_price": 180.0},
        )

        self.assertFalse(changed)
        client.table.assert_not_called()

    def test_invalid_active_price_can_be_quarantined_without_price_write(self):
        client = MagicMock()
        row = {
            "sku_id": "rei:255689",
            "sale_price": 186.93,
            "original_price": 180.0,
            "status": "active",
            "missing_runs": 0,
        }

        quarantined = quarantine_invalid_price_row(client, row, "product_redirect")

        self.assertTrue(quarantined)
        payload = client.table.return_value.update.call_args.args[0]
        self.assertEqual(payload, {"status": "missing", "missing_runs": 1})
        self.assertNotIn("sale_price", payload)
        self.assertNotIn("original_price", payload)
        self.assertNotIn("last_updated", payload)

    def test_camoufox_auto_geoip_falls_back_only_after_startup_failure(self):
        attempts = []

        class BrowserContext:
            def __init__(self, geoip):
                self.geoip = geoip
                self.closed = False

            def __enter__(self):
                if self.geoip:
                    raise RuntimeError("InvalidIP")
                return "browser"

            def __exit__(self, _exc_type, _exc, _traceback):
                self.closed = True

        def factory(**kwargs):
            attempts.append(kwargs)
            return BrowserContext(kwargs["geoip"])

        with patch.dict("os.environ", {"CAMOUFOX_GEOIP": "auto"}):
            with open_camoufox_browser(factory=factory) as browser:
                self.assertEqual(browser, "browser")

        self.assertEqual([attempt["geoip"] for attempt in attempts], [True, False])
        self.assertTrue(all(attempt["humanize"] for attempt in attempts))

    def test_camoufox_explicit_geoip_setting_does_not_fallback(self):
        self.assertEqual(_camoufox_geoip_candidates(True), [True])
        self.assertEqual(_camoufox_geoip_candidates(False), [False])

    def test_runtime_error_preserves_exception_detail(self):
        message = _format_error("goto", RuntimeError("connection closed"))
        self.assertEqual(message, "goto RuntimeError: connection closed")

    def test_requested_dealers_accepts_only_supported_subset(self):
        self.assertEqual(
            requested_dealers(" REI,mec,ssense "),
            {"rei", "mec", "ssense"},
        )
        self.assertIsNone(requested_dealers(""))
        with self.assertRaisesRegex(ValueError, "unsupported.*outlet"):
            requested_dealers("rei,outlet")

    def test_requested_sku_ids_builds_bounded_exact_allowlist(self):
        self.assertEqual(
            requested_sku_ids("rei:243326\nssense:17580131"),
            {"rei:243326", "ssense:17580131"},
        )
        self.assertIsNone(requested_sku_ids(""))
        with self.assertRaisesRegex(ValueError, "limited to 100"):
            requested_sku_ids(",".join(f"rei:{index}" for index in range(101)))

    @patch("dealers.revalidate.time.sleep")
    def test_rei_current_buy_box_full_price(self, _sleep):
        page = FakePage([
            RuntimeError("document is changing"),
            "<html>akamai transition</html>",
            rei_html(
                '<span id="buy-box-product-price" class="price-value"> $200.00</span>',
                '"skus":[{"skuId":"2428560001","status":"AVAILABLE","price":'
                '{"compareAt":{"value":200.0},"price":{"value":200.0}}}]',
            ),
        ])

        result = fetch_rei_pdp(page, "https://www.rei.com/product/242856/item")

        self.assertEqual(page.wait_until, "domcontentloaded")
        self.assertEqual(result, {
            "sale_price": 200.0,
            "original_price": 200.0,
            "discount_pct": 0,
        })

    @patch("dealers.revalidate.time.sleep")
    def test_rei_structured_variant_preserves_compare_at_price(self, _sleep):
        page = FakePage([rei_html(
            '<span id="buy-box-product-price">$59.83</span>',
            '"skus":['
            '{"skuId":"2092520001","status":"AVAILABLE","price":'
            '{"compareAt":{"value":120.0},"price":{"value":59.83}}},'
            '{"skuId":"2092520002","status":"UNAVAILABLE","price":'
            '{"compareAt":{"value":120.0},"price":{"value":39.83}}}'
            ']',
        )])

        result = fetch_rei_pdp(page, "https://www.rei.com/product/209252/item")

        self.assertEqual(result, {
            "sale_price": 59.83,
            "original_price": 120.0,
            "discount_pct": 50,
        })

    @patch("dealers.revalidate.time.sleep")
    def test_rei_legacy_sale_markup_still_wins(self, _sleep):
        page = FakePage([rei_html(
            '<span data-ui="sale-price">$49.83</span>'
            '<span data-ui="full-price">- $200.00</span>'
            '<span id="buy-box-product-price">$49.83</span>'
        )])

        result = fetch_rei_pdp(page, "https://www.rei.com/product/242856/item")

        self.assertEqual(result, {
            "sale_price": 49.83,
            "original_price": 200.0,
            "discount_pct": 75,
        })

    @patch("dealers.revalidate.time.sleep")
    def test_rei_product_redirect_is_not_parsed_as_a_pdp(self, _sleep):
        page = FakePage(
            [rei_html(
                '<span data-ui="sale-price">$186.93</span>'
                '<span data-ui="full-price">$180.00</span>'
            )],
            final_url="https://www.rei.com/b/arcteryx/c/day-packs",
        )

        result = fetch_rei_pdp(
            page,
            "https://www.rei.com/product/255689/arcteryx-mantis-16-pack",
        )

        self.assertEqual(result, {"_err": "product_redirect"})

    def test_list_fallback_preserves_existing_discount(self):
        self.assertTrue(should_preserve_previous_discount("mec", "list_fallback", 200, 200, 100, 200))
        self.assertTrue(should_preserve_previous_discount("evo", "list_fallback", 200, 200, 49.83, 200))
        self.assertTrue(should_preserve_previous_discount("rei", "list_fallback", 125.93, 200, 125.93, 180))
        self.assertTrue(should_preserve_previous_discount("evo", "list_fallback", 450, 600, 379.99, 600))
        self.assertTrue(should_preserve_previous_discount("rei", "list_fallback", 129.93, 180, 125.93, 180))
        self.assertFalse(should_preserve_previous_discount("rei", "list_fallback", 119.93, 180, 125.93, 180))
        self.assertFalse(should_preserve_previous_discount("mec", "api", 200, 200, 49.83, 200))

    def test_mec_revalidation_session_uses_scrapling_when_warm_fails(self):
        browser_session = FakeBrowserSession()
        browser_factory = FakeBrowserContext(browser_session)

        session, cleanup, source = open_mec_revalidation_session(
            session_factory=lambda: object(),
            warm_fn=lambda _session: False,
            browser_session_factory=browser_factory,
            browser_shim_factory=lambda session: session,
            warm_url="https://www.mec.ca/en/",
        )

        self.assertEqual(source, "scrapling")
        self.assertIsNotNone(cleanup)
        self.assertEqual(browser_session.fetch_calls, [("https://www.mec.ca/en/", 90000)])
        cleanup.__exit__(None, None, None)
        self.assertTrue(browser_factory.closed)

    def test_low_success_ratio_is_failure(self):
        stats = defaultdict(lambda: {"ok": 0, "unavail": 0})
        stats["evo"]["ok"] = 7
        stats["rei"]["ok"] = 6
        dealers = {"rei": [{}] * 10, "evo": [{}] * 10}
        failed = underperforming_dealers(dealers, stats)
        self.assertEqual(failed, ["rei"])

    def test_quarantined_invalid_row_counts_as_bounded_coverage(self):
        stats = defaultdict(lambda: {"ok": 0, "unavail": 0, "quarantined": 0})
        stats["rei"]["quarantined"] = 1

        self.assertEqual(underperforming_dealers({"rei": [{}]}, stats), [])

    def test_evo_browser_snapshot_uses_lowest_available_variant(self):
        snapshot = {
            "ShopifyAnalytics": {"meta": {"product": {"id": 1}}},
            "igProductData": {"1": {"lowestVariantPrice": 28000}},
            "RegiosDOPP_ProductPage": {
                "variants": [
                    {"priceInCents": 40000, "compareAtPriceInCents": 40000, "isOutOfStock": True},
                    {"priceInCents": 28000, "compareAtPriceInCents": 40000, "isOutOfStock": False},
                    {"priceInCents": 32000, "compareAtPriceInCents": 40000, "isOutOfStock": False},
                ]
            },
        }

        result = parse_evo_browser_snapshot(snapshot, "https://www.evo.com/products/test")

        self.assertEqual(result, {
            "sale_price": 280.0,
            "original_price": 400.0,
            "discount_pct": 30,
        })

    def test_evo_browser_fallback_triggers_on_any_non_successful_direct_result(self):
        self.assertTrue(_evo_needs_browser_fallback(None))
        self.assertTrue(_evo_needs_browser_fallback({"_err": "http HTTPError"}))
        self.assertFalse(_evo_needs_browser_fallback({"_unavailable": True}))
        self.assertFalse(_evo_needs_browser_fallback({
            "sale_price": 280.0,
            "original_price": 400.0,
            "discount_pct": 30,
        }))

    def test_evo_browser_confirmation_targets_every_usable_direct_result(self):
        self.assertTrue(_evo_should_confirm_with_browser({
            "sale_price": 180.0,
            "original_price": 180.0,
            "discount_pct": 0,
        }))
        self.assertTrue(_evo_should_confirm_with_browser({
            "sale_price": 119.99,
            "original_price": 180.0,
            "discount_pct": 33,
        }))
        self.assertFalse(_evo_should_confirm_with_browser({"_err": "http HTTPError"}))

    def test_evo_browser_price_overrides_flat_direct_snapshot_when_discounted(self):
        direct = {
            "sale_price": 180.0,
            "original_price": 180.0,
            "discount_pct": 0,
        }
        browser = {
            "sale_price": 119.99,
            "original_price": 180.0,
            "discount_pct": 33,
        }

        self.assertEqual(_evo_choose_more_informative_price(direct, browser), browser)
        self.assertEqual(
            _evo_choose_more_informative_price(direct, {"_err": "goto TimeoutError"}),
            {"_err": "browser_confirmation_failed:goto TimeoutError"},
        )

    def test_evo_browser_price_overrides_shallower_direct_discount(self):
        direct = {
            "sale_price": 450.0,
            "original_price": 600.0,
            "discount_pct": 25,
        }
        browser = {
            "sale_price": 379.99,
            "original_price": 600.0,
            "discount_pct": 37,
        }

        self.assertEqual(_evo_choose_more_informative_price(direct, browser), browser)

    def test_evo_combines_browser_sale_with_direct_regular_price(self):
        direct = {
            "sale_price": 850.0,
            "original_price": 850.0,
            "discount_pct": 0,
        }
        browser = {
            "sale_price": 679.99,
            "original_price": 679.99,
            "discount_pct": 0,
        }

        self.assertEqual(
            _evo_choose_more_informative_price(direct, browser),
            {
                "sale_price": 679.99,
                "original_price": 850.0,
                "discount_pct": 20,
            },
        )

    @patch.dict("os.environ", {"EVO_BROWSER_SETTLE_SECONDS": "3"})
    def test_evo_browser_fetch_uses_fresh_url_and_waits_for_runtime_price(self):
        snapshot = {
            "ShopifyAnalytics": {"meta": {"product": {"id": 1}}},
            "igProductData": {"1": {"lowestVariantPrice": 4200}},
            "RegiosDOPP_ProductPage": {
                "variants": [
                    {
                        "priceInCents": 4200,
                        "compareAtPriceInCents": 6000,
                        "isOutOfStock": False,
                    }
                ]
            },
        }
        page = FakeEvoPage(snapshot)

        result = fetch_evo_pdp_browser(page, "https://www.evo.com/products/test")

        self.assertEqual(result["sale_price"], 42.0)
        self.assertIn("price_revalidate=", page.goto_url)
        self.assertEqual(page.wait_until, "commit")
        self.assertEqual(page.wait_ms, 3000)

    @patch("dealers.revalidate.time.sleep")
    @patch.dict(
        "os.environ",
        {
            "EVO_BROWSER_CONFIRM_ATTEMPTS": "2",
            "EVO_BROWSER_RETRY_DELAY_SECONDS": "0",
        },
    )
    def test_evo_browser_confirmation_retries_with_a_fresh_page(self, _sleep):
        first = FakeEvoPage()
        second = FakeEvoPage()
        browser = FakeEvoBrowser([first, second])
        expected = {
            "sale_price": 42.0,
            "original_price": 60.0,
            "discount_pct": 30,
        }

        with patch(
            "dealers.revalidate.fetch_evo_pdp_browser",
            side_effect=[{"_err": "http 429"}, expected],
        ):
            result = fetch_evo_pdp_browser_with_retry(
                browser,
                "https://www.evo.com/products/test",
            )

        self.assertEqual(result, expected)
        self.assertTrue(first.closed)
        self.assertTrue(second.closed)

    @patch("dealers.revalidate.time.sleep")
    @patch.dict(
        "os.environ",
        {
            "EVO_BROWSER_CONFIRM_ATTEMPTS": "2",
            "EVO_BROWSER_RETRY_DELAY_SECONDS": "0",
        },
    )
    def test_evo_browser_confirmation_retries_flat_discount_snapshot(self, _sleep):
        first = FakeEvoPage()
        second = FakeEvoPage()
        browser = FakeEvoBrowser([first, second])
        flat = {
            "sale_price": 600.0,
            "original_price": 600.0,
            "discount_pct": 0,
        }
        discounted = {
            "sale_price": 600.0,
            "original_price": 800.0,
            "discount_pct": 25,
        }

        with patch(
            "dealers.revalidate.fetch_evo_pdp_browser",
            side_effect=[flat, discounted],
        ):
            result = fetch_evo_pdp_browser_with_retry(
                browser,
                "https://www.evo.com/products/test",
                retry_flat=True,
            )

        self.assertEqual(result, discounted)
        self.assertTrue(first.closed)
        self.assertTrue(second.closed)

    def test_browser_rotation_chunks_cover_every_row(self):
        chunks = list(_chunks(list(range(65)), 30))

        self.assertEqual([start for start, _rows in chunks], [0, 30, 60])
        self.assertEqual([len(rows) for _start, rows in chunks], [30, 30, 5])

    def test_ssense_html_extracts_sale_and_original(self):
        html = """
        <html><body>
        <script type="application/ld+json">
        {"@context":"https://schema.org","@type":"Product","offers":{"price":160,"priceCurrency":"USD"}}
        </script>
        <span class="line-through">$200 USD</span>
        </body></html>
        """

        result = parse_ssense_html(html)

        self.assertEqual(result, {
            "sale_price": 160.0,
            "original_price": 200.0,
            "discount_pct": 20,
        })

    def test_ssense_html_prefers_pdp_price_markers_over_page_wide_line_through(self):
        html = """
        <html><body>
        <span class="line-through">$300 USD</span>
        <script type="application/ld+json">
        {"@context":"https://schema.org","@type":"Product","offers":{"price":160,"priceCurrency":"USD"}}
        </script>
        <span data-test="salePriceText">$160 USD</span>
        <span data-test="regularPriceText">$220 USD</span>
        </body></html>
        """

        result = parse_ssense_html(html)

        self.assertEqual(result, {
            "sale_price": 160.0,
            "original_price": 220.0,
            "discount_pct": 27,
        })

    @patch("dealers.revalidate.time.sleep")
    @patch.dict(
        "os.environ",
        {
            "SSENSE_BROWSER_CONFIRM_ATTEMPTS": "2",
            "SSENSE_BROWSER_RETRY_DELAY_SECONDS": "0",
        },
    )
    def test_ssense_browser_retries_flat_discount_snapshot(self, _sleep):
        flat = {
            "sale_price": 80.0,
            "original_price": 80.0,
            "discount_pct": 0,
        }
        discounted = {
            "sale_price": 80.0,
            "original_price": 300.0,
            "discount_pct": 73,
        }

        with patch(
            "dealers.revalidate.fetch_ssense_pdp_browser",
            side_effect=[flat, discounted],
        ):
            result = fetch_ssense_pdp_browser_with_retry(
                object(),
                "https://www.ssense.com/en-us/men/product/test",
                retry_flat=True,
            )

        self.assertEqual(result, discounted)


if __name__ == "__main__":
    unittest.main()
