# Pilot-B results — Qwen3-8B

Run on a Colab T4 under the pre-registered plan (`pilot_b/PREREGISTRATION.md`): frozen data, prompt v2, scorer v1.0.0. **COMPLETE: 210/210**; all checksums verified; tables reproduce the stored metrics. Returned ZIP SHA-256 `3d1cef58a01116caf7a81f8ace5b641096034735b3e9655267f501ac62455180`. Full tables: `pilotb-Qwen3-8B/tables.md`.

## Pre-registered endpoints

| Form | Strict correct | Accuracy | Wilson 95% CI |
|---|---:|---:|---:|
| E | 69/70 | 98.6% | [92.3, 99.7] |
| R | 64/70 | 91.4% | [82.5, 96.0] |
| C | 69/70 | 98.6% | [92.3, 99.7] |

| Paired contrast | Difference | Bootstrap 95% interval | Discordant (first only / second only) |
|---|---:|---:|---:|
| E−R | +7.1 pp | [0.0, +14.3] | 6 / 1 |
| E−C | 0.0 pp | [−4.3, +4.3] | 1 / 1 |
| R−C | −7.1 pp | [−14.3, 0.0] | 1 / 6 |

Operation-word strata (descriptive): R is 94% (keep), 94% (switch) and 89% (no operation word); C is 94–100% in every stratum. All 6 R errors are in R; no stratum concentrates them.

## Secondary endpoint: specification gap (reported as pre-registered)

numeric_literal_v1 gives E 84.3%, R 74.3%, C 80.0%, below strict. All 36 renderings that strict scores correct but numeric does not are amounts written with a **trailing rupee symbol** (`FINAL: 1575 ₹`). Strict v1.0.0 accepts ₹ as a unit, while the frozen numeric grammar accepts only letter-word suffixes, so these become `unsupported_answer`. The gap is in the secondary endpoint's specification, not in the model. Strict, the primary endpoint, is unaffected. **Post-hoc sensitivity (not pre-registered):** treating a trailing ₹ as an allowed suffix makes numeric agree with strict on all 36. The only other disagreement is PB065-E, `11 years old.`, which strict rejects as an invalid unit although the value is right.

## Reading

Qwen3-8B is near ceiling on E and C, with a modest R deficit (+7.1 pp, interval touching 0). Contrast Llama-3.2-3B (E 94.3 / R 57.1 / C 70.0): the R gap is very model-dependent. Primary Qwen3-4B pending.
