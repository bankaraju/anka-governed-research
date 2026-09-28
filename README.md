# Anka — governed equity research

[![ci](https://github.com/bankaraju/anka-governed-research/actions/workflows/ci.yml/badge.svg)](https://github.com/bankaraju/anka-governed-research/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
![dependencies](https://img.shields.io/badge/runtime%20deps-none-brightgreen)
![license](https://img.shields.io/badge/license-MIT-lightgrey)

A system for producing equity research where every number is traceable to its source filing, computation method, and reporting basis. The core problem it solves: conventional report generation cannot answer *"where did this number come from?"* Anka answers it structurally, and when it cannot answer, it refuses to print the number and says why.

## Try it in 30 seconds

No dependencies beyond the Python standard library:

```bash
git clone https://github.com/bankaraju/anka-governed-research && cd anka-governed-research
python demo.py
```

```text
ANKA basis contract: every number knows what it is, where it came from,
and which accounting basis it is on. When it cannot know, it refuses by name.

1. Two correct numbers that disagree
------------------------------------
Company A ROE: ours 16.0% vs a data vendor's 14.9%
  basis-blind  -> VALUE_DIFFERENCE (someone must be wrong)
  basis-aware  -> BASIS_MISMATCH: reference CONSOLIDATED vs pilot STANDALONE
  Both are right. One is the parent company, one is the group.

2. The resolver asked for one basis; a fallback served another
--------------------------------------------------------------
Company A revenue growth 12.4%  (standalone requested, not filed; fallback used)
  label from pinned basis -> 'standalone'      <- false: not what the figure is on
  label from served basis -> 'consolidated group'

3. Refusing by name instead of guessing
---------------------------------------
  Bank B ROA 2.1%, only a group figure exists  -> withheld (BANK_STANDALONE_ABSENT)
  Bank B ROCE 15.2%                            -> withheld (ARCHETYPE_INAPPLICABLE)
  Bank B ROA 1.8%, standalone filing           -> standalone

4. A derived estimate inherits its operands' basis, or refuses
--------------------------------------------------------------
  price (MARKET) / group EPS           -> CONSOLIDATED
  group EPS vs parent book value       -> ESTIMATE_OPERAND_BASIS_MISMATCH: CONSOLIDATED vs STANDALONE
  price / EPS with no basis recorded   -> ESTIMATE_OPERAND_BASIS_MISMATCH: no lawful basis on operand

5. Provenance sets status and confidence; the weakest input wins
----------------------------------------------------------------
  own_computed   statements_roe           -> ('company_reported', 'high')
  doc_extracted  -                        -> ('company_disclosed', 'medium')
  own_computed   analyst_adjusted_margin  -> ('calculated', 'medium')
  unknown_feed   -                        -> STATUS_UNRESOLVED (refused)
  derived from (high, medium, high) inputs  -> confidence 'medium'
```

Then check that the rules are actually enforced:

```bash
pip install pytest
pytest                   # 24 tests
python tools/mutate.py   # breaks each rule on purpose; every break must be caught by a named test
```

`tools/mutate.py` reports **19/19 mutants killed**. CI runs all three on every push.

## The core idea

Every claim carries four governed attributes:

| Field | Values | Purpose |
|-------|--------|---------|
| `status` | company_disclosed, company_reported, calculated, market_derived, estimate | Who produced the number |
| `confidence` | high, medium, low | Set by the weakest input |
| `served_basis` | STANDALONE, CONSOLIDATED, UNSPECIFIED, MARKET, DERIVED, EVENT, LADDER | What basis the figure is actually on. **This is what prints.** |
| `pinned_basis` | (internal) | What the resolver asked for. Never printed. |

The `served_basis` / `pinned_basis` split exists because of a real failure. In a 231-claim pilot, **51 claims had been served through a fallback route while still stamped with the basis that was requested.** Printing that stamp would have told readers the numbers were on a basis they were not on. The story is in [`DESIGN.md`](DESIGN.md).

When the data cannot support a figure, the system refuses by name:

```
BANK_STANDALONE_ABSENT           No standalone filing exists; never falls back to the group figure
ARCHETYPE_INAPPLICABLE           Metric undefined for this kind of business (e.g. ROCE for a bank)
ESTIMATE_OPERAND_BASIS_MISMATCH  A derived estimate whose inputs sit on different bases
SCENARIO_LADDER_DISORDERED       Bear case >= base case; every slot refuses
VECTOR_DENOMINATOR_UNRESOLVED    Segment parts do not reconcile to the total; no share prints
```

## Verification

A rule nobody can break is not tested. Each rule gets a fail-side mutant, a deliberate break that a **named** test must catch. A kill requires pytest exit code 1 *and* a named failing test, never the exit code alone: pytest exits 4 or 5 when nothing ran, and a harness that counts those as kills is testing nothing.

| Contract | This repo | Production system |
|----------|-----------|-------------------|
| Basis contract | 24 tests · **19/19 mutants killed** ([`tools/mutate.py`](tools/mutate.py)) | 33/33 fail-side mutants killed |
| Vector (segment / geography) | — | 24/24 fail-side mutants killed |

Detail: [`docs/results/mutant_verification.md`](docs/results/mutant_verification.md)

## Production results

This repository holds the core contract. The full system, which ingests exchange XBRL filings for the 1,000 largest listed companies in its market and writes reports with an LLM, lives in a private repository. Its measured results:

| Metric | Result | Evidence |
|--------|--------|----------|
| Companies with enough filed data to report on | 927 / 1,000 (criterion: ≥4 parsed quarterly filings) | [`census_summary.md`](docs/results/census_summary.md) |
| LLM-written reports whose every numeral matched a governed figure | 94 reports · 752 sections · 752 clean on first draw | [`narrative_batch.md`](docs/results/narrative_batch.md) |
| Model spend for that batch | $6.63 total · **$0.077 per report** | [`narrative_batch.md`](docs/results/narrative_batch.md) |

The LLM only ever sees frozen fact packets. It cannot compute, cannot search, and must reproduce every number at the precision it was given. Earlier runs caught it dropping the minus sign on a loss-making company's P/E; the gate that caught that is now part of the contract.

## Architecture

```
XBRL filings ──► parse ──► canonical store ──► formula layer ──► claim layer ──► verify ──► render
                          (one value per      (versioned,       (status,         (numeral    (HTML with
                           cell, period,       tested)           confidence,      identity,   evidence
                           basis)                                basis)           mutants)    ledger)
Annual reports, decks ──► extraction ──────────────────────────►
```

More: [`docs/OVERVIEW.md`](docs/OVERVIEW.md) · [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · [`docs/GOVERNANCE.md`](docs/GOVERNANCE.md)

**Portability.** The production system reads one exchange's XBRL filings. The claim model is not tied to them: served basis, named refusals and basis-aware comparison apply unchanged to SEC EDGAR 10-K/10-Q filings, IFRS reporters, or any source where one entity files more than one set of accounts.

## Second project: FlowCV

A systematic long/short strategy on single-stock futures, with a regime gate built from global ETF features. Its write-up is deliberately candid. It gives a raw backtest of +0.66% per cycle gross over 216 overlapping cycles, and a first month of live paper trading that came in at −0.84% per position. It explains why I withdrew the strategy's +1.36% headline figure: one exit rule used hindsight. See [`flowcv/README.md`](flowcv/README.md).

## How this was built

The design, engineering decisions, and all production code are mine. I used a multi-model agent flow throughout: local models via Ollama (Gemma, GLM 5.3, others), Perplexity Sonar API, and Claude Code as a coding agent. Different models handled different tasks — local models for fast iteration and offline work, Sonar for research and verification, Claude Code for structured code generation. The mutation harness, the `pinned_basis`/`served_basis` split, and the refusal logic all emerged from that process and are described in [`DESIGN.md`](DESIGN.md).

## Repository

```
demo.py                     30-second walkthrough (stdlib only)
DESIGN.md                   Why a claim carries two bases; what failed first
src/basis_contract.py       The contract: status, confidence, basis resolution, refusals, comparison
tests/                      24 tests
tools/mutate.py             Mutation harness (kill = named test failure)
docs/                       Overview, architecture, governance, production results
flowcv/README.md            The FlowCV strategy and its record
.github/workflows/ci.yml    Tests + demo + mutation harness on Python 3.10–3.12
```

## License

MIT
