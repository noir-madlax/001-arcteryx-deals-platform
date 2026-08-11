import assert from 'node:assert/strict';
import test from 'node:test';

import {
  filterYearbookProducts,
  formatCatalogPrice,
  normalizeCatalogProduct,
  yearbookBrands,
  yearbookCategories,
  yearbookYear,
  yearbookYears,
} from '../lib/yearbook';
import type { CatalogProductRow } from '../lib/types';

function arcRow(overrides: Partial<CatalogProductRow> = {}): CatalogProductRow {
  return {
    catalog_product_id: 'arcteryx:x000009715',
    brand_key: 'arcteryx',
    official_product_id: 'X000009715',
    brand: "Arc'teryx",
    catalog_scope: 'full_price',
    market: 'outdoor',
    country: 'us',
    language: 'en',
    name: "Vertex Speed Low Shoe Men's",
    gender: 'men',
    collection: null,
    categories: ['footwear'],
    category_sources: { footwear: 'official_category_feed' },
    list_price: 180,
    list_price_max: 180,
    currency: 'USD',
    color_names: ['Black/Arctic Silk'],
    primary_colors: ['Black'],
    season_codes: ['S25', 'F26'],
    source_name: 'arcteryx_us_official_product_feed',
    source_url: 'https://arcteryx.com/us/en/shop/mens/vertex-speed-low-shoe-9715',
    source_hash: 'a'.repeat(64),
    status: 'active',
    first_seen_at: '2026-08-04T10:00:00Z',
    last_seen_at: '2026-08-04T10:00:00Z',
    last_changed_at: '2026-08-04T10:00:00Z',
    ...overrides,
  };
}

function burtonRow(overrides: Partial<CatalogProductRow> = {}): CatalogProductRow {
  return {
    ...arcRow(),
    catalog_product_id: 'burton:106881',
    brand_key: 'burton',
    official_product_id: '106881',
    brand: 'Burton',
    market: 'snow',
    name: "Men's Burton Custom Camber Snowboard",
    categories: ['boards'],
    category_sources: { boards: 'official_shopify_product_type' },
    list_price: 699.95,
    list_price_max: 699.95,
    color_names: ['Graphic'],
    primary_colors: [],
    season_codes: [],
    source_name: 'burton_us_official_collection_json',
    source_url: 'https://www.burton.com/en-us/products/mens-burton-custom-camber-snowboard-106881',
    first_seen_at: '2025-05-01T00:00:00Z',
    ...overrides,
  };
}

function patagoniaRow(overrides: Partial<CatalogProductRow> = {}): CatalogProductRow {
  return {
    ...arcRow(),
    catalog_product_id: 'patagonia:37996',
    brand_key: 'patagonia',
    official_product_id: '37996',
    brand: 'Patagonia',
    country: 'au',
    name: 'Airfarer Cap',
    gender: 'unisex',
    categories: ['headwear', 'caps'],
    category_sources: { headwear: 'official_shopify_tag:type', caps: 'official_shopify_tag:subtype' },
    list_price: 49.95,
    list_price_max: 54.95,
    currency: 'AUD',
    color_names: ['P-6 Logo: Weathered Stone', 'Strata Stencil: Black'],
    primary_colors: ['Green', 'Black'],
    season_codes: ['W26'],
    source_name: 'patagonia_au_official_collection_json',
    source_url: 'https://www.patagonia.com.au/products/airfarer-cap-37996-plws',
    ...overrides,
  };
}

test('normalizes all three official source contracts and Supabase arrays', () => {
  const arc = normalizeCatalogProduct(arcRow({ categories: '["footwear","trail"]', list_price: '180' }));
  const burton = normalizeCatalogProduct(burtonRow());
  const patagonia = normalizeCatalogProduct(patagoniaRow());

  assert.ok(arc && burton && patagonia);
  assert.deepEqual(arc.categories, ['footwear', 'trail']);
  assert.equal(burton.brand_key, 'burton');
  assert.equal(patagonia.currency, 'AUD');
});

test('rejects cross-brand identities, third-party links, inactive rows, and invalid prices', () => {
  assert.equal(normalizeCatalogProduct(burtonRow({ source_url: 'https://www.backcountry.com/burton' })), null);
  assert.equal(normalizeCatalogProduct(burtonRow({ catalog_product_id: 'patagonia:106881' })), null);
  assert.equal(normalizeCatalogProduct(patagoniaRow({ country: 'us' })), null);
  assert.equal(normalizeCatalogProduct(arcRow({ status: 'inactive' })), null);
  assert.equal(normalizeCatalogProduct(arcRow({ list_price_max: 100 })), null);
  assert.equal(normalizeCatalogProduct(arcRow({ source_hash: 'not-a-hash' })), null);
  assert.equal(normalizeCatalogProduct(arcRow({ first_seen_at: 'not-a-date' })), null);
});

test('uses official season codes as year and first-seen as fallback', () => {
  const arc = normalizeCatalogProduct(arcRow());
  const patagonia = normalizeCatalogProduct(patagoniaRow());
  const burton = normalizeCatalogProduct(burtonRow({ first_seen_at: '2025-05-01T00:00:00Z' }));
  assert.ok(arc && patagonia && burton);
  assert.equal(yearbookYear(arc), 2026);
  assert.equal(yearbookYear(patagonia), 2026);
  assert.equal(yearbookYear(burton), 2025);
});

test('filters independently by brand, text, gender, category, and year', () => {
  const arc = normalizeCatalogProduct(arcRow());
  const burton = normalizeCatalogProduct(burtonRow());
  const patagonia = normalizeCatalogProduct(patagoniaRow());
  assert.ok(arc && burton && patagonia);
  const products = [arc, burton, patagonia];

  assert.deepEqual(filterYearbookProducts(products, { query: 'strata' }).map((item) => item.catalog_product_id), ['patagonia:37996']);
  assert.deepEqual(filterYearbookProducts(products, { brand: 'burton' }).map((item) => item.catalog_product_id), ['burton:106881']);
  assert.deepEqual(filterYearbookProducts(products, { gender: 'unisex' }).map((item) => item.catalog_product_id), ['patagonia:37996']);
  assert.deepEqual(filterYearbookProducts(products, { category: 'footwear' }).map((item) => item.catalog_product_id), ['arcteryx:x000009715']);
  assert.deepEqual(filterYearbookProducts(products, { year: 2025 }).map((item) => item.catalog_product_id), ['burton:106881']);
  assert.deepEqual(yearbookBrands(products), ['arcteryx', 'burton', 'patagonia']);
  assert.deepEqual(yearbookYears(products), [2026, 2025]);
  assert.deepEqual(yearbookCategories(products), ['boards', 'caps', 'footwear', 'headwear']);
});

test('formats single and ranged prices in each source currency', () => {
  const burton = normalizeCatalogProduct(burtonRow());
  const patagonia = normalizeCatalogProduct(patagoniaRow());
  assert.ok(burton && patagonia);
  assert.match(formatCatalogPrice(burton), /699\.95/);
  assert.match(formatCatalogPrice(patagonia), /49\.95.*54\.95/);
});
