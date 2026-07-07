import type { Product, WatchEntry } from './types';

export const WATCHLIST_STORAGE_KEY = 'geardrop.watchlist.v1';
export const FREE_WATCHLIST_LIMIT = 20;

type WatchProduct = Pick<Product, 'sku_id' | 'sale_price' | 'symbol'>;

export function parseWatchEntries(raw: string | null) {
  if (!raw) return [] as WatchEntry[];
  try {
    const entries = JSON.parse(raw) as WatchEntry[];
    return Array.isArray(entries) ? entries : [];
  } catch {
    return [];
  }
}

export function makeWatchEntry(product: WatchProduct, nowIso = new Date().toISOString()): WatchEntry {
  return {
    skuId: product.sku_id,
    savedAt: nowIso,
    savedPrice: product.sale_price,
    symbol: product.symbol,
  };
}

export function toggleWatchEntry(entries: WatchEntry[], product: WatchProduct, isPro: boolean, nowIso = new Date().toISOString()) {
  if (entries.some((entry) => entry.skuId === product.sku_id)) {
    return {
      accepted: true,
      entries: entries.filter((entry) => entry.skuId !== product.sku_id),
    };
  }

  if (!isPro && entries.length >= FREE_WATCHLIST_LIMIT) {
    return {
      accepted: false,
      entries,
    };
  }

  return {
    accepted: true,
    entries: [makeWatchEntry(product, nowIso), ...entries],
  };
}

export function setWatchAlertTarget(entries: WatchEntry[], product: WatchProduct, target: number | null, nowIso = new Date().toISOString()) {
  const existing = entries.find((entry) => entry.skuId === product.sku_id);
  const nextEntry: WatchEntry = existing ? { ...existing } : makeWatchEntry(product, nowIso);
  nextEntry.alertTarget = target ?? undefined;
  return [nextEntry, ...entries.filter((entry) => entry.skuId !== product.sku_id)];
}
