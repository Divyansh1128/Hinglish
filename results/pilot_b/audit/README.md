# Pilot-B output audit (pre-registered endpoint 6), Qwen3-4B primary backbone

- Two independent AI pre-taggers labelled all 210 outputs under `AUDIT_INSTRUCTIONS.md`: Claude (`claude_tags.jsonl`) and GPT (`gpt_tags.jsonl`), each blind to the other's tags.
- Agreement: error category 206/210 (Cohen's κ = 0.94); English compliance 208/210 (κ = 0.96).
- **Human check** (`human_check_sheet.csv`): the 4 disagreement rows plus 20 seeded random agreed rows (seed 101). Taggers are anonymised as A and B. The human fills `YOUR_category`, `YOUR_english_status` and `YOUR_note`. Final audit = human label where checked; otherwise the agreed AI label, reported as **AI pre-tag, human-checked on disagreements and a sample**.

## Final audit (27 October 2026)
The human check was returned (`human_check_returned.csv`, 24/24 rows). Human labels agree with tagger A on 22/24 and with tagger B on 21/24. The human label "ambiguous" (PB033-R, question flagged as ambiguous) is mapped to `unresolved`. Final labels (`final_audit_qwen3-4b.csv`): human label where checked (24), otherwise the agreed AI label (186). Summary (`final_audit_summary.json`): of 18 strict failures, 6 are format_only; substantive errors E 1 / R 8 / C 3; English-compliant explanations E 70 / R 53 / C 59 of 70. The coordinator performed the human check; this is an audit of model outputs, not of the dataset.

## Post-hoc extension: Qwen3-8B and Llama-3.2-3B (28 October–3 November 2026, not pre-registered)
The pre-registered audit covered the primary model only. This extension applies the same `AUDIT_INSTRUCTIONS.md` to the other two backbones (`qwen3-8b_outputs_for_audit.jsonl`, `llama-3.2-3b_outputs_for_audit.jsonl`, 210 rows each).
- Three taggers, each blind to the others: A = Claude Opus (`claude_tags_<model>.jsonl`), B = GPT (`gpt_tags_<model>.jsonl`, added 3 November once Codex was available again), C = Claude Sonnet (`second_tags_<model>.jsonl`, run while GPT was unavailable).
- Agreement (`extension_agreement.json`), category / English status:

| Model | A vs B (cross-family, headline) | A vs C (both Claude) | B vs C |
|---|---|---|---|
| Qwen3-8B | 200/210 (κ 0.87) / 209/210 (κ 0.99) | 207/210 (κ 0.96) / 209/210 (κ 0.99) | 197/210 (κ 0.83) / 208/210 (κ 0.97) |
| Llama-3.2-3B | 187/210 (κ 0.84) / 208/210 (κ 0.98) | 205/210 (κ 0.97) / 210/210 (κ 1.00) | 190/210 (κ 0.86) / 208/210 (κ 0.98) |

- The two Claude taggers agree with each other more than either agrees with GPT, as expected for same-family raters; the cross-family pair is the headline.
- Human check (`human_check_sheet_extension.csv`, built by `build_extension_sheet.py`): every row where any two taggers differ (13 Qwen3-8B, 24 Llama) plus 30 seeded random all-agree rows per model, 97 rows in all. Pending the human's return. This sheet replaces the 68-row two-tagger version of 28 October.

### Human check returned (10 November 2026)
`human_check_extension_returned.csv`: 97/97 rows labelled, all with a note; no fixed column changed. The checker's role and credit preference are still to be recorded. The checker agreed with all 60 unanimous sample rows. On the 37 disagreement rows, the checker's category matched A on 32, B on 5 and C on 30. Category agreement with the human over all 97 rows: A 92, B 65, C 90; English status: A 94, B 95, C 95. `finalize_extension.py` writes `final_audit_qwen3-8b.csv`, `final_audit_llama-3.2-3b.csv` and `final_audit_extension_summary.json`: the human label where checked, otherwise the unanimous AI label. There are no format-only R failures for either backbone. Qwen3-8B has 6 substantive R errors; Llama has 25 substantive R errors plus 5 truncations. English-compliant R explanations: Qwen3-8B 37/70, Llama 0/70. Descriptive and post hoc; strict scores are unchanged.
