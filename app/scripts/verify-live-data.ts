import assert from 'node:assert/strict';

import { SUPABASE_ANON, SUPABASE_URL, visibleProducts } from '../lib/catalog';
import { computeSignal, groupHistoryBySku } from '../lib/signals';
import type { PriceHistoryRow, Product, ProductRow } from '../lib/types';

const headers = {
  apikey: SUPABASE_ANON,
  Authorization: `Bearer ${SUPABASE_ANON}`,
};

async function rest<T>(path: string, init: RequestInit = {}) {
  const response = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    ...init,
    headers: {
      ...headers,
      ...(init.headers || {}),
    },
  });
  const text = await response.text();
  if (!response.ok) throw new Error(`HTTP ${response.status} ${path}: ${text.slice(0, 180)}`);
  return {
    data: text ? (JSON.parse(text) as T) : null,
    contentRange: response.headers.get('content-range') || '',
  };
}

async function loadProducts() {
  const pageSize = 1000;
  const rows: ProductRow[] = [];

  for (let offset = 0; ; offset += pageSize) {
    const { data } = await rest<ProductRow[]>(`products?select=*&offset=${offset}&limit=${pageSize}`);
    if (!data?.length) break;
    rows.push(...data);
    if (data.length < pageSize || offset > 50000) break;
  }

  return visibleProducts(rows);
}

async function loadHistory(skuIds: string[]) {
  const encoded = skuIds.map((skuId) => `"${skuId.replaceAll('"', '\\"')}"`).join(',');
  const { data } = await rest<PriceHistoryRow[]>(`price_history?select=sku_id,sale_price,original_price,recorded_at&sku_id=in.(${encoded})&order=recorded_at.asc`);
  return data || [];
}

function cheaperAlternatives(products: Product[], product: Product) {
  const byRegion = new Map<string, Product>();
  for (const candidate of products) {
    if (candidate.model !== product.model || candidate.sku_id === product.sku_id || candidate.region === product.region || candidate.sale_price <= 0 || candidate.sale_price >= product.sale_price) {
      continue;
    }
    const current = byRegion.get(candidate.region);
    if (!current || candidate.sale_price < current.sale_price) byRegion.set(candidate.region, candidate);
  }
  return [...byRegion.values()].sort((a, b) => a.sale_price - b.sale_price);
}

async function main() {
  const { contentRange: productsRange } = await rest<ProductRow[]>('products?select=sku_id&limit=1', {
    headers: { Range: '0-0', Prefer: 'count=exact' },
  });
  const { contentRange: historyRange } = await rest<PriceHistoryRow[]>('price_history?select=sku_id&limit=1', {
    headers: { Range: '0-0', Prefer: 'count=exact' },
  });

  const products = await loadProducts();
  assert.ok(products.length >= 5000, `expected at least 5000 products, got ${products.length}`);

  const deEuro = products.find((product) => product.region === 'de' && product.symbol === '€' && /beta/i.test(`${product.full_name || ''} ${product.model || ''}`));
  assert.ok(deEuro, 'missing DE euro beta sample');

  const betaResults = products.filter((product) => `${product.full_name || ''} ${product.model || ''} ${product.description || ''}`.toLowerCase().includes('beta'));
  assert.ok(betaResults.length > 0, 'beta search should return products');

  const signalProduct = products.find((product) => product.sku_id === 'kopec-mid-gtx-boot-0029_Black_Nightscape_be') || products.find((product) => product.sku_id && product.sale_price > 0);
  assert.ok(signalProduct, 'missing product for signal probe');
  const historyRows = await loadHistory([signalProduct.sku_id]);
  const signal = computeSignal(signalProduct, historyRows);
  assert.ok(['all_time_low', 'ninety_day_low', 'drop_today', 'steady', 'insufficient'].includes(signal.kind));

  const cheaperBase = products.find((product) => product.sku_id === 'kopec-mid-gtx-boot-0029_Black_Nightscape_be') || deEuro;
  assert.ok(cheaperBase, 'missing product for cheaper alternative probe');
  const cheaper = cheaperAlternatives(products, cheaperBase);

  console.log(
    JSON.stringify(
      {
        products_content_range: productsRange,
        price_history_content_range: historyRange,
        paginated_products_loaded: products.length,
        de_euro_beta_sample: {
          sku_id: deEuro.sku_id,
          sale_price: deEuro.sale_price,
          symbol: deEuro.symbol,
          region: deEuro.region,
        },
        beta_result_count: betaResults.length,
        signal_sample: {
          sku_id: signalProduct.sku_id,
          kind: signal.kind,
          label: signal.label,
          history_rows: historyRows.length,
        },
        cheaper_region_sample: {
          base: {
            sku_id: cheaperBase.sku_id,
            region: cheaperBase.region,
            price: cheaperBase.sale_price,
            symbol: cheaperBase.symbol,
          },
          cheaper: cheaper.slice(0, 3).map((product) => ({
            sku_id: product.sku_id,
            region: product.region,
            price: product.sale_price,
            symbol: product.symbol,
          })),
        },
      },
      null,
      2,
    ),
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
