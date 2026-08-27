import { visibleProducts } from './catalog';
import type { Product, ProductRow } from './types';

export const INITIAL_PRODUCT_REGION = 'us';
export const INITIAL_PRODUCT_LIMIT = 200;
export const INITIAL_SIGNAL_WINDOW = 20;
export const PRODUCT_PREVIEW_STORAGE_KEY = 'geardrop.product-preview.v2';
export const PRODUCT_PREVIEW_MAX_AGE_MS = 24 * 60 * 60 * 1000;

type ProductPreviewCache = {
  version: 2;
  savedAt: number;
  products: Product[];
};

export function parseProductPreviewCache(raw: string | null, now = Date.now()) {
  if (!raw) return [] as Product[];
  try {
    const value = JSON.parse(raw) as ProductPreviewCache;
    const age = now - value.savedAt;
    if (
      value.version !== 2 ||
      !Number.isFinite(value.savedAt) ||
      age < 0 ||
      age > PRODUCT_PREVIEW_MAX_AGE_MS ||
      !Array.isArray(value.products)
    ) {
      return [];
    }
    return visibleProducts(value.products as ProductRow[]);
  } catch {
    return [];
  }
}

export function serializeProductPreview(products: Product[], savedAt = Date.now()) {
  const payload: ProductPreviewCache = {
    version: 2,
    savedAt,
    products: products.slice(0, INITIAL_PRODUCT_LIMIT),
  };
  return JSON.stringify(payload);
}
