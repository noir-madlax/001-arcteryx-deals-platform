# GearDrop iOS Release Readiness

Last updated: 2026-08-02 11:07 EDT.

This file separates locally proven work from evidence that still requires Apple, App Store Connect, deployment, or product decisions. The 2026-08-02 snapshot below is authoritative for local, EAS, RevenueCat, and the read-only App Store Connect audit completed after fresh login.

## Current Launch Snapshot

### Proven now

- The preserved iOS release work is now on `codex/ios-appstore-launch-20260802`, based on the 2026-08-02 `origin/main` snapshot. It has not been merged into `main` or deployed.
- `npm run verify` passed end to end on 2026-08-02: 37/37 tests, config, release assets, typecheck, Expo Doctor 20/20, live exchange rates, 5,812 products, 83,934 price-history rows, and an iOS export of 1,492 modules / 5.4 MB. The command ended with `verify_local_ok`.
- Expo account: `noir-madlax`; EAS project: `@noir-madlax/geardrop` (`ead43b0e-5dbf-44a2-838e-f65db29abb30`).
- EAS iOS build list returned `[]` again on 2026-08-02; no cloud production build has been created or charged by this continuation pass.
- EAS production config resolves to `credentialsSource=remote`, `distribution=store`, and `autoIncrement=true`; production and preview each contain the Sensitive variable `EXPO_PUBLIC_REVENUECAT_IOS_API_KEY`.
- Bundle ID `dev.100app.geardrop`, version `1.0.0`, local build number `1`, portrait orientation.
- Physical iPhone 16 Pro Release build, Apple Development signing, wireless install, launch, live Deals, localization, currency switching, persistence, and Chinese “值de” branding have runtime evidence in `.agent/TASK-ios-app-port.md`.
- Privacy URL and website return HTTP 200 on 2026-07-12.
- v1 is now explicitly iPhone-only because no iPad layout or screenshot acceptance has been run.
- The 1024×1024 App Store icon has been converted to RGB PNG without alpha; `npm run verify:release-assets` guards dimensions and transparency.
- Paid v1 was selected. The app now uses `react-native-purchases` with RevenueCat entitlement `Pro`, StoreKit-localized prices, purchase, restore, cancellation, pending-payment, and unavailable-service states. Local AsyncStorage Pro unlocking and the Me-screen Pro switch have been removed.
- App Store Connect app `GearDrop: Outdoor Deals` (Apple ID `6790165332`) and the three matching IAP products exist. RevenueCat App Store app `appc81815554d` has valid Apple IAP credentials; its three real products are attached to `Pro` and the default offering.
- `eas.json` production submit now targets `ascAppId` `6790165332`; config validation and resolved EAS production config pass.
- A clean Expo prebuild and CocoaPods install auto-linked `RNPurchases 10.4.2`, `PurchasesHybridCommon 18.19.0`, and `RevenueCat 5.80.2`. A code-signing-disabled iOS Simulator Release build completed with exit 0.
- That Release app was installed and launched on the iPhone 17 simulator. An intentionally invalid public SDK key produced RevenueCat `Invalid API Key` logs and the paywall's localized unavailable state without a crash or local Pro grant. The Me screen showed Free with no manual Pro toggle.
- A second arm64 Release was built with the real RevenueCat public key injected only through the process environment. It installed and launched, but StoreKit returned no products; RevenueCat logged `None of the products registered in the RevenueCat dashboard could be fetched from App Store Connect`, and the paywall stayed unavailable. A 16:01 EDT post-account-action rerun produced the same StoreKit/RevenueCat result. This proves real-key configuration/failure handling, not a successful offering or transaction.
- RevenueCat was rechecked live on 2026-08-02: the `default` offering is Active with three packages, all three real App Store product identifiers are attached, `Pro` is Active with six total products, and the App Store IAP key still shows `Valid credentials`. There are still no sandbox transactions.
- App Store Connect was rechecked live after the account holder submitted W-8BEN on 2026-08-02. W-8BEN is now `Active`, Paid Apps Agreement advanced from `Pending User Info` to `Processing`, the bank account remains `Processing`, and Free Apps Agreement remains `Active`.
- iOS 1.0 remains `Prepare for Submission` with no build and no App Review submission. The version has 0 screenshots and blank Description, Keywords, Support URL, Copyright, and App Review contact/account fields. App Information still lacks Subtitle, Category, Content Rights, and Age Ratings; App Privacy has no URL and its questionnaire has not started. App price and availability are not set.
- Monthly, annual, and lifetime products are present with the expected identifiers, all-region availability, prices, and English (U.S.) localization. All three remain `Prepare for Submission`; their required Review Information screenshots are absent. RevenueCat remains correctly bound to those same identifiers.
- Five local 1206x2622 screenshots match App Store Connect's live iPhone 6.3-inch slot, but they are unsigned-Simulator readiness evidence and have not been uploaded. The paywall screenshot is intentionally absent until a signed sandbox/TestFlight purchase and restore pass.

### Submission blockers

1. **IAP transaction proof:** the three matching App Store products, RevenueCat `Pro` entitlement, default monthly/annual/lifetime offering, EAS public key, and submit `ascAppId` are configured. The real-key Simulator run still returns empty StoreKit products. After Apple commercial/metadata blockers clear, verify localized prices, purchase, cancellation, pending purchase, entitlement activation, reinstall/restore, and no-purchase restore on a signed sandbox/TestFlight build.
2. **Apple commercial state:** W-8BEN is `Active`, closing the tax-form gap. Paid Apps Agreement and banking are still `Processing`; paid IAP cannot launch until Apple finishes processing and the agreement becomes `Active`.
3. **App Store metadata:** Subtitle, Category, Content Rights, Age Ratings, App Privacy, app price/availability, Description, Keywords, Support URL, Copyright, review credentials/contact/notes, and final screenshots are incomplete.
4. **IAP review metadata:** the three products are configured and localized, but each is still `Prepare for Submission` and lacks its Review Information screenshot. The first products must be reviewed with iOS 1.0.
5. **Distribution credentials/build:** this Mac currently has an Apple Development identity, not an Apple Distribution identity. EAS remote Distribution credentials remain uninspected; EAS and TestFlight both show no iOS builds.
6. **Public support contact:** `https://001.100app.dev/support.html` returns HTTP 404 on 2026-08-02. This branch contains the page and hardened RPC migration, but neither is deployed; the Support URL cannot be entered as live yet.
7. **Content rights:** merchant product names, images, and prices require a defensible rights/permission basis for the selected storefronts.
8. **App Privacy answers:** email, price-alert interaction data, support requests, and RevenueCat purchase history must be declared in App Store Connect and reviewed against all bundled third-party SDKs.
9. **Dependency audit:** the 2026-08-02 `npm audit --omit=dev` exits 1 with 10 moderate findings rooted in Expo's build-time `@expo/config-plugins -> xcode -> uuid <11.1.1` chain. npm's forced fix would install Expo 46.0.21, a breaking downgrade; do not use it as a release fix.
10. **Price-alert abuse control:** the branch contains hardened support/price-alert RPCs and direct-table revocations, but the migration is not verified in production. Deployment plus receipt/readback smoke remains required.

### Release boundary

Do not run a paid EAS production build, upload TestFlight, publish App Privacy answers, or submit for review until the relevant external action is explicitly authorized. The exact product and sandbox steps are in `IAP_SETUP.md`.

## Historical Local Gate (2026-07-08)

Run from `app/`:

```sh
npm run verify
```

Latest recorded result after the local notification fix, native Simulator regression, and price-alert contract hardening:

```text
# tests 23
# pass 23
config_ok name=GearDrop bundle=dev.100app.geardrop buildNumber=1 usesNonExemptEncryption=false privacyUrl=https://001.100app.dev/privacy.html plugins=expo-router,expo-status-bar,expo-web-browser,expo-notifications,expo-font
20/20 checks passed. No issues detected!
products_content_range=0-0/6108
price_history_content_range=0-0/73302
paginated_products_loaded=6108
iOS Bundled 4170ms node_modules/expo-router/entry.js (1440 modules)
verify_local_ok
```

Also verified after the run:

```text
find app -maxdepth 2 \( -name dist-check -o -name web-check -o -name '.expo' \) -print
# no output

git status --short --ignored app/node_modules
!! app/node_modules/
```

The first full `npm run verify` attempt hit a transient Supabase TLS `ECONNRESET` during `verify:live-data`; `npm run verify:live-data` was retried successfully, then the full `npm run verify` command passed.

After the final rebase onto the latest remote data commit, targeted checks also passed: `npm test`, `npm run verify:config`, `npm run typecheck`, and `npm run verify:live-data`. The latest targeted live-data result reported `products_content_range=0-0/6108` and `price_history_content_range=0-0/73304`.

After the local gate, LAN Metro on port 8081 remained intentionally running via launchd for optional manual Expo Go smoke testing. A temporary native Simulator Metro on port 8084 was used for the current regression and should be stopped after verification.

Live privacy URL was verified after the Vercel deployment:

```text
curl -I https://001.100app.dev/privacy.html
HTTP/2 200
x-vercel-cache: HIT
content-type: text/html; charset=utf-8
```

## Acceptance Matrix

| Requirement | Current evidence | Status |
|---|---|---|
| Expo app starts locally | Native Debug app launched on iPhone 17 iOS 26.5 Simulator from `/tmp/geardrop-derived-generic/Build/Products/Debug-iphonesimulator/GearDrop.app` against Metro `localhost:8084`; LAN Metro still returns `packager-status:running` at `http://192.168.50.88:8081/status`. | Native Simulator proven; physical Expo Go optional |
| Bottom tabs Deals / Watchlist / Me | Native Simulator screenshots show Deals, Watchlist, and Me tabs. | Native Simulator proven |
| Deals loads live products, DE euro filter, beta search, signals, hero | `verify:live-data` proves 6108 live products, DE euro beta sample, beta count 333, signal sample. Native Simulator loaded Deals with `6,108 loaded · 705 shown`. | Proven |
| Product detail chart, verdict, cheaper region | Native Simulator detail screen shows `Alpha Pant Women's`, price, chart/paywall area, verdict, Alert, and Buy. `verify:live-data` proves signal and cheaper-region data. | Proven |
| Free/Pro price history gate | Code path uses `usePro()` with 30-day free chart and full-history Pro chart; TypeScript/export pass. | Static/code proven |
| Watchlist persistence | Native Simulator saved `Alpha Pant Women's`, force-quit/relaunched the app, and Watchlist still showed `1 saved`. Pure storage tests also pass. | Proven |
| Price alert insert | Prior live app-shaped insert returned HTTP 201. Current detail flow calls tested `buildPriceAlertPayload()` -> `insertPriceAlert()` and stores local alert target after the insert succeeds. Unit tests prove payload fields, nullable target handling, safe URL/image fallbacks, `POST /rest/v1/price_alerts`, `Prefer: return=minimal`, and failure propagation without follow-up calls. | Contract proven; repeat live insert only with approved test email |
| Local notification chain | `scheduleTestPriceNotification()` now checks iOS `ios.status`, schedules an immediate local notification, and avoids blocking the banner with a success Alert. Native Simulator screenshot `/tmp/geardrop-regression-sample-notification-result.png` shows the `GearDrop alert armed` system banner; SpringBoard logs show destinations `NotificationCenter, LockScreen, Alert`. Notification tap routing remains statically asserted by `verify:config`. | Delivery proven; tap route static/code proven |
| Buy opens system browser | Native Simulator screenshot `/tmp/geardrop-buy-after-click-sim.png` shows iOS WebBrowser/SafariViewController opening `outlet.arcteryx.com`; code path still wraps `WebBrowser.openBrowserAsync(url)`. | Proven |
| App Store privacy policy URL | `https://001.100app.dev/privacy.html` returns HTTP 200 and contains the GearDrop policy. | Proven |
| TypeScript / Expo doctor / iOS export | Post-IAP `npm run verify` passed 36/36 tests, config, assets, typecheck, Doctor 20/20, and rates before failing only the live `4,970 < 5,000` threshold. Separate iOS export bundled 1,488 modules and emitted a 5.3 MB HBC file. | Code/export proven; complete gate blocked by live count |
| `node_modules` not staged | `app/node_modules/` is ignored. | Proven |

## Current External State

### Optional Expo Go device smoke

Native Simulator evidence now covers the main device-smoke checklist. LAN Metro is still running for optional physical iPhone / Expo Go testing:

```text
PID file: /tmp/geardrop-expo-metro.pid
Log file: /tmp/geardrop-expo-metro.log
Metro URL: exp://192.168.50.88:8081
Status probe: http://192.168.50.88:8081/status -> packager-status:running
Launchd job: geardrop-expo-metro
```

Expo CLI still reports a `simctl` warning during startup:

```text
Unable to run simctl:
Error: xcrun simctl help exited with non-zero code: 72
```

Use `app/DEVICE_CHECKLIST.md` for physical-device evidence fields if a real iPhone pass is desired. Stop LAN Metro after device testing with:

```sh
launchctl remove geardrop-expo-metro
```

### Live privacy URL

Resolved by commit `23f56c67e74ed9383a4d9eb0bfff5dc4edb4b2a0` (`Add GearDrop privacy policy page`) and Vercel production deployment `dpl_7vdAywivmeqRZBHvXBUEo2Ak35K4`.

Live check:

```text
curl -I https://001.100app.dev/privacy.html
HTTP/2 200
content-type: text/html; charset=utf-8
server: Vercel
```

Content check:

```text
Privacy Policy - GearDrop
GearDrop helps shoppers discover outdoor gear markdowns
GearDrop stores the email address you enter
GearDrop does not implement third-party advertising tracking in this version
```

### Simulator host

Full Xcode is installed:

```text
Xcode 26.6
Build version 17F113
iOS SDK 26.5
iOS Simulator SDK 26.5
```

Current Simulator acceptance was completed through direct Xcode/`simctl` commands:

```text
device=43718BED-F3F6-41ED-B781-80BD3B83B85C
runtime=iOS 26.5
bundle=dev.100app.geardrop
app=/tmp/geardrop-derived-generic/Build/Products/Debug-iphonesimulator/GearDrop.app
```

Native build evidence:

```text
** BUILD SUCCEEDED **
GearDrop: Mach-O 64-bit executable arm64
```

The Debug simulator app still shows this non-fatal LogBox on launch because the temporary build was produced with code signing disabled:

```text
[expo-notifications] Error reading persisted server registration info:
Keychain access failed: A required entitlement isn't present.
```

It did not block the native smoke run or local notification banner delivery. For EAS/TestFlight builds, verify again with normal signing entitlements instead of this temporary `CODE_SIGNING_ALLOWED=NO` Simulator build.

Temporary native Simulator Metro:

```text
localhost:8084
```

Stop it after this regression. Keep the LAN 8081 Metro only if physical Expo Go testing is still desired.

### Vercel CLI

Current CLI state:

```text
vercel whoami
No existing credentials found. Starting login flow...
```

The CLI needs `vercel login`, or publish via GitHub main as above.

### EAS / Apple (historical 2026-07-08; superseded by Current Launch Snapshot)

Current EAS state:

```text
env | cut -d= -f1 | rg -i '^(EXPO|EAS|APPLE|ASC|APP_STORE|FASTLANE|MATCH|ITC|IOS|DEVELOPER)_'
# no output

cd app && npx eas-cli whoami
Not logged in
```

Required before final build/submit:

- Expo login or `EXPO_TOKEN`
- Apple Developer account
- App Store Connect app record for `dev.100app.geardrop`
- Final decision on merchant content rights wording

## Submission Notes

- The local Pro flag has been removed. Pro is granted only from an active RevenueCat `Pro` entitlement.
- Do not submit until the sandbox matrix in `IAP_SETUP.md` has transaction evidence.
- The app is native React Native / Expo, not a WebView wrapper.

## Source Control

The initial Expo app source is committed on `main`:

```text
commit=15f9d8c6c6acd70eb2563fd1e0c7f72756681cba
message=Add GearDrop Expo iOS app
```

The live privacy page is also committed and deployed:

```text
commit=23f56c67e74ed9383a4d9eb0bfff5dc4edb4b2a0
message=Add GearDrop privacy policy page
```

Current working tree changes after that commit include the iOS notification permission/display fix and this readiness update. They are verified locally but not committed unless explicitly staged and committed after review.

The same push triggered Vercel production deployment `dpl_DnpGEbHmjGPJLwEhLJTV76fN8WoV`. The root static site remained healthy and `.vercelignore` kept the app source out of the deployed public site:

```text
https://001.100app.dev/ -> HTTP/2 200
https://001.100app.dev/privacy.html -> HTTP/2 200
https://001.100app.dev/app/package.json -> HTTP/2 404
```
