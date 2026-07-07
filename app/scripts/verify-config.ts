import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const root = process.cwd();

function readJson<T>(path: string): T {
  return JSON.parse(readFileSync(join(root, path), 'utf8')) as T;
}

function assertNoTrademark(value: string, label: string) {
  assert.ok(!/arc'?teryx|始祖鸟/i.test(value), `${label} must not contain protected brand terms`);
}

type AppConfig = {
  expo: {
    name: string;
    slug: string;
    version: string;
    scheme: string;
    icon: string;
    ios?: {
      bundleIdentifier?: string;
      buildNumber?: string;
      config?: {
        usesNonExemptEncryption?: boolean;
      };
    };
    plugins?: Array<string | [string, Record<string, unknown>]>;
  };
};

type PackageJson = {
  main: string;
  dependencies: Record<string, string>;
  scripts: Record<string, string>;
};

type EasJson = {
  build?: Record<string, unknown>;
  submit?: {
    production?: {
      ios?: Record<string, unknown>;
    };
  };
};

const appConfig = readJson<AppConfig>('app.json');
const packageJson = readJson<PackageJson>('package.json');
const easJson = readJson<EasJson>('eas.json');
const metadata = readFileSync(join(root, 'APP_STORE_METADATA.md'), 'utf8');
const actionsSource = readFileSync(join(root, 'lib/actions.ts'), 'utf8');
const layoutSource = readFileSync(join(root, 'app/_layout.tsx'), 'utf8');
const productDetailSource = readFileSync(join(root, 'app/product/[skuId].tsx'), 'utf8');
const expo = appConfig.expo;

assert.equal(expo.name, 'GearDrop');
assert.equal(expo.slug, 'geardrop');
assert.equal(expo.scheme, 'geardrop');
assert.equal(expo.ios?.bundleIdentifier, 'dev.100app.geardrop');
assert.equal(expo.ios?.buildNumber, '1');
assert.equal(expo.ios?.config?.usesNonExemptEncryption, false);
assertNoTrademark(expo.name, 'expo.name');
assertNoTrademark(expo.slug, 'expo.slug');
assertNoTrademark(expo.scheme, 'expo.scheme');
assertNoTrademark(expo.ios?.bundleIdentifier || '', 'ios.bundleIdentifier');

for (const assetPath of ['./assets/icon.png', './assets/splash-icon.png', './assets/favicon.png']) {
  assert.ok(existsSync(join(root, assetPath)), `missing asset ${assetPath}`);
}

const pluginNames = new Set((expo.plugins || []).map((plugin) => (Array.isArray(plugin) ? plugin[0] : plugin)));
for (const plugin of ['expo-router', 'expo-notifications', 'expo-web-browser', 'expo-font']) {
  assert.ok(pluginNames.has(plugin), `missing Expo plugin ${plugin}`);
}

for (const dependency of ['expo', 'expo-router', '@supabase/supabase-js', '@react-native-async-storage/async-storage', 'expo-notifications', 'react-native-svg']) {
  assert.ok(packageJson.dependencies[dependency], `missing dependency ${dependency}`);
}

assert.equal(packageJson.main, 'expo-router/entry');
assert.ok(packageJson.scripts.typecheck, 'missing typecheck script');
assert.ok(packageJson.scripts.doctor, 'missing doctor script');
assert.ok(packageJson.scripts.test, 'missing test script');
assert.ok(packageJson.scripts['eas:build:ios'], 'missing EAS iOS build script');
assert.ok(packageJson.scripts['eas:submit:ios'], 'missing EAS iOS submit script');
assert.ok(easJson.build?.production, 'missing production build profile');
assert.ok(easJson.build?.simulator, 'missing simulator build profile');
assert.ok(easJson.submit?.production?.ios, 'missing production iOS submit profile');
assert.ok(existsSync(join(root, '..', 'privacy.html')), 'missing root privacy.html for App Store privacy policy URL');
assert.ok(metadata.includes('https://001.100app.dev/privacy.html'), 'metadata missing privacy policy URL');
assert.ok(!/Privacy Policy URL[\s\S]*?TODO/.test(metadata), 'metadata privacy policy URL still has TODO');
assert.ok(actionsSource.includes('WebBrowser.openBrowserAsync(url)'), 'Buy flow must stay wrapped by openBuyUrl');
assert.ok(actionsSource.includes("data: { url: '/(tabs)/watchlist' }"), 'local price notification must deep-link to Watchlist');
assert.ok(layoutSource.includes('Notifications.addNotificationResponseReceivedListener'), 'root layout must observe notification taps');
assert.ok(layoutSource.includes('Notifications.getLastNotificationResponse'), 'root layout must handle launch-from-notification');
assert.ok(layoutSource.includes('router.push(url)'), 'notification observer must route data.url');
assert.ok(productDetailSource.includes('await insertPriceAlert'), 'Alert flow must write price_alerts');
assert.ok(productDetailSource.includes('await scheduleTestPriceNotification(name)'), 'Alert flow must exercise local notification chain');
assert.ok(productDetailSource.includes('openBuyUrl(currentProduct.url)'), 'Buy button must use openBuyUrl');

console.log(
  'config_ok name=GearDrop bundle=dev.100app.geardrop buildNumber=1 usesNonExemptEncryption=false privacyUrl=https://001.100app.dev/privacy.html plugins=' +
    [...pluginNames].join(','),
);
