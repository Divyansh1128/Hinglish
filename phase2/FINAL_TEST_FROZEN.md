# Phase-2 FINAL_TEST frozen dataset

Frozen 16 October 2026. File `final_test.v3.json`, SHA-256 `da89dd9a626e438dffca39e3a74c4c8abac6bb57501495723b87e6ee143f3d46`.

- 100 AI-drafted families (GPT), gold computed in code. Blind-verified by Claude and GPT on v1 (all 300 Phase-2 families: Claude 900/900, GPT 897/900; the TRA072 miss was a GPT error) and again on every changed rendering in v3 (204/204 each).
- Human review by one bilingual team member: 32 ACCEPT, 68 REVISE. Fixes were applied verbatim (v2). Claude made consequential edits and Hindi-verb swaps that keep R distinct from C; the reviewer confirmed these (53 OK, 30 EDIT, 5 MINE → v3).
- FT057-C v4: Claude restored a distractor omitted in C (12 marigolds) under delegated authority. Gold 30 checked by hand; not blind re-solved.
- Main review finding: GPT-drafted Romanized Hindi was systematically over-formal (68/100 needed repair, against 13/70 for the Claude-drafted Pilot-B).
- **UNTOUCHED TEST SET:** no model may be evaluated on, tuned on or inspected against these families until the confirmatory Phase-2 evaluation. They are excluded from all development, prompt work and training.
- Status `ACCEPT` by a single reviewer; a second-annotator sample is still planned (D027).
