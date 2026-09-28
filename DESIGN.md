# Design notes: why a claim carries two bases

## The problem I started with

An equity report is a few hundred numbers. For each one a reader is entitled to ask three things: where did it come from, how was it computed, and what is it a number *of*. The third question is the one most systems skip. A company files two sets of accounts: the parent company alone (standalone) and the whole group (consolidated). The same ROE can legitimately be 16.0% on one and 14.9% on the other. Neither is wrong. A report that prints "ROE 16.0%" without saying which has made a claim the reader cannot check.

## What I built first, and how it failed

My first design gave each claim one basis field. A resolver asked for the basis the rules wanted (standalone for a bank's asset-quality ratios, for example). It fetched the figure and stamped the requested basis on it.

That works until the requested basis does not exist. Then a fallback route serves the nearest figure the issuer did state, and the claim still carries the basis that was asked for. When I audited a 231-claim pilot, **51 claims had been served through a fallback while still stamped with the requested basis.** Every one would have printed a basis the number was not on. The tests passed, because they checked that a basis was present, not that it was true.

## The split

So the contract now carries two fields:

- `pinned_basis`: what the resolver asked for. Useful for audit, and never printed.
- `served_basis`: what the figure is actually on. The only basis a reader sees.

When the two disagree, that is a fact about the pipeline, not about the company. The page says what it is showing you. Where no lawful basis exists, a bank's standalone ROA for example, the claim refuses with a named code (`BANK_STANDALONE_ABSENT`). It does not substitute the group figure.

The same idea changed comparison. Two figures on different bases are a `BASIS_MISMATCH`, their own outcome class, never a `VALUE_DIFFERENCE`. Otherwise every reconciliation sends someone chasing a discrepancy that does not exist.

## What I learned about testing

The second lesson was about my own instruments. My early mutation harness scored a mutant as killed whenever pytest exited non-zero. pytest exits 4 on a usage error and 5 when no tests ran at all. So a harness pointed at a moved test file credits itself with kills in which no assertion ever executed. Now a kill requires exit code 1 **and** a named test in the failure list. The harness also checks that each mutation matched its anchor exactly once and actually changed the file. `tools/mutate.py` in this repo follows those rules.

The general form, which I now apply everywhere: **a check must be able to fail, and it must fail for the reason it names.** A gate that passes on empty input, a test built on a fixture that already assumes the answer, or a counter that merges two causes of refusal: each reads as green while measuring nothing.

## Portability

The production system reads Indian exchange XBRL filings. Nothing in the claim model is specific to them. `served_basis`, named refusals and basis-aware comparison apply equally to SEC EDGAR 10-K/10-Q filings, IFRS filers, or any source where one entity reports more than one set of accounts.
