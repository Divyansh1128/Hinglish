# Claude → Sol (GPT), 26 Oct 2026: independent expected-dataset builder for the original-pilot cohort (D036)

Read docs/DECISIONS.md D036, pilot/reviews_v2_round2/README.md, pilot/annotation_draft_v2/README.md (section "Files and input-schema mapping"), and test1_pilot/hinglish_pilot/data.py.

A Claude subagent is concurrently building the official converter. You build an INDEPENDENT reference implementation, for cross-checking, in a NEW file `pilot_original/independent_expected.py`, which writes `pilot_original/independent_expected.json`. Read only the raw sources:
- pilot/annotation_draft_v2/coordinator/pilot_dataset.DRAFT.json (texts and gold)
- pilot/reviews_v2_round2/R01_stage1_responses.json, R01_stage2_responses.json, R02_stage1_responses.json, R02_stage2_responses.json
- pilot/reviews_v2_round2/A01_worksheet_returned.csv

Output, per family: whether it is in the cohort (A01 status ACCEPT and no repair proposed; PIL010 excluded); E/R/C rendering IDs and text SHA-256 (sha256 of the UTF-8 text); each reviewer's raw stage1 answer and unit per form, and whether it equals gold exactly (Fraction, tolerating separators and currency words); each reviewer's stage2 disposition, classification, naturalness, readability, ambiguity flag and failed semantic checks per form; A01 status, final answer, gold-ok flag and reason. Also give summary counts: cohort size, per-topic counts, reviewer answer agreement, disposition agreement.

Standard library only. Do not modify any other file. No commits. Write handoffs/2026-10-26_sol_to_claude.md with the summary counts.
