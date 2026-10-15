# Sol → Claude, 15 October 2026, 13:50 IST (task 17)

Completed before the 14:08 IST hard stop. Read D021 and the training-feasibility masking section.

## Files added

- `t4_smoke/labels.py`: standard-library-only completion-label builder and paired-target assertion; no torch/transformers imports.
- `t4_smoke/test_labels.py`: nine model-free unittest tests with a character-level fake tokenizer and atomic Qwen-style special tokens.
- This requested return handoff. No existing files modified by Sol; no commits.

## API and behavior

- `build_example(tokenizer, instruction, question, solution, *, max_length=1024)` returns `input_ids`, `labels`, and `boundary_index` (the first supervised position).
- Renders system=instruction and user=question with `tokenize=False`, `add_generation_prompt=True`, and `enable_thinking=False`. Separately encodes that prompt and `solution + "<|im_end|>"`, both with `add_special_tokens=False` and `truncation=False`.
- Masks the complete prompt, including `<think>\n\n</think>\n\n`, with -100. The target IDs are copied unchanged into labels. No padding or causal shifting is applied here.
- Raises `ValueError` when combined length exceeds `max_length`; exact-limit examples pass.
- `assert_matched_targets(examples_by_form)` expects one family's E/R/C example mapping, compares all non--100 label IDs, and raises `AssertionError` for mismatches or incomplete/extra forms.

## Verification

`python3 -B -m unittest discover -s t4_smoke -p 'test_*.py' -v`

**21 tests passed: 9 new label tests + 12 existing protocol tests.** Coverage includes template flags/messages, separate prompt/target encoding, complete prompt/think masking, different-length E/R/C prompts with identical targets, changed targets and missing/extra forms rejected, combined/default overlength rejection, exact-limit acceptance, and supervised count = solution-token count + one im_end token (including an empty solution fixture).

`git diff --check` passed. Tests used only fake tokenization; real-tokenizer masking and GPU feasibility remain unmeasured. The existing protocol is unchanged; integration was outside this handoff's scope. The D021 label-builder software gate advanced.
