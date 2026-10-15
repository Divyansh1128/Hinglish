# Astra → Claude — 15 October 2026, task 18

Completed the requested proposal in `research/eacl_srw_paper_plan_2026-10-15.md` (under 120 lines). Only that plan and this required handoff were written; no commits, inference, protocol adoption or changes to other files.

- Four-page outline, three title options, concrete tables/figures mapped to `paper_analysis/`, and a claim separating the format/scoring development evidence from possible Romanized-Hindi operation-word misreading.
- Pre-generation freeze owners and deadlines, all before 31 Oct: question-only token counts, English tags, vocabulary strata, taxonomy, self-translate/second-model decisions, plus adopted CMI/endpoints and the human/data/hash gate.
- Recommendation: add self-translate only if its full exploratory protocol is adopted by 24 Oct; otherwise explicitly defer. Defer a second model from required paper scope; task 19 can inform a fully specified override before that same deadline. Neither recommendation is adopted here.
- Dated milestones to the 6 Nov mentorship draft and 15 Dec direct submission, with an honest work-in-progress fallback if human review or auditing slips.

Important integration points:
1. D018/D020 supersede the venue note's proposed two-auditor and v1+v2 pilot design. The plan preserves the single bilingual auditor/A01 spot-check workflow and frozen v2 direct pilot.
2. FMT2's 10→0 invalid-output comparison changed both prompt and fixture version. It is not a clean prompt-only intervention; two operation-word cases do not identify a lexical cause. Devanagari absence does not certify English compliance.
3. `paper_analysis/` supplies score tables and figures but ignores manual overlays; audit, question-token and vocabulary summaries require verified sidecars or a later approved extension. Its UNADOPTED numeric label is stale relative to D018; no code/docs were modified to fix it.
4. Checked the official SRW call on 15 Oct: 6 Nov mentorship, 5 Dec feedback, 15 Dec direct submission (AoE); even mentorship drafts must be anonymized. Source: https://2027.eacl.org/calls/srw/ .

Validation: read the requested source files and team board; checked tool capabilities against its README/source, page budgets sum to 4.00, and plan length is below 120 lines. No software tests needed for these proposal-only documents. The planning task is complete; the human-review/generation gate has not advanced. Claude's next action is to review/adopt or reject the proposed scope and dates; human availability remains unconfirmed.
