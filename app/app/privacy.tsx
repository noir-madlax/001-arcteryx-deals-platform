import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { usePreferences } from '../contexts/PreferencesContext';
import { openSupportUrl } from '../lib/actions';
import { colors, radii } from '../lib/theme';

export default function PrivacyScreen() {
  const { t } = usePreferences();
  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.nav}>
        <Pressable style={styles.back} onPress={() => router.back()}>
          <Ionicons name="chevron-back" size={24} color={colors.ink} />
        </Pressable>
      </View>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.kicker}>{t('brand.name')}</Text>
        <Text style={styles.title}>{t('privacy.title')}</Text>
        <PolicyBlock
          title={t('privacy.storeTitle')}
          body={t('privacy.storeBody')}
        />
        <PolicyBlock
          title={t('privacy.readTitle')}
          body={t('privacy.readBody')}
        />
        <PolicyBlock
          title={t('privacy.notificationsTitle')}
          body={t('privacy.notificationsBody')}
        />
        <PolicyBlock
          title={t('privacy.purchasesTitle')}
          body={t('privacy.purchasesBody')}
        />
        <PolicyBlock
          title={t('privacy.contactTitle')}
          body={t('privacy.contactBody')}
        />
        <Pressable accessibilityRole="link" style={styles.supportButton} onPress={openSupportUrl}>
          <Text style={styles.supportButtonText}>{t('privacy.openSupport')}</Text>
          <Ionicons name="open-outline" size={18} color={colors.onPill} />
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

function PolicyBlock({ title, body }: { title: string; body: string }) {
  return (
    <View style={styles.block}>
      <Text style={styles.blockTitle}>{title}</Text>
      <Text style={styles.blockBody}>{body}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  nav: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  back: {
    width: 42,
    height: 42,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 21,
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
  },
  content: {
    gap: 14,
    padding: 20,
    paddingBottom: 36,
  },
  kicker: {
    color: colors.accent,
    fontSize: 12,
    fontWeight: '900',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  title: {
    color: colors.ink,
    fontSize: 32,
    lineHeight: 38,
    fontWeight: '900',
    marginBottom: 4,
  },
  block: {
    gap: 6,
    borderRadius: radii.md,
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    padding: 16,
  },
  blockTitle: {
    color: colors.ink,
    fontSize: 16,
    fontWeight: '900',
  },
  blockBody: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 21,
    fontWeight: '600',
  },
  supportButton: {
    minHeight: 48,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderRadius: radii.md,
    backgroundColor: colors.accent,
    paddingHorizontal: 16,
  },
  supportButtonText: {
    color: colors.onPill,
    fontSize: 15,
    fontWeight: '900',
  },
});
