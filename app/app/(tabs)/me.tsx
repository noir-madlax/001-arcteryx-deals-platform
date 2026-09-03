import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useState } from 'react';
import { Alert, Modal, Platform, Pressable, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as WebBrowser from 'expo-web-browser';

import { useProducts } from '../../contexts/ProductsContext';
import { usePreferences } from '../../contexts/PreferencesContext';
import { usePro } from '../../contexts/ProContext';
import { CURRENCY_OPTIONS, CurrencyPreference } from '../../lib/currency';
import { LANGUAGE_LABELS, LANGUAGE_OPTIONS, LanguageChoice } from '../../lib/i18n';
import { openSupportUrl, requestNotificationPermission, scheduleTestPriceNotification } from '../../lib/actions';
import { colors, radii } from '../../lib/theme';

export default function MeScreen() {
  const { isPro, state: proState } = usePro();
  const { loadedCount } = useProducts();
  const { currency, formatNumber, languageChoice, rateDate, rateStatus, setCurrency, setLanguage, t } = usePreferences();
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [sampleStatus, setSampleStatus] = useState<string | null>(null);
  const [picker, setPicker] = useState<'language' | 'currency' | null>(null);

  async function toggleNotifications(next: boolean) {
    setSampleStatus(null);
    if (!next) {
      setNotificationsEnabled(false);
      return;
    }
    const granted = await requestNotificationPermission();
    setNotificationsEnabled(granted);
    if (!granted) Alert.alert(t('me.notificationsDisabled'), t('me.notificationsDisabledBody'));
  }

  async function sendSampleNotification() {
    setSampleStatus(null);
    const ok = await scheduleTestPriceNotification('Saved gear');
    if (ok) {
      setNotificationsEnabled(true);
      setSampleStatus(t('me.sampleSent'));
      return;
    }
    Alert.alert(t('me.permissionNeeded'), t('me.permissionNeededBody'));
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>{t('me.title')}</Text>
        <Text style={styles.subtitle}>{t('me.subtitle')}</Text>

        <View style={styles.card}>
          <View style={styles.cardHead}>
            <View>
              <Text style={styles.cardTitle}>{isPro ? t('me.proActive') : t('me.freeMode')}</Text>
              <Text style={styles.cardSub}>
                {proState === 'loading' ? t('me.proChecking') : proState === 'unavailable' || proState === 'error' ? t('me.proUnavailable') : t('me.available', { count: formatNumber(loadedCount) })}
              </Text>
            </View>
            <View style={[styles.proStatus, isPro && styles.proStatusActive]}>
              <Ionicons name={isPro ? 'checkmark' : 'lock-closed-outline'} size={15} color={isPro ? colors.onPill : colors.muted} />
              <Text style={[styles.proStatusText, isPro && styles.proStatusTextActive]}>{isPro ? t('common.pro') : t('common.free')}</Text>
            </View>
          </View>
          <Pressable style={styles.primaryRow} onPress={() => router.push('/paywall')}>
            <Text style={styles.primaryText}>{isPro ? t('me.managePro') : t('me.upgrade')}</Text>
            <Ionicons name="chevron-forward" size={18} color="#fff" />
          </Pressable>
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionLabel}>{t('me.preferences')}</Text>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t('me.language')}
            accessibilityValue={{ text: LANGUAGE_LABELS[languageChoice] }}
            style={styles.preferenceRow}
            onPress={() => setPicker('language')}
          >
            <View style={styles.preferenceLead}>
              <Ionicons name="language-outline" size={19} color={colors.ink} />
              <Text style={styles.linkText}>{t('me.language')}</Text>
            </View>
            <View style={styles.preferenceValueWrap}>
              <Text style={styles.preferenceValue}>{LANGUAGE_LABELS[languageChoice]}</Text>
              <Ionicons name="chevron-forward" size={17} color={colors.faint} />
            </View>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t('me.currency')}
            accessibilityValue={{ text: currency === 'original' ? t('me.currencyOriginal') : currency }}
            style={styles.preferenceRow}
            onPress={() => setPicker('currency')}
          >
            <View style={styles.preferenceLead}>
              <Ionicons name="cash-outline" size={19} color={colors.ink} />
              <Text style={styles.linkText}>{t('me.currency')}</Text>
            </View>
            <View style={styles.preferenceValueWrap}>
              <Text style={styles.preferenceValue}>{currency === 'original' ? t('me.currencyOriginal') : currency}</Text>
              <Ionicons name="chevron-forward" size={17} color={colors.faint} />
            </View>
          </Pressable>
          <Text style={styles.cardSub}>{t('me.currencySub')}</Text>
          {currency !== 'original' ? (
            <Text style={styles.rateStatus}>{rateDate && rateStatus !== 'unavailable' ? t('me.ratesUpdated', { date: rateDate }) : t('me.ratesUnavailable')}</Text>
          ) : null}
        </View>

        <View style={styles.card}>
          <View style={styles.settingRow}>
            <View style={styles.settingText}>
              <Text style={styles.cardTitle}>{t('me.notifications')}</Text>
              <Text style={styles.cardSub}>{t('me.notificationsSub')}</Text>
            </View>
            <Switch value={notificationsEnabled} onValueChange={toggleNotifications} trackColor={{ true: colors.accentSoft }} thumbColor={notificationsEnabled ? colors.accent : colors.faint} />
          </View>
          <Pressable style={styles.secondaryRow} onPress={sendSampleNotification}>
            <Ionicons name="notifications-outline" size={18} color={colors.ink} />
            <Text style={styles.secondaryText}>{t('me.sendSample')}</Text>
          </Pressable>
          {sampleStatus ? <Text style={styles.statusText}>{sampleStatus}</Text> : null}
        </View>

        <View style={styles.card}>
          <Pressable style={styles.linkRow} onPress={() => WebBrowser.openBrowserAsync('https://geardrop.100app.dev')}>
            <Text style={styles.linkText}>{t('me.about')}</Text>
            <Ionicons name="open-outline" size={18} color={colors.muted} />
          </Pressable>
          <Pressable accessibilityRole="link" style={styles.linkRow} onPress={openSupportUrl}>
            <Text style={styles.linkText}>{t('me.support')}</Text>
            <Ionicons name="open-outline" size={18} color={colors.muted} />
          </Pressable>
          <Pressable style={styles.linkRow} onPress={() => router.push('/privacy')}>
            <Text style={styles.linkText}>{t('me.privacy')}</Text>
            <Ionicons name="chevron-forward" size={18} color={colors.muted} />
          </Pressable>
        </View>
      </ScrollView>
      <PreferencePicker
        visible={picker === 'language'}
        title={t('me.language')}
        value={languageChoice}
        options={LANGUAGE_OPTIONS.map((value) => ({ value, label: LANGUAGE_LABELS[value] }))}
        onClose={() => setPicker(null)}
        onSelect={(value) => {
          void setLanguage(value as LanguageChoice);
          setPicker(null);
        }}
      />
      <PreferencePicker
        visible={picker === 'currency'}
        title={t('me.currency')}
        value={currency}
        options={CURRENCY_OPTIONS.map((value) => ({ value, label: value === 'original' ? t('me.currencyOriginal') : value }))}
        onClose={() => setPicker(null)}
        onSelect={(value) => {
          void setCurrency(value as CurrencyPreference);
          setPicker(null);
        }}
      />
    </SafeAreaView>
  );
}

function PreferencePicker({ visible, title, value, options, onClose, onSelect }: { visible: boolean; title: string; value: string; options: { value: string; label: string }[]; onClose: () => void; onSelect: (value: string) => void }) {
  return (
    <Modal visible={visible} transparent animationType={Platform.OS === 'web' ? 'fade' : 'slide'} onRequestClose={onClose}>
      <View style={styles.pickerBackdrop}>
        <View style={styles.pickerSheet}>
          <View style={styles.pickerHead}>
            <Text style={styles.pickerTitle}>{title}</Text>
            <Pressable style={styles.pickerClose} onPress={onClose}>
              <Ionicons name="close" size={20} color={colors.ink} />
            </Pressable>
          </View>
          {options.map((option) => (
            <Pressable
              key={option.value}
              accessibilityRole="button"
              accessibilityLabel={option.label}
              accessibilityState={{ selected: value === option.value }}
              style={styles.pickerOption}
              onPress={() => onSelect(option.value)}
            >
              <Text style={[styles.pickerOptionText, value === option.value && styles.pickerOptionActive]}>{option.label}</Text>
              {value === option.value ? <Ionicons name="checkmark" size={18} color={colors.buy} /> : null}
            </Pressable>
          ))}
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  content: {
    gap: 16,
    padding: 20,
    paddingBottom: 34,
  },
  title: {
    color: colors.ink,
    fontSize: 34,
    lineHeight: 40,
    fontWeight: '900',
  },
  subtitle: {
    color: colors.muted,
    marginTop: -10,
    fontSize: 14,
    fontWeight: '700',
  },
  card: {
    gap: 14,
    borderRadius: radii.md,
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    padding: 16,
  },
  cardHead: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  cardTitle: {
    color: colors.ink,
    fontSize: 17,
    fontWeight: '900',
  },
  proStatus: {
    minHeight: 30,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    borderRadius: 8,
    paddingHorizontal: 9,
    backgroundColor: colors.surfaceAlt,
  },
  proStatusActive: {
    backgroundColor: colors.pill,
  },
  proStatusText: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: '900',
  },
  proStatusTextActive: {
    color: colors.onPill,
  },
  cardSub: {
    color: colors.muted,
    marginTop: 4,
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '700',
  },
  primaryRow: {
    minHeight: 48,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    borderRadius: radii.sm,
    backgroundColor: colors.ink,
  },
  primaryText: {
    color: '#fff',
    fontWeight: '900',
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  settingText: {
    flex: 1,
  },
  secondaryRow: {
    minHeight: 46,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderRadius: radii.sm,
    backgroundColor: colors.surfaceAlt,
  },
  secondaryText: {
    color: colors.ink,
    fontWeight: '800',
  },
  statusText: {
    color: colors.accent,
    fontSize: 12,
    fontWeight: '800',
  },
  linkRow: {
    minHeight: 44,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  linkText: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: '800',
  },
  sectionLabel: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  preferenceRow: {
    minHeight: 46,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  preferenceLead: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 9,
  },
  preferenceValueWrap: {
    flexShrink: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: 4,
  },
  preferenceValue: {
    flexShrink: 1,
    color: colors.muted,
    fontSize: 13,
    fontWeight: '800',
  },
  rateStatus: {
    color: colors.buy,
    fontSize: 11.5,
    fontWeight: '800',
  },
  pickerBackdrop: {
    flex: 1,
    justifyContent: 'flex-end',
    backgroundColor: 'rgba(8,9,10,.38)',
  },
  pickerSheet: {
    padding: 18,
    paddingBottom: 34,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    backgroundColor: colors.card,
  },
  pickerHead: {
    minHeight: 44,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  pickerTitle: {
    color: colors.ink,
    fontSize: 19,
    fontWeight: '900',
  },
  pickerClose: {
    width: 34,
    height: 34,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 17,
    backgroundColor: colors.screen,
  },
  pickerOption: {
    minHeight: 48,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
  },
  pickerOptionText: {
    color: colors.ink,
    fontSize: 15,
    fontWeight: '700',
  },
  pickerOptionActive: {
    color: colors.buy,
  },
});
