# Anka — Technical Architecture

## Stack

| Layer | Technology |
|-------|-----------|
| Data stores | DuckDB (columnar, single-writer, read-only consumers) |
| XBRL parsing | Python (arelle-based), BSE/NSE filing ingestion |
| Formula engine | Python, versioned per snapshot, replay-capable |
| Report rendering | Python → HTML (Jinja-free, deterministic) |
| Prose generation | LLM (Perplexity Sonar), frozen-fact packets, JSON-schema enforced |
| Testing | pytest + custom mutation-testing framework (`mutant_kill.py`) |
| Verification | Whole-page inventory, numeral-identity gates, SHA256 checksums |

## Codebase scale

| Metric | Count |
|--------|-------|
| Python files (pipeline) | ~3,200 |
| Test files | ~1,600 |
| Commits | 10,600+ |
| Governed claim kinds | 6 (CELL, DERIVED, ESTIMATE, SCENARIO, EVENT, VECTOR) |
| Refusal codes | Named, one per failure class |
| Basis contract rules | 8 served-basis values, tier rules, amendment history |

## Key modules

| Module | Purpose |
|--------|---------|
| `pipeline/statements/` | XBRL parsing, filing enumeration, ratio computation |
| `pipeline/integrity/` | Formula versioning, migration inventory, scenario contract audit |
| `pipeline/terminal/nlo_pilot.py` | Claim construction, basis resolution, refusal logic |
| `pipeline/terminal/nlo_estimate.py` | ESTIMATE + SCENARIO claim kinds (forward P/E, valuation ladders) |
| `pipeline/terminal/nlo_s2_inventory.py` | Whole-page governed inventory (numeral-by-numeral) |
| `pipeline/terminal/dispatch_audit.py` | Pre-release page audit (visible-text debris, provenance leaks) |
| `pipeline/terminal/write_staging.py` | Staged writes with hard-fail on live-default paths |
| `pipeline/infra/mutant_kill.py` | Mutation-testing authority (KILLED = named test failed, not just rc≠0) |

## The mutation-testing framework

```python
# pipeline/infra/mutant_kill.py — the one kill authority

KILLED      rc == 1 AND at least one of the harness's own named tests failed
SURVIVED    the mutation ran against a working suite and nothing named it
BROKEN_RUN  the suite did not execute — NOT a kill, and not a survivor
```

A mutant is killed only by a **named test that ran and failed** — never by a non-zero exit code alone. This prevents the false-pass where a broken harness reports a perfect mutation score.

## Determinism guarantees

- CLI tools run twice with different `PYTHONHASHSEED` values → outputs must be byte-identical
- Page rebuilds from manifests → byte-identical to the original
- Formula replays at historical commits → deterministic per commit

## Data pipeline safety

| Guard | Mechanism |
|-------|-----------|
| Staging root | Hard-fails on the live default; must explicitly override |
| Read-only connections | `connect(path, read_only=True)` for all consumer queries |
| Store writes | Single-writer, transactional, with pre-write backup and post-write verification |
| Rollback | Rowid-level maps, tested revert paths, SHA256 receipt on every rollback |
