import unittest

from sku_scraper import color_price_map_from_product_data, price_from_variants


class SkuScraperPriceTests(unittest.TestCase):
    def test_price_map_uses_color_specific_variant_prices(self):
        product = {
            "colourOptions": [
                {"id": "c1", "label": "Blaze"},
                {"id": "c2", "label": "Forage"},
            ],
            "variants": [
                {"colourId": "c1", "price": "600", "discountPrice": "300", "stockStatus": "inStock"},
                {"colourId": "c1", "price": "600", "discountPrice": "300", "stockStatus": "inStock"},
                {"colourId": "c2", "price": "600", "discountPrice": "360", "stockStatus": "inStock"},
                {"colourId": "c2", "price": "600", "discountPrice": "360", "stockStatus": "inStock"},
            ],
        }

        price_map = color_price_map_from_product_data(product)

        self.assertEqual(price_map["Blaze"], (300.0, 600.0))
        self.assertEqual(price_map["Forage"], (360.0, 600.0))
        self.assertEqual(price_from_variants(product, "Blaze"), (300.0, 600.0))
        self.assertEqual(price_from_variants(product, "Forage"), (360.0, 600.0))

    def test_price_map_ignores_out_of_stock_variants(self):
        product = {
            "colourOptions": [{"id": "c1", "label": "Vitality"}],
            "variants": [
                {"colourId": "c1", "price": "600", "discountPrice": "300", "stockStatus": "outOfStock"},
                {"colourId": "c1", "price": "600", "discountPrice": "360", "stockStatus": "inStock"},
            ],
        }

        self.assertEqual(price_from_variants(product, "Vitality"), (360.0, 600.0))


if __name__ == "__main__":
    unittest.main()
