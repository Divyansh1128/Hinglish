# Sol → Claude, 14 October 2026

Completed the task in `handoffs/2026-10-14_claude_to_sol.md` as additive,
opt-in code. **UNADOPTED; secondary only; strict scorer v1.0.0 remains primary.**
Python 3 standard library only. No model inference, training, network calls,
paid APIs, commits, pushes, resets or branch changes.

## Files created

- `secondary_analysis/__init__.py` — separate module version 0.1.0.
- `secondary_analysis/numeric_endpoint.py` — pure exact-Fraction extraction,
  bool `numeric_correct`, and detailed `evaluate_numeric` diagnostics.
- `secondary_analysis/cmi.py` — CMI, switch points, explicitly heuristic
  romanized tagging, and exclusive-create editable annotation JSON CLI.
- `secondary_analysis/report_secondary.py` — completed-run validation,
  original strict scores beside secondary numeric accuracy, per-form cross-tabs,
  invalid-reason breakdowns, per-rendering paths/units/flags, input fingerprints;
  creates a new `secondary_diagnostic_*` subfolder on every invocation.
- `secondary_analysis/format_fixtures.json` — 12 fresh synthetic families / 36
  E/R/C texts, INR, algebra, fraction ratios, kg/L/km/minute and counts.
  All marked `EXCLUDED_FORMAT_FIXTURE`, all IDs prefixed `FMT2-`; exclusion
  identities include family/source/template/rendering IDs and descendants.
- `secondary_analysis/tests/test_numeric_endpoint.py`
- `secondary_analysis/tests/test_cmi.py`
- `secondary_analysis/tests/test_report_secondary.py`
- `secondary_analysis/tests/test_fixtures.py`
- `secondary_analysis/README.md` — scope, CLI usage, policies and limitations.
- `handoffs/2026-10-14_sol_to_claude.md` — this handoff.

No existing file was edited by Sol. A before/after SHA-256 inventory confirms
all existing pilot, scorer, notebook, builder and other implementation files
remain unchanged. Two existing files changed concurrently outside this work:
`docs/TEAM_BOARD.md` and `research/pre_pilot_endpoint_spec_v1.md`. Other agents'
new documents were left untouched. No existing file disappeared.

## Verification results

Final secondary suite:

```text
python3 -B -m unittest discover -s secondary_analysis/tests -v
Ran 34 tests in 0.185s
OK
```

Existing suites from the root README:

```text
python3 -B -m unittest discover -s pilot/scripts -p 'test_*.py' -v
Ran 3 tests in 0.001s
OK

python3 -B -m unittest discover -s t4_smoke -p 'test_*.py' -v
Ran 4 tests in 0.012s
OK

PYTHONPATH=test1_pilot python3 -B -m unittest discover -s test1_pilot/tests -p 'test_*.py' -v
Ran 22 tests in 0.555s
OK
```

**63 unittest tests passed** across the final secondary suite and the three
existing suites. Existing Test 1 tests also executed their fake-backend notebook
software demo in a temporary directory; no research/model generation occurred.

The README annotation v1 verifier was executed from an unchanged temporary copy
of the annotation packet, with copied helper code and the historical review
packet. Its script writes `verification.json`, so executing the copy preserves
the handoff's prohibition on modifying existing files. Result counts:

```text
PASS — SOFTWARE CHECKS ONLY; NO HUMAN VALIDATION
families: 30
renderings: 90
exact_unit_conversion_checks: 27
reviewer_javascript_syntax_checks: 4
verified_checksums: 20
form_import_export_logic_checks: PASS
```

New tests cover every category in `scorer_probe_output.txt`, using freshly
specified synthetic answers rather than reading pilot gold. Accepted strict
controls remain accepted; every probe rejection retains its original reason
in both scorer copies. Both scorer files are byte-identical and match the
pre-task SHA-256:

```text
c48f9d12e733eb1bfe5af5b1fece6e3ff69cb2342a97fe3ba8ac9f01f68dbbbc
```

Report tests use temporary fake run exports with infrastructure retries,
checksums and completed E/R/C coverage. They verify original-file preservation,
fresh report directories on repeat invocation, stored strict booleans copied
without rescoring, all four cross-tab cells, and rejection of incomplete,
active, corrupt, foreign or multiply generated attempts.

## Design choices to reconcile with Astra's spec

1. The handoff says both "use the LAST FINAL marker" and "multiple FINAL
   markers (report ambiguous, do not guess)." The ambiguity rule takes priority:
   the last marker's line is selected only when it is the sole marker. Repeated
   markers, even with identical answers, produce null value and
   `ambiguous_multiple_final`. Notes after a sole marker are ignored.
2. Without FINAL, extraction tries only the last nonempty line as a standalone
   scalar expression. It does not search reasoning for a matching number.
   Supported wrappers are simple bold, dollar math and `\boxed{v}`; nested
   LaTeX fractions, tuples and alternative numeric answers are rejected.
3. Gold aliases/conversions map units exactly. INR spelling variants are fixed
   format aliases. Unknown unit words and omitted units use factor 1, regardless
   of strict omission policy, and unknown words are recorded. Romanized unit
   words are not silently interpreted as physical conversions. Percent is
   converted to a fraction during extraction. No approximate matching is used.
4. Refusal/truncation do not suppress numeric extraction: this diagnostic asks
   only whether the extracted scalar matches. Reports preserve original flags
   and warn that this is not human-reviewed semantic correctness. Strict scores
   remain the stored scores, including their existing refusal/truncation policy.
5. CMI excludes `univ` from its denominator; empty/all-univ input has CMI zero.
   Switch points compare successive hi/en tokens while skipping univ tokens.
   The tiny tagger defaults unknown/overlapping words to univ, accepts explicit
   names, and clearly marks its editable JSON NOT GOLD. Human correction and
   borrowing-policy decisions remain required.
6. The 12-family fixture container has its own excluded schema and the requested
   exact pilot gold fields. It is intentionally not relabeled accepted/demo
   research data. A future smoke-notebook adapter is outside this handoff's
   scope. Texts were freshly authored without loading/copying/paraphrasing pilot
   questions or the existing format-smoke fixture; mathematical equations were
   independently checked. Equivalence, naturalness and classification remain
   unreviewed human judgments.

## Remaining work

Nothing left undone within this coding handoff. Claude's reconciliation/code
review and the user's adoption decision remain pending. No fixture model run,
prompt/scorer revision, notebook integration, actual pilot report or annotated
gold CMI is claimed or included.
