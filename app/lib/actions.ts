import * as Crypto from 'expo-crypto';
import * as Haptics from 'expo-haptics';
import * as Notifications from 'expo-notifications';
import * as WebBrowser from 'expo-web-browser';
import { Platform } from 'react-native';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldPlaySound: false,
    shouldSetBadge: false,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

export async function softImpact() {
  try {
    await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  } catch {
    // Haptics can be unavailable in simulators or web previews.
  }
}

export async function openBuyUrl(url?: string | null) {
  if (!url) return;
  await WebBrowser.openBrowserAsync(url);
}

export function uuid4() {
  return Crypto.randomUUID();
}

export async function requestNotificationPermission() {
  try {
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('price-alerts', {
        name: 'Price alerts',
        importance: Notifications.AndroidImportance.MAX,
      });
    }
    const existing = await Notifications.getPermissionsAsync();
    if (existing.status === 'granted') return true;
    const requested = await Notifications.requestPermissionsAsync();
    return requested.status === 'granted';
  } catch {
    return false;
  }
}

export async function scheduleTestPriceNotification(productName: string) {
  const granted = await requestNotificationPermission();
  if (!granted) return false;
  try {
    await Notifications.scheduleNotificationAsync({
      content: {
        title: 'GearDrop alert armed',
        body: `${productName} is now on your watchlist.`,
        data: { url: '/(tabs)/watchlist' },
      },
      trigger: {
        type: Notifications.SchedulableTriggerInputTypes.TIME_INTERVAL,
        seconds: 2,
      },
    });
    return true;
  } catch {
    return false;
  }
}
