import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors, radii } from '../lib/theme';

export default function PrivacyScreen() {
  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.nav}>
        <Pressable style={styles.back} onPress={() => router.back()}>
          <Ionicons name="chevron-back" size={24} color={colors.ink} />
        </Pressable>
      </View>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.kicker}>GearDrop</Text>
        <Text style={styles.title}>Privacy policy</Text>
        <PolicyBlock
          title="What we store"
          body="Saved products and Pro status are stored on this device. Price alerts submit your email, target price, product SKU, region, product URL, and unsubscribe token so alerts can be delivered."
        />
        <PolicyBlock
          title="What we read"
          body="The app reads public product and price-history data from the GearDrop catalog. It does not read other users' price-alert subscriptions."
        />
        <PolicyBlock
          title="Notifications"
          body="Local notifications are used for alert testing in this version. Remote push notifications are not enabled."
        />
        <PolicyBlock
          title="Purchases"
          body="Pro status is stored locally in this version. Apple in-app purchases are not connected yet."
        />
        <PolicyBlock
          title="Contact"
          body="For data or privacy requests, use the contact channel associated with 001.100app.dev."
        />
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
});
