import assert from 'node:assert/strict';
import test from 'node:test';

import { buildPriceAlertRequest, postPriceAlert } from '../lib/priceAlerts';
import { product } from './helpers';

test('buildPriceAlertRequest sends only user input and the catalog identifier', () => {
  const current = product({
    sku_id: 'alpha-pant_Black_us',
    sale_price: 105,
    currency: 'USD',
    region: 'us',
    url: 'https://outlet.example/alpha-pant',
    image_url: 'https://cdn.example/alpha-pant.jpg',
  });

  assert.deepEqual(buildPriceAlertRequest(current, 'shopper@example.com', 90), {
    email: 'shopper@example.com',
    sku_id: 'alpha-pant_Black_us',
    target_price: 90,
  });
});

test('buildPriceAlertRequest keeps nullable targets', () => {
  const current = product({
    url: null,
    image_url: null,
  });

  const request = buildPriceAlertRequest(current, 'shopper@example.com', null);

  assert.equal(request.target_price, null);
});

test('postPriceAlert calls the hardened registration RPC', async () => {
  const calls: Array<{ url: string; init?: RequestInit }> = [];
  const fetchImpl = (async (url: string | URL | Request, init?: RequestInit) => {
    calls.push({ url: String(url), init });
    return new Response('42', { status: 200, headers: { 'Content-Type': 'application/json' } });
  }) as typeof fetch;

  const request = buildPriceAlertRequest(product(), 'shopper@example.com', 250);
  const alertId = await postPriceAlert('https://supabase.example', 'anon-key', request, fetchImpl);

  assert.equal(alertId, 42);
  assert.equal(calls.length, 1);
  assert.equal(calls[0]!.url, 'https://supabase.example/rest/v1/rpc/register_price_alert');
  assert.equal(calls[0]!.init?.method, 'POST');
  assert.deepEqual(calls[0]!.init?.headers, {
    apikey: 'anon-key',
    Authorization: 'Bearer anon-key',
    'Content-Type': 'application/json',
  });
  assert.deepEqual(JSON.parse(String(calls[0]!.init?.body)), {
    p_email: 'shopper@example.com',
    p_sku_id: request.sku_id,
    p_target_price: 250,
  });
});

test('postPriceAlert reports Supabase insert failures without follow-up calls', async () => {
  let calls = 0;
  const fetchImpl = (async () => {
    calls += 1;
    return new Response('row-level security policy', { status: 401 });
  }) as typeof fetch;

  const request = buildPriceAlertRequest(product(), 'shopper@example.com', 250);
  await assert.rejects(() => postPriceAlert('https://supabase.example', 'anon-key', request, fetchImpl), /HTTP 401: row-level security policy/);
  assert.equal(calls, 1);
});

test('postPriceAlert rejects malformed success responses', async () => {
  const fetchImpl = (async () => new Response('null', { status: 200, headers: { 'Content-Type': 'application/json' } })) as typeof fetch;
  const request = buildPriceAlertRequest(product(), 'shopper@example.com', 250);

  await assert.rejects(
    () => postPriceAlert('https://supabase.example', 'anon-key', request, fetchImpl),
    /invalid response/,
  );
});
