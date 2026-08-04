# GearDrop Apple IAP Setup

The app-side RevenueCat integration, matching App Store products, RevenueCat `Pro` entitlement/default offering, and EAS public iOS SDK key are configured. They were rechecked live on 2026-08-02: the default offering is Active with three real App Store packages, `Pro` is Active, and the IAP key remains `Valid credentials`. Real purchases remain unverified until the sandbox matrix below runs on a signed build.

The last real-key iPhone Simulator probe returned no StoreKit products and logged `None of the products registered in the RevenueCat dashboard could be fetched from App Store Connect`; a 2026-07-13 11:38 EDT rerun produced the same result. On 2026-08-04 Paid Apps Agreement, banking, W-8BEN, and DSA were all read back as Active. All three products are still `Prepare for Submission` without Review Information screenshots. TestFlight build `1.0.0 (4)` is now `IN_BETA_TESTING` in `GearDrop Internal`; do not treat the empty Simulator offering as resolved until the signed build-4 sandbox matrix passes.

## Fixed Contract

Do not rename these identifiers after creating them:

| Type | Identifier |
|---|---|
| Bundle ID | `dev.100app.geardrop` |
| RevenueCat entitlement | `Pro` |
| Monthly subscription | `dev.100app.geardrop.pro.monthly` |
| Annual subscription | `dev.100app.geardrop.pro.annual` |
| Lifetime non-consumable | `dev.100app.geardrop.pro.lifetime` |

The app expects the RevenueCat current offering to expose the standard monthly, annual, and lifetime packages. StoreKit supplies all displayed prices. A trial is shown only when Apple reports that the current customer is eligible.

## 1. App Store Connect

1. Confirm the app record uses bundle ID `dev.100app.geardrop`.
2. Confirm Paid Apps agreements, tax, and banking are active.
3. Create one subscription group for GearDrop Pro.
4. Create the monthly and annual auto-renewable subscriptions in that group.
5. Create the lifetime product as a non-consumable IAP.
6. Add display names, descriptions, availability, price tiers, and review screenshots for every product.
7. Optionally add a seven-day introductory free trial to the subscription group. Do not describe a trial in metadata until its eligibility behavior has been verified in sandbox.

Suggested US launch prices are `$3.99/month`, `$23.99/year`, and `$49.99` lifetime. App Store Connect remains the source of truth for storefront prices.

## 2. RevenueCat

1. Create or select the GearDrop project and add an iOS app for `dev.100app.geardrop`.
2. Connect App Store Connect using RevenueCat's current Apple integration requirements.
3. Import all three product identifiers.
4. Use entitlement `Pro` and attach all three products.
5. Create an offering, mark it current, and attach the products as the standard monthly, annual, and lifetime packages.
6. Copy the public iOS SDK key beginning with `appl_`. Never put an App Store Connect private key or RevenueCat secret key in the client or EAS public environment.

## 3. EAS Environment

Set the public SDK key for the environments used by native builds:

```sh
cd app
npx eas-cli@20.5.1 env:create production \
  --name EXPO_PUBLIC_REVENUECAT_IOS_API_KEY \
  --value 'appl_REPLACE_WITH_PUBLIC_IOS_KEY' \
  --visibility sensitive \
  --scope project \
  --non-interactive
```

Use the same command with `preview` when TestFlight-like preview builds should use the configured RevenueCat project. Confirm without printing the value:

```sh
npx eas-cli@20.5.1 env:list production
```

## 4. Sandbox Acceptance

Run these checks on a signed development, preview, or TestFlight build. Expo Go cannot load `react-native-purchases`.

1. A fresh sandbox Apple account sees localized monthly, annual, and lifetime prices.
2. Trial copy appears only for an eligible account and matches App Store Connect.
3. Cancelling the purchase sheet leaves the user on Free without an error banner.
4. Monthly purchase activates the `Pro` entitlement and unlocks full price history and the all-time-low signal.
5. Reinstalling the app and choosing Restore Purchases restores Pro.
6. An account with no purchases gets a clear no-purchases result from Restore Purchases.
7. Annual purchase and lifetime purchase each activate the same `Pro` entitlement.
8. A pending Ask to Buy transaction does not grant Pro before approval.
9. Offline launch preserves the last RevenueCat entitlement state and recovers when connectivity returns.
10. Terms of Use and Privacy Policy links open successfully.

Record the tester account type, storefront, build ID, product, displayed price, result, and screenshot for each run. Do not use a production Apple ID for sandbox evidence.

## 5. Release Commands

Only after the sandbox matrix passes and the user authorizes the paid external action:

```sh
cd app
npm run verify
npx eas-cli@20.5.1 build --platform ios --profile production
```

Upload or submit only the build whose RevenueCat public key, App Store products, metadata, privacy answers, and review notes match this contract.
