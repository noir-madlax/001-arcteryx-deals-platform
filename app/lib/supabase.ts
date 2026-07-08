import 'react-native-url-polyfill/auto';

import { createClient } from '@supabase/supabase-js';

import { SUPABASE_ANON, SUPABASE_URL, visibleProducts } from './catalog';
import { postPriceAlert } from './priceAlerts';
import type { PriceAlertPayload, PriceHistoryRow, Product, ProductRow } from './types';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON, {
  auth: {
    autoRefreshToken: false,
    detectSessionInUrl: false,
    persistSession: false,
  },
});

export async function fetchAllProducts(onPage?: (rows: Product[]) => void) {
  const pageSize = 1000;
  let all: ProductRow[] = [];

  for (let offset = 0; ; offset += pageSize) {
    const { data, error } = await supabase.from('products').select('*').range(offset, offset + pageSize - 1);
    if (error) throw error;
    if (!data?.length) break;
    all = all.concat(data as ProductRow[]);
    onPage?.(visibleProducts(all));
    if (data.length < pageSize || offset > 50000) break;
  }

  return visibleProducts(all);
}

export async function fetchProductFamilyBySku(skuId: string) {
  const { data: target, error: targetError } = await supabase.from('products').select('url').eq('sku_id', skuId).maybeSingle();
  if (targetError) throw targetError;
  if (!target?.url) {
    const { data, error } = await supabase.from('products').select('*').eq('sku_id', skuId);
    if (error) throw error;
    return visibleProducts((data || []) as ProductRow[]);
  }
  const { data, error } = await supabase.from('products').select('*').eq('url', target.url);
  if (error) throw error;
  return visibleProducts((data || []) as ProductRow[]);
}

export async function fetchPriceHistoryForSkus(skuIds: string[], sinceIso?: string) {
  if (!skuIds.length) return [] as PriceHistoryRow[];
  const rows: PriceHistoryRow[] = [];
  const batchSize = 45;

  for (let i = 0; i < skuIds.length; i += batchSize) {
    const batch = skuIds.slice(i, i + batchSize);
    let query = supabase
      .from('price_history')
      .select('sku_id,sale_price,original_price,recorded_at')
      .in('sku_id', batch)
      .order('recorded_at', { ascending: true });
    if (sinceIso) query = query.gte('recorded_at', sinceIso);
    const { data, error } = await query;
    if (error) throw error;
    rows.push(...((data || []) as PriceHistoryRow[]));
  }

  return rows;
}

export async function fetchPriceHistory(skuId: string, sinceIso?: string) {
  return fetchPriceHistoryForSkus([skuId], sinceIso);
}

export async function insertPriceAlert(payload: PriceAlertPayload) {
  await postPriceAlert(SUPABASE_URL, SUPABASE_ANON, payload);
}
