# Phase-2 FINAL_TEST results (confirmatory, S = 3)

- `Phase2_FinalTest_results.zip`: the sealed export from `Phase2_FinalTest.ipynb`. All 10 runs are COMPLETE (300/300, 0 unresolved), all checksums are OK and the gate passed CONFIRMATORY (S = 3).
- `phase2_analysis.md` / `.json`: the unchanged pre-registered analysis (`phase2_analysis/analyze.py` SHA-256 `11d6f1c8…`). It was run once on 10 Nov 2026 with the frozen inputs.

## Primary result

**Δ_C (E+C − E+R, strict accuracy on C) = −4.33 pp, 95% paired family bootstrap [−8.00, −0.67].** The decision label is **Harm** (U < 0). All three seeds are negative (−3, −1, −9 pp). numeric_literal_v1/v2 agree in sign (−5.67 pp [−11.00, −0.67]).

Descriptive: every fine-tuned arm is far below the unchanged model in every form. On English, strict accuracy is 54–64 % vs 85 %, and the English-retention flags show "loss beyond margin" for EC, ER and EE against the unchanged model. Outputs are about 42 tokens vs about 110. This matches the DEV observation in D050: the terse reference-solution targets shorten the answers and raise unit errors.

## Infrastructure events (disclosed; allowed by Amendment 2 item 5)

| Run | Event | Effect |
|---|---|---|
| EC-s22 | Stale RUNNING.lock recovered on 10 Nov 03:21 UTC; 278 journal records kept | 301 attempts / 300 completed, 1 infrastructure failure |
| EE-s33 | Stale RUNNING.lock recovered on 10 Nov 03:28 UTC (6 records kept) and 05:41 UTC (297 records kept) | 301 attempts / 300 completed, 1 infrastructure failure |

The stale locks came from Colab runtimes that disconnected; no response was regenerated. The results-ZIP and checksum hashes printed in different sessions differ only because each session re-exports the derived summaries; each secondary-diagnostic folder gets a random name. The generated responses are fixed by the journal.

**Process launches (from Sol's verification):** the top-level `attempts.jsonl` records seven evaluation-process launches with exit code 1 (two for EC-s22, five for EE-s33). Six were refusals because a stale lock existed (`ValueError` in `log.txt`), raised before any generation. The seventh has no recorded cause, most likely a runtime that disconnected. These were process launches, not generations: the journals hold exactly the two infrastructure-failure records above and one committed response per rendering.

## Independent verification

Sol recomputed the result with an independent stdlib-only script: `handoffs/2026-11-10_sol_verify_final_test.md`. All 30 strict accuracies and Wilson intervals, Δ_C = −13/300, the bootstrap bounds [−2/25, −1/150], the tails, the matrix hash and the label Harm match exactly. There are no duplicate renderings.
