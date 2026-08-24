import { Ionicons } from '@expo/vector-icons';
import { useMemo, useState } from 'react';
import { Modal, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { usePreferences } from '../contexts/PreferencesContext';
import { CATEGORY_ORDER, PLATFORM, SORT_OPTIONS, GENDER_OPTIONS } from '../lib/catalog';
import { colors, radii, typography } from '../lib/theme';

type FilterState = {
  platform: string;
  category: string;
  gender: string;
  series: string;
  sort: string;
};

type Props = {
  value: FilterState;
  platforms: string[];
  categories: string[];
  series: string[];
  onChange: (next: Partial<FilterState>) => void;
};

export function FilterChips({ value, platforms, categories, series: _series, onChange }: Props) {
  const { categoryLabel, genderLabel, t } = usePreferences();
  const [sortOpen, setSortOpen] = useState(false);
  const [filterOpen, setFilterOpen] = useState(false);
  const normalizedPlatforms = useMemo(
    () => ['all', ...platforms.slice().sort((a, b) => (PLATFORM[a]?.label || a).localeCompare(PLATFORM[b]?.label || b))],
    [platforms],
  );
  const normalizedCategories = useMemo(
    () => [
      'all',
      ...categories
        .slice()
        .sort((a, b) => {
          const ai = CATEGORY_ORDER.indexOf(a);
          const bi = CATEGORY_ORDER.indexOf(b);
          if (ai !== -1 && bi !== -1) return ai - bi;
          if (ai !== -1) return -1;
          if (bi !== -1) return 1;
          return a.localeCompare(b);
        })
        .slice(0, 14),
    ],
    [categories],
  );
  const activeFilters = [
    value.platform !== 'all'
      ? {
          key: 'platform',
          label: PLATFORM[value.platform]?.label || value.platform,
          clear: () => onChange({ platform: 'all' }),
        }
      : null,
    value.category !== 'all' ? { key: 'category', label: categoryLabel(value.category), clear: () => onChange({ category: 'all' }) } : null,
    value.gender !== 'all'
      ? {
          key: 'gender',
          label: genderLabel(value.gender),
          clear: () => onChange({ gender: 'all' }),
        }
      : null,
  ].filter(Boolean) as Array<{ key: string; label: string; clear: () => void }>;
  const hasActiveFilters = activeFilters.length > 0;

  return (
    <View style={styles.wrap}>
      <View style={styles.controlRow}>
        <Pressable accessibilityRole="button" accessibilityLabel={`${t('filters.sort')}: ${t(`sort.${value.sort}`)}`} style={styles.sortButton} onPress={() => setSortOpen(true)}>
          <Text style={styles.sortPrefix}>{t('filters.sort')}</Text>
          <Text style={styles.sortText}>{t(`sort.${value.sort}`)}</Text>
          <Ionicons name="chevron-down" size={14} color={colors.ink} />
        </Pressable>
        <Pressable accessibilityRole="button" accessibilityLabel={t('filters.filters')} style={styles.filterButton} onPress={() => setFilterOpen(true)}>
          <Ionicons name="filter" size={18} color={colors.ink} />
          {hasActiveFilters ? <View style={styles.filterDot} /> : null}
        </Pressable>
      </View>

      {hasActiveFilters ? (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.activeRow}>
          {activeFilters.map((filter) => (
            <Pressable key={filter.key} accessibilityRole="button" accessibilityLabel={`Clear ${filter.label}`} style={styles.activeChip} onPress={filter.clear}>
              <Text style={styles.activeChipText} numberOfLines={1}>
                {filter.label}
              </Text>
              <Ionicons name="close" size={12} color={colors.disc} />
            </Pressable>
          ))}
        </ScrollView>
      ) : null}

      <SelectionSheet
        visible={sortOpen}
        title={t('filters.sort')}
        onClose={() => setSortOpen(false)}
        options={SORT_OPTIONS}
        value={value.sort}
        getLabel={(option) => t(`sort.${option}`)}
        onSelect={(sort) => {
          onChange({ sort });
          setSortOpen(false);
        }}
      />

      <Modal visible={filterOpen} animationType={Platform.OS === 'web' ? 'fade' : 'slide'} transparent onRequestClose={() => setFilterOpen(false)}>
        <View style={styles.backdrop}>
          <View style={styles.sheet}>
            <View style={styles.sheetHead}>
              <Text style={styles.sheetTitle}>{t('filters.filters')}</Text>
              <Pressable style={styles.closeButton} onPress={() => setFilterOpen(false)}>
                <Ionicons name="close" size={20} color={colors.ink} />
              </Pressable>
            </View>
            <ScrollView
              style={styles.filterScroll}
              contentContainerStyle={styles.filterContent}
              showsVerticalScrollIndicator
            >
              <FilterSection
                title={t('filters.brand')}
                options={normalizedPlatforms}
                value={value.platform}
                getLabel={(option) => (option === 'all' ? t('filters.allBrands') : PLATFORM[option]?.label || option)}
                onSelect={(platform) => onChange({ platform })}
              />
              <FilterSection
                title={t('filters.category')}
                options={normalizedCategories}
                value={value.category}
                getLabel={(option) => (option === 'all' ? t('filters.allCategories') : categoryLabel(option))}
                onSelect={(category) => onChange({ category })}
              />
              <FilterSection
                title={t('filters.gender')}
                options={GENDER_OPTIONS}
                value={value.gender}
                getLabel={(option) => (option === 'all' ? t('filters.allGenders') : genderLabel(option))}
                onSelect={(gender) => onChange({ gender })}
              />
            </ScrollView>
            <View style={styles.sheetActions}>
              <Pressable style={styles.resetButton} onPress={() => onChange({ platform: 'all', category: 'all', gender: 'all', series: 'all' })}>
                <Text style={styles.resetText}>{t('common.reset')}</Text>
              </Pressable>
              <Pressable style={styles.doneButton} onPress={() => setFilterOpen(false)}>
                <Text style={styles.doneText}>{t('common.done')}</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

function FilterSection({
  title,
  options,
  value,
  getLabel,
  onSelect,
}: {
  title: string;
  options: string[];
  value: string;
  getLabel: (option: string) => string;
  onSelect: (option: string) => void;
}) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <View style={styles.optionWrap}>
        {options.map((option) => {
          const active = value === option;
          return (
            <Pressable key={option} accessibilityRole="button" accessibilityLabel={`${title}: ${getLabel(option)}`} accessibilityState={{ selected: active }} style={[styles.option, active && styles.optionActive]} onPress={() => onSelect(option)}>
              <Text style={[styles.optionText, active && styles.optionTextActive]} numberOfLines={1}>
                {getLabel(option)}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

function SelectionSheet({
  visible,
  title,
  options,
  value,
  getLabel,
  onSelect,
  onClose,
}: {
  visible: boolean;
  title: string;
  options: string[];
  value: string;
  getLabel: (option: string) => string;
  onSelect: (option: string) => void;
  onClose: () => void;
}) {
  return (
    <Modal visible={visible} animationType={Platform.OS === 'web' ? 'fade' : 'slide'} transparent onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <View style={styles.sheetHead}>
            <Text style={styles.sheetTitle}>{title}</Text>
            <Pressable style={styles.closeButton} onPress={onClose}>
              <Ionicons name="close" size={20} color={colors.ink} />
            </Pressable>
          </View>
          <View style={styles.optionList}>
            {options.map((option) => {
              const active = value === option;
              return (
                <Pressable key={option} style={styles.sortOption} onPress={() => onSelect(option)}>
                  <Text style={[styles.sortOptionText, active && styles.sortOptionTextActive]}>{getLabel(option)}</Text>
                  {active ? <Ionicons name="checkmark" size={18} color={colors.buy} /> : null}
                </Pressable>
              );
            })}
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  wrap: {
    gap: 10,
  },
  controlRow: {
    minHeight: 36,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sortButton: {
    minHeight: 34,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  sortPrefix: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: '600',
  },
  sortText: {
    color: colors.ink,
    fontSize: 13,
    fontWeight: '800',
  },
  filterButton: {
    width: 34,
    height: 34,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.borderStrong,
    backgroundColor: colors.screen,
  },
  filterDot: {
    position: 'absolute',
    right: -3,
    top: -3,
    width: 9,
    height: 9,
    borderRadius: 5,
    borderWidth: 2,
    borderColor: colors.card,
    backgroundColor: colors.disc,
  },
  activeRow: {
    gap: 7,
    paddingRight: 2,
  },
  activeChip: {
    minHeight: 27,
    maxWidth: 170,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    borderRadius: radii.sm,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.discLine,
    backgroundColor: colors.discBg,
    paddingHorizontal: 8,
  },
  activeChipText: {
    color: colors.disc,
    fontSize: 11,
    fontWeight: '800',
  },
  backdrop: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(8,9,10,.38)',
  },
  sheet: {
    maxHeight: '82%',
    gap: 18,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    backgroundColor: colors.card,
    padding: 18,
    paddingBottom: 34,
  },
  sheetHead: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sheetTitle: {
    color: colors.ink,
    fontSize: 19,
    fontWeight: '900',
  },
  filterScroll: {
    flexShrink: 1,
  },
  filterContent: {
    gap: 18,
    paddingBottom: 2,
  },
  closeButton: {
    width: 34,
    height: 34,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 17,
    backgroundColor: colors.screen,
  },
  section: {
    gap: 9,
  },
  sectionTitle: {
    color: colors.faint,
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.7,
    textTransform: 'uppercase',
  },
  optionWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  option: {
    minHeight: 34,
    justifyContent: 'center',
    borderRadius: radii.sm,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    backgroundColor: colors.screen,
    paddingHorizontal: 11,
  },
  optionActive: {
    borderColor: colors.buyLine,
    backgroundColor: colors.buyBg,
  },
  optionText: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: '700',
  },
  optionTextActive: {
    color: colors.buy,
  },
  sheetActions: {
    flexDirection: 'row',
    gap: 10,
    paddingTop: 2,
  },
  resetButton: {
    flex: 1,
    minHeight: 46,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.lg,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.borderStrong,
  },
  doneButton: {
    flex: 1,
    minHeight: 46,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.lg,
    backgroundColor: colors.pill,
  },
  resetText: {
    color: colors.ink,
    fontWeight: '900',
  },
  doneText: {
    color: colors.onPill,
    fontWeight: '900',
  },
  optionList: {
    gap: 2,
  },
  sortOption: {
    minHeight: 48,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  sortOptionText: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: '700',
  },
  sortOptionTextActive: {
    color: colors.buy,
    fontFamily: typography.mono,
    fontVariant: typography.tabular,
  },
});
