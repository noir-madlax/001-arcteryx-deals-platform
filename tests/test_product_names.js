const assert = require('node:assert/strict');
const test = require('node:test');

const {
  MODEL_FAMILIES,
  extractModelFamily,
  isArcTeryxProduct,
  standardProductName,
} = require('../arcteryx-names.js');
const {
  isSupportedBrandProduct,
  productBrand,
  standardProductName: standardGearProductName,
} = require('../gear-brands.js');

test('preserves Arc\'teryx discriminators and canonical gender', () => {
  assert.equal(
    standardProductName("Arc'teryx Micon LiTRIC 32L Airbag Pack", { gender: 'unisex' }),
    'Micon LiTRIC 32L Airbag Pack Unisex',
  );
  assert.equal(
    standardProductName("Arc'teryx Beta AR - StormHood Jacket - Men's"),
    "Beta AR - StormHood Jacket Men's",
  );
  assert.equal(standardProductName("Diene Shirt LS Women's"), "Diene Shirt LS Women's");
});

test('strips retailer color only for a verified Arc\'teryx model URL', () => {
  const valid = {
    dealer: 'ssense',
    gender: 'men',
    url: 'https://www.ssense.com/en-us/men/product/arcteryx/black-and-navy-alpha-sv-jacket/1',
  };
  assert.equal(standardProductName('Black & Navy Alpha SV Jacket', valid), "Alpha SV Jacket Men's");
  assert.equal(
    standardProductName('Teal FutureModel Jacket', { ...valid, gender: 'women' }),
    "Teal FutureModel Jacket Women's",
  );
});

test('rejects SSENSE rows whose brand path is not Arc\'teryx', () => {
  const contaminant = {
    dealer: 'ssense',
    url: 'https://www.ssense.com/en-us/women/product/marc-jacobs/pink-bag/1',
  };
  assert.equal(isArcTeryxProduct(contaminant), false);
  assert.equal(isArcTeryxProduct({ dealer: 'evo', url: 'https://www.evo.com/products/arc-teryx-beta' }), true);
});

test('registry includes every newly audited production family', () => {
  for (const family of ['Diene', 'Micon', 'Rhoam', 'Sunna', 'Venta', "Arc'Word", 'AR-385a', 'AR-395a']) {
    assert.ok(MODEL_FAMILIES.includes(family), family);
    assert.equal(extractModelFamily(`${family} Test Product`), family);
  }
});

test('shared brand runtime normalizes Burton and Patagonia without Arc naming rules', () => {
  const burton = { brand: 'Burton', dealer: 'evo', gender: 'men', url: 'https://www.evo.com/products/burton-custom' };
  const patagonia = { brand: 'patagonia', dealer: 'evo', gender: 'women', url: 'https://www.evo.com/products/patagonia-nano' };
  assert.equal(productBrand(burton), 'burton');
  assert.equal(productBrand(patagonia), 'patagonia');
  assert.equal(standardGearProductName("Burton Custom Camber Snowboard - Men's", burton), "Custom Camber Snowboard Men's");
  assert.equal(standardGearProductName("Patagonia Nano Puff Jacket - Women's", patagonia), "Nano Puff Jacket Women's");
  assert.equal(isSupportedBrandProduct({ ...burton, brand: 'unknown' }), false);
  assert.equal(isSupportedBrandProduct({ ...burton, full_name: 'Patagonia Nano Puff Jacket' }), false);
});

test('Arc name audit skips supported non-Arc rows without treating them as contamination', async () => {
  const { auditRows } = await import('../tools/audit_product_names.mjs');
  const result = auditRows([
    { brand: 'burton', dealer: 'evo', full_name: 'Burton Custom Camber Snowboard', status: 'active', url: 'https://www.evo.com/products/burton-custom' },
    { brand: 'patagonia', dealer: 'evo', full_name: 'Patagonia Nano Puff Jacket', status: 'active', url: 'https://www.evo.com/products/patagonia-nano' },
  ], { strictSource: true });
  assert.equal(result.accepted, 0);
  assert.equal(result.supportedNonArc, 2);
  assert.equal(result.rejected, 0);
  assert.equal(result.violations, 0);
});

test('full-catalog audit fails closed on unknown families and source contamination', async () => {
  const { auditRows } = await import('../tools/audit_product_names.mjs');
  const result = auditRows([
    {
      dealer: 'evo',
      full_name: "Arc'teryx FutureModel 88 Jacket - Men's",
      gender: 'men',
      status: 'active',
      url: 'https://www.evo.com/products/arc-teryx-future-model-88-jacket',
    },
    {
      dealer: 'ssense',
      full_name: "Pink 'The Glam Mirror Satchel' Bag",
      gender: 'women',
      status: 'active',
      url: 'https://www.ssense.com/en-us/women/product/marc-jacobs/pink-bag/1',
    },
  ], { strictSource: true });

  assert.equal(result.unknownFamilies.length, 1);
  assert.equal(result.lostDiscriminators.length, 0);
  assert.equal(result.rejectedRows.length, 1);
  assert.equal(result.violations, 2);
});
