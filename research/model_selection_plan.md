# Model Selection Plan

Status: draft research plan, verified against public model pages on 8 October 2026. This plan does not download models or run experiments.

## Decision

We should not make the project a Qwen-only study. Qwen3-4B remains the main trainable model because it is a strong, permissively licensed 4B model that is plausible for QLoRA testing on a Colab T4. To reduce the risk of model-specific conclusions, the pilot baseline should evaluate several small open-weight models without training. Training additional models is optional and should happen only after the Qwen pipeline is stable.

## Model Roles

| Priority | Model | Role in study | Why include it | Main caveat |
| --- | --- | --- | --- | --- |
| 1 | `Qwen/Qwen3-4B` | Primary unchanged baseline and primary QLoRA training model | 4.0B parameters, Apache 2.0, multilingual support, long context, and documented reasoning/math improvements | Actual T4 training fit remains unverified |
| 2 | `microsoft/Phi-3.5-mini-instruct` | Inference-only baseline; possible second trainable model if resources permit | 3.8B active parameters and model card reports multilingual and MGSM benchmarks | Uses `trust_remote_code`; training implementation may need separate checks |
| 3 | `sarvamai/sarvam-1` | Indic-focused inference-only baseline | 2B model optimized for 10 Indic languages including Hindi; useful to test whether Indic specialization helps Hinglish/Romanized Hindi | Smaller model may have weaker math reasoning than Qwen/Phi |
| 4 | `meta-llama/Llama-3.2-3B-Instruct` | General small-model inference baseline if access is approved | Widely used 3B instruction model; good reference family for reviewers | Gated access and custom Llama license; do not make it required |
| 5 | `google/gemma-2-2b` or `google/gemma-2-2b-it` if accessible | Small fallback inference baseline | Very small and practical for broad diagnostic comparisons | Requires accepting Google usage license; base version may be less suitable than instruction-tuned models |

## Experimental Use

### Stage A: Pilot Baseline Across Models

Run all accessible models on the frozen 30-family pilot:

- Same E/R/C prompts.
- Same answer format instruction.
- Same deterministic or low-temperature decoding policy where supported.
- Same scorer and manual audit process.
- Record output validity, refusals, truncation, latency, memory, and token counts.

Purpose: determine whether the E/R/C robustness pattern appears across models or only in Qwen.

### Stage B: Primary Controlled Training

Train only Qwen first:

- Condition 1: E+R training.
- Condition 2: E+C training.
- Optional condition: English-only matched exposure.
- Three seeds only after the T4 smoke test succeeds.

Purpose: test whether code-mixed training improves held-out Hinglish accuracy beyond Romanized-Hindi exposure under matched conditions.

### Stage C: Optional Replication

If time and GPU budget remain, choose one second model for partial replication:

1. Prefer `Phi-3.5-mini-instruct` if T4 training is stable and license/checkpoint loading are manageable.
2. Prefer `sarvamai/sarvam-1` if Hindi/Romanized-Hindi behavior becomes the central finding.
3. Do not train Llama or Gemma unless access, license terms, and reproducibility are clearly resolved.

## Final Claim Boundaries

If only Qwen is trained, the final paper may claim:

> In a controlled Qwen3-4B QLoRA experiment, code-mixed training showed or did not show an advantage over Romanized-Hindi training under the specified protocol.

It should not claim:

> Hinglish mathematical reasoning is solved generally, or all LLMs benefit from Hinglish training.

If multiple unchanged models show a similar E/R/C pattern, the paper can more safely claim that the diagnostic issue is not unique to Qwen. If only Qwen shows the pattern, report it as model-specific.

## Selection Gates Before Running

| Gate | Required evidence | Decision |
| --- | --- | --- |
| Access | Model can be downloaded or served legally under accepted terms | Include only accessible models |
| Prompt compatibility | Chat template or prompt format is defined and documented | Freeze model-specific prompt wrappers |
| Memory | Inference completes on available GPU or CPU fallback within practical time | Include in pilot baseline |
| Scoring | Output can be parsed or marked invalid without special treatment | Use common scorer for all models |
| Training feasibility | Six-update smoke test with save/reload succeeds | Allow QLoRA scaling only for that model |

## Implementation Tasks

1. Add a `models.yaml` registry with model IDs, prompt format notes, access status, license notes, and intended role.
2. Build a baseline runner that accepts a model key, loads the tokenizer/model, generates outputs, and stores raw responses.
3. Freeze one prompt wrapper per model after a short format-only dry run; do not tune prompts using final-test accuracy.
4. Run the 30-family pilot across Qwen, Phi, Sarvam, and any accessible Llama/Gemma model.
5. Use the pilot output to decide whether the final study needs an additional trained model or only the Qwen training comparison.

## Sources Checked

- Qwen/Qwen3-4B model card: https://huggingface.co/Qwen/Qwen3-4B
- Microsoft Phi-3.5-mini-instruct model card: https://huggingface.co/microsoft/Phi-3.5-mini-instruct
- Sarvam-1 model card: https://huggingface.co/sarvamai/sarvam-1
- Meta Llama-3.2-3B-Instruct model card and license gate: https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct
- Google Gemma-2-2B model card and access note: https://huggingface.co/google/gemma-2-2b
