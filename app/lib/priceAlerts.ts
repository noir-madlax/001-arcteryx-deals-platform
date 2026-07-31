import type { PriceAlertRequest, Product } from './types';

export function buildPriceAlertRequest(product: Product, email: string, target: number | null): PriceAlertRequest {
  return {
    email,
    sku_id: product.sku_id,
    target_price: target,
  };
}

export async function postPriceAlert(supabaseUrl: string, supabaseAnon: string, request: PriceAlertRequest, fetchImpl: typeof fetch = fetch) {
  const response = await fetchImpl(`${supabaseUrl}/rest/v1/rpc/register_price_alert`, {
    method: 'POST',
    headers: {
      apikey: supabaseAnon,
      Authorization: `Bearer ${supabaseAnon}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      p_email: request.email,
      p_sku_id: request.sku_id,
      p_target_price: request.target_price,
    }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`HTTP ${response.status}: ${text.slice(0, 140)}`);
  }

  const alertId = Number(await response.json());
  if (!Number.isSafeInteger(alertId) || alertId <= 0) {
    throw new Error('Price alert service returned an invalid response.');
  }
  return alertId;
}
