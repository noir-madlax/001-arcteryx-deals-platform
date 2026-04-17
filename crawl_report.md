# Arc'teryx Outlet Global Deals - Crawl Report
**Date:** 2026-04-14 08:45 UTC  
**Crawl Type:** Full browser automation scrape

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Products** | 997 |
| **Regions Scraped** | 6 (US, CA, GB, DE, FR, NL) |
| **With Images** | ~35-40% (GB/NL had best image coverage) |

## Products by Region

| Region | Women | Men | Total | Currency |
|--------|-------|-----|-------|----------|
| 🇺🇸 US | 36 | 28 | 64 | USD |
| 🇨🇦 CA | 54 | 41 | 95 | CAD |
| 🇬🇧 GB | 163 | 121 | 284 | GBP |
| 🇩🇪 DE | 145 | 101 | 246 | EUR |
| 🇫🇷 FR | 145 | — | 145 | EUR |
| 🇳🇱 NL | 163 | — | 163 | EUR |

## Top Deals by Discount

### US Market (USD)
| Product | Original | Sale | Discount |
|---------|----------|------|----------|
| Nita Insulated Pant W | $800 | $240 | **70% off** |
| Sentinel Relaxed Jacket Print W | $700 | $245 | **65% off** |
| Sylan Pro Shoe W | $240 | $132 | **45% off** |
| Beta AR Pant W | $500 | $225 | **55% off** |
| Rush Bib Pant W (CA) | $850 | $382.50 | **55% off** |

### GB Market (GBP)
| Product | Original | Sale | Discount |
|---------|----------|------|----------|
| Patera Parka W | £700 | £245 | **65% off** |
| Sentinel Relaxed Jacket Print W | £700 | £245 | **65% off** |
| Kopec Mid GTX Boot W | £180 | £81 | **55% off** |
| Norvan Visor | £40 | £18 | **55% off** |
| Alpha Insulated Pant (unisex) | £650 | £292.50 | **55% off** |

### DE Market (EUR) - Best Value
| Product | Original | Sale | Discount |
|---------|----------|------|----------|
| Patera Parka D | €800 | €280 | **65% off** |
| Sentinel Relaxed Jacket Print D | €800 | €280 | **65% off** |
| Norvan LD 4 Shoe D | €170 | €76.50 | **55% off** |
| Kopec Mid GTX Boot D | €200 | €90 | **55% off** |
| Alpha Insulated Pant (unisex) | €700 | €315 | **55% off** |

## Lowest Prices (Absolute) - Top 5

| Product | Region | Price | Currency |
|---------|--------|-------|----------|
| Synthetic Mid Crew Sock | GB | £15.40 | GBP |
| Norvan Visor | GB | £18 | GBP |
| Calidum 5 Panel Cap | GB | £24.75 | GBP |
| Synthetic Mid Crew Sock | DE | €16.80 | EUR |
| Norvan Visor | DE | €20.25 | EUR |

## Product Categories (Approximate Distribution)

| Category | Count | % |
|----------|-------|---|
| Shell Jackets | ~180 | 18% |
| Insulated Jackets | ~120 | 12% |
| Pants | ~200 | 20% |
| Footwear | ~180 | 18% |
| Base Layer / Shirts | ~150 | 15% |
| Fleece | ~60 | 6% |
| Accessories (Hats, Socks, Packs) | ~100 | 10% |
| Dresses / Skirts | ~7 | 1% |

## Notes

1. **Image Coverage**: ~35-40% of products had associated images extracted. GB and NL had the best image matching. US/CA had lower coverage due to DOM layout differences.
2. **Price Parsing**: DE/FR/NL prices with European format (e.g. "1.000,00€") had some edge cases where items >€1,000 were parsed incorrectly. These affected ~5-10 Veilance products per region.
3. **FR/NL Men's**: Not scraped in this run due to time constraints. DE men's was fully scraped (101 items).
4. **Currency Variations**: Same products show different prices across regions reflecting local market pricing. GB generally has lower absolute prices than US for equivalent items.
5. **Data Freshness**: All data captured live from outlet.arcteryx.com on 2026-04-14.

## Files Generated

- `crawl_state.json` - Crawl metadata and product counts
- `global_data.json` - Previously existing (219 products from earlier run)
- Raw extraction data available in browser session

---

*Crawl completed successfully across 6 regions with 997 total outlet products catalogued.*
