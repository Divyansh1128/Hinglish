# Sol independent verification — Phase-2 FINAL_TEST

Date: 10 November 2026. Scope: independently verify the stored strict scores, checkpoint accuracies, primary paired-family bootstrap, decision label, duplicate protection and disclosed evaluation infrastructure events. **The primary result agrees: Δ_C = −4.33 pp [−8.00, −0.67], Harm.** No numerical or scored-attempt discrepancy was found. An additional launch-log disclosure detail is recorded below.

## Independent method and reproducibility

- Wrote and ran `/tmp/sol_verify_final_test.py`, using only the Python standard library. It extracts the outer ZIP into a fresh `/tmp` temporary directory, reads each of the ten inner `*_results.zip` files, and computes outcomes from `predictions.csv`'s strict `correct` column (`True`/`False`). It does not use the numeric diagnostic endpoints or archived aggregate metrics to calculate accuracy.
- No project module was imported. `phase2_analysis/analyze.py` was neither read nor imported. Statistical mechanics came from `phase2/PREREGISTRATION.md` §§6–8 and Amendment 1 items 2 and 4. Only the matrix-hash serialization convention was consulted in `phase2_analysis/tests/test_analyze.py:634–635`: comma-separated index rows, each ending with LF.
- Families sorted by ID (`FT001` … `FT100`). A fresh `random.Random(101)` generates exactly 10,000 rows of 100 `randrange(100)` draws in row-major order. The same matrix is reused for the primary and per-seed intervals. Each family retains its three paired seed contrasts; family–seed rows are never sampled independently.
- Contrasts and quantiles use exact rational arithmetic: seed-summed integer contrasts divided by three; linear interpolation at `h = 9999p`, for `p = 0.025, 0.975`. The decision uses unrounded bounds and checks the degeneracy override first.
- Independent runtime: Python **3.14.5** (reported original analysis: Python 3.12.7). The matrix hash and numerical results agree across these runtimes.

Reproduction command (reads repository inputs; writes its JSON output only under `/tmp`):

```sh
python3 /tmp/sol_verify_final_test.py '/Users/divyanshraj/Major Project' > /tmp/sol_verify_final_test.json
```

| Artifact | SHA-256 |
|---|---|
| Outer `Phase2_FinalTest_results.zip` | `fb4a71ccb22d8d4f274ec3c94c0b7455f870aebe7fcc673d18e47632a0024f9a` |
| Independent `/tmp/sol_verify_final_test.py` | `ef540d254dee00e85620e238d5582cfebd44bdc41de37c594552d4838a8bee4a` |
| Bootstrap matrix (CSV rows with final LF) | `33f4920eab5738cf29b346be8d63a15115f9fcbda58699ee9fc44b031e46e6a1` |

The script and JSON are temporary local artifacts, not repository additions.

## Agreement table: strict accuracy

Each entry below is correct/100, equivalently percent accuracy. Both reported and independently computed values are shown in E/R/C order. All **30 counts, 30 percentages and 30 Wilson 95% intervals** match the strict checkpoint table in `results/phase2/final_test/phase2_analysis.md`; Wilson intervals were independently calculated over 100 outcomes per checkpoint and form.

| Checkpoint | Reported E / R / C (%) | Independent E / R / C (%) | Agreement |
|---|---|---|---|
| EE:11 | 62 / 41 / 44 | 62 / 41 / 44 | Exact |
| EE:22 | 63 / 41 / 41 | 63 / 41 / 41 | Exact |
| EE:33 | 59 / 39 / 44 | 59 / 39 / 44 | Exact |
| ER:11 | 61 / 42 / 44 | 61 / 42 / 44 | Exact |
| ER:22 | 56 / 35 / 47 | 56 / 35 / 47 | Exact |
| ER:33 | 61 / 37 / 50 | 61 / 37 / 50 | Exact |
| EC:11 | 64 / 43 / 41 | 64 / 43 / 41 | Exact |
| EC:22 | 58 / 41 / 46 | 58 / 41 / 46 | Exact |
| EC:33 | 54 / 40 / 41 | 54 / 40 / 41 | Exact |
| Unchanged | 85 / 63 / 66 | 85 / 63 / 66 | Exact |

## Agreement table: primary inference

E+C has 128 strict-correct C outcomes across the three seeds, versus 141 for E+R: seed-mean accuracies 42⅔% and 47%. Thus `Δ_C = (128 − 141)/300 = −13/300` as a proportion, or −4⅓ pp. The bootstrap resamples the 100 seed-averaged family contrasts, rather than these 300 individual outcomes.

| Quantity | Reported | Independent | Agreement |
|---|---|---|---|
| Primary Δ_C | −4.33 pp | −4.333333333333… pp (`−13/300`) | Exact, rounded as reported |
| 95% bootstrap interval | [−8.00, −0.67] pp | [−8, −2/3] pp; proportions [`−2/25`, `−1/150`] | Exact |
| Decision | Harm | Harm: unrounded `U = −1/150 < 0` | Exact |
| Non-zero / distinct family contrasts | 24 / 5 | 24 / 5 | Exact |
| Degenerate | False | False (contrasts vary; interval width > 0) | Exact |
| Bootstrap tails ≤0 / ≥0 | 9921 / 120 of 10000 | 9921 / 120 of 10000 | Exact |
| Bootstrap tails ≤+5 / ≥+5 pp | 10000 / 0 of 10000 | 10000 / 0 of 10000 | Exact |
| Wald 95% | [−8.01, −0.66] pp | [−8.0074316434, −0.6592350232] pp | Matches rounding |
| Hoeffding 95% | [−31.50, +22.83] pp | [−31.4953636481, +22.8286969815] pp | Matches rounding |
| Seed 11 Δ_C [bootstrap] | −3.00 [−9.00, +3.00] pp | −3 [−9, +3] pp | Exact |
| Seed 22 Δ_C [bootstrap] | −1.00 [−8.00, +6.00] pp | −1 [−8, +6] pp | Exact |
| Seed 33 Δ_C [bootstrap] | −9.00 [−17.00, −2.00] pp | −9 [−17, −2] pp | Exact |
| Matrix SHA-256 | `33f4920e…e46e6a1` | Same full hash as above | Exact |

The Wald check uses sample SD (ddof 1) and `z = 1.959963984540054`; Hoeffding uses range [−1, 1], radius `2√(log(40)/200)`, and clipping. The primary interval is conditional on the retained trained checkpoints; this check does not add uncertainty for training-seed variation.

## Completeness and duplication checks

- Exactly ten expected inner result archives: unchanged plus EE/ER/EC × seeds 11/22/33. Every run has 300 prediction rows, 300 distinct rendering IDs, and exactly one row for each of the expected 100 families × E/R/C. Total: **3,000 scored predictions**, with no duplicate rendering within a run.
- Every run has exactly 300 committed `generated` journal records, also one per family/form. Prediction attempt IDs are unique and point to the corresponding successful journal record; family/form, input text, raw response and strict correctness agree. No committed response appears twice for a rendering.
- All ten prediction-file hashes differ; all ten full response-set fingerprints differ. No run's prediction file or complete generated-response set was copied from another run.
- Outer expanded copies of each `predictions.csv` and `generation_attempts.jsonl` are byte-identical to the respective inner-ZIP copy. They are duplicate export representations of the same run, not additional observations, and were counted only once.
- All manifests and exported status files say COMPLETE, 300/300, unresolved 0, with matching journal attempt counts. The current inner-ZIP hashes agree with their exported status records.

## Infrastructure disclosure check

The generation journals, `errors.jsonl`, status records and `*_lock_recoveries.jsonl` agree with `results/phase2/final_test/README.md`:

| Run | Independent journal finding | Recovery evidence (10 Nov, UTC) | README agreement |
|---|---|---|---|
| EC-s22 | 301 attempts; 300 generated; 1 infrastructure failure, FT011/R | 03:21:37.978557; 278 records kept | Yes |
| EE-s33 | 301 attempts; 300 generated; 1 infrastructure failure, FT100/R | 03:28:08.427776, 6 records kept; 05:41:58.278966, 297 records kept | Yes |
| Other eight runs | 300 attempts; 300 generated; 0 infrastructure failures each | No recovery records | Yes |

Both failure records have `error_code = interrupted_before_commit`, `raw_response = null`, and attempt number 1. Each is followed by exactly one successful attempt number 2 for that family/form, with the same configuration hash. Neither failed record contributes a scored prediction. All three lock recoveries record `operator_confirmed_no_active_writer = true`. The archived evidence is consistent with Amendment 2 item 5 and with preserving stored responses.

**Additional disclosure detail:** the top-level `attempts.jsonl` records seven evaluation-process invocations with exit code 1 (two EC-s22, five EE-s33). `log.txt` contains six explicit stale-lock `ValueError` tracebacks. The README summarizes journal-level failures and recoveries, and does not enumerate these seven unsuccessful process launches. The export does not explicitly explain the remaining nonzero process exit; its cause cannot be independently established here. These launch counts must not be mistaken for seven failed generations: the journals contain only the two disclosed infrastructure-failure records, and no extra committed responses. This is a disclosure-granularity caveat, not a numerical discrepancy.

Artifact inspection cannot establish what happened outside the stored journals, or independently prove the physical cause of a Colab disconnect. It does establish one stored successful response per rendering and agreement of all disclosed journal failure/recovery counts.

## Disposition

**Verified within scope.** The requested strict accuracy and primary bootstrap results agree, and the registered rule maps the unrounded bounds to Harm without a degeneracy override. No change to the analysis is indicated by this verification. Secondary numeric endpoints and a full freeze/environment provenance audit were outside this task.

Only this new handoff file was added to the repository; no other repository file was modified and no commit was made.
