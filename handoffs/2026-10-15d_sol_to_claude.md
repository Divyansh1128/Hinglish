# Sol → Claude, 15 October 2026 (task 26): automated verification pipeline complete

Implemented the requested offline pipeline under `autoverify/`, using only the
Python standard library. No network/model calls, existing-file edits, or commits.
No research families were solved, checked by a model, or assigned acceptance.
Qwen is explicitly prohibited as a solver/checker in the solver protocol.

## Added

- `make_solver_tasks.py`: accepts an authoring families list or a dataset object
  containing `families`; writes `claude_tasks.jsonl` and `gpt_tasks.jsonl`. Each
  record has exactly `family_id`, `rendering_id`, `form`, and `text`. Explicit
  whitelisting excludes gold, reference equations/solutions, and all metadata.
  Per-solver fixed-seed shuffles start from sorted family IDs.
- `SOLVER_INSTRUCTIONS.md`: independent-context protocol, JSONL schema, numeric
  quantity/extraction conventions, examples, CLI commands, flags, and limitations.
  Solver rows use `final_answer`, `unit`, `extraction` (`quantities`, `entities`,
  `asked_for`), and optional `ambiguity_note`, joined by `rendering_id`.
- `compare.py`: exact Fraction comparisons against gold and between solvers;
  per-solver cross-form quantity multisets and asked-for checks; all five
  requested flags. Writes `verification_report.json` for all families and
  `review_sheet.csv` for selected families. Flags do not change source status.
- `_common.py` / package initializers: shared input validation and exact parsing.
- `tests/test_autoverify.py`: 23 unittest cases using synthetic software fixtures.

## Usage

```sh
python3 -B autoverify/make_solver_tasks.py families.json --out-dir /tmp/blind-tasks --seed 20261015
# Separate independent Claude/GPT solver contexts produce their own output files.
python3 -B autoverify/compare.py families.json --claude /tmp/claude_outputs.jsonl --gpt /tmp/gpt_outputs.jsonl --out-dir /tmp/verification --seed 20261015
python3 -B -m unittest discover -s autoverify/tests -v
```

Both tools also support `python3 -B -m autoverify.<tool>`. Default seed: `20261015`.
Successful comparison exits 0 even with flags; malformed input exits 2 before
writing reports. Empty solver files flag missing outputs; nonexistent files,
malformed rows, duplicate IDs, and unknown rendering IDs are hard input errors.
Full authoring validation remains the responsibility of `authoring/check_family.py`.

## Explicit conventions and limits

- Review CSV: all flagged families first in family-ID order, then seeded random
  sampling without replacement of `ceil(unflagged_count / 5)`. One row per
  selected family; all families remain in the JSON report. Reviewer fields are
  blank, and `gold_after_review` (value + unit) is the sole gold column, rightmost
  after `notes`. Hide that column until the independent human review is recorded.
- Quantity comparisons preserve multiplicity, ignore list ordering, and compare
  exact values. Extract only explicitly stated quantities; the protocol specifies
  percentage/rate/ratio conventions. Entities are retained for inspection.
- `asked_for` is compared within each solver across E/R/C after case/whitespace
  normalization. Synonyms can trigger human review. Asked-for differences use
  the prescribed `cross_form_quantity_mismatch` flag; separate report booleans
  distinguish quantity vs asked-for failures.
- Missing comparisons are null, not incorrect/disagreement. Available pairs are
  still checked for cross-form consistency, with `complete: false`.
- Numeric answers and JSON decimals are parsed exactly (no binary floating point
  tolerance). Units are retained, not validated/converted. This is a numeric and
  extraction diagnostic; humans still assess units, equivalence and naturalness.
- Freeze the families snapshot used to make tasks until comparison. Outputs in
  the chosen destination are replaced on rerun; use a new directory per round.

## Validation

`python3 -B -m unittest discover -s autoverify/tests -v`: **23 tests passed**.
Coverage includes every individual flag and their union; exact/reduced/unreduced
fractions and signed denominators; rejection of rounded thirds; exact JSON
decimals; quantity multiplicity and asked-for differences; missing/empty outputs;
blind-field whitelisting and metadata/gold sentinels; seeded sampling/rounding and
flag-first ordering; byte determinism including reordered inputs; CSV Unicode,
quotes/newlines, blank review fields and gold placement; malformed/duplicate/
unknown rows; direct-script and module CLI invocation.

`git diff --check` passed; no tracked files changed. Other untracked handoffs and
the concurrent `research/autoverify_protocol_2026-10-15.md` were left untouched.
