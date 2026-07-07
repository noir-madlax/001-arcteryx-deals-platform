import { Ionicons } from '@expo/vector-icons';
import { useEffect, useState } from 'react';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';

import { cleanName, formatPrice, freshnessLabel, productCategory, REGION_LABEL, staleDays } from '../lib/catalog';
import { colors, radii, shadow } from '../lib/theme';
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
  const name = cleanName(product.full_name || product.model);
  const imageUri = product.image_url || product.images[0];
  const [imageFailed, setImageFailed] = useState(false);
  const stale = staleDays(product.last_updated) > 3;
  const signalLabel = signal?.label || (signal?.kind === 'insufficient' ? `${product.discount_pct}% off` : 'Checking price signal');
  const tone = signal?.tone === 'success' ? styles.signalSuccess : styles.signalNeutral;

  useEffect(() => {
    setImageFailed(false);
  }, [imageUri]);

  return (
    <Pressable style={[styles.card, hero && styles.heroCard]} onPress={onPress}>
      <View style={[styles.imageWrap, hero && styles.heroImageWrap]}>
        {imageUri && !imageFailed ? <Image source={{ uri: imageUri }} style={styles.image} resizeMode="cover" onError={() => setImageFailed(true)} /> : <View style={styles.imageFallback}><Text style={styles.fallbackText}>{name}</Text></View>}
        <View style={styles.discountBadge}>
          <Text style={styles.discountText}>-{product.discount_pct}%</Text>
        </View>
        {onToggleSave ? (
          <Pressable style={styles.saveButton} onPress={onToggleSave} hitSlop={10}>
            <Ionicons name={saved ? 'heart' : 'heart-outline'} color={saved ? colors.danger : colors.ink} size={18} />
          </Pressable>
        ) : null}
      </View>
      <View style={styles.body}>
        <View style={styles.metaRow}>
          <Text style={styles.category} numberOfLines={1}>{productCategory(product)}</Text>
          <Text style={styles.region} numberOfLines={1}>{REGION_LABEL[product.region] || product.region.toUpperCase()}</Text>
        </View>
        <Text style={[styles.name, hero && styles.heroName]} numberOfLines={hero ? 2 : 2}>{name}</Text>
        <View style={styles.signalRow}>
          <View style={[styles.signalPill, tone]}>
            <Text style={[styles.signalText, signal?.tone === 'success' && styles.signalTextSuccess]} numberOfLines={1}>{signalLabel}</Text>
          </View>
          {stale ? <Text style={styles.stale}>{freshnessLabel(product.last_updated)}</Text> : null}
        </View>
        <View style={styles.priceRow}>
          <Text style={styles.sale}>{formatPrice(product.sale_price, product.symbol)}</Text>
          {product.original_price > product.sale_price ? <Text style={styles.original}>{formatPrice(product.original_price, product.symbol)}</Text> : null}
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radii.md,
    overflow: 'hidden',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    ...shadow,
  },
  heroCard: {
    marginHorizontal: 20,
  },
  imageWrap: {
    height: 190,
    backgroundColor: colors.surfaceAlt,
  },
  heroImageWrap: {
    height: 260,
  },
  image: {
    width: '100%',
    height: '100%',
  },
  imageFallback: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 18,
  },
  fallbackText: {
    color: colors.muted,
    textAlign: 'center',
    fontWeight: '700',
  },
  discountBadge: {
    position: 'absolute',
    left: 10,
    top: 10,
    backgroundColor: colors.danger,
    borderRadius: radii.sm,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  discountText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '800',
  },
  saveButton: {
    position: 'absolute',
    right: 10,
    top: 10,
    width: 34,
    height: 34,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 17,
    backgroundColor: 'rgba(255,255,255,0.88)',
  },
  body: {
    padding: 12,
    gap: 8,
  },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 8,
  },
  category: {
    flex: 1,
    color: colors.faint,
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  region: {
    maxWidth: 130,
    color: colors.faint,
    fontSize: 11,
    fontWeight: '600',
  },
  name: {
    color: colors.ink,
    fontSize: 15,
    lineHeight: 20,
    fontWeight: '800',
  },
  heroName: {
    fontSize: 20,
    lineHeight: 26,
  },
  signalRow: {
    minHeight: 28,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  signalPill: {
    flexShrink: 1,
    borderRadius: radii.sm,
    paddingHorizontal: 9,
    paddingVertical: 5,
  },
  signalSuccess: {
    backgroundColor: colors.successSoft,
  },
  signalNeutral: {
    backgroundColor: colors.surfaceAlt,
  },
  signalText: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: '800',
  },
  signalTextSuccess: {
    color: colors.success,
  },
  stale: {
    color: colors.danger,
    fontSize: 12,
    fontWeight: '700',
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 8,
  },
  sale: {
    color: colors.danger,
    fontSize: 19,
    fontWeight: '900',
  },
  original: {
    color: colors.faint,
    fontSize: 13,
    textDecorationLine: 'line-through',
    fontWeight: '600',
  },
});
