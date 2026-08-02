# GearDrop / 值de App Store Metadata Draft

Use this as the starting copy for App Store Connect. Do not paste the monetization-dependent sections until the release mode is selected. Keep the public listing brand-neutral: do not use protected merchant brand names in the app name, subtitle, keywords, or promotional copy.

## Release Mode: Paid v1

The paid path was selected on 2026-07-12. The app now uses RevenueCat's StoreKit wrapper in code; the products, `Pro` entitlement, default offering, and EAS public SDK key are configured. Submission remains blocked until sandbox purchase and restore are verified.

Planned App Store products:

```text
dev.100app.geardrop.pro.monthly  auto-renewable subscription  target US price $3.99/month
dev.100app.geardrop.pro.annual   auto-renewable subscription  target US price $23.99/year
dev.100app.geardrop.pro.lifetime non-consumable               target US price $49.99
RevenueCat entitlement: Pro
RevenueCat offering: current/default with monthly, annual, and lifetime packages
```

Prices shown in the app must come from StoreKit. A seven-day trial may be configured for the subscription group; the app only advertises it when RevenueCat reports the current Apple ID as eligible.

## App Information

Name:

```text
GearDrop: Outdoor Deals
```

Simplified Chinese name:

```text
值de
```

Subtitle:

```text
Outdoor gear deal tracker
```

Category:

```text
Shopping
```

Content Rights:

```text
The app displays merchant product names, prices, and images as deal discovery links to public product pages. Confirm any additional merchant-content rights policy before submission.
```

## Promotional Text

```text
Track outdoor gear markdowns across regions, compare current prices with recent history, and save items to watch later.
```

## Description

```text
GearDrop helps outdoor shoppers spot worthwhile markdowns without sorting through long outlet catalogs.

Browse live deal feeds, filter by region and category, search by product line, and open each deal with a clear price signal. Product pages show recent price history, a simple buy-or-wait verdict, and cheaper regional alternatives when available.

Save items to your watchlist, set target prices, and keep an eye on movement since you saved.
```

Paid-release-only description addition, after real Apple IAP passes:

```text
GearDrop Pro unlocks full price history and richer low-price signals.
```

## Keywords

```text
outdoor gear,deals,price tracker,watchlist,markdowns,sale,shopping,hiking,climbing,skiing
```

## Support URL

```text
https://001.100app.dev/support.html
```

The dedicated form accepts app help, purchase, price-alert, privacy, and data requests. As of 2026-08-02 the live URL returns HTTP 404 because this branch has not been merged/deployed. Do not enter it in App Store Connect until the page and RPC migration are deployed and one controlled end-to-end request is verified.

## Privacy Policy URL

Live and verified:

```text
https://001.100app.dev/privacy.html
```

## Review Notes

```text
GearDrop is a native React Native / Expo app, not a WebView wrapper. The app uses merchant product and price-history data, local device storage for saved items, and an email address only when a user creates a price alert.

Support is available at https://001.100app.dev/support.html. Support-form submissions are stored in a private queue and are not readable through the public API.

Pro is unlocked only when the RevenueCat `Pro` entitlement is active. The paywall loads localized prices from StoreKit and includes user-triggered Restore Purchases, Terms of Use, Privacy Policy, pending-purchase handling, and cancellation/error states.

Before review, replace this paragraph with sandbox/TestFlight account instructions and the exact products verified in App Store Connect.
```

## App Privacy Answers Draft

Data collected:

```text
Email address: collected only when the user creates a price alert.
Product interaction data: saved item SKU, target price, product URL, region, and current price are stored for alert delivery and on-device watchlist behavior.
Customer support: email address, subject, message, language, and request status are collected only when the user submits the support form.
Purchase history: collected by RevenueCat for App Functionality (receipt validation and entitlements) and Analytics (subscription reporting).
```

Linked to user:

```text
Email address may be linked to a price alert subscription.
Support-form content is linked to the email address supplied in that request.
RevenueCat purchase history uses an anonymous app user ID and is not linked to the alert email or another identified user account.
```

Tracking:

```text
No third-party tracking is implemented in this version.
```

Encryption export compliance:

```text
The app does not implement custom or non-exempt encryption. iOS app config sets usesNonExemptEncryption=false for standalone builds.
```

## Screenshot Checklist

Capture after device smoke passes:

```text
1. Deals feed with New all-time low hero
2. Germany region filter showing euro prices
3. Product detail with price chart and verdict
4. Watchlist with saved item
5. StoreKit-backed Pro paywall with localized prices
6. Privacy policy screen
```

Capture item 5 only after sandbox purchase and restore flows pass. Existing 1206×2622 iPhone 16 Pro screenshots are an accepted 6.3-inch portrait size; capture clean store screenshots after the RevenueCat offering is finalized.
