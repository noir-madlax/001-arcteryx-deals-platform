import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useState } from 'react';
import { Alert, Pressable, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as WebBrowser from 'expo-web-browser';

import { useProducts } from '../../contexts/ProductsContext';
import { usePro } from '../../contexts/ProContext';
import { requestNotificationPermission, scheduleTestPriceNotification } from '../../lib/actions';
import { colors, radii } from '../../lib/theme';

export default function MeScreen() {
  const { isPro, setPro } = usePro();
  const { loadedCount } = useProducts();
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [sampleStatus, setSampleStatus] = useState<string | null>(null);

  async function toggleNotifications(next: boolean) {
    setSampleStatus(null);
    if (!next) {
      setNotificationsEnabled(false);
      return;
    }
    const granted = await requestNotificationPermission();
    setNotificationsEnabled(granted);
    if (!granted) Alert.alert('Notifications disabled', 'Enable notifications in iOS Settings to receive price alerts.');
  }

  async function sendSampleNotification() {
    setSampleStatus(null);
    const ok = await scheduleTestPriceNotification('Saved gear');
    if (ok) {
      setNotificationsEnabled(true);
      setSampleStatus('Sample notification sent.');
      return;
    }
    Alert.alert('Permission needed', 'Notifications are not enabled.');
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>Me</Text>
        <Text style={styles.subtitle}>GearDrop · Gear that's worth it.</Text>

        <View style={styles.card}>
          <View style={styles.cardHead}>
            <View>
              <Text style={styles.cardTitle}>{isPro ? 'Pro active' : 'Free mode'}</Text>
              <Text style={styles.cardSub}>{loadedCount.toLocaleString('en-US')} deals are available right now.</Text>
            </View>
            <Switch value={isPro} onValueChange={setPro} trackColor={{ true: colors.accentSoft }} thumbColor={isPro ? colors.accent : colors.faint} />
          </View>
          <Pressable style={styles.primaryRow} onPress={() => router.push('/paywall')}>
            <Text style={styles.primaryText}>Upgrade to Pro</Text>
            <Ionicons name="chevron-forward" size={18} color="#fff" />
          </Pressable>
        </View>

        <View style={styles.card}>
          <View style={styles.settingRow}>
            <View style={styles.settingText}>
              <Text style={styles.cardTitle}>Notifications</Text>
              <Text style={styles.cardSub}>Get a nudge when saved gear reaches your target.</Text>
            </View>
            <Switch value={notificationsEnabled} onValueChange={toggleNotifications} trackColor={{ true: colors.accentSoft }} thumbColor={notificationsEnabled ? colors.accent : colors.faint} />
          </View>
          <Pressable style={styles.secondaryRow} onPress={sendSampleNotification}>
            <Ionicons name="notifications-outline" size={18} color={colors.ink} />
            <Text style={styles.secondaryText}>Send sample notification</Text>
          </Pressable>
          {sampleStatus ? <Text style={styles.statusText}>{sampleStatus}</Text> : null}
        </View>

        <View style={styles.card}>
          <Pressable style={styles.linkRow} onPress={() => WebBrowser.openBrowserAsync('https://001.100app.dev')}>
            <Text style={styles.linkText}>About GearDrop</Text>
            <Ionicons name="open-outline" size={18} color={colors.muted} />
          </Pressable>
          <Pressable style={styles.linkRow} onPress={() => router.push('/privacy')}>
            <Text style={styles.linkText}>Privacy policy</Text>
            <Ionicons name="chevron-forward" size={18} color={colors.muted} />
          </Pressable>
        </View>
      </ScrollView>
    </SafeAreaView>
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
});
