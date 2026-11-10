# EXPLORATORY — not pre-registered; does not change the confirmatory result (Harm, D052)

This post hoc analysis describes Phase-2 FINAL_TEST errors, strict-accuracy gap
components, output length, rejected unit strings and numeric-only Δ_C subsets.
It uses Python 3.9+ and the standard library, including the repository's
`secondary_analysis/numeric_literal_v2.py`. It needs no network or installed
packages and does not extract the archive or modify the original results.

From the repository root:

```sh
python3 -B analysis/phase2_exploratory/error_analysis.py
python3 -B analysis/phase2_exploratory/error_analysis.py --check
```

The first command writes `error_analysis.md` and `error_analysis.json` in this
folder and prints a ten-line findings summary. The second regenerates both
artifacts in memory and checks byte equality without writing. A successful
check exits with status 0 and prints the same summary. Paths are anchored to
the script, so both commands also work from other working directories.
Use `--output-dir /path/to/new/folder` to create a separate copy; `--archive`
and `--confirmatory-report` can override the two input paths.

The reader validates inner ZIP checksums, checkpoint identities, unique paired
coverage and matching snapshots/scorers. It checks all 60 strict and numeric
checkpoint × form accuracy counts against the supplied confirmatory report.
Input, endpoint, archived scorer and script hashes are recorded in JSON.
Outputs contain no timestamp, complete raw responses, item IDs or gold answer values.
Numeric literals in displayed model answer strings are masked; at most three
anonymised response-prefix snippets appear (first 200 source characters, then
masked and capped at 200). Title-case words are hidden to remove names.
The JSON includes all redacted unit
patterns, detailed length strata and decomposition cells.

The four disjoint outcome categories are strict-correct, numeric-correct but
strict-wrong, literal mismatch among strict-wrong, and numerically unscored
strict-wrong. The last category is **not** evidence of a reasoning error.
Numeric matching ignores units and conversions and has narrower suffix syntax
than strict scoring, so strict success need not imply numeric success.
The report accounts for this explicitly. Gap components are accounting
identities, length associations are observational, and numerically scored
subsets are selected by both models' outputs. Only counts and percentages are
reported; there is no resampling or significance testing.

EXPLORATORY — not pre-registered; does not change the confirmatory result (Harm, D052)
