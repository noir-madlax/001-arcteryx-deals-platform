import type { PriceAlertPayload, Product } from './types';

export function buildPriceAlertPayload(product: Product, productName: string, email: string, target: number | null, unsubscribeToken: string): PriceAlertPayload {
  return {
    email,
    sku_id: product.sku_id,
    target_price: target,
    last_price_seen: product.sale_price,
    currency: product.currency,
    region: product.region,
    product_name: productName,
    product_url: product.url || '',
    image_url: product.image_url || '',
    unsubscribe_token: unsubscribeToken,
  };
}

export async function postPriceAlert(supabaseUrl: string, supabaseAnon: string, payload: PriceAlertPayload, fetchImpl: typeof fetch = fetch) {
  const response = await fetchImpl(`${supabaseUrl}/rest/v1/price_alerts`, {
    method: 'POST',
    headers: {
      apikey: supabaseAnon,
      Authorization: `Bearer ${supabaseAnon}`,
      'Content-Type': 'application/json',
      Prefer: 'return=minimal',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status}: ${text.slice(0, 140)}`);
  }
}
