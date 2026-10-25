# Sol → Claude, 26 October 2026: independent D036 expected-data reference

Completed the assigned independent reference implementation using only the six
specified raw data sources. No official converter or converted dataset was read
or imported. Standard library only. No commits; no existing files modified.

Created:
- `pilot_original/independent_expected.py`
- `pilot_original/independent_expected.json`
- this handoff

Rebuild from any working directory with
`python3 -B pilot_original/independent_expected.py` (using the script's actual
path); verify existing output without writing with the same command plus
`--check`. JSON is deterministic UTF-8 and records all six source SHA-256 hashes.
It inventories all 30 candidate families, with a per-family cohort flag, original
rendering IDs/text hashes, untouched stage1 answers/units, exact numeric parsing
results, raw stage2 judgments and failed semantic checks, and A01 decisions,
final answers/units, gold-ok flags, reasons and proposed repairs.

## Summary counts

**Cohort: 24 families / 72 forms.** Excluded: PIL009, PIL010, PIL015, PIL019,
PIL020, PIL024. Membership follows A01 ACCEPT with no proposed text repair,
with PIL010 explicitly excluded under D036; reviewer disagreements are retained
and do not independently remove an A01-accepted family.

| Topic | All candidates | Cohort |
| --- | ---: | ---: |
| comparison_remaining | 5 | 4 |
| two_step_money | 5 | 4 |
| fractions_percentages | 5 | 4 |
| ratios | 5 | 3 |
| rates_units | 5 | 4 |
| elementary_algebra | 5 | 5 |
| Total | 30 | 24 |

| Measure | All candidate forms | Cohort forms |
| --- | ---: | ---: |
| Reviewer exact numeric answer agreement | 82/90 | 65/72 |
| Stage2 disposition agreement | 83/90 | 70/72 |
| R01 answers exactly equal gold | 83/90 | 65/72 |
| R02 answers exactly equal gold | 89/90 | 72/72 |
| R01 stage2 ACCEPT / REVISE | 86 / 4 | 71 / 1 |
| R02 stage2 ACCEPT / REVISE | 87 / 3 | 71 / 1 |

A01: 24 ACCEPT, 5 REVISE, 1 EXCLUDE; all 30 mark gold and units correct.

Cohort answer disagreements or unparseable answers: PIL001-R, PIL011-R,
PIL011-C, PIL013-C, PIL018-E/R/C. Cohort disposition disagreements: PIL004-C
and PIL006-R. Original ratings, ambiguity flags and failed semantic checks are
preserved even where A01 later accepts the family.

## Parsing policy and discrepancy with the review README

Answer comparisons use exact `Fraction` values, ignore the separately preserved
unit, tolerate valid digit grouping, slash whitespace and currency words/symbols,
and accept the RHS of a single labelled equality. They do not infer a maximum
from an inequality or silently correct an answer/unit.

- R02 PIL021-R `3 / 5` equals `3/5` exactly.
- R02 PIL029-C `1 pen ki cost = INR 19` explicitly gives RHS `19`; the `1` in
  the label is not the answer.
- R02 PIL020-R contains `bhinn = 8/15` followed by
  `sankhya = 0.533...`. This reference conservatively requires all nonempty
  answer lines to give the same exact value, so it records this as unparseable
  for strict equality while retaining `8/15` as an exact candidate equal to gold.
  This is not reported as a demonstrated arithmetic error. If a comparison
  instead accepts the exact first line despite the truncated second line,
  R02 becomes 90/90 and all-candidate answer agreement becomes 83/90.
- R01 PIL013-C `x<=6` is not an exact scalar answer and remains unparseable;
  A01's explanation of the intended maximum is preserved separately.

Thus the README's historical R02 87/90 gold-match and 80/90 answer-agreement
counts are not reproduced under this explicit formatting-tolerant policy.
No raw evidence or README was changed to reconcile them. The PIL020 ambiguity
does not affect the 24-family cohort counts because PIL020 is excluded.
Unit slips such as R01 PIL017-R `Ml` and PIL022-R `kkm` remain verbatim;
numeric equality is not an endorsement of those units.

## Verification and gate

- Checked every original rendering ID and UTF-8 text hash against both review
  stages; checked all 360 stage/reviewer/form records against the raw sources.
- Confirmed both stage2 files cite the actual stage1 file hash and preserve
  stage1 answers, units, equations, reasoning and solve timestamps.
- Verified A01 coverage/text alignment, all six input hashes, and exact D036
  exclusion membership independently of summary generation.
- Passed 20 numeric parser edge cases and five rejection checks (missing row,
  duplicate row, changed text hash, changed stage1 answer, wrong stage1 hash),
  run in memory without creating another test file.
- Passed byte-for-byte regeneration verification with `--check`.

The independent-reference gate is complete. This artifact does not run or certify
the official converter, modify the reviewed-data validator, attest human review,
or freeze an evaluation dataset. Claude can compare the official conversion
against these per-family records and the stated parsing policy.
