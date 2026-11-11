# Phase-3 target generation (step 1)

- `Phase3_Targets_results.zip` (SHA-256 `558c6fdfde1c8fa05245b59a54a09f1ac6c1e2a62c0dc197a7dabb00c7d501cf`): the Colab T4 run as returned. 160/160 TRAIN E renderings generated in one launch, 160 attempts, no retries; stack torch 2.11.0+cu130, transformers 4.51.3, bitsandbytes 0.50.2, PEFT 0.15.2; all internal checksums verify.
- `Phase3_Targets_frozen.zip` (SHA-256 `2e05232ea20b6fb36efb7848107b7c0a13ac09b271248082f4ecddb69ca59100`): the same run folder after `phase3_targets.py freeze`, re-sealed with the (empty) human return. Bound in `phase3/TARGETS_FROZEN.md`.

## Selection (PREREGISTRATION §3)

- **Q = 158 of 160** (threshold 120): branch *proceed*.
- Excluded: 2 families, both strict-incorrect (one also had an invalid terminal FINAL line).
- Language gate: 0 Devanagari, 0 flagged by the Romanized-Hindi word list, so no human review was needed.
- Length gate: no candidate exceeded 1,024 tokens on any form.
- Target length (supervised tokens incl. `<|im_end|>`): median 106, range 44–223.
- Explanation status (descriptive heuristic, never used for selection): 107 "explanatory proposition", 53 "labelled equations only". The heuristic's verb list is narrow (e.g. "we add 38" counts as labelled equations), so it undercounts explanations.

The local freeze (pinned transformers 4.51.3 / tokenizers 0.21.1 tokenizer) recomputed every family's text and target-token hashes, lengths and decisions; all 160 match the Colab ledger exactly.
