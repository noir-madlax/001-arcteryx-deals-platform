import type { Product, ProductRow } from './types';
import {
  extractModelFamily,
} from './arcteryx-names';
import {
  BRANDS,
  isSupportedBrandProduct,
  productBrand,
  productSeries,
  standardProductName,
} from './gear-brands';

export const SUPABASE_URL = 'https://bupqagkrcvrezjkdbald.supabase.co';
export const SUPABASE_ANON =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ1cHFhZ2tyY3ZyZXpqa2RiYWxkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY0NDU1NTMsImV4cCI6MjA5MjAyMTU1M30.oszdUJIEKMCvpD9XFzTYTCYXj078uwjzFx84tfStfRU';

export const REGION_LABEL: Record<string, string> = {
  us: 'United States',
  ca: 'Canada',
  gb: 'United Kingdom',
  de: 'Germany',
  fr: 'France',
  nl: 'Netherlands',
  fi: 'Finland',
  ie: 'Ireland',
  au: 'Australia',
  se: 'Sweden',
  at: 'Austria',
  ch: 'Switzerland',
  jp: 'Japan',
  it: 'Italy',
  es: 'Spain',
  dk: 'Denmark',
  be: 'Belgium',
};

export const GENDER_LABEL: Record<string, string> = {
  men: 'Men',
  women: 'Women',
  unisex: 'Unisex',
  unknown: 'Unisex',
};

export const BRAND = BRANDS;

export const PLATFORM: Record<string, { label: string; color: string }> = {
  arcteryx_outlet: { label: "Arc'teryx Outlet", color: '#151513' },
  ssense: { label: 'SSENSE', color: '#151513' },
  mec: { label: 'MEC', color: '#c8102e' },
  evo: { label: 'EVO', color: '#1a1a1a' },
  burton: { label: 'Burton', color: '#111111' },
  rei: { label: 'REI', color: '#067a46' },
  backcountry: { label: 'Backcountry', color: '#003a70' },
  steepandcheap: { label: 'Steep&Cheap', color: '#d22730' },
  moosejaw: { label: 'Moosejaw', color: '#e87722' },
  sierra: { label: 'Sierra', color: '#5c2d91' },
  altitude: { label: 'Altitude', color: '#003c5c' },
  thelasthunt: { label: 'TheLastHunt', color: '#151513' },
  sportsshoes: { label: 'SportsShoes', color: '#003a8c' },
  zalando_lounge: { label: 'Zalando Lounge', color: '#ff6900' },
};

export const REGION_OPTIONS = ['all', 'us', 'ca', 'gb', 'de', 'fr', 'nl', 'fi', 'ie', 'jp'];
export const BRAND_OPTIONS = ['all', 'arcteryx', 'burton', 'patagonia'];
export const GENDER_OPTIONS = ['all', 'women', 'men', 'unisex'];
export const SORT_OPTIONS = ['discount_desc', 'price_asc', 'price_desc', 'recent'];
export const CATEGORY_ORDER = [
  '冲锋衣',
  '保暖羽绒',
  '卫衣/抓绒',
  '裤装',
  '鞋类',
  '滑雪板',
  '固定器',
  '背包',
  '上衣',
  '内衣',
  '手套',
  '帽子',
  'Veilance',
  '其他',
];

const SEASON_LABEL: Record<string, string> = { F: 'Fall/Winter', W: 'Fall/Winter', S: 'Spring/Summer' };

export function cleanName(raw?: string | null) {
  return standardProductName(raw);
}

export function productName(product: Pick<ProductRow, 'brand' | 'dealer' | 'full_name' | 'gender' | 'model' | 'url'>) {
  return standardProductName(product.full_name || product.model, product);
}

export function inferCategory(name?: string | null, url?: string | null) {
  const n = (name || '').toLowerCase();
  const u = (url || '').toLowerCase();
  if (/snowboard|splitboard|powder board/.test(n) || /snowboards?/.test(u)) return '滑雪板';
  if (/binding/.test(n) || /bindings?/.test(u)) return '固定器';
  if (/veilance/.test(n) || /veilance/.test(u)) return 'Veilance';
  if (/shoe|boot|sandal|kragg|konseal|aerios|bora|acrux|vertex|kopec|norvan\s*sl|sylan/.test(n)) return '鞋类';
  if (/\bpack\b|backpack|bag|mantis|arro|brize|khard|\bindex\b/.test(n)) return '背包';
  if (/\bpants?\b|bib\s*pants?|bib\s*shorts?|\bshorts?\b|leggings?|tights?|\bliner\b|trousers?/.test(n)) return '裤装';
  if (/one\s*piece|onesie|coverall/.test(n)) return '连体雪衣';
  if (/harness|belay|carabiner|sling|rope|cordelette/.test(n)) return '攀岩装备';
  if (/bandana|belt|visor|conveyor|scarf|gaiter|sleeve/.test(n)) return '配饰';
  if (/down\s*jacket|insulated\s*jacket|cerium|thorium|nuclei|calidum|proton\s*lt\s*j/.test(n)) return '保暖羽绒';
  if (/jacket|shell/.test(n)) return '冲锋衣';
  if (/hoody|hoodie|fleece|zip.*neck|pullover|crew|cardigan|sweater/.test(n)) return '卫衣/抓绒';
  if (/\btee\b|t-shirt|\bshirt\b|\bpolo\b/.test(n)) return '上衣';
  if (/glove|mitt/.test(n)) return '手套';
  if (/\bhat\b|toque|beanie|\bcap\b|headband/.test(n)) return '帽子';
  if (/brief|boxer|base.?layer/.test(n)) return '内衣';
  return '其他';
}

export function releaseSeason(product: Pick<Product, 'image_url' | 'images'>) {
  const urls = [product.image_url, ...product.images].filter(Boolean);
  for (const url of urls) {
    const match = String(url).match(/\/([FSWfsw])(\d{2})(?=[-_/])/);
    const code = match?.[1]?.toUpperCase();
    const year = match?.[2];
    if (code && year) return `${SEASON_LABEL[code] || ''} 20${year}`.trim();
  }
  return null;
}

export function platformKey(product: Pick<ProductRow, 'dealer' | 'url'>) {
  if (product.dealer && PLATFORM[product.dealer]) return product.dealer;
  const url = (product.url || '').toLowerCase();
  if (url.includes('outlet.arcteryx.com')) return 'arcteryx_outlet';
  if (url.includes('ssense.com')) return 'ssense';
  if (url.includes('mec.ca')) return 'mec';
  if (url.includes('evo.com')) return 'evo';
  if (url.includes('burton.com')) return 'burton';
  if (url.includes('rei.com')) return 'rei';
  if (url.includes('backcountry')) return 'backcountry';
  if (url.includes('steepandcheap')) return 'steepandcheap';
  return 'arcteryx_outlet';
}

export function parseMaybeJson<T>(value: unknown, fallback: T): T {
  if (value == null || value === '') return fallback;
  if (typeof value === 'object') return value as T;
  try {
    return JSON.parse(String(value)) as T;
  } catch {
    return fallback;
  }
}

export function normalizeTimestamp(ts?: string | null) {
  if (!ts) return '';
  return ts.replace('T', ' ').slice(0, 19);
}

export function extractSeries(cleanedName: string) {
  return extractModelFamily(cleanedName) || '其他';
}

function allKnownSizesOutOfStock(product: ProductRow) {
  const sizes = parseMaybeJson<string[]>(product.sizes, []);
  const stock = parseMaybeJson<Record<string, string>>(product.size_stock, {});
  const keys = Array.isArray(sizes) && sizes.length ? sizes : Object.keys(stock);
  return keys.length > 0 && keys.every((size) => stock[size] === 'out_of_stock');
}

export function isBlockedProduct(product: ProductRow) {
  if (!isSupportedBrandProduct(product)) return true;
  const dealer = product.dealer || platformKey(product);
  if (dealer !== 'arcteryx_outlet') return false;
  const url = (String(product.url || '').split('?')[0] || '').replace(/\/$/, '').toLowerCase();
  return /outlet\.arcteryx\.com\/(?:[a-z]{2}\/[a-z]{2}\/)?shop\/womens\/rush-bib-pant$/.test(url) || allKnownSizesOutOfStock(product);
}

export function normalizeProduct(row: ProductRow): Product | null {
  if (!row.sku_id || row.sale_price == null) return null;
  const sizes = parseMaybeJson<string[]>(row.sizes, []);
  const sizeStock = parseMaybeJson<Record<string, string>>(row.size_stock, {});
  const images = parseMaybeJson<string[]>(row.images, []);
  const name = productName(row);
  const brand = productBrand(row);
  if (!brand) return null;
  return {
    ...row,
    sku_id: row.sku_id,
    sizes: Array.isArray(sizes) ? sizes : [],
    size_stock: sizeStock && typeof sizeStock === 'object' ? sizeStock : {},
    images: Array.isArray(images) ? images : [],
    original_price: Number(row.original_price || 0),
    sale_price: Number(row.sale_price || 0),
    discount_pct: Number(row.discount_pct || 0),
    symbol: row.symbol || '$',
    currency: row.currency || 'USD',
    region: row.region || 'us',
    brand,
    last_updated: normalizeTimestamp(row.last_updated),
    _brand: brand,
    _series: productSeries(name, row) || '其他',
    _platform: platformKey(row),
  };
}

export function visibleProducts(rows: ProductRow[]) {
  return rows.filter((row) => !isBlockedProduct(row)).map(normalizeProduct).filter((row): row is Product => Boolean(row));
}

export function productCategory(product: Product) {
  return product.category && product.category !== '其他' ? product.category : inferCategory(productName(product), product.url);
}

export function formatPrice(value?: number | null, symbol = '$') {
  if (value == null || Number.isNaN(value)) return `${symbol}--`;
  return `${symbol}${Math.round(value).toLocaleString('en-US')}`;
}

export function freshnessLabel(lastUpdated?: string | null) {
  if (!lastUpdated) return '';
  const stamp = Date.parse(lastUpdated.replace(' ', 'T') + (lastUpdated.endsWith('Z') ? '' : 'Z'));
  if (Number.isNaN(stamp)) return '';
  const days = Math.floor((Date.now() - stamp) / 86400000);
  if (days <= 0) return 'today';
  if (days === 1) return 'yesterday';
  return `${days}d ago`;
}

export function staleDays(lastUpdated?: string | null) {
  if (!lastUpdated) return 0;
  const stamp = Date.parse(lastUpdated.replace(' ', 'T') + (lastUpdated.endsWith('Z') ? '' : 'Z'));
  if (Number.isNaN(stamp)) return 0;
  return Math.floor((Date.now() - stamp) / 86400000);
}
