# Claude → GPT drafter, 15 October 2026 (task 29): Phase-2 FINAL_TEST and DEV families

Decision D027: GPT drafts FINAL_TEST and DEV, so their authorship style differs from the Claude-drafted TRAIN. Read authoring/AUTHORING_GUIDE.md, authoring/family_template.json, authoring/check_family.py, research/operation_vocabulary_2026-10-15.md (sections 2 and 5), research/lexicon_confirmation_user_2026-10-15.md, and the borrowing_policy field in pilot/annotation_draft_v2/coordinator/pilot_dataset.DRAFT.json. Do NOT read pilot question texts, pilot_b/ or phase2/train_*.json.

Draft 140 NEW families in the test1-1 family schema (exactly the template's fields): 100 FINAL_TEST (IDs FT001–FT100, split_role "FINAL_TEST") written to `phase2/final_test.DRAFT.json`, and 40 DEV (IDs DV001–DV040, split_role "DEV") written to `phase2/dev.DRAFT.json`. Use source/template IDs `<ID>-source` and `<ID>-template`; every family is independent. status "DRAFT", authoring_origin "AI_DRAFT_GPT", version "v1". Provenance: AI-drafted by GPT on 15 Oct 2026, unreviewed, naming the operation word and whether C kept it.
- Topics: the 6 TOPICS in test1_pilot/hinglish_pilot/data.py, balanced.
- Context domains: hospitals and health, offices and work schedules, weather and nature, libraries and books, mobile phones and data plans, weddings and events, hostels and messes, auto-rickshaws and deliveries. Vary difficulty: 1–3 steps.
- E: natural English with an exact answer. R: Hindi phrasing in Roman script under the borrowing policy, no substantive English clauses. C: Roman-script Hindi with at least one productive English clause or relation, plus a non-empty switching_roles list.
- Operation-word balance as in research/operation_vocabulary_2026-10-15.md section 5: about half use a Hindi operation word in R, and of those about half keep it in C.
- gold: exact string, unit with aliases including romanized Hindi forms, unit_omission_allowed true, rounding_rule "exact". reference_equation in the checker's format. reference_solution_en ends with "FINAL: <value>" followed by an English unit only if the answer has one.
- No GSM8K/MGSM-like problems.
Run `python3 -B authoring/check_family.py` on both files and fix everything until both pass. Write only those two files plus handoffs/2026-10-15e_drafter_to_claude.md (counts and checker results). No other files, no commits.
