import type { ChartPoint, DealSignal, PriceHistoryRow, Product } from './types';
import { formatPrice } from './catalog';

export function historyToPoints(rows: PriceHistoryRow[], current?: Product | null) {
  const byDay = new Map<string, ChartPoint>();

  for (const row of rows) {
    const day = (row.recorded_at || '').slice(0, 10);
    const sale = Number(row.sale_price || 0);
    if (!day || sale <= 0) continue;
    byDay.set(day, {
      day,
      sale,
      original: Number(row.original_price || 0),
    });
  }

  if (current?.sale_price) {
    const day = (current.last_updated || new Date().toISOString()).slice(0, 10);
    byDay.set(day, {
      day,
      sale: current.sale_price,
      original: current.original_price,
    });
  }

  return [...byDay.values()].sort((a, b) => a.day.localeCompare(b.day));
}

export function recentPoints(points: ChartPoint[], days: number) {
  const cutoff = Date.now() - days * 86400000;
  return points.filter((point) => {
    const stamp = Date.parse(`${point.day}T00:00:00Z`);
    return !Number.isNaN(stamp) && stamp >= cutoff;
  });
}

export function computeSignal(product: Product, historyRows: PriceHistoryRow[]): DealSignal {
  const historyOnly = historyToPoints(historyRows, null);
  const points = historyToPoints(historyRows, product);
  const current = product.sale_price;

  if (historyOnly.length < 2 || points.length < 2) {
    return {
      kind: 'insufficient',
      label: '',
      tone: 'neutral',
      verdict: 'Not enough price history yet',
      isLow: false,
      minPrice: null,
      pointCount: historyOnly.length,
    };
  }

  const minAll = Math.min(...points.map((point) => point.sale).filter((value) => value > 0));
  const ninety = recentPoints(points, 90);
  const min90 = ninety.length ? Math.min(...ninety.map((point) => point.sale).filter((value) => value > 0)) : minAll;
  const latestHistory = historyOnly[historyOnly.length - 1];

  if (current <= minAll) {
    return {
      kind: 'all_time_low',
      label: 'All-time low',
      tone: 'success',
      verdict: 'Good time to buy — at/near all-time low',
      isLow: true,
      minPrice: minAll,
      pointCount: points.length,
    };
  }

  if (current <= min90) {
    return {
      kind: 'ninety_day_low',
      label: '90-day low',
      tone: 'success',
      verdict: 'Good time to buy — at/near all-time low',
      isLow: true,
      minPrice: minAll,
      pointCount: points.length,
    };
  }

  if (latestHistory && current < latestHistory.sale) {
    const delta = latestHistory.sale - current;
    return {
      kind: 'drop_today',
      label: `↓ ${formatPrice(delta, product.symbol)} today`,
      tone: 'success',
      verdict: 'Often cheaper — consider waiting',
      isLow: false,
      minPrice: minAll,
      pointCount: points.length,
    };
  }

  return {
    kind: 'steady',
    label: 'Steady · not a low',
    tone: 'neutral',
    verdict: 'Often cheaper — consider waiting',
    isLow: false,
    minPrice: minAll,
    pointCount: points.length,
  };
}

export function groupHistoryBySku(rows: PriceHistoryRow[]) {
  const grouped = new Map<string, PriceHistoryRow[]>();
  for (const row of rows) {
    if (!row.sku_id) continue;
    const list = grouped.get(row.sku_id) || [];
    list.push(row);
    grouped.set(row.sku_id, list);
  }
  return grouped;
}
