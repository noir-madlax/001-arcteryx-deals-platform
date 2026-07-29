import unittest

from sku_scraper import (
    color_price_map_from_product_data,
    price_from_variants,
    prune_existing_skus_for_key,
)


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

    def test_prune_existing_skus_for_key_replaces_stale_colors(self):
        sku_map = {
            "spere-pant-9123_Gnosis_us": {
                "sku_id": "spere-pant-9123_Gnosis_us",
                "color": "Gnosis",
                "gender": "men",
                "url": "https://outlet.arcteryx.com/us/en/shop/mens/spere-pant-9123",
            },
            "spere-pant-9123_Passport_us": {
                "sku_id": "spere-pant-9123_Passport_us",
                "color": "Passport",
                "gender": "men",
                "url": "https://outlet.arcteryx.com/us/en/shop/mens/spere-pant-9123",
            },
            "beta-coat-9096_Bliss_ca": {
                "sku_id": "beta-coat-9096_Bliss_ca",
                "color": "Bliss",
                "gender": "women",
                "url": "https://outlet.arcteryx.com/ca/en/shop/womens/beta-coat-9096",
            },
        }

        pruned = prune_existing_skus_for_key(sku_map, "spere-pant-9123::men")

        self.assertEqual(pruned, 2)
        self.assertEqual(list(sku_map), ["beta-coat-9096_Bliss_ca"])


if __name__ == "__main__":
    unittest.main()
