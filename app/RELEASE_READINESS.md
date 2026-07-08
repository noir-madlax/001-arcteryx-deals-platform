# GearDrop iOS Release Readiness

Last updated: 2026-07-08 03:32 EDT.

This file is the current release audit for the Expo iOS port. It separates locally proven work from evidence that still requires an external account, deployment, or iOS host.

## Local Gate

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
| TypeScript / Expo doctor / iOS export | `npm run verify` passes. | Proven |
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

### EAS / Apple

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

- The MVP intentionally uses a local Pro flag to test Free and Pro states. Real StoreKit/IAP remains out of scope for this build per the task file.
- If submitting this exact build, App Review notes must clearly state that Apple IAP is not enabled and that Pro is a local MVP state. A production monetized release should replace this with StoreKit before submission.
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
