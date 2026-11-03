# Claude → GPT audit tagger, 3 Nov 2026 (post-hoc audit extension, cross-family rater)
Follow results/pilot_b/audit/AUDIT_INSTRUCTIONS.md exactly. Inputs: results/pilot_b/audit/qwen3-8b_outputs_for_audit.jsonl and results/pilot_b/audit/llama-3.2-3b_outputs_for_audit.jsonl (210 rows each).
Write ONLY results/pilot_b/audit/gpt_tags_qwen3-8b.jsonl and results/pilot_b/audit/gpt_tags_llama-3.2-3b.jsonl. Use the same six fields as results/pilot_b/audit/gpt_tags.jsonl; read only its first 2 lines, for the schema.
Do not open any claude_tags*, second_tags*, human_check*, final_audit* or extension_agreement* file.
Conventions:
- A food word that the E questions themselves use (ghee, dal, paneer, samosa, laddoo, gulab jamun, kaju katli) counts as English.
- Any other Hindi word in the English prose makes the explanation non_english.
- The FINAL line is excluded from the English judgement.
Tag every row from your own reading. No commits.
