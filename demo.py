"""A 30-second walk through the basis contract. Standard library only.

    python demo.py

Every figure below is illustrative. The companies are fictional; the rules are
the ones the production system enforces on real exchange filings.
"""
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from basis_contract import (  # noqa: E402
    Claim, basis_label, cell_status, compare_claims, derive_operand_basis, weakest,
)


def rule(title):
    print(f"\n{title}\n" + "-" * len(title))


print("ANKA basis contract: every number knows what it is, where it came from,")
print("and which accounting basis it is on. When it cannot know, it refuses by name.")

rule("1. Two correct numbers that disagree")
ours = Claim("roe_pct", 16.0, "STANDALONE", "STANDALONE", "own_computed", "statements_roe")
vendor = Claim("roe_pct", 14.9, "CONSOLIDATED", "CONSOLIDATED", "screener_series")
cls, detail = compare_claims(ours, vendor)
print(f"Company A ROE: ours 16.0% vs a data vendor's 14.9%")
naive, _ = compare_claims(ours, replace(vendor, served_basis=ours.served_basis))
print(f"  basis-blind  -> {naive} (someone must be wrong)")
print(f"  basis-aware  -> {cls}: {detail}")
print("  Both are right. One is the parent company, one is the group.")

rule("2. The resolver asked for one basis; a fallback served another")
c = Claim("revenue_growth_pct", 12.4, served_basis="CONSOLIDATED", pinned_basis="STANDALONE",
          source_kind="doc_extracted", serve_route="issuer_stated_fallback")
print("Company A revenue growth 12.4%  (standalone requested, not filed; fallback used)")
print(f"  label from pinned basis -> '{c.pinned_basis.lower()}'      <- false: not what the figure is on")
print(f"  label from served basis -> '{basis_label(c)}'")

rule("3. Refusing by name instead of guessing")
cases = [
    ("Bank B ROA 2.1%, only a group figure exists",
     Claim("roa_pct", 2.1, "CONSOLIDATED", "STANDALONE", "own_computed", "statements_roa", is_bank=True)),
    ("Bank B ROCE 15.2%",
     Claim("roce_pct", 15.2, "STANDALONE", "STANDALONE", "own_computed", "statements_roce", is_bank=True)),
    ("Bank B ROA 1.8%, standalone filing",
     Claim("roa_pct", 1.8, "STANDALONE", "STANDALONE", "own_computed", "statements_roa", is_bank=True)),
]
for text, claim in cases:
    print(f"  {text:<44} -> {basis_label(claim)}")

rule("4. A derived estimate inherits its operands' basis, or refuses")
for text, ops in [
    ("price (MARKET) / group EPS", [{"served_basis": "MARKET"}, {"served_basis": "CONSOLIDATED"}]),
    ("group EPS vs parent book value", [{"served_basis": "CONSOLIDATED"}, {"served_basis": "STANDALONE"}]),
    ("price / EPS with no basis recorded", [{"served_basis": "MARKET"}, {"served_basis": None}]),
]:
    basis, refusal = derive_operand_basis(ops)
    print(f"  {text:<36} -> {basis or refusal}")

rule("5. Provenance sets status and confidence; the weakest input wins")
for kind, fid in [("own_computed", "statements_roe"), ("doc_extracted", ""),
                  ("own_computed", "analyst_adjusted_margin"), ("unknown_feed", "")]:
    print(f"  {kind:<14} {fid or '-':<24} -> {cell_status(kind, fid) or 'STATUS_UNRESOLVED (refused)'}")
print(f"  derived from (high, medium, high) inputs  -> confidence '{weakest('high', 'medium', 'high')}'")
