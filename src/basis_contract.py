"""Basis contract — the core governance logic.

Every claim in a report carries a served_basis (what the figure is actually on)
and a pinned_basis (what the resolver asked for). Only the served_basis prints.
A pinned_basis that differs from the served_basis means the resolver's request
was not honoured — the figure is on a different basis than requested, and
printing the pinned basis would mislead the reader.

This module implements the status/confidence derivation, the basis resolution
rules, and the named refusal codes that prevent invalid figures from serving.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# ── Enums ─────────────────────────────────────────────────────────────────────

STATUSES = ("company_disclosed", "company_reported", "calculated", "market_derived", "estimate")
CONFIDENCES = ("low", "medium", "high")

BANK_TIER1_KEYS = frozenset({
    "gnpa_pct", "nnpa_pct", "cost_to_income_pct", "cet1_pct", "ppop_cr",
    "advances_cr", "deposits_cr", "roa_pct", "roe_pct",
})

BANK_BANNED_KEYS = frozenset({
    "ebitda_margin_pct", "ebit_margin_pct", "gross_margin_pct", "roce_pct",
    "fcf_conversion_pct", "net_debt_cr", "dso_days", "inventory_days",
})

_FILED_FORMULA_PREFIXES = ("statements_", "bank_", "xbrl_")


# ── Claim ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Claim:
    canonical_key: str
    value: float
    served_basis: str          # what this figure is actually on
    pinned_basis: str          # what the resolver requested (never printed)
    source_kind: str           # "own_computed" | "doc_extracted" | "screener_series"
    formula_id: str = ""
    is_bank: bool = False
    serve_route: str = "direct"  # "direct" | "issuer_stated_fallback" | ...


# ── Status and confidence ─────────────────────────────────────────────────────

def cell_status(source_kind: str, formula_id: str) -> Optional[tuple[str, str]]:
    """Derive (status, confidence) from provenance. None = unresolvable."""
    sk, fid = str(source_kind or ""), str(formula_id or "")
    if sk == "doc_extracted":
        return "company_disclosed", "medium"
    if sk == "own_computed" and fid.startswith(_FILED_FORMULA_PREFIXES):
        return "company_reported", "high"
    if sk == "own_computed":
        return "calculated", "medium"
    if sk == "screener_series":
        return "company_reported", "medium"
    return None  # producer unnamed → STATUS_UNRESOLVED


def weakest(*confidences: str) -> str:
    """A derivation is only as trustworthy as its weakest operand."""
    return min(confidences, key=CONFIDENCES.index)


# ── Basis resolution ──────────────────────────────────────────────────────────

def resolve_basis(claim: Claim) -> tuple[Optional[str], Optional[str]]:
    """Resolve the printable basis for a claim. Returns (basis, refusal_code).

    Only the served_basis is printable. If the pinned basis differs from the
    served basis, that is a fact about the resolver's request, not about the
    figure — and it never changes what prints.
    """
    if claim.is_bank:
        return _resolve_bank_basis(claim)
    return claim.served_basis, None


def _resolve_bank_basis(claim: Claim) -> tuple[Optional[str], Optional[str]]:
    if claim.canonical_key in BANK_BANNED_KEYS:
        return None, "ARCHETYPE_INAPPLICABLE"
    if claim.canonical_key in BANK_TIER1_KEYS:
        if claim.served_basis != "STANDALONE":
            return None, "BANK_STANDALONE_ABSENT"
    return claim.served_basis, None


# ── Rendering ─────────────────────────────────────────────────────────────────

BASIS_LABELS = {
    "STANDALONE": "standalone",
    "CONSOLIDATED": "consolidated group",
    "UNSPECIFIED": "as stated by the issuer (basis not specified)",
    "MARKET": "market price",
    "DERIVED": "derived",
}


def basis_label(claim: Claim) -> str:
    """The basis line a reader sees. Built from the SERVED basis only.

    The pinned basis is what the resolver asked for. When a fallback route
    served a different basis, printing the pinned one would assert a basis the
    figure is not on. A refused claim prints its refusal code, never a number.
    """
    basis, refusal = resolve_basis(claim)
    if refusal:
        return f"withheld ({refusal})"
    return BASIS_LABELS.get(basis, str(basis).lower())


# ── Comparison ────────────────────────────────────────────────────────────────

def compare_claims(pilot: Claim, reference: Claim) -> tuple[str, str]:
    """Compare two claims. Returns (classification, detail).

    A basis mismatch is its own class — never a value difference.
    Both figures can be correct on their own basis.
    """
    if pilot.canonical_key != reference.canonical_key:
        return "KEY_MISMATCH", f"{pilot.canonical_key} vs {reference.canonical_key}"
    if pilot.served_basis != reference.served_basis:
        return "BASIS_MISMATCH", (
            f"reference {reference.served_basis} vs pilot {pilot.served_basis}"
        )
    if abs(pilot.value - reference.value) > max(0.05, 0.001 * abs(reference.value)):
        return "VALUE_DIFFERENCE", f"{pilot.value} vs {reference.value}"
    return "MATCH", f"{pilot.value} == {reference.value}"


# ── Derivation ────────────────────────────────────────────────────────────────

def derive_operand_basis(operands: list[dict]) -> tuple[Optional[str], Optional[str]]:
    """The single basis for a derived claim from its operand set.

    Rules:
    - A MARKET leg is basis-neutral (carries a price, not a reporting basis).
    - Every non-MARKET operand must declare a basis; unset = no basis = refusal.
    - All non-MARKET bases must agree.
    - A set resolving to UNSPECIFIED is rejected for non-issuer claims.
    """
    bases = []
    for op in operands:
        b = op.get("served_basis")
        if b == "MARKET":
            continue
        bases.append(b)

    if not bases:
        return None, "ESTIMATE_OPERAND_BASIS_MISMATCH: no non-MARKET operand basis"

    first = bases[0]
    other = next((b for b in bases if b != first), None)
    if other is not None:
        return None, f"ESTIMATE_OPERAND_BASIS_MISMATCH: {first} vs {other}"
    if first is None:
        return None, "ESTIMATE_OPERAND_BASIS_MISMATCH: no lawful basis on operand"
    if first == "UNSPECIFIED":
        return None, "ESTIMATE_UNSPECIFIED_REJECTED"
    return first, None
