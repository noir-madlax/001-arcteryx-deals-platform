import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const iconPath = join(process.cwd(), 'assets', 'icon.png');
const png = readFileSync(iconPath);
const pngSignature = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

assert.ok(png.subarray(0, 8).equals(pngSignature), 'App icon must be a PNG file');
assert.equal(png.toString('ascii', 12, 16), 'IHDR', 'App icon must contain a valid IHDR chunk');

const width = png.readUInt32BE(16);
const height = png.readUInt32BE(20);
const colorType = png[25];
const chunks: string[] = [];

for (let offset = 8; offset + 12 <= png.length; ) {
  const chunkLength = png.readUInt32BE(offset);
  const chunkType = png.toString('ascii', offset + 4, offset + 8);
  chunks.push(chunkType);
  offset += chunkLength + 12;
  if (chunkType === 'IEND') break;
}

assert.equal(width, 1024, 'App Store icon width must be 1024px');
assert.equal(height, 1024, 'App Store icon height must be 1024px');
assert.ok(colorType !== 4 && colorType !== 6, `App Store icon must not have an alpha channel (PNG color type ${colorType})`);
assert.ok(!chunks.includes('tRNS'), 'App Store icon must not contain a transparency chunk');

console.log(`release_assets_ok icon=${width}x${height} colorType=${colorType} alpha=false`);
