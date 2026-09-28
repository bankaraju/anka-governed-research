# Mutation Verification Results

## What mutation testing proves

A test suite that cannot fail is not a test suite. Mutation testing deliberately breaks each rule and verifies that a named test catches the break. A mutant that survives means the rule is unenforced.

## Verification framework

```python
# KILLED:     rc == 1 AND a named test failed
# SURVIVED:   the suite passed with the mutation in place
# BROKEN_RUN: the suite did not execute (not a kill, not a survivor)
```

A kill is credited only when the **named test** fails — never by exit code alone.

## Results

### Scenario contract + peer tiers (33/33 fail-side mutants killed)

| Rule tested | Mutant | Killing test |
|-------------|--------|-------------|
| Probability total must be 100 ±1 | Tolerance widened to 1000 | `test_probability_total_off_blocks` |
| Missing probability → not complete | Probability forced to PRESENT | `test_a_leg_without_a_probability_is_not_complete` |
| Printed % must match computed upside | Tolerance widened to 15pp | `test_upside_present_only_when_the_printed_pct_matches` |
| Date required for "dated CMP" | Date check removed | `test_no_date_means_upside_absent` |
| Disordered ladder blocks | Ladder check disabled | `test_disordered_ladder_blocks` |
| Stated multiple must reproduce target | Tolerance widened ×1000 | `test_a_stated_multiple_that_does_not_reproduce_blocks` |
| Lineage mode defaults to strict | Default flipped | `test_lineage_mode_defaults_to_strict` |
| 7 required elements | Element removed from tuple | `test_required_elements_are_the_seven_named` |
| Confidence retired | Confidence added to optional | `test_confidence_is_retired_from_the_contract` |
| Tier-1 floor ≥5 | Floor lowered to 2 | `test_tier3_exact_label_and_no_number` |
| Tier-2 exact label | Label changed to "peer median" | `test_tier2_never_says_peer_median` |
| Cap-band thresholds | Large threshold 20000→200000 | `test_cap_bands` |
| Subject excluded by default | Subject included | `test_subject_excluded_by_default` |
| Cross-basis members refused | Basis check disabled | `test_basis_mismatch_is_refused` |
| ...and 19 more | | |

### Vector contract (24/24 fail-side mutants killed)

| Rule | Mutant shape | Result |
|------|-------------|--------|
| V1: one basis per mix | Mixed members admitted | KILLED |
| V2: lawful bases only | DERIVED/MARKET admitted as lawful | KILLED |
| V3: latest period preferred | Oldest period used | KILLED |
| V4: net denominator reconciled | Lines dropped from total | KILLED |
| V5: closure tolerance | Tolerance widened | KILLED |
| V6: freshness limits | Limits removed | KILLED |
| V7: geography issuer-stated | Calculated geography admitted | KILLED |
| V8: calculated cells one basis/period | Mixed-basis derived cells admitted | KILLED |

### Adversarial verification (false-GOVERNED hunt)

14 hostile mutations thrown at the whole-page inventory classifier:
- Value transplants between cells
- Tenfold/decimal inflation
- Comma-stripping
- Side-by-side clones
- Decoy-label injection
- Period-word swaps
- Unit-context saturation
- Basis-word stripping

**Zero false-GOVERNED breaks.** The classifier's behavior under attack was strictly conservative: hostile input either left governed items untouched or correctly lost governed status.

### Keep-side controls

Every mutant set includes a keep-side control (a semantically identical change that must NOT break any test). All keep-side mutants survived, confirming the tests are discriminative, not brittle.
