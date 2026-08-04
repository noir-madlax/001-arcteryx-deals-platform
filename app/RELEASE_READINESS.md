# GearDrop iOS Release Readiness

Last updated: 2026-08-04 EDT.

This file separates locally proven work from evidence that still requires Apple, App Store Connect, deployment, or product decisions. The 2026-08-04 live Apple readback below supersedes older external-state observations elsewhere in this file.

## Current Launch Snapshot

### Proven now

- The current signed candidate is on `codex/ios-appstore-build4-logo-20260804` in a clean isolated worktree. It has not been merged into `main` or deployed.
- `npm run verify` passed end to end on 2026-08-04: 39/39 tests, config, release assets, typecheck, Expo Doctor 20/20, live exchange rates, 5,689 products, 84,047 price-history rows, a 200-item image-complete startup preview, and an iOS export of 1,497 modules / 5.4 MB. The command ended with `verify_local_ok`.
- Expo account: `noir-madlax`; EAS project: `@noir-madlax/geardrop` (`ead43b0e-5dbf-44a2-838e-f65db29abb30`).
- EAS production build `33fcb413-26c7-4282-9903-1021eeb40909` finished successfully as App `1.0.0`, build `4`, from source commit `2e73e3b5553dca15c9658393d9ec866dbe1b6aa6`. Its 30,078,471-byte signed IPA has SHA-256 `ebbfcd65a1fedcf0c444b102d0639b526dfb2dc5f68c29921c2fa8175d9df8d5`; signing, Info.plist, AppIcon, Splash, and embedded logo assets were independently validated. Apple returned `VERIFY SUCCEEDED with no errors`, `UPLOAD SUCCEEDED with no errors`, then `processingState=VALID` / `APP_STORE_ELIGIBLE`.
- EAS production config resolves to `credentialsSource=remote`, `distribution=store`, and `autoIncrement=true`; production and preview each contain the Sensitive variable `EXPO_PUBLIC_REVENUECAT_IOS_API_KEY`.
- Bundle ID `dev.100app.geardrop`, version `1.0.0`, submitted build number `4`, portrait orientation.
- Physical iPhone 16 Pro Release build, Apple Development signing, wireless install, launch, live Deals, localization, currency switching, persistence, and Chinese “值de” branding have runtime evidence in `.agent/TASK-ios-app-port.md`.
- Privacy URL, website, and Support URL return HTTP 200; the Support URL is saved in App Store Connect.
- v1 is now explicitly iPhone-only because no iPad layout or screenshot acceptance has been run.
- The 1024×1024 App Store icon has been converted to RGB PNG without alpha; `npm run verify:release-assets` guards dimensions and transparency.
- Paid v1 was selected. The app now uses `react-native-purchases` with RevenueCat entitlement `Pro`, StoreKit-localized prices, purchase, restore, cancellation, pending-payment, and unavailable-service states. Local AsyncStorage Pro unlocking and the Me-screen Pro switch have been removed.
- App Store Connect app `GearDrop: Outdoor Deals` (Apple ID `6790165332`) and the three matching IAP products exist. RevenueCat App Store app `appc81815554d` has valid Apple IAP credentials; its three real products are attached to `Pro` and the default offering.
- `eas.json` production submit now targets `ascAppId` `6790165332`; config validation and resolved EAS production config pass.
- A clean Expo prebuild and CocoaPods install auto-linked `RNPurchases 10.4.2`, `PurchasesHybridCommon 18.19.0`, and `RevenueCat 5.80.2`. A code-signing-disabled iOS Simulator Release build completed with exit 0.
- That Release app was installed and launched on the iPhone 17 simulator. An intentionally invalid public SDK key produced RevenueCat `Invalid API Key` logs and the paywall's localized unavailable state without a crash or local Pro grant. The Me screen showed Free with no manual Pro toggle.
- A second arm64 Release was built with the real RevenueCat public key injected only through the process environment. It installed and launched, but StoreKit returned no products; RevenueCat logged `None of the products registered in the RevenueCat dashboard could be fetched from App Store Connect`, and the paywall stayed unavailable. A 16:01 EDT post-account-action rerun produced the same StoreKit/RevenueCat result. This proves real-key configuration/failure handling, not a successful offering or transaction.
- RevenueCat was rechecked live on 2026-08-02: the `default` offering is Active with three packages, all three real App Store product identifiers are attached, `Pro` is Active with six total products, and the App Store IAP key still shows `Valid credentials`. There are still no sandbox transactions.
- Free/Paid Apps Agreement, banking, and W-8BEN were all read back as `Active` on 2026-08-03.
- iOS 1.0 remains `PREPARE_FOR_SUBMISSION`, now with build 4 attached. Apple returned 204 for the official build-relationship PATCH and an independent GET returned build 4 ID `a9601f62-78a4-4e52-9336-8934a0c57e85`. Description, keywords, Support URL, privacy, availability outside mainland China, category, age rating, content rights, review contact, notes, and automatic release are saved; no App Review submission exists and App Store screenshots remain at 0.
- Monthly, annual, and lifetime products retain the expected identifiers, prices, localizations, and RevenueCat bindings. Apple currently returns `MISSING_METADATA` for all three because their required Review Information screenshots are absent.
- TestFlight build `1.0.0 (4)` is `IN_BETA_TESTING` and `READY_FOR_BETA_SUBMISSION`. Internal group `GearDrop Internal` now contains build 2, build 3, and build 4 with 3 testers. The group relationship, tester count, and iOS version relationship were independently read back through Apple's API after the build-4 writes.
- Five local 1206x2622 screenshots match App Store Connect's live iPhone 6.3-inch slot, but they predate the image, startup, and first-logo fixes; one homepage capture visibly contains missing-image placeholders, and they have not been uploaded. The final App Store and paywall screenshots must come from build 4 after signed StoreKit purchase and restore pass.

### Submission blockers

1. **Build-4 device smoke:** install or update to build 4 from TestFlight and verify the first logo, homepage image rendering, and 200-item startup preview before the complete catalog.
2. **IAP transaction proof:** on build 4 verify localized prices, monthly/annual/lifetime purchase, cancellation, pending purchase, entitlement activation, reinstall/restore, no-purchase restore, and offline recovery using the matrix in `IAP_SETUP.md`.
3. **Final review media:** recapture the App Store screenshots from the signed candidate after the transaction pass, then upload the App Store set and one review screenshot for each of the three IAP products. All three products currently report `MISSING_METADATA`.
4. **Submission assembly:** attach the three first-release products to iOS 1.0, perform the final export-compliance/review-information readback, and submit the version and products together.
5. **Dependency audit:** `npm audit --omit=dev --audit-level=high` exits 0 with 11 moderate findings in Expo's build-time toolchain and no high/critical findings. npm's forced fix would install Expo 46.0.21, a breaking downgrade; do not use it as a release fix.
6. **Price-alert abuse control:** the branch contains hardened support/price-alert RPCs and direct-table revocations, but the migration still lacks a production receipt/readback smoke.

### Release boundary

Build 4, Apple upload, processing, TestFlight internal-group assignment, and App Store version attachment are complete. Do not submit for App Review until the build-4 signed transaction matrix and final review screenshots are complete. The exact product and sandbox steps are in `IAP_SETUP.md`.

## Historical Local Gate (2026-07-08)

Run from `app/`:

```sh
npm run verify
```

Latest recorded result after the local notification fix, native Simulator regression, and price-alert contract hardening:

```text
# tests 23
# pass 23
config_ok name=GearDrop bundle=dev.100app.geardrop buildNumber=2 usesNonExemptEncryption=false privacyUrl=https://001.100app.dev/privacy.html plugins=expo-router,expo-status-bar,expo-web-browser,expo-notifications,expo-font
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
