# Next-Version App Store Screenshot Plan

## Boundary

This file defines the conversion story and capture requirements; it is not a completed screenshot set. Final images depend on the final signed next-version build, current StoreKit products, and a fresh device smoke pass.

Use iPhone 16 Pro portrait at 1206×2622. The first three slots are the search-results story and must remain in this order.

## Slots

| Slot | Source screen | Proof required in the signed build | Conversion job |
|---|---|---|---|
| 1 | `deals-feed` | Current feed, real product images, strongest valid low/drop signal | Establish outdoor deal discovery immediately |
| 2 | `product-detail-signal` | Price chart plus actual all-time/90-day signal or buy/wait verdict | Differentiate GearDrop from a coupon feed |
| 3 | `region-comparison` | Two or more real region prices for the exact product family | Prove cross-region intelligence |
| 4 | `watchlist` | Saved item and movement-since-save state | Show retention and tracking value |
| 5 | `pro-price-history` | StoreKit-backed paywall/full-history state with localized price | Explain the paid value without fabricated pricing |
| 6 | `display-preferences` | Region, display currency, and language controls | Close with international usefulness |

The localized headline for each slot is the same array index in `app/store-metadata/next-version.json`.

## Composition Rules

- Use only UI captured from the exact next-version signed build.
- Keep the captured UI legible; a headline may sit above it, but must not cover price signals or primary controls.
- Do not add device frames, fake notifications, invented savings, fake ratings, merchant logos, or unverified superlatives.
- Do not expose tester emails, invite codes, account names, debug overlays, placeholder images, or sandbox-only labels.
- The visible StoreKit price must match the screenshot locale/storefront and the current product returned by Apple.
- Keep merchant/product content inside the genuine app capture; keep added overlay copy brand-neutral.
- Check light and dark contrast, text clipping, image safe areas, and exact 1206×2622 output before upload.

## Product Page Optimization

After the next version is live and has enough product-page traffic, keep metadata fixed and test screenshot storytelling separately:

- Control: discovery-first order from this plan.
- Treatment A: price-intelligence first (`product-detail-signal`, then `deals-feed`).
- Treatment B: cross-region first (`region-comparison`, then `product-detail-signal`).

Do not declare a winner from a short or underpowered run. Use App Store Product Page Optimization confidence and conversion rate, then apply only the verified winner.
