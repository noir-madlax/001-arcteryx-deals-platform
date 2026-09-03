import assert from 'node:assert/strict';

import { fetchRateSnapshot, RATE_QUOTES } from '../lib/currency';

async function main() {
  const snapshot = await fetchRateSnapshot();
  for (const currency of RATE_QUOTES) {
    assert.ok((snapshot.rates[currency] ?? 0) > 0, `missing positive ${currency} reference rate`);
  }
  console.log(JSON.stringify({ date: snapshot.date, base: 'EUR', rates: snapshot.rates }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
