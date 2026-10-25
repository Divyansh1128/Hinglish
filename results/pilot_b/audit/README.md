# Pilot-B output audit (pre-registered endpoint 6), Qwen3-4B primary backbone

- Two independent AI pre-taggers labelled all 210 outputs under `AUDIT_INSTRUCTIONS.md`: Claude (`claude_tags.jsonl`) and GPT (`gpt_tags.jsonl`), each blind to the other's tags.
- Agreement: error category 206/210 (Cohen's κ = 0.94); English compliance 208/210 (κ = 0.96).
- **Human check** (`human_check_sheet.csv`): the 4 disagreement rows plus 20 seeded random agreed rows (seed 101). Taggers are anonymised as A and B. The human fills `YOUR_category`, `YOUR_english_status` and `YOUR_note`. Final audit = human label where checked; otherwise the agreed AI label, reported as **AI pre-tag, human-checked on disagreements and a sample**.
