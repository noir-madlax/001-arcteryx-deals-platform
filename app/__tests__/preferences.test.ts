import assert from 'node:assert/strict';
import test from 'node:test';

import { convertAmount, formatCurrencyValue, parseRateRows } from '../lib/currency';
import { LANGUAGE_OPTIONS, localizedCategory, missingTranslationKeys, resolveLanguage, translate } from '../lib/i18n';

const snapshot = parseRateRows(
  [
    { date: '2026-07-10', base: 'EUR', quote: 'USD', rate: 1.2 },
    { date: '2026-07-10', base: 'EUR', quote: 'CAD', rate: 1.6 },
  ],
  '2026-07-10T12:00:00Z',
);

test('system language resolves to a supported locale with English fallback', () => {
  assert.equal(resolveLanguage('system', 'zh'), 'zh-Hans');
  assert.equal(resolveLanguage('system', 'de'), 'de');
  assert.equal(resolveLanguage('system', 'es'), 'en');
  assert.equal(resolveLanguage('ja', 'en'), 'ja');
});

test('translations interpolate values and localize catalog labels', () => {
  assert.equal(translate('zh-Hans', 'deals.loadedShown', { loaded: '100', shown: '25' }), '已加载 100 · 显示 25');
  assert.equal(translate('zh-Hans', 'brand.name'), '值de');
  assert.equal(translate('en', 'brand.name'), 'GearDrop');
  assert.equal(translate('de', 'privacy.title'), 'Datenschutz');
  assert.equal(localizedCategory('ja', '裤装'), 'パンツ');
});

test('every shipped language covers the complete UI message catalog', () => {
  for (const language of LANGUAGE_OPTIONS) {
    if (language === 'system') continue;
    assert.deepEqual(missingTranslationKeys(language), [], `${language} is missing translations`);
  }
});

test('EUR-base rates convert between non-EUR currencies', () => {
  assert.ok(snapshot);
  const converted = convertAmount(120, 'USD', 'CAD', snapshot);
  assert.equal(converted.currency, 'CAD');
  assert.equal(converted.converted, true);
  assert.ok(Math.abs(converted.value - 160) < 0.0001);
});

test('missing rates fall back to the source amount and currency', () => {
  assert.deepEqual(convertAmount(100, 'SEK', 'USD', snapshot), { value: 100, currency: 'SEK', converted: false });
  assert.deepEqual(convertAmount(100, 'EUR', 'original', snapshot), { value: 100, currency: 'EUR', converted: false });
});

test('currency formatting follows locale and currency minor units', () => {
  assert.match(formatCurrencyValue(1234.5, 'USD', 'en-US'), /1,234\.5/);
  assert.match(formatCurrencyValue(1234.5, 'EUR', 'de-DE'), /1\.234,5/);
  assert.doesNotMatch(formatCurrencyValue(1234.5, 'JPY', 'ja-JP'), /\.5/);
});
