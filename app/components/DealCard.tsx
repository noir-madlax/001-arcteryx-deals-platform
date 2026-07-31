import { Ionicons } from '@expo/vector-icons';
import { Image } from 'expo-image';
import { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { TopoPlaceholder } from './TopoPlaceholder';
import { usePreferences } from '../contexts/PreferencesContext';
import { cleanName, freshnessLabel, productCategory, staleDays } from '../lib/catalog';
import { colors, radii, typography } from '../lib/theme';
import type { DealSignal, Product } from '../lib/types';

type Props = {
  product: Product;
  signal?: DealSignal;
  saved?: boolean;
  hero?: boolean;
  onPress: () => void;
  onToggleSave?: () => void;
};

export function DealCard({ product, signal, saved = false, hero = false, onPress, onToggleSave }: Props) {
  const { categoryLabel, formatMoney, t } = usePreferences();
  const name = cleanName(product.full_name || product.model);
  const imageCandidates = Array.from(new Set([product.image_url, ...product.images].filter(Boolean))) as string[];
  const [failedImages, setFailedImages] = useState<Record<string, boolean>>({});
  const imageUri = imageCandidates.find((uri) => !failedImages[uri]);
  const stale = staleDays(product.last_updated) > 3;
  const category = categoryLabel(productCategory(product));
  const allTimeLow = signal?.kind === 'all_time_low';
  const signalLabel = stale
    ? t('signal.seen', { when: freshnessLabel(product.last_updated) })
    : signal?.kind === 'all_time_low'
      ? t('signal.all_time_low')
      : signal?.kind === 'ninety_day_low'
        ? t('signal.ninety_day_low')
        : signal?.kind === 'drop_today' && signal.dropAmount
          ? t('signal.drop_today', { amount: formatMoney(signal.dropAmount, product.currency, product.symbol) })
          : signal?.kind === 'steady'
            ? t('signal.steady')
            : signal?.kind === 'insufficient'
              ? t('signal.off', { percent: product.discount_pct })
              : t('signal.checking');
  const signalStyle = stale ? styles.signalStale : signal?.tone === 'success' ? styles.signalGood : styles.signalFlat;

  useEffect(() => {
    setFailedImages({});
  }, [product.sku_id]);

  return (
    <Pressable style={[styles.card, hero && styles.heroCard]} onPress={onPress}>
      <View style={styles.imageWrap}>
        <TopoPlaceholder label={category} showLabel={false} />
        {imageUri ? <Image source={{ uri: imageUri }} style={styles.image} contentFit="cover" transition={160} onError={() => setFailedImages((current) => ({ ...current, [imageUri]: true }))} /> : null}
        {allTimeLow ? (
          <View style={styles.lowRibbon}>
            <Ionicons name="star" size={9} color="#FFFFFF" />
            <Text style={styles.lowRibbonText}>{t('signal.all_time_low')}</Text>
          </View>
        ) : (
          <View style={styles.imageBadge}>
            <Text style={styles.imageBadgeText}>-{product.discount_pct}%</Text>
          </View>
        )}
        <View style={styles.regionBadge}>
          <Text style={styles.regionBadgeText}>{regionFlag(product.region)}</Text>
        </View>
        {onToggleSave ? (
          <Pressable accessibilityRole="button" accessibilityLabel={saved ? t('watch.remove') : t('watch.save')} style={styles.saveButton} onPress={onToggleSave} hitSlop={10}>
            <Ionicons name={saved ? 'heart' : 'heart-outline'} color={saved ? colors.disc : colors.ink} size={16} />
          </Pressable>
        ) : null}
        <Text style={styles.imageLabel} numberOfLines={1}>
          {category}
        </Text>
      </View>
      <View style={styles.body}>
        <Text style={[styles.name, hero && styles.heroName]} numberOfLines={2}>
          {name}
        </Text>
        {hero ? (
          <Text style={styles.meta} numberOfLines={1}>
            {[product.color, product.gender].filter(Boolean).join(' · ')}
          </Text>
        ) : null}
        <View style={styles.priceRow}>
          <Text style={[styles.sale, hero && styles.heroSale]}>{formatMoney(product.sale_price, product.currency, product.symbol)}</Text>
          {product.original_price > product.sale_price ? <Text style={styles.original}>{formatMoney(product.original_price, product.currency, product.symbol)}</Text> : null}
        </View>
        <Text style={[styles.signal, signalStyle]} numberOfLines={1}>
          {signalLabel}
        </Text>
      </View>
    </Pressable>
  );
}

function regionFlag(region: string) {
  const flags: Record<string, string> = {
    us: '🇺🇸',
    ca: '🇨🇦',
    gb: '🇬🇧',
    de: '🇩🇪',
    fr: '🇫🇷',
    nl: '🇳🇱',
    jp: '🇯🇵',
  };
  return flags[region] || region.toUpperCase();
}

const numeric = {
  fontFamily: typography.mono,
  fontVariant: typography.tabular,
};

const styles = StyleSheet.create({
  card: {
    flex: 1,
    gap: 7,
    paddingBottom: 12,
  },
  heroCard: {
    paddingBottom: 12,
  },
  imageWrap: {
    width: '100%',
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
  imageBadge: {
    position: 'absolute',
    top: 7,
    left: 7,
    borderRadius: radii.sm,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.discLine,
    backgroundColor: colors.onPhotoBadge,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  imageBadgeText: {
    ...numeric,
    color: colors.onPhotoDisc,
    fontSize: 10,
    fontWeight: '900',
  },
  lowRibbon: {
    position: 'absolute',
    top: 7,
    left: 7,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    borderRadius: radii.sm,
    backgroundColor: '#1E7A52',
    paddingHorizontal: 6,
    paddingVertical: 3,
  },
  lowRibbonText: {
    color: '#FFFFFF',
    fontSize: 9.5,
    fontWeight: '900',
  },
  regionBadge: {
    position: 'absolute',
    top: 7,
    right: 7,
    minWidth: 20,
    minHeight: 16,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 4,
    backgroundColor: colors.onPhotoBadge,
  },
  regionBadgeText: {
    fontSize: 11,
    fontFamily: typography.mono,
    fontVariant: typography.tabular,
  },
  imageLabel: {
    position: 'absolute',
    left: 8,
    bottom: 7,
    maxWidth: '80%',
    color: colors.photoCat,
    fontSize: 8.5,
    fontWeight: '900',
    letterSpacing: 0.6,
    textTransform: 'uppercase',
  },
  body: {
    minWidth: 0,
    gap: 4,
  },
  name: {
    color: colors.ink,
    fontSize: 13.5,
    lineHeight: 17,
    fontWeight: '800',
  },
  heroName: {
    fontSize: 14.5,
    lineHeight: 19,
  },
  meta: {
    color: colors.muted,
    marginTop: 1,
    fontSize: 11.5,
    fontWeight: '600',
  },
  saveButton: {
    position: 'absolute',
    right: 7,
    bottom: 7,
    width: 26,
    height: 26,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 14,
    backgroundColor: colors.onPhotoBadge,
  },
  signal: {
    fontSize: 11.5,
    lineHeight: 15,
    fontWeight: '700',
  },
  signalGood: {
    color: colors.buy,
  },
  signalFlat: {
    color: colors.muted,
    fontWeight: '600',
  },
  signalStale: {
    color: colors.faint,
    fontWeight: '600',
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    flexWrap: 'wrap',
    gap: 7,
  },
  sale: {
    ...numeric,
    color: colors.disc,
    fontSize: 14.5,
    fontWeight: '900',
    letterSpacing: 0,
  },
  heroSale: {
    fontSize: 17,
  },
  original: {
    ...numeric,
    color: colors.faint,
    fontSize: 11.5,
    textDecorationLine: 'line-through',
    fontWeight: '700',
  },
});
