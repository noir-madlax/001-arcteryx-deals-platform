import { Ionicons } from '@expo/vector-icons';
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
import { SafeAreaView } from 'react-native-safe-area-context';

import { ScreenState } from '../../components/ScreenState';
import { fetchYearbookProducts } from '../../lib/supabase';
import { colors, radii } from '../../lib/theme';
import type { CatalogBrandKey, CatalogGender, CatalogProduct } from '../../lib/types';
import {
  brandLabel,
  categoryLabel,
  filterYearbookProducts,
  formatCatalogPrice,
  yearbookBrands,
  yearbookCategories,
  yearbookYear,
  yearbookYears,
} from '../../lib/yearbook';

type BrandFilter = 'all' | CatalogBrandKey;
type GenderFilter = 'all' | CatalogGender;

export default function YearbookScreen() {
  const [products, setProducts] = useState<CatalogProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [unavailable, setUnavailable] = useState(false);
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
        setProducts(rows);
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

  const brands = useMemo(() => yearbookBrands(products), [products]);
  const years = useMemo(() => yearbookYears(products), [products]);
  const categories = useMemo(() => yearbookCategories(products), [products]);
  const visible = useMemo(
    () => filterYearbookProducts(products, { query, brand, gender, category, year }),
    [products, query, brand, gender, category, year],
  );

  if (loading) {
    return <ScreenState title="Opening the Yearbook" body="Loading the official full-price catalogs." loading />;
  }
  if (unavailable) {
    return (
      <ScreenState
        title="Yearbook data isn't published yet"
        body="The catalog archive is separate from Deals, so deal browsing remains available in the Deals tab."
      />
    );
  }
  if (!products.length) {
    return <ScreenState title="The Yearbook is being built" body="Official catalog observations will appear after the first archive run." />;
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <FlatList
        data={visible}
        keyExtractor={(item) => item.catalog_product_id}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
        ListHeaderComponent={
          <View style={styles.header}>
            <Text style={styles.eyebrow}>THREE BRANDS · OFFICIAL FULL-PRICE CATALOGS</Text>
            <Text style={styles.title}>Yearbook</Text>
            <Text style={styles.subtitle}>{products.length} styles archived · factual metadata only</Text>
            <View style={styles.searchWrap}>
              <Ionicons name="search-outline" size={18} color={colors.faint} />
              <TextInput
                value={query}
                onChangeText={setQuery}
                placeholder="Search brand, model, style, colour"
                placeholderTextColor={colors.faint}
                autoCapitalize="none"
                autoCorrect={false}
                style={styles.search}
              />
              {query ? (
                <Pressable onPress={() => setQuery('')} hitSlop={10} accessibilityLabel="Clear search">
                  <Ionicons name="close-circle" size={18} color={colors.faint} />
                </Pressable>
              ) : null}
            </View>
            <FilterRail>
              <FilterChip active={brand === 'all'} label="All brands" onPress={() => setBrand('all')} />
              {brands.map((value) => (
                <FilterChip key={value} active={brand === value} label={brandLabel(value)} onPress={() => setBrand(value)} />
              ))}
            </FilterRail>
            <FilterRail>
              {(['all', 'men', 'women', 'kids', 'unisex'] as GenderFilter[]).map((value) => (
                <FilterChip key={value} active={gender === value} label={genderLabel(value)} onPress={() => setGender(value)} />
              ))}
            </FilterRail>
            <FilterRail>
              <FilterChip active={year === 'all'} label="All years" onPress={() => setYear('all')} />
              {years.map((value) => <FilterChip key={value} active={year === value} label={String(value)} onPress={() => setYear(value)} />)}
            </FilterRail>
            <FilterRail>
              <FilterChip active={category === 'all'} label="All categories" onPress={() => setCategory('all')} />
              {categories.map((value) => (
                <FilterChip key={value} active={category === value} label={categoryLabel(value)} onPress={() => setCategory(value)} />
              ))}
            </FilterRail>
            <Text style={styles.resultCount}>{visible.length} matching styles</Text>
          </View>
        }
        ListEmptyComponent={<ScreenState title="No matching styles" body="Try clearing one of the Yearbook filters." />}
        renderItem={({ item }) => <YearbookCard product={item} />}
      />
    </SafeAreaView>
  );
}

function genderLabel(value: GenderFilter) {
  if (value === 'all') return 'All';
  if (value === 'kids') return 'Kids';
  if (value === 'unisex') return 'Unisex';
  return value === 'men' ? 'Men' : 'Women';
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

function YearbookCard({ product }: { product: CatalogProduct }) {
  const colorPreview = product.color_names.slice(0, 3).join(' · ');
  const categoryPreview = product.categories.slice(0, 4).map(categoryLabel).join(' · ');
  const firstSeen = new Date(product.first_seen_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
  return (
    <Pressable
      style={styles.card}
      onPress={() => void Linking.openURL(product.source_url)}
      accessibilityRole="link"
      accessibilityLabel={`${product.brand} ${product.name}, official product page`}
    >
      <View style={styles.cardTop}>
        <View style={styles.badges}>
          <View style={styles.brandBadge}><Text style={styles.brandText}>{product.brand}</Text></View>
          <View style={styles.yearBadge}><Text style={styles.yearText}>{yearbookYear(product)}</Text></View>
        </View>
        <Text style={styles.price}>{formatCatalogPrice(product)}</Text>
      </View>
      <Text style={styles.productName}>{product.name}</Text>
      <Text style={styles.sku}>{product.official_product_id} · {product.gender.toUpperCase()} · {product.country.toUpperCase()}</Text>
      {categoryPreview ? <Text style={styles.metadata}>{categoryPreview}</Text> : null}
      {colorPreview ? (
        <Text style={styles.metadata} numberOfLines={2}>
          {product.color_names.length} colours · {colorPreview}{product.color_names.length > 3 ? ' …' : ''}
        </Text>
      ) : null}
      <View style={styles.cardFooter}>
        <Text style={styles.observed}>First archived {firstSeen}</Text>
        <View style={styles.officialLink}>
          <Text style={styles.officialText}>Official page</Text>
          <Ionicons name="open-outline" size={14} color={colors.accent} />
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 20, paddingBottom: 36, gap: 12 },
  header: { gap: 10, marginBottom: 4 },
  eyebrow: { color: colors.accent, fontSize: 11, fontWeight: '900', letterSpacing: 1.2 },
  title: { color: colors.ink, fontSize: 38, lineHeight: 42, fontWeight: '900' },
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
  card: {
    gap: 7,
    borderRadius: radii.lg,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    padding: 16,
  },
  cardTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  badges: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  brandBadge: { borderRadius: radii.sm, backgroundColor: colors.ink, paddingHorizontal: 9, paddingVertical: 5 },
  brandText: { color: colors.surface, fontSize: 11, fontWeight: '900' },
  yearBadge: { borderRadius: radii.sm, backgroundColor: colors.accentSoft, paddingHorizontal: 9, paddingVertical: 5 },
  yearText: { color: colors.accent, fontSize: 12, fontWeight: '900' },
  price: { color: colors.ink, fontSize: 16, fontWeight: '900' },
  productName: { color: colors.ink, fontSize: 19, lineHeight: 24, fontWeight: '900' },
  sku: { color: colors.faint, fontSize: 11, fontWeight: '800', letterSpacing: 0.4 },
  metadata: { color: colors.muted, fontSize: 13, lineHeight: 18, fontWeight: '700' },
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
