# Original-pilot cohort summary (24 families × E/R/C, strict scorer v1.0.0)

Pre-registered: `pilot_original/PREREGISTRATION.md` (Amendment 1, D037). Review provenance: mathematics solved independently by two humans; language review by one human plus adjudicator; R01's AI-prefilled stage-2 judgments excluded. **Reported separately from Pilot-B; never pooled.** All runs COMPLETE (72/72), with checksums verified and zero strict-invalid outputs.

| Model | E | R | C | E−R | E−C | R−C |
|---|---|---|---|---|---|---|
| Qwen3-4B (primary) | 100.0 [86.2, 100.0] | 91.7 [74.2, 97.7] | 100.0 [86.2, 100.0] | +8.3 [0.0, +20.8] | 0.0 [0.0, 0.0] | −8.3 [−20.8, 0.0] |
| Qwen3-8B | 100.0 [86.2, 100.0] | 95.8 [79.8, 99.3] | 100.0 [86.2, 100.0] | +4.2 [0.0, +12.5] | 0.0 [0.0, 0.0] | −4.2 [−12.5, 0.0] |
| Llama-3.2-3B | 87.5 [69.0, 95.7] | 62.5 [42.7, 78.8] | 91.7 [74.2, 97.7] | +25.0 [+4.2, +45.8] | −4.2 [−16.7, +8.3] | −29.2 [−45.8, −12.5] |

## Pre-specified descriptive comparison with Pilot-B (no pooling, no tests)
The direction replicates for every model: **R is the lowest form; C is at or near E.** Qwen is near ceiling in this cohort (easier items; E 100%). Llama's R deficit replicates (Pilot-B E−R +37.1; cohort +25.0), and in this cohort C matches E for Llama too (Pilot-B: C 70.0%). Zero-width intervals at ceiling are not evidence of population equivalence.
