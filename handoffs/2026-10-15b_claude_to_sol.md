# Claude → Sol, 15 October 2026, 13:50 IST (task 17). HARD STOP 14:08 IST

Read: docs/DECISIONS.md D021 and research/claude_deep_research/training_feasibility_2026-10-15.md (masking section).

Build, in t4_smoke/ ONLY, a new file `t4_smoke/labels.py` plus `t4_smoke/test_labels.py`. Python standard library only; no torch or transformers imports at module level.
- `build_example(tokenizer, instruction, question, solution)` → dict(input_ids, labels). It uses `tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)` for the prompt (system=instruction, user=question). The prompt, including the empty think block, is fully masked (-100). Supervised tokens = tokenize(solution + "<|im_end|>") with add_special_tokens=False. Return the boundary index too.
- `assert_matched_targets(examples_by_form)`: the supervised label IDs must be identical across E/R/C for a family.
- No truncation: raise if len > max_length.
- Tests use a small FAKE tokenizer class (whitespace or char-level, with a Qwen3-like template that emits `<think>\n\n</think>\n\n` when enable_thinking=False). Cover: prompt and think block masked, target identical across forms, overlength raises, label count equals solution tokens + 1.
Do not modify other files. No commits. Write handoffs/2026-10-15b_sol_to_claude.md (files, test count) before 14:08.
