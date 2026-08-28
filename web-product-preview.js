(function (root, factory) {
    const api = factory();
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) root.GearDropPreview = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
    'use strict';

    const PRODUCT_PREVIEW_CACHE_VERSION = 1;
    const PRODUCT_PREVIEW_LIMIT = 200;
    const PRODUCT_PREVIEW_MAX_AGE_MS = 24 * 60 * 60 * 1000;
    const PRODUCT_PREVIEW_CACHE_PREFIX = 'geardrop.web-product-preview.v1';

    const productPreviewCacheKey = region =>
        `${PRODUCT_PREVIEW_CACHE_PREFIX}:${encodeURIComponent(region || 'us')}`;

    const isPreviewProduct = product =>
        product &&
        typeof product.sku_id === 'string' &&
        product.sku_id.length > 0 &&
        (!product.status || product.status === 'active') &&
        String(product.dealer || '').toLowerCase() !== 'ssense' &&
        Number.isFinite(product.sale_price);

    function parseProductPreviewCache(raw, region, now = Date.now()) {
        if (!raw) return [];
        try {
            const value = JSON.parse(raw);
            const age = now - value.savedAt;
            if (
                value.version !== PRODUCT_PREVIEW_CACHE_VERSION ||
                value.region !== region ||
                !Number.isFinite(value.savedAt) ||
                age < 0 ||
                age > PRODUCT_PREVIEW_MAX_AGE_MS ||
                !Array.isArray(value.products) ||
                value.products.length > PRODUCT_PREVIEW_LIMIT
            ) {
                return [];
            }
            return value.products.filter(isPreviewProduct);
        } catch (_) {
            return [];
        }
    }

    function serializeProductPreviewCache(products, region, savedAt = Date.now()) {
        return JSON.stringify({
            version: PRODUCT_PREVIEW_CACHE_VERSION,
            region,
            savedAt,
            products: (products || []).filter(isPreviewProduct).slice(0, PRODUCT_PREVIEW_LIMIT),
        });
    }

    return {
        PRODUCT_PREVIEW_CACHE_VERSION,
        PRODUCT_PREVIEW_LIMIT,
        PRODUCT_PREVIEW_MAX_AGE_MS,
        productPreviewCacheKey,
        parseProductPreviewCache,
        serializeProductPreviewCache,
    };
});
