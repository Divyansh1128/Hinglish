# Phase-2 family authoring guide (DRAFT, not yet human-frozen)
Strategy 1 of `research/claude_deep_research/datasets_2026-10-15.md`: bilingual
team members write each English (E) problem from scratch, code computes the gold,
R and C are drafted, then the two-reviewer + adjudicator protocol runs. The
schema is test1-1 (`test1_pilot/DATA_CONTRACT.md`). Every family starts as
`status: "DRAFT"`; only the human review process can make it ACCEPT.

## Independence rules (read before writing anything)

- Write from scratch, using only the style guide and topic/operation quotas. Do not
  browse or adapt GSM8K, MGSM or any other benchmark while authoring.
- No derivatives of the 30 pilot draft families (`pilot/annotation_draft_v1/v2`)
  or the FMT2 format fixtures (`secondary_analysis/format_fixtures.json`). These are
  permanently excluded from training and final tests, including descendants.
- Numeric siblings are the same family. Changing numbers, names, units or wording
  does not create a new family: reuse its `source_family_id`/`template_group_id`,
  or better, do not submit it. One underlying problem per family.
- Authors must not review their own families.

## Steps

1. Copy `authoring/family_template.json` (a list holding one blank family).
2. Fill identities with pseudonymous safe IDs (`[A-Za-z0-9][A-Za-z0-9_.-]*`):
   `family_id`, `source_family_id`, `template_group_id`. Pick one `topic`:
   comparison_remaining, two_step_money, fractions_percentages, ratios,
   rates_units, elementary_algebra. Set `split_role` as assigned by the coordinator.
3. Write E: one unambiguous English question with a single numeric answer and a
   clear unit. Avoid approximate answers; if rounding is asked for, state the rule
   in the question and store the rounded value as exact gold.
4. Compute gold in code, not by hand. Write `reference_equation` so that its last
   `;`-separated statement is `[variable =] arithmetic [= arithmetic ...] = value`,
   e.g. `9*x-14=58; x=(58+14)/9=8`. Only integers/decimals, `+ - * /` and
   parentheses are allowed there. Every arithmetic segment of that last statement
   must equal `gold.value` exactly (the checker uses fractions, so `10/3=3.33` fails).
5. Fill `gold`: `value` is an exact numeric string ("1/3", "0.5", "18"); `unit`,
   `aliases`, `conversions` (unit -> exact multiplier), `unit_omission_allowed`,
   `rounding_rule: "exact"`. Write `reference_solution_en` step by step.
6. Draft R: Hindi phrasing in Roman script under the frozen borrowing policy
   (digits, symbols, listed units, INR notation, names and the listed loan nouns may
   be shared). No substantive English clauses or relations in R.
7. Draft C: Roman-script Hindi-English mixing with productive English clauses or
   relations (comparison, rate, requested_answer, ...). English object nouns alone
   are not code mixing. List the switched roles in C's `switching_roles`.
8. Check that E, R and C are mathematically equivalent: same numbers, same unknown,
   same unit, no added or dropped information.
9. Record provenance (below), then run the checker.

## Operation-word balancing for C

Do not let C systematically replace Hindi operation words (`kam`, `zyada`,
`guna`, `baaki`, `hissa`, `pratishat`, ...) with English ones. Otherwise an apparent
C advantage may only reflect the removal of difficult Hindi vocabulary
(`research/operation_vocabulary_2026-10-15.md`, section 5). Keep the Hindi operation
word in a planned share of C items and switch only other relations (e.g. the
requested answer or a rate clause) there. Record which choice each C item uses in
`generation_or_edit_history`, and counterbalance it across topics as the
coordinator's quota sheet specifies.

## Provenance fields

- `authoring_origin`: `HUMAN_AUTHORED`, or `AI_DRAFT` when a model drafted any part.
  AI origin is preserved after human editing.
- `provenance`: author pseudonym, date, and "written from scratch; no benchmark
  consulted". Name any source that was introduced.
- `source_license`: "No external source used" or the licence and document identifier.
- Per form: `creator_type` (HUMAN / model name) and `generation_or_edit_history`
  (model, prompt version, human edits, transliteration cross-checks used).
- No names, emails or tokens anywhere; reviewer identity mappings stay outside.

## Checking

```sh
python3 -B authoring/check_family.py my_families.json
```

It checks structure, gold (test1_pilot `validate_gold`), equation exactness, duplicate
texts/IDs, and flags 5-gram Jaccard >= 0.5 against pilot draft or FMT2 texts (IDs only,
never pilot gold). Exit 0 does not certify equivalence, naturalness or independence;
retire or rewrite flagged near-duplicates, do not reword until they pass.
