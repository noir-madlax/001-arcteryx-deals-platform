import { Ionicons } from '@expo/vector-icons';
import { BlurView } from 'expo-blur';
import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Alert, Image, Pressable, ScrollView, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { AlertModal } from '../../components/AlertModal';
import { PriceChart } from '../../components/PriceChart';
import { ScreenState } from '../../components/ScreenState';
import { useProducts } from '../../contexts/ProductsContext';
import { usePro } from '../../contexts/ProContext';
import { useWatchlist } from '../../contexts/WatchlistContext';
import { cleanName, formatPrice, GENDER_LABEL, productCategory, REGION_LABEL, releaseSeason } from '../../lib/catalog';
import { openBuyUrl, scheduleTestPriceNotification, softImpact, uuid4 } from '../../lib/actions';
import { computeSignal, historyToPoints, recentPoints } from '../../lib/signals';
import { fetchPriceHistory, fetchProductFamilyBySku, insertPriceAlert } from '../../lib/supabase';
import { colors, radii, shadow } from '../../lib/theme';
import type { PriceHistoryRow, Product } from '../../lib/types';

export default function ProductDetailScreen() {
  const { skuId } = useLocalSearchParams<{ skuId: string }>();
  const { getProduct, cheaperAlternatives } = useProducts();
  const watchlist = useWatchlist();
  const { isPro } = usePro();
  const [fallbackFamily, setFallbackFamily] = useState<Product[]>([]);
  const [history, setHistory] = useState<PriceHistoryRow[]>([]);
  const [loadingProduct, setLoadingProduct] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [alertOpen, setAlertOpen] = useState(false);
  const { width } = useWindowDimensions();
  const contextProduct = getProduct(skuId);
  const product = contextProduct || fallbackFamily.find((row) => row.sku_id === skuId) || fallbackFamily[0];

  useEffect(() => {
    if (!skuId || contextProduct) return;
    setLoadingProduct(true);
    fetchProductFamilyBySku(skuId)
      .then(setFallbackFamily)
      .finally(() => setLoadingProduct(false));
  }, [contextProduct, skuId]);

  useEffect(() => {
    if (!product?.sku_id) return;
    setLoadingHistory(true);
    fetchPriceHistory(product.sku_id)
      .then(setHistory)
      .finally(() => setLoadingHistory(false));
  }, [product?.sku_id]);

  const points = useMemo(() => (product ? historyToPoints(history, product) : []), [history, product]);
  const chartPoints = useMemo(() => (isPro ? points : recentPoints(points, 30)), [isPro, points]);
  const signal = useMemo(() => (product ? computeSignal(product, history) : null), [history, product]);
  const alternatives = product ? cheaperAlternatives(product) : [];
  const saved = product ? watchlist.isSaved(product.sku_id) : false;

  if (!product && loadingProduct) {
    return <ScreenState title="Loading product" body="Checking the latest price." loading />;
  }

  if (!product) {
    return <ScreenState title="Product not found" body="It may be sold out or removed from the catalog." />;
  }

  const currentProduct = product;
  const name = cleanName(currentProduct.full_name || currentProduct.model);
  const images = (currentProduct.images.length ? currentProduct.images : [currentProduct.image_url]).filter(Boolean) as string[];
  const season = releaseSeason(currentProduct);

  async function submitAlert(email: string, target: number | null) {
    await insertPriceAlert({
      email,
      sku_id: currentProduct.sku_id,
      target_price: target,
      last_price_seen: currentProduct.sale_price,
      currency: currentProduct.currency,
      region: currentProduct.region,
      product_name: name,
      product_url: currentProduct.url || '',
      image_url: currentProduct.image_url || '',
      unsubscribe_token: uuid4(),
    });
    await watchlist.setAlertTarget(currentProduct, target);
    await scheduleTestPriceNotification(name);
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.nav}>
          <Pressable style={styles.iconButton} onPress={() => router.back()}>
            <Ionicons name="chevron-back" size={24} color={colors.ink} />
          </Pressable>
          <Pressable
            style={styles.iconButton}
            onPress={async () => {
              const savedNow = await watchlist.toggle(currentProduct);
              if (!savedNow) {
                Alert.alert('Watchlist limit reached', `Free watchlists hold ${watchlist.freeLimit} items. Upgrade to Pro for unlimited saves.`);
              }
            }}
          >
            <Ionicons name={saved ? 'heart' : 'heart-outline'} size={23} color={saved ? colors.danger : colors.ink} />
          </Pressable>
        </View>

        <ScrollView horizontal pagingEnabled showsHorizontalScrollIndicator={false} style={styles.gallery}>
          {images.map((uri) => (
            <View style={[styles.imageFrame, { width }]} key={uri}>
              <Image source={{ uri }} resizeMode="cover" style={styles.image} />
            </View>
          ))}
        </ScrollView>

        <View style={styles.block}>
          <Text style={styles.category}>{productCategory(currentProduct)}</Text>
          <Text style={styles.title}>{name}</Text>
          <Text style={styles.meta}>{[currentProduct.color, GENDER_LABEL[currentProduct.gender || ''] || currentProduct.gender, REGION_LABEL[currentProduct.region] || currentProduct.region.toUpperCase(), season].filter(Boolean).join(' · ')}</Text>
        </View>

        <View style={styles.priceBlock}>
          <Text style={styles.sale}>{formatPrice(currentProduct.sale_price, currentProduct.symbol)}</Text>
          {currentProduct.original_price > currentProduct.sale_price ? <Text style={styles.original}>{formatPrice(currentProduct.original_price, currentProduct.symbol)}</Text> : null}
          <View style={styles.discount}>
            <Text style={styles.discountText}>-{currentProduct.discount_pct}%</Text>
          </View>
          {isPro && signal?.kind === 'all_time_low' ? (
            <View style={styles.lowBadge}>
              <Text style={styles.lowBadgeText}>All-time low</Text>
            </View>
          ) : null}
        </View>

        <View style={styles.section}>
          <View style={styles.sectionHead}>
            <Text style={styles.sectionTitle}>Price history</Text>
            {loadingHistory ? <ActivityIndicator color={colors.accent} /> : <Text style={styles.sectionMeta}>{isPro ? 'Full history' : 'Last 30 days'}</Text>}
          </View>
          <View style={styles.chartWrap}>
            <PriceChart points={chartPoints} product={currentProduct} />
            {!isPro ? (
              <BlurView intensity={22} tint="light" style={styles.paywallOverlay}>
                <Text style={styles.paywallTitle}>Upgrade for full history</Text>
                <Text style={styles.paywallSub}>Unlock all-time lows and cross-season context.</Text>
                <Pressable style={styles.paywallButton} onPress={() => router.push('/paywall')}>
                  <Text style={styles.paywallButtonText}>View Pro</Text>
                </Pressable>
              </BlurView>
            ) : null}
          </View>
        </View>

        {signal ? (
          <View style={[styles.verdict, signal.isLow ? styles.verdictGood : styles.verdictNeutral]}>
            <Text style={[styles.verdictText, signal.isLow && styles.verdictGoodText]}>{signal.verdict}</Text>
          </View>
        ) : null}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Also cheaper</Text>
          {alternatives.length ? (
            <View style={styles.alternatives}>
              {alternatives.map((item) => (
                <Pressable key={item.sku_id} style={styles.altPill} onPress={() => router.push({ pathname: '/product/[skuId]', params: { skuId: item.sku_id } })}>
                  <Text style={styles.altText}>{REGION_LABEL[item.region] || item.region.toUpperCase()} {formatPrice(item.sale_price, item.symbol)}</Text>
                </Pressable>
              ))}
            </View>
          ) : (
            <Text style={styles.muted}>No cheaper region in the loaded catalog.</Text>
          )}
        </View>

        <View style={styles.actions}>
          <Pressable
            style={[styles.actionButton, styles.alertButton]}
            onPress={async () => {
              await softImpact();
              setAlertOpen(true);
            }}
          >
            <Ionicons name="notifications-outline" size={18} color={colors.ink} />
            <Text style={styles.alertText}>Alert</Text>
          </Pressable>
          <Pressable style={[styles.actionButton, styles.buyButton]} onPress={() => openBuyUrl(currentProduct.url)}>
            <Text style={styles.buyText}>Buy</Text>
            <Ionicons name="open-outline" size={18} color="#fff" />
          </Pressable>
        </View>
      </ScrollView>
      <AlertModal visible={alertOpen} product={currentProduct} onClose={() => setAlertOpen(false)} onSubmit={submitAlert} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  content: {
    paddingBottom: 34,
  },
  nav: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  iconButton: {
    width: 42,
    height: 42,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 21,
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
  },
  gallery: {
    width: '100%',
  },
  imageFrame: {
    aspectRatio: 4 / 5,
    backgroundColor: colors.surfaceAlt,
  },
  image: {
    width: '100%',
    height: '100%',
  },
  block: {
    gap: 8,
    padding: 20,
  },
  category: {
    color: colors.faint,
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  title: {
    color: colors.ink,
    fontSize: 27,
    lineHeight: 33,
    fontWeight: '900',
  },
  meta: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '700',
  },
  priceBlock: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 10,
    marginHorizontal: 20,
    borderRadius: radii.md,
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    padding: 14,
    ...shadow,
  },
  sale: {
    color: colors.danger,
    fontSize: 28,
    fontWeight: '900',
  },
  original: {
    color: colors.faint,
    fontSize: 16,
    fontWeight: '700',
    textDecorationLine: 'line-through',
  },
  discount: {
    borderRadius: radii.sm,
    backgroundColor: colors.dangerSoft,
    paddingHorizontal: 8,
    paddingVertical: 5,
  },
  discountText: {
    color: colors.danger,
    fontWeight: '900',
  },
  lowBadge: {
    borderRadius: radii.sm,
    backgroundColor: colors.successSoft,
    paddingHorizontal: 8,
    paddingVertical: 5,
  },
  lowBadgeText: {
    color: colors.success,
    fontWeight: '900',
  },
  section: {
    gap: 10,
    paddingHorizontal: 20,
    paddingTop: 22,
  },
  sectionHead: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sectionTitle: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: '900',
  },
  sectionMeta: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: '800',
  },
  chartWrap: {
    overflow: 'hidden',
    borderRadius: radii.md,
  },
  paywallOverlay: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 18,
    backgroundColor: 'rgba(247,245,239,0.58)',
  },
  paywallTitle: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: '900',
    textAlign: 'center',
  },
  paywallSub: {
    color: colors.muted,
    fontWeight: '700',
    textAlign: 'center',
  },
  paywallButton: {
    marginTop: 4,
    borderRadius: radii.sm,
    backgroundColor: colors.ink,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  paywallButtonText: {
    color: '#fff',
    fontWeight: '900',
  },
  verdict: {
    marginHorizontal: 20,
    marginTop: 18,
    borderRadius: radii.md,
    padding: 14,
  },
  verdictGood: {
    backgroundColor: colors.successSoft,
  },
  verdictNeutral: {
    backgroundColor: colors.surfaceAlt,
  },
  verdictText: {
    color: colors.muted,
    fontSize: 15,
    fontWeight: '900',
  },
  verdictGoodText: {
    color: colors.success,
  },
  alternatives: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  altPill: {
    borderRadius: radii.sm,
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  altText: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: '800',
  },
  muted: {
    color: colors.muted,
    fontWeight: '700',
  },
  actions: {
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 20,
    paddingTop: 22,
  },
  actionButton: {
    flex: 1,
    minHeight: 52,
    borderRadius: radii.sm,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  alertButton: {
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
  },
  buyButton: {
    backgroundColor: colors.ink,
  },
  alertText: {
    color: colors.ink,
    fontWeight: '900',
  },
  buyText: {
    color: '#fff',
    fontWeight: '900',
  },
});
