# Pilot-B output audit (pre-registered endpoint 6), Qwen3-4B primary backbone

- Two independent AI pre-taggers labelled all 210 outputs under `AUDIT_INSTRUCTIONS.md`: Claude (`claude_tags.jsonl`) and GPT (`gpt_tags.jsonl`), each blind to the other's tags.
- Agreement: error category 206/210 (Cohen's κ = 0.94); English compliance 208/210 (κ = 0.96).
- **Human check** (`human_check_sheet.csv`): the 4 disagreement rows plus 20 seeded random agreed rows (seed 101). Taggers are anonymised as A and B. The human fills `YOUR_category`, `YOUR_english_status` and `YOUR_note`. Final audit = human label where checked; otherwise the agreed AI label, reported as **AI pre-tag, human-checked on disagreements and a sample**.

## Final audit (27 October 2026)
The human check was returned (`human_check_returned.csv`, 24/24 rows). Human labels agree with tagger A on 22/24 and with tagger B on 21/24. The human label "ambiguous" (PB033-R, question flagged as ambiguous) is mapped to `unresolved`. Final labels (`final_audit_qwen3-4b.csv`): human label where checked (24), otherwise the agreed AI label (186). Summary (`final_audit_summary.json`): of 18 strict failures, 6 are format_only; substantive errors E 1 / R 8 / C 3; English-compliant explanations E 70 / R 53 / C 59 of 70. The coordinator performed the human check; this is an audit of model outputs, not of the dataset.
