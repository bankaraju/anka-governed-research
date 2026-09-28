# Anka — Architecture Overview

## The pipeline in one diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  XBRL FILINGS          FORMULA LAYER         CLAIM LAYER            │
│  (BSE/NSE exchanges)   (versioned, tested)   (the contract)         │
│                                                                     │
│  ┌──────────┐    ┌───────────────┐    ┌──────────────────────┐     │
│  │ Parse    │    │ Compute       │    │ Label: status,       │     │
│  │ XBRL     ├───>│ canonical    ├───>│ confidence, basis,   │     │
│  │ facts    │    │ ratios       │    │ provenance           │     │
│  └──────────┘    └───────────────┘    └──────────┬───────────┘     │
│                                                    │                │
│  ┌──────────┐    ┌───────────────┐    ┌──────────▼───────────┐     │
│  │ Document │    │ LLM writer    │    │ VERIFY               │     │
│  │ extrac-  │    │ (frozen facts │    │ • whole-page         │     │
│  │ tion     ├───>│ only, no     │    │   inventory           │     │
│  │ (decks)  │    │ outside nums)│    │ • numeral identity    │     │
│  └──────────┘    └───────────────┘    │ • basis contract     │     │
│                                       │ • mutant gates       │     │
│                                       └──────────┬───────────┘     │
│                                                    │                │
│                                       ┌──────────▼───────────┐     │
│                                       │ RENDER               │     │
│                                       │ HTML tearsheet       │     │
│                                       │ (every numeral       │     │
│                                       │  bound to a claim)   │     │
│                                       └──────────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## The layers

### 1. Data ingestion (XBRL + documents)
- **XBRL parser** reads exchange filings (BSE, NSE) into a single canonical store — one value per cell, per period, per basis
- **Document extraction** reads annual reports and investor decks for KPIs that XBRL doesn't tag (utilisation, order book, segment mix)
- Both paths stamp provenance: source file, formula, extraction method

### 2. Formula layer (versioned, tested, mutant-gated)
- Canonical ratios computed from parsed facts through **versioned formulas** — each formula has an ID and version tracked per snapshot
- When a formula changes, the system generates a **migration inventory**: which rows were computed under the superseded version, what the replayed values would be, and whether the change is material — before any store write
- Every formula rule is pinned by a fail-side mutant: break the rule, a named test must fail

### 3. Claim layer (the contract)
Every figure in a report is a **claim** that carries:

| Field | Values | What it means |
|-------|--------|---------------|
| `status` | company_disclosed, company_reported, calculated, market_derived, estimate | Who produced the number |
| `confidence` | high, medium, low | How much to trust it (weakest-input rule) |
| `served_basis` | STANDALONE, CONSOLIDATED, UNSPECIFIED, MARKET, DERIVED, BRIDGE, EVENT, LADDER | What basis the figure is actually on |
| `pinned_basis` | (internal) | What the resolver requested — **never printed** |

The `served_basis` / `pinned_basis` split is the core innovation. A figure that was requested on a standalone basis but actually served consolidated would be misleading if the page printed "standalone" — so the contract prints only what was served, and the requested basis is structurally dropped from the render path.

### 4. Verification layer
- **Whole-page inventory**: classifies every numeral on a rendered page as GOVERNED (bound to one claim with matching value, period, unit, and basis), WITHHELD (refused with a named reason), or UNBOUND (not traceable — the page cannot serve)
- **Numeral identity**: the printed number must exactly match the claim's value at its printed precision — no rounding drift, no sign drops
- **Mutation gates**: every rule has a deliberate-break test; a rule whose mutant survives is a defect

### 5. Rendering
- HTML tearsheets with a governed evidence ledger section (Section VI)
- The LLM writes prose about frozen fact packets — it sees the numbers but cannot modify them, compute new ones, or import outside facts
- Search is disabled at the API level; output is JSON-schema enforced

## Key design decisions

| Decision | Why |
|----------|-----|
| One canonical store per fact | Eliminates the "which source is right?" ambiguity — one cell, one value, one provenance |
| Versioned formulas with migration inventory | A formula change is a measured event, not a silent overwrite |
| served_basis only on the page | Prevents the most common research-report error: printing the basis you asked for, not the one you got |
| Basis mismatch ≠ value difference | Two figures on different bases are both correct on their own basis; calling that a "discrepancy" manufactures a false finding |
| Refusal over substitution | A missing standalone figure refuses with a named error; it never falls back to consolidated |
| Mutation testing as a first-class gate | A test suite that can't fail is not a test suite; every rule must have a mutant that proves its test catches the break |
