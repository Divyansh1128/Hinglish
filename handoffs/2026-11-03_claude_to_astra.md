# Claude → Astra (GPT), 3 Nov 2026: adversarial review of the Phase-2 pre-registration

`phase2/PREREGISTRATION.md` (committed 58d330d, D044) was drafted by a Claude subagent while Codex was unavailable. No Phase-2 training, DEV or FINAL_TEST output exists yet, so amendments are still clean.

Read it together with D040–D044 in docs/DECISIONS.md, research/phase2_protocol_v1_2026-10-27.md, research/phase2_power/, results/training_smoke/README.md and phase2/*_FROZEN.md. Do not open the contents of final_test.v3.json.

Review it as a hostile methods reviewer. Look for:
- internal contradictions;
- rules that cannot be implemented or are ambiguous;
- loopholes that allow outcome-dependent choices;
- statistical errors (the bootstrap, decision-label boundaries, Holm, retention labels, the ceiling flag);
- whether the 60-update schedule and the data-order rule are well justified;
- whether the numeric_literal_v2 rule is exactly specified;
- whether the failure, rerun and access rules are leak-proof;
- anything a reviewer of a pre-registered NLP training study would expect but is missing.

Write `research/astra_prereg_review_2026-11-03.md` (under 150 lines). Give each issue a severity (blocking / should-fix / optional), quote the exact text concerned, and propose replacement wording usable as a dated amendment. Do not edit the pre-registration or any other file. No commits. Then write handoffs/2026-11-03_astra_to_claude.md.
