# Anka — Governance: The Basis Contract

## The problem it solves

When a research report says "ROE 16.0%", the reader assumes the company reported it. But 16.0% could be:
- the company's standalone filing
- the consolidated group
- a number the analyst computed from components
- a vendor transcription

Each is legitimate. Confusing them is not. Anka's basis contract makes the distinction structural rather than editorial.

## The two-field rule: served vs requested

Every claim carries two basis fields:

```
pinned_basis  = what the resolver asked for     → NEVER printed
served_basis  = what was actually delivered     → this is what prints
```

A figure that was requested standalone but served consolidated prints "consolidated group" — because that is what the reader is actually looking at. The pinned basis is structurally excluded from the render path (enforced by a build-failing mutant).

## The eight served-basis values

| Value | Scope prints as | Period goes to | When used |
|-------|----------------|----------------|-----------|
| STANDALONE | "standalone bank" | claim's period | The entity-only filing |
| CONSOLIDATED | "consolidated group" | claim's period | The group with subsidiaries |
| UNSPECIFIED | "issuer-stated, basis not disclosed" | claim's period | The company disclosed the figure but not which basis |
| MARKET | (empty) | close date | Market prices — no reporting basis |
| DERIVED | agreed operand basis | operands' windows | Computed from other claims |
| BRIDGE | (empty) | bridged period | The gap between two bases |
| EVENT | (empty) | event date | A filing/event, not a reporting figure |
| LADDER | (empty) | stated horizon | A valuation scenario slot |

## Refusal logic — named errors, never silent fallbacks

When the data cannot support a figure, the system refuses and names why:

```
BANK_STANDALONE_ABSENT
  → The company has no standalone filing for this metric.
    The figure is refused — it never falls back to consolidated.

ESTIMATE_OPERAND_BASIS_MISMATCH
  → A derived estimate requires all operands on one basis.
    Mixed-basis operands refuse; no "best guess" basis is assigned.

ARCHETYPE_INAPPLICABLE
  → This metric is undefined for this sector.
    ROCE is meaningless for a bank (no operating capital).
    19 such metrics are banned for financials, enforced by killed mutants.

SCENARIO_LADDER_DISORDERED
  → A bear/base/bull ladder where bear ≥ base.
    All three slots refuse — not just the bad leg.

VECTOR_DENOMINATOR_UNRESOLVED
  → A segment share whose total doesn't reconcile with its parts.
    No share prints; the amounts may show.
```

## Basis mismatch is not a value difference

When comparing a pilot figure against a gold reference:

```
Gold ROE 14.9% (consolidated)
Pilot ROE 16.0% (standalone)
```

Both are correct on their own basis. Calling this a "value difference" would send someone chasing a discrepancy that doesn't exist. Anka classifies it as `BASIS_MISMATCH` — its own outcome class, never `VALUE_DIFFERENCE`.

## Sector-specific rules (bank key tiers)

| Tier | Keys | Rule |
|------|------|------|
| Tier 1 — XBRL-derivable | GNPA, NNPA, cost-to-income, CET1, PPOP, advances, deposits, ROA, ROE | Strict standalone. Missing → refused |
| Tier 2 — deck-only | NIM, CASA, PCR, credit growth, yields, funding cost | Issuer-stated accepted, labelled UNSPECIFIED. The exchange XBRL taxonomy doesn't tag these |
| Tier 3 — group-level | PAT margin, group ROE, valuation | Consolidated, labelled |
| Banned | EBITDA margin, ROCE, DSO, etc. | ARCHETYPE_INAPPLICABLE for financials |

## Amendment history

The contract is versioned. Every change is recorded with its date, what changed, and why — with evidence links. Recent amendments:
- 2026-09-18: `pinned_basis`/`served_basis` split introduced (51 of 231 claims were serving via fallback while stamping the pinned basis)
- 2026-09-19: Eight-value basis set closed; MARKET ruled basis-neutral
- 2026-09-27: Non-issuer kinds (ESTIMATE, SCENARIO, EVENT) never take UNSPECIFIED — each with a cause-specific refusal
