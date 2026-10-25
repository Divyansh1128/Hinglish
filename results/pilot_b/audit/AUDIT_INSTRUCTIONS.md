# Pilot-B output audit: AI pre-tagging instructions (endpoint 6)

Input: `qwen3-4b_outputs_for_audit.jsonl` (210 Qwen3-4B outputs: question, gold, model output, stored strict score). Two independent AI taggers (Claude, GPT) tag every row **without seeing each other's tags**. A human checks only the rows where the taggers disagree, plus a random sample. These are **AI pre-tags, not human judgments**.

Taxonomy and English-compliance definitions: `research/pre_pilot_endpoint_spec_v1.md` sections 3 and 4. Apply them exactly.

For every row write one JSON line:
- `rendering_id`
- `category`: exactly one of truncated, refusal, unresolved, misread_quantity, wrong_relation_operation, arithmetic_slip, unit_error, format_only, language_drift, no_error. Take the first applicable in this precedence order. If the final answer is mathematically correct and the explanation is English, use `no_error`. If the answer is correct but the strict score failed only on serialisation, use `format_only`.
- `additional_categories`: list (may be empty).
- `english_status`: one of compliant, non_english, no_explanation, uncertain (section 4 rules; numbers, equations, names, units and the FINAL line do not count as prose).
- `evidence`: a short quote from the model output supporting the category (max 25 words).
- `reason`: one sentence.

Never change the stored strict score. Do not guess causes: use `unresolved` if the evidence is insufficient.
