# Pilot-B results summary (70 families × E/R/C, strict scorer v1.0.0)

Pre-registered plan: `pilot_b/PREREGISTRATION.md`. Single-reviewer frozen data (D035); reported separately from the original 30-family pilot. Accuracy in % with Wilson 95% intervals; paired differences in percentage points with a 10,000-resample family bootstrap (seed 101). All three runs COMPLETE (210/210), with checksums verified.

| Model | E | R | C | E−R | E−C | R−C |
|---|---|---|---|---|---|---|
| **Qwen3-4B** (primary) | 94.3 [86.2, 97.8] | 85.7 [75.7, 92.1] | 94.3 [86.2, 97.8] | +8.6 [−1.4, +18.6] | 0.0 [−7.1, +7.1] | −8.6 [−15.7, −1.4] |
| Qwen3-8B | 98.6 [92.3, 99.7] | 91.4 [82.5, 96.0] | 98.6 [92.3, 99.7] | +7.1 [0.0, +14.3] | 0.0 [−4.3, +4.3] | −7.1 [−14.3, 0.0] |
| Llama-3.2-3B | 94.3 [86.2, 97.8] | 57.1 [45.5, 68.1] | 70.0 [58.5, 79.5] | +37.1 [+24.3, +50.0] | +24.3 [+11.4, +37.1] | −12.9 [−27.1, +1.4] |

## Findings (descriptive; 70 families is a diagnostic sample)
1. **R (Romanized Hindi) is the weakest form for all three models.** The size of the gap depends strongly on the model: about 7–9 points for Qwen, 37 for Llama.
2. **C (Hinglish) is not harder than E for Qwen** (difference 0.0 for both sizes), and is better than R; for Qwen3-4B the R−C interval excludes 0. For Llama, C is in between.
3. **Scale helps within the Qwen family:** 4B→8B improves every form, but the R deficit stays (8.6 → 7.1 pp).
4. **The operation-word hypothesis (bhaag/bhinn-type misreading) does not explain the gap:** R errors are spread across families with and without Hindi operation words, for all models.
5. **Formatting confounds remain visible at the margins:** English unit phrases (`years old`, `bags of cement`) and an unlisted spelling (`rupye`) cost Qwen3-4B 4 strict points. The pre-registered numeric endpoint has a specification gap for a trailing `₹`. Both are reported as such and not corrected post hoc.
6. **Exploratory (Llama):** reasoning in romanized-Hindi prose goes with lower accuracy on C (48% against 84%). This needs the planned English-compliance audit.
