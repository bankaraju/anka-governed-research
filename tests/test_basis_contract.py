"""Tests for the basis contract. Run with: pytest -v"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from basis_contract import (  # noqa: E402
    Claim, basis_label, cell_status, weakest, resolve_basis, compare_claims,
    derive_operand_basis,
)


# ── Status derivation ─────────────────────────────────────────────────────────

def test_doc_extracted_is_company_disclosed():
    assert cell_status("doc_extracted", "") == ("company_disclosed", "medium")

def test_filed_formula_is_company_reported_high():
    result = cell_status("own_computed", "statements_promote_roe_pct")
    assert result == ("company_reported", "high")

def test_own_computed_unfiled_is_calculated():
    assert cell_status("own_computed", "my_custom_formula") == ("calculated", "medium")

def test_screener_series_is_company_reported_medium():
    assert cell_status("screener_series", "") == ("company_reported", "medium")

def test_unnamed_producer_returns_none():
    """An unnamed producer is unresolvable — never guessed."""
    assert cell_status("mystery_source", "x") is None

def test_weakest_operand_governs():
    assert weakest("high", "low", "medium") == "low"
    assert weakest("high", "high") == "high"


# ── Bank basis rules ──────────────────────────────────────────────────────────

def test_bank_tier1_standalone_serves():
    c = Claim("roa_pct", 1.8, "STANDALONE", "STANDALONE", "own_computed", "statements_roa", is_bank=True)
    basis, refusal = resolve_basis(c)
    assert basis == "STANDALONE" and refusal is None

def test_bank_tier1_consolidated_refuses():
    """A Tier 1 bank key on consolidated basis must refuse — never silently substitute."""
    c = Claim("roa_pct", 2.1, "CONSOLIDATED", "STANDALONE", "own_computed", "statements_roa", is_bank=True)
    basis, refusal = resolve_basis(c)
    assert basis is None and refusal == "BANK_STANDALONE_ABSENT"

def test_bank_banned_key_refuses():
    """ROCE is undefined for a bank — banned by archetype."""
    c = Claim("roce_pct", 15.2, "STANDALONE", "STANDALONE", "own_computed", "statements_roce", is_bank=True)
    basis, refusal = resolve_basis(c)
    assert basis is None and refusal == "ARCHETYPE_INAPPLICABLE"

def test_bank_non_tier1_key_serves_its_own_basis():
    """Only Tier 1 bank keys demand standalone; other keys serve what they are on."""
    c = Claim("credit_growth_pct", 14.0, "CONSOLIDATED", "CONSOLIDATED", "doc_extracted", is_bank=True)
    assert resolve_basis(c) == ("CONSOLIDATED", None)

def test_non_bank_serves_consolidated_even_for_a_bank_tier1_key_name():
    """The bank rules apply to banks only."""
    c = Claim("roa_pct", 7.5, "CONSOLIDATED", "STANDALONE", "own_computed", "statements_roa")
    assert resolve_basis(c) == ("CONSOLIDATED", None)


def test_unknown_served_basis_refuses():
    """No basis, or one outside the closed set, has no lawful basis to print."""
    for bad in (None, "", "CONSOLIDATEDD", "GROUP"):
        c = Claim("roe_pct", 16.0, bad, "STANDALONE", "own_computed")
        assert resolve_basis(c) == (None, "BASIS_UNRESOLVED")
        assert basis_label(c) == "withheld (BASIS_UNRESOLVED)"

def test_every_lawful_basis_serves():
    """Keep-side control: each of the eight lawful bases is accepted as served."""
    for b in ("STANDALONE", "CONSOLIDATED", "UNSPECIFIED", "MARKET",
              "DERIVED", "BRIDGE", "EVENT", "LADDER"):
        c = Claim("x_key", 1.0, b, b, "own_computed")
        assert resolve_basis(c) == (b, None)


# ── Rendering: only the served basis reaches the page ─────────────────────────

def test_fallback_prints_served_basis_not_pinned():
    """The resolver asked for standalone; a fallback served consolidated.
    The page must say consolidated, because that is what the number is on."""
    c = Claim("revenue_growth_pct", 12.4, "CONSOLIDATED", "STANDALONE", "doc_extracted",
              serve_route="issuer_stated_fallback")
    assert basis_label(c) == "consolidated group"
    assert "standalone" not in basis_label(c)

def test_refused_claim_prints_its_refusal_not_a_basis():
    c = Claim("roce_pct", 15.2, "STANDALONE", "STANDALONE", "own_computed", is_bank=True)
    assert basis_label(c) == "withheld (ARCHETYPE_INAPPLICABLE)"

def test_unspecified_basis_is_labelled_as_issuer_stated():
    c = Claim("order_book_cr", 4100.0, "UNSPECIFIED", "STANDALONE", "doc_extracted")
    assert basis_label(c) == "as stated by the issuer (basis not specified)"


# ── Basis-aware comparison ────────────────────────────────────────────────────

def test_same_basis_value_match():
    a = Claim("roe_pct", 16.0, "STANDALONE", "STANDALONE", "own_computed")
    b = Claim("roe_pct", 16.0, "STANDALONE", "STANDALONE", "own_computed")
    cls, _ = compare_claims(a, b)
    assert cls == "MATCH"

def test_same_basis_value_difference():
    a = Claim("roe_pct", 16.0, "STANDALONE", "STANDALONE", "own_computed")
    b = Claim("roe_pct", 14.9, "STANDALONE", "STANDALONE", "own_computed")
    cls, _ = compare_claims(a, b)
    assert cls == "VALUE_DIFFERENCE"

def test_small_rounding_difference_is_a_match():
    a = Claim("roe_pct", 16.0, "STANDALONE", "STANDALONE", "own_computed")
    b = Claim("roe_pct", 16.04, "STANDALONE", "STANDALONE", "own_computed")
    assert compare_claims(a, b)[0] == "MATCH"

def test_different_keys_are_never_compared_as_values():
    a = Claim("roe_pct", 16.0, "STANDALONE", "STANDALONE", "own_computed")
    b = Claim("roa_pct", 16.0, "STANDALONE", "STANDALONE", "own_computed")
    assert compare_claims(a, b)[0] == "KEY_MISMATCH"

def test_different_basis_is_basis_mismatch_not_value_difference():
    """The core insight: two correct figures on different bases are not a value error."""
    pilot = Claim("roe_pct", 16.0, "STANDALONE", "STANDALONE", "own_computed")
    reference = Claim("roe_pct", 14.9, "CONSOLIDATED", "CONSOLIDATED", "own_computed")
    cls, detail = compare_claims(pilot, reference)
    assert cls == "BASIS_MISMATCH"
    assert cls != "VALUE_DIFFERENCE"
    assert "STANDALONE" in detail and "CONSOLIDATED" in detail


def test_different_period_is_period_mismatch_not_value_difference():
    """FY24 against FY25 is two different facts, not a discrepancy."""
    a = Claim("roe_pct", 16.0, "STANDALONE", "STANDALONE", "own_computed", period_end="2025-03-31")
    b = Claim("roe_pct", 16.0, "STANDALONE", "STANDALONE", "own_computed", period_end="2024-03-31")
    cls, detail = compare_claims(a, b)
    assert cls == "PERIOD_MISMATCH"
    assert "2024-03-31" in detail and "2025-03-31" in detail


# ── Operand basis derivation ──────────────────────────────────────────────────

def test_clean_pair_resolves():
    ops = [{"served_basis": "MARKET"}, {"served_basis": "CONSOLIDATED"}]
    basis, refusal = derive_operand_basis(ops)
    assert basis == "CONSOLIDATED" and refusal is None

def test_all_market_refuses():
    """A set of price legs only has no basis to serve — must refuse."""
    ops = [{"served_basis": "MARKET"}, {"served_basis": "MARKET"}]
    basis, refusal = derive_operand_basis(ops)
    assert basis is None and "no non-MARKET" in refusal

def test_disagreeing_operands_refuse():
    ops = [{"served_basis": "STANDALONE"}, {"served_basis": "CONSOLIDATED"}]
    basis, refusal = derive_operand_basis(ops)
    assert basis is None and "STANDALONE vs CONSOLIDATED" in refusal

def test_unset_operand_refuses():
    """An operand with no basis is refused — never silently defaulted."""
    ops = [{"served_basis": "MARKET"}, {"served_basis": None}]
    basis, refusal = derive_operand_basis(ops)
    assert basis is None and "no lawful basis" in refusal

def test_all_unspecified_rejected():
    """UNSPECIFIED asserts the issuer stated the figure — false for a derived estimate."""
    ops = [{"served_basis": "MARKET"}, {"served_basis": "UNSPECIFIED"}]
    basis, refusal = derive_operand_basis(ops)
    assert basis is None and "ESTIMATE_UNSPECIFIED_REJECTED" in refusal
