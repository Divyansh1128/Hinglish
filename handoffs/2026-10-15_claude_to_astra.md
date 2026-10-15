# Claude → Astra, 15 October 2026 (task 12)

Read first: docs/TEAM_BOARD.md, docs/DECISIONS.md (D017–D020), research/fmt2_format_test_2026-10-14/README.md.

Context: under prompt v2 the only remaining FMT2 errors were R-only misreadings of Romanized-Hindi operation words. "bhaag dekar bhinn likho" (divide, write a fraction) was treated as a difference, and "kitna bhinn istemaal hua" (what fraction was used) was answered with the remaining count. *Bhinn* also means "different". This is development evidence (n=2), not a result.

Write ONE document: research/operation_vocabulary_2026-10-15.md (aim for under 150 lines). Cover:

1. Bounded literature check: is misreading of Hindi/Romanized-Hindi (or other code-mixed/low-resource) mathematical-operation vocabulary by LLMs already documented? Also cover math word-problem keyword/operation-cue studies, Hindi/Hinglish math benchmarks and transliteration ambiguity. Cite primary sources with links; say plainly what you could not find. Time-box it; do not expand the general novelty audit.
2. A small lexicon of Romanized-Hindi operation/relation words likely to appear in the pilot domain (e.g. jod, ghata, guna, bhaag, bhinn, anupat, pratishat, kam, zyada, bacha, kul), with English meaning, known homographs/ambiguities and common spelling variants. Mark each entry as a proposal needing bilingual human confirmation.
3. A tagging table for the 30 DRAFT pilot families: for each R and C rendering, list which lexicon operation words appear (read pilot/annotation_draft_v2/coordinator/pilot_dataset.DRAFT.json). Give rendering IDs and words ONLY: no gold values, no answers, no wording suggestions. This is a pre-registered descriptive covariate, frozen before pilot generation. It must not be used to edit pilot wording.
4. A pre-specified exploratory analysis for the pilot: descriptive error rates for renderings with vs without ambiguous operation words, per form, with the audit taxonomy category. Say clearly that 30 families cannot support inference and that this is hypothesis generation for the training/confirmatory stage.
5. How to make operation vocabulary a deliberate, balanced design feature of the future (post-pilot) datasets.

Constraints: modify no other file except your handoff. Do not change scorer, prompt, packets v1/v2 or Sol's files. Sol is working in t4_smoke/ and secondary_analysis/ at the same time. No model inference, training or paid APIs. No commits, pushes, resets or branch changes. Label proposals as proposals. Cite where any user statement comes from; do not cite prior conversations as "today's" user replies.

When finished write handoffs/2026-10-15_astra_to_claude.md: files changed, key findings in 5 bullets, open questions.
