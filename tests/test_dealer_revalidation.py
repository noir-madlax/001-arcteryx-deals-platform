import unittest
from collections import defaultdict
from unittest.mock import patch

from dealers.revalidate import fetch_rei_pdp, zero_successful_dealers
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


def rei_html(price_markup: str) -> str:
    return "<html>" + ("x" * 20000) + price_markup + "</html>"


class DealerRevalidationTests(unittest.TestCase):
    @patch("dealers.revalidate.time.sleep")
    def test_rei_current_buy_box_full_price(self, _sleep):
        page = FakePage([
            RuntimeError("document is changing"),
            rei_html('<span id="buy-box-product-price" class="price-value"> $200.00</span>'),
        ])

        result = fetch_rei_pdp(page, "https://www.rei.com/product/242856/item")

        self.assertEqual(page.wait_until, "domcontentloaded")
        self.assertEqual(result, {
            "sale_price": 200.0,
            "original_price": 200.0,
            "discount_pct": 0,
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

    def test_only_mec_preserves_previous_discount(self):
        self.assertTrue(should_preserve_previous_discount("mec", 200, 200, 100, 200))
        self.assertFalse(should_preserve_previous_discount("rei", 200, 200, 49.83, 200))

    def test_zero_successful_dealer_is_failure(self):
        stats = defaultdict(lambda: {"ok": 0, "unavail": 0})
        stats["evo"]["ok"] = 1
        failed = zero_successful_dealers({"rei": [{}], "evo": [{}]}, stats)
        self.assertEqual(failed, ["rei"])


if __name__ == "__main__":
    unittest.main()
