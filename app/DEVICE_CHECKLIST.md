# GearDrop iOS Device Checklist

This checklist closes the acceptance items that cannot be proven by local static checks alone.

## Local Gate

Run from `app/` before device testing:

```sh
npm run verify
```

Expected final line:

```text
verify_local_ok
```

## Expo Go Device Smoke

Start Metro on LAN:

```sh
npm run start -- --host lan --port 8081
```

Expected server line:

```text
Metro: exp://<LAN-IP>:8081
```

On iPhone:

1. Open Expo Go and scan the QR code.
2. Confirm the app opens without a red screen.
3. Confirm the default tab is Deals.
4. Switch Deals, Watchlist, and Me tabs.
5. On Deals, choose Region: Germany and confirm euro prices show.
6. Open search, enter `beta`, and confirm beta products show.
7. Open a product detail screen.
8. Confirm price chart, verdict, cheaper-region row, Alert button, and Buy button are visible.
9. Tap heart to save; open Watchlist and confirm the saved item appears.
10. Force quit Expo Go, reopen the project, and confirm Watchlist still contains the saved item.
11. Open Alert, submit a real test email and target below current price, and confirm the UI closes without error.
12. Confirm the local notification permission prompt appears when requested and the test notification is delivered.
13. Tap Buy and confirm the system browser opens the original product URL.

Record evidence:

```text
device_model=
iOS_version=
Expo_Go_version=
Metro_URL=
red_screen=no
tabs_ok=yes/no
de_filter_euro_ok=yes/no
beta_search_ok=yes/no
detail_chart_verdict_ok=yes/no
watchlist_persists_after_force_quit=yes/no
price_alert_insert_ok=yes/no
local_notification_delivered=yes/no
buy_opens_system_browser=yes/no
```

## Simulator Path

If CoreSimulator is healthy, use the full Xcode developer directory:

```sh
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun simctl list devices available
npm run ios -- --port 8081
```

If `simctl list devices available` hangs or returns no device list, do not count Simulator acceptance as complete.

## EAS Build And Submit

Required external state:

- Expo account login or `EXPO_TOKEN`
- Apple Developer account access
- App Store Connect app record for bundle id `dev.100app.geardrop`

Commands:

```sh
npm run eas:build:ios:preview
npm run eas:build:ios
npm run eas:submit:ios
```

Record evidence:

```text
eas_preview_build_id=
eas_production_build_id=
app_store_connect_app_id=
submit_status=
```
