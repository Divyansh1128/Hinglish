# Original-pilot cohort (24 families) — Qwen3-4B

Pre-registered plan: `pilot_original/PREREGISTRATION.md` (with Amendment 1, D037). Frozen data (`pilot_original/FROZEN.md`), prompt v2, scorer v1.0.0. **COMPLETE 72/72**; checksums verified; tables reproduce the stored metrics. Returned ZIP SHA-256 `ff2af2bfd51d3ae301e2c6549f390c8953501c199fe5255ed7a76a19865cab37`. Reported separately from Pilot-B; never pooled.

| Form | Strict correct | Accuracy | Wilson 95% CI |
|---|---:|---:|---:|
| E | 24/24 | 100.0% | [86.2, 100.0] |
| R | 22/24 | 91.7% | [74.2, 97.7] |
| C | 24/24 | 100.0% | [86.2, 100.0] |

Paired: E−R +8.3 pp [0.0, +20.8] (2/0); E−C 0.0 [0.0, 0.0]; R−C −8.3 pp [−20.8, 0.0] (0/2).

- No strict-invalid outputs; numeric_literal_v1 agrees on all 72.
- R errors: PIL001-R answered 41 (gold 31): "Riya se 5 kam" treated as addition, an operation-word (*kam*) misreading. PIL028-R answered 50/9 cm (wrong value).
- Same direction as Pilot-B Qwen3-4B (E 94.3 / R 85.7 / C 94.3): R lowest, C = E. Descriptive; 24 families.
