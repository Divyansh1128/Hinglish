# Phase-2 pre-registered analysis — FINAL_TEST

Analysis `phase2_analysis 3.1.0 (Amendments 1-3)`; plan `phase2/PREREGISTRATION.md sections 6-8 as amended by Amendment 1 (b4fb956, D045), Amendment 2 (17986d4, D046) and Amendment 3 (7e84654, D047)`.
Dataset SHA-256 `da89dd9a626e438dffca39e3a74c4c8abac6bb57501495723b87e6ee143f3d46` (FINAL_TEST); 100 families; seeds 11, 22, 33 (S = 3); base `Qwen/Qwen3-4B`.
Status: **COMPLETE**. Analysis type: **confirmatory (S = 3, retained seeds from the freeze)**. Python 3.12.7.

Checkpoints, retained seeds and S from `phase2/ADAPTERS_FROZEN.md` (SHA-256 `1bebf10d708620b2b8f5c11aac340ca76b12e4c990dbfff9dcc82a8f9f20929f`): slot→seed 11→11, 22→22, 33→33; S = 3; confirmatory True. Implementation manifest `phase2/IMPLEMENTATION_MANIFEST.md` (SHA-256 `726241c5726aaba2c51fc027866dd572abfc13d02ef9235d1901af87a9f5b43d`); unchanged-DEV baseline results ZIP `a8194ac29cb17711d8e8e526835daacc368fdc4b5265f51d41f96edff347171a` (verified: 120 resolved unchanged-model generations; the ceiling-risk count is derived from it). Every run's adapter and hashes, model, mode, instruction, engine sources, configuration, backend and attempt budget were checked against them (Amendment 2 item 7), and every run and session's T4 hardware, gpu_verified, attention/dtype/quantization, pinned package versions and execution digest (Amendment 3 item 3).


## Inputs

| Checkpoint | Run ID | Status | Completed | Unresolved | Attempts | Source |
|---|---|---|---:|---:|---:|---|
| EE:11 | `phase2_final_test-3ede70f24b4a42c4935888926123f192` | COMPLETE | 300/300 | 0 | 300 | zip |
| EE:22 | `phase2_final_test-3fc3f2cf06524aac953870f34ac56cc7` | COMPLETE | 300/300 | 0 | 300 | zip |
| EE:33 | `phase2_final_test-79f763077420466ebdec1682c22437a2` | COMPLETE | 300/300 | 0 | 301 | zip |
| ER:11 | `phase2_final_test-1291f3910db9410287733ca0763746ac` | COMPLETE | 300/300 | 0 | 300 | zip |
| ER:22 | `phase2_final_test-ec9f9c427c1841c68e1236ec44567f5e` | COMPLETE | 300/300 | 0 | 300 | zip |
| ER:33 | `phase2_final_test-62858c148afd44e7a2de44aeb46be288` | COMPLETE | 300/300 | 0 | 300 | zip |
| EC:11 | `phase2_final_test-11b4206dc26e4249a3660bf268955419` | COMPLETE | 300/300 | 0 | 300 | zip |
| EC:22 | `phase2_final_test-d28adcc7cc5a49b4b6c18906092cdd12` | COMPLETE | 300/300 | 0 | 301 | zip |
| EC:33 | `phase2_final_test-e3c4af4c860e456eb7f9f6853c8173a8` | COMPLETE | 300/300 | 0 | 300 | zip |
| unchanged | `phase2_final_test-627d68ad676f426c8c698c0258d433d6` | COMPLETE | 300/300 | 0 | 300 | zip |

## Primary: Δ_C (strict, E+C − E+R on C)

- Δ_C = -4.33 pp [-8.00, -0.67] (95% paired family bootstrap, 10,000 resamples, seed 101; matrix SHA-256 `33f4920eab5738cf29b346be8d63a15115f9fcbda58699ee9fc44b031e46e6a1`).
- Precision: bootstrap half-width 3.67 pp.
- E+R C headroom (1 − mean y_ER,C): 53.00 pp.
- **Decision label: Harm** (from unrounded bounds L = -2/25, U = -1/150 as proportions).
- Wald 95%: [-8.01, -0.66] pp; Hoeffding 95% (clipped to [−1, 1]): [-31.50, +22.83] pp (radius 27.2 pp).
- Non-zero family contrasts: 24/100; distinct d_i values: 5; degenerate: False.
- Bootstrap tails: ≤ +0 pp: 9921/10000, ≥ +0 pp: 120/10000; ≤ +5 pp: 10000/10000, ≥ +5 pp: 0/10000.

High unchanged-DEV accuracy (ceiling-risk proxy): unchanged DEV C 24/40 (60.0%; Wilson 95% 44.6–73.7; DEV headroom 40.0 pp); threshold >= 38/40: **not fired**. Source of k: derived: strict-correct C count of the frozen unchanged-model DEV baseline results ZIP (SHA-256 a8194ac29cb17711d8e8e526835daacc368fdc4b5265f51d41f96edff347171a, run phase2_dev-b0d6a0eab0de48edbd251d5703c81ec8, 120 resolved generations). A proxy from the unchanged model on DEV; it does not establish a ceiling for the trained comparator. Δ_C stays first in the report and S2 stays descriptive.

Approximate interval conditional on the trained checkpoints; does not cover training-seed variance. The 100-family mean is a finite-set descriptive quantity; intervals describe hypothetical independent families from this fixed authoring and review process (template and author dependence is a limitation). Δ_C is the effect of the complete training-rendering recipe, not an isolated effect of code-switching (Amendment 1 item 3).

## S2: R transfer (descriptive)

- T_R (E+R − E+E on R) = -2.33 pp [-9.33, +4.33]
- Δ_R (E+C − E+R on R) = +3.33 pp [-2.00, +8.67]

## S1: English retention (descriptive flags; margin −2 pp)

| Estimand | Estimate [95% bootstrap] | Non-zero | Flags |
|---|---|---:|---|
| S1 English retention: E+C − E+E on E | -2.67 pp [-7.00, +1.33] | 22 | no retention criterion met |
| S1: E+C − unchanged on E | -26.33 pp [-34.33, -19.00] | 37 | loss detected; loss beyond margin |
| S1: E+R − E+E on E | -2.00 pp [-6.33, +2.33] | 26 | no retention criterion met |
| S1: E+R − unchanged on E | -25.67 pp [-33.67, -18.00] | 38 | loss detected; loss beyond margin |
| S1: E+E − unchanged on E | -23.67 pp [-31.67, -16.33] | 38 | loss detected; loss beyond margin |

Flags are independent descriptive criteria, not multiplicity-controlled non-inferiority.

## S3: specificity (descriptive)

- Δ_C − Δ_R per family = -7.67 pp [-14.67, -1.33] (Hoeffding radius 54.3 pp for values in [−2, 2], clipped)

All secondary contrasts, numeric endpoints and per-seed McNemar p-values are descriptive; no Holm or other inferential secondary analysis (Amendment 1 item 5).

## All estimands, all endpoints

| Estimand | strict | numeric_literal_v1 | numeric_literal_v2 |
|---|---|---|---|
| Primary: E+C − E+R on C | -4.33 pp [-8.00, -0.67] | -5.67 pp [-11.00, -0.67] | -5.67 pp [-11.00, -0.67] |
| S1 English retention: E+C − E+E on E | -2.67 pp [-7.00, +1.33] | -1.67 pp [-6.33, +2.67] | -1.67 pp [-6.33, +2.67] |
| S1: E+C − unchanged on E | -26.33 pp [-34.33, -19.00] | -13.67 pp [-20.33, -7.00] | -13.67 pp [-20.33, -7.00] |
| S1: E+R − E+E on E | -2.00 pp [-6.33, +2.33] | -3.67 pp [-8.00, +0.67] | -3.67 pp [-8.00, +0.67] |
| S1: E+R − unchanged on E | -25.67 pp [-33.67, -18.00] | -15.67 pp [-23.00, -8.67] | -15.67 pp [-23.00, -8.67] |
| S1: E+E − unchanged on E | -23.67 pp [-31.67, -16.33] | -12.00 pp [-18.67, -6.00] | -12.00 pp [-18.67, -6.00] |
| S2 R transfer: E+R − E+E on R | -2.33 pp [-9.33, +4.33] | -0.33 pp [-7.67, +7.00] | -0.33 pp [-7.67, +7.00] |
| S2: E+C − E+R on R | +3.33 pp [-2.00, +8.67] | +1.67 pp [-4.67, +8.00] | +1.67 pp [-4.67, +8.00] |
| Δ_C − Δ_R per family (specificity) | -7.67 pp [-14.67, -1.33] | -7.33 pp [-14.67, -0.33] | -7.33 pp [-14.67, -0.33] |

| Estimand (strict) | Non-zero families | Degenerate | Wald 95% | Hoeffding 95% | Bootstrap tails |
|---|---:|---|---|---|---|
| Primary: E+C − E+R on C | 24 | False | [-8.01, -0.66] | [-31.50, +22.83] | ≤ +0 pp: 9921/10000, ≥ +0 pp: 120/10000; ≤ +5 pp: 10000/10000, ≥ +5 pp: 0/10000 |
| S1 English retention: E+C − E+E on E | 22 | False | [-6.89, +1.56] | [-29.83, +24.50] | ≤ +0 pp: 9029/10000, ≥ +0 pp: 1300/10000; ≤ -2 pp: 6414/10000, ≥ -2 pp: 4181/10000 |
| S1: E+C − unchanged on E | 37 | False | [-34.23, -18.44] | [-53.50, +0.83] | ≤ +0 pp: 10000/10000, ≥ +0 pp: 0/10000; ≤ -2 pp: 10000/10000, ≥ -2 pp: 0/10000 |
| S1: E+R − E+E on E | 26 | False | [-6.44, +2.44] | [-29.16, +25.16] | ≤ +0 pp: 8314/10000, ≥ +0 pp: 2085/10000; ≤ -2 pp: 5205/10000, ≥ -2 pp: 5379/10000 |
| S1: E+R − unchanged on E | 38 | False | [-33.59, -17.74] | [-52.83, +1.50] | ≤ +0 pp: 10000/10000, ≥ +0 pp: 0/10000; ≤ -2 pp: 10000/10000, ≥ -2 pp: 0/10000 |
| S1: E+E − unchanged on E | 38 | False | [-31.45, -15.88] | [-50.83, +3.50] | ≤ +0 pp: 10000/10000, ≥ +0 pp: 0/10000; ≤ -2 pp: 10000/10000, ≥ -2 pp: 0/10000 |
| S2 R transfer: E+R − E+E on R | 32 | False | [-9.24, +4.57] | [-29.50, +24.83] | ≤ +0 pp: 7640/10000, ≥ +0 pp: 2648/10000 |
| S2: E+C − E+R on R | 27 | False | [-1.96, +8.63] | [-23.83, +30.50] | ≤ +0 pp: 1159/10000, ≥ +0 pp: 9085/10000 |
| Δ_C − Δ_R per family (specificity) | 39 | False | [-14.22, -1.11] | [-61.99, +46.66] | ≤ +0 pp: 9916/10000, ≥ +0 pp: 109/10000 |

Decision and retention labels use strict only.

## Per seed (strict, descriptive)

| Estimand | Seed | Estimate [95% bootstrap] | First only | Second only | Exact McNemar p |
|---|---:|---|---:|---:|---:|
| Primary: E+C − E+R on C | 11 | -3.00 pp [-9.00, +3.00] | 3 | 6 | 0.5078 |
| Primary: E+C − E+R on C | 22 | -1.00 pp [-8.00, +6.00] | 6 | 7 | 1 |
| Primary: E+C − E+R on C | 33 | -9.00 pp [-17.00, -2.00] | 3 | 12 | 0.03516 |
| S1 English retention: E+C − E+E on E | 11 | +2.00 pp [-6.00, +10.00] | 10 | 8 | 0.8145 |
| S1 English retention: E+C − E+E on E | 22 | -5.00 pp [-11.00, +1.00] | 2 | 7 | 0.1797 |
| S1 English retention: E+C − E+E on E | 33 | -5.00 pp [-12.00, +2.00] | 4 | 9 | 0.2668 |
| S2 R transfer: E+R − E+E on R | 11 | +1.00 pp [-7.00, +9.00] | 9 | 8 | 1 |
| S2 R transfer: E+R − E+E on R | 22 | -6.00 pp [-15.00, +3.00] | 8 | 14 | 0.2863 |
| S2 R transfer: E+R − E+E on R | 33 | -2.00 pp [-10.00, +6.00] | 8 | 10 | 0.8145 |
| S2: E+C − E+R on R | 11 | +1.00 pp [-5.00, +7.00] | 5 | 4 | 1 |
| S2: E+C − E+R on R | 22 | +6.00 pp [-1.00, +13.00] | 10 | 4 | 0.1796 |
| S2: E+C − E+R on R | 33 | +3.00 pp [-5.00, +11.00] | 10 | 7 | 0.6291 |

Range across seeds and signs (descriptive, never a test):

- Primary: E+C − E+R on C: range [-9.0, -1.0] pp; positive/zero/negative seeds 0/0/3
- S1 English retention: E+C − E+E on E: range [-5.0, +2.0] pp; positive/zero/negative seeds 1/0/2
- S2 R transfer: E+R − E+E on R: range [-6.0, +1.0] pp; positive/zero/negative seeds 1/0/2
- S2: E+C − E+R on R: range [+1.0, +6.0] pp; positive/zero/negative seeds 3/0/0

Crossed family × seed resampling is not run (Amendment 1 item 4).

## Accuracy by checkpoint — strict (Wilson 95% over N per checkpoint)

| Checkpoint | E | R | C |
|---|---|---|---|
| EE:11 | 62/100 (62.0%; 52.2–70.9) | 41/100 (41.0%; 31.9–50.8) | 44/100 (44.0%; 34.7–53.8) |
| EE:22 | 63/100 (63.0%; 53.2–71.8) | 41/100 (41.0%; 31.9–50.8) | 41/100 (41.0%; 31.9–50.8) |
| EE:33 | 59/100 (59.0%; 49.2–68.1) | 39/100 (39.0%; 30.0–48.8) | 44/100 (44.0%; 34.7–53.8) |
| ER:11 | 61/100 (61.0%; 51.2–70.0) | 42/100 (42.0%; 32.8–51.8) | 44/100 (44.0%; 34.7–53.8) |
| ER:22 | 56/100 (56.0%; 46.2–65.3) | 35/100 (35.0%; 26.4–44.7) | 47/100 (47.0%; 37.5–56.7) |
| ER:33 | 61/100 (61.0%; 51.2–70.0) | 37/100 (37.0%; 28.2–46.8) | 50/100 (50.0%; 40.4–59.6) |
| EC:11 | 64/100 (64.0%; 54.2–72.7) | 43/100 (43.0%; 33.7–52.8) | 41/100 (41.0%; 31.9–50.8) |
| EC:22 | 58/100 (58.0%; 48.2–67.2) | 41/100 (41.0%; 31.9–50.8) | 46/100 (46.0%; 36.6–55.7) |
| EC:33 | 54/100 (54.0%; 44.3–63.4) | 40/100 (40.0%; 30.9–49.8) | 41/100 (41.0%; 31.9–50.8) |
| unchanged | 85/100 (85.0%; 76.7–90.7) | 63/100 (63.0%; 53.2–71.8) | 66/100 (66.0%; 56.3–74.5) |

## Accuracy by checkpoint — numeric_literal_v1 (Wilson 95% over N per checkpoint)

| Checkpoint | E | R | C |
|---|---|---|---|
| EE:11 | 76/100 (76.0%; 66.8–83.3) | 52/100 (52.0%; 42.3–61.5) | 58/100 (58.0%; 48.2–67.2) |
| EE:22 | 81/100 (81.0%; 72.2–87.5) | 49/100 (49.0%; 39.4–58.7) | 53/100 (53.0%; 43.3–62.5) |
| EE:33 | 77/100 (77.0%; 67.8–84.2) | 54/100 (54.0%; 44.3–63.4) | 57/100 (57.0%; 47.2–66.3) |
| ER:11 | 78/100 (78.0%; 68.9–85.0) | 55/100 (55.0%; 45.2–64.4) | 54/100 (54.0%; 44.3–63.4) |
| ER:22 | 72/100 (72.0%; 62.5–79.9) | 48/100 (48.0%; 38.5–57.7) | 58/100 (58.0%; 48.2–67.2) |
| ER:33 | 73/100 (73.0%; 63.6–80.7) | 51/100 (51.0%; 41.3–60.6) | 61/100 (61.0%; 51.2–70.0) |
| EC:11 | 78/100 (78.0%; 68.9–85.0) | 55/100 (55.0%; 45.2–64.4) | 49/100 (49.0%; 39.4–58.7) |
| EC:22 | 76/100 (76.0%; 66.8–83.3) | 52/100 (52.0%; 42.3–61.5) | 56/100 (56.0%; 46.2–65.3) |
| EC:33 | 75/100 (75.0%; 65.7–82.5) | 52/100 (52.0%; 42.3–61.5) | 51/100 (51.0%; 41.3–60.6) |
| unchanged | 90/100 (90.0%; 82.6–94.5) | 73/100 (73.0%; 63.6–80.7) | 71/100 (71.0%; 61.5–79.0) |

## Accuracy by checkpoint — numeric_literal_v2 (Wilson 95% over N per checkpoint)

| Checkpoint | E | R | C |
|---|---|---|---|
| EE:11 | 76/100 (76.0%; 66.8–83.3) | 52/100 (52.0%; 42.3–61.5) | 58/100 (58.0%; 48.2–67.2) |
| EE:22 | 81/100 (81.0%; 72.2–87.5) | 49/100 (49.0%; 39.4–58.7) | 53/100 (53.0%; 43.3–62.5) |
| EE:33 | 77/100 (77.0%; 67.8–84.2) | 54/100 (54.0%; 44.3–63.4) | 57/100 (57.0%; 47.2–66.3) |
| ER:11 | 78/100 (78.0%; 68.9–85.0) | 55/100 (55.0%; 45.2–64.4) | 54/100 (54.0%; 44.3–63.4) |
| ER:22 | 72/100 (72.0%; 62.5–79.9) | 48/100 (48.0%; 38.5–57.7) | 58/100 (58.0%; 48.2–67.2) |
| ER:33 | 73/100 (73.0%; 63.6–80.7) | 51/100 (51.0%; 41.3–60.6) | 61/100 (61.0%; 51.2–70.0) |
| EC:11 | 78/100 (78.0%; 68.9–85.0) | 55/100 (55.0%; 45.2–64.4) | 49/100 (49.0%; 39.4–58.7) |
| EC:22 | 76/100 (76.0%; 66.8–83.3) | 52/100 (52.0%; 42.3–61.5) | 56/100 (56.0%; 46.2–65.3) |
| EC:33 | 75/100 (75.0%; 65.7–82.5) | 52/100 (52.0%; 42.3–61.5) | 51/100 (51.0%; 41.3–60.6) |
| unchanged | 90/100 (90.0%; 82.6–94.5) | 73/100 (73.0%; 63.6–80.7) | 71/100 (71.0%; 61.5–79.0) |

## Operation-word strata (strict; descriptive counts and percentages)

| Stratum | Families | Δ_C (pp) | C acc EE | C acc ER | C acc EC | C acc unchanged |
|---|---:|---:|---:|---:|---:|---:|
| keep | 25 | -1.3 | 43 (57.3%) | 43 (57.3%) | 42 (56.0%) | 19 (76.0%) |
| none | 50 | -6.7 | 50 (33.3%) | 55 (36.7%) | 45 (30.0%) | 32 (64.0%) |
| switch | 25 | -2.7 | 36 (48.0%) | 43 (57.3%) | 41 (54.7%) | 15 (60.0%) |

## Strict-invalid reasons, tokens and latency

| Checkpoint | Form | Invalid reasons | Truncated | Median output tokens | Median latency (s) |
|---|---|---|---:|---:|---:|
| EE:11 | E | invalid_unit 19, percent_requires_dimensionless 4 | 0 | 42.5 | 9.307239387499976 |
| EE:11 | R | invalid_answer 1, invalid_unit 24, multiple_finals 1, percent_requires_dimensionless 4 | 0 | 42.0 | 9.235909302999971 |
| EE:11 | C | invalid_answer 3, invalid_unit 20, multiple_finals 1, percent_requires_dimensionless 4 | 0 | 41.5 | 9.263839271000506 |
| EE:22 | E | invalid_unit 25, percent_requires_dimensionless 4 | 0 | 43.5 | 9.244656125999882 |
| EE:22 | R | invalid_unit 23, multiple_finals 1, percent_requires_dimensionless 4 | 0 | 42.0 | 9.097412567999982 |
| EE:22 | C | invalid_answer 2, invalid_unit 25, multiple_finals 1, percent_requires_dimensionless 4 | 0 | 45.5 | 9.35874798750001 |
| EE:33 | E | invalid_unit 26, percent_requires_dimensionless 4 | 0 | 43.0 | 9.107793848500023 |
| EE:33 | R | invalid_unit 32, percent_requires_dimensionless 4 | 0 | 44.5 | 9.150376464000146 |
| EE:33 | C | invalid_answer 2, invalid_unit 27, multiple_finals 1, percent_requires_dimensionless 4 | 0 | 44.5 | 9.023224504499922 |
| ER:11 | E | invalid_unit 19, percent_requires_dimensionless 4 | 0 | 42.0 | 9.20185308300006 |
| ER:11 | R | invalid_answer 1, invalid_unit 27, percent_requires_dimensionless 4 | 0 | 42.5 | 9.307915869999306 |
| ER:11 | C | invalid_answer 2, invalid_unit 23, multiple_finals 1, percent_requires_dimensionless 4 | 0 | 41.5 | 8.956180161500924 |
| ER:22 | E | invalid_unit 24, percent_requires_dimensionless 4 | 0 | 43.5 | 9.269140260499626 |
| ER:22 | R | invalid_number 1, invalid_unit 28, percent_requires_dimensionless 4 | 0 | 42.5 | 8.905381215000489 |
| ER:22 | C | invalid_answer 3, invalid_unit 22, multiple_finals 1, percent_requires_dimensionless 4 | 0 | 44.5 | 9.465269992499998 |
| ER:33 | E | invalid_answer 2, invalid_unit 19, percent_requires_dimensionless 4 | 0 | 42.5 | 9.144641184500188 |
| ER:33 | R | invalid_unit 29, percent_requires_dimensionless 4 | 0 | 41.5 | 8.848940298499883 |
| ER:33 | C | invalid_answer 3, invalid_unit 22, multiple_finals 1, percent_requires_dimensionless 4 | 0 | 42.0 | 9.135553132000041 |
| EC:11 | E | invalid_answer 1, invalid_unit 18, percent_requires_dimensionless 4 | 0 | 44.0 | 9.799516840999786 |
| EC:11 | R | final_not_terminal_line 1, invalid_unit 26, percent_requires_dimensionless 4 | 0 | 41.0 | 8.974506604499766 |
| EC:11 | C | invalid_answer 3, invalid_unit 24, percent_requires_dimensionless 4 | 0 | 42.0 | 9.667624228000022 |
| EC:22 | E | invalid_unit 25, percent_requires_dimensionless 4 | 0 | 44.0 | 9.225652850999268 |
| EC:22 | R | invalid_unit 28, percent_requires_dimensionless 4 | 0 | 42.0 | 8.945243429500351 |
| EC:22 | C | invalid_answer 2, invalid_unit 25, percent_requires_dimensionless 4 | 0 | 41.5 | 9.15977393150024 |
| EC:33 | E | invalid_unit 27, percent_requires_dimensionless 4 | 0 | 43.0 | 8.951129945499815 |
| EC:33 | R | invalid_answer 1, invalid_unit 28, percent_requires_dimensionless 4 | 0 | 43.0 | 9.291543035500581 |
| EC:33 | C | invalid_answer 3, invalid_unit 23, multiple_finals 1, percent_requires_dimensionless 4 | 0 | 41.5 | 8.715434936999372 |
| unchanged | E | invalid_unit 8, percent_requires_dimensionless 3 | 0 | 115.0 | 11.972645184499697 |
| unchanged | R | invalid_number 2, invalid_unit 12, percent_requires_dimensionless 4 | 0 | 105.5 | 10.865437818499913 |
| unchanged | C | invalid_answer 2, invalid_number 1, invalid_unit 11, percent_requires_dimensionless 4 | 0 | 111.0 | 11.64701286649995 |

Code SHA-256: `phase2_analysis/analyze.py` `11d6f1c837ff05d8de7ef96732ddca023f1f4b8faa4762b25747f7a49749150f`; `secondary_analysis/numeric_endpoint.py` `ce70aefd1f4c03ffe80bbd06d4df025abe92fc0865732b6d2e6db13504ed883f`; `secondary_analysis/numeric_literal_v2.py` `80269ac62d09ce2bdee3271e9ed253ad4a52ec51de105c3ed7dc919d81a712b4`

