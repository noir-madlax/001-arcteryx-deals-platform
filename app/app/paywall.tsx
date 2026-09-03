import { Ionicons } from '@expo/vector-icons';
import * as WebBrowser from 'expo-web-browser';
import { router } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { BrandLogo } from '../components/BrandLogo';
import { usePreferences } from '../contexts/PreferencesContext';
import { usePro } from '../contexts/ProContext';
import { ProPlan, ProPlanId } from '../lib/iap';
import { colors, radii, typography } from '../lib/theme';

type FeatureValue = 'check' | 'lock' | string;

type ProFeature = {
  label: string;
  detail: string;
  free: FeatureValue;
  pro: FeatureValue;
  core?: boolean;
  shipped: boolean;
};

export const PRO_FEATURES: ProFeature[] = [
  { label: 'Browse deals, search & filter', detail: 'Current markdowns across loaded regions', free: 'check', pro: 'check', shipped: false },
  { label: 'Price history', detail: 'See where today\'s price really sits', free: '30d', pro: 'Full', core: true, shipped: true },
  { label: 'All-time-low signal', detail: '"Good time to buy" verdicts', free: 'lock', pro: 'check', core: true, shipped: true },
  { label: 'Price-drop alerts', detail: 'Set a target, get notified', free: '1', pro: 'Unlimited', shipped: false },
  { label: 'Alert speed', detail: 'How fast you hear about a drop', free: 'Daily', pro: 'Instant', shipped: false },
  { label: 'Cross-region landed cost', detail: 'Cheapest country incl. shipping & tax', free: 'lock', pro: 'check', shipped: false },
  { label: 'Saved items & no ads', detail: 'Watchlist size and a quieter app', free: '20', pro: 'Unlimited', shipped: false },
];

const visibleFeatures = PRO_FEATURES.filter((feature) => feature.shipped || __DEV__);
const TERMS_URL = 'https://www.apple.com/legal/internet-services/itunes/dev/stdeula/';
const PRIVACY_URL = 'https://geardrop.100app.dev/privacy.html';

export default function PaywallScreen() {
  const { isPro, plans, state, busyPlan, purchase, restore, redeemOfferCode, refresh } = usePro();
  const { t } = usePreferences();
  const [selectedId, setSelectedId] = useState<ProPlanId>('annual');
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    if (!plans.length || plans.some((plan) => plan.id === selectedId)) return;
    setSelectedId(plans.find((plan) => plan.id === 'annual')?.id || plans[0]!.id);
  }, [plans, selectedId]);

  const selectedPlan = useMemo(() => plans.find((plan) => plan.id === selectedId) || null, [plans, selectedId]);
  const selectedLabel = selectedPlan ? planLabel(selectedPlan.id, t) : '';

  async function handlePurchase() {
    if (isPro) {
      router.back();
      return;
    }
    if (!selectedPlan) return;
    setNotice(null);
    const outcome = await purchase(selectedPlan.id);
    if (outcome === 'purchased') {
      router.back();
    } else if (outcome === 'pending') {
      setNotice(t('paywall.pending'));
    } else if (outcome !== 'cancelled') {
      setNotice(t('paywall.purchaseFailed'));
    }
  }

  async function handleRestore() {
    setNotice(null);
    const outcome = await restore();
    if (outcome === 'restored') {
      setNotice(t('paywall.restored'));
    } else {
      setNotice(t('paywall.nothingToRestore'));
    }
  }

  async function handleRedeemOfferCode() {
    setNotice(null);
    const outcome = await redeemOfferCode();
    setNotice(outcome === 'presented' ? t('paywall.redeemPresented') : t('paywall.redeemUnavailable'));
  }

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.topbar}>
          <View style={styles.mark}>
            <BrandLogo markOnly style={styles.brandMark} />
          </View>
          <Pressable accessibilityRole="button" accessibilityLabel="Close paywall" style={styles.close} onPress={() => router.back()}>
            <Ionicons name="close" size={22} color={colors.ink} />
          </Pressable>
        </View>

        <View style={styles.head}>
          <Text style={styles.kicker}>{t('paywall.kicker')}</Text>
          <Text style={styles.title}>{t('paywall.title')}</Text>
          <Text style={styles.subtitle}>{t('paywall.subtitle')}</Text>
        </View>

        <View style={styles.table}>
          <View style={styles.tableHead}>
            <Text style={styles.tableKicker}>{t('paywall.whatYouGet')}</Text>
            <Text style={styles.tablePlan}>{t('common.free')}</Text>
            <View style={styles.proHead}>
              <Ionicons name="lock-closed-outline" size={13} color={colors.onPill} />
              <Text style={styles.proHeadText}>{t('common.pro')}</Text>
            </View>
          </View>
          {visibleFeatures.map((feature) => (
            <View key={feature.label} style={styles.row}>
              <View style={styles.feature}>
                <Text style={styles.featureTitle}>
                  {feature.label === 'Price history' ? t('paywall.priceHistory') : feature.label === 'All-time-low signal' ? t('paywall.lowSignal') : feature.label}
                  {feature.core ? <Text style={styles.coreMark}> ★core</Text> : null}
                </Text>
                <Text style={styles.featureDetail}>{feature.label === 'Price history' ? t('paywall.priceHistoryDetail') : feature.label === 'All-time-low signal' ? t('paywall.lowSignalDetail') : feature.detail}</Text>
              </View>
              <FeatureCell value={feature.free} tone="free" t={t} />
              <FeatureCell value={feature.pro} tone="pro" t={t} />
            </View>
          ))}
        </View>

        {isPro ? (
          <View style={styles.activeBanner}>
            <Ionicons name="checkmark-circle" size={21} color={colors.buy} />
            <Text style={styles.activeText}>{t('paywall.proActive')}</Text>
          </View>
        ) : (
          <View style={styles.plans}>
            {state === 'loading' ? (
              <View style={styles.loadingPlans}>
                <ActivityIndicator color={colors.ink} />
                <Text style={styles.loadingText}>{t('paywall.loadingPlans')}</Text>
              </View>
            ) : plans.length ? plans.map((plan) => (
              <PlanOption key={plan.id} plan={plan} selected={plan.id === selectedId} t={t} onPress={() => setSelectedId(plan.id)} />
            )) : (
              <View style={styles.unavailable}>
                <Text style={styles.unavailableText}>{t('paywall.unavailable')}</Text>
                <Pressable accessibilityRole="button" style={styles.retry} onPress={() => void refresh()}>
                  <Text style={styles.retryText}>{t('paywall.retry')}</Text>
                </Pressable>
              </View>
            )}
          </View>
        )}

        <Pressable
          accessibilityRole="button"
          accessibilityState={{ disabled: Boolean(busyPlan) || (!isPro && !selectedPlan) }}
          disabled={Boolean(busyPlan) || (!isPro && !selectedPlan)}
          style={[styles.cta, (busyPlan || (!isPro && !selectedPlan)) && styles.ctaDisabled]}
          onPress={() => void handlePurchase()}
        >
          {busyPlan && busyPlan !== 'restore' && busyPlan !== 'redeem' ? <ActivityIndicator color={colors.onPill} /> : null}
          <Text style={styles.ctaText}>{isPro ? t('paywall.proActive') : t('paywall.continue', { plan: selectedLabel })}</Text>
          {!busyPlan ? <Ionicons name="arrow-forward" size={17} color={colors.onPill} /> : null}
        </Pressable>

        <Pressable accessibilityRole="button" disabled={Boolean(busyPlan)} style={styles.restore} onPress={() => void handleRestore()}>
          {busyPlan === 'restore' ? <ActivityIndicator size="small" color={colors.ink} /> : <Ionicons name="refresh" size={16} color={colors.ink} />}
          <Text style={styles.restoreText}>{busyPlan === 'restore' ? t('paywall.restoring') : t('paywall.restore')}</Text>
        </Pressable>

        {!isPro ? (
          <Pressable accessibilityRole="button" disabled={Boolean(busyPlan)} style={styles.redeem} onPress={() => void handleRedeemOfferCode()}>
            {busyPlan === 'redeem' ? <ActivityIndicator size="small" color={colors.ink} /> : <Ionicons name="ticket-outline" size={16} color={colors.ink} />}
            <Text style={styles.redeemText}>{busyPlan === 'redeem' ? t('paywall.redeemingCode') : t('paywall.redeemCode')}</Text>
          </Pressable>
        ) : null}

        {notice ? <Text accessibilityRole="alert" style={styles.notice}>{notice}</Text> : null}
        <Text style={styles.fine}>{selectedPlan?.id === 'lifetime' ? t('paywall.lifetimeTerms') : t('paywall.renewalTerms')}</Text>
        <View style={styles.legalLinks}>
          <Pressable accessibilityRole="link" onPress={() => void WebBrowser.openBrowserAsync(TERMS_URL)}><Text style={styles.legalLink}>{t('paywall.terms')}</Text></Pressable>
          <Text style={styles.legalDot}>·</Text>
          <Pressable accessibilityRole="link" onPress={() => void WebBrowser.openBrowserAsync(PRIVACY_URL)}><Text style={styles.legalLink}>{t('paywall.privacy')}</Text></Pressable>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function PlanOption({ plan, selected, t, onPress }: { plan: ProPlan; selected: boolean; t: ReturnType<typeof usePreferences>['t']; onPress: () => void }) {
  return (
    <Pressable accessibilityRole="radio" accessibilityState={{ checked: selected }} style={[styles.plan, selected && styles.planSelected]} onPress={onPress}>
      <View style={styles.radioOuter}>{selected ? <View style={styles.radioInner} /> : null}</View>
      <View style={styles.planCopy}>
        <View style={styles.planTitleRow}>
          <Text style={styles.planTitle}>{planLabel(plan.id, t)}</Text>
          {plan.id === 'annual' ? <Text style={styles.bestValue}>{t('paywall.bestValue')}</Text> : null}
          {plan.trialDays ? <Text style={styles.trial}>{t('paywall.trialDays', { count: plan.trialDays })}</Text> : null}
        </View>
        {plan.id === 'annual' && plan.pricePerMonth ? <Text style={styles.planSub}>{t('paywall.perMonth', { price: plan.pricePerMonth })}</Text> : null}
      </View>
      <Text style={styles.planPrice}>{plan.price}</Text>
    </Pressable>
  );
}

function planLabel(id: ProPlanId, t: ReturnType<typeof usePreferences>['t']) {
  if (id === 'monthly') return t('paywall.planMonthly');
  if (id === 'annual') return t('paywall.planAnnual');
  return t('paywall.planLifetime');
}

function FeatureCell({ value, tone, t }: { value: FeatureValue; tone: 'free' | 'pro'; t: ReturnType<typeof usePreferences>['t'] }) {
  if (value === 'check') return <View style={styles.cell}><Ionicons name="checkmark" size={17} color={colors.buy} /></View>;
  if (value === 'lock') return <View style={styles.cell}><Ionicons name="lock-closed-outline" size={15} color={colors.faint} /></View>;
  return <View style={styles.cell}><Text style={[styles.cellText, tone === 'pro' && styles.proCellText]}>{value === 'Full' ? t('paywall.full') : value}</Text></View>;
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 22, paddingBottom: 36 },
  topbar: { minHeight: 36, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  mark: { width: 34, height: 34, alignItems: 'center', justifyContent: 'center', borderRadius: 8, borderWidth: StyleSheet.hairlineWidth, borderColor: colors.borderStrong, backgroundColor: colors.card },
  brandMark: { width: 27, height: 27 },
  close: { width: 38, height: 38, alignItems: 'center', justifyContent: 'center', borderRadius: 19 },
  head: { marginTop: 12, paddingBottom: 22 },
  kicker: { color: colors.muted, fontSize: 11, fontWeight: '800', letterSpacing: 1.4, textTransform: 'uppercase' },
  title: { maxWidth: 310, color: colors.ink, marginTop: 9, fontSize: 31, lineHeight: 36, fontWeight: '900', letterSpacing: 0 },
  subtitle: { maxWidth: 360, color: colors.muted, marginTop: 10, fontSize: 14, lineHeight: 21, fontWeight: '600' },
  table: { overflow: 'hidden', borderRadius: radii.md, borderWidth: StyleSheet.hairlineWidth, borderColor: colors.border, backgroundColor: colors.card },
  tableHead: { minHeight: 48, flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 16 },
  tableKicker: { flex: 1, color: colors.faint, fontSize: 11, fontWeight: '900', letterSpacing: 0.8, textTransform: 'uppercase' },
  tablePlan: { width: 58, color: colors.muted, textAlign: 'center', fontSize: 12, fontWeight: '800' },
  proHead: { width: 70, minHeight: 26, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 5, borderRadius: 8, backgroundColor: colors.pill },
  proHeadText: { color: colors.onPill, fontSize: 12, fontWeight: '900' },
  row: { minHeight: 66, flexDirection: 'row', alignItems: 'center', gap: 8, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border, paddingHorizontal: 16, paddingVertical: 10 },
  feature: { flex: 1, minWidth: 0 },
  featureTitle: { color: colors.ink, fontSize: 13.5, lineHeight: 18, fontWeight: '800' },
  coreMark: { color: colors.disc, fontSize: 10.5, fontWeight: '900' },
  featureDetail: { color: colors.muted, marginTop: 2, fontSize: 11.5, lineHeight: 16, fontWeight: '600' },
  cell: { width: 58, alignItems: 'center', justifyContent: 'center' },
  cellText: { color: colors.ink2, fontFamily: typography.mono, fontVariant: typography.tabular, fontSize: 12, fontWeight: '900' },
  proCellText: { color: colors.buy },
  plans: { gap: 8, marginTop: 18 },
  loadingPlans: { minHeight: 72, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10 },
  loadingText: { color: colors.muted, fontSize: 13, fontWeight: '700' },
  plan: { minHeight: 66, flexDirection: 'row', alignItems: 'center', gap: 11, borderWidth: 1, borderColor: colors.border, borderRadius: radii.sm, paddingHorizontal: 14, paddingVertical: 10, backgroundColor: colors.card },
  planSelected: { borderColor: colors.ink, backgroundColor: colors.surfaceAlt },
  radioOuter: { width: 19, height: 19, borderRadius: 10, borderWidth: 1.5, borderColor: colors.ink, alignItems: 'center', justifyContent: 'center' },
  radioInner: { width: 9, height: 9, borderRadius: 5, backgroundColor: colors.ink },
  planCopy: { flex: 1, minWidth: 0 },
  planTitleRow: { flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap', gap: 6 },
  planTitle: { color: colors.ink, fontSize: 14, fontWeight: '900' },
  bestValue: { color: colors.onPill, backgroundColor: colors.buy, borderRadius: 5, overflow: 'hidden', paddingHorizontal: 5, paddingVertical: 2, fontSize: 9.5, fontWeight: '900' },
  trial: { color: colors.buy, fontSize: 10.5, fontWeight: '900' },
  planSub: { color: colors.muted, marginTop: 3, fontSize: 11.5, fontWeight: '700' },
  planPrice: { color: colors.ink, fontFamily: typography.mono, fontVariant: typography.tabular, fontSize: 16, fontWeight: '900' },
  unavailable: { gap: 10, alignItems: 'center', borderWidth: StyleSheet.hairlineWidth, borderColor: colors.border, borderRadius: radii.sm, padding: 16, backgroundColor: colors.card },
  unavailableText: { color: colors.muted, textAlign: 'center', fontSize: 13, lineHeight: 18, fontWeight: '700' },
  retry: { minHeight: 36, justifyContent: 'center', paddingHorizontal: 14, borderRadius: 8, backgroundColor: colors.surfaceAlt },
  retryText: { color: colors.ink, fontWeight: '800' },
  activeBanner: { minHeight: 58, marginTop: 18, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, borderWidth: StyleSheet.hairlineWidth, borderColor: colors.buy, borderRadius: radii.sm, backgroundColor: colors.card },
  activeText: { color: colors.buy, fontSize: 15, fontWeight: '900' },
  cta: { minHeight: 54, marginTop: 18, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, borderRadius: radii.xl, backgroundColor: colors.pill },
  ctaDisabled: { opacity: 0.45 },
  ctaText: { color: colors.onPill, fontSize: 15, fontWeight: '900' },
  restore: { minHeight: 44, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 },
  restoreText: { color: colors.ink, fontSize: 13, fontWeight: '800' },
  redeem: { minHeight: 44, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  redeemText: { color: colors.ink, fontSize: 13, fontWeight: '800' },
  notice: { color: colors.buy, textAlign: 'center', marginTop: 2, fontSize: 12, lineHeight: 17, fontWeight: '800' },
  fine: { color: colors.faint, marginTop: 6, textAlign: 'center', fontSize: 10.5, lineHeight: 15, fontWeight: '600' },
  legalLinks: { minHeight: 34, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  legalLink: { color: colors.muted, textDecorationLine: 'underline', fontSize: 11, fontWeight: '700' },
  legalDot: { color: colors.faint },
});
