import json
import unittest
from pathlib import Path
from unittest.mock import patch

from dealers.evo import Scraper as EvoScraper
from dealers.mec import Scraper as MecScraper
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

    def test_ssense_list_page_urls_add_pagination(self):
        scraper = SsenseScraper()
        self.assertEqual(
            scraper.list_page_urls("https://www.ssense.com/en-us/men/designers/arcteryx"),
            [
                "https://www.ssense.com/en-us/men/designers/arcteryx",
                "https://www.ssense.com/en-us/men/designers/arcteryx?page=2",
                "https://www.ssense.com/en-us/men/designers/arcteryx?page=3",
                "https://www.ssense.com/en-us/men/designers/arcteryx?page=4",
                "https://www.ssense.com/en-us/men/designers/arcteryx?page=5",
                "https://www.ssense.com/en-us/men/designers/arcteryx?page=6",
            ],
        )

    @patch("curl_cffi.requests.Session")
    def test_ssense_scrape_advances_to_later_pages(self, session_cls):
        session = session_cls.return_value
        session.get.return_value.status_code = 200

        scraper = SsenseScraper()
        scraper.LIST_URLS = ["https://www.ssense.com/en-us/men/designers/arcteryx"]
        scraper.MIN_LIST_ITEMS = 1

        fetched_urls = []
        page_items = {
            "https://www.ssense.com/en-us/men/designers/arcteryx": [
                {"url": "https://www.ssense.com/en-us/men/product/arcteryx/a/1", "name": "A", "sale_price": 100.0, "original_price": 120.0, "currency": "USD", "in_stock": True, "gender": "men"}
            ],
            "https://www.ssense.com/en-us/men/designers/arcteryx?page=2": [
                {"url": "https://www.ssense.com/en-us/men/product/arcteryx/b/2", "name": "B", "sale_price": 90.0, "original_price": 110.0, "currency": "USD", "in_stock": True, "gender": "men"}
            ],
        }

        def fake_fetch(_session, url, retries=4, is_pdp=False):
            del retries, is_pdp
            fetched_urls.append(url)
            return url if url in page_items else ""

        def fake_parse_list(body, page_url):
            self.assertEqual(body, page_url)
            return page_items.get(page_url, [])

        scraper._fetch = fake_fetch
        scraper.parse_list = fake_parse_list

        items = scraper.scrape()
        self.assertEqual([item["url"] for item in items], [
            "https://www.ssense.com/en-us/men/product/arcteryx/a/1",
            "https://www.ssense.com/en-us/men/product/arcteryx/b/2",
        ])
        self.assertIn("https://www.ssense.com/en-us/men/designers/arcteryx?page=2", fetched_urls)
        self.assertTrue(scraper.crawl_complete)

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

    def test_rei_list_urls_paginate_search_results(self):
        scraper = ReiScraper()
        self.assertEqual(
            scraper.list_urls(),
            [
                "https://www.rei.com/search?q=arcteryx",
                "https://www.rei.com/search?q=arcteryx&page=2",
                "https://www.rei.com/search?q=arcteryx&page=3",
                "https://www.rei.com/search?q=arcteryx&page=4",
            ],
        )

    def test_mec_scrapling_fallback_marks_list_prices_as_low_trust(self):
        scraper = MecScraper()
        item = {"url": "https://www.mec.ca/en/product/6030-116/example", "_hit": {"id": 1}}

        with self.subTest("before fallback cleanup"):
            self.assertNotIn("price_source_quality", item)

        item["price_source_quality"] = "list_fallback"
        item.pop("_hit", None)

        self.assertEqual(item["price_source_quality"], "list_fallback")
        self.assertNotIn("_hit", item)

    def test_browser_stack_versions_are_pinned_to_live_working_combo(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("camoufox[geoip]==0.4.11", requirements)
        self.assertIn("playwright==1.58.0", requirements)
        self.assertIn("patchright==1.58.2", requirements)
        self.assertIn("curl_cffi==0.15.0", requirements)


if __name__ == "__main__":
    unittest.main()
