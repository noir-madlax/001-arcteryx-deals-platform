import { StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, G, Line, Path, Text as SvgText } from 'react-native-svg';

import { colors, radii } from '../lib/theme';
import type { ChartPoint, Product } from '../lib/types';

type Props = {
  points: ChartPoint[];
  product: Product;
};

const W = 320;
const H = 168;
const PAD_L = 42;
const PAD_R = 14;
const PAD_T = 14;
const PAD_B = 26;

export function PriceChart({ points, product }: Props) {
  if (points.length < 2) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyText}>Not enough price history yet</Text>
      </View>
    );
  }

  const innerW = W - PAD_L - PAD_R;
  const innerH = H - PAD_T - PAD_B;
  const prices = points.flatMap((point) => [point.sale, point.original].filter((value) => value > 0));
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = Math.max(max - min, 1);
  const yMin = Math.max(0, min - range * 0.1);
  const yMax = max + range * 0.1;
  const yRange = yMax - yMin;
  const xOf = (index: number) => PAD_L + (points.length === 1 ? innerW / 2 : (index / (points.length - 1)) * innerW);
  const yOf = (value: number) => PAD_T + innerH - ((value - yMin) / yRange) * innerH;
  const salePath = points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${xOf(index).toFixed(1)} ${yOf(point.sale).toFixed(1)}`).join(' ');
  const minY = yOf(Math.min(...points.map((point) => point.sale))).toFixed(1);
  const last = points[points.length - 1]!;
  const lastX = xOf(points.length - 1);
  const lastY = yOf(last.sale);
  const yTicks = [yMin, (yMin + yMax) / 2, yMax];
  const xTicks = Array.from(new Set([0, Math.floor(points.length / 2), points.length - 1]));

  return (
    <View style={styles.wrap}>
      <Svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H}>
        {yTicks.map((tick) => {
          const y = yOf(tick);
          return (
            <G key={tick}>
              <Line x1={PAD_L} y1={y} x2={W - PAD_R} y2={y} stroke={colors.border} strokeWidth={1} />
              <SvgText x={PAD_L - 6} y={y + 4} textAnchor="end" fill={colors.faint} fontSize={10}>
                {Math.round(tick)}
              </SvgText>
            </G>
          );
        })}
        <Line x1={PAD_L} y1={minY} x2={W - PAD_R} y2={minY} stroke={colors.success} strokeDasharray="5 5" strokeWidth={1.2} />
        <Path d={salePath} fill="none" stroke={colors.danger} strokeWidth={3} strokeLinejoin="round" strokeLinecap="round" />
        <Circle cx={lastX} cy={lastY} r={4.3} fill={colors.danger} />
        {xTicks.map((index) => (
          <SvgText key={`${points[index]?.day}-${index}`} x={xOf(index)} y={H - 7} textAnchor="middle" fill={colors.faint} fontSize={10}>
            {points[index]?.day.slice(5)}
          </SvgText>
        ))}
      </Svg>
      <View style={styles.legend}>
        <Text style={styles.legendText}>Actual sale price</Text>
        <Text style={styles.legendText}>{points.length} points · {product.currency}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    backgroundColor: colors.surface,
    borderRadius: radii.md,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    paddingTop: 8,
    overflow: 'hidden',
  },
  empty: {
    minHeight: 150,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.md,
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
  },
  emptyText: {
    color: colors.muted,
    fontWeight: '700',
  },
  legend: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
    paddingHorizontal: 12,
    paddingVertical: 9,
  },
  legendText: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: '700',
  },
});
