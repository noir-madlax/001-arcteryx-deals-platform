import assert from 'node:assert/strict';
import test from 'node:test';

import { cleanName, inferCategory, normalizeRegion, platformKey, productCategory, regionFlag, releaseSeason, visibleProducts } from '../lib/catalog';
import { product, row } from './helpers';

test('cleanName strips brand prefixes and dashed gender suffixes', () => {
  assert.equal(cleanName("Arc'teryx Beta AR Jacket - Men's"), 'Beta AR Jacket');
  assert.equal(cleanName("Arc'teryx Sentinel Jacket - Women's"), 'Sentinel Jacket');
  assert.equal(cleanName("Der Alpha Pant Women's"), "Alpha Pant Women's");
  assert.equal(cleanName('veilanceSpere LT Jacket'), 'Veilance Spere LT Jacket');
});

test('inferCategory covers key outdoor catalog categories', () => {
  assert.equal(inferCategory('Kopec Mid GTX Boot'), '鞋类');
  assert.equal(inferCategory('Mantis 26 Backpack'), '背包');
  assert.equal(inferCategory('Beta AR Jacket'), '冲锋衣');
  assert.equal(inferCategory('Conveyor Belt'), '配饰');
});

test('releaseSeason reads season codes from product image URLs', () => {
  assert.equal(releaseSeason({ image_url: 'https://cdn.example/F25-X000-Beta.jpg', images: [] }), 'Fall/Winter 2025');
  assert.equal(releaseSeason({ image_url: '', images: ['https://cdn.example/S24-X000-Gamma.jpg'] }), 'Spring/Summer 2024');
  assert.equal(releaseSeason({ image_url: 'https://cdn.example/no-season.jpg', images: [] }), null);
});

test('visibleProducts normalizes rows and filters known unavailable outlet products', () => {
  const visible = visibleProducts([
    row({
      sizes: '["M","L"]',
      size_stock: '{"M":"in_stock","L":"out_of_stock"}',
      images: '["https://cdn.example/beta-2.jpg"]',
    }),
    row({
      id: 2,
      sku_id: 'rush-bib-pant_Black_us',
      url: 'https://outlet.arcteryx.com/us/en/shop/womens/rush-bib-pant',
    }),
    row({
      id: 3,
      sku_id: 'sold-out_Black_us',
      size_stock: { M: 'out_of_stock' },
      sizes: ['M'],
    }),
    row({
      id: 4,
      sku_id: 'alpha-pant_Black_us',
      url: 'https://outlet.arcteryx.com/us/en/shop/womens/alpha-pant',
    }),
    row({
      id: 5,
      sku_id: 'alpha-pant_Black_de',
      url: 'https://outlet.arcteryx.com/de/de/shop/womens/alpha-pant',
    }),
    row({
      id: 6,
      sku_id: 'missing-product_Black_us',
      status: 'missing',
    }),
    row({
      id: 7,
      sku_id: 'gone-product_Black_us',
      url_http_status: 410,
    }),
    row({
      id: 8,
      sku_id: 'stale-product_Black_us',
      last_seen_at: '2026-01-01T00:00:00Z',
    }),
  ]);

  assert.equal(visible.length, 2);
  assert.equal(visible[0]?.sale_price, 300);
  assert.deepEqual(visible[0]?.sizes, ['M', 'L']);
  assert.equal(visible[0]?._series, 'Beta');
  assert.equal(productCategory(visible[0]!), '冲锋衣');
  assert.equal(visible[1]?.sku_id, 'alpha-pant_Black_de');
});

test('platformKey prefers dealer and falls back to URL domains', () => {
  assert.equal(platformKey(row({ dealer: 'mec', url: 'https://example.com' })), 'mec');
  assert.equal(platformKey(row({ dealer: null, url: 'https://www.rei.com/product/123' })), 'rei');
  assert.equal(platformKey(row({ dealer: null, url: 'https://www.ssense.com/en-us/men/product' })), 'ssense');
});

test('productCategory uses catalog category unless it is generic', () => {
  assert.equal(productCategory(product({ category: '鞋类' })), '鞋类');
  assert.equal(productCategory(product({ category: '其他', full_name: 'Mantis 26 Backpack' })), '背包');
});

test('normalizeRegion accepts supported regions and falls back to US', () => {
  assert.equal(normalizeRegion('de'), 'de');
  assert.equal(normalizeRegion('au'), 'au');
  assert.equal(normalizeRegion('CH'), 'ch');
  assert.equal(normalizeRegion('all'), 'all');
  assert.equal(normalizeRegion('xx'), 'us');
  assert.equal(normalizeRegion(null), 'us');
});

test('region presentation covers every live catalog country and has a readable fallback', () => {
  assert.equal(regionFlag('fi'), '🇫🇮');
  assert.equal(regionFlag('ie'), '🇮🇪');
  assert.equal(regionFlag('au'), '🇦🇺');
  assert.equal(regionFlag('all'), '◎');
  assert.equal(regionFlag('xx'), 'XX');
});
