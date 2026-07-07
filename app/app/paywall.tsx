import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { usePro } from '../contexts/ProContext';
import { colors, radii } from '../lib/theme';

export default function PaywallScreen() {
  const { isPro, setPro } = usePro();

  async function enable(next: boolean) {
    await setPro(next);
    router.back();
  }

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.head}>
        <Pressable style={styles.close} onPress={() => router.back()}>
          <Ionicons name="close" size={24} color={colors.ink} />
        </Pressable>
      </View>
      <View style={styles.body}>
        <Text style={styles.kicker}>GearDrop Pro</Text>
        <Text style={styles.title}>Unlock full price history and low-price signals.</Text>
        <View style={styles.card}>
          <Feature text="Full historical chart with cross-season context" />
          <Feature text="All-time low badge and richer deal signals" />
          <Feature text="Unlimited watchlist and alerts in the next billing phase" />
        </View>
        <View style={styles.pricing}>
          <Text style={styles.price}>Pro $3.99/月</Text>
          <Text style={styles.priceSub}>$23.99/年 · Lifetime $49.99</Text>
        </View>
        <Pressable style={styles.primary} onPress={() => enable(true)}>
          <Text style={styles.primaryText}>{isPro ? 'Keep Pro active' : 'Start Pro'}</Text>
        </Pressable>
        <Pressable style={styles.secondary} onPress={() => enable(false)}>
          <Text style={styles.secondaryText}>Use free mode</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

function Feature({ text }: { text: string }) {
  return (
    <View style={styles.feature}>
      <Ionicons name="checkmark-circle" size={18} color={colors.success} />
      <Text style={styles.featureText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  head: {
    alignItems: 'flex-end',
    paddingHorizontal: 18,
    paddingTop: 8,
  },
  close: {
    width: 42,
    height: 42,
    alignItems: 'center',
    justifyContent: 'center',
  },
  body: {
    flex: 1,
    padding: 24,
    gap: 18,
  },
  kicker: {
    color: colors.accent,
    fontSize: 13,
    fontWeight: '900',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  title: {
    color: colors.ink,
    fontSize: 32,
    lineHeight: 38,
    fontWeight: '900',
  },
  card: {
    gap: 14,
    borderRadius: radii.md,
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    padding: 16,
  },
  feature: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  featureText: {
    flex: 1,
    color: colors.ink,
    fontSize: 15,
    lineHeight: 21,
    fontWeight: '700',
  },
  pricing: {
    borderRadius: radii.md,
    backgroundColor: colors.ink,
    padding: 16,
  },
  price: {
    color: '#fff',
    fontSize: 22,
    fontWeight: '900',
  },
  priceSub: {
    color: '#d8d2c6',
    marginTop: 4,
    fontWeight: '700',
  },
  primary: {
    minHeight: 52,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radii.sm,
    backgroundColor: colors.accent,
  },
  primaryText: {
    color: '#fff',
    fontWeight: '900',
    fontSize: 16,
  },
  secondary: {
    minHeight: 48,
    alignItems: 'center',
    justifyContent: 'center',
  },
  secondaryText: {
    color: colors.muted,
    fontWeight: '800',
  },
});
