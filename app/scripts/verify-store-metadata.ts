import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

type LocaleMetadata = {
  name: string;
  subtitle: string;
  promotionalText: string;
  keywords: string;
  description: string;
  screenshots: string[];
};

type StoreMetadataManifest = {
  schemaVersion: number;
  target: string;
  appId: string;
  bundleId: string;
  primaryLocale: string;
  releaseBoundary: {
    applyToCurrentReview: boolean;
    requiresFreshAppStoreReadback: boolean;
    requiresFinalBuildScreenshots: boolean;
  };
  shared: {
    category: string;
    supportUrl: string;
    privacyPolicyUrl: string;
    termsUrl: string;
  };
  screenshotSources: string[];
  locales: Record<string, LocaleMetadata>;
};

const REQUIRED_LOCALES = ['en-US', 'zh-Hans', 'de-DE', 'fr-FR', 'ja'] as const;
const EXPECTED_SCREENSHOT_SOURCES = [
  'deals-feed',
  'product-detail-signal',
  'region-comparison',
  'watchlist',
  'pro-price-history',
  'display-preferences',
];
const SUPPORT_URL = 'https://001.100app.dev/support.html';
const PRIVACY_URL = 'https://001.100app.dev/privacy.html';
const TERMS_URL = 'https://www.apple.com/legal/internet-services/itunes/dev/stdeula/';
const FORBIDDEN_PUBLIC_TERMS: Array<{ label: string; pattern: RegExp }> = [
  { label: "Arc'teryx", pattern: /arc[’']?teryx/iu },
  { label: '始祖鸟', pattern: /始祖鸟/u },
  { label: 'Keepa', pattern: /\bkeepa\b/iu },
  { label: 'ShopSavvy', pattern: /\bshopsavvy\b/iu },
  { label: 'Slickdeals', pattern: /\bslickdeals\b/iu },
  { label: 'Backcountry', pattern: /\bbackcountry\b/iu },
  { label: 'REI', pattern: /\brei\b/iu },
];

function characterCount(value: string) {
  return [...value].length;
}

function occurrences(value: string, needle: string) {
  return value.split(needle).length - 1;
}

function assertCharacterRange(value: string, minimum: number, maximum: number, label: string) {
  const count = characterCount(value);
  assert.ok(count >= minimum && count <= maximum, `${label} must be ${minimum}-${maximum} characters, got ${count}`);
}

function assertNoForbiddenTerms(value: string, label: string) {
  for (const forbidden of FORBIDDEN_PUBLIC_TERMS) {
    assert.ok(!forbidden.pattern.test(value), `${label} must not contain protected or competing term ${forbidden.label}`);
  }
}

const manifestPath = join(process.cwd(), 'store-metadata', 'next-version.json');
const manifest = JSON.parse(readFileSync(manifestPath, 'utf8')) as StoreMetadataManifest;

assert.equal(manifest.schemaVersion, 1);
assert.equal(manifest.target, 'next-app-version');
assert.equal(manifest.appId, '6790165332');
assert.equal(manifest.bundleId, 'dev.100app.geardrop');
assert.equal(manifest.primaryLocale, 'en-US');
assert.equal(manifest.releaseBoundary.applyToCurrentReview, false, 'ASO package must not target the current review');
assert.equal(manifest.releaseBoundary.requiresFreshAppStoreReadback, true);
assert.equal(manifest.releaseBoundary.requiresFinalBuildScreenshots, true);
assert.equal(manifest.shared.category, 'SHOPPING');
assert.equal(manifest.shared.supportUrl, SUPPORT_URL);
assert.equal(manifest.shared.privacyPolicyUrl, PRIVACY_URL);
assert.equal(manifest.shared.termsUrl, TERMS_URL);
assert.deepEqual(manifest.screenshotSources, EXPECTED_SCREENSHOT_SOURCES);
assert.equal(new Set(manifest.screenshotSources).size, EXPECTED_SCREENSHOT_SOURCES.length);
assert.deepEqual(Object.keys(manifest.locales).sort(), [...REQUIRED_LOCALES].sort());

for (const localeKey of REQUIRED_LOCALES) {
  const locale = manifest.locales[localeKey];
  assert.ok(locale, `missing locale ${localeKey}`);

  assertCharacterRange(locale.name, 2, 30, `${localeKey}.name`);
  assertCharacterRange(locale.subtitle, 1, 30, `${localeKey}.subtitle`);
  assertCharacterRange(locale.promotionalText, 1, 170, `${localeKey}.promotionalText`);
  assertCharacterRange(locale.description, 1, 4000, `${localeKey}.description`);

  const keywordBytes = Buffer.byteLength(locale.keywords, 'utf8');
  assert.ok(keywordBytes <= 100, `${localeKey}.keywords must be at most 100 UTF-8 bytes, got ${keywordBytes}`);
  assert.ok(!/\s,|,\s/u.test(locale.keywords), `${localeKey}.keywords must use commas without surrounding spaces`);

  const keywords = locale.keywords.split(',');
  assert.equal(keywords.join(','), locale.keywords, `${localeKey}.keywords must not contain empty or normalized-away terms`);
  assert.equal(new Set(keywords.map((keyword) => keyword.toLocaleLowerCase(localeKey))).size, keywords.length, `${localeKey}.keywords must be unique`);
  for (const keyword of keywords) {
    assertCharacterRange(keyword, 3, 40, `${localeKey}.keyword(${keyword})`);
    assert.match(keyword, /^[\p{L}\p{N} -]+$/u, `${localeKey}.keyword(${keyword}) contains unsupported punctuation`);
    assert.ok(!/^(app|shopping)$/iu.test(keyword), `${localeKey}.keyword(${keyword}) must not repeat the app category or the word app`);
  }

  assert.equal(occurrences(locale.description, TERMS_URL), 1, `${localeKey}.description must include the standard EULA exactly once`);
  assert.equal(occurrences(locale.description, PRIVACY_URL), 1, `${localeKey}.description must include the privacy URL exactly once`);
  assert.ok(!/\$(?:3\.99|23\.99|49\.99)|€(?:3\.99|23\.99|49\.99)|¥(?:3\.99|23\.99|49\.99)/u.test(locale.description), `${localeKey}.description must not hardcode storefront prices`);

  assert.equal(locale.screenshots.length, EXPECTED_SCREENSHOT_SOURCES.length, `${localeKey}.screenshots must cover all six slots`);
  assert.equal(new Set(locale.screenshots).size, locale.screenshots.length, `${localeKey}.screenshots must use unique headlines`);
  for (const [index, headline] of locale.screenshots.entries()) {
    assertCharacterRange(headline, 3, 48, `${localeKey}.screenshots[${index}]`);
  }

  for (const [field, value] of Object.entries({
    name: locale.name,
    subtitle: locale.subtitle,
    promotionalText: locale.promotionalText,
    keywords: locale.keywords,
    description: locale.description,
    screenshots: locale.screenshots.join('\n'),
  })) {
    assertNoForbiddenTerms(value, `${localeKey}.${field}`);
  }

  console.log(
    `${localeKey} name=${characterCount(locale.name)} subtitle=${characterCount(locale.subtitle)} ` +
      `promo=${characterCount(locale.promotionalText)} description=${characterCount(locale.description)} ` +
      `keywords=${keywordBytes}B screenshots=${locale.screenshots.length}`,
  );
}

console.log(
  `store_metadata_ok target=${manifest.target} locales=${REQUIRED_LOCALES.length} ` +
    `screenshots=${EXPECTED_SCREENSHOT_SOURCES.length} currentReview=${manifest.releaseBoundary.applyToCurrentReview}`,
);
