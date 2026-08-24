import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { Alert, FlatList, Modal, Platform, Pressable, RefreshControl, ScrollView, StyleSheet, Text, TextInput, useWindowDimensions, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { BrandLogo } from '../../components/BrandLogo';
import { DealCard } from '../../components/DealCard';
import { FilterChips } from '../../components/FilterChips';
import { ScreenState } from '../../components/ScreenState';
import { useProducts } from '../../contexts/ProductsContext';
import { usePreferences } from '../../contexts/PreferencesContext';
import { useRegion } from '../../contexts/RegionContext';
import { useWatchlist } from '../../contexts/WatchlistContext';
import { productCategory, regionFlag } from '../../lib/catalog';
import { availableDealRegions, DEFAULT_DEAL_FILTERS, filterDeals, productsForRegion, type DealFilters } from '../../lib/deals';
import { INITIAL_SIGNAL_WINDOW } from '../../lib/productPreview';
import { colors, typography } from '../../lib/theme';
import type { Product } from '../../lib/types';

export default function DealsScreen() {
  const { products, loading, refreshing, error, loadedCount, reload, signals, ensureSignalsFor } = useProducts();
  const { regionLabel, t } = usePreferences();
  const { region, setRegion } = useRegion();
  const watchlist = useWatchlist();
  const [query, setQuery] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [filters, setFilters] = useState<DealFilters>({ ...DEFAULT_DEAL_FILTERS });
  const [visibleLimit, setVisibleLimit] = useState(500);
  const [signalWindow, setSignalWindow] = useState(INITIAL_SIGNAL_WINDOW);

  const regionProducts = useMemo(() => productsForRegion(products, region), [products, region]);
  const categories = useMemo(() => [...new Set(regionProducts.map(productCategory))], [regionProducts]);
  const platforms = useMemo(() => [...new Set(regionProducts.map((product) => product._platform))], [regionProducts]);
  const series = useMemo(() => [...new Set(regionProducts.map((product) => product._series))], [regionProducts]);
  const regionOptions = useMemo(() => availableDealRegions(products), [products]);
  const filtered = useMemo(() => filterDeals(products, region, query, filters), [filters, products, query, region]);
  const listRevision = `${region}\u001f${searchOpen ? 'open' : 'closed'}\u001f${query}\u001f${filters.platform}\u001f${filters.category}\u001f${filters.gender}\u001f${filters.series}\u001f${filters.sort}`;

  useEffect(() => {
    if (!loading && products.length && region !== 'all' && !regionOptions.includes(region)) {
      void setRegion('all');
    }
  }, [loading, products.length, region, regionOptions, setRegion]);

  useEffect(() => {
    ensureSignalsFor(filtered.slice(0, signalWindow));
  }, [ensureSignalsFor, filtered, signalWindow]);

  const data = filtered.slice(0, visibleLimit);

  if (loading && !products.length) {
    return <ScreenState title={t('deals.loading')} body={t('deals.loadingBody')} loading />;
  }

  if (error && !products.length) {
    return <ScreenState title={t('deals.loadError')} body={error} />;
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <FlatList
        data={data}
        extraData={listRevision}
        keyExtractor={(item) => item.sku_id}
        numColumns={2}
        keyboardShouldPersistTaps="handled"
        columnWrapperStyle={styles.columns}
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={reload} tintColor={colors.pill} />}
        ListHeaderComponent={
          <Header
            loadedCount={loadedCount}
            resultCount={filtered.length}
            query={query}
            searchOpen={searchOpen}
            onToggleSearch={() => setSearchOpen((next) => !next)}
            onQueryChange={setQuery}
            region={region}
            regionOptions={regionOptions}
            onRegionChange={async (nextRegion) => {
              setQuery('');
              setSearchOpen(false);
              setVisibleLimit(500);
              setSignalWindow(INITIAL_SIGNAL_WINDOW);
              setFilters((current) => ({ ...DEFAULT_DEAL_FILTERS, sort: current.sort }));
              await setRegion(nextRegion);
            }}
            filters={filters}
            categories={categories}
            platforms={platforms}
            series={series}
            onFilterChange={(next) => {
              setVisibleLimit(500);
              setSignalWindow(INITIAL_SIGNAL_WINDOW);
              setFilters((current) => ({ ...current, ...next }));
            }}
          />
        }
        renderItem={({ item }) => (
          <View style={styles.item}>
            <DealCard
              product={item}
              signal={signals[item.sku_id]}
              saved={watchlist.isSaved(item.sku_id)}
              onPress={() => openProduct(item)}
              onToggleSave={() => toggleSave(watchlist, item, t)}
            />
          </View>
        )}
        ListEmptyComponent={
          loading ? (
            <ScreenState title={t('deals.loading')} body={t('deals.loadingBody')} loading />
          ) : (
            <ScreenState title={t('deals.noMatches')} body={t('deals.noMatchesBody', { region: regionLabel(region) })} />
          )
        }
        onEndReachedThreshold={0.4}
        onEndReached={() => {
          setVisibleLimit((current) => Math.min(current + 300, filtered.length));
          setSignalWindow((current) => Math.min(current + 40, filtered.length));
        }}
      />
    </SafeAreaView>
  );
}

function openProduct(product: Product) {
  router.push({ pathname: '/product/[skuId]', params: { skuId: product.sku_id } });
}

function Header({
  loadedCount,
  resultCount,
  query,
  searchOpen,
  onToggleSearch,
  onQueryChange,
  region,
  regionOptions,
  onRegionChange,
  filters,
  categories,
  platforms,
  series,
  onFilterChange,
}: {
  loadedCount: number;
  resultCount: number;
  query: string;
  searchOpen: boolean;
  onToggleSearch: () => void;
  onQueryChange: (value: string) => void;
  region: string;
  regionOptions: string[];
  onRegionChange: (region: string) => Promise<void>;
  filters: DealFilters;
  categories: string[];
  platforms: string[];
  series: string[];
  onFilterChange: (next: Partial<DealFilters>) => void;
}) {
  const { formatNumber, regionLabel, t } = usePreferences();
  const [regionOpen, setRegionOpen] = useState(false);
  const selectedRegionLabel = regionLabel(region);
  const regionShort = region === 'all' ? 'ALL' : region.toUpperCase();

  return (
    <View style={styles.header}>
      <View style={styles.topBar}>
        <View>
          <BrandLogo style={styles.brandLogo} />
          <Text style={styles.subtitle}>{t('deals.loadedShown', { loaded: formatNumber(loadedCount), shown: formatNumber(resultCount) })}</Text>
        </View>
        <View style={styles.titleActions}>
          <Pressable accessibilityRole="button" accessibilityLabel={`${t('deals.region')}: ${selectedRegionLabel}`} style={styles.regionPill} onPress={() => setRegionOpen(true)}>
            <Text style={styles.regionFlag}>{regionFlag(region)}</Text>
            <Text style={styles.regionText}>{regionShort}</Text>
            <Ionicons name="chevron-down" size={13} color={colors.ink} />
          </Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel={searchOpen ? 'Close search' : 'Open search'} style={styles.searchButton} onPress={onToggleSearch}>
            <Ionicons name={searchOpen ? 'close' : 'search'} size={20} color={colors.ink} />
          </Pressable>
        </View>
      </View>
      {searchOpen ? (
        <View style={styles.searchWrap}>
          <Ionicons name="search" size={18} color={colors.faint} />
          <TextInput
            value={query}
            onChangeText={onQueryChange}
            autoCapitalize="none"
            autoComplete="off"
            autoCorrect={false}
            spellCheck={false}
            placeholder={t('deals.search')}
            style={styles.searchInput}
          />
        </View>
      ) : null}
      <View style={styles.controlsWrap}>
        <FilterChips value={filters} platforms={platforms} categories={categories} series={series} onChange={onFilterChange} />
      </View>
      <Text style={styles.sectionTitle}>{t('deals.biggestDrops')}</Text>
      <RegionSheet
        visible={regionOpen}
        value={region}
        options={regionOptions}
        onClose={() => setRegionOpen(false)}
        onSelect={(nextRegion) => {
          void onRegionChange(nextRegion);
          setRegionOpen(false);
        }}
      />
    </View>
  );
}

function RegionSheet({ visible, value, options, onClose, onSelect }: { visible: boolean; value: string; options: string[]; onClose: () => void; onSelect: (region: string) => void }) {
  const { regionLabel, t } = usePreferences();
  const { height: windowHeight } = useWindowDimensions();
  const optionListMaxHeight = Math.max(48, windowHeight * 0.9 - 98);
  return (
    <Modal visible={visible} animationType={Platform.OS === 'web' ? 'fade' : 'slide'} transparent onRequestClose={onClose}>
      <View style={styles.sheetBackdrop}>
        <View style={styles.regionSheet}>
          <View style={styles.sheetHead}>
            <Text style={styles.sheetTitle}>{t('deals.region')}</Text>
            <Pressable style={styles.closeButton} onPress={onClose}>
              <Ionicons name="close" size={20} color={colors.ink} />
            </Pressable>
          </View>
          <ScrollView style={[styles.regionOptions, { maxHeight: optionListMaxHeight }]} showsVerticalScrollIndicator={options.length > 8}>
            {options.map((region) => {
              const active = value === region;
              return (
                <Pressable key={region} style={styles.regionOption} onPress={() => onSelect(region)}>
                  <Text style={styles.regionOptionFlag}>{regionFlag(region)}</Text>
                  <Text style={[styles.regionOptionText, active && styles.regionOptionTextActive]}>{regionLabel(region)}</Text>
                  {active ? <Ionicons name="checkmark" size={18} color={colors.buy} /> : null}
                </Pressable>
              );
            })}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

async function toggleSave(watchlist: ReturnType<typeof useWatchlist>, product: Product, t: ReturnType<typeof usePreferences>['t']) {
  const saved = await watchlist.toggle(product);
  if (!saved) {
    Alert.alert(t('deals.watchLimitTitle'), t('deals.watchLimitBody', { count: watchlist.freeLimit }));
  }
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  content: {
    paddingBottom: 26,
    paddingHorizontal: 15,
  },
  header: {
    gap: 13,
    paddingTop: 4,
    paddingBottom: 2,
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 14,
  },
  brandLogo: {
    width: 156,
    height: 44,
  },
  subtitle: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: '700',
  },
  titleActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  regionPill: {
    minHeight: 34,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    borderRadius: 18,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.borderStrong,
    paddingHorizontal: 10,
  },
  regionFlag: {
    fontSize: 14,
  },
  regionText: {
    color: colors.ink,
    fontSize: 12.5,
    fontWeight: '800',
  },
  searchButton: {
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 18,
    backgroundColor: colors.card,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
  },
  searchWrap: {
    minHeight: 44,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.borderStrong,
    backgroundColor: colors.card,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 12,
  },
  searchInput: {
    flex: 1,
    color: colors.ink,
    fontSize: 14,
  },
  controlsWrap: {
    marginBottom: 1,
  },
  sectionTitle: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 0.8,
    marginTop: 2,
    textTransform: 'uppercase',
  },
  columns: {
    gap: 12,
    justifyContent: 'space-between',
  },
  item: {
    flex: 1,
    maxWidth: '48.4%',
  },
  sheetBackdrop: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(8,9,10,.38)',
  },
  regionSheet: {
    maxHeight: '90%',
    overflow: 'hidden',
    gap: 4,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    backgroundColor: colors.card,
    padding: 18,
    paddingBottom: 34,
  },
  regionOptions: {
    flexShrink: 1,
  },
  sheetHead: {
    flexShrink: 0,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  sheetTitle: {
    color: colors.ink,
    fontSize: 19,
    fontWeight: '900',
  },
  closeButton: {
    width: 34,
    height: 34,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 17,
    backgroundColor: colors.screen,
  },
  regionOption: {
    minHeight: 48,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  regionOptionFlag: {
    width: 26,
    color: colors.ink,
    fontFamily: typography.mono,
    fontVariant: typography.tabular,
    fontSize: 15,
  },
  regionOptionText: {
    flex: 1,
    color: colors.ink,
    fontSize: 15,
    fontWeight: '700',
  },
  regionOptionTextActive: {
    color: colors.buy,
  },
});
