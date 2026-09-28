# Repository structure

**What is here and what is not.** This repository contains the basis contract, the core rule set
of the Anka system, with its tests, a mutation harness, a demo and an example output page. The full
production system (filing ingestion, data stores, report writer) lives in a private repository and
is described, not included, in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Folders and files

| Path | What it does |
|---|---|
| `src/basis_contract.py` | The contract. Every claim carries a *served* basis (what the figure is on) and a *pinned* basis (what was requested); only the served basis prints. Derives status and confidence from provenance, resolves the printable basis, compares two claims, derives the basis of a computed figure, and returns a named refusal code when a figure has no lawful basis. Standard library only. |
| `tests/test_basis_contract.py` | 24 tests, one or more per rule, including the refusal cases. |
| `tools/mutate.py` | Mutation harness: 19 mutants, each breaking one rule in a temporary copy. A mutant counts as killed only if pytest exits 1 *and* a named test fails. |
| `demo.py` | A 30-second terminal walk through five rules on fictional companies. |
| `render_example.py` | Renders `docs/example.html`, a one-page brief for a fictional company in which every cell is decided by the contract. `--check` fails if the committed page is stale. |
| `docs/` | `OVERVIEW.md` and `ARCHITECTURE.md` (production system), `GOVERNANCE.md` (the contract's rules in prose), `results/` (measured results from the production system), `example.html` (served on GitHub Pages). |
| `flowcv/` | Write-up of a separate trading-strategy project, including why its headline figure was withdrawn. No code. |
| `DESIGN.md` | Why a claim carries two bases, in first person. |

## How the pieces connect

1. `src/basis_contract.py` states the rules.
2. `tests/` proves each rule holds on known inputs.
3. `tools/mutate.py` proves each test can fail: every rule is broken on purpose, and a named test
   must catch it. A rule no test can catch is reported as unenforced.
4. `demo.py` and `render_example.py` exercise the same functions a reader would see in output.
5. CI (`.github/workflows/ci.yml`) runs all of it on Python 3.10–3.12: tests, the demo, the
   example-page freshness check and the mutation harness. A change that breaks a rule, weakens a
   test or makes the example page drift fails the build.
