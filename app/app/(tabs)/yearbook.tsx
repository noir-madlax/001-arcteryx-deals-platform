import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import {
  FlatList,
  Linking,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import type { GestureResponderEvent } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ScreenState } from '../../components/ScreenState';
import { useProducts } from '../../contexts/ProductsContext';
import { usePreferences } from '../../contexts/PreferencesContext';
import { freshnessLabel, PLATFORM } from '../../lib/catalog';
import { fetchYearbookProducts } from '../../lib/supabase';
import { colors, radii, typography } from '../../lib/theme';
import type { CatalogBrandKey, CatalogGender, CatalogProduct, Product } from '../../lib/types';
import {
  bestYearbookOffers,
  brandLabel,
  categoryLabel,
  filterYearbookArchive,
  filterYearbookProducts,
  formatCatalogPrice,
  groupYearbookArchive,
  indexYearbookDeals,
  yearbookBrands,
  yearbookCategories,
  yearbookYear,
  yearbookYears,
} from '../../lib/yearbook';
import type { YearbookArchiveStyle } from '../../lib/yearbook';

type BrandFilter = 'all' | CatalogBrandKey;
type GenderFilter = 'all' | CatalogGender;
type YearbookScope = 'current' | 'archive';
type YearbookListItem =
  | { kind: 'current'; product: CatalogProduct }
  | { kind: 'archive'; product: YearbookArchiveStyle };

export default function YearbookScreen() {
  const { products: dealProducts, loading: dealsLoading } = useProducts();
  const { formatNumber, genderLabel, t } = usePreferences();
  const [catalogProducts, setCatalogProducts] = useState<CatalogProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [unavailable, setUnavailable] = useState(false);
  const [scope, setScope] = useState<YearbookScope>('current');
  const [query, setQuery] = useState('');
  const [brand, setBrand] = useState<BrandFilter>('all');
  const [gender, setGender] = useState<GenderFilter>('all');
  const [category, setCategory] = useState('all');
  const [year, setYear] = useState<number | 'all'>('all');

  useEffect(() => {
    let active = true;
    fetchYearbookProducts()
      .then((rows) => {
        if (!active) return;
        setCatalogProducts(rows);
        setUnavailable(false);
      })
      .catch(() => {
        if (active) setUnavailable(true);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const dealIndex = useMemo(
    () => indexYearbookDeals(catalogProducts, dealProducts),
    [catalogProducts, dealProducts],
  );
  const archiveProducts = useMemo(
    () => groupYearbookArchive(dealIndex.unmatched),
    [dealIndex.unmatched],
  );
  const currentBrands = useMemo(() => yearbookBrands(catalogProducts), [catalogProducts]);
  const archiveBrands = useMemo(() => {
    const present = new Set(archiveProducts.map((product) => product.brand_key));
    return (['arcteryx', 'burton', 'patagonia'] as CatalogBrandKey[]).filter((value) => present.has(value));
  }, [archiveProducts]);
  const brands = scope === 'current' ? currentBrands : archiveBrands;
  const years = useMemo(() => yearbookYears(catalogProducts), [catalogProducts]);
  const currentCategories = useMemo(() => yearbookCategories(catalogProducts), [catalogProducts]);
  const archiveCategories = useMemo(
    () => [...new Set(archiveProducts.flatMap((product) => product.categories))].sort((left, right) => left.localeCompare(right)),
    [archiveProducts],
  );
  const categories = scope === 'current' ? currentCategories : archiveCategories;
  const visibleCurrent = useMemo(
    () => filterYearbookProducts(catalogProducts, { query, brand, gender, category, year }),
    [catalogProducts, query, brand, gender, category, year],
  );
  const visibleArchive = useMemo(
    () => filterYearbookArchive(archiveProducts, { query, brand, gender, category }),
    [archiveProducts, query, brand, gender, category],
  );
  const listData = useMemo<YearbookListItem[]>(
    () => scope === 'current'
      ? visibleCurrent.map((product) => ({ kind: 'current' as const, product }))
      : visibleArchive.map((product) => ({ kind: 'archive' as const, product })),
    [scope, visibleArchive, visibleCurrent],
  );

  function switchScope(next: YearbookScope) {
    setScope(next);
    setBrand('all');
    setCategory('all');
    if (next === 'archive') setYear('all');
  }

  function filterGenderLabel(value: GenderFilter) {
    if (value === 'all') return t('yearbook.all');
    if (value === 'kids') return t('yearbook.kids');
    return genderLabel(value);
  }

  if (loading) {
    return <ScreenState title={t('yearbook.loadingTitle')} body={t('yearbook.loadingBody')} loading />;
  }
  if (unavailable) {
    return <ScreenState title={t('yearbook.unavailableTitle')} body={t('yearbook.unavailableBody')} />;
  }
  if (!catalogProducts.length) {
    return <ScreenState title={t('yearbook.emptyTitle')} body={t('yearbook.emptyBody')} />;
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <FlatList
        data={listData}
        keyExtractor={(item) => item.kind === 'current' ? item.product.catalog_product_id : item.product.archive_id}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
        ListHeaderComponent={
          <View style={styles.header}>
            <Text style={styles.eyebrow}>{t('yearbook.eyebrow')}</Text>
            <Text style={styles.title}>{t('tabs.yearbook')}</Text>
            <Text style={styles.subtitle}>
              {t('yearbook.summary', { current: formatNumber(catalogProducts.length), archive: formatNumber(archiveProducts.length) })}
            </Text>
            <FilterRail>
              <FilterChip
                active={scope === 'current'}
                label={t('yearbook.current', { count: formatNumber(catalogProducts.length) })}
                onPress={() => switchScope('current')}
              />
              <FilterChip
                active={scope === 'archive'}
                label={t('yearbook.archive', { count: formatNumber(archiveProducts.length) })}
                onPress={() => switchScope('archive')}
              />
            </FilterRail>
            <View style={styles.searchWrap}>
              <Ionicons name="search-outline" size={18} color={colors.faint} />
              <TextInput
                value={query}
                onChangeText={setQuery}
                placeholder={scope === 'current' ? t('yearbook.searchCurrent') : t('yearbook.searchArchive')}
                placeholderTextColor={colors.faint}
                autoCapitalize="none"
                autoComplete="off"
                autoCorrect={false}
                spellCheck={false}
                style={styles.search}
              />
              {query ? (
                <Pressable onPress={() => setQuery('')} hitSlop={10} accessibilityLabel={t('yearbook.clearSearch')}>
                  <Ionicons name="close-circle" size={18} color={colors.faint} />
                </Pressable>
              ) : null}
            </View>
            <FilterRail>
              <FilterChip active={brand === 'all'} label={t('yearbook.allBrands')} onPress={() => setBrand('all')} />
              {brands.map((value) => (
                <FilterChip key={value} active={brand === value} label={brandLabel(value)} onPress={() => setBrand(value)} />
              ))}
            </FilterRail>
            <FilterRail>
              {(['all', 'men', 'women', 'kids', 'unisex'] as GenderFilter[]).map((value) => (
                <FilterChip key={value} active={gender === value} label={filterGenderLabel(value)} onPress={() => setGender(value)} />
              ))}
            </FilterRail>
            {scope === 'current' ? (
              <FilterRail>
                <FilterChip active={year === 'all'} label={t('yearbook.allYears')} onPress={() => setYear('all')} />
                {years.map((value) => <FilterChip key={value} active={year === value} label={String(value)} onPress={() => setYear(value)} />)}
              </FilterRail>
            ) : null}
            <FilterRail>
              <FilterChip active={category === 'all'} label={t('yearbook.allCategories')} onPress={() => setCategory('all')} />
              {categories.map((value) => (
                <FilterChip key={value} active={category === value} label={categoryLabel(value)} onPress={() => setCategory(value)} />
              ))}
            </FilterRail>
            <Text style={styles.resultCount}>{t('yearbook.matching', { count: formatNumber(listData.length) })}</Text>
            <Text style={styles.linkStatus}>
              {dealsLoading
                ? t('yearbook.linking')
                : t('yearbook.linkStatus', { count: formatNumber(Object.keys(dealIndex.byCatalogId).length) })}
            </Text>
          </View>
        }
        ListEmptyComponent={<ScreenState title={t('yearbook.noMatchesTitle')} body={t('yearbook.noMatchesBody')} />}
        renderItem={({ item }) => item.kind === 'current'
          ? <YearbookCard product={item.product} offers={dealIndex.byCatalogId[item.product.catalog_product_id] || []} />
          : <ArchiveCard product={item.product} />}
      />
    </SafeAreaView>
  );
}

function FilterRail({ children }: { children: ReactNode }) {
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filters}>
      {children}
    </ScrollView>
  );
}

function FilterChip({ active, label, onPress }: { active: boolean; label: string; onPress: () => void }) {
  return (
    <Pressable
      style={[styles.chip, active && styles.chipActive]}
      onPress={onPress}
      accessibilityRole="button"
      accessibilityState={{ selected: active }}
    >
      <Text style={[styles.chipText, active && styles.chipTextActive]}>{label}</Text>
    </Pressable>
  );
}

function openDeal(product: Product, event: GestureResponderEvent) {
  event.stopPropagation();
  router.push({ pathname: '/product/[skuId]', params: { skuId: product.sku_id } });
}

function platformLabel(product: Product) {
  return PLATFORM[product._platform]?.label || product._platform.replace(/_/g, ' ');
}

function OfferRows({ offers, preferredCurrency }: { offers: Product[]; preferredCurrency?: string }) {
  const { formatMoney, formatNumber, regionLabel, t } = usePreferences();
  const bestOffers = bestYearbookOffers(offers, preferredCurrency);
  if (!bestOffers.length) {
    return (
      <View style={styles.noOffers}>
        <Ionicons name="pricetag-outline" size={14} color={colors.faint} />
        <Text style={styles.noOffersText}>{t('yearbook.noLinked')}</Text>
      </View>
    );
  }
  return (
    <View style={styles.offers}>
      <View style={styles.offerHeader}>
        <Text style={styles.offerHeaderText}>{t('yearbook.bestDeals')}</Text>
        <Text style={styles.offerHeaderMeta}>{t('yearbook.verifiedListings', { count: formatNumber(offers.length) })}</Text>
      </View>
      {bestOffers.slice(0, 3).map((offer) => {
        const freshness = freshnessLabel(offer.last_updated);
        const price = formatMoney(offer.sale_price, offer.currency, offer.symbol);
        return (
          <Pressable
            key={`${offer.currency}:${offer.sku_id}`}
            style={({ pressed }) => [styles.offerRow, pressed && styles.offerRowPressed]}
            onPress={(event) => openDeal(offer, event)}
            accessibilityRole="button"
            accessibilityLabel={t('yearbook.offerA11y', { platform: platformLabel(offer), price })}
          >
            <View style={styles.offerSource}>
              <Text style={styles.offerPlatform} numberOfLines={1}>{platformLabel(offer)}</Text>
              <Text style={styles.offerMeta} numberOfLines={1}>
                {offer.currency} · {regionLabel(offer.region)}{freshness ? ` · ${t('yearbook.updated', { when: freshness })}` : ''}
              </Text>
            </View>
            <View style={styles.offerPriceBlock}>
              <View style={styles.offerPrices}>
                <Text style={styles.offerPrice}>{price}</Text>
                <Text style={styles.offerOriginal}>{formatMoney(offer.original_price, offer.currency, offer.symbol)}</Text>
              </View>
              <View style={styles.discountBadge}>
                <Text style={styles.discountText}>-{Math.round(offer.discount_pct)}%</Text>
              </View>
              <Ionicons name="chevron-forward" size={15} color={colors.faint} />
            </View>
          </Pressable>
        );
      })}
      {bestOffers.length > 3 ? (
        <Text style={styles.moreOffers}>{t('yearbook.moreCurrencies', { count: formatNumber(bestOffers.length - 3) })}</Text>
      ) : null}
    </View>
  );
}

function YearbookCard({ product, offers }: { product: CatalogProduct; offers: Product[] }) {
  const { formatNumber, genderLabel, locale, t } = usePreferences();
  const colorPreview = product.color_names.slice(0, 3).join(' · ');
  const categoryPreview = product.categories.slice(0, 4).map(categoryLabel).join(' · ');
  const firstSeen = new Date(product.first_seen_at).toLocaleDateString(locale, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
  const gender = product.gender === 'kids' ? t('yearbook.kids') : genderLabel(product.gender);
  return (
    <Pressable
      style={styles.card}
      onPress={() => void Linking.openURL(product.source_url)}
      accessibilityRole="link"
      accessibilityLabel={t('yearbook.officialA11y', { brand: product.brand, name: product.name })}
    >
      <View style={styles.cardTop}>
        <View style={styles.badges}>
          <View style={styles.brandBadge}><Text style={styles.brandText}>{product.brand}</Text></View>
          <View style={styles.yearBadge}><Text style={styles.yearText}>{yearbookYear(product)}</Text></View>
        </View>
        <View style={styles.listPriceBlock}>
          <Text style={styles.listPriceLabel}>{t('yearbook.officialList')}</Text>
          <Text style={styles.price}>{formatCatalogPrice(product)}</Text>
        </View>
      </View>
      <Text style={styles.productName}>{product.name}</Text>
      <Text style={styles.sku}>{product.official_product_id} · {gender.toUpperCase()} · {product.country.toUpperCase()}</Text>
      {categoryPreview ? <Text style={styles.metadata}>{categoryPreview}</Text> : null}
      {colorPreview ? (
        <Text style={styles.metadata} numberOfLines={2}>
          {t('yearbook.colours', { count: formatNumber(product.color_names.length), preview: colorPreview })}{product.color_names.length > 3 ? ' …' : ''}
        </Text>
      ) : null}
      <OfferRows offers={offers} preferredCurrency={product.currency} />
      <View style={styles.cardFooter}>
        <Text style={styles.observed}>{t('yearbook.firstArchived', { date: firstSeen })}</Text>
        <View style={styles.officialLink}>
          <Text style={styles.officialText}>{t('yearbook.officialPage')}</Text>
          <Ionicons name="open-outline" size={14} color={colors.accent} />
        </View>
      </View>
    </Pressable>
  );
}

function ArchiveCard({ product }: { product: YearbookArchiveStyle }) {
  const { formatNumber, genderLabel, t } = usePreferences();
  const categoryPreview = product.categories.slice(0, 4).map(categoryLabel).join(' · ');
  const colorPreview = product.colors.slice(0, 3).join(' · ');
  const gender = product.gender === 'kids' ? t('yearbook.kids') : genderLabel(product.gender);
  return (
    <View style={[styles.card, styles.archiveCard]}>
      <View style={styles.cardTop}>
        <View style={styles.badges}>
          <View style={styles.brandBadge}><Text style={styles.brandText}>{brandLabel(product.brand_key)}</Text></View>
          <View style={styles.archiveBadge}><Text style={styles.archiveBadgeText}>{t('yearbook.archiveBadge')}</Text></View>
        </View>
        <Text style={styles.archiveOfferCount}>{t('yearbook.listings', { count: formatNumber(product.offers.length) })}</Text>
      </View>
      <Text style={styles.productName}>{product.name}</Text>
      <Text style={styles.sku}>
        {product.official_product_id || t('yearbook.styleIdUnavailable')} · {gender.toUpperCase()}
      </Text>
      {categoryPreview ? <Text style={styles.metadata}>{categoryPreview}</Text> : null}
      {colorPreview ? (
        <Text style={styles.metadata} numberOfLines={2}>
          {t('yearbook.colours', { count: formatNumber(product.colors.length), preview: colorPreview })}{product.colors.length > 3 ? ' …' : ''}
        </Text>
      ) : null}
      <OfferRows offers={product.offers} />
      <Text style={styles.archiveNote}>{t('yearbook.archiveNote')}</Text>
    </View>
  );
}

const numeric = {
  fontFamily: typography.mono,
  fontVariant: typography.tabular,
};

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 20, paddingBottom: 36, gap: 12 },
  header: { gap: 10, marginBottom: 4 },
  eyebrow: { color: colors.accent, fontSize: 11, fontWeight: '900', letterSpacing: 1.1 },
  title: { color: colors.ink, fontSize: 34, lineHeight: 40, fontWeight: '900' },
  subtitle: { color: colors.muted, fontSize: 13, fontWeight: '700' },
  searchWrap: {
    minHeight: 48,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    borderRadius: radii.md,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    paddingHorizontal: 14,
  },
  search: { flex: 1, color: colors.ink, fontSize: 15, fontWeight: '700' },
  filters: { gap: 8, paddingRight: 18 },
  chip: {
    borderRadius: 999,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  chipActive: { borderColor: colors.ink, backgroundColor: colors.ink },
  chipText: { color: colors.muted, fontSize: 12, fontWeight: '800' },
  chipTextActive: { color: colors.surface },
  resultCount: { color: colors.faint, fontSize: 12, fontWeight: '800', marginTop: 2 },
  linkStatus: { color: colors.muted, fontSize: 11, lineHeight: 16, fontWeight: '700' },
  card: {
    gap: 7,
    borderRadius: radii.lg,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    padding: 16,
  },
  cardTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  badges: { flex: 1, flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap', gap: 6 },
  brandBadge: { borderRadius: radii.sm, backgroundColor: colors.ink, paddingHorizontal: 9, paddingVertical: 5 },
  brandText: { color: colors.surface, fontSize: 11, fontWeight: '900' },
  yearBadge: { borderRadius: radii.sm, backgroundColor: colors.accentSoft, paddingHorizontal: 9, paddingVertical: 5 },
  yearText: { ...numeric, color: colors.accent, fontSize: 12, fontWeight: '900' },
  archiveBadge: { borderRadius: radii.sm, backgroundColor: colors.dangerSoft, paddingHorizontal: 9, paddingVertical: 5 },
  archiveBadgeText: { color: colors.danger, fontSize: 10, fontWeight: '900' },
  archiveCard: { borderColor: '#d7c7b2' },
  archiveOfferCount: { ...numeric, color: colors.faint, fontSize: 11, fontWeight: '800' },
  listPriceBlock: { alignItems: 'flex-end', gap: 1 },
  listPriceLabel: { color: colors.faint, fontSize: 8, fontWeight: '900', letterSpacing: 0.5 },
  price: { ...numeric, color: colors.ink, fontSize: 16, fontWeight: '900' },
  productName: { color: colors.ink, fontSize: 19, lineHeight: 24, fontWeight: '900' },
  sku: { ...numeric, color: colors.faint, fontSize: 11, fontWeight: '800', letterSpacing: 0.2 },
  metadata: { color: colors.muted, fontSize: 13, lineHeight: 18, fontWeight: '700' },
  noOffers: {
    minHeight: 38,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    borderRadius: radii.sm,
    backgroundColor: colors.surfaceAlt,
    paddingHorizontal: 10,
    marginTop: 3,
  },
  noOffersText: { color: colors.faint, fontSize: 11, fontWeight: '800' },
  offers: {
    borderRadius: radii.md,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    overflow: 'hidden',
    marginTop: 3,
  },
  offerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
    backgroundColor: colors.accentSoft,
    paddingHorizontal: 10,
    paddingVertical: 7,
  },
  offerHeaderText: { flex: 1, color: colors.accent, fontSize: 9, fontWeight: '900', letterSpacing: 0.5 },
  offerHeaderMeta: { color: colors.accent, fontSize: 9, fontWeight: '800' },
  offerRow: {
    minHeight: 54,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
    backgroundColor: colors.surface,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  offerRowPressed: { backgroundColor: colors.surfaceAlt },
  offerSource: { flex: 1, minWidth: 0, gap: 2 },
  offerPlatform: { color: colors.ink, fontSize: 12, fontWeight: '900', textTransform: 'capitalize' },
  offerMeta: { color: colors.faint, fontSize: 9, fontWeight: '700' },
  offerPriceBlock: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  offerPrices: { alignItems: 'flex-end', gap: 1 },
  offerPrice: { ...numeric, color: colors.ink, fontSize: 14, fontWeight: '900' },
  offerOriginal: { ...numeric, color: colors.faint, fontSize: 9, fontWeight: '700', textDecorationLine: 'line-through' },
  discountBadge: { borderRadius: radii.sm, backgroundColor: colors.dangerSoft, paddingHorizontal: 6, paddingVertical: 4 },
  discountText: { ...numeric, color: colors.danger, fontSize: 10, fontWeight: '900' },
  moreOffers: { color: colors.faint, fontSize: 9, fontWeight: '800', paddingHorizontal: 10, paddingVertical: 7 },
  archiveNote: { color: colors.faint, fontSize: 10, lineHeight: 14, fontWeight: '700' },
  cardFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
    paddingTop: 10,
    marginTop: 3,
  },
  observed: { flex: 1, color: colors.faint, fontSize: 11, fontWeight: '700' },
  officialLink: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  officialText: { color: colors.accent, fontSize: 12, fontWeight: '900' },
});
