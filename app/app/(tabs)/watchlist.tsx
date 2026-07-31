import { Ionicons } from '@expo/vector-icons';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ScreenState } from '../../components/ScreenState';
import { TopoPlaceholder } from '../../components/TopoPlaceholder';
import { useProducts } from '../../contexts/ProductsContext';
import { usePreferences } from '../../contexts/PreferencesContext';
import { useWatchlist } from '../../contexts/WatchlistContext';
import { cleanName, productCategory } from '../../lib/catalog';
import { colors, radii, typography } from '../../lib/theme';
import type { Product, WatchEntry } from '../../lib/types';

export default function WatchlistScreen() {
  const { entries, remove } = useWatchlist();
  const { getProduct } = useProducts();
  const { formatNumber, t } = usePreferences();
  const rows = entries.map((entry) => ({ entry, product: getProduct(entry.skuId) })).filter((row) => row.product);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <FlatList
        data={rows as { entry: WatchEntry; product: Product }[]}
        keyExtractor={(item) => item.entry.skuId}
        contentContainerStyle={styles.content}
        ListHeaderComponent={
          <View style={styles.header}>
            <Text style={styles.title}>{t('watch.title')}</Text>
            <Text style={styles.subtitle}>{t('watch.summary', { saved: formatNumber(entries.length), alerts: formatNumber(entries.filter((entry) => entry.alertTarget).length) })}</Text>
          </View>
        }
        ListEmptyComponent={<ScreenState title={t('watch.emptyTitle')} body={t('watch.emptyBody')} />}
        renderItem={({ item }) => (
          <WatchRow entry={item.entry} product={item.product} onPress={() => router.push({ pathname: '/product/[skuId]', params: { skuId: item.product.sku_id } })} onRemove={() => remove(item.product.sku_id)} />
        )}
        ListFooterComponent={<ProGuide />}
      />
    </SafeAreaView>
  );
}

function WatchRow({ entry, product, onPress, onRemove }: { entry: WatchEntry; product: Product; onPress: () => void; onRemove: () => void }) {
  const { categoryLabel, formatMoney, t } = usePreferences();
  const delta = product.sale_price - entry.savedPrice;
  const down = delta < 0;
  const same = Math.abs(delta) < 0.01;
  const text = same ? t('watch.noChange') : t('watch.sinceSaved', { direction: down ? '↓' : '↑', amount: formatMoney(Math.abs(delta), product.currency, product.symbol) });
  const imageCandidates = Array.from(new Set([product.image_url, ...product.images].filter(Boolean))) as string[];
  const [failedImages, setFailedImages] = useState<Record<string, boolean>>({});
  const imageUri = imageCandidates.find((uri) => !failedImages[uri]);

  useEffect(() => {
    setFailedImages({});
  }, [product.sku_id]);

  return (
    <Pressable style={styles.row} onPress={onPress}>
      <View style={styles.thumb}>
        <TopoPlaceholder label={categoryLabel(productCategory(product))} showLabel={false} />
        {imageUri ? <Image source={{ uri: imageUri }} style={styles.image} contentFit="cover" transition={140} onError={() => setFailedImages((current) => ({ ...current, [imageUri]: true }))} /> : null}
        <Text style={styles.thumbLabel} numberOfLines={1}>
          {categoryLabel(productCategory(product))}
        </Text>
      </View>
      <View style={styles.rowBody}>
        <View style={styles.rowHead}>
          <Text style={styles.name} numberOfLines={1}>
            {cleanName(product.full_name || product.model)}
          </Text>
          <Pressable accessibilityRole="button" accessibilityLabel={t('watch.remove')} style={styles.removeButton} onPress={onRemove} hitSlop={10}>
            <Ionicons name="close" size={15} color={colors.faint} />
          </Pressable>
        </View>
        <View style={styles.deltaRow}>
          {down ? <Ionicons name="arrow-down" size={12} color={colors.buy} /> : null}
          <Text style={[styles.statusText, down ? styles.goodText : styles.flatText]}>{text}</Text>
        </View>
        {entry.alertTarget ? (
          <View style={styles.alertLine}>
            <Ionicons name="notifications-outline" size={12} color={colors.ink2} />
            <Text style={styles.alert}>{t('watch.alertAt')} <Text style={styles.mono}>{formatMoney(entry.alertTarget, product.currency, product.symbol)}</Text></Text>
          </View>
        ) : null}
        <Text style={styles.current}>
          <Text style={styles.mono}>{formatMoney(product.sale_price, product.currency, product.symbol)}</Text> <Text style={styles.currentUnit}>{t('watch.now')}</Text>
        </Text>
      </View>
    </Pressable>
  );
}

function ProGuide() {
  const { t } = usePreferences();
  return (
    <Pressable style={styles.proGuide} onPress={() => router.push('/paywall')}>
      <View>
        <Text style={styles.proTitle}>{t('watch.proTitle')}</Text>
        <Text style={styles.proSub}>{t('watch.proSub')}</Text>
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
    gap: 0,
  },
  header: {
    marginBottom: 12,
  },
  title: {
    color: colors.ink,
    fontSize: 28,
    lineHeight: 34,
    fontWeight: '900',
    letterSpacing: 0,
  },
  subtitle: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: '700',
  },
  row: {
    minHeight: 88,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 11,
    paddingVertical: 13,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
  },
  thumb: {
    width: 58,
    aspectRatio: 4 / 5,
    overflow: 'hidden',
    borderRadius: 11,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    backgroundColor: colors.photo,
  },
  image: {
    position: 'absolute',
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    width: '100%',
    height: '100%',
  },
  thumbLabel: {
    position: 'absolute',
    left: 6,
    bottom: 5,
    maxWidth: '80%',
    color: colors.photoCat,
    fontSize: 8.5,
    fontWeight: '900',
    letterSpacing: 0.6,
    textTransform: 'uppercase',
  },
  rowBody: {
    flex: 1,
    minWidth: 0,
  },
  rowHead: {
    minHeight: 20,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusText: {
    color: colors.muted,
    fontWeight: '800',
    fontSize: 11.5,
  },
  goodText: {
    color: colors.buy,
  },
  flatText: {
    color: colors.muted,
  },
  current: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: '700',
  },
  alert: {
    color: colors.ink2,
    fontSize: 11.5,
    fontWeight: '800',
  },
  name: {
    flex: 1,
    color: colors.ink,
    fontSize: 13.5,
    fontWeight: '800',
  },
  removeButton: {
    width: 24,
    height: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  deltaRow: {
    marginTop: 2,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  alertLine: {
    marginTop: 3,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  mono: {
    fontFamily: typography.mono,
    fontVariant: typography.tabular,
  },
  currentUnit: {
    color: colors.faint,
    fontSize: 10.5,
    fontWeight: '600',
  },
  proGuide: {
    minHeight: 72,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
    borderRadius: radii.lg,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.borderStrong,
    backgroundColor: colors.card,
    padding: 13,
    marginTop: 14,
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
