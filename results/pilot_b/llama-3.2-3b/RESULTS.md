# Pilot-B results — Llama-3.2-3B-Instruct (first real evaluation)

Run 16 October 2026 on a Colab T4. Pre-registered plan: `pilot_b/PREREGISTRATION.md`. Frozen data, prompt v2, scorer v1.0.0. **COMPLETE: 210/210** renderings; all checksums verified; tables reproduce the stored metrics exactly. Returned ZIP SHA-256 `08120040e841b1208f708a83ceec145c02316e2352d1bc8b7a0a29ae39792458`. Full tables: `pilotb-Llama-3.2-3B-Instruct/tables.md`; figures in `.../figures/`.

Pilot-B is single-reviewer data (D035) and is reported separately from the original 30-family pilot.

## Pre-registered endpoints

| Form | Strict correct | Accuracy | Wilson 95% CI |
|---|---:|---:|---:|
| E | 66/70 | 94.3% | [86.2, 97.8] |
| R | 40/70 | 57.1% | [45.5, 68.1] |
| C | 49/70 | 70.0% | [58.5, 79.5] |

| Paired contrast | Difference | Bootstrap 95% interval | Discordant (first only / second only) |
|---|---:|---:|---:|
| E−R | +37.1 pp | [+24.3, +50.0] | 28 / 2 |
| E−C | +24.3 pp | [+11.4, +37.1] | 21 / 4 |
| R−C | −12.9 pp | [−27.1, +1.4] | 10 / 19 |

- Secondary numeric_literal_v1 agrees with strict scoring on all 210 renderings, so the gaps are **not formatting**. 11 strict-invalid outputs in total (E 1, R 6, C 4); 7 are truncations (R 5, C 2).
- **Operation-word strata (descriptive, endpoint 5):**

| Stratum | Families | E | R | C |
|---|---:|---:|---:|---:|
| Hindi op-word in R, C keeps it | 18 | 100% | 67% | 72% |
| Hindi op-word in R, C switches it | 17 | 94% | 59% | 65% |
| No Hindi op-word | 35 | 91% | 51% | 71% |

  The R drop is **not concentrated** in families with Hindi operation words. R is lower across all strata, so the operation-word misreading hypothesis does not explain most of the R gap for this model.

## Exploratory (not pre-registered; heuristic language detection)

- Llama explains in romanized-Hindi prose for 60/70 R and 27/70 C outputs, despite the English instruction (E: 0/70). No Devanagari.
- C outputs explained in Hindi prose were correct 13/27 (48%) against 36/43 (84%) for English explanations; R: 35/60 against 5/10. This is **observational**: harder items may both trigger Hindi explanations and cause errors. The English-compliance audit (endpoint 6) is needed before any claim.
- Many R errors are arithmetic slips on simple problems (e.g. PB017: 1200 − 3×265 = 405, model answered 435).

## Reading

On this model, the E→R gap is large (about 37 points, interval well above zero) and C sits between E and R. 70 families is a diagnostic sample. Compare with Qwen3-4B (primary) and Qwen3-8B once they are returned.
