# Phase-2 TRAIN and DEV frozen datasets

Frozen 16 October 2026.

| File | Families | SHA-256 |
|---|---:|---|
| `train_A.v2.json` | 80 | `b9656a8c41af2a795bce9c131efc6a5efc652df78368d14fb7720fd985883666` |
| `train_B.v2.json` | 80 | `c975fe12459df6160effc5aeb0087f94666ba0b49778c3d827a67bb923ff35bd` |
| `dev.v2.json` | 40 | `e741c1652f5b3dcaebc78d9dd9d7c31fdf4417306fbb2f0862149f27f858f28b` |

- TRAIN (160) was drafted by Claude and DEV (40) by GPT, with gold computed in code. All 200 were blind-verified by Claude and GPT on v1 (Phase-2 totals: Claude 900/900, GPT 897/900; the TRA072 miss was a GPT error). Every rendering changed in v2 was re-verified by both (43/43 each).
- Human review (one bilingual reviewer) covered the 6 strictly flagged families plus a seeded 20% random sample of the rest (45 families): 19 ACCEPT and 26 REVISE, with fixes applied verbatim as v2 (DV034 typo 'miktar' changed to 'matra'). The remaining TRAIN/DEV families are accepted on automated verification plus the sample; this is sample-based review, not full human review (D027).
- The sampled review found heavy repair needs in GPT-drafted DEV (10/11 revised) and moderate needs in Claude-drafted TRAIN (16/34 revised). Unsampled families may therefore still contain stilted Romanized Hindi; report this as a limitation.
- Any change requires a new version and hash. These families are permanently separate from the pilot, Pilot-B and FINAL_TEST.
