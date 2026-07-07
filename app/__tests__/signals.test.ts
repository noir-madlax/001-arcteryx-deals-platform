import assert from 'node:assert/strict';
import test from 'node:test';

import { computeSignal, groupHistoryBySku, historyToPoints } from '../lib/signals';
import { daysAgo, product } from './helpers';

test('historyToPoints adds the current product price as the latest point', () => {
  const current = product({ sale_price: 80, original_price: 100, last_updated: daysAgo(0) });
  const points = historyToPoints(
    [
      { sku_id: current.sku_id, sale_price: 100, original_price: 120, recorded_at: daysAgo(5) },
      { sku_id: current.sku_id, sale_price: 90, original_price: 120, recorded_at: daysAgo(2) },
    ],
    current,
  );

  assert.equal(points.length, 3);
  assert.equal(points.at(-1)?.sale, 80);
});

test('computeSignal marks a new absolute low as all_time_low', () => {
  const current = product({ sale_price: 80, original_price: 120, last_updated: daysAgo(0) });
  const signal = computeSignal(current, [
    { sku_id: current.sku_id, sale_price: 100, original_price: 120, recorded_at: daysAgo(10) },
    { sku_id: current.sku_id, sale_price: 90, original_price: 120, recorded_at: daysAgo(2) },
  ]);

  assert.equal(signal.kind, 'all_time_low');
  assert.equal(signal.label, 'All-time low');
  assert.equal(signal.isLow, true);
});

test('computeSignal marks a 90-day low when older history was lower', () => {
  const current = product({ sale_price: 80, original_price: 120, last_updated: daysAgo(0) });
  const signal = computeSignal(current, [
    { sku_id: current.sku_id, sale_price: 50, original_price: 120, recorded_at: daysAgo(120) },
    { sku_id: current.sku_id, sale_price: 90, original_price: 120, recorded_at: daysAgo(10) },
    { sku_id: current.sku_id, sale_price: 85, original_price: 120, recorded_at: daysAgo(2) },
  ]);

  assert.equal(signal.kind, 'ninety_day_low');
  assert.equal(signal.label, '90-day low');
  assert.equal(signal.minPrice, 50);
});

test('computeSignal marks a fresh drop only when it is not a low', () => {
  const current = product({ sale_price: 90, original_price: 120, last_updated: daysAgo(0) });
  const signal = computeSignal(current, [
    { sku_id: current.sku_id, sale_price: 70, original_price: 120, recorded_at: daysAgo(20) },
    { sku_id: current.sku_id, sale_price: 95, original_price: 120, recorded_at: daysAgo(2) },
  ]);

  assert.equal(signal.kind, 'drop_today');
  assert.equal(signal.label, '↓ $5 today');
});

test('computeSignal marks steady prices as neutral', () => {
  const current = product({ sale_price: 90, original_price: 120, last_updated: daysAgo(0) });
  const signal = computeSignal(current, [
    { sku_id: current.sku_id, sale_price: 70, original_price: 120, recorded_at: daysAgo(20) },
    { sku_id: current.sku_id, sale_price: 80, original_price: 120, recorded_at: daysAgo(2) },
  ]);

  assert.equal(signal.kind, 'steady');
  assert.equal(signal.label, 'Steady · not a low');
  assert.equal(signal.isLow, false);
});

test('computeSignal hides signal text when history is insufficient', () => {
  const current = product({ sale_price: 90, original_price: 120, last_updated: daysAgo(0) });
  const signal = computeSignal(current, [{ sku_id: current.sku_id, sale_price: 100, original_price: 120, recorded_at: daysAgo(2) }]);

  assert.equal(signal.kind, 'insufficient');
  assert.equal(signal.label, '');
});

test('groupHistoryBySku ignores empty sku rows', () => {
  const grouped = groupHistoryBySku([
    { sku_id: 'a', sale_price: 100, original_price: 120, recorded_at: daysAgo(2) },
    { sku_id: null, sale_price: 90, original_price: 120, recorded_at: daysAgo(1) },
  ]);

  assert.equal(grouped.get('a')?.length, 1);
  assert.equal(grouped.has(''), false);
});
