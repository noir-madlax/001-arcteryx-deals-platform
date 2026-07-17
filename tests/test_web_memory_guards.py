import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WebMemoryGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.detail = (ROOT / "product-detail.html").read_text(encoding="utf-8")

    def test_homepage_renders_one_bounded_page(self):
        self.assertIn("const PAGE_SIZE = 60;", self.index)
        self.assertIn("filteredProducts.slice(start, start + PAGE_SIZE)", self.index)
        self.assertIn("grid.innerHTML = pageProducts.map(buildCard).join('');", self.index)
        self.assertNotIn("grid.innerHTML = filtered.map(buildCard).join('');", self.index)
        self.assertIn('id="page-prev"', self.index)
        self.assertIn('id="page-next"', self.index)

    def test_homepage_uses_lean_rows_without_full_table_cache(self):
        self.assertIn(".select(LIST_COLUMNS).range(", self.index)
        self.assertNotIn(".select('*').range(", self.index)
        self.assertNotIn("localStorage.getItem(CACHE_KEY)", self.index)
        self.assertNotIn("localStorage.setItem(CACHE_KEY", self.index)
        self.assertIn("localStorage.removeItem('products_cache_v1')", self.index)

    def test_card_images_are_resized_before_loading(self):
        self.assertIn("url.searchParams.set('w', String(width));", self.index)
        self.assertIn("url.searchParams.set('h', String(height));", self.index)
        self.assertIn("thumbnailUrl(p.image_url)", self.index)
        self.assertIn('width="480" height="600" loading="lazy" decoding="async"', self.index)

    def test_detail_page_does_not_eagerly_load_static_catalog(self):
        self.assertNotIn('<script src="data.js"></script>', self.detail)
        self.assertIn("script.src = 'data.js';", self.detail)
        self.assertIn("if (!skuMatches.length && queryFailed)", self.detail)

    def test_detail_queries_are_server_scoped(self):
        self.assertIn(".select(DETAIL_COLUMNS).eq('url', target.url)", self.detail)
        self.assertIn(".select(DETAIL_COLUMNS).eq('url', url)", self.detail)
        self.assertIn(".select(DETAIL_COLUMNS).ilike('url', `%/${slug}%`).limit(50)", self.detail)
        self.assertNotIn("db.from('products').select('*')", self.detail)


if __name__ == "__main__":
    unittest.main()
