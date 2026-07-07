# GearDrop iOS Release Readiness

Last updated: 2026-07-07 19:06 EDT.

This file is the current release audit for the Expo iOS port. It separates locally proven work from evidence that still requires an external account, deployment, or iOS host.

## Local Gate

Run from `app/`:

```sh
npm run verify
```

Latest recorded result after the live privacy deployment:

```text
# tests 19
# pass 19
config_ok name=GearDrop bundle=dev.100app.geardrop buildNumber=1 usesNonExemptEncryption=false privacyUrl=https://001.100app.dev/privacy.html plugins=expo-router,expo-status-bar,expo-web-browser,expo-notifications,expo-font
20/20 checks passed. No issues detected!
products_content_range=0-0/6108
price_history_content_range=0-0/73296
paginated_products_loaded=6108
iOS Bundled 4418ms node_modules/expo-router/entry.js (1439 modules)
verify_local_ok
```

Also verified after the run:

```text
find app -maxdepth 2 \( -name dist-check -o -name web-check -o -name '.expo' \) -print
# no output

git status --short --ignored app/node_modules
!! app/node_modules/
```

After the local gate, Metro was intentionally restarted via launchd for manual device smoke testing.

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
| Expo app starts locally | Launchd-managed LAN Metro currently returns `packager-status:running` at `http://192.168.50.88:8081/status`. | Locally started, device smoke still needed |
| Bottom tabs Deals / Watchlist / Me | Web smoke previously clicked all three tabs; native device still needed. | Partially proven |
| Deals loads live products, DE euro filter, beta search, signals, hero | `verify:live-data` proves 6108 live products, DE euro beta sample, beta count 333, signal sample. Web smoke previously verified UI. | Locally proven, native visual still needed |
| Product detail chart, verdict, cheaper region | Web smoke and `verify:live-data` prove product route, signal, cheaper region sample. | Locally proven, native visual still needed |
| Free/Pro price history gate | Code path uses `usePro()` with 30-day free chart and full-history Pro chart; TypeScript/export pass. | Static/code proven |
| Watchlist persistence | Pure watchlist storage tests pass; real kill-app persistence requires iOS host. | Unit proven, host verification missing |
| Price alert insert | Prior live app-shaped insert returned HTTP 201; current detail flow still calls `insertPriceAlert()` and stores local alert target. | Live insert previously proven; repeat only with approved test email |
| Local notification chain | `scheduleTestPriceNotification()` requests permission, schedules a 2-second local notification, and deep-links to Watchlist on tap; `verify:config` asserts this path. | Static/code proven, iOS notification delivery missing |
| Buy opens system browser | `openBuyUrl()` wraps `WebBrowser.openBrowserAsync(url)` and product detail uses it. | Static/code proven, host verification missing |
| App Store privacy policy URL | `https://001.100app.dev/privacy.html` returns HTTP 200 and contains the GearDrop policy. | Proven |
| TypeScript / Expo doctor / iOS export | `npm run verify` passes. | Proven |
| `node_modules` not staged | `app/node_modules/` is ignored. | Proven |

## Current External Blockers

### Expo Go device smoke

Metro is currently running for manual iPhone / Expo Go testing:

```text
PID file: /tmp/geardrop-expo-metro.pid
Log file: /tmp/geardrop-expo-metro.log
Metro URL: exp://192.168.50.88:8081
Status probe: http://192.168.50.88:8081/status -> packager-status:running
Launchd job: geardrop-expo-metro
```

Expo reported the same CoreSimulator issue during startup:

```text
Unable to run simctl:
Error: xcrun simctl help exited with non-zero code: 72
```

Use `app/DEVICE_CHECKLIST.md` for the manual evidence fields. Stop Metro after device testing with:

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

`simctl` still hangs:

```text
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun simctl list devices available
# no device list within 15-25 seconds
```

CoreSimulator diagnosis:

```text
/Library/Developer/PrivateFrameworks/CoreSimulator.framework/Resources/bin/simdiskimaged
/Library/Developer/PrivateFrameworks/CoreSimulator.framework/.../com.apple.CoreSimulator.CoreSimulatorService
```

Two old root-owned CoreSimulator processes cannot be killed by the current user:

```text
kill -9 53945 53974
operation not permitted
```

Recommended host repair, to run only when it is acceptable to interrupt local Simulator services:

```sh
sudo pkill -9 -f '/CoreSimulator.framework'
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun simctl list devices available
```

If that does not recover the service, reboot macOS before counting Simulator acceptance.

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
