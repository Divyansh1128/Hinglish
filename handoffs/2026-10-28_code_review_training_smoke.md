# Code review: D021 T4 training smoke (28 Oct 2026)

**Reviewer:** a Claude Opus subagent, standing in for the GPT reviewer, who was unavailable. This is an adversarial review, but it is not a cross-model check.

**Scope:** `t4_smoke/train_smoke.py`, `t4_smoke/labels.py`, `t4_smoke/test_train_smoke.py`, `colab_notebooks/build_training_smoke_notebook.py`, and the notebook it generates. These were checked against `handoffs/2026-10-27_claude_to_sol.md`, D021 and `handoffs/2026-10-27_sol_to_claude.md`.

**What was not changed:** the recipe, hyperparameters, data selection and thresholds. No data files were touched and nothing was committed.

## How it was checked

- **Library source.** I pip-downloaded the exact wheels and read their source: transformers 4.51.3, peft 0.15.2, accelerate 1.6.0 and bitsandbytes 0.50.2 (manylinux). I installed them in a temporary venv with **torch 2.11.0 (CPU)**.
- **Real tokenizer.** I ran the real Qwen3-4B tokenizer at revision `1cfa9a72…` through `build_examples` and `mask_audit` on the 16 smoke families.
- **CPU emulation of the training loop.** I built a tiny random `Qwen3ForCausalLM` with PEFT LoRA (all 7 targets, dropout 0.05) and non-reentrant checkpointing. The repo's own `Trainer`, `save` and `restore` ran on it, with a shim that maps "cuda" to the CPU. I then compared six straight updates against four updates, a save, a fresh model, a restore and two more updates.
- **Notebook `step()`.** I ran the generated notebook's cell 2 against stub phase scripts to exercise interrupts and undecodable output.

## Issues

| # | Severity | Issue | Evidence | Status |
|---|---|---|---|---|
| 1 | **Medium** | Interrupting a notebook cell left the phase process running on the GPU. On KeyboardInterrupt, `subprocess.Popen.__exit__` does not kill the child. Re-running the cell would then start a second training process alongside it, with three effects: contended timings that give a wrong s/update and a wrong verdict, a possible OOM, and two writers on the same report and checkpoint. | Reproduced with the original cell: after a simulated interrupt, the child was still alive. | **Fixed.** `step()` now kills and reaps the child on any exception and logs `[notebook] interrupted; phase process killed`. The attempt is still written to `attempts.jsonl` (returncode `null`). |
| 2 | Medium-low | A child output line that is not valid UTF-8 crashed the notebook's streaming loop with `UnicodeDecodeError`, and the child was orphaned. | Reproduced with a stub that writes `b"\xff"`. | **Fixed.** Uses `Popen(..., errors='replace')`. |
| 3 | Low-medium | A failure before the GPU work left no report: `gpu_setup` (stack mismatch, which is plausible if Colab has moved past torch 2.11.0+cu130, or a non-T4), `read_json` and `validate_dataset` all ran outside `try`. The preflight cell then died with `FileNotFoundError` instead of its own message. The ZIP carried the reason only inside `log.txt`, and run phases left no report at all. | Code reading; new tests reproduce it with a mocked `gpu_setup`. | **Fixed.** `preflight` and `run` now write a `FAILED` report with the traceback (`setup_failure()`). `decide` reads `stack_matches_d021` defensively. The preflight cell checks that the report exists and points to the Download cell. |
| 4 | Low | The checkpoint (`save()`, after update 4) depends on the network. PEFT's `save_pretrained` defaults to `save_embedding_layers="auto"`, which calls `file_exists` on the Hub and then makes an **unpinned** `Qwen3Config.from_pretrained("Qwen/Qwen3-4B")` call (peft 0.15.2 `utils/save_and_load.py` lines 222–248). A Hub error or 429 there would fail the first phase after four updates. | Library source. | **Fixed.** `save_pretrained(..., save_embedding_layers=False)`. Embeddings are frozen, so the adapter content is unchanged. The CPU emulation ran it with real PEFT. |
| 5 | Low | On a CPU runtime there is no `nvidia-smi`, so the GPU check raised `FileNotFoundError` instead of "select a T4". | Code reading. | **Fixed.** The error is caught and the T4 assertion fires instead. |
| 6 | Low | Hub download progress bars are streamed through a text-mode pipe, where each `\r` refresh becomes a new line. That means hundreds to thousands of output and log lines. | Code reading. | **Fixed.** `HF_HUB_DISABLE_PROGRESS_BARS=1` is set in cell 2. |

## Concerns not fixed (each would change the recipe or plan, or is an operator choice)

- **A. Timed updates 5–6 run cold.** They are the first backward passes in a fresh process; only the forward reload probe comes before them. One-time setup costs (autograd/cuBLAS backward initialization, allocator growth) therefore fall inside the timed window. The effect is likely only seconds on update 5, but it biases the median upward. Options: drop update 5's first microbatch from timing, or time only updates 3–4 plus 6. That is a D021 timing-rule change, so it has to be decided before the results come in.
- **B. The smoke data is short.** With the real tokenizer, the 48 examples have at most **207 tokens**. Input tokens per 32-example cycle are EE 5288, ER 5557 and EC 5401, so roughly 2.6–2.8k tokens per update, with 1546 supervised tokens per cycle. The 1024 cap is never approached. The s/update and headroom figures therefore apply to this length distribution. That is fine if Phase-2 TRAIN looks like this, but it is not a test of 1024-token memory. The 8–55 s/update research estimate assumed longer sequences.
- **C. The reload probe tolerance is about one fp16 ulp.** With atol = rtol = 1e-3 on fp16 logits, any cross-process kernel difference would fail spuriously.
  - Why a pass is expected: the shapes are identical; `CUBLAS_WORKSPACE_CONFIG` and deterministic mode are set; bitsandbytes 0.50.2's custom 4-bit GEMM has no split-K workspace; and on T4 with M > 128 tokens it routes through dequantize + `F.linear` (`backends/cuda/ops.py` `_gemm_4bit_use_custom_cuda`). The CPU emulation was bit-exact.
  - If it does fail: when the adapter, optimizer, RNG and digests are all exact and only `probe_max_abs_diff` is small (about 1e-2), read it as numerics, not lost state. The report records everything needed to tell these apart.
- **D. `prepare_model_for_kbit_training` upcasts the tied embedding/lm_head (389M parameters) to fp32.**
  - This adds about 0.78 GB of resident memory.
  - Under autocast, the fp32 lm_head is recast to fp16 on every forward pass: about 0.78 GB transient, kept for the backward pass.
  - The residual stream becomes fp32.
  - This is upstream behaviour and the smoke measures it. It only transfers if the real training also calls `prepare_model_for_kbit_training`.
- **E. Deterministic mode may slow training.** `torch.use_deterministic_algorithms(True, warn_only=True)` also fills uninitialized memory. The s/update only transfers if the real training uses the same flags (the inference engine used them too).
- **F. `USE_DRIVE = False` by default.** The run includes seven model loads and is estimated at 60–120 minutes, so a free-tier disconnect loses everything. Recommendation: set `USE_DRIVE = True` for the first run.
- **G. `t4_smoke/requirements.txt` still pins `torch==2.7.1+cu126`** with the cu126 index. The notebook does not use it, but `pip install -r` of that file on Colab would replace Colab's torch. It should be labelled as the fallback stack only.
- **H. `mask_audit` checks `labels`, but `Trainer` never reads them.** It takes targets from `input_ids[boundary_index:]`. The two are equivalent by construction, so this is noted for when the real trainer is written.
- **I. A stack mismatch does not block the verdict.** With `ALLOW_STACK_MISMATCH=True` the mismatch is flagged in `decision.json` but does not block a GO. This is by design; a flagged verdict should be read as provisional.
- **J. The worst-arm median is a conservative reading of D021's "median ≤ 56 s/update".** The alternative reading is a pooled median across arms.

## Verified correct (no change needed)

- **Labels.**
  - All 48 real-tokenizer rows pass the audit: the prompt is masked through `<|im_start|>assistant\n<think>\n\n</think>\n\n`, and the target decodes to the solution plus `<|im_end|>`.
  - The last label is `<|im_end|>`, E/R/C targets are identical, and the joint-tokenization round-trip holds for every row.
  - The prompt construction matches the inference engine (`hf_backend.prepare`).
- **Loss.**
  - With `logits_to_keep = S+1` and the last row dropped, the cross-entropy equals HF's own `labels=` loss (4.51.3, through the PEFT 0.15.2 wrapper).
  - `logits_to_keep` is visible to `inspect.signature` despite the decorators.
  - Each per-example mean is divided by 16, as the recipe states.
- **Checkpointing.**
  - PEFT skips `enable_input_require_grads` when `use_reentrant=False`.
  - Non-reentrant checkpointing with frozen embeddings still gives non-zero gradients to every LoRA tensor.
  - `_gradient_checkpointing_func.keywords == {'use_reentrant': False}`, so the assertion in `load_model` holds.
  - `use_cache=False` is set on the config and passed on every call.
- **GradScaler.**
  - The grads are fp32 (LoRA in fp32), so `unscale_` is legal.
  - The order is unscale, then clip, then step, then update.
  - Skip detection by scale decrease is valid, because growth_interval 2000 is never reached in 32 updates.
  - `state_dict()` equality after `load_state_dict` holds in a fresh process.
- **Reload.**
  - `torch.load(weights_only=True)` accepts the torch 2.11 AdamW state_dict, including its param-group keys (among them `decoupled_weight_decay`), the scaler dict, the RNG ByteTensors and the probe tensor.
  - In CPU emulation, four updates plus save, fresh model, restore and two updates match six straight updates bit for bit: losses, grad norms, every allclose check and every exact digest. Dropout RNG continuity is included.
- **Stack.**
  - None of the pins forces a torch reinstall. Checked against wheel metadata: bnb needs `torch>=2.4,<3`, accelerate `>=2.0`, peft `>=1.13`, transformers needs `huggingface-hub>=0.30,<1.0` and `tokenizers>=0.21,<0.22`.
  - bitsandbytes 0.50.2 ships `libbitsandbytes_cuda130.so`.
  - Every bnb symbol PEFT uses exists in 0.50.2.
  - `importlib.metadata` normalises `huggingface-hub`.
- **Data.**
  - Only the two hash-checked TRAIN files are read. The runtime reads only the embedded `smoke_data.json`.
  - The payload holds no DEV or FINAL_TEST material.
  - Script-mode imports of the extracted payload work, and the new `FAILED` report path also works there.

## Tests

| Suite | Result |
|---|---|
| `python3 -B -m unittest discover -s t4_smoke -p 'test_*.py'` | **Ran 55, OK** (was 50) |
| `PYTHONPATH=test1_pilot python3 -B -m unittest discover -s test1_pilot/tests -p 'test_*.py'` | **Ran 23, OK** |

Also passing: the notebook builder's `--check` reports the notebook current, and `protocol.py self-check` passes.

There are five new regression tests. All of them fail on the original code and pass on the fixed code:
- `SetupFailureTests.test_preflight_setup_failure_is_reported`
- `SetupFailureTests.test_phase_setup_failure_is_reported`
- `SetupFailureTests.test_checkpoint_does_not_ask_the_hub_about_embeddings`
- `NotebookTests.test_step_kills_the_phase_on_interrupt_and_tolerates_bad_bytes` (runs the real cell 2 in a subprocess against stub phases)
- `NotebookTests.test_preflight_cell_survives_a_missing_report`

## Still unverified (GPU only)

These are the same as items 1–7 in the Sol handoff, narrowed by the checks above:
- the T4 numerics: fp16 overflow and early skips;
- real s/update and memory;
- the bnb 0.50.2 + PEFT 0.15.2 training kernels on sm75;
- cross-process probe determinism on CUDA;
- whether Colab still ships torch 2.11.0+cu130.
