'use strict';

const assert = require('node:assert/strict');
const test = require('node:test');

const {
    PRODUCT_PREVIEW_LIMIT,
    PRODUCT_PREVIEW_MAX_AGE_MS,
    parseProductPreviewCache,
    productPreviewCacheKey,
    serializeProductPreviewCache,
} = require('../web-product-preview.js');

const product = index => ({
    sku_id: `preview-${index}`,
    sale_price: 100 + index,
    region: 'us',
    dealer: 'evo',
    status: 'active',
});

test('web preview cache is region-scoped, fresh, and bounded', () => {
    const now = 1_800_000_000_000;
    const products = Array.from({ length: PRODUCT_PREVIEW_LIMIT + 25 }, (_, index) => product(index));
    const raw = serializeProductPreviewCache(products, 'us', now);
    const parsed = parseProductPreviewCache(raw, 'us', now + 1_000);

    assert.equal(parsed.length, PRODUCT_PREVIEW_LIMIT);
    assert.equal(parsed[0].sku_id, 'preview-0');
    assert.equal(parsed.at(-1).sku_id, `preview-${PRODUCT_PREVIEW_LIMIT - 1}`);
    assert.notEqual(productPreviewCacheKey('us'), productPreviewCacheKey('ca'));
});

test('web preview cache rejects stale, future, wrong-region, oversized, and malformed values', () => {
    const now = 1_800_000_000_000;
    const valid = serializeProductPreviewCache([product(1)], 'us', now);

    assert.deepEqual(parseProductPreviewCache(valid, 'ca', now), []);
    assert.deepEqual(
        parseProductPreviewCache(
            serializeProductPreviewCache([product(1)], 'us', now - PRODUCT_PREVIEW_MAX_AGE_MS - 1),
            'us',
            now,
        ),
        [],
    );
    assert.deepEqual(
        parseProductPreviewCache(serializeProductPreviewCache([product(1)], 'us', now + 1), 'us', now),
        [],
    );
    assert.deepEqual(
        parseProductPreviewCache(
            JSON.stringify({
                version: 1,
                region: 'us',
                savedAt: now,
                products: Array.from({ length: PRODUCT_PREVIEW_LIMIT + 1 }, (_, index) => product(index)),
            }),
            'us',
            now,
        ),
        [],
    );
    assert.deepEqual(parseProductPreviewCache('not json', 'us', now), []);
});

test('web preview cache drops invalid rows before storage and readback', () => {
    const now = 1_800_000_000_000;
    const raw = serializeProductPreviewCache(
        [product(1), { sku_id: '', sale_price: 10 }, { sku_id: 'bad-price', sale_price: '10' }],
        'us',
        now,
    );

    assert.deepEqual(parseProductPreviewCache(raw, 'us', now), [product(1)]);
});

test('web preview cache drops retired and inactive products', () => {
    const now = 1_800_000_000_000;
    const raw = serializeProductPreviewCache(
        [
            product(1),
            { ...product(2), dealer: 'ssense' },
            { ...product(3), status: 'inactive' },
        ],
        'us',
        now,
    );

    assert.deepEqual(parseProductPreviewCache(raw, 'us', now), [product(1)]);
});
