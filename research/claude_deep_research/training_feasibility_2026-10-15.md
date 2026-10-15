# Training feasibility and compute: QLoRA Qwen3-4B on a free T4

Date: 15 October 2026. Author: Claude research subagent (desk research only; no model runs, no GPU use).
Scope: Phase 2 recipe from `research/astra_experiment_spec_v1.md` (3 arms x 3 seeds x 256 updates = 2304 updates;
microbatch 1, accumulation 16, seq cap 1024, LoRA r16/alpha32 on all 7 linear projections, completion-only loss,
NF4 + double quant, FP16 compute, gradient checkpointing). Labels: **[V]** = verified from a primary source or by inspecting
an artifact; **[E]** = my estimate, with its basis; **[R]** = recommendation, not an approved decision.

## Bottom line

- Memory: **feasible with large margin** [E]. Estimated peak ~5.5-7.5 GB against ~14.5 GiB usable; the 2 GiB headroom rule should pass. This is still untested, so the smoke test decides.
- Time: **the uncertainty is large and it is the real risk** [E]. Estimated ~8-55 s per update, i.e. ~5-35 GPU-hours for 2304 updates before overhead.
  One 256-update run is ~0.6-3.9 h, so one arm-seed run per session is plausible on Colab or Kaggle.
- Stack: the pinned `bitsandbytes 0.45.5` **has no CUDA 13 binary** [V], so it cannot run alongside Colab's torch 2.11.0+cu130.
  The lowest-risk training stack is the one already verified for inference, with no TRL: torch 2.11.0+cu130, transformers 4.51.3, bnb 0.50.2, plus PEFT.
- Masking: Qwen3's template puts the empty `<think>\n\n</think>\n\n` block in the **generation prompt** when `enable_thinking=False` [V].
  Build labels yourself so this block is unsupervised prompt, exactly as at inference. Do not rely on TRL's patched Qwen3 training template.

## 1. Memory feasibility on T4

Model facts [V] (Qwen3-4B `config.json` at the pinned revision `1cfa9a72…`): hidden 2560, 36 layers, MLP 9728, 32 query / 8 KV heads, head_dim 128,
vocab 151,936, tied embeddings, stored as bf16. My parameter count from that config: 3.633B in linear projections + 0.389B embedding.

| Component | Estimate | Basis |
| --- | --- | --- |
| NF4 base linear weights | ~1.82 GB (+~0.06 GB quant constants) | 3.633B x 4 bit; double-quant overhead ~0.127 bit/param per QLoRA paper [E] |
| Embedding/lm_head (tied, not quantized) | 0.78 GB fp16, **1.56 GB if upcast to fp32** | PEFT `prepare_model_for_kbit_training` casts every fp16/bf16 non-`Params4bit` parameter to fp32 [V, source code] |
| LoRA r16 params (fp32) | 33,030,144 params = 0.13 GB | computed from config; cross-check: Unsloth's Qwen3-4B notebook reports 66,060,288 trainable at r=32, exactly 2x [V] |
| LoRA grads + AdamW m,v (fp32) | 0.40 GB | 3 x 0.13 GB [E] |
| Checkpointed layer inputs, seq 1024 | ~0.19 GB | 36 x 1024 x 2560 x 2 B [E] |
| One-layer recompute + SDPA math scores | ~0.3-0.5 GB | 32 heads x 1024^2 fp16 = 64 MiB per score tensor, several live copies; MLP 1024x9728 tensors [E] |
| Logits + loss at 1024 x 151,936 | ~0.6-1.9 GB | 155.6M elements, fp16 0.31 GB, fp32 0.62 GB, plus grad/log-softmax copies [E] |
| CUDA context + allocator fragmentation | ~0.5-1 GB | typical, not measured here [E] |
| **Total peak** | **~5.5-7.5 GB** | sum [E] |

Corroboration: the project's own T4 inference run peaked at 4.19 GiB reserved [V, PROJECT_STATUS]. Unsloth's public T4 notebooks [V, outputs inspected]:
Llama-3.2-3B QLoRA, batch 2, max_seq 2048, peaked at 6.53 GB reserved. Qwen3-14B QLoRA, same batch, reached 14.51 GB (98.4%), so 14B is the T4 ceiling and 4B is far below it.
Those runs used Unsloth's own kernels and are not our configuration.

The logits tensor is the dominant activation. If memory is ever tight, compute the loss only on completion positions (slice hidden states before `lm_head`) [R].

### T4 numerical and kernel pitfalls

- **No bf16** (compute capability 7.5). The checkpoint ships in bf16 and is converted to fp16. fp16 has a max of ~65504, so activation overflow means inf/NaN.
  The project's 6 fp16 inference generations are weak evidence that the forward pass is safe. They say nothing about the backward pass.
  I found no Qwen3-specific T4 NaN report, and the absence of a report is not evidence of safety. A HF forum thread on Qwen3.5-4B loss explosions points first to template/masking/EOS bugs
  (https://discuss.huggingface.co/t/qwen3-5-4b-loss-exploding/174057).
- **GradScaler + 4-bit:** `torch.amp.GradScaler.unscale_` raises `ValueError("Attempting to unscale FP16 gradients.")` when any gradient is fp16 [V, torch 2.11 `amp/grad_scaler.py` L274].
  So LoRA params must be fp32 (the protocol already sets `adapter_dtype: float32`) while matmuls run under fp16 autocast. Log scaler skips: the default initial scale (2^16) usually skips the first few steps.
  This is expected behaviour, and the skips must be counted, not hidden.
- **Library defaults that break on T4 (if TRL is used):** `SFTConfig` sets `bf16=True` whenever `fp16` is not set, and its `model_init_kwargs` dtype defaults to float32 [V, TRL v1.15 docs].
  Set `fp16=True` explicitly and load the model yourself.
- **Attention:** FlashAttention-2 supports only Ampere/Ada/Hopper [V, https://github.com/Dao-AILab/flash-attention]. PyTorch SDPA also offers math and memory-efficient backends.
  At seq 1024, attention is ~7% of training FLOPs [E: 4·L·d_attn per layer vs 2·params], so the "math only" choice costs little speed. The main cost is ~64 MiB per score tensor.
  Keep math-only for parity with the inference condition, unless the smoke test shows it is the bottleneck [R].
- **fp32 upcast of the tied embedding** (above) costs ~0.8 GB and makes `lm_head` fp32-stored. Under autocast the matmul still runs in fp16. Record the dtypes in preflight.
- **Packing / padding-free** need FlashAttention in current TRL [V, `padding_free` doc]. This is irrelevant here: microbatch 1 means there is no padding.

## 2. Speed and wall-clock

No credible published tokens/s figure exists for Qwen3-4B QLoRA on a T4 at our settings. I did not find one, and I will not invent one.

Evidence that does exist [V]:
- The Unsloth notebooks on Colab T4 log end-to-end time, but not tokens. Llama-3.2-3B ran 60 steps x 8 sequences in 446.5 s. Qwen3-14B ran 30 steps x 8 sequences in 2476.6 s.
  Their sequence lengths vary and are unreported, so neither converts to tokens/s.
  Source: https://github.com/unslothai/notebooks (`nb/Llama3.2_(1B_and_3B)-Conversational.ipynb`, `nb/Qwen3_(14B)-Reasoning-Conversational.ipynb`).
- The HF + Unsloth blog (T4 rows, QLoRA r16 all-linear, gradient checkpointing on) reports Unsloth at 1.56x-1.95x HF speed for 7B models and 3.87x for TinyLlama.
  These are 2024 versions (https://huggingface.co/blog/unsloth-trl).

FLOP-based estimate [E]:
- Per supervised-or-not token, the cost is a forward pass, a checkpoint recompute and the input-gradient backward. Frozen base weights need no weight gradients.
  That is ~6 x 4.02B ≈ 24 GFLOP, plus attention, giving ~26 GFLOP per token.
- T4 datasheet peak is 65 TFLOPS FP16 tensor at 70 W. With NF4 dequantization done three times per layer per step, I assume an **effective 8-20 TFLOPS**.
  This is an assumption, not a measurement. It gives ~300-770 tokens/s.
- Per update = 16 x L̄ tokens, where L̄ is the mean prompt+completion length. There is no padding at batch 1.

| Mean length L̄ | s/update [E] | One run (256 updates) | 2304 updates (GPU-hours) |
| --- | --- | --- | --- |
| 400 tokens | ~8-21 s | ~0.6-1.5 h | ~5-14 h |
| 700 tokens | ~15-37 s | ~1.0-2.7 h | ~9-24 h |
| 1024 tokens | ~21-55 s | ~1.5-3.9 h | ~14-35 h |

Add per-session model loading. The observed figure was 224.75 s including download [V, PROJECT_STATUS]. Also add checkpoint saves, periodic validation and lost work after disconnects.
A 1.3-1.5x overhead factor is a reasonable planning margin [R]. R and C prompts are Romanized Hindi and may tokenize longer than E.
The completions are identical English, so **supervised tokens match across arms, but per-update time will differ by arm**. Record t_EE, t_ER and t_EC separately, as the spec says.

Platform limits:
- **Colab free** [V, https://research.google.com/colaboratory/faq.html]: notebooks run "at most 12 hours, depending on availability and your usage patterns". It uses "dynamic usage limits that sometimes fluctuate".
  Resources are "not guaranteed and not unlimited", and idle timeouts vary. In practice: expect GPU denials and sub-12 h sessions, and plan for one arm-seed run (≤4 h) per session, with checkpoints every 32 updates.
- **Kaggle** (secondary source citing Kaggle docs, checked 21 Sep 2026: https://gpuperhour.com/blog/free-cloud-gpus-and-credits): 12 h GPU sessions.
  The weekly quota is not published and floats; ~30 h is user-reported. Hardware is T4 x2 or P100.
  "Save & Run All" runs non-interactively, which avoids Colab's interaction requirement. At ~30 h/week, 2304 updates take ~1-2 weeks [E].

## 3. Library compatibility on Colab CUDA 13

- **bitsandbytes** [V, wheels inspected from PyPI]: the 0.45.5 wheel bundles `libbitsandbytes_cuda117…cuda128.so`, with **no cuda130**.
  The 0.50.2 wheel adds `cuda130` and `cuda132`. Release notes [https://github.com/bitsandbytes-foundation/bitsandbytes/releases]:
  - 0.48.0 added CUDA 13.0 builds "limited to Turing and newer".
  - 0.50.0 added CUDA 13.2 wheels and a new 4-bit GEMM covering Turing through Blackwell. It also removed legacy quantization functions and non-blockwise optimizers, and requires torch ≥2.4.
  - bnb 0.50.2 + torch 2.11 cu130 + transformers 4.51.3 already loads and generates on T4 [V, project run].
- **Old pinned stack (torch 2.7.1+cu126, bnb 0.45.5)**: it carries its own CUDA 12.6 runtime in pip wheels. NVIDIA drivers are backward compatible with older CUDA runtimes (https://docs.nvidia.com/deploy/cuda-compatibility/).
  So it *may* install on Colab, but this is untested. It also replaces Colab's torch, Python-version wheel availability is unchecked, and training would then use a different stack from the verified inference/evaluation stack.
  CUDA 13 dropped Maxwell/Pascal/Volta [V, https://docs.nvidia.com/cuda/cuda-features-archive/index.html]. Kaggle's **P100 (sm60) cannot use cu130 wheels**.
- **PEFT** [V, https://github.com/huggingface/peft/releases]: latest is 0.21.2 (1 Oct 2026). PEFT <0.18.0 is incompatible with Transformers v5, but this does not matter for transformers 4.51.3.
  Qwen3 uses standard `nn.Linear` names, so LoRA targets need no model-specific support. Compatibility of PEFT 0.15.2 with bnb 0.50.2's removals is **unverified**: smoke-test it.
- **TRL** [V, tag source + release dates via GitHub API]:
  - `completion_only_loss` first appears in `SFTConfig` at v0.17.0 (25 Apr 2025), and `assistant_only_loss` at v0.19.0 (21 Jun 2025).
  - `DataCollatorForCompletionOnlyLM` is gone from the top-level exports at v0.20.0 (29 Jul 2025).
  - v0.19.x requires transformers ≥4.51.0; v0.20.0 requires ≥4.53.2. So **with transformers 4.51.3, the newest usable TRL is 0.19.1**.
  - The current TRL is 1.15.0 (8 Oct 2026; requires transformers ≥4.56.2). For prompt-completion data, `completion_only_loss=None` defaults to completion-only.
    A pre-tokenized dataset with a `labels` column "is used as is" [V, https://huggingface.co/docs/trl/sft_trainer].
- **Qwen3 template and masks** [V]:
  - The pinned Qwen3-4B template has no `{% generation %}` tags.
  - With `add_generation_prompt=True, enable_thinking=False`, it emits `<|im_start|>assistant\n<think>\n\n</think>\n\n`.
  - TRL's `qwen3_training.jinja` (swapped in for `assistant_only_loss`) "always include[s] the thinking block" inside the assistant turn (https://huggingface.co/docs/trl/chat_templates).
    That likely makes the empty think block a **supervised** target, unlike our inference prompt [E from the diff; verify by decoding masks].
  - Recommended construction [R]:
    - prompt_ids = template(user, add_generation_prompt=True, enable_thinking=False)
    - completion_ids = tokenize(English solution + `<|im_end|>`)
    - labels = -100 on the prompt
    - Assert that the concatenation round-trips and that completion_ids are byte-identical across E/R/C.
- **Unsloth** [V, PyPI 2026.10.5 metadata]: requires transformers ≥4.52.4 (≤5.17.0), trl ≥0.18.2 and bnb ≥0.45.5. It is **incompatible with the verified transformers 4.51.3**.

## 4. Alternatives if T4 is too slow

| Option | Gains | Costs for a controlled study |
| --- | --- | --- |
| Kaggle 1 GPU per run | Same T4 silicon. Background execution. Published 12 h sessions | Different driver/image than Colab; weekly quota floats. Run **all 9 runs + evaluation** there, or record platform per run and balance arms across platforms |
| Kaggle T4 x2: two independent single-GPU runs in parallel (e.g. two seeds) | ~2x throughput with the same per-run recipe (no DDP, so the recipe is unchanged) | Host RAM/disk shared; verify the two processes don't contend. Assign GPUs to runs in a balanced pre-declared schedule |
| Unsloth (supports T4, CC ≥7.0, and Qwen3 [V, https://unsloth.ai/docs/get-started/fine-tuning-for-beginners/unsloth-requirements]) | Vendor-reported 1.5-2x on T4 for 7B, plus less VRAM | Custom Triton kernels and monkey-patching. Requires a newer transformers, so **baseline inference must be re-run on the same stack**. Fast version churn; harder to audit masks |
| Qwen3-1.7B | ~2.3x fewer FLOPs per token [E: 1.72B vs 4.02B incl. lm_head; 1.41B linear + 0.31B emb from its config] | Changes the model under study. The Test-1 pilot (4B) no longer describes the trained model. Weaker math, so more floor effects. Use only as a pre-declared fallback |
| Shorter seq cap / fewer updates | Linear time saving | Must not truncate any target. 256 updates is already provisional; change it before outcomes, for all arms |
| Lightning AI free | Persistent studio | Free Studios "become paid after 4 hours"; monthly credit unconfirmed (gpuperhour, above). Not suitable as the primary platform |
| Paperspace free (M4000, 8 GB, 6 h) / SageMaker Studio Lab (closed to new users) | — | Not viable (same source) |

Controlled-study rule [R]: every arm and seed must use the same GPU model, software stack hash, recipe and update count. Seeds and arms should be interleaved across days and platforms rather than run arm-by-arm.
Any hardware or stack change mid-study means restarting the affected comparison, not mixing results.

## 5. Recommendation

**Stack A (test first) [R]:** Colab's preinstalled torch 2.11.0+cu130 (record the exact build), transformers 4.51.3, bitsandbytes 0.50.2, peft 0.15.2, and accelerate frozen at the version in the inference run.
Use **no TRL**: a ~150-line custom loop matching `t4_smoke/protocol.py` (torch AdamW, fp32 adapters, fp16 autocast, GradScaler, non-reentrant checkpointing, explicit labels).
This makes training and evaluation share one quantization stack. If PEFT 0.15.2 breaks on bnb 0.50 (it is unverified), move only PEFT to the newest release that installs against transformers 4.51.3, and re-test.
**Stack B (fallback):** the existing pins (torch 2.7.1+cu126, bnb 0.45.5) in a fresh Colab runtime. If chosen, baseline inference must be re-run on B.
**Do not** mix bnb 0.45.5 with torch cu130. **Do not** adopt Unsloth or TRL 1.x without re-running baseline inference on that stack.

**Smoke-test plan [R]** (extends the spec's six-update concept):
1. Preflight: GPU/driver/CUDA, `pip freeze` hash and quantized-module count. Also check dtypes: adapters fp32, embedding dtype after prep, compute fp16.
   Confirm 33,030,144 trainable params and that optimizer membership equals the adapter set.
2. Mask audit per arm, on real tokenizer output: decode the supervised spans. Assert prompt (incl. empty think block) = -100. Assert the completion+`<|im_end|>` ids are identical across E/R/C and that there is no truncation at 1024.
3. Per arm (E+E, E+R, E+C): 2 warm-up + 4 timed updates. Checkpoint after update 4, then do a clean-process reload restoring adapters, optimizer, scaler, RNG and cursor, and run updates 5-6.
   Log the loss and grad-norm for each update, scaler scale/skips, per-update seconds, torch peak alloc/reserved, NVML device used sampled ≥1 Hz, and host RSS.
4. **Stability probe (added):** one arm, 32 updates on smoke data at the real LR. Six updates cannot reveal fp16 overflow that develops as the adapter moves.
5. Before/after reload probe: fixed-input logits within the protocol's 1e-3 atol/rtol.

**Go / no-go [R; thresholds are proposals]:**
- GO (memory): no OOM, and NVML minimum free ≥2 GiB throughout every phase (existing spec margin).
- GO (numerics): all losses and grad norms finite. Scaler skips ≤3 in the first steps and **0 after update 4**, plus none in the 32-update probe. Reload probe within tolerance.
- GO (masks): the step-2 assertions pass for 100% of smoke families.
- GO (time) on Colab: median s/update ≤56 for every arm, so 256 updates fit in ≤4 h per session.
  56-150 s means moving to Kaggle background runs (or the T4 x2 parallel schedule). Projected 2304-update time x 1.4 must be ≤ the declared compute budget.
- NO-GO for Qwen3-4B on T4: repeated non-finite losses after one fix attempt (e.g. lower LR, scaler init 2^10), memory headroom <2 GiB, or median >150 s/update.
  In that case invoke the pre-declared fallback (Qwen3-1.7B with re-run baseline, or a narrowed descriptive claim) **before** any confirmatory outcome is seen.

Note: none of the above has been run. All time and memory figures are estimates until the smoke test returns NVML and timing logs.
