import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WebMemoryGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.detail = (ROOT / "product-detail.html").read_text(encoding="utf-8")
        cls.catalog = (ROOT / "app/lib/catalog.ts").read_text(encoding="utf-8")
        cls.support = (ROOT / "support.html").read_text(encoding="utf-8")
        cls.submission_migration = (
            ROOT
            / "supabase"
            / "migrations"
            / "20260719161928_geardrop_submission_security.sql"
        ).read_text(encoding="utf-8").lower()

    def test_finland_and_ireland_are_mapped_on_all_catalog_surfaces(self):
        for region, label in (("fi", "芬兰"), ("ie", "爱尔兰")):
            self.assertIn(f"{region}:'{label}'", self.index)
            self.assertIn(f"{region}:'{label}'", self.detail)
        self.assertIn("fi: 'Finland'", self.catalog)
        self.assertIn("ie: 'Ireland'", self.catalog)
        self.assertIn("'fi', 'ie'", self.catalog)

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

    def test_public_submission_surfaces_use_hardened_rpcs(self):
        self.assertIn("/rest/v1/rpc/register_price_alert", self.detail)
        self.assertNotIn("/rest/v1/price_alerts", self.detail)
        self.assertNotIn("unsubscribe_token", self.detail)
        self.assertIn("/rest/v1/rpc/submit_support_request", self.support)
        self.assertIn("p_website", self.support)
        self.assertIn('href="/support.html"', self.index)

    def test_submission_migration_is_self_contained_and_closes_direct_access(self):
        migration = self.submission_migration
        self.assertIn("create table if not exists public.price_alerts", migration)
        self.assertIn("create table if not exists public.support_requests", migration)
        self.assertIn("create or replace function public.register_price_alert", migration)
        self.assertIn("create or replace function public.submit_support_request", migration)
        self.assertIn(
            "revoke all on table public.price_alerts from public, anon, authenticated",
            migration,
        )
        self.assertIn(
            "revoke all on table public.support_requests from public, anon, authenticated",
            migration,
        )
        self.assertIn(
            "grant execute on function public.register_price_alert(text, text, numeric) "
            "to anon, authenticated, service_role",
            migration,
        )
        self.assertIn(
            "grant execute on function public.submit_support_request(text, text, text, text, text) "
            "to anon, authenticated, service_role",
            migration,
        )


if __name__ == "__main__":
    unittest.main()
