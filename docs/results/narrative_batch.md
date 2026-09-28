# AI Narrative Batch — Results

## What was measured

94 full reports (8 sections each) generated for the top-100 READY companies, using a governed LLM writing layer that receives frozen fact packets and cannot modify, compute, or import numbers.

## Results

| Metric | Value |
|--------|-------|
| Reports completed | 94 of 94 |
| Sections generated | 752 |
| Sections clean on first draw | 752 (100%) |
| Retries needed | 0 |
| Total spend | $6.63 |
| **Cost per report** | **$0.077** |
| Stop rules triggered | 0 |

## What "clean" means

Every section passed the numeral-identity gate: every number printed by the LLM exactly matched a packet figure at its printed precision. Specifically:

- No computed numbers (the model cannot do arithmetic on packet values)
- No outside facts (search is disabled at the API level)
- No sign drops (negative figures keep their minus sign — verified by adversarial testing)
- No comma-formatting artifacts (numerals are comma-stripped before comparison)
- No date-component confusion (hyphenated date parts are not treated as signed values)

## How the adversarial testing worked

Before the clean run, 8 earlier attempts surfaced and cured real defects through the stop rules:

| Attempt | Defect found | Cure |
|---------|-------------|------|
| 1 | Rate-limiting from parallel calls | Sequential execution with backoff |
| 2 | Full-precision floats in packets → 15-decimal prose | Packets frozen at display precision |
| 3 | Prose-counting integers flagged as data | Small integers ≤12 allowed as counting |
| 4 | Comma-formatted numerals split by regex | Comma-stripping before numeral extraction |
| 5 | **Sign drops on loss-making companies** (PE −172.3 printed as 172.3) | Sign-preservation prompt rule + sign-capturing gate |
| 6 | Hyphenated dates parsed as signed values | Date-component allowance |
| 7-8 | Edge cases in the gate | Fixed and re-run |

Each attempt was a full re-run (no mixing of old and new outputs), and every stop was honored before the final clean run.

## The packet discipline

Each name receives a **frozen evidence packet** — deterministic JSON with:
- 11 core ratios at display precision (1dp for percentages, 1dp for multiples, 0dp for market cap)
- Valuation metrics (PE, EV/EBITDA, P/B, dividend yield)
- Latest close price with date
- Industry classification and peer tier

The LLM sees only these fields. It cannot query databases, browse the web, or access any data outside the packet. The packet is SHA256-hashed and included in the manifest for reproducibility.
