# iPhone 6.9-inch App Store Screenshots

Target device: iPhone 16 Pro Max, portrait, 1320 x 2868 pixels. Final files must be opaque RGB PNGs without alpha.

Each locale directory (`en-US`, `zh-Hans`, `de-DE`, `fr-FR`, `ja`) must contain:

1. `01-deals-feed.png`
2. `02-product-detail-signal.png`
3. `03-region-comparison.png`
4. `04-watchlist.png`
5. `05-pro-price-history.png`
6. `06-yearbook-current-deals.png`

Capture the visible UI from the exact signed 1.1.0 / Build 10 candidate after device smoke and StoreKit price verification. Added overlay copy must match `store-metadata/next-version.json`. Do not use fixture data, fabricate prices, expose tester data, or imply that unlinked deals are absent from a current official catalog.

Validate before upload:

```sh
npm run verify:store-screenshots
```
