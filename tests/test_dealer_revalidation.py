import unittest
from collections import defaultdict
from unittest.mock import patch

from dealers.revalidate import fetch_rei_pdp, underperforming_dealers
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

    def test_list_fallback_preserves_previous_discount(self):
        self.assertTrue(should_preserve_previous_discount("list_fallback", 200, 200, 100, 200))
        self.assertFalse(should_preserve_previous_discount("api", 200, 200, 49.83, 200))

    def test_low_success_ratio_is_failure(self):
        stats = defaultdict(lambda: {"ok": 0, "unavail": 0})
        stats["evo"]["ok"] = 7
        stats["rei"]["ok"] = 6
        dealers = {"rei": [{}] * 10, "evo": [{}] * 10}
        failed = underperforming_dealers(dealers, stats)
        self.assertEqual(failed, ["rei"])


if __name__ == "__main__":
    unittest.main()
