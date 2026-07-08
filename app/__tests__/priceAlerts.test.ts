import assert from 'node:assert/strict';
import test from 'node:test';

import { buildPriceAlertPayload, postPriceAlert } from '../lib/priceAlerts';
import { product } from './helpers';

test('buildPriceAlertPayload preserves the production price alert contract', () => {
  const current = product({
    sku_id: 'alpha-pant_Black_us',
    sale_price: 105,
    currency: 'USD',
    region: 'us',
    url: 'https://outlet.example/alpha-pant',
    image_url: 'https://cdn.example/alpha-pant.jpg',
  });

  assert.deepEqual(buildPriceAlertPayload(current, 'Alpha Pant', 'shopper@example.com', 90, 'token-123'), {
    email: 'shopper@example.com',
    sku_id: 'alpha-pant_Black_us',
    target_price: 90,
    last_price_seen: 105,
    currency: 'USD',
    region: 'us',
    product_name: 'Alpha Pant',
    product_url: 'https://outlet.example/alpha-pant',
    image_url: 'https://cdn.example/alpha-pant.jpg',
    unsubscribe_token: 'token-123',
  });
});

test('buildPriceAlertPayload keeps nullable targets and safe empty URLs', () => {
  const current = product({
    url: null,
    image_url: null,
  });

  const payload = buildPriceAlertPayload(current, 'Beta Jacket', 'shopper@example.com', null, 'token-456');

  assert.equal(payload.target_price, null);
  assert.equal(payload.product_url, '');
  assert.equal(payload.image_url, '');
});

test('postPriceAlert posts to price_alerts without reading rows', async () => {
  const calls: Array<{ url: string; init?: RequestInit }> = [];
  const fetchImpl = (async (url: string | URL | Request, init?: RequestInit) => {
    calls.push({ url: String(url), init });
    return new Response(null, { status: 201 });
  }) as typeof fetch;

  const payload = buildPriceAlertPayload(product(), 'Beta Jacket', 'shopper@example.com', 250, 'token-789');
  await postPriceAlert('https://supabase.example', 'anon-key', payload, fetchImpl);

  assert.equal(calls.length, 1);
  assert.equal(calls[0]!.url, 'https://supabase.example/rest/v1/price_alerts');
  assert.equal(calls[0]!.init?.method, 'POST');
  assert.deepEqual(calls[0]!.init?.headers, {
    apikey: 'anon-key',
    Authorization: 'Bearer anon-key',
    'Content-Type': 'application/json',
    Prefer: 'return=minimal',
  });
  assert.deepEqual(JSON.parse(String(calls[0]!.init?.body)), payload);
});

test('postPriceAlert reports Supabase insert failures without follow-up calls', async () => {
  let calls = 0;
  const fetchImpl = (async () => {
    calls += 1;
    return new Response('row-level security policy', { status: 401 });
  }) as typeof fetch;

  const payload = buildPriceAlertPayload(product(), 'Beta Jacket', 'shopper@example.com', 250, 'token-error');
  await assert.rejects(() => postPriceAlert('https://supabase.example', 'anon-key', payload, fetchImpl), /HTTP 401: row-level security policy/);
  assert.equal(calls, 1);
});
