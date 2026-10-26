# Astra → Claude: novelty refresh for the short paper

Requested filename date: 27 October 2026. Work actually performed and sources checked **26 October 2026**; no future search coverage is implied.

Delivered:

- `research/novelty_refresh_2026-10-27.md`: 15-source comparison matrix, verified full citations/locators, search/access limitations, verdict, exact Introduction positioning sentence and submission-facing cautions.
- `research/novelty_refresh_2026-10-27.bib`: 11 verified new/replacement citation candidates. Four already-cited sources are not duplicated. Optional references are distinguished from essential additions in the memo.

## Decision for integration

The broad R<C framing is **not new**: Sthānika's CodeMixTax explicitly compares aligned Romanized Hindi and Romanized Hinglish on GSM8K. Cite it as direct prior work, not merely as an aligned dataset. Peter et al., GEM 2026, is essential missing related work on translation/extraction-induced multilingual math gaps. The exact Qwen/cohort/protocol result was not found, but that is a bounded search result, not novelty proof. Position the paper as a reproducible small-model audit/extension on new reviewed problems.

Use the exact sentence proposed in the memo; say **equal observed aggregate E/C accuracy**, not established equivalence. Retain Llama's E/C deficit. Native-script control is absent, so do not infer a causal script effect. Keep 70-family Pilot-B and 24-family original cohort separate.

Additional priorities: TeluguEval; Khattar et al.'s 19 October 2026 Indic pretraining/evaluation preprint; MathIF; Azime et al.'s multilingual math localization. Script Gap now has an EMNLP 2026 Industry proceedings record; replace its old preprint label/key if integrated. Do not import every optional citation into a four-page paper.

## Manuscript issues exposed by the refresh

- D037 supersedes earlier two-independent-language-review claims: two independent solves, R02+A01 language review, R01 AI-prefill judgments excluded. Original RESULTS files now exist while main.tex still has pending-cohort text.
- Strict/numeric agreement does not establish absence of formatting confounds: both can reject the same malformed or truncated response. Keep the audit outstanding and preserve frozen scores.
- Equal E/C counts hide discordant items; ceiling-cohort zero bootstrap width is not evidence of population equivalence.
- Development prompt/fixture/alias changes cannot be attributed solely to prompting. Sparse lexical strata cannot rule out every vocabulary explanation.

## Verification and limits

Read all requested local inputs, team board and latest handoffs. Checked substantive citations against primary ACL/arXiv/author sources; inspected relevant full-text sections for closest comparisons. OpenReview was searched and a relevant PDF inspected. Semantic Scholar targeted searches/lookup produced no usable extra records; coverage is explicitly incomplete. One OpenReview lead remains UNVERIFIED and is excluded from the bibliography and verdict. No external study was rerun; no new model evaluation or human validation was performed.

Only these two research files and this explicitly requested handoff were written. No commits, pushes, branch changes, paper edits or existing-bibliography edits. The existing untracked `paper/latex/PATCH_original_cohort.md` remains untouched. Manuscript and existing bibliography hashes are recorded in the memo for verification.

Next action: review/adopt the narrower positioning, integrate chosen citations and current D037/cohort facts, then complete the scoring/language audit and remaining author decisions. This task completes the requested evidence refresh, not the submission-readiness gate.
