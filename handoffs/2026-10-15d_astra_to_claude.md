# Astra → Claude, 15 October 2026: task 27 delivered

Proposal: [automated-checker validation and data separation](../research/autoverify_protocol_2026-10-15.md). Read D027, the dataset research, experiment specification, authoring guide, team board and task-26 handoff. Only this handoff and the requested protocol were created; no code/data/decision changes or commits.

The protocol specifies original-v2 A01 adjudication as validation ground truth, including naturalness-driven REVISE/REJECT; a family-level confusion matrix and intervals; proposed precision >=0.70 / recall >=0.90, minimum 10 positive and 10 negative labels, and zero critical false negatives. Failure or insufficient cases requires full primary human review until a fresh validation succeeds. No validation was run or claimed.

It also specifies GPT FINAL_TEST/DEV versus Claude TRAIN drafting, an optional 12-family wholly human-written FINAL_TEST stratum, 30 additional independently double-reviewed candidates, exact unflagged sampling and attrition rules, proposed topic quotas, permanent ancestry exclusions, four freeze points and ledger fields.

Integration decisions to record before use:

- The 20% sample is of unflagged candidates, in addition to all flags, matching task 26. Proposed hash-ranking selection must be reconciled with Sol's seeded implementation before the validation freeze; neither is silently adopted by this handoff.
- Gold must be withheld until first judgments are saved; a right-hand CSV gold column does not establish blinding. Freeze all actual flag logic, including unit and requested-unknown checks, before validating it.
- Single-reviewed and auto-screened families cannot satisfy legacy `test1-1` two-reviewer/adjudicator attestations. A separate versioned cohort/review-coverage format is needed before use, preserving the original pilot validator.
- The proposed 16 smoke families are additional exclusions, never part of the 160 usable TRAIN families. This resolves an older budget ambiguity but needs recorded adoption.
- Existing Pilot-B drafts may predate these proposed quotas/freezes; record that history rather than call their construction preregistered. Naturalness remains unassessed on unreviewed families.

Verification: protocol is under 120 lines; relative document links and quota totals checked. Task-27 proposal delivered; the human/checker-validation gate has not advanced. R01/R02/A01 returns, recorded protocol adoption and implementation alignment remain prerequisites. No user approval is requested here: this assignment explicitly requested proposals only.
