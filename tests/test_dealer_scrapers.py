import json
import unittest
from pathlib import Path

from dealers.evo import Scraper as EvoScraper
from dealers.rei import Scraper as ReiScraper
from dealers.ssense import Scraper as SsenseScraper


ROOT = Path(__file__).resolve().parent.parent


class DealerScraperTests(unittest.TestCase):
    def test_evo_rendered_shopify_snapshot_normalizes_product(self):
        snapshot = {
            "products": [{
                "id": 123,
                "vendor": "Arc'teryx",
                "type": "Shell Jackets",
                "handle": "beta-ar-jacket-men-s",
                "variants": [
                    {
                        "price": 30000,
                        "name": "Arc'teryx Beta AR Jacket - Men's - Black Sapphire / M",
                        "public_title": "Black Sapphire / M",
                    },
                    {
                        "price": 30000,
                        "name": "Arc'teryx Beta AR Jacket - Men's - Black Sapphire / L",
                        "public_title": "Black Sapphire / L",
                    },
                ],
            }],
            "inventory": {"123": {"inventory": 5, "lowestVariantPrice": 22500}},
            "cards": [{
                "url": "https://www.evo.com/products/beta-ar-jacket-men-s",
                "name": "Arc'teryx Beta AR Jacket - Men's",
                "current_price": "Current price $225.00",
                "original_price": "Original price $300.00",
                "image": "https://cdn.example/beta.jpg",
                "colors": ["Black Sapphire"],
            }],
        }
        items = EvoScraper().parse_browser_snapshot(snapshot, "men")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["sale_price"], 225.0)
        self.assertEqual(items[0]["original_price"], 300.0)
        self.assertEqual(items[0]["sizes"], ["L", "M"])
        self.assertEqual(items[0]["discount_pct"], 25)
        self.assertTrue(items[0]["in_stock"])

    def test_ssense_rendered_html_uses_existing_json_ld_parser(self):
        product = {
            "@type": "Product",
            "brand": {"name": "Arc'teryx"},
            "name": "Black Konseal GTX Sneakers",
            "url": "/men/product/arcteryx/black-konseal-gtx-sneakers/17580131",
            "image": ["https://img.example/konseal.jpg"],
            "offers": {
                "price": "220",
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock",
            },
        }
        body = f'<script type="application/ld+json">{json.dumps(product, separators=(",", ":"))}</script>'
        items = SsenseScraper().parse_list(body, "https://www.ssense.com/en-us/men/designers/arcteryx")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["sale_price"], 220.0)
        self.assertIn("/en-us/men/product/", items[0]["url"])
        self.assertEqual(items[0]["price_source_quality"], "list_fallback")

    def test_rei_detail_parser_is_deterministic(self):
        body = (
            '<button class="size-selector__size-button" data-ui="size-selector-button:available">'
            '<span aria-hidden="true">M</span></button>'
            '<button class="color-btn" data-color="BLACK" data-ui="available"></button>'
            '<span class="color-selector-wrapper__selected-color">Black</span>'
        )
        detail = ReiScraper().parse_detail(body)
        self.assertEqual(detail["sizes"], ["M"])
        self.assertEqual(detail["size_stock"], {"M": "in_stock"})
        self.assertEqual(detail["color"], "Black")

    def test_browser_stack_versions_are_pinned_to_live_working_combo(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("camoufox[geoip]==0.4.11", requirements)
        self.assertIn("playwright==1.58.0", requirements)
        self.assertIn("patchright==1.58.2", requirements)
        self.assertIn("curl_cffi==0.15.0", requirements)


if __name__ == "__main__":
    unittest.main()
