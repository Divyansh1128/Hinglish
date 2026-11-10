# Phase-2 C-failure audit: AI pre-tagging instructions

Input: `phase2_outputs_for_audit.jsonl` (331 strict-incorrect C outputs: E+R 159 and E+C 172, seeds 11, 22, 33; question, gold, model output and stored scores). Adapted from `results/pilot_b/audit/AUDIT_INSTRUCTIONS.md`, the rubric frozen by `phase2/PREREGISTRATION.md`, Amendment 1 item 17. Two independent AI taggers (Claude Opus, GPT) tag every row **without seeing each other's tags**, with arm labels hidden where feasible. A human checks **every audited output**, resolves disagreements, and leaves anything still unresolved as `unresolved`. These are **AI pre-tags, not human judgments**.

Taxonomy and English-compliance definitions: `research/pre_pilot_endpoint_spec_v1.md` sections 3 and 4. Apply them exactly. The key descriptive distinction is **format-only versus substantive failure**; numeric equality alone does not establish format-only correctness. Counts must be reported over all C generations (300 per arm, 600 combined), as well as the failure-only audit counts. Do not make mechanism claims.

For every row write one JSON line:
- `rendering_id` (copy the packet's unique, run-qualified ID verbatim).
- `category`: exactly one of truncated, refusal, unresolved, misread_quantity, wrong_relation_operation, arithmetic_slip, unit_error, format_only, language_drift, no_error. Take the first applicable in this precedence order. If the final answer is mathematically correct and the explanation is English, use `no_error`. If the answer is correct but the strict score failed only on serialisation, use `format_only`.
- `additional_categories`: list (may be empty).
- `english_status`: one of compliant, non_english, no_explanation, uncertain (section 4 rules; numbers, equations, names, units and the FINAL line do not count as prose).
- `evidence`: a short quote from the model output supporting the category (max 25 words).
- `reason`: one sentence.

Never change the stored strict score. Do not guess causes: use `unresolved` if the evidence is insufficient. All labels are descriptive; they never overwrite strict scores or change the pre-registered decision label. A right numeral with a wrong unit or referent is not `format_only`; an accepted synonym rejected by metadata may be `format_only`. Review every row individually, including any labels proposed by a script.

`rendering_id` is `<arm>-s<seed>:<source_rendering_id>` to keep the Pilot-B tag schema uniquely joinable across repeated renderings. `source_rendering_id` retains the original ID; `arm` and `seed` are also separate packet fields. The `numeric` object is the archive's stored `numeric_literal_v1` diagnostic, copied without rescoring; `gold_metadata` preserves unit aliases and conversions. For blind review, use temporary row numbers and hide arm/seed/qualified IDs; restore the exact packet ID when saving tags. Do not read another tagger's labels.
