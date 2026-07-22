import unittest
from collections import defaultdict
from unittest.mock import patch

from dealers.revalidate import (
    _evo_needs_browser_fallback,
    fetch_rei_pdp,
    open_mec_revalidation_session,
    parse_evo_browser_snapshot,
    parse_ssense_html,
    underperforming_dealers,
)
from dealers.supabase_sync import should_preserve_previous_discount


class FakePage:
    def __init__(self, bodies):
        self.bodies = iter(bodies)
        self.wait_until = None

    def goto(self, _url, *, wait_until, timeout):
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


def rei_html(price_markup: str, skus: str = "") -> str:
    return "<html>" + ("x" * 20000) + price_markup + skus + "</html>"


class DealerRevalidationTests(unittest.TestCase):
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

    def test_list_fallback_preserves_existing_discount(self):
        self.assertTrue(should_preserve_previous_discount("mec", "list_fallback", 200, 200, 100, 200))
        self.assertTrue(should_preserve_previous_discount("evo", "list_fallback", 200, 200, 49.83, 200))
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


if __name__ == "__main__":
    unittest.main()
