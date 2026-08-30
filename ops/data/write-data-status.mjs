#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

function usage() {
  console.error('Usage: write-data-status.mjs MANIFEST OUTPUT');
  process.exit(2);
}

if (process.argv.length !== 4) usage();

const manifestPath = path.resolve(process.argv[2]);
const outputPath = path.resolve(process.argv[3]);
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
const revisionPattern = /^[a-f0-9]+$/;
if (
  typeof manifest.data_revision !== 'string'
  || manifest.data_revision.length !== 20
  || !revisionPattern.test(manifest.data_revision)
  || typeof manifest.artifact_revision !== 'string'
  || manifest.artifact_revision.length !== 20
  || !revisionPattern.test(manifest.artifact_revision)
  || typeof manifest.code_revision !== 'string'
  || manifest.code_revision.length !== 40
  || !revisionPattern.test(manifest.code_revision)
  || !Number.isInteger(manifest.active_products)
  || manifest.active_products <= 0
) {
  throw new Error('Data manifest identity is invalid');
}

const status = {
  schema_version: 1,
  checked_at: new Date().toISOString(),
  code_revision: manifest.code_revision,
  data_revision: manifest.data_revision,
  artifact_revision: manifest.artifact_revision,
  active_products: manifest.active_products,
  snapshot_observed_at: manifest.snapshot_observed_at,
  release_generated_at: manifest.generated_at,
};
fs.writeFileSync(outputPath, `${JSON.stringify(status, null, 2)}\n`, { flag: 'wx' });
console.log(
  `status_data_revision=${status.data_revision} active_products=${status.active_products} checked_at=${status.checked_at}`,
);
