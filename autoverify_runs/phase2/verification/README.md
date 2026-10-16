# Phase-2 blind verification, 16 October 2026

300 AI-drafted families (160 TRAIN by Claude; 100 FINAL_TEST + 40 DEV by GPT), 900 renderings, each solved blind by Claude (3 isolated chunks) and GPT (1 isolated run). Neither solver saw gold, reference equations or other forms' metadata. Qwen was never used.

- Answers matching code-computed gold: **Claude 900/900; GPT 897/900**. The 3 GPT misses are all TRA072 (GPT answered 12; gold 16 verified by hand: 2h + 4(h−12) = 120 ⇒ h = 28, goats = 16). This is a solver error, not an item error.
- `compare.py`'s per-solver cross-form *multiset* check flagged 234/300 families, almost entirely because of solver extraction conventions (split clock times, repeated mentions, number words), so it is too noisy to route human review. **Review routing uses a stricter rule, chosen before any human review:** flag a family if either solver misses gold, the solvers disagree, a solver notes an ambiguity, or **both** solvers extract different number *sets* across E/R/C. `verification_report.json` keeps the original flags unchanged.
- Strict flags: 10 FINAL_TEST families, 6 TRAIN/DEV families.

Review sheets (see `docs/REVIEW_INSTRUCTIONS.md`):
- `review_FINAL_TEST.csv`: all 100 FINAL_TEST families, flagged first. Full human review is required.
- `review_TRAIN_DEV.csv`: 6 flagged plus a seeded random 20% sample (39 of 194 unflagged) of TRAIN and DEV families.
