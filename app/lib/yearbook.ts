import type {
  CatalogBrandKey,
  CatalogGender,
  CatalogProduct,
  CatalogProductRow,
} from './types';

type BrandRule = {
  label: string;
  country: string;
  currency: string;
  sourceName: string;
  validId: (value: string) => boolean;
  validUrl: (url: URL) => boolean;
};

const STYLE_ID = /^[0-9A-Z][0-9A-Z._-]{1,63}$/;

export const YEARBOOK_BRAND_RULES: Record<CatalogBrandKey, BrandRule> = {
  arcteryx: {
    label: "Arc'teryx",
    country: 'us',
    currency: 'USD',
    sourceName: 'arcteryx_us_official_product_feed',
    validId: (value) => /^X[0-9A-Z]{6,}$/.test(value),
    validUrl: (url) => url.hostname === 'arcteryx.com' && url.pathname.startsWith('/us/en/shop/'),
  },
  burton: {
    label: 'Burton',
    country: 'us',
    currency: 'USD',
    sourceName: 'burton_us_official_collection_json',
    validId: (value) => STYLE_ID.test(value),
    validUrl: (url) => url.hostname === 'www.burton.com' && url.pathname.startsWith('/en-us/products/'),
  },
  patagonia: {
    label: 'Patagonia',
    country: 'au',
    currency: 'AUD',
    sourceName: 'patagonia_au_official_collection_json',
    validId: (value) => STYLE_ID.test(value),
    validUrl: (url) => url.hostname === 'www.patagonia.com.au' && url.pathname.startsWith('/products/'),
  },
};

export type YearbookFilters = {
  query?: string;
  brand?: CatalogBrandKey | 'all';
  gender?: CatalogGender | 'all';
  category?: string | 'all';
  year?: number | 'all';
};

function strings(value: string[] | string | null): string[] {
  if (Array.isArray(value)) return [...new Set(value.map((item) => item.trim()).filter(Boolean))];
  if (typeof value !== 'string' || !value.trim()) return [];
  try {
    const parsed: unknown = JSON.parse(value);
    return Array.isArray(parsed)
      ? [...new Set(parsed.map((item) => String(item).trim()).filter(Boolean))]
      : [];
  } catch {
    return [];
  }
}

function sourceMap(value: Record<string, string> | string | null): Record<string, string> {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return Object.fromEntries(
      Object.entries(value)
        .map(([key, item]) => [key.trim(), String(item).trim()])
        .filter(([key, item]) => Boolean(key && item)),
    );
  }
  if (typeof value !== 'string' || !value.trim()) return {};
  try {
    const parsed: unknown = JSON.parse(value);
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed)
      ? sourceMap(parsed as Record<string, string>)
      : {};
  } catch {
    return {};
  }
}

function finiteNumber(value: number | string | null): number | null {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : null;
}

function validDate(value: string | null): value is string {
  return Boolean(value && Number.isFinite(Date.parse(value)));
}

function brandKey(value: string | null): CatalogBrandKey | null {
  return value === 'arcteryx' || value === 'burton' || value === 'patagonia' ? value : null;
}

function genderValue(value: string | null): CatalogGender | null {
  return value === 'men' || value === 'women' || value === 'kids' || value === 'unisex' ? value : null;
}

function isOfficialUrl(rule: BrandRule, value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && !url.username && !url.password && rule.validUrl(url);
  } catch {
    return false;
  }
}

export function normalizeCatalogProduct(row: CatalogProductRow): CatalogProduct | null {
  const normalizedBrand = brandKey(row.brand_key);
  const gender = genderValue(row.gender);
  const officialId = row.official_product_id?.trim().toUpperCase() || '';
  const catalogId = row.catalog_product_id?.trim().toLowerCase() || '';
  const name = row.name?.trim() || '';
  const sourceUrl = row.source_url?.trim() || '';
  const listPrice = finiteNumber(row.list_price);
  const listPriceMax = finiteNumber(row.list_price_max);
  if (!normalizedBrand || !gender || !name || listPrice === null || listPriceMax === null || listPriceMax < listPrice) return null;
  const rule = YEARBOOK_BRAND_RULES[normalizedBrand];
  if (
    row.brand !== rule.label
    || row.catalog_scope !== 'full_price'
    || row.country !== rule.country
    || row.currency !== rule.currency
    || row.language !== 'en'
    || row.source_name !== rule.sourceName
    || row.status !== 'active'
    || !rule.validId(officialId)
    || catalogId !== `${normalizedBrand}:${officialId.toLowerCase()}`
    || !isOfficialUrl(rule, sourceUrl)
    || !/^[0-9a-f]{64}$/.test(row.source_hash || '')
    || !validDate(row.first_seen_at)
    || !validDate(row.last_seen_at)
    || !validDate(row.last_changed_at)
  ) return null;
  return {
    catalog_product_id: catalogId,
    brand_key: normalizedBrand,
    official_product_id: officialId,
    brand: rule.label,
    catalog_scope: 'full_price',
    market: row.market?.trim() || 'outdoor',
    country: rule.country,
    language: 'en',
    name,
    gender,
    collection: row.collection?.trim() || null,
    categories: strings(row.categories),
    category_sources: sourceMap(row.category_sources),
    list_price: listPrice,
    list_price_max: listPriceMax,
    currency: rule.currency,
    color_names: strings(row.color_names),
    primary_colors: strings(row.primary_colors),
    season_codes: strings(row.season_codes),
    source_name: rule.sourceName,
    source_url: sourceUrl,
    source_hash: row.source_hash || '',
    status: 'active',
    first_seen_at: row.first_seen_at,
    last_seen_at: row.last_seen_at,
    last_changed_at: row.last_changed_at,
  };
}

export function yearbookYear(product: CatalogProduct): number {
  const seasonYears = product.season_codes
    .map((value) => /^[FSW](\d{2})$/i.exec(value)?.[1])
    .filter((value): value is string => Boolean(value))
    .map((value) => 2000 + Number(value));
  return seasonYears.length ? Math.max(...seasonYears) : new Date(product.first_seen_at).getUTCFullYear();
}

export function filterYearbookProducts(products: CatalogProduct[], filters: YearbookFilters): CatalogProduct[] {
  const query = filters.query?.trim().toLocaleLowerCase() || '';
  return products.filter((product) => {
    if (filters.brand && filters.brand !== 'all' && product.brand_key !== filters.brand) return false;
    if (filters.gender && filters.gender !== 'all' && product.gender !== filters.gender) return false;
    if (filters.category && filters.category !== 'all' && !product.categories.includes(filters.category)) return false;
    if (filters.year && filters.year !== 'all' && yearbookYear(product) !== filters.year) return false;
    if (!query) return true;
    return [
      product.name,
      product.brand,
      product.official_product_id,
      product.collection || '',
      ...product.categories,
      ...product.color_names,
      ...product.primary_colors,
    ].join(' ').toLocaleLowerCase().includes(query);
  });
}

export function yearbookBrands(products: CatalogProduct[]): CatalogBrandKey[] {
  const present = new Set(products.map((product) => product.brand_key));
  return (['arcteryx', 'burton', 'patagonia'] as CatalogBrandKey[]).filter((brand) => present.has(brand));
}

export function yearbookYears(products: CatalogProduct[]): number[] {
  return [...new Set(products.map(yearbookYear))].sort((a, b) => b - a);
}

export function yearbookCategories(products: CatalogProduct[]): string[] {
  return [...new Set(products.flatMap((product) => product.categories))].sort((a, b) => a.localeCompare(b));
}

export function categoryLabel(value: string): string {
  return value.split('-').map((word) => word ? `${word.charAt(0).toUpperCase()}${word.slice(1)}` : '').join(' ');
}

export function brandLabel(value: CatalogBrandKey): string {
  return YEARBOOK_BRAND_RULES[value].label;
}

export function formatCatalogPrice(product: CatalogProduct): string {
  const locale = product.country === 'au' ? 'en-AU' : 'en-US';
  const formatter = new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: product.currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
  const minimum = formatter.format(product.list_price);
  return product.list_price_max > product.list_price
    ? `${minimum}–${formatter.format(product.list_price_max)}`
    : minimum;
}
