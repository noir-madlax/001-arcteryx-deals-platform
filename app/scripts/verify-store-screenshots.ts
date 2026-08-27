import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const root = process.cwd();
const target = join(root, 'store-assets', 'iphone-6.9');
const locales = ['en-US', 'zh-Hans', 'de-DE', 'fr-FR', 'ja'];
const files = [
  '01-deals-feed.png',
  '02-product-detail-signal.png',
  '03-region-comparison.png',
  '04-watchlist.png',
  '05-pro-price-history.png',
  '06-yearbook-current-deals.png',
];
const missing: string[] = [];

for (const locale of locales) {
  for (const file of files) {
    const path = join(target, locale, file);
    if (!existsSync(path)) {
      missing.push(`${locale}/${file}`);
      continue;
    }
    const png = readFileSync(path);
    assert.ok(png.length > 33, `${locale}/${file} is not a complete PNG`);
    assert.deepEqual([...png.subarray(0, 8)], [137, 80, 78, 71, 13, 10, 26, 10], `${locale}/${file} must be PNG`);
    assert.equal(png.readUInt32BE(16), 1320, `${locale}/${file} width must be 1320`);
    assert.equal(png.readUInt32BE(20), 2868, `${locale}/${file} height must be 2868`);
    assert.equal(png[25], 2, `${locale}/${file} must be opaque RGB without an alpha channel`);
  }
}

assert.deepEqual(missing, [], `missing final signed screenshots:\n${missing.join('\n')}`);
console.log(`store_screenshots_ok locales=${locales.length} images=${locales.length * files.length} size=1320x2868 alpha=false`);
