# Claude review of Sol's secondary_analysis/ (task 6)

14 October 2026. AI code review; nothing adopted.

Sol's code was well structured and stayed inside its write scope. Claude aligned it with Astra's spec section 1 (numeric_literal_v1), resolving the differences between Claude's parallel brief and the spec in favour of the spec:

- `numeric_endpoint.py` was rewritten. Changes: a FINAL marker is required at the start of its line, with no recovery from other lines (`missing_final` / `unsupported_marker`); no unit conversion; truncated outputs fail; any one-letter assignment is accepted; whole-line `**FINAL: v**` is accepted; `trailing_nonblank` and `unvalidated_suffix` flags are added; the spec's reason codes are used (`status` replaces `error`). The API names Sol chose are kept.
- `report_secondary.py` now passes `truncated`, adds per-form `numeric_status` counts and the strict × numeric 2×2 table, and its policy text matches the spec.
- The tests were updated to the spec: 35 secondary tests, all OK. Existing suites pass: 3 + 4 + 22. The scorer v1.0.0 SHA-256 is unchanged (c48f9d12…).
- README endpoint section rewritten.

Fixtures: 12 families FMT2-001…012. All 12 answers were hand-checked and are correct. Still needed before any GPU use: a human check of E/R/C equivalence and lineage (FMT2-012 uses beads, a count noun also used in the pilot), and a decision on whether R texts should use romanized unit words to actually elicit them.

Not yet aligned (lower priority, needs a decision first): `cmi.py` uses hi/en/univ tags; the spec proposes HI/EN/SHARED/MIXED/UNCERTAIN with missing CMI when MIXED or UNCERTAIN remain. Adapt after the user adopts CMI_v1.
