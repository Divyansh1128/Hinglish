# Astra → Claude, 15 October 2026 (task 12 complete)

Files written by Astra:

- `research/operation_vocabulary_2026-10-15.md`
- `handoffs/2026-10-15_astra_to_claude.md` (this handoff)

Key findings:

1. Primary literature documents English LLM operation-cue failures (GSM-NoOp), earlier shallow MWP heuristics (SVAMP), and human lexical-consistency effects. The bounded search did not locate a primary study isolating Hindi/Romanized-Hindi operation-word polysemy as an LLM error cause, or an equivalent controlled result in another code-mixed/low-resource language. This is not a novelty claim.
2. HAWP, GSM8K-Hi, CodeMixBench and Sarvam's native/Romanized Indic evaluations establish relevant benchmark precedents. HAWP also documents word-sense problems in translation; those are dataset-construction errors, not evidence of the proposed LLM mechanism. Transliteration literature supports spelling/context controls. The dictionary confirms that fraction/different polysemy of `bhinn` already exists in Hindi script.
3. The document proposes 25 operation/relation entries, each explicitly needing bilingual confirmation. It separates lexical ambiguity-family exposure (A) from contextual relation cues (C). A is a broad surface-family risk proxy, not proof that a sentence is ambiguous or that vocabulary caused a model error.
4. All 60 R/C rendering IDs across 30 DRAFT families have reproducible, question-only lexical tags, with no gold values, answers or wording suggestions in the table. Any-match counts are R 27/30 and C 10/30; A-family counts are R 19/30 and C 5/30. The fixed `bhaag`/`bhinn` subset occurs in R 2/30 and C 0/30, so a C exposed/unexposed comparison for that subset is unavailable.
5. The pre-specified exploratory proposal reports within-form counts/rates by exposure for both frozen endpoints and the adopted audit categories, with explicit missingness/empty-cell rules and no inference from 30 families. Future proposals counterbalance Hindi/English operation words inside C and distinguish polysemy, script/spelling and contextual cues. None of this authorizes pilot wording or prompt changes.

Verification: research document is 111 lines; all 30 families/60 exact versioned IDs are covered once. Tags were generated deterministically from the finite lexicon and question texts and checked against the source. Source DRAFT SHA-256 remains `9a4434b67941505e9a3679ba6cf0c344f50804230e4fd3591df1f3e192d4711a`. No inference, training, paid APIs, commits, pushes, resets or branch changes. No scorer, prompt, packet, Sol-owned or board/decision files were written by Astra.

Freeze artifact: research document SHA-256 `b70f967a5b8df3dccabb8afcfefc66a3881765b15836482f1d4366c48a8e78e4`. Independent regex verification matched every table cell; all local links resolve. Other agents' concurrent changes are visible in git status and were left untouched.

Open questions for integration (not claims of completed review):

- A bilingual reviewer still needs to confirm the proposed lexicon's meanings, spellings and ambiguity labels before causal interpretation; the current snapshot is explicitly unconfirmed. Do not select ambiguity labels using pilot outcomes.
- If independent human review changes the DRAFT text, the accepted-text tags need a separately versioned freeze with exact IDs/hashes before generation; preserve this snapshot and do not use tags to motivate wording edits.
- Future balancing quotas, confirmation sample size and independent reviewer budget remain undecided; this task makes no adoption claim about them.

Gate status: task 12's literature check and concrete pre-generation DRAFT covariate table are complete. Human acceptance of the pilot and interpretation of lexical ambiguity remain pending. The task-specific scope came from [Claude's handoff](2026-10-15_claude_to_astra.md); adopted pilot workflow/provenance remains [D017–D020](../docs/DECISIONS.md), not a newly invented user reply.
