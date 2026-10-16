# Pilot-B frozen dataset

Frozen 16 October 2026. File `pilot_b_families.v2.json`, SHA-256 `e632e5fcc6b050e93d85920d7938fbb229936fa1474095d6c4c4a6517fcf3478`.

- 70 AI-drafted families (Claude), gold computed in code, verified by blind Claude and GPT solving (210/210 each on v1; 15/15 each on the revised v2 renderings).
- Reviewed by one bilingual team member: 57 ACCEPT and 13 REVISE, with the fixes applied as v2 (decision D033). Status `ACCEPT`, by a **single reviewer**: no second annotator yet.
- `pilot_b_families.DRAFT.json` (v1) is kept unchanged. The returned review sheet is `autoverify_runs/pilot_b/verification/review_returned_user_2026-10-16.csv`.
- PB051 (10:05–10:25) was accepted by the reviewer despite a solver ambiguity note; gold assumes 20 minutes.
- Any further text change requires a new version and a new hash. Pilot-B families are permanently excluded from Phase-2 TRAIN, DEV and FINAL_TEST.
