"""Render a one-page example brief for a fictional company. Standard library only.

    python render_example.py            # writes docs/example.html
    python render_example.py --check    # exits 1 if docs/example.html is stale

Every cell on the page is decided by src/basis_contract.py: the basis line comes
from basis_label (served basis only), status and confidence from cell_status,
derived multiples from derive_operand_basis and weakest, and the peer check from
compare_claims. The company and its figures are fictional.
"""
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from basis_contract import (  # noqa: E402
    Claim, basis_label, cell_status, compare_claims, derive_operand_basis, weakest,
)

OUT = ROOT / "docs" / "example.html"
COMPANY = "Northwind Components Ltd"
PERIOD = "FY2026 (year to 31 March 2026)"

# (label, claim, unit, source note). All figures fictional and mutually consistent.
ROWS = [
    ("Revenue", Claim("revenue_cr", 4820.0, "CONSOLIDATED", "CONSOLIDATED", "own_computed",
                      "statements_revenue"), "₹ cr", "Annual filing, income statement"),
    ("Revenue growth", Claim("revenue_growth_pct", 11.6, "CONSOLIDATED", "CONSOLIDATED",
                             "own_computed", "statements_revenue_growth"), "%",
     "Computed from two filed years"),
    ("EBITDA margin", Claim("ebitda_margin_pct", 18.4, "CONSOLIDATED", "CONSOLIDATED",
                            "own_computed", "statements_ebitda_margin"), "%",
     "Computed from filed income statement"),
    ("Net profit margin", Claim("pat_margin_pct", 9.7, "CONSOLIDATED", "CONSOLIDATED",
                                "own_computed", "statements_pat_margin"), "%",
     "Computed from filed income statement"),
    ("Return on equity (group)", Claim("roe_pct", 14.9, "CONSOLIDATED", "CONSOLIDATED",
                                       "own_computed", "statements_roe"), "%",
     "Group profit over group equity"),
    ("Return on equity (parent company)", Claim("roe_pct", 16.0, "STANDALONE", "STANDALONE",
                                                "own_computed", "statements_roe"), "%",
     "Parent profit over parent equity"),
    ("Net debt / EBITDA", Claim("net_debt_to_ebitda_x", 0.8, "CONSOLIDATED", "CONSOLIDATED",
                                "own_computed", "statements_net_debt_to_ebitda"), "x",
     "Computed from filed balance sheet"),
    ("Order book", Claim("order_book_cr", 6100.0, "CONSOLIDATED", "CONSOLIDATED",
                         "doc_extracted"), "₹ cr", "Stated in investor presentation"),
    ("Revenue growth guided for FY2027", Claim("guided_revenue_growth_pct", 13.0, "UNSPECIFIED",
                                               "CONSOLIDATED", "doc_extracted",
                                               serve_route="issuer_stated_fallback"), "%",
     "Management commentary (12-14% range, midpoint shown)"),
]

PRICE = 1240.0             # fictional share price, a market figure
EPS_CONSOLIDATED = 51.0    # fictional group earnings per share


def fmt(value, unit):
    if unit == "₹ cr":
        return f"₹{value:,.0f} cr"
    if unit == "x":
        return f"{value:.1f}x"
    return f"{value:.1f}%"


def claim_row(label, claim, unit, source):
    status, confidence = cell_status(claim.source_kind, claim.formula_id)
    return (label, fmt(claim.value, unit), basis_label(claim), status.replace("_", " "),
            confidence, source)


def derived_pe_row():
    basis, refusal = derive_operand_basis(
        [{"served_basis": "MARKET"}, {"served_basis": "CONSOLIDATED"}])
    assert refusal is None, refusal
    eps_conf = cell_status("own_computed", "statements_eps")[1]
    conf = weakest("high", eps_conf)  # market price is observed, so high
    label = basis_label(Claim("pe_x", 0.0, basis, basis, "own_computed"))
    return ("Price / earnings", f"{PRICE / EPS_CONSOLIDATED:.1f}x", label, "market derived",
            conf, f"₹{PRICE:,.0f} share price / ₹{EPS_CONSOLIDATED:.1f} group EPS")


def peer_check():
    ours = next(c for label, c, _, _ in ROWS if label.startswith("Return on equity (parent"))
    vendor = Claim("roe_pct", 14.9, "CONSOLIDATED", "CONSOLIDATED", "screener_series")
    return compare_claims(ours, vendor)


CSS = """
:root{--bg:#fbfaf7;--fg:#1d1d1b;--mut:#6b6b66;--rule:#dcd9d0;--acc:#1f3a5f;--chip:#eef1f5;--warn:#fff6e0}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ecebe6;--mut:#a3a29b;--rule:#34332f;--acc:#9cc0ea;--chip:#23272d;--warn:#2d2616}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 Georgia,'Times New Roman',serif}
main{max-width:900px;margin:0 auto;padding:32px 16px 48px}
.kicker{font:12px/1.4 system-ui,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--mut)}
h1{font-size:32px;margin:6px 0 4px}h2{font:600 13px/1.4 system-ui,sans-serif;letter-spacing:.14em;text-transform:uppercase;margin:36px 0 10px;padding-bottom:6px;border-bottom:2px solid var(--fg)}
.banner{background:var(--warn);border:1px solid var(--rule);padding:10px 14px;font:13px/1.5 system-ui,sans-serif;margin:18px 0}
.wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;font:14px/1.45 system-ui,sans-serif}
th{text-align:left;font-weight:600;color:var(--mut);font-size:12px;letter-spacing:.06em;text-transform:uppercase;border-bottom:1px solid var(--rule);padding:8px 8px 6px}
td{border-bottom:1px solid var(--rule);padding:9px 8px;vertical-align:top}td.num{text-align:right;font-variant-numeric:tabular-nums;font-weight:600;white-space:nowrap}
.chip{display:inline-block;background:var(--chip);padding:1px 8px;border-radius:10px;font-size:12px;white-space:nowrap}
.src{color:var(--mut);font-size:13px}p,li{max-width:70ch}code{font-size:13px}
.call{border-left:3px solid var(--acc);padding:4px 0 4px 14px;margin:14px 0}
footer{margin-top:40px;color:var(--mut);font:12px/1.5 system-ui,sans-serif}
"""


def render():
    rows = [claim_row(*r) for r in ROWS] + [derived_pe_row()]
    cls, detail = peer_check()
    esc = html.escape
    body = []
    for label, value, basis, status, conf, src in rows:
        body.append(
            f"<tr><td>{esc(label)}</td><td class=num>{esc(value)}</td>"
            f"<td><span class=chip>{esc(basis)}</span></td><td>{esc(status)}</td>"
            f"<td>{esc(conf)}</td><td class=src>{esc(src)}</td></tr>")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Example Brief</title><style>{CSS}</style></head><body><main>
<div class=kicker>Anka · example output · {esc(PERIOD)}</div>
<h1>{esc(COMPANY)}</h1>
<div class=banner><strong>Fictional company, illustrative figures.</strong> This page shows the output
format of a governed research system. It is not a report on any real company and is not
investment advice.</div>

<h2>Key figures</h2>
<p>Every number states what it is a number <em>of</em>. The basis column says whether it covers the
parent company alone (standalone), the whole group (consolidated), a market price, or a figure the
company stated without saying which. Status and confidence come from where the number was sourced.</p>
<div class=wrap><table>
<thead><tr><th>Metric</th><th>Value</th><th>Basis</th><th>Status</th><th>Confidence</th><th>Source</th></tr></thead>
<tbody>
{chr(10).join(body)}
</tbody></table></div>

<h2>Why two ROE figures</h2>
<div class=call><p>The parent company's return on equity is 16.0%; the group's is 14.9%. A data
vendor quoting 14.9% would look like a disagreement. Checked by the contract, it is
<code>{esc(cls)}</code> ({esc(detail)}): both numbers are right, on different bases.
A system that prints "ROE 16.0%" without the basis has made a claim the reader cannot check.</p></div>

<h2>How each cell was decided</h2>
<ul>
<li><strong>Basis</strong> is printed from the basis the figure is actually on, never the one that
was requested. The guided growth figure was requested on a group basis, but management did not say
which basis it meant, so the page says exactly that.</li>
<li><strong>Status and confidence</strong> follow the source: computed from filed statements is
<em>company reported, high</em>; stated in a presentation is <em>company disclosed, medium</em>.</li>
<li><strong>Derived figures</strong> inherit their inputs' basis and the weakest input's confidence.
The P/E divides a market price by group EPS, so it is on a group basis. Group EPS divided by parent
book value would be refused rather than printed.</li>
<li><strong>Refusals are named.</strong> Had any figure lacked a lawful basis, it would appear here
as a named refusal code instead of a number. None did on this page.</li>
</ul>

<footer>Generated by <code>render_example.py</code> from <code>src/basis_contract.py</code> in
<a href="https://github.com/bankaraju/anka-governed-research">bankaraju/anka-governed-research</a>.
The same rules are enforced by the tests and the mutation harness in that repository.</footer>
</main></body></html>
"""


if __name__ == "__main__":
    page = render()
    if "--check" in sys.argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != page:
            sys.exit("docs/example.html is stale: run python render_example.py")
        print("docs/example.html is up to date")
    else:
        OUT.write_text(page, encoding="utf-8")
        print(f"wrote {OUT.relative_to(ROOT)}")
