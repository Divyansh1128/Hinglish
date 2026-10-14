# Claude → Sol, 14 October 2026

Part of task 5 on docs/TEAM_BOARD.md, started early for speed while Astra writes research/pre_pilot_endpoint_spec_v1.md in parallel. Build ADDITIVE, opt-in code only. Nothing here is adopted until the user decides; Claude will reconcile your code with Astra's spec afterwards.

Read first: README.md, docs/PROJECT_STATUS.md, docs/TEAM_BOARD.md, research/claude_review/README.md, research/claude_review/scorer_probe_output.txt, test1_pilot/hinglish_pilot/scorer_v1.py and report.py.

Work ONLY in a new directory `secondary_analysis/` at the repository root (plus your handoff file). Python 3 standard library only. Do not modify any existing file: not test1_pilot/, not pilot/, not the scorer, not the notebooks or builders, not research/. Astra is writing in research/ at the same time.

Build:

1. `secondary_analysis/numeric_endpoint.py`: `extract_numeric(response)` → dict with extracted value (exact Fraction as string or None), unit text, and an `extraction_path` label. It is a SECONDARY, opt-in diagnostic and never replaces scorer v1.0.0. Handle the cases in the probe: **FINAL:** bold marker, FINAL: **v**, \boxed{v}, $v$, `x = v`, Rs./Rs/₹ prefix, ₹v/-, Indian digit grouping, fractions, decimals, percent, trailing lines after the FINAL line (use the LAST FINAL marker), multiple FINAL markers (report ambiguous, do not guess). `numeric_correct(response, gold)` compares the value only (apply gold conversions when the unit maps; ignore unknown unit words, but record them). Pure functions, no I/O.
2. `secondary_analysis/cmi.py`: Code-Mixing Index per Gambäck & Das (2014/2016): CMI = 100 × (1 − max_lang_tokens / (N − U)) where U = language-independent tokens; CMI = 0 when N = U. Input is a list of (token, tag) with tags in {hi, en, univ}. Also provide a simple, clearly labelled HEURISTIC romanized tagger (small English and romanized-Hindi wordlists; numbers/punctuation/names marked univ) that writes tags to be human-corrected; never present heuristic output as a gold tag. Count switch points too.
3. `secondary_analysis/report_secondary.py`: given a completed run directory (same layout as test1_pilot output: run_manifest.json, dataset.json, generation_attempts.jsonl), compute per-form strict accuracy (copied from stored `correct`, unchanged) beside numeric-value accuracy, a cross-tab of strict-invalid vs numeric-correct by form, and write `secondary_metrics.json` + `secondary_summary.md` into a NEW subfolder of the run, labelled "SECONDARY DIAGNOSTIC — strict v1.0.0 endpoint remains primary". Never overwrite existing run files.
4. `secondary_analysis/format_fixtures.json`: 12 NEW synthetic fixture families (E/R/C each = 36 texts), clearly marked `EXCLUDED_FORMAT_FIXTURE`, IDs prefixed `FMT2-`, covering currency (INR), elementary algebra (x = ?), ratio-as-fraction, metric units (kg, L, km, minute), and counts. Write them fresh; do not copy, paraphrase or derive from pilot families PIL001–PIL030 or the existing format_smoke.json. Use the same gold schema as pilot_dataset (value, unit, aliases, conversions, unit_omission_allowed, rounding_rule). Do NOT run any model.
5. `secondary_analysis/tests/test_*.py` (unittest): cover every probe case from scorer_probe_output.txt, CMI edge cases (all univ, monolingual, balanced), report on a fake run directory built in a temp dir, and fixture schema/ID-prefix checks. Also add a test asserting that `pilot/scripts/scorer.py` and `test1_pilot/hinglish_pilot/scorer_v1.py` are byte-identical and unchanged in behaviour on the probe cases (strict scorer must still reject them).
6. `secondary_analysis/README.md`: short; what it is, how to run tests, and that it is unadopted, secondary and model-free.

Run: `python3 -B -m unittest discover -s secondary_analysis/tests -v` and the existing suites from README.md to show nothing else changed.

Constraints: no model inference, training, network calls or paid APIs. No commits, pushes, resets or branch changes. Do not quote pilot gold values.

When finished write handoffs/2026-10-14_sol_to_claude.md: files created, test results (paste the counts), design choices Claude should check, and anything left undone.
