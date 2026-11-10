# EXPLORATORY — not pre-registered; does not change the confirmatory result (Harm, D052)

Phase-2 FINAL_TEST error analysis. Counts are descriptive, post hoc, and conditional on these fixed checkpoints and families.

## Main findings

- Validated 10 complete runs, 3,000 outputs and all 60 published strict/numeric checkpoint × form counts.
- Strict: trained 1295/2700 (48.0%); unchanged 214/300 (71.3%).
- Numeric literal: trained 1651/2700 (61.1%); unchanged 234/300 (78.0%).
- Pooled strict deficits E/R/C: 25.22/23.11/21.78 pp.
- Excess number-correct unit failures explain E/R/C: 11.00/2.89/4.67 pp of those deficits.
- Excess numeric mismatches explain E/R/C: 13.44/21.67/16.22 pp; residual unscored errors are separate.
- Median output tokens: trained 42.0 vs unchanged 113.0; omitted reasoning is not established causally.
- Trained invalid_unit: 658 outputs, 410 numeric matches; most common pattern [NUM] km (36).
- Numeric Δ_C stays negative: all -5.67 pp; paired scored -6.79 pp (280 pairs); all-six common -6.52 pp.

## Inputs and validation

Only the ten inner `*_results.zip` predictions were scored; duplicate outer copies were checked, not counted. Inner checksums, complete unique pairing, identical dataset snapshots and strict-scorer sources were verified. All 60 strict/numeric checkpoint × form counts match the supplied confirmatory report. Strict scores were copied unchanged.

Outer archive SHA-256: `fb4a71ccb22d8d4f274ec3c94c0b7455f870aebe7fcc673d18e47632a0024f9a`.
Confirmatory report SHA-256: `1a1ffffe58fadc23e82d0bc000dfd41455edfa2205e0ba3995782573b967aea6`.
Source and inner-member hashes are in JSON. No generated timestamp or absolute path enters the outputs.

## Error partition by checkpoint and form

S = stored strict-correct; F = numeric-correct but strict-wrong; M = numeric literal mismatch among strict-wrong; U = numerically unscored and strict-wrong. S+F+M+U=N. Numeric endpoints require an extractable FINAL scalar and do not convert units. M is evidence of a wrong declared literal, not a diagnosis of arithmetic versus reasoning or semantic quantity accuracy. U cannot be labelled a reasoning error. F establishes a strict unit/format failure; it does not validate dimensional meaning.

| Checkpoint | Form | S strict | F rescued | M numeric wrong | U unscored wrong | Numeric correct | Strict-only successes | F by invalid_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| unchanged | E | 85/100 (85.0%) | 8/100 (8.0%) | 7/100 (7.0%) | 0/100 (0.0%) | 90/100 (90.0%) | 3 | invalid_unit: 8 |
| unchanged | R | 63/100 (63.0%) | 11/100 (11.0%) | 23/100 (23.0%) | 3/100 (3.0%) | 73/100 (73.0%) | 1 | invalid_unit: 11 |
| unchanged | C | 66/100 (66.0%) | 8/100 (8.0%) | 23/100 (23.0%) | 3/100 (3.0%) | 71/100 (71.0%) | 3 | invalid_unit: 8 |
| EE:11 | E | 62/100 (62.0%) | 16/100 (16.0%) | 21/100 (21.0%) | 1/100 (1.0%) | 76/100 (76.0%) | 2 | invalid_unit: 16 |
| EE:11 | R | 41/100 (41.0%) | 12/100 (12.0%) | 44/100 (44.0%) | 3/100 (3.0%) | 52/100 (52.0%) | 1 | invalid_unit: 12 |
| EE:11 | C | 44/100 (44.0%) | 14/100 (14.0%) | 36/100 (36.0%) | 6/100 (6.0%) | 58/100 (58.0%) | 0 | invalid_unit: 14 |
| EE:22 | E | 63/100 (63.0%) | 21/100 (21.0%) | 16/100 (16.0%) | 0/100 (0.0%) | 81/100 (81.0%) | 3 | invalid_unit: 21 |
| EE:22 | R | 41/100 (41.0%) | 10/100 (10.0%) | 48/100 (48.0%) | 1/100 (1.0%) | 49/100 (49.0%) | 2 | invalid_unit: 10 |
| EE:22 | C | 41/100 (41.0%) | 14/100 (14.0%) | 42/100 (42.0%) | 3/100 (3.0%) | 53/100 (53.0%) | 2 | invalid_unit: 14 |
| EE:33 | E | 59/100 (59.0%) | 21/100 (21.0%) | 20/100 (20.0%) | 0/100 (0.0%) | 77/100 (77.0%) | 3 | invalid_unit: 21 |
| EE:33 | R | 39/100 (39.0%) | 17/100 (17.0%) | 43/100 (43.0%) | 1/100 (1.0%) | 54/100 (54.0%) | 2 | invalid_unit: 17 |
| EE:33 | C | 44/100 (44.0%) | 14/100 (14.0%) | 38/100 (38.0%) | 4/100 (4.0%) | 57/100 (57.0%) | 1 | invalid_unit: 14 |
| ER:11 | E | 61/100 (61.0%) | 19/100 (19.0%) | 19/100 (19.0%) | 1/100 (1.0%) | 78/100 (78.0%) | 2 | invalid_unit: 19 |
| ER:11 | R | 42/100 (42.0%) | 15/100 (15.0%) | 42/100 (42.0%) | 1/100 (1.0%) | 55/100 (55.0%) | 2 | invalid_unit: 15 |
| ER:11 | C | 44/100 (44.0%) | 12/100 (12.0%) | 41/100 (41.0%) | 3/100 (3.0%) | 54/100 (54.0%) | 2 | invalid_unit: 12 |
| ER:22 | E | 56/100 (56.0%) | 19/100 (19.0%) | 25/100 (25.0%) | 0/100 (0.0%) | 72/100 (72.0%) | 3 | invalid_unit: 19 |
| ER:22 | R | 35/100 (35.0%) | 14/100 (14.0%) | 48/100 (48.0%) | 3/100 (3.0%) | 48/100 (48.0%) | 1 | invalid_unit: 14 |
| ER:22 | C | 47/100 (47.0%) | 14/100 (14.0%) | 35/100 (35.0%) | 4/100 (4.0%) | 58/100 (58.0%) | 3 | invalid_unit: 14 |
| ER:33 | E | 61/100 (61.0%) | 15/100 (15.0%) | 22/100 (22.0%) | 2/100 (2.0%) | 73/100 (73.0%) | 3 | invalid_unit: 15 |
| ER:33 | R | 37/100 (37.0%) | 16/100 (16.0%) | 45/100 (45.0%) | 2/100 (2.0%) | 51/100 (51.0%) | 2 | invalid_unit: 16 |
| ER:33 | C | 50/100 (50.0%) | 14/100 (14.0%) | 32/100 (32.0%) | 4/100 (4.0%) | 61/100 (61.0%) | 3 | invalid_unit: 14 |
| EC:11 | E | 64/100 (64.0%) | 16/100 (16.0%) | 18/100 (18.0%) | 2/100 (2.0%) | 78/100 (78.0%) | 2 | invalid_unit: 16 |
| EC:11 | R | 43/100 (43.0%) | 14/100 (14.0%) | 42/100 (42.0%) | 1/100 (1.0%) | 55/100 (55.0%) | 2 | invalid_unit: 14 |
| EC:11 | C | 41/100 (41.0%) | 9/100 (9.0%) | 46/100 (46.0%) | 4/100 (4.0%) | 49/100 (49.0%) | 1 | invalid_unit: 9 |
| EC:22 | E | 58/100 (58.0%) | 21/100 (21.0%) | 21/100 (21.0%) | 0/100 (0.0%) | 76/100 (76.0%) | 3 | invalid_unit: 21 |
| EC:22 | R | 41/100 (41.0%) | 13/100 (13.0%) | 46/100 (46.0%) | 0/100 (0.0%) | 52/100 (52.0%) | 2 | invalid_unit: 13 |
| EC:22 | C | 46/100 (46.0%) | 12/100 (12.0%) | 40/100 (40.0%) | 2/100 (2.0%) | 56/100 (56.0%) | 2 | invalid_unit: 12 |
| EC:33 | E | 54/100 (54.0%) | 23/100 (23.0%) | 22/100 (22.0%) | 1/100 (1.0%) | 75/100 (75.0%) | 2 | invalid_unit: 23 |
| EC:33 | R | 40/100 (40.0%) | 14/100 (14.0%) | 44/100 (44.0%) | 2/100 (2.0%) | 52/100 (52.0%) | 2 | invalid_unit: 14 |
| EC:33 | C | 41/100 (41.0%) | 11/100 (11.0%) | 43/100 (43.0%) | 5/100 (5.0%) | 51/100 (51.0%) | 1 | invalid_unit: 11 |

Strict-only successes are retained in S even when the numeric parser rejects their suffix syntax. They prevent treating numeric accuracy as a simple superset of strict accuracy. Full mismatch-by-invalid-reason, U statuses and reasons are in JSON.

Numeric mismatches by strict invalid_reason, pooled across forms (these are components of M, not additional errors):

| Group | No strict format/unit failure | invalid_unit | percent_requires_dimensionless | Total M | Strict-only successes |
| --- | --- | --- | --- | --- | --- |
| unchanged | 38 | 4 | 11 | 53 | 7 |
| trained | 586 | 245 | 108 | 939 | 54 |

A mismatch with an invalid unit can have both a number and a unit problem. The endpoint cannot isolate those mechanisms. Percent literals are scaled by 1/100 by the numeric endpoint; invalid percentage-unit combinations can thus also be literal mismatches. The no-format/unit-failure column confirms that the trained deficit includes wrong values even when strict answer syntax and units are accepted.

## Trained-versus-unchanged gap decomposition

Positive gaps mean unchanged is better. For each form, **strict gap = excess F + excess M + excess U**, where excess is the trained error rate minus the unchanged error rate. Each row is an exact disjoint accounting identity. An invalid_unit answer with a wrong literal belongs to M, so the F component is a conservative count of demonstrably number-correct strict failures, not all unit-invalid answers. The mechanism of an individual failure is not identified.

Arm rows pool three seeds (300 outputs/form); unchanged is 100 outputs/form. The same families and baseline are reused, without treating observations as independent.

| Arm | Form | Strict gap pp | F pp (% gap) | M pp (% gap) | U pp (% gap) | Numeric endpoint gap pp | Strict-only correction pp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EE | E | 23.67 | 11.33 (47.9%) | 12.00 (50.7%) | 0.33 (1.4%) | 12.00 | 0.33 |
| EE | R | 22.67 | 2.00 (8.8%) | 22.00 (97.1%) | -1.33 (-5.9%) | 21.33 | -0.67 |
| EE | C | 23.00 | 6.00 (26.1%) | 15.67 (68.1%) | 1.33 (5.8%) | 15.00 | 2.00 |
| ER | E | 25.67 | 9.67 (37.7%) | 15.00 (58.4%) | 1.00 (3.9%) | 15.67 | 0.33 |
| ER | R | 25.00 | 4.00 (16.0%) | 22.00 (88.0%) | -1.00 (-4.0%) | 21.67 | -0.67 |
| ER | C | 19.00 | 5.33 (28.1%) | 13.00 (68.4%) | 0.67 (3.5%) | 13.33 | 0.33 |
| EC | E | 26.33 | 12.00 (45.6%) | 13.33 (50.6%) | 1.00 (3.8%) | 13.67 | 0.67 |
| EC | R | 21.67 | 2.67 (12.3%) | 21.00 (96.9%) | -2.00 (-9.2%) | 20.00 | -1.00 |
| EC | C | 23.33 | 2.67 (11.4%) | 20.00 (85.7%) | 0.67 (2.9%) | 19.00 | 1.67 |
| All trained | E | 25.22 | 11.00 (43.6%) | 13.44 (53.3%) | 0.78 (3.1%) | 13.78 | 0.44 |
| All trained | R | 23.11 | 2.89 (12.5%) | 21.67 (93.7%) | -1.44 (-6.2%) | 21.00 | -0.78 |
| All trained | C | 21.78 | 4.67 (21.4%) | 16.22 (74.5%) | 0.89 (4.1%) | 15.78 | 1.33 |

The nonnested endpoint identity is also checked: strict gap = numeric endpoint gap + excess F + (unchanged strict-only success rate − trained strict-only success rate). Consequently strict-minus-numeric gap reduction alone is not an exact count of added unit failures.

Checkpoint-level decomposition (all entries in percentage points):

| Checkpoint | Form | Strict gap | F | M | U |
| --- | --- | --- | --- | --- | --- |
| EE:11 | E | 23.00 | 8.00 | 14.00 | 1.00 |
| EE:11 | R | 22.00 | 1.00 | 21.00 | 0.00 |
| EE:11 | C | 22.00 | 6.00 | 13.00 | 3.00 |
| EE:22 | E | 22.00 | 13.00 | 9.00 | 0.00 |
| EE:22 | R | 22.00 | -1.00 | 25.00 | -2.00 |
| EE:22 | C | 25.00 | 6.00 | 19.00 | 0.00 |
| EE:33 | E | 26.00 | 13.00 | 13.00 | 0.00 |
| EE:33 | R | 24.00 | 6.00 | 20.00 | -2.00 |
| EE:33 | C | 22.00 | 6.00 | 15.00 | 1.00 |
| ER:11 | E | 24.00 | 11.00 | 12.00 | 1.00 |
| ER:11 | R | 21.00 | 4.00 | 19.00 | -2.00 |
| ER:11 | C | 22.00 | 4.00 | 18.00 | 0.00 |
| ER:22 | E | 29.00 | 11.00 | 18.00 | 0.00 |
| ER:22 | R | 28.00 | 3.00 | 25.00 | 0.00 |
| ER:22 | C | 19.00 | 6.00 | 12.00 | 1.00 |
| ER:33 | E | 24.00 | 7.00 | 15.00 | 2.00 |
| ER:33 | R | 26.00 | 5.00 | 22.00 | -1.00 |
| ER:33 | C | 16.00 | 6.00 | 9.00 | 1.00 |
| EC:11 | E | 21.00 | 8.00 | 11.00 | 2.00 |
| EC:11 | R | 20.00 | 3.00 | 19.00 | -2.00 |
| EC:11 | C | 25.00 | 1.00 | 23.00 | 1.00 |
| EC:22 | E | 27.00 | 13.00 | 14.00 | 0.00 |
| EC:22 | R | 22.00 | 2.00 | 23.00 | -3.00 |
| EC:22 | C | 20.00 | 4.00 | 17.00 | -1.00 |
| EC:33 | E | 31.00 | 15.00 | 15.00 | 1.00 |
| EC:33 | R | 23.00 | 3.00 | 21.00 | -1.00 |
| EC:33 | C | 25.00 | 3.00 | 20.00 | 2.00 |

## Length, correctness and visible working

Bins and the ≤48-token short threshold were chosen after seeing the length distribution. Token counts come from the stored generation metadata. Within-bin rates compare different items; difficulty, form and checkpoint can confound them. No causal effect of length is estimated.

| Group | Form | N | Median tokens all / S / F / M / U | Mean nonfinal lines | ≤1 nonfinal line | ≥2 '=' signs |
| --- | --- | --- | --- | --- | --- | --- |
| unchanged | E | 100 | 115.0 / 115.0 / 111.5 / 126.0 / — | 7.33 | 13/100 (13.0%) | 86/100 (86.0%) |
| unchanged | R | 100 | 105.5 / 114.0 / 91.0 / 104.0 / 98.0 | 5.59 | 33/100 (33.0%) | 70/100 (70.0%) |
| unchanged | C | 100 | 111.0 / 123.0 / 84.0 / 99.0 / 107.0 | 5.87 | 30/100 (30.0%) | 76/100 (76.0%) |
| trained | E | 900 | 43.0 / 42.0 / 42.0 / 48.0 / 36.0 | 0.99 | 900/900 (100.0%) | 788/900 (87.6%) |
| trained | R | 900 | 42.0 / 41.0 / 40.0 / 46.0 / 44.0 | 0.99 | 895/900 (99.4%) | 747/900 (83.0%) |
| trained | C | 900 | 42.0 / 42.0 / 40.0 / 46.0 / 39.0 | 0.99 | 891/900 (99.0%) | 740/900 (82.2%) |

All forms pooled, then within each form:

| Group | Form | Tokens | N | Strict | Numeric |
| --- | --- | --- | --- | --- | --- |
| unchanged | all | 0–32 | 1 | 0/1 (0.0%) | 0/1 (0.0%) |
| unchanged | all | 33–48 | 2 | 2/2 (100.0%) | 2/2 (100.0%) |
| unchanged | all | 49–64 | 18 | 15/18 (83.3%) | 15/18 (83.3%) |
| unchanged | all | 65–96 | 82 | 47/82 (57.3%) | 57/82 (69.5%) |
| unchanged | all | 97–128 | 88 | 66/88 (75.0%) | 73/88 (83.0%) |
| unchanged | all | 129+ | 109 | 84/109 (77.1%) | 87/109 (79.8%) |
| unchanged | E | 0–32 | 0 | 0/0 (—%) | 0/0 (—%) |
| unchanged | E | 33–48 | 0 | 0/0 (—%) | 0/0 (—%) |
| unchanged | E | 49–64 | 3 | 3/3 (100.0%) | 3/3 (100.0%) |
| unchanged | E | 65–96 | 24 | 21/24 (87.5%) | 20/24 (83.3%) |
| unchanged | E | 97–128 | 39 | 32/39 (82.1%) | 37/39 (94.9%) |
| unchanged | E | 129+ | 34 | 29/34 (85.3%) | 30/34 (88.2%) |
| unchanged | R | 0–32 | 0 | 0/0 (—%) | 0/0 (—%) |
| unchanged | R | 33–48 | 2 | 2/2 (100.0%) | 2/2 (100.0%) |
| unchanged | R | 49–64 | 10 | 8/10 (80.0%) | 8/10 (80.0%) |
| unchanged | R | 65–96 | 28 | 12/28 (42.9%) | 17/28 (60.7%) |
| unchanged | R | 97–128 | 24 | 17/24 (70.8%) | 20/24 (83.3%) |
| unchanged | R | 129+ | 36 | 24/36 (66.7%) | 26/36 (72.2%) |
| unchanged | C | 0–32 | 1 | 0/1 (0.0%) | 0/1 (0.0%) |
| unchanged | C | 33–48 | 0 | 0/0 (—%) | 0/0 (—%) |
| unchanged | C | 49–64 | 5 | 4/5 (80.0%) | 4/5 (80.0%) |
| unchanged | C | 65–96 | 30 | 14/30 (46.7%) | 20/30 (66.7%) |
| unchanged | C | 97–128 | 25 | 17/25 (68.0%) | 16/25 (64.0%) |
| unchanged | C | 129+ | 39 | 31/39 (79.5%) | 31/39 (79.5%) |
| trained | all | 0–32 | 520 | 265/520 (51.0%) | 345/520 (66.3%) |
| trained | all | 33–48 | 1255 | 623/1255 (49.6%) | 812/1255 (64.7%) |
| trained | all | 49–64 | 687 | 333/687 (48.5%) | 384/687 (55.9%) |
| trained | all | 65–96 | 210 | 66/210 (31.4%) | 97/210 (46.2%) |
| trained | all | 97–128 | 15 | 5/15 (33.3%) | 7/15 (46.7%) |
| trained | all | 129+ | 13 | 3/13 (23.1%) | 6/13 (46.2%) |
| trained | E | 0–32 | 146 | 88/146 (60.3%) | 123/146 (84.2%) |
| trained | E | 33–48 | 449 | 286/449 (63.7%) | 359/449 (80.0%) |
| trained | E | 49–64 | 225 | 138/225 (61.3%) | 160/225 (71.1%) |
| trained | E | 65–96 | 62 | 18/62 (29.0%) | 33/62 (53.2%) |
| trained | E | 97–128 | 10 | 5/10 (50.0%) | 6/10 (60.0%) |
| trained | E | 129+ | 8 | 3/8 (37.5%) | 5/8 (62.5%) |
| trained | R | 0–32 | 186 | 89/186 (47.8%) | 99/186 (53.2%) |
| trained | R | 33–48 | 417 | 171/417 (41.0%) | 252/417 (60.4%) |
| trained | R | 49–64 | 226 | 78/226 (34.5%) | 89/226 (39.4%) |
| trained | R | 65–96 | 66 | 21/66 (31.8%) | 28/66 (42.4%) |
| trained | R | 97–128 | 2 | 0/2 (0.0%) | 0/2 (0.0%) |
| trained | R | 129+ | 3 | 0/3 (0.0%) | 0/3 (0.0%) |
| trained | C | 0–32 | 188 | 88/188 (46.8%) | 123/188 (65.4%) |
| trained | C | 33–48 | 389 | 166/389 (42.7%) | 201/389 (51.7%) |
| trained | C | 49–64 | 236 | 117/236 (49.6%) | 135/236 (57.2%) |
| trained | C | 65–96 | 82 | 27/82 (32.9%) | 36/82 (43.9%) |
| trained | C | 97–128 | 3 | 0/3 (0.0%) | 1/3 (33.3%) |
| trained | C | 129+ | 2 | 0/2 (0.0%) | 1/2 (50.0%) |

Same-family, same-form token differences (trained − unchanged), averaged across each arm's seeds:

| Arm | Form | All N; mean Δ tokens | Both strict-correct N; mean Δ tokens | Base correct / trained wrong N; mean Δ tokens |
| --- | --- | --- | --- | --- |
| EE | E | 300; -76.5 | 180; -74.6 | 75; -80.7 |
| EE | R | 300; -79.3 | 102; -65.5 | 87; -82.7 |
| EE | C | 300; -74.8 | 111; -72.5 | 87; -86.1 |
| ER | E | 300; -76.9 | 175; -73.0 | 80; -84.9 |
| ER | R | 300; -79.0 | 99; -63.8 | 90; -83.6 |
| ER | C | 300; -75.5 | 118; -74.0 | 80; -87.2 |
| EC | E | 300; -77.0 | 174; -73.6 | 81; -84.4 |
| EC | R | 300; -79.7 | 104; -64.1 | 85; -84.3 |
| EC | C | 300; -76.3 | 107; -72.9 | 91; -91.3 |

Among trained outputs, ≤48-token answers have numeric accuracy 1157/1775 (65.2%), versus 494/925 (53.4%) for >48 tokens; strict accuracy is 888/1775 (50.0%) versus 407/925 (44.0%). The shorter group is more accurate in this descriptive comparison, so a simple within-trained length-deficit story is unsupported.

Trained answers use fewer separate lines, while the table shows that multiple '=' signs remain common: visible equations are often compressed into a single line. A single line may contain several operations and a long response may repeat errors. Nonfinal-line and '=' counts are layout proxies, not a semantic step audit. The data do not establish that omitted steps caused the numeric loss. Full checkpoint × form length strata and all four paired outcome cells are in JSON.
No output was truncated (0/3000), so the observed brevity is not an output-token-cap failure.

## Trained invalid_unit answer strings

There are 658 invalid_unit outputs across 41 distinct families: 410 numeric matches, 245 mismatches, 3 unscored. 487 occur on items whose canonical unit is empty. Counts are outputs, with repeated forms/seeds, not independent failures.

Strict scorer 1.0.0 accepts the canonical unit, supplied aliases and declared conversions (plus its currency rules); otherwise it returns invalid_unit. An added count noun on an item with an empty canonical unit can therefore fail. A rejected real unit can also reflect wording or scale; numeric_literal_v2 neither validates nor converts it.

Top 25 emitted final-answer strings after replacing numeric literals with `[NUM]` and collapsing whitespace. Different scalar values are pooled; unit wording/case is preserved. Only model-emitted text is displayed, with no gold answer values. All patterns, form/arm counts and distinct-family counts are in JSON.

| Literal-redacted final answer | Count | Numeric match | Mismatch | Unscored | Empty canonical unit |
| --- | --- | --- | --- | --- | --- |
| [NUM] km | 36 | 15 | 21 | 0 | 36 |
| [NUM] entries | 27 | 14 | 13 | 0 | 27 |
| [NUM] lockers | 27 | 15 | 12 | 0 | 27 |
| [NUM] pages | 27 | 11 | 16 | 0 | 27 |
| [NUM] photos | 27 | 27 | 0 | 0 | 27 |
| [NUM] screens | 27 | 27 | 0 | 0 | 27 |
| [NUM] slots | 27 | 22 | 5 | 0 | 0 |
| [NUM] kits | 25 | 25 | 0 | 0 | 25 |
| [NUM] people | 25 | 5 | 20 | 0 | 6 |
| [NUM] trays | 25 | 24 | 1 | 0 | 0 |
| [NUM] stops | 22 | 22 | 0 | 0 | 22 |
| [NUM] of the report | 19 | 8 | 11 | 0 | 19 |
| [NUM] helpers | 18 | 18 | 0 | 0 | 0 |
| [NUM] invitations | 18 | 5 | 13 | 0 | 18 |
| [NUM] plants | 17 | 8 | 9 | 0 | 8 |
| [NUM] reminders | 17 | 15 | 2 | 0 | 17 |
| [NUM] seats | 17 | 9 | 8 | 0 | 9 |
| [NUM] cm | 14 | 13 | 1 | 0 | 0 |
| [NUM] saplings | 13 | 6 | 7 | 0 | 12 |
| [NUM] books | 11 | 11 | 0 | 0 | 11 |
| [NUM] patients | 11 | 6 | 5 | 0 | 11 |
| [NUM] hours | 10 | 7 | 3 | 0 | 0 |
| [NUM] meals per minute | 10 | 9 | 1 | 0 | 0 |
| [NUM] of the document | 10 | 9 | 1 | 0 | 10 |
| [NUM] times | 10 | 1 | 9 | 0 | 10 |

Three anonymised response snippets only, one representative per leading unit pattern (first 200 source characters, then capped at 200 after redaction). Numbers are `[NUM]`; all title-case words are conservatively hidden as `[WORD]` to remove names. No item IDs, question text, or gold answers are included:

- Example 1: `[WORD] ratio part: [NUM] = [NUM] km. [WORD] distance: [NUM] x [NUM] = [NUM] km. FINAL: [NUM] km`
- Example 2: `[WORD]: [NUM]% of [NUM] = [NUM] entries. [WORD]: [NUM] - [NUM] = [NUM] entries. [WORD] to check: [NUM] - [NUM]% of [NUM] = [NUM] - [NUM] = [NUM] entries. [WORD] [NUM] more entries need to be checked. `
- Example 3: `[WORD] part: [NUM] = [NUM] lockers. [WORD] ward: [NUM] x [NUM] = [NUM] lockers. FINAL: [NUM] lockers`

## Δ_C on numerically scored items

Δ_C is EC − ER on C. 'Numerically scored' means an endpoint status of match or mismatch, including both successes and failures. Both arms must be scored on the identical family within a seed; independently filtering each arm would break pairing. We also use the same family subset across all six EC/ER checkpoints. Output-dependent filtering changes the estimand and is descriptive only.

| Subset | Pairs | EC numeric | ER numeric | Strict Δ_C pp | Numeric Δ_C pp |
| --- | --- | --- | --- | --- | --- |
| All C outputs | 300 | 156/300 (52.0%) | 173/300 (57.7%) | -4.33 | -5.67 |
| Both parseable within seed (pooled) | 280 | 154/280 (55.0%) | 173/280 (61.8%) | -3.21 | -6.79 |
| Common families, all six checkpoints | 276 | 151/276 (54.7%) | 169/276 (61.2%) | -2.90 | -6.52 |
| Seed 11, both parseable | 94 | 49/94 (52.1%) | 54/94 (57.4%) | -2.13 | -5.32 |
| Seed 22, both parseable | 93 | 55/93 (59.1%) | 58/93 (62.4%) | 0.00 | -3.23 |
| Seed 33, both parseable | 93 | 50/93 (53.8%) | 61/93 (65.6%) | -7.53 | -11.83 |

Equal-seed mean of within-seed restricted numeric contrasts: -6.79 pp. Common all-six subset: 92 families. No uncertainty interval or significance test is attached to these filtered contrasts.

## Interpretation limits

The trained deficit contains both extra number-correct unit failures and a larger wrong-literal component. Brevity and added answer nouns are consistent with a changed response style, but these outputs alone cannot identify the training cause, distinguish arithmetic from comprehension failures, or show that longer reasoning would repair the errors. Unit-blind literal matching is not a replacement primary scorer. Pooling repeats the same authored families across forms and seeds; it does not increase the number of independent families. The confirmatory strict Harm decision (D052) is unchanged.

EXPLORATORY — not pre-registered; does not change the confirmatory result (Harm, D052)
