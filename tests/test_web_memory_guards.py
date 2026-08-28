import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WebMemoryGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.preview = (ROOT / "web-product-preview.js").read_text(encoding="utf-8")
        cls.detail = (ROOT / "product-detail.html").read_text(encoding="utf-8")
        cls.catalog = (ROOT / "app/lib/catalog.ts").read_text(encoding="utf-8")
        cls.names = (ROOT / "arcteryx-names.js").read_text(encoding="utf-8")
        cls.app_names = (ROOT / "app/lib/arcteryx-names.js").read_text(encoding="utf-8")
        cls.brands = (ROOT / "gear-brands.js").read_text(encoding="utf-8")
        cls.app_brands = (ROOT / "app/lib/gear-brands.js").read_text(encoding="utf-8")
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

    def test_homepage_uses_lean_rows_with_only_a_bounded_preview_cache(self):
        self.assertIn(".select(LIST_COLUMNS)", self.index)
        self.assertIn(".range(offset, offset + PAGE - 1)", self.index)
        self.assertIn(".order('sku_id', { ascending: true })", self.index)
        self.assertNotIn(".select('*').range(", self.index)
        self.assertNotIn("localStorage.getItem(CACHE_KEY)", self.index)
        self.assertNotIn("localStorage.setItem(CACHE_KEY", self.index)
        self.assertIn("localStorage.removeItem('products_cache_v1')", self.index)
        self.assertIn("const PRODUCT_PREVIEW_LIMIT = 200;", self.preview)
        self.assertIn(".slice(0, PRODUCT_PREVIEW_LIMIT)", self.preview)
        self.assertIn("value.products.length > PRODUCT_PREVIEW_LIMIT", self.preview)
        self.assertIn("localStorage.getItem(previewCacheKey)", self.index)
        self.assertIn("serializeProductPreviewCache(previewRows, previewRegion)", self.index)
        self.assertNotIn("serializeProductPreviewCache(loadedProducts", self.index)

    def test_homepage_renders_a_preview_before_the_full_catalog(self):
        self.assertIn('<link rel="preconnect" href="https://bupqagkrcvrezjkdbald.supabase.co" crossorigin>', self.index)
        self.assertIn('<script src="web-product-preview.js"></script>', self.index)
        self.assertIn(".limit(PRODUCT_PREVIEW_LIMIT)", self.index)
        self.assertIn("previewQuery.eq('region', previewRegion)", self.index)
        self.assertIn("showProducts(loadedProducts, 'complete')", self.index)
        self.assertIn("document.documentElement.dataset.catalogPhase = phase", self.index)
        preview_render = self.index.index("previewRows.map(decorate)")
        full_loop = self.index.index("for (let offset = 0; ; offset += PAGE)")
        self.assertLess(preview_render, full_loop)

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

    def test_mixed_case_product_names_are_not_treated_as_glued_descriptions(self):
        unsafe_boundary = "match(/^(.+?[a-z])([A-Z].{12,})$/)"
        self.assertNotIn(unsafe_boundary, self.index)
        self.assertNotIn(unsafe_boundary, self.detail)
        self.assertNotIn(unsafe_boundary, self.catalog)
        for token in ("LiTRIC", "SuperLight", "StormHood", "DownWord"):
            self.assertIn(token, self.names)

    def test_web_and_app_use_the_same_model_name_runtime(self):
        self.assertIn('<script src="arcteryx-names.js"></script>', self.index)
        self.assertIn('<script src="arcteryx-names.js"></script>', self.detail)
        self.assertIn("from './arcteryx-names'", self.catalog)
        self.assertEqual(self.names, self.app_names)
        for source in (self.index, self.detail, self.catalog):
            self.assertNotIn("NAME_PREFIX_STRIP", source)

    def test_web_and_app_share_brand_runtime_and_brand_filter(self):
        self.assertEqual(self.brands, self.app_brands)
        for source in (self.index, self.detail):
            self.assertIn('<script src="gear-brands.js"></script>', source)
            self.assertIn("'brand'", source)
            self.assertIn("window.GearBrands", source)
        self.assertIn('id="brand-select"', self.index)
        self.assertIn("from './gear-brands'", self.catalog)
        self.assertIn("_brand: brand", self.catalog)

    def test_burton_sources_have_platform_labels_on_every_surface(self):
        for source in (self.index, self.detail, self.catalog):
            self.assertIn("burton", source)
            self.assertIn("backcountry", source.lower())
        self.assertIn("Burton Outlet", self.index)
        self.assertIn("Backcountry Burton", self.index)

    def test_supported_brand_and_platform_filters_remain_visible_at_zero_count(self):
        self.assertIn("const brandOrder = ['arcteryx', 'burton', 'patagonia'];", self.index)
        self.assertIn("...brandOrder.map(k => ({", self.index)
        self.assertIn("disabled: !brandCounts[k] && state.brand !== k", self.index)
        self.assertIn(
            "const platformOrder = ['arcteryx_outlet','burton','backcountry','ssense','mec','evo','rei'];",
            self.index,
        )
        self.assertIn("disabled: !platformCounts[k] && state.platform !== k", self.index)

    def test_public_pages_use_the_confirmed_geardrop_logo_assets(self):
        for source in (self.index, self.detail, self.support):
            self.assertIn('/assets/brand/geardrop-logo.png', source)
            self.assertIn('/site.webmanifest', source)
        self.assertIn('https://001.100app.dev/assets/brand/geardrop-og.png', self.index)

    def test_homepage_has_truthful_app_download_guidance(self):
        self.assertIn('id="app-download"', self.index)
        self.assertIn('GearDrop 已在 App Store 上线', self.index)
        self.assertIn(
            'https://apps.apple.com/us/app/geardrop-outdoor-deals/id6790165332',
            self.index,
        )
        self.assertIn('https://apps.apple.com/us/app/testflight/id899247664', self.index)
        self.assertIn('已收到专门内测邀请', self.index)
        self.assertNotIn('App Store 即将上线', self.index)

    def test_detail_purchase_cta_names_the_actual_platform(self):
        self.assertIn(
            "function ctaBlock(url, klass = '', platformLabel = '销售平台')",
            self.detail,
        )
        self.assertIn("前往 ${esc(platformLabel)} 购买", self.detail)
        self.assertIn("const platformLabel = inferPlatform(current).label;", self.detail)
        self.assertIn("ctaBlock(ctaUrl, 'cta-inline', platformLabel)", self.detail)

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
