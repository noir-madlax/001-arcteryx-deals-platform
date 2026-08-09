export type ProductNameContext = {
  dealer?: string | null;
  gender?: string | null;
  url?: string | null;
};

export const MODEL_FAMILIES: readonly string[];
export function extractModelFamily(standardName?: string | null): string | null;
export function isArcTeryxProduct(product?: ProductNameContext | null): boolean;
export function standardProductName(raw?: string | null, context?: ProductNameContext): string;
