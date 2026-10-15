# paper_analysis 0.1.0

Turns Test 1 results ZIPs into paper-ready Markdown and LaTeX (booktabs) tables, a combined per-rendering CSV and optional figures. It uses only the Python 3 standard library. matplotlib is optional: without it, the tool skips the figures and says so.

**This tool reports stored scores and adds no new scoring.** Strict correctness is the stored automatic `correct` (scorer v1.0.0) of the one terminal generated attempt for each rendering. Accuracy, Wilson intervals and the paired family bootstrap use the same formulas as `test1_pilot/hinglish_pilot/report.py`, including its RNG order (E−C, E−R, R−C) with the seed and resample count stored in the run's `experiment_config.json`. Each run's numbers are checked against the `metrics.json` and `predictions.csv` stored in its ZIP. Any mismatch is flagged and the exit code is 3. The `numeric_literal_v1` column is an UNADOPTED secondary diagnostic from `secondary_analysis`, shown beside the strict endpoint.

## Usage

From the repository root:

```sh
python3 -B -m paper_analysis.build_tables RUN_results.zip [MORE_results.zip ...] --out NEW_DIR
python3 -B -m paper_analysis.build_tables FMT2_format_test_results.zip --out NEW_DIR   # outer ZIP of *_results.zip
python3 -B -m unittest discover -s paper_analysis/tests -v
```

`--out` must be a new or empty directory. Add `--no-figures` to skip matplotlib. Exit codes: 0 means success, 1 means an input was rejected and nothing was written, and 3 means outputs were written but a value disagrees with the stored report.py outputs.

Output: `README.md` (inputs with SHA-256 and a status for each run), `per_rendering.csv` (all runs), and a folder for each run containing:
- `tables.md` (status, consistency checks and all tables);
- `tables.tex`;
- `tables/{accuracy,paired,invalid,resources,numeric}.{md,tex}`;
- `summary.json`;
- `figures/{accuracy_by_form,family_heatmap}.{pdf,png}`.

## Safety and limits

ZIPs are treated as untrusted. They are read into memory and never extracted or executed. The tool rejects:
- absolute, drive-qualified, backslashed or `..` member paths;
- symlinks;
- encrypted, duplicate or oversized members.

Every `checksums.sha256` entry must match, and every member must be listed. Attempt `record_sha256` values and the config, dataset and split snapshot hashes are verified against `run_manifest.json`.

An incomplete run gets only the invalid-reason and resource tables. Headline accuracy, paired comparisons, the numeric table and the figures are suppressed, matching report.py. Manual audit overlays (`analysis_revisions/`) are not used. In an outer ZIP, only the inner results ZIPs are verified; other members are listed as ignored. Runs are never pooled.
