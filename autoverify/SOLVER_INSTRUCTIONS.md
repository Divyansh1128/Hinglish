# Independent blind solver protocol

Only **Claude** and **GPT** solve/check these tasks. Qwen must never be a solver
or checker. The scripts are offline standard-library Python: they make no model
or network calls. A coordinator provides each solver only its own task JSONL and
this protocol. Keep the families source, gold, equations, reference solutions,
other solver's work, and verification report outside the solver's context. Use
separate independent contexts for the two solvers. Do not give a solver its own
authored families for review.

Each task has exactly `family_id`, `rendering_id`, `form` (E/R/C), and `text`.
Solve each rendering independently from its text, including when other renderings
share a family ID. Do not infer an answer/extraction from sibling forms, consult
external benchmarks, or compare with the other solver. Emit one JSON object per
rendering, one object per line, without Markdown fences or surrounding prose:

```json
{"rendering_id":"synthetic-01-E","final_answer":"7/3","unit":"litres","extraction":{"quantities":["7","3"],"entities":["water","bottles"],"asked_for":"water per bottle"},"ambiguity_note":""}
```

The example is a software illustration, not a dataset answer. Required fields:

- `rendering_id`: copy the task's exact ID. Never repeat or invent an ID.
- `final_answer`: an exact numeric string (`"18"`, `"0.5"`, `"1/3"`) or JSON
  number. Prefer strings, especially for nonintegral values. Use a reduced or
  unreduced fraction when necessary; never replace `1/3` with an approximation.
  JSON decimal tokens are read exactly, without binary floating point. Do not
  include units, percentages, commas, equations, or explanations in this field.
  Follow any rounding rule explicitly requested by the question.
- `unit`: answer unit as requested in the question, or `""` if dimensionless.
  Do not change to another scale, e.g. centimetres when metres are requested.
- `extraction`: an object with all three fields below.
  - `quantities`: a list of exact numeric values explicitly stated in the
    question, including quantities written as words. Preserve repetition and
    exclude computed intermediate quantities and the computed final answer.
    Use the scale stated in the text: `25%` becomes `"25"`, `2 cm` becomes
    `"2"`, a stated one-half becomes `"1/2"`. Include explicit rate and ratio
    components separately (e.g. 3:4 becomes `["3","4"]`); a fraction itself
    stays one value. Do not add an implicit 1 for “per” or “each”. Apply the same
    convention to all languages/forms. List order does not affect comparison.
  - `entities`: a list of short English names for the people, objects, or
    quantities involved. Preserve proper names; use consistent English object
    labels across forms. These are retained for inspection, not auto-matched.
  - `asked_for`: a short English phrase naming the unknown, including its owner
    or target when relevant (e.g. `"money remaining for Mira"`). Translate this
    phrase to English for R/C too. Use a consistent phrase when the unknown is
    the same; do not merely write `"answer"` or include the numeric answer.
- `ambiguity_note`: optional string, blank when unambiguous. If the wording
  admits multiple mathematical readings, briefly explain the issue and give
  your best reading's answer/extraction in the required fields. Do not silently
  resolve ambiguity by consulting sibling forms. Omit no task intentionally.

# Coordinator usage

Run from the repository root (Python 3, no dependencies):

```sh
python3 -B autoverify/make_solver_tasks.py families.json --out-dir /tmp/blind-tasks --seed 20261015
# Have independent Claude/GPT agents produce their output JSONL separately.
python3 -B autoverify/compare.py families.json --claude /tmp/claude_outputs.jsonl --gpt /tmp/gpt_outputs.jsonl --out-dir /tmp/verification --seed 20261015
python3 -B -m unittest discover -s autoverify/tests -v
```

Both scripts also support `python3 -B -m autoverify.make_solver_tasks` /
`python3 -B -m autoverify.compare`. Input is either the authoring JSON list or a
dataset object with a `families` list. Run `authoring/check_family.py` separately
for full authoring validation; this pipeline validates its consumed fields only.

Task filenames are `claude_tasks.jsonl` and `gpt_tasks.jsonl`. They contain only
the four whitelisted fields; metadata is never copied. Families are sorted by ID
before per-solver seeded shuffles, making output independent of input ordering.
The default seed is `20261015`. Keep task text fixed between task generation and
comparison; rendering IDs must refer to that same snapshot. Existing outputs at
the destination are replaced, so use a fresh directory for a new review round.

Solver outputs are joined by `rendering_id`, never by line order. Blank lines are
ignored. An empty output file is allowed and flags all that solver's renderings
as missing. A nonexistent file, malformed JSON/schema/numeric value, duplicate ID,
or unknown ID is an input error (exit 2); fix it and rerun. Such errors are
validated before reports are written. The scripts reject output paths that would
overwrite an input. Successful generation/comparison returns exit 0 even when
families are flagged: flags request human review, not an execution failure.

`verification_report.json` includes every family/rendering, each solver's exact
numeric equality with gold, numeric solver agreement, original extractions and
units, missing results, cross-form checks and sampling metadata. Missing results
have `answer_equals_gold: null`; solver agreement is null when either result is
missing. Units are retained, **not validated or converted**: these checks are
exact numeric diagnostics, not a replacement for dimensional/semantic review.

Per solver, quantity multisets (including repeated values, normalized through
`Fraction`) and `asked_for` are compared across E/R/C. `asked_for` comparison only
normalizes case and whitespace; it is not a semantic model. Synonymous phrases
can therefore trigger review. With missing forms, available pairs are still
compared and `complete` is false; fewer than two outputs yields null consistency.

Family flags are the union of:

- `solver_gold_mismatch`: any present solver answer differs numerically from gold.
- `solver_disagreement`: both answers exist and differ numerically.
- `cross_form_quantity_mismatch`: a solver's quantity multiset **or asked_for**
  differs across forms. Separate report booleans identify which check failed.
- `ambiguity_noted`: any solver supplies a nonblank ambiguity note.
- `missing_output`: either solver has no row for any rendering.

`review_sheet.csv` contains one row per **selected** family: all flagged families
first (sorted by ID), followed by a seeded random sample without replacement of
20% of the unflagged families, rounded **up** (`ceil(n/5)`; zero if none remain).
Sampling starts from sorted family IDs and uses its own seeded RNG. Every family
appears at most once. The full report includes unselected families too.

The sheet includes E/R/C texts, flags, selection type, and blank reviewer columns:
`equivalence_ok`, `naturalness_R (1-5)`, `naturalness_C (1-5)`,
`decision (ACCEPT/REVISE/REJECT)`, and `notes`. The sole gold column,
`gold_after_review`, is the rightmost column after reviewer notes; it holds the
exact value and unit. Hide it until the reviewer has independently assessed the
question. Automated checks never assign ACCEPT or modify source family status.
