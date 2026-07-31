import assert from 'node:assert/strict';
import test from 'node:test';

import { availableDealRegions, DEFAULT_DEAL_FILTERS, filterDeals } from '../lib/deals';
import { product } from './helpers';

const products = [
  product({ sku_id: 'beta-us', region: 'us', sale_price: 300, discount_pct: 25 }),
  product({ sku_id: 'beta-ca', region: 'ca', sale_price: 350, discount_pct: 30, symbol: 'C$', currency: 'CAD' }),
  product({ sku_id: 'beta-de', region: 'de', sale_price: 280, discount_pct: 35, symbol: '€', currency: 'EUR' }),
];

test('region filtering returns deals for each loaded country', () => {
  assert.deepEqual(filterDeals(products, 'ca', '', DEFAULT_DEAL_FILTERS).map((item) => item.sku_id), ['beta-ca']);
  assert.deepEqual(filterDeals(products, 'de', '', DEFAULT_DEAL_FILTERS).map((item) => item.sku_id), ['beta-de']);
  assert.deepEqual(filterDeals(products, 'all', '', DEFAULT_DEAL_FILTERS).map((item) => item.sku_id), ['beta-de', 'beta-ca', 'beta-us']);
});

test('region menu only includes countries present in the loaded catalog', () => {
  assert.deepEqual(availableDealRegions(products), ['all', 'us', 'ca', 'de']);
  assert.equal(availableDealRegions(products).includes('jp'), false);
});

test('search and secondary filters still apply within the selected country', () => {
  assert.equal(filterDeals(products, 'de', 'beta', DEFAULT_DEAL_FILTERS).length, 1);
  assert.equal(filterDeals(products, 'de', 'gamma', DEFAULT_DEAL_FILTERS).length, 0);
  assert.equal(filterDeals(products, 'de', '', { ...DEFAULT_DEAL_FILTERS, platform: 'mec' }).length, 0);
});
