import type { Product, ProductRow } from '../lib/types';

export function product(overrides: Partial<Product> = {}): Product {
  return {
    id: 1,
    sku_id: 'beta-jacket_Black_us',
    model: "Arc'teryx Beta Jacket - Men's",
    full_name: "Arc'teryx Beta Jacket - Men's",
    color: 'Black',
    sizes: ['M'],
    size_stock: { M: 'in_stock' },
    original_price: 400,
    sale_price: 300,
    discount_pct: 25,
    currency: 'USD',
    symbol: '$',
    gender: 'men',
    region: 'us',
    region_name: 'United States',
    category: '夹克/外套',
    url: 'https://outlet.arcteryx.com/us/en/shop/mens/beta-jacket',
    image_url: 'https://images-dynamic-arcteryx.imgix.net/details/1350x1710/F25-X000000000-Beta-Jacket-Black-Men-s-Front-View.jpg',
    images: [],
    description: null,
    last_updated: new Date().toISOString(),
    created_at: null,
    dealer: 'arcteryx_outlet',
    first_seen: null,
    _series: 'Beta',
    _platform: 'arcteryx_outlet',
    ...overrides,
  };
}

export function row(overrides: Partial<ProductRow> = {}): ProductRow {
  return {
    id: 1,
    sku_id: 'beta-jacket_Black_us',
    model: "Arc'teryx Beta Jacket - Men's",
    full_name: "Arc'teryx Beta Jacket - Men's",
    color: 'Black',
    sizes: ['M'],
    size_stock: { M: 'in_stock' },
    original_price: '400',
    sale_price: '300',
    discount_pct: '25',
    currency: 'USD',
    symbol: '$',
    gender: 'men',
    region: 'us',
    region_name: 'United States',
    category: '其他',
    url: 'https://outlet.arcteryx.com/us/en/shop/mens/beta-jacket',
    image_url: 'https://images-dynamic-arcteryx.imgix.net/details/1350x1710/F25-X000000000-Beta-Jacket-Black-Men-s-Front-View.jpg',
    images: [],
    description: null,
    last_updated: '2026-07-07T12:00:00Z',
    created_at: null,
    dealer: 'arcteryx_outlet',
    first_seen: null,
    ...overrides,
  };
}

export function daysAgo(days: number) {
  return new Date(Date.now() - days * 86400000).toISOString();
}
