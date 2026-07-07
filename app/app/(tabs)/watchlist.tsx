import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { DealCard } from '../../components/DealCard';
import { ScreenState } from '../../components/ScreenState';
import { useProducts } from '../../contexts/ProductsContext';
import { useWatchlist } from '../../contexts/WatchlistContext';
import { cleanName, formatPrice } from '../../lib/catalog';
import { colors, radii } from '../../lib/theme';
import type { Product, WatchEntry } from '../../lib/types';

export default function WatchlistScreen() {
  const { entries, remove } = useWatchlist();
  const { getProduct, signals } = useProducts();
  const rows = entries.map((entry) => ({ entry, product: getProduct(entry.skuId) })).filter((row) => row.product);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <FlatList
        data={rows as { entry: WatchEntry; product: Product }[]}
        keyExtractor={(item) => item.entry.skuId}
        contentContainerStyle={styles.content}
        ListHeaderComponent={
          <View style={styles.header}>
            <Text style={styles.title}>Watchlist</Text>
            <Text style={styles.subtitle}>{entries.length} saved · price movement since saved</Text>
          </View>
        }
        ListEmptyComponent={<ScreenState title="No saved deals" body="Save a product from Deals or the detail screen to track it here." />}
        renderItem={({ item }) => (
          <View style={styles.row}>
            <DealCard
              product={item.product}
              signal={signals[item.product.sku_id]}
              saved
              onPress={() => router.push({ pathname: '/product/[skuId]', params: { skuId: item.product.sku_id } })}
              onToggleSave={() => remove(item.product.sku_id)}
            />
            <WatchStatus entry={item.entry} product={item.product} />
          </View>
        )}
        ListFooterComponent={<ProGuide />}
      />
    </SafeAreaView>
  );
}

function WatchStatus({ entry, product }: { entry: WatchEntry; product: Product }) {
  const delta = product.sale_price - entry.savedPrice;
  const down = delta < 0;
  const same = Math.abs(delta) < 0.01;
  const text = same ? 'No change since saved' : `${down ? '↓' : '↑'} ${formatPrice(Math.abs(delta), product.symbol)} since you saved`;

  return (
    <View style={styles.status}>
      <View style={[styles.statusPill, down ? styles.goodPill : styles.neutralPill]}>
        <Text style={[styles.statusText, down && styles.goodText]}>{text}</Text>
      </View>
      <Text style={styles.current}>
        Current {formatPrice(product.sale_price, product.symbol)} · saved {formatPrice(entry.savedPrice, entry.symbol)}
      </Text>
      {entry.alertTarget ? <Text style={styles.alert}>Alert at {formatPrice(entry.alertTarget, product.symbol)}</Text> : null}
      <Text style={styles.name} numberOfLines={1}>{cleanName(product.full_name || product.model)}</Text>
    </View>
  );
}

function ProGuide() {
  return (
    <Pressable style={styles.proGuide} onPress={() => router.push('/paywall')}>
      <View>
        <Text style={styles.proTitle}>Unlimited alerts with Pro</Text>
        <Text style={styles.proSub}>Unlock full history, richer lows, and more room to track gear.</Text>
      </View>
      <Ionicons name="chevron-forward" size={20} color={colors.ink} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  content: {
    padding: 20,
    paddingBottom: 32,
    gap: 14,
  },
  header: {
    marginBottom: 4,
  },
  title: {
    color: colors.ink,
    fontSize: 34,
    lineHeight: 40,
    fontWeight: '900',
  },
  subtitle: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: '700',
  },
  row: {
    gap: 8,
  },
  status: {
    gap: 6,
    borderRadius: radii.md,
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    padding: 12,
  },
  statusPill: {
    alignSelf: 'flex-start',
    borderRadius: radii.sm,
    paddingHorizontal: 9,
    paddingVertical: 5,
  },
  goodPill: {
    backgroundColor: colors.successSoft,
  },
  neutralPill: {
    backgroundColor: colors.surfaceAlt,
  },
  statusText: {
    color: colors.muted,
    fontWeight: '900',
    fontSize: 12,
  },
  goodText: {
    color: colors.success,
  },
  current: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: '700',
  },
  alert: {
    color: colors.accent,
    fontSize: 13,
    fontWeight: '800',
  },
  name: {
    color: colors.faint,
    fontSize: 12,
    fontWeight: '700',
  },
  proGuide: {
    minHeight: 80,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderRadius: radii.md,
    backgroundColor: colors.accentSoft,
    padding: 16,
    marginTop: 8,
  },
  proTitle: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: '900',
  },
  proSub: {
    color: colors.muted,
    marginTop: 4,
    fontSize: 13,
    fontWeight: '700',
  },
});
