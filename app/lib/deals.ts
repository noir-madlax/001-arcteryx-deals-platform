import { productCategory, productName, REGION_LABEL, REGION_OPTIONS } from './catalog';
import { normalizeSearchText } from './search';
import type { Product } from './types';

export type DealFilters = {
  brand: string;
  platform: string;
  category: string;
  gender: string;
  series: string;
  sort: string;
};

export const DEFAULT_DEAL_FILTERS: DealFilters = {
  brand: 'all',
  platform: 'all',
  category: 'all',
  gender: 'all',
  series: 'all',
  sort: 'discount_desc',
};

export function productsForRegion(products: Product[], region: string) {
  return region === 'all' ? products : products.filter((product) => product.region === region);
}

export function availableDealRegions(products: Product[]) {
  const present = new Set(products.map((product) => product.region).filter(Boolean));
  const preferred = REGION_OPTIONS.filter((region) => region !== 'all' && present.has(region));
  const extras = [...present]
    .filter((region) => !preferred.includes(region))
    .sort((a, b) => (REGION_LABEL[a] || a).localeCompare(REGION_LABEL[b] || b));
  return ['all', ...preferred, ...extras];
}

export function filterDeals(products: Product[], region: string, query: string, filters: DealFilters) {
  const q = normalizeSearchText(query);
  const rows = productsForRegion(products, region).filter((product) => {
    if (filters.brand !== 'all' && product._brand !== filters.brand) return false;
    if (filters.platform !== 'all' && product._platform !== filters.platform) return false;
    if (filters.gender !== 'all') {
      const gender = product.gender === 'unknown' ? 'unisex' : product.gender || 'unisex';
      if (gender !== filters.gender) return false;
    }
    if (filters.category !== 'all' && productCategory(product) !== filters.category) return false;
    if (filters.series !== 'all' && product._series !== filters.series) return false;
    if (q) {
      const haystack = normalizeSearchText(`${product._brand} ${product.brand} ${productName(product)} ${product.full_name || ''} ${product.model || ''} ${product.description || ''} ${product.category || ''}`);
      if (!haystack.includes(q)) return false;
    }
    return true;
  });

  switch (filters.sort) {
    case 'price_asc':
      return rows.sort((a, b) => a.sale_price - b.sale_price);
    case 'price_desc':
      return rows.sort((a, b) => b.sale_price - a.sale_price);
    case 'recent':
      return rows.sort((a, b) => (b.last_updated || '').localeCompare(a.last_updated || ''));
    case 'discount_desc':
    default:
      return rows.sort((a, b) => (b.discount_pct || 0) - (a.discount_pct || 0));
  }
}
