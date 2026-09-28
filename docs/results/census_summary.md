# Coverage Census — Top 1,000 Indian Companies

## Methodology

The universe is the top 1,000 companies by market capitalisation (from the valuation universe, ranked by market cap descending). Each name is assessed for:

- **XBRL depth**: parsed annual and quarterly filings from exchange data
- **Canonical ratios**: presence of 8 core ratios at the latest period
- **Price**: fresh end-of-day close
- **Peer tier**: whether ≥5 comparable companies exist (tier 1: same business; tier 2: same sector + market-cap band; tier 3: insufficient peers)

A name is **READY** when it has sufficient XBRL history, canonical ratios, a fresh price, and a computable peer tier. A name with **≥4 parsed quarters** is considered data-ready (annual figures can be derived from Q4 integrated filings).

## Results

| Top-N | READY | DATA_GAP | BLOCKED |
|-------|-------|----------|---------|
| 100 | 94 | 4 | 2 |
| 250 | 235 | 12 | 3 |
| 500 | 473 | 24 | 3 |
| 1000 | 927 | 68 | 5 |

**927 of 1,000 names (92.7%) are READY for report generation.**

### What the DATA_GAPs are

| Gap class | Count | Cure |
|-----------|-------|------|
| Filings fetched but not parsed | 178 | Parse run (batch operation) |
| No XBRL filings discovered | 9 | Acquisition from exchange |
| Core ratios missing | 11 | Formula rebuild |
| Price stale | 1 | Price feed refresh |

### Peer tier distribution (all 1,000)

| Tier | Count | Meaning |
|------|-------|---------|
| Tier 1 | 718 | ≥5 same-business peers available |
| Tier 2 | 146 | ≥5 same-sector + same-cap-band peers |
| Tier 3 | 136 | Insufficient peers — page prints "unavailable" |

## Key findings

1. **The 100-name target is nearly met**: 94 of the top 100 are READY, with only 4 data gaps (all curable by a parse run) and 2 operational holds.
2. **Banks and financials are data-rich in quarterly XBRL but annual-report-dependent for KPIs**: NIM, CASA, credit growth etc. are deck-only metrics (the exchange doesn't tag them), which is why the tier-2 issuer-stated basis class exists.
3. **The sector KPI landscape is history-shallow**: only 1 of 737 sector×KPI rows has ≥50% of its names with 16-quarter-complete histories. The 16-quarter spine is carried by core financial ratios (statements-backed), not sector KPIs.
