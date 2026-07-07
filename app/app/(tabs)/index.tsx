import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { Alert, FlatList, Pressable, RefreshControl, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { DealCard } from '../../components/DealCard';
import { FilterChips } from '../../components/FilterChips';
import { ScreenState } from '../../components/ScreenState';
import { useProducts } from '../../contexts/ProductsContext';
import { useWatchlist } from '../../contexts/WatchlistContext';
import { cleanName, productCategory } from '../../lib/catalog';
import { colors } from '../../lib/theme';
import type { Product } from '../../lib/types';

type FilterState = {
  platform: string;
  region: string;
  category: string;
  gender: string;
  series: string;
  sort: string;
};

export default function DealsScreen() {
  const { products, loading, refreshing, error, loadedCount, reload, signals, ensureSignalsFor } = useProducts();
  const watchlist = useWatchlist();
  const [query, setQuery] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [filters, setFilters] = useState<FilterState>({
    platform: 'all',
    region: 'us',
    category: 'all',
    gender: 'all',
    series: 'all',
    sort: 'discount_desc',
  });
  const [visibleLimit, setVisibleLimit] = useState(500);
  const [signalWindow, setSignalWindow] = useState(120);

  const categories = useMemo(() => [...new Set(products.map(productCategory))], [products]);
  const platforms = useMemo(() => [...new Set(products.map((product) => product._platform))], [products]);
  const series = useMemo(() => [...new Set(products.map((product) => product._series))], [products]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const rows = products.filter((product) => {
      if (filters.region !== 'all' && product.region !== filters.region) return false;
      if (filters.platform !== 'all' && product._platform !== filters.platform) return false;
      if (filters.gender !== 'all') {
        const gender = product.gender === 'unknown' ? 'unisex' : product.gender || 'unisex';
        if (gender !== filters.gender) return false;
      }
      if (filters.category !== 'all' && productCategory(product) !== filters.category) return false;
      if (filters.series !== 'all' && product._series !== filters.series) return false;
      if (q) {
        const haystack = `${product.full_name || ''} ${product.model || ''} ${product.description || ''} ${product.category || ''}`.toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      return true;
    });

    switch (filters.sort) {
      case 'price_asc':
        rows.sort((a, b) => a.sale_price - b.sale_price);
        break;
      case 'price_desc':
        rows.sort((a, b) => b.sale_price - a.sale_price);
        break;
      case 'recent':
        rows.sort((a, b) => (b.last_updated || '').localeCompare(a.last_updated || ''));
        break;
      case 'discount_desc':
      default:
        rows.sort((a, b) => (b.discount_pct || 0) - (a.discount_pct || 0));
    }
    return rows;
  }, [filters, products, query]);

  useEffect(() => {
    ensureSignalsFor(filtered.slice(0, signalWindow));
  }, [ensureSignalsFor, filtered, signalWindow]);

  const data = filtered.slice(0, visibleLimit);
  const stableHeroPool = filtered.filter(hasStableHeroImage);
  const imageHeroPool = filtered.filter((product) => product.image_url || product.images.length);
  const heroRows = stableHeroPool.length ? stableHeroPool : imageHeroPool.length ? imageHeroPool : filtered;
  const hero =
    heroRows.find((product) => signals[product.sku_id]?.kind === 'all_time_low') ||
    heroRows.find((product) => signals[product.sku_id]?.isLow) ||
    heroRows[0];
  const heroSignal = hero ? signals[hero.sku_id] : undefined;

  if (loading && !products.length) {
    return <ScreenState title="Loading deals" body="Checking current prices and markdowns." loading />;
  }

  if (error && !products.length) {
    return <ScreenState title="Could not load deals" body={error} />;
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <FlatList
        data={data}
        keyExtractor={(item) => item.sku_id}
        numColumns={2}
        columnWrapperStyle={styles.columns}
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={reload} tintColor={colors.accent} />}
        ListHeaderComponent={
          <Header
            loadedCount={loadedCount}
            resultCount={filtered.length}
            query={query}
            searchOpen={searchOpen}
            onToggleSearch={() => setSearchOpen((next) => !next)}
            onQueryChange={setQuery}
            filters={filters}
            categories={categories}
            platforms={platforms}
            series={series}
            onFilterChange={(next) => {
              setVisibleLimit(500);
              setSignalWindow(120);
              setFilters((current) => ({ ...current, ...next }));
            }}
            hero={hero}
            heroSignal={heroSignal}
            onHeroPress={() => hero && openProduct(hero)}
            onHeroSave={() => hero && toggleSave(watchlist, hero)}
            heroSaved={hero ? watchlist.isSaved(hero.sku_id) : false}
          />
        }
        renderItem={({ item }) => (
          <View style={styles.item}>
            <DealCard
              product={item}
              signal={signals[item.sku_id]}
              saved={watchlist.isSaved(item.sku_id)}
              onPress={() => openProduct(item)}
              onToggleSave={() => toggleSave(watchlist, item)}
            />
          </View>
        )}
        ListEmptyComponent={<ScreenState title="No matching deals" body="Adjust filters or search terms." />}
        onEndReachedThreshold={0.4}
        onEndReached={() => {
          setVisibleLimit((current) => Math.min(current + 300, filtered.length));
          setSignalWindow((current) => Math.min(current + 160, filtered.length));
        }}
      />
    </SafeAreaView>
  );
}

function openProduct(product: Product) {
  router.push({ pathname: '/product/[skuId]', params: { skuId: product.sku_id } });
}

function hasStableHeroImage(product: Product) {
  const imageUrl = product.image_url || product.images[0] || '';
  return Boolean(imageUrl) && !/\/\/www\.rei\.com\/media\//i.test(imageUrl);
}

function Header({
  loadedCount,
  resultCount,
  query,
  searchOpen,
  onToggleSearch,
  onQueryChange,
  filters,
  categories,
  platforms,
  series,
  onFilterChange,
  hero,
  heroSignal,
  onHeroPress,
  onHeroSave,
  heroSaved,
}: {
  loadedCount: number;
  resultCount: number;
  query: string;
  searchOpen: boolean;
  onToggleSearch: () => void;
  onQueryChange: (value: string) => void;
  filters: FilterState;
  categories: string[];
  platforms: string[];
  series: string[];
  onFilterChange: (next: Partial<FilterState>) => void;
  hero?: Product;
  heroSignal?: ReturnType<typeof useProducts>['signals'][string];
  onHeroPress: () => void;
  onHeroSave: () => void;
  heroSaved: boolean;
}) {
  return (
    <View style={styles.header}>
      <View style={styles.topBar}>
        <View>
          <Text style={styles.title}>Deals</Text>
          <Text style={styles.subtitle}>{loadedCount.toLocaleString('en-US')} loaded · {resultCount.toLocaleString('en-US')} shown</Text>
        </View>
        <Pressable accessibilityRole="button" accessibilityLabel={searchOpen ? 'Close search' : 'Open search'} style={styles.searchButton} onPress={onToggleSearch}>
          <Ionicons name={searchOpen ? 'close' : 'search'} size={22} color={colors.ink} />
        </Pressable>
      </View>
      {searchOpen ? (
        <View style={styles.searchWrap}>
          <Ionicons name="search" size={18} color={colors.faint} />
          <TextInput value={query} onChangeText={onQueryChange} autoCapitalize="none" placeholder="Search beta, atom, jacket..." style={styles.searchInput} />
        </View>
      ) : null}
      <FilterChips value={filters} platforms={platforms} categories={categories} series={series} onChange={onFilterChange} />
      {hero ? (
        <View style={styles.heroSection}>
          <Text style={styles.heroLabel}>{heroSignal?.kind === 'all_time_low' ? 'New all-time low' : heroSignal?.kind === 'ninety_day_low' ? '90-day low' : 'Best signal now'}</Text>
          <DealCard product={hero} signal={heroSignal} hero saved={heroSaved} onPress={onHeroPress} onToggleSave={onHeroSave} />
          <Text style={styles.heroHint} numberOfLines={1}>{cleanName(hero.full_name || hero.model)}</Text>
        </View>
      ) : null}
      <Text style={styles.sectionTitle}>Discount stream</Text>
    </View>
  );
}

async function toggleSave(watchlist: ReturnType<typeof useWatchlist>, product: Product) {
  const saved = await watchlist.toggle(product);
  if (!saved) {
    Alert.alert('Watchlist limit reached', `Free watchlists hold ${watchlist.freeLimit} items. Upgrade to Pro for unlimited saves.`);
  }
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  content: {
    paddingBottom: 26,
  },
  header: {
    gap: 14,
    paddingTop: 4,
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
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
  searchButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 22,
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
  },
  searchWrap: {
    minHeight: 48,
    marginHorizontal: 20,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 12,
  },
  searchInput: {
    flex: 1,
    color: colors.ink,
    fontSize: 16,
  },
  heroSection: {
    gap: 8,
  },
  heroLabel: {
    color: colors.success,
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    paddingHorizontal: 20,
  },
  heroHint: {
    color: colors.faint,
    paddingHorizontal: 20,
    fontSize: 12,
    fontWeight: '700',
  },
  sectionTitle: {
    color: colors.ink,
    fontSize: 17,
    fontWeight: '900',
    paddingHorizontal: 20,
    marginTop: 6,
  },
  columns: {
    gap: 12,
    paddingHorizontal: 14,
  },
  item: {
    flex: 1,
    marginBottom: 12,
  },
});
