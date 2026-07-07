import { ScrollView, StyleSheet, Text, Pressable, View } from 'react-native';

import { CATEGORY_ORDER, GENDER_LABEL, PLATFORM, REGION_LABEL, REGION_OPTIONS, SORT_OPTIONS, GENDER_OPTIONS } from '../lib/catalog';
import { colors, radii } from '../lib/theme';

type FilterState = {
  platform: string;
  region: string;
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

const SORT_LABEL: Record<string, string> = {
  discount_desc: 'Discount',
  price_asc: 'Low price',
  price_desc: 'High price',
  recent: 'Fresh',
};

export function FilterChips({ value, platforms, categories, series, onChange }: Props) {
  const normalizedPlatforms = ['all', ...platforms.slice().sort((a, b) => (PLATFORM[a]?.label || a).localeCompare(PLATFORM[b]?.label || b))];
  const normalizedCategories = [
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
      .slice(0, 12),
      ];
  const normalizedSeries = ['all', ...series.slice().filter((name) => name !== '其他').sort((a, b) => a.localeCompare(b, 'en', { sensitivity: 'base' })).slice(0, 20)];

  return (
    <View style={styles.wrap}>
      <ChipRow
        label="Source"
        options={normalizedPlatforms}
        value={value.platform}
        getLabel={(option) => (option === 'all' ? 'All' : PLATFORM[option]?.label || option)}
        onSelect={(platform) => onChange({ platform })}
      />
      <ChipRow
        label="Region"
        options={REGION_OPTIONS}
        value={value.region}
        getLabel={(option) => (option === 'all' ? 'All' : REGION_LABEL[option] || option.toUpperCase())}
        onSelect={(region) => onChange({ region })}
      />
      <ChipRow
        label="Category"
        options={normalizedCategories}
        value={value.category}
        getLabel={(option) => (option === 'all' ? 'All' : option)}
        onSelect={(category) => onChange({ category })}
      />
      <ChipRow
        label="Gender"
        options={GENDER_OPTIONS}
        value={value.gender}
        getLabel={(option) => (option === 'all' ? 'All' : GENDER_LABEL[option] || option)}
        onSelect={(gender) => onChange({ gender })}
      />
      <ChipRow
        label="Series"
        options={normalizedSeries}
        value={value.series}
        getLabel={(option) => (option === 'all' ? 'All' : option)}
        onSelect={(series) => onChange({ series })}
      />
      <ChipRow
        label="Sort"
        options={SORT_OPTIONS}
        value={value.sort}
        getLabel={(option) => SORT_LABEL[option] || option}
        onSelect={(sort) => onChange({ sort })}
      />
    </View>
  );
}

function ChipRow({
  label,
  options,
  value,
  getLabel,
  onSelect,
}: {
  label: string;
  options: string[];
  value: string;
  getLabel: (option: string) => string;
  onSelect: (option: string) => void;
}) {
  return (
    <View style={styles.rowWrap}>
      <Text style={styles.rowLabel}>{label}</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row}>
        {options.map((option) => {
          const active = value === option;
          return (
            <Pressable key={option} accessibilityRole="button" accessibilityLabel={`${label}: ${getLabel(option)}`} accessibilityState={{ selected: active }} style={[styles.chip, active && styles.chipActive]} onPress={() => onSelect(option)}>
              <Text style={[styles.chipText, active && styles.chipTextActive]} numberOfLines={1}>
                {getLabel(option)}
              </Text>
            </Pressable>
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    gap: 8,
    paddingBottom: 12,
  },
  rowWrap: {
    gap: 6,
  },
  rowLabel: {
    color: colors.faint,
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.4,
    textTransform: 'uppercase',
    paddingHorizontal: 20,
  },
  row: {
    gap: 8,
    paddingHorizontal: 20,
  },
  chip: {
    minHeight: 32,
    justifyContent: 'center',
    borderRadius: radii.sm,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    paddingHorizontal: 12,
    backgroundColor: colors.surface,
  },
  chipActive: {
    backgroundColor: colors.accentSoft,
    borderColor: colors.accent,
  },
  chipText: {
    color: colors.muted,
    fontSize: 13,
    fontWeight: '600',
  },
  chipTextActive: {
    color: colors.accent,
  },
});
