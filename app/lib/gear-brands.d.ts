export type GearBrand = 'arcteryx' | 'burton' | 'patagonia';

export type BrandContext = {
  brand?: string | null;
  dealer?: string | null;
  full_name?: string | null;
  gender?: string | null;
  model?: string | null;
  name?: string | null;
  url?: string | null;
};

export const BRANDS: Readonly<Record<GearBrand, { readonly label: string }>>;
export const SUPPORTED_BRAND_KEYS: readonly GearBrand[];
export function brandLabel(value?: string | null): string;
export function isSupportedBrandProduct(product?: BrandContext | null): boolean;
export function normalizeBrand(value?: string | null): GearBrand | null;
export function productBrand(product?: BrandContext | null): GearBrand | null;
export function productSeries(raw?: string | null, context?: BrandContext): string | null;
export function standardProductName(raw?: string | null, context?: BrandContext): string;
