export type ProductRow = {
  id: number;
  sku_id: string | null;
  model: string | null;
  full_name: string | null;
  color: string | null;
  sizes: string[] | string | null;
  size_stock: Record<string, string> | string | null;
  original_price: number | string | null;
  sale_price: number | string | null;
  discount_pct: number | string | null;
  currency: string | null;
  symbol: string | null;
  gender: string | null;
  region: string | null;
  region_name: string | null;
  category: string | null;
  url: string | null;
  image_url: string | null;
  images: string[] | string | null;
  description: string | null;
  last_updated: string | null;
  created_at: string | null;
  dealer: string | null;
  first_seen: string | null;
};

export type Product = Omit<ProductRow, 'sku_id' | 'sizes' | 'size_stock' | 'images' | 'original_price' | 'sale_price' | 'discount_pct' | 'symbol' | 'currency' | 'region'> & {
  sku_id: string;
  sizes: string[];
  size_stock: Record<string, string>;
  images: string[];
  original_price: number;
  sale_price: number;
  discount_pct: number;
  symbol: string;
  currency: string;
  region: string;
  _series: string;
  _platform: string;
};

export type PriceHistoryRow = {
  sku_id?: string | null;
  sale_price: number | string | null;
  original_price: number | string | null;
  recorded_at: string | null;
};

export type ChartPoint = {
  day: string;
  sale: number;
  original: number;
};

export type SignalKind = 'all_time_low' | 'ninety_day_low' | 'drop_today' | 'steady' | 'insufficient';

export type DealSignal = {
  kind: SignalKind;
  label: string;
  tone: 'success' | 'neutral';
  verdict: string;
  isLow: boolean;
  minPrice: number | null;
  pointCount: number;
};

export type WatchEntry = {
  skuId: string;
  savedAt: string;
  savedPrice: number;
  symbol: string;
  alertTarget?: number;
};

export type PriceAlertPayload = {
  email: string;
  sku_id: string;
  target_price: number | null;
  last_price_seen: number;
  currency: string;
  region: string;
  product_name: string;
  product_url: string;
  image_url: string;
  unsubscribe_token: string;
};
