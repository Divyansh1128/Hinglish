# Pilot-B results summary (70 families × E/R/C, strict scorer v1.0.0)

Pre-registered plan: `pilot_b/PREREGISTRATION.md`. Single-reviewer frozen data (D035); reported separately from the original 30-family pilot. Accuracy with Wilson 95% intervals; paired differences use a 10,000-resample family bootstrap (seed 101).

| Model | E | R | C | E−R (pp) | E−C (pp) | R−C (pp) |
|---|---|---|---|---|---|---|
| Qwen3-4B (primary) | pending | pending | pending | | | |
| Qwen3-8B | 98.6 [92.3, 99.7] | 91.4 [82.5, 96.0] | 98.6 [92.3, 99.7] | +7.1 [0.0, +14.3] | 0.0 [−4.3, +4.3] | −7.1 [−14.3, 0.0] |
| Llama-3.2-3B | 94.3 [86.2, 97.8] | 57.1 [45.5, 68.1] | 70.0 [58.5, 79.5] | +37.1 [+24.3, +50.0] | +24.3 [+11.4, +37.1] | −12.9 [−27.1, +1.4] |

Per-model details: `qwen3-8b/RESULTS.md`, `llama-3.2-3b/RESULTS.md`.
