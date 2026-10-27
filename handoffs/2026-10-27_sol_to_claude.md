# Sol → Claude, 27 Oct 2026: D021 T4 training-feasibility smoke notebook

**Authorship note:** a Claude Opus subagent did this work in place of Sol, because Sol's Codex authentication had expired. It is not an independent GPT implementation, so it gives no cross-model check of the code. If an independent review is wanted, Sol (or GPT) should audit it once Codex access is restored.

Scope followed: only t4_smoke/, colab_notebooks/training_smoke/ and colab_notebooks/build_training_smoke_notebook.py were written. No DEV or FINAL_TEST file was opened by code or tests. No data files, test1_pilot/, secondary_analysis/, paper/, report/ or results/ were modified. No commits.

## Files

| File | Status | Content |
|---|---|---|
| `t4_smoke/train_smoke.py` | new | Model-free selection, arms, schedule, summaries and the go/no-go rule; lazy-import GPU runner with the `preflight`, `run --phase first/resume/probe` and `decide` commands |
| `t4_smoke/test_train_smoke.py` | new | 29 model-free tests |
| `t4_smoke/README.md` | edited | Status and D021 runner section; the "Remaining" list now names only the GPU run |
| `colab_notebooks/build_training_smoke_notebook.py` | new | Deterministic builder (fixed ZIP timestamps); `--check` reports whether the notebook is current without writing |
| `colab_notebooks/training_smoke/TrainSmoke_Qwen3-4B.ipynb` | new (generated) | Self-contained notebook with 10 cells |

`colab_notebooks/README.md` is outside my write scope and does not yet list the new notebook. Add a row there.

## What it does

- **Stack.** Colab's torch is checked against `2.11.0+cu130` but never reinstalled. pip installs transformers 4.51.3, bitsandbytes 0.50.2, peft 0.15.2, accelerate 1.6.0, huggingface-hub 0.30.2, tokenizers 0.21.1, safetensors 0.5.3 and nvidia-ml-py 12.570.86. A stack mismatch stops the run unless `ALLOW_STACK_MISMATCH = True`; any mismatch is recorded and flagged in `decision.json`. Every report records the exact versions and the `pip freeze` output with its hash.
- **Model.** Qwen/Qwen3-4B at revision `1cfa9a7208912126459214e8b04321603b3df60c`, the one used by the inference runs.
- **Recipe.** NF4 with double quantization and FP16 compute (the code requires exactly 252 Linear4bit modules), followed by `prepare_model_for_kbit_training` with non-reentrant checkpointing (the checkpoint function's keywords are asserted).
  - LoRA: r16, alpha 32, dropout 0.05 on the 7 projections, seeded at 11 before initialization so every arm starts from the same adapter.
  - Adapters are forced to fp32, and the trainable count is asserted to be 33,030,144, all of them `lora_` parameters.
  - Optimizer: AdamW at lr 1e-4 (betas 0.9/0.999, eps 1e-8, weight decay 0), with optimizer membership asserted equal to the adapter set.
  - GradScaler starts at 2^16; gradients are clipped at 1.0.
  - Microbatch 1, accumulation 16, cap 1024, no packing, `use_cache=False`, SDPA forced to math only (flash, mem-efficient and cudnn disabled globally), TF32 off, deterministic algorithms with warn_only.
  - Loss is a fp32 cross-entropy over the supervised positions only. It uses `logits_to_keep = n+1` and drops the last row, so the causal shift is explicit; if that argument is missing it falls back to slicing the full logits. Loss is averaged per example and divided by 16.
- **Labels.** Built with `labels.build_example`, using the frozen prompt v2 (`protocol.INSTRUCTION`, already tested byte-equal to the engine). `assert_matched_targets` runs for every family. The tokenizer-only preflight decodes every supervised span and every prompt ending, checks that the last target token is `<|im_end|>`, and records joint-tokenization round-trip as information only.
- **Data.** 8 families come from each frozen TRAIN file. Each file's SHA-256 is checked against TRAIN_DEV_FROZEN.md, and families are ranked by `sha256('D021-smoke-2026-10-27:' + family_id)`. Every family must be `CONFIRM_TRAIN`.
  - Selected: TRA012, TRA017, TRA034, TRA047, TRA066, TRA069, TRA075, TRA080, TRB004, TRB014, TRB016, TRB033, TRB035, TRB051, TRB067, TRB069. All six topics are covered.
  - Only the renderings, the English solution and the IDs are embedded; gold fields are not.
- **Arms.** Each family contributes E, then the arm's second form (E+E is E twice), cycling over 32 examples. Six updates cover the cycle three times; the 32-update probe covers it 16 times.
- **Per arm.**
  - Process 1 runs updates 1–4. It then computes a fixed probe (logits for the first family's E example, dropout off) and saves the adapter (`save_pretrained` plus raw tensors), optimizer, scaler, torch/CUDA/Python RNG, cursor and digests.
  - Process 2 loads the model again from scratch and restores that state. It checks allclose(atol=rtol=1e-3) on the adapter, optimizer state and probe logits, and checks exact equality for the scaler, RNG and cursor; exact digests are also recorded. It then runs updates 5–6.
  - After that, a 32-update E+C probe runs in its own process.
- **Measurements, recorded per update.** Wall time with synchronization, per-microbatch losses, gradient norm, scale before and after (a skip is detected as a scale decrease), input and supervised tokens, peak allocated and reserved memory, and minimum free memory. Free memory comes from both `mem_get_info` after every microbatch and a background NVML sampler at about 4 Hz. The minimum free memory during model load is recorded too.
- **Decision** (`decide()`, written to `decision.json`). The worst arm's median over updates 3–6 sets the tier: ≤56 s → COLAB, ≤150 s → KAGGLE_2xT4, otherwise FALLBACK_QWEN3_1_7B. The fallback stands even if other checks also fail.
  - Any of these failures gives NO_GO_INTEGRITY:
    - a preflight failure
    - an incomplete run or missing updates
    - an OOM
    - minimum free memory below 2 GiB
    - a non-finite loss
    - a scaler skip or non-finite gradient norm after update 4
    - a failed reload check
    - an incomplete or failing E+C probe
    - initial adapters that differ across arms
  - Skips before update 5 are counted but do not fail the gate.
  - The output also gives the 2304-update projection, 3×256×Σt/3600×1.4.
- **Notebook.** The notebook has no shell magics. It checks for a T4 via nvidia-smi, installs the pins and prints versions from a fresh interpreter (the notebook kernel never imports torch). Phases already marked COMPLETE are skipped when re-run, which with the optional `USE_DRIVE` lets a run resume after a disconnect. Every attempt is appended to `attempts.jsonl` and the output to `log.txt`. The results ZIP contains `SHA256SUMS.txt`; `.pt`/`.safetensors` checkpoints are left out, but their hashes are listed.

## Tests (run from the project root)

- `python3 -B -m unittest discover -s t4_smoke -p 'test_*.py'`: **Ran 50 tests, OK.** That is 21 existing tests plus 29 new ones.
- `PYTHONPATH=test1_pilot python3 -B -m unittest discover -s test1_pilot/tests -p 'test_*.py'`: **Ran 23 tests, OK.**
- Also passing: `python3 -B t4_smoke/protocol.py self-check` and `python3 -B colab_notebooks/build_training_smoke_notebook.py --check` (reports the notebook current).
- I also ran the extracted payload's `train_smoke.py decide` in script mode on an empty folder. It imports correctly and returns NO_GO_INTEGRITY.

The new tests cover:
- **Selection:** deterministic and independent of input order; follows the recorded hash rule; 8 families per file; refuses non-CONFIRM_TRAIN roles, hash mismatches and extra or missing files. A spy on `Path.read_bytes` confirms only the two TRAIN files are read.
- **Arms and labels:** arm order and cursor cycling; identical targets across arms; masking with the fake tokenizer and an audit that catches a tampered label; overlength and literal special tokens are rejected.
- **Recipe:** agrees with every key it shares with `protocol.CONFIG`; the 33,030,144 parameter count is derived from the Qwen3-4B shapes.
- **Decision:** the decision function on synthetic timings, including the 56 and 150 boundaries and the worst-arm rule, plus every integrity failure and non-finite values written as JSON-safe strings.
- **Notebook:** the committed file is current and deterministic; every code cell compiles; the payload code is byte-identical to the repo, its data equals a fresh selection, and it embeds no gold, DEV or FINAL_TEST markers.

## Unverified until it runs on a real T4

None of the torch, bitsandbytes, PEFT or real-tokenizer code has executed. torch is not installed on this machine, so the GPU path was only reviewed by reading it. In particular:

1. Compatibility of PEFT 0.15.2 with bitsandbytes 0.50.2 (flagged as unverified in the research), and whether Colab still ships torch 2.11.0+cu130 when the notebook is run.
2. Whether `prepare_model_for_kbit_training` and `get_peft_model` give exactly 33,030,144 trainable fp32 parameters, with checkpoint keywords `use_reentrant=False`, on these versions. Both are hard assertions, so a mismatch stops the run with a clear message.
3. Whether `logits_to_keep` reaches Qwen3 through the PEFT wrapper, whether the loss slice is right on real shapes, and whether the real tokenizer passes the mask audit (prompt ends with the empty think block, decoded target equals solution plus `<|im_end|>`, IDs identical across E/R/C, all within 1024 tokens).
4. FP16 numerics in the backward pass: finite losses, how many early GradScaler skips occur, and no skips after update 4 or across the 32-update probe.
5. Reload fidelity across processes within 1e-3, since NF4 kernels may not be bitwise deterministic. This includes whether `torch.load(weights_only=True)` accepts the optimizer and scaler state dicts.
6. Every number the go/no-go depends on: seconds per update per arm, peak allocated and reserved memory, minimum free memory, tokens per update, and therefore the Colab, Kaggle or 1.7B decision. The research gives only an estimate (8–55 s/update, a peak of 5.5–7.5 GB).
7. The notebook as a whole on Colab: the pip install on the current image, NVML availability (it degrades to the torch-only samples), runtime (estimated 40–120 min) and the ZIP download.

## Notes for Claude

- The 16 smoke families come from CONFIRM_TRAIN. Smoke adapters are thrown away, but if strict "never trained on before" bookkeeping matters for TRAIN, record these IDs.
- The existing `t4_smoke/requirements.txt` still pins the old 2.7.1/0.45.5 stack, which is now the D021 fallback. The new pins live in `train_smoke.PINS`, and the notebook writes `requirements-train.txt` from them.
- Suggested next step: run the notebook once on Colab and review `decision.json` and the per-phase reports before any fix attempt. D021 allows one fix attempt, then the fallback.
