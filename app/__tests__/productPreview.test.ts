import assert from 'node:assert/strict';
import test from 'node:test';

import {
  INITIAL_PRODUCT_LIMIT,
  parseProductPreviewCache,
  PRODUCT_PREVIEW_MAX_AGE_MS,
  serializeProductPreview,
} from '../lib/productPreview';
import { product } from './helpers';

test('product preview cache round-trips a fresh bounded product list', () => {
  const now = Date.parse('2026-08-04T09:00:00.000Z');
  const products = Array.from({ length: INITIAL_PRODUCT_LIMIT + 5 }, (_, index) =>
    product({ sku_id: `preview-${index}`, sale_price: 100 + index }),
  );

  const parsed = parseProductPreviewCache(serializeProductPreview(products, now), now + 1000);

  assert.equal(parsed.length, INITIAL_PRODUCT_LIMIT);
  assert.equal(parsed[0]?.sku_id, 'preview-0');
  assert.equal(parsed.at(-1)?.sku_id, `preview-${INITIAL_PRODUCT_LIMIT - 1}`);
});

test('product preview cache re-normalizes protocol-relative image URLs on upgrade', () => {
  const now = Date.parse('2026-08-27T12:00:00.000Z');
  const cached = product({
    image_url: '//cdn.shopify.com/primary.jpg?v=1',
    images: ['//cdn.shopify.com/alternate.jpg?v=2'],
  });

  const [normalized] = parseProductPreviewCache(serializeProductPreview([cached], now), now + 1000);

  assert.equal(normalized?.image_url, 'https://cdn.shopify.com/primary.jpg?v=1');
  assert.deepEqual(normalized?.images, ['https://cdn.shopify.com/alternate.jpg?v=2']);
});

test('product preview cache rejects expired, future, malformed, and invalid rows', () => {
  const now = Date.parse('2026-08-04T09:00:00.000Z');
  const valid = [product({ sku_id: 'valid-preview' })];

  assert.deepEqual(
    parseProductPreviewCache(serializeProductPreview(valid, now - PRODUCT_PREVIEW_MAX_AGE_MS - 1), now),
    [],
  );
  assert.deepEqual(parseProductPreviewCache(serializeProductPreview(valid, now + 1), now), []);
  assert.deepEqual(parseProductPreviewCache('not json', now), []);
  assert.deepEqual(
    parseProductPreviewCache(
      JSON.stringify({ version: 1, savedAt: now, products: [{ sku_id: '', sale_price: null }] }),
      now,
    ),
    [],
  );
});
