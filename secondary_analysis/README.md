# Secondary analysis 0.1.0

**UNADOPTED, opt-in, secondary and model-free. Strict scorer v1.0.0 remains primary.**
Python 3 standard library only. This package does not run a model or alter any
pilot scorer, prompt, dataset, notebook, stored score or research decision.

From the repository root:

```sh
python3 -B -m unittest discover -s secondary_analysis/tests -v
python3 -B -m secondary_analysis.report_secondary /path/to/completed_run
python3 -B -m secondary_analysis.cmi 'Tara has 19 beads aur kul kitne hain?' --output /path/to/new_tags.json
```

The report reads `run_manifest.json`, `dataset.json`, and
`generation_attempts.jsonl`. It requires complete E/R/C coverage, selects the
sole terminal generated attempt after any infrastructure retries, and copies
stored `correct`/`invalid_reason` unchanged. Input hashes and available snapshot
checksums are verified. Each invocation creates a new `secondary_diagnostic_*`
subfolder containing `secondary_metrics.json` and `secondary_summary.md`.

`numeric_endpoint.py` implements `numeric_literal_v1` exactly as proposed in
`research/pre_pilot_endpoint_spec_v1.md` section 1 (aligned by Claude on
14 October 2026). `extract_numeric(response, truncated=False)` never consults
gold. It requires exactly one FINAL marker at the start of its line (`FINAL:`,
`**FINAL:**`, `**FINAL**:` or a whole-line `**FINAL: ...**`); zero markers give
`missing_final`, more than one give `multiple_finals`, and no answer is ever
recovered from other lines. Trailing lines are ignored but flagged
`trailing_nonblank`. Supported answer grammar: optional one-letter assignment
(`x =`), optional currency prefix (₹, INR, Rs., Rs), a scalar optionally wrapped
in `**`, `$` or `\boxed{}`, then an optional word suffix (or `/-` after a
currency prefix). Truncated outputs fail with `truncated`; refusal regex hits
do not veto extraction.

`evaluate_numeric(response, gold, truncated=False)` compares the literal value
with the gold value exactly. **No unit conversion is applied**, so an
equivalent quantity in another unit is a mismatch and a right number with a
wrong unit can match. Suffixes outside the canonical unit and aliases are
flagged `unvalidated_suffix`. This is not semantic or dimensional accuracy.

`cmi(tagged_tokens)` uses CMI = 100 × (1 − max(hi,en)/(N−U)), or zero when N=U,
for supplied `(token, tag)` pairs with `hi`, `en`, `univ` tags. `analyze_tags`
returns counts and switch points; switches compare consecutive language-bearing
tokens, skipping `univ`. The formula follows the Gambäck & Das (2014/2016)
definition specified in the handoff. `heuristic_tag` and the CLI use tiny
wordlists, mark numbers/punctuation/known or supplied names as `univ`, and
default unknown/overlapping words to `univ`. Their editable JSON is explicitly
**HEURISTIC — NOT GOLD; HUMAN CORRECTION REQUIRED**. Human token/tag correction,
name identification and borrowing-policy decisions are necessary before using
the result as annotated CMI. The CLI refuses existing output files.

`format_fixtures.json` contains 12 newly authored, unreviewed synthetic families
and 36 E/R/C texts, all `FMT2-` and `EXCLUDED_FORMAT_FIXTURE`. Gold fields follow
the pilot gold schema. All source/template IDs, renderings and descendants stay
excluded from confirmatory training and final testing. The fixture container
has its own schema: it is not an accepted pilot dataset or a smoke-notebook
adapter. No model was run; language equivalence/naturalness remain unvalidated.

## FMT2 format test notebook (decision D019)

`Hinglish_FMT2_Format_Test_Colab.ipynb` is self-contained. Upload it to Colab, select a T4 GPU and choose Run all. It runs the 36 excluded fixture prompts through the unchanged Test 1 engine, frozen prompt and Qwen3-4B recipe in two demo-mode parts of six families each. It reports scorer v1.0.0 beside numeric_literal_v1 and downloads `FMT2_format_test_results.zip`. This is development evidence only. Rebuild with `python3 -B secondary_analysis/build_format_notebook.py` after any source change; `tests/test_format_notebook.py` fails if the notebook is stale.
