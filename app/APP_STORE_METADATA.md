# GearDrop App Store Metadata Draft

Use this as the starting copy for App Store Connect. Keep the public listing brand-neutral: do not use protected brand names in the app name, subtitle, keywords, or promotional copy.

## App Information

Name:

```text
GearDrop
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

Save items to your watchlist, set target prices, and keep an eye on movement since you saved. GearDrop Pro unlocks full price history and richer low-price signals.
```

## Keywords

```text
outdoor gear,deals,price tracker,watchlist,markdowns,sale,shopping,hiking,climbing,skiing
```

## Support URL

```text
https://001.100app.dev
```

## Privacy Policy URL

Live and verified:

```text
https://001.100app.dev/privacy.html
```

## Review Notes

```text
GearDrop is a native React Native / Expo app, not a WebView wrapper. The app uses public product and price-history data, local device storage for saved items, and an email address only when a user creates a price alert.

The current build includes a local Pro status toggle as an MVP stub. Real Apple in-app purchase integration is not enabled in this version unless a later build adds StoreKit.
```

## App Privacy Answers Draft

Data collected:

```text
Email address: collected only when the user creates a price alert.
Product interaction data: saved item SKU, target price, product URL, region, and current price are stored for alert delivery and on-device watchlist behavior.
```

Linked to user:

```text
Email address may be linked to a price alert subscription.
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
5. Paywall screen
6. Privacy policy screen
```
