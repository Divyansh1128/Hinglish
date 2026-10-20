# Pilot-B results — Qwen3-4B (primary backbone)

Run on a Colab T4 under the pre-registered plan (`pilot_b/PREREGISTRATION.md`): frozen data, prompt v2, scorer v1.0.0. **COMPLETE: 210/210**; all checksums verified; tables reproduce the stored metrics. Returned ZIP SHA-256 `7d9274d4af0d4c7599cb68f8353ee6cd695a5d8acd2c22a5facd738f7076e7c5`. Full tables: `pilotb-Qwen3-4B/tables.md`.

## Primary endpoint (strict)

| Form | Strict correct | Accuracy | Wilson 95% CI |
|---|---:|---:|---:|
| E | 66/70 | 94.3% | [86.2, 97.8] |
| R | 60/70 | 85.7% | [75.7, 92.1] |
| C | 66/70 | 94.3% | [86.2, 97.8] |

| Paired contrast | Difference | Bootstrap 95% interval | Discordant (first only / second only) |
|---|---:|---:|---:|
| E−R | +8.6 pp | [−1.4, +18.6] | 9 / 3 |
| E−C | 0.0 pp | [−7.1, +7.1] | 3 / 3 |
| R−C | **−8.6 pp** | **[−15.7, −1.4]** | 1 / 7 |

- R is the weakest form. C is not worse than E; C beats R in 7 families against 1, with the interval excluding 0.
- Strict-invalid: 6 (E 3, R 2, C 1), all `invalid_unit`. **Three of E's four failures are formatting**, with numerically right answers given English unit phrases outside the aliases: `11 years old`, `13 years old`, `4 bags of cement`. One C failure is the form-dependent spelling penalty predicted in the pre-pilot review: `300 rupye` is not a listed alias.
- Operation-word strata (descriptive): R is 89% (keep), 82% (switch) and 86% (no operation word), so the R errors are not concentrated in operation-word families.
- Secondary numeric_literal_v1: E 72.9 / R 82.9 / C 82.9%. As with Qwen3-8B, all 30 strict-correct/numeric-fail cases are a trailing rupee symbol (`2125 ₹`), a gap in the frozen secondary grammar; see `qwen3-8b/RESULTS.md`.

## Reading

Qwen3-4B shows a modest R deficit (E−R +8.6 pp, interval crossing 0) and C ≈ E. Within the Qwen family, 4B→8B raises R from 85.7% to 91.4% and E/C from 94.3% to 98.6%.
