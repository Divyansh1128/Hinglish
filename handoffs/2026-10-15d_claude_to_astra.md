# Claude → Astra, 15 October 2026 (task 27): validation protocol and Phase-2 design

Context: the user decided on a 70-family Pilot-B extension (for the EACL paper, total 100 with the pilot) and 300 Phase-2 families (100 FINAL_TEST, 40 DEV, 160 TRAIN). Families are AI-drafted with gold computed in code. Claude and GPT independently solve every rendering, never Qwen. The user (one bilingual team member) reviews flagged families plus a 20% random sample; FINAL_TEST is reviewed fully. Read docs/DECISIONS.md, research/claude_deep_research/datasets_2026-10-15.md, research/astra_experiment_spec_v1.md and authoring/AUTHORING_GUIDE.md.

Write ONE file, research/autoverify_protocol_2026-10-15.md (under 120 lines):
1. A pre-registered validation of the automated checker against the 30 human-reviewed pilot families (once R01/R02/A01 return): which human decision counts as ground truth, the metrics (precision/recall of flags for REVISE/REJECT), and the acceptance threshold for relying on the checker. State what happens if it fails.
2. A drafter split: GPT drafts FINAL_TEST/DEV and Claude drafts TRAIN (author-style transfer), plus an optional human-written FINAL_TEST subset. Cover the risks and what the paper must disclose.
3. The second-annotator plan: about 30 families double-reviewed, with the agreement statistics to report.
4. Exact sampling rules, freeze points and ledger entries, so Pilot-B and the Phase-2 families stay permanently separate from the pilot and from each other.
5. Honest limitations: AI-drafted plus AI-checked data, a single primary reviewer, and that naturalness remains human-only.
Proposals only. Do not modify other files. No commits. Write handoffs/2026-10-15d_astra_to_claude.md when done.
