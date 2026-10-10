# Test 1 JSON contract (test1-1)

This is a JSON adaptation of pilot_review_packet.md's family/rendering/review/split tables. Original files remain unchanged. The complete schema is shown in templates/pilot_dataset.template.json and templates/split_manifest.template.json. Templates deliberately fail validation. No accepted research dataset is supplied.

## Dataset

Upload pilot_dataset.json, an object with exactly schema_version, version, kind, borrowing_policy and families. schema_version is test1-1; kind is reviewed. Supply 30 genuinely independent families: five per topic. Topic keys map to the packet:

| Key | Packet topic |
|---|---|
| comparison_remaining | comparison / remaining quantities |
| two_step_money | two-step money |
| fractions_percentages | fractions / percentages |
| ratios | ratios |
| rates_units | rates / units |
| elementary_algebra | elementary algebra |

Every family supplies three identity fields (family_id, source_family_id, template_group_id), topic, PILOT_EVAL split_role, version, authoring_origin, provenance, source_license, reference_equation, reference_solution_en, ACCEPT status, gold, forms and review. Use stable safe IDs, not names or emails. A source/template grouping is a leakage identity for a specific underlying problem family, not a broad mathematical skill label. Number changes and paraphrases stay with their source family. The validator rejects shared source/template identities within the 30 slots; do not evade that check with invented IDs.

Forms is an object keyed E/R/C. Each rendering has rendering_id, text, creator_type, generation_or_edit_history and switching_roles. C must document productive switches (e.g. comparison, rate, requested_answer); English object nouns alone do not establish code mixing. Preserve AI origin after human editing. The borrowing policy and human judgment establish classification; no automated language detector claims to certify it.

Gold has value (exact numeric STRING such as "1/3" or "0.5"), unit, aliases, conversions (unit to exact canonical multiplier), unit_omission_allowed (boolean) and rounding_rule. This pilot implements exact equality only. For questions explicitly requesting a rounded answer, store that predetermined answer as an exact value and document the rounding instruction/method in the question and reference solution. Otherwise avoid approximate-answer questions. Example: value "1", unit "m", aliases ["metre", "metres"], conversions {"cm":"1/100"}. Do not provide an arbitrary floating tolerance. Explicitly wrong units remain incorrect even where unit omission is permitted.

Review contains two independent reviewers and adjudication. Each reviewer has reviewer_id, independent_solve_before_gold and forms keyed E/R/C. Each form record contains its reviewed text_sha256, independently obtained equation and canonical answer/unit, semantic_equivalence, ambiguity_resolved, classification, naturalness, readability and disposition. Both scores must be 4–5, classifications must match, and acceptance/equivalence/ambiguity checks must pass. A distinct adjudicator supplies adjudicator_id, status ACCEPT, zero unresolved_issues and reviewed_at.

Compute the rendering hash with Python:

```python
import hashlib
text_sha256 = hashlib.sha256(rendering_text.encode('utf-8')).hexdigest()
```

Editing text invalidates the accepted review hash. Retain raw first-pass reviews, revisions and adjudication history in your source annotation records; JSON captures the accepted version for this pilot. Independent equations cannot be checked for algebraic equivalence automatically. Review fields are attestations; setting booleans does not perform human review.

## Split manifest

Upload split_manifest.json. Required fields: schema_version, version, kind, audit, PILOT_EVAL, SMOKE_TRAIN, RETIRED_DRAFT, CONFIRM_TRAIN, FINAL_TEST and development_exclusion_ids. Each role list contains identity-only records with family_id/source_family_id/template_group_id. PILOT_EVAL must exactly match the dataset. Other lists cover all known families, not fabricated future IDs. Empty future splits are allowed when not yet created.

Keep the template's test1-format-smoke-v1 identity in SMOKE_TRAIN and all three IDs in permanent exclusions. It is a software format fixture, not the packet's 16 human-audited training-smoke families. Include the actual 16 and the five illustrative pilot drafts/descendants when known: a draft adopted into PILOT_EVAL belongs there; unadopted drafts belong in RETIRED_DRAFT. Do not assign the same underlying identity to two roles.

Development exclusions must include ALL pilot, smoke and retired identities and their known descendants. CONFIRM_TRAIN/FINAL_TEST must not overlap any exclusions or one another. Complete a genuine human cross-split audit: audit.approved true, pseudonymous reviewer_id, unresolved_matches 0 and audited_at. Matching IDs cannot find undisclosed near-duplicates; human inspection remains required.

## Privacy and provenance

Only documented fields are accepted. Use pseudonymous reviewer IDs. Keep identity/contact mappings outside the shareable package. Record licensed source URLs or document identifiers, avoiding sensitive query strings. Do not paste Hugging Face tokens into data/config/notebook cells; public Qwen access normally needs no token. The export blocks common credential and email patterns, but cannot identify every personal detail in arbitrary prose: review free text before sharing.

## Demo

kind demo, family status DEMO, split_role DEMO; reviewer list empty, adjudication null, split audit null. The supplied two synthetic families are software fixtures, not naturalness-validated Hinglish, and cannot pass reviewed mode. Do not turn fixtures into accepted data by changing status flags.
