"""Mutation harness for src/basis_contract.py.

Each mutant deliberately breaks one rule. The test suite must catch every one.

Scoring (the part most harnesses get wrong):
  KILLED      pytest exited 1 AND at least one NAMED test failed
  SURVIVED    pytest exited 0 with the rule broken — the rule is unenforced
  BROKEN_RUN  anything else (usage error, collection error, no tests ran).
              Not a kill: pytest exits 4 or 5 when nothing executed, and a
              harness that scores `rc != 0` as a kill credits itself for runs
              in which no assertion was ever evaluated.

Each mutant must also match its anchor exactly once and must change the file's
hash, otherwise the harness reports BROKEN_RUN instead of a false pass.

Every run happens in a temporary copy of the repository; the working tree is
never modified.  Usage:  python tools/mutate.py
"""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = "src/basis_contract.py"

# (id, rule being broken, anchor, replacement)
MUTANTS = [
    ("M01", "document extraction is company-disclosed",
     'return "company_disclosed", "medium"', 'return "company_reported", "medium"'),
    ("M02", "a filed formula carries high confidence",
     'return "company_reported", "high"', 'return "company_reported", "medium"'),
    ("M03", "an unfiled own formula is 'calculated'",
     'return "calculated", "medium"', 'return "company_reported", "medium"'),
    ("M04", "screener series is company-reported at medium confidence",
     'if sk == "screener_series":\n        return "company_reported", "medium"',
     'if sk == "screener_series":\n        return "company_reported", "high"'),
    ("M05", "an unnamed producer is unresolvable, never guessed",
     "return None  # producer unnamed", 'return ("calculated", "low")  # producer unnamed'),
    ("M06", "a derivation is only as strong as its weakest operand",
     "return min(confidences", "return max(confidences"),
    ("M07", "bank rules apply only to banks",
     "if claim.is_bank:", "if True:"),
    ("M08", "an archetype-banned key refuses for a bank",
     "if claim.canonical_key in BANK_BANNED_KEYS:", "if False:"),
    ("M09", "a bank Tier 1 key refuses anything but standalone",
     'if claim.served_basis != "STANDALONE":', "if False:"),
    ("M10", "the page prints the SERVED basis, never the pinned one",
     "basis, refusal = resolve_basis(claim)\n    if refusal:",
     "basis, refusal = claim.pinned_basis, None\n    if refusal:"),
    ("M11", "a refused claim prints its refusal, not a basis",
     'return f"withheld ({refusal})"', "return BASIS_LABELS.get(claim.served_basis)"),
    ("M12", "different keys are never compared as values",
     "if pilot.canonical_key != reference.canonical_key:", "if False:"),
    ("M13", "a basis difference is its own class, never a value difference",
     "if pilot.served_basis != reference.served_basis:", "if False:"),
    ("M14", "the value tolerance stays tight",
     "max(0.05, 0.001 * abs(reference.value))", "max(5.0, 0.1 * abs(reference.value))"),
    ("M15", "a MARKET leg is basis-neutral",
     'if b == "MARKET":', "if False:"),
    ("M16", "a set of price legs alone has no basis to serve",
     "if not bases:", "if False and not bases:"),
    ("M17", "operands on different bases refuse",
     "if other is not None:", "if False:"),
    ("M18", "an operand with no basis refuses",
     "if first is None:", "if False:"),
    ("M19", "UNSPECIFIED is rejected for a derived estimate",
     'if first == "UNSPECIFIED":', "if False:"),
]

_FAILED = re.compile(r"^FAILED (tests/\S+::\S+)", re.M)


def _pytest(cwd: Path) -> tuple[int, list[str]]:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rf", "tests"],
        cwd=cwd, capture_output=True, text=True,
    )
    return r.returncode, _FAILED.findall(r.stdout)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "repo"
        shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
        target = work / TARGET
        pristine = target.read_text()

        rc, failed = _pytest(work)
        if rc != 0:
            print(f"baseline suite is not green (rc={rc}, failed={failed}); refusing to score mutants")
            return 2

        rows, bad = [], 0
        for mid, rule, anchor, repl in MUTANTS:
            n = pristine.count(anchor)
            if n != 1:
                rows.append((mid, "BROKEN_RUN", f"anchor matched {n}x", rule))
                bad += 1
                continue
            before = _sha(target)
            target.write_text(pristine.replace(anchor, repl, 1))
            if _sha(target) == before:
                rows.append((mid, "BROKEN_RUN", "mutation changed nothing", rule))
                bad += 1
                target.write_text(pristine)
                continue
            rc, failed = _pytest(work)
            target.write_text(pristine)
            if rc == 1 and failed:
                verdict, why = "KILLED", failed[0].split("::")[-1] + (f" (+{len(failed) - 1})" if len(failed) > 1 else "")
            elif rc == 0:
                verdict, why = "SURVIVED", "suite passed with the rule broken"
            else:
                verdict, why = "BROKEN_RUN", f"pytest rc={rc}, no named failure"
            if verdict != "KILLED":
                bad += 1
            rows.append((mid, verdict, why, rule))

        width = max(len(r[2]) for r in rows)
        for mid, verdict, why, rule in rows:
            print(f"{mid}  {verdict:<10}  {why:<{width}}  {rule}")
        killed = sum(r[1] == "KILLED" for r in rows)
        print(f"\n{killed}/{len(rows)} mutants killed by a named test")
        return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
