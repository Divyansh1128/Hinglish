# Phase-2 training runs: log of returned ZIPs

The adapter weights stay on Drive; their hashes are recorded below. **DEV numbers are sanity checks only** (pre-registration §5). They never select checkpoints, hyperparameters, arms or reruns.

| Run | Attempt | ZIP SHA-256 | Valid for gate | Steps / skips | Median s/update | Adapter model SHA-256 | DEV E / R / C (of 40) | DEV invalid | Mean output tokens |
|---|---|---|---|---|---|---|---|---|---|
| EC-s11 | 1 | `c1b5b252…7c99` | yes | 60/60, 0 | 20.66 | `fd29387d…46e4` | 24 / 13 / 19 | 23/120 | 43 |
| ER-s11 | 1 | `ec51cd46…4189` | yes | 60/60, 0 | 19.18 | `58c0b7ec…b722` | 23 / 12 / 17 | 25/120 | 44 |
| EE-s11 | 1 | `207c3dde…93d8` | yes | 60/60, 0 | 20.59 | `05da095e…bb74` | 25 / 15 / 17 | 23/120 | 46 |
| *Unchanged baseline* | – | `1c0d2609…ffef` | – | – | – | – | 33 / 19 / 24 | 12/120 | 121 |

## Observation after the first adapter (DEV sanity, descriptive)

The E+C seed-11 adapter writes much shorter answers than the unchanged model: a mean of 43 vs 121 output tokens. That is the length of the terse frozen `reference_solution_en` targets. On DEV it is less accurate than the unchanged model in every form. It also ends with a unit more often, and with words such as `pounds` or `g` that the strict scorer does not accept for the gold unit (invalid_unit 18 vs 8).

This follows from the pre-registered design: all three arms train on the identical English targets. It is not an implementation fault: the run is valid, with 60/60 steps, no scaler skips, exact hashes and the registered recipe. Under §5 and §13 nothing changes. The primary contrast Δ_C (E+C vs E+R) compares arms trained on the same targets. A loss against the unchanged model is reported through the pre-registered English-retention flags (EC − unchanged) and as a limitation of the training targets. See D050.

- **Pairing check (seed 11):** EC, ER and EE share data order `be9aa90b…` and initial adapter `0bbfaad4…`, as §3 requires.
