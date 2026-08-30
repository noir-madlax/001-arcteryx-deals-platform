#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(process.argv[2] || '');
const keep = Number(process.argv[3] || 12);
if (!path.isAbsolute(root) || !Number.isInteger(keep) || keep < 2 || keep > 100) {
  throw new Error('Usage: prune-data-releases.mjs ABSOLUTE_DATA_ROOT KEEP_COUNT');
}

const releases = path.join(root, 'releases');
const current = fs.existsSync(path.join(root, 'current'))
  ? fs.realpathSync(path.join(root, 'current'))
  : '';
const entries = fs.readdirSync(releases, { withFileTypes: true })
  .filter((entry) => entry.isDirectory() && /^[a-f0-9]{20}$/.test(entry.name))
  .map((entry) => {
    const filename = path.join(releases, entry.name);
    if (!fs.existsSync(path.join(filename, 'MANIFEST.json'))) {
      throw new Error(`Refusing to prune unrecognized directory: ${filename}`);
    }
    return { filename, modified: fs.statSync(filename).mtimeMs };
  })
  .sort((left, right) => right.modified - left.modified);

for (const entry of entries.slice(keep)) {
  const resolved = fs.realpathSync(entry.filename);
  if (resolved === current) continue;
  if (path.dirname(resolved) !== fs.realpathSync(releases)) {
    throw new Error(`Refusing to prune outside releases root: ${resolved}`);
  }
  fs.rmSync(resolved, { recursive: true });
  console.log(`pruned=${path.basename(resolved)}`);
}
