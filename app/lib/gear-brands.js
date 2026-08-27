/* Canonical GearDrop brand runtime shared by web and Expo. */
(function initGearBrands(root, factory) {
    let arcNames = root && root.ArcTeryxNames;
    if (!arcNames && typeof module === 'object' && module.exports) {
        arcNames = require('./arcteryx-names.js');
    }
    const api = factory(arcNames);
    if (typeof module === 'object' && module.exports) module.exports = api;
    if (root) root.GearBrands = api;
}(typeof globalThis !== 'undefined' ? globalThis : this, function createGearBrands(arcNames) {
    'use strict';

    const BRANDS = Object.freeze({
        arcteryx: Object.freeze({ label: "Arc'teryx" }),
        burton: Object.freeze({ label: 'Burton' }),
        patagonia: Object.freeze({ label: 'Patagonia' }),
    });
    const SUPPORTED_BRAND_KEYS = Object.freeze(Object.keys(BRANDS));

    function normalizeWhitespace(value) {
        return String(value || '').normalize('NFKC').replace(/\s+/g, ' ').trim();
    }

    function normalizeBrand(value) {
        const normalized = String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, '');
        if (normalized === 'arcteryx' || normalized === 'arcteryxoutlet') return 'arcteryx';
        if (normalized === 'burton') return 'burton';
        if (normalized === 'patagonia') return 'patagonia';
        return null;
    }

    function inferredBrand(product) {
        const item = product || {};
        const url = String(item.url || '').toLowerCase();
        if (/(?:^|\.)burton\.com(?:\/|$)/.test(url.replace(/^https?:\/\//, ''))) return 'burton';
        if (/(?:^|\.)patagonia\.com(?:\.au)?(?:\/|$)/.test(url.replace(/^https?:\/\//, ''))) return 'patagonia';
        if (/arcteryx\.com|\/product\/arcteryx\//.test(url)) return 'arcteryx';

        const raw = normalizeWhitespace(item.full_name || item.model || item.name);
        if (/^burton(?:\s|$)/i.test(raw)) return 'burton';
        if (/^patagonia(?:\s|$)/i.test(raw)) return 'patagonia';
        if (/^arc[\s-]*[’'`]?teryx(?:\s|$)/i.test(raw)) return 'arcteryx';

        return null;
    }

    function productBrand(product) {
        const item = product || {};
        if (item.brand != null && String(item.brand).trim()) return normalizeBrand(item.brand);

        const inferred = inferredBrand(item);
        if (inferred) return inferred;

        // Every product row written before the brand migration was Arc'teryx.
        return 'arcteryx';
    }

    function brandLabel(value) {
        const key = normalizeBrand(value);
        return key ? BRANDS[key].label : '';
    }

    function normalizeGender(value) {
        const key = String(value || '').trim().toLowerCase().replace(/[’']/g, '');
        if (['women', 'womens', 'woman', 'female'].includes(key)) return "Women's";
        if (['men', 'mens', 'man', 'male'].includes(key)) return "Men's";
        if (key === 'unisex') return 'Unisex';
        return '';
    }

    function standardProductName(raw, context) {
        const product = context || {};
        const brand = productBrand(product);
        if (brand === 'arcteryx' && arcNames) return arcNames.standardProductName(raw, product);

        let value = normalizeWhitespace(raw);
        if (!value) return '';
        if (brand === 'burton') value = value.replace(/^burton\s+/i, '');
        if (brand === 'patagonia') value = value.replace(/^patagonia\s+/i, '');

        let gender = '';
        const genderMatch = value.match(/\b(?:women(?:[’']?s)?|woman|men(?:[’']?s)?|man|unisex)\b/i);
        if (genderMatch) {
            gender = /^wo/i.test(genderMatch[0]) ? "Women's" : /^unisex$/i.test(genderMatch[0]) ? 'Unisex' : "Men's";
            value = `${value.slice(0, genderMatch.index)} ${value.slice((genderMatch.index || 0) + genderMatch[0].length)}`
                .replace(/\s*[-–—]\s*$/, '')
                .replace(/^\s*[-–—]\s*/, '');
        } else {
            gender = normalizeGender(product.gender);
        }
        value = normalizeWhitespace(value).replace(/^[-–—]\s*|\s*[-–—]$/g, '');
        return gender && value ? `${value} ${gender}` : value;
    }

    function productSeries(raw, context) {
        const brand = productBrand(context || {});
        const name = standardProductName(raw, context);
        if (!name) return null;
        if (brand === 'arcteryx' && arcNames) return arcNames.extractModelFamily(name);
        return name.split(/\s+/)[0] || null;
    }

    function isSupportedBrandProduct(product) {
        const item = product || {};
        const brand = productBrand(item);
        if (brand === null) return false;
        const inferred = inferredBrand(item);
        if (inferred && inferred !== brand) return false;
        const dealer = String(item.dealer || '').toLowerCase();
        const url = String(item.url || '');
        const fromSsense = dealer === 'ssense' || /(^|\.)ssense\.com(?=\/|$)/i.test(url.replace(/^https?:\/\//i, ''));
        if (fromSsense) return brand === 'arcteryx' && Boolean(arcNames && arcNames.isArcTeryxProduct(item));
        if (dealer === 'arcteryx_outlet') return brand === 'arcteryx';
        if (dealer === 'burton') {
            return brand === 'burton' && /^https:\/\/(?:www\.)?burton\.com\/en-us\/products\/[a-z0-9-]+(?:[?#].*)?$/i.test(url);
        }
        if (dealer === 'backcountry') {
            return brand === 'burton' && /^https:\/\/(?:www\.)?backcountry\.com\/burton-[^?#]+(?:[?#].*)?$/i.test(url);
        }
        if (dealer === 'patagonia') {
            return brand === 'patagonia' && /^https:\/\/(?:www\.)?patagonia\.com\.au\/products\/[a-z0-9-]+(?:[?#].*)?$/i.test(url);
        }
        return true;
    }

    return Object.freeze({
        BRANDS,
        SUPPORTED_BRAND_KEYS,
        brandLabel,
        isSupportedBrandProduct,
        normalizeBrand,
        productBrand,
        productSeries,
        standardProductName,
    });
}));
