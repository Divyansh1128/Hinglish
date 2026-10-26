# Original-pilot cohort — frozen (decision D036)

Built by `python3 -B pilot_original/build_cohort.py` from the raw sources only. Texts, gold, units and IDs are unchanged from the v2 draft; only `status` (DRAFT → ACCEPT) and `review` (round-2 R01/R02 + A01) are filled in.

Engine mode `pilot_adjudicated`; 24 families × E/R/C = 72 prompts.

## Outputs

| File | SHA-256 |
|---|---|
| pilot_original/cohort_dataset.json | 5c3e8746f0629d1908902658bda2c280aeb388c55e741fb8e612bc49b5d43103 |
| pilot_original/cohort_splits.json | 8da8f40eaa01932152032c290f32e20345b7b22092104c0c329d63d0df0067cc |

Engine digests (canonical JSON): dataset `02752d35b6bde18392afb2e02fa3cdc430437801606706a35662bc62fe2ad03a`, splits `8f5996187c291bae21d75fbccb83486ce18bad3b9a13feaaad9fda20a2628433`.

## Sources

| File | SHA-256 |
|---|---|
| pilot/annotation_draft_v2/coordinator/pilot_dataset.DRAFT.json | 9a4434b67941505e9a3679ba6cf0c344f50804230e4fd3591df1f3e192d4711a |
| pilot/reviews_v2_round2/A01_worksheet_returned.csv | ece059d68bbb0d4233ce8e8b06dfec403c31ba92136b8299ae9aec709fd65a18 |
| pilot/reviews_v2_round2/R01_stage1_responses.json | 5445234d04d626f666db9719c165d3afdf5c912158ff5c5b933adf9e80d48e7d |
| pilot/reviews_v2_round2/R01_stage2_responses.json | 0f773fc95d3ee9e4f457b6a85669802623d94e440bd6f0a5501a97dab42149bf |
| pilot/reviews_v2_round2/R02_stage1_responses.json | c3b35de0ed8b420975816a16aa257603feb2e59d182bc6bd0adf37504e265b9b |
| pilot/reviews_v2_round2/R02_stage2_responses.json | c2e7279abc43bd6a4cf90e551b8e0a1da441f97266ed33cf5f654e6c7bace603 |

## Cohort

PIL001, PIL002, PIL003, PIL004, PIL005, PIL006, PIL007, PIL008, PIL011, PIL012, PIL013, PIL014, PIL016, PIL017, PIL018, PIL021, PIL022, PIL023, PIL025, PIL026, PIL027, PIL028, PIL029, PIL030

Out: PIL010 (A01 EXCLUDE, near-duplicate of PIL002); PIL009, PIL015, PIL019, PIL020, PIL024 (A01 REVISE; the repairs lack an independent re-review). All 30 pilot identities stay in `development_exclusion_ids`; no descendant IDs exist in the sources.

## Review metadata

- Reviewer entries copy the round-2 stage-2 rows as entered (answers are the stage-1 independent answers, verified unchanged). Ratings, dispositions, classifications, ambiguity flags and notes are not corrected, even where they conflict with each other or with gold.
- `answer_matches_gold` is derived: True iff the last number written in the raw answer equals the gold value exactly (units ignored). False entries (resolved by A01, who confirmed the gold for every cohort family):

  - PIL001-R R01: raw answer '26' (gold 31)
  - PIL011-C R01: raw answer '135' (gold 45)
  - PIL011-R R01: raw answer '135' (gold 45)
  - PIL018-C R01: raw answer '7' (gold 35)
  - PIL018-E R01: raw answer '7' (gold 35)
  - PIL018-R R01: raw answer '7' (gold 35)
- `failed_semantic_checks` lists the semantic checks the reviewer marked false.
- `adjudication.reviewed_at` = 2026-10-26, the date the A01 worksheet was returned (it has no timestamp); `reason` is A01's decision reason verbatim.
- No separate human split audit is claimed (`audit: null`).

## Provenance warning

The official `R01_stage2_responses.json` carries a field `_annotation_provenance = {"source": "AI prefill suggestion", "human_verified": false}` on 70/90 stage-2 rows (52 of the cohort's 72 R01 renderings). The project's annotation form does not write this field. It is not carried into the engine schema; the affected cohort renderings are:

PIL001-C-v1, PIL001-E-v1, PIL001-R-v1, PIL002-C-v1, PIL002-E-v1, PIL002-R-v1, PIL003-C-v1, PIL003-E-v1, PIL003-R-v1, PIL006-C-v1, PIL006-E-v1, PIL006-R-v2, PIL007-C-v1, PIL007-E-v1, PIL007-R-v1, PIL008-C-v2, PIL008-E-v1, PIL008-R-v1, PIL011-C-v1, PIL011-E-v1, PIL011-R-v1, PIL012-C-v1, PIL012-E-v1, PIL012-R-v1, PIL014-C-v1, PIL016-C-v2, PIL016-E-v1, PIL016-R-v1, PIL017-C-v1, PIL017-E-v1, PIL017-R-v1, PIL022-C-v1, PIL022-E-v1, PIL022-R-v1, PIL023-C-v1, PIL023-E-v1, PIL023-R-v1, PIL025-C-v2, PIL025-E-v1, PIL025-R-v1, PIL026-C-v2, PIL026-E-v1, PIL026-R-v1, PIL027-C-v1, PIL027-E-v1, PIL027-R-v1, PIL028-C-v1, PIL028-E-v1, PIL028-R-v1, PIL029-C-v1, PIL029-E-v1, PIL029-R-v1

R02 rows with this field: 0.

## Amendment (D037)
`cohort_dataset.json` (current SHA-256 `5c3e8746f0629d1908902658bda2c280aeb388c55e741fb8e612bc49b5d43103`) records `judgment_source` for every reviewer form: R02 72/72 human; R01 20 human and 52 `ai_prefill_unverified` (R01's stage-2 rows carrying `_annotation_provenance: AI prefill suggestion, human_verified: false`). Stage-1 answers are human for both reviewers. The conversion was cross-checked against the independent GPT implementation in `independent_expected.json`: cohort, text hashes, answers and decisions all match.

## Provenance correction (author statement, 27 October 2026)
The project author states that the **English (E) problem statements of the original 30 families were written by the author**, and that the **Romanized Hindi (R) and Hinglish (C) renderings were produced by AI translation** (OpenAI GPT via Codex) and then reviewed by humans. The draft metadata created on 10 October records `authoring_origin = AI_DRAFT` for all 30 families. Per the author, that label is mistaken for the E texts. The frozen files are left unchanged so their hashes and the review record stay valid. This note is the authoritative provenance for the original cohort (decision D038).
