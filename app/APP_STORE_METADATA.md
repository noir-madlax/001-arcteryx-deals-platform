# GearDrop App Store Metadata

## Status

The ASO package is prepared for **GearDrop 1.1.0 / Build 10 only**. It must not be pasted into, or otherwise mutate, a version that is already in review.

Canonical metadata:

```text
app/store-metadata/next-version.json
```

The manifest contains five localizations (`en-US`, `zh-Hans`, `de-DE`, `fr-FR`, `ja`), localized What’s New text, six localized screenshot headlines per language, the standard Apple EULA link, and the production support/privacy URLs.

Validate before any App Store Connect edit:

```sh
cd app
npm run verify:store-metadata
```

The verifier fails closed on Apple field limits, the 100-byte keyword limit, missing locales, malformed keywords, protected or competing names, duplicate EULA links, hard-coded storefront prices, incomplete screenshot slots, or a manifest that targets the current review.

## Positioning

Primary promise:

```text
See whether an outdoor gear deal is actually worth buying now.
```

Indexed English fields:

```text
Name: GearDrop: Outdoor Deals
Subtitle: Price Tracker & Buy Signals
Keywords: gear,sale,discount,watchlist,alert,history,hiking,ski,snowboard,camping,climbing,outlet,compare,drop
```

The listing stays brand-neutral. Protected merchant names and competing app names do not belong in the name, subtitle, keywords, promotional text, description, or screenshot headlines.

## Screenshot Set

The next-version order is:

1. Deals feed — discover the strongest current outdoor price drops.
2. Product detail signal — show whether the price is genuinely low.
3. Region comparison — compare the same product across regions.
4. Watchlist — save an item and track movement after saving.
5. Pro price history — show the complete StoreKit-backed Pro value.
6. Yearbook current deals — show localized Current and Outlet/unlinked controls plus a deterministically linked live offer.

Localized overlay copy is stored in the manifest. Capture and compose the final opaque 1320×2868 images for Apple’s 6.9-inch well only from the final signed 1.1.0 / Build 10 candidate. Do not reuse old simulator evidence, fabricate prices, or add merchant marks to the overlay copy. The old 6.3-inch captures are evidence only. See `app/store-metadata/SCREENSHOT_PLAN.md`.

## Review Notes Baseline

```text
GearDrop is a native React Native / Expo app, not a WebView wrapper. It uses public merchant product and price-history data, stores saved products on-device, and collects an email address only when the user creates a price alert or sends a support request.

In 1.1, the new Yearbook tab displays current full-price catalog records for three outdoor brands. Live discounts are linked only by a validated official style ID or one unique normalized exact-name match. Discounted listings that cannot be linked reliably appear in a separate Outlet / Unlinked view and are not represented as discontinued official styles.

Pro access is granted only from the RevenueCat `Pro` entitlement. The paywall loads localized prices from StoreKit and includes user-triggered Restore Purchases, Apple offer-code redemption, Terms of Use, Privacy Policy, pending-purchase handling, and cancellation/error states.

Products included with the first paid release:
- dev.100app.geardrop.pro.monthly
- dev.100app.geardrop.pro.annual
- dev.100app.geardrop.pro.lifetime

Support: https://geardrop.100app.dev/support.html
Privacy: https://geardrop.100app.dev/privacy.html
Terms: https://www.apple.com/legal/internet-services/itunes/dev/stdeula/
```

Before submission, replace or extend these notes with evidence from the exact next-version build and the current App Store Connect product states. Do not copy historical sandbox credentials into the repository.

## App Privacy Baseline

Data collected depends on user action:

- Email address and product/target-price details when a price alert is created.
- Email address, subject, message, language, and request status when support is contacted.
- Purchase history handled by Apple and RevenueCat for entitlement validation and subscription reporting.

Saved watchlist items remain on-device. RevenueCat uses an anonymous app user ID that is not intentionally linked to the alert or support email. No third-party advertising tracking is implemented in the reviewed source baseline.

These are preparation notes, not proof of the live App Privacy answers. Read the live form again before the next submission.

## Next-Version Apply Boundary

1. Read the live App, version, build, localization, screenshot, IAP, release-mode, and review-submission state.
2. Wait until a new editable App version exists; do not edit an in-review version.
3. Re-run the metadata verifier and the full App release gate on the final source commit.
4. Capture all 30 localized 6.9-inch screenshots from that exact signed build, verify every visible claim and StoreKit price, and run `npm run verify:store-screenshots`.
5. Apply only the five manifest localizations and six matching screenshot sets.
6. Use a fresh process or fresh UI navigation to read back every field, What’s New value, screenshot-set display type, and screenshot count.
7. Keep metadata edit and App Review submission as separately authorized external actions.

Research and measurement rationale: `reports/2026-08-14-geardrop-next-version-aso.md`.
