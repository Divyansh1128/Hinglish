# Second (and third) model for the frozen 30-family E/R/C pilot

Astra-2, 15 Oct 2026. Sources: the Hugging Face model API (`/api/models/<id>`: gating, licence, parameter count, architecture), plus each repo's `config.json`, `tokenizer_config.json` and README, all fetched today.
**Not verified:** no candidate has been loaded on Colab T4 with transformers 4.51.3 yet. The T4 and 4.51.3 compatibility below is inferred from each model's architecture class and its stated minimum transformers version.

## Recommendation

1. **Primary: `microsoft/Phi-4-mini-instruct`** (3.8B, MIT, not gated). It is a different family and close in size to Qwen3-4B, and the card emphasises math (GSM8K 88.6 on 8-shot CoT, per its own card). Its card lists many languages but **not Hindi**. That makes it a useful contrast: a strong-math model with no stated Hindi support.
2. **Optional third: `ibm-granite/granite-3.3-8b-instruct`** (8.17B, Apache-2.0, not gated), or the 2.5B variant if T4 time is short. It is a third family, but **Hindi is not among its 12 listed languages** either. The alternative is `allenai/OLMo-2-1124-7B-Instruct` (fully open data, but English-only according to its card).
3. Run each model unchanged with its own chat template and pin the repository revision (commit hash) in the run log. Pass our fixed English instruction explicitly, because both Granite and Phi otherwise insert defaults (see the system-message notes below).
4. **Indic-tuned models are not usable as-is.** Sarvam-1's card says it is a text-completion model that "cannot be used directly as a chat or an instruction-following model". Airavata is gated (`auto` gating) and has no chat template in its tokenizer config. Sarvam-M is 23.6B, too large for a T4. If you mention them, mention them only in Limitations or future work.

## Candidate table

| Model (URL) | Gated | Licence | Params | Min transformers / class | System message in template | Hindi / multilingual claim |
|---|---|---|---|---|---|---|
| [microsoft/Phi-4-mini-instruct](https://huggingface.co/microsoft/Phi-4-mini-instruct) | No | MIT | 3.84B | Card pins `transformers==4.49.0`; `Phi3ForCausalLM` is native* | Yes (`<\|system\|>`) | Card lists about 23 languages; Hindi not listed |
| [HuggingFaceTB/SmolLM3-3B](https://huggingface.co/HuggingFaceTB/SmolLM3-3B) | No | Apache-2.0 | 3.08B | `SmolLM3ForCausalLM`; config written by 4.54.0.dev0, so **fails on 4.51.3** | Template not in tokenizer_config (separate file, unchecked) | en, fr, es, it, pt, zh, ar, ru; no Hindi |
| [ibm-granite/granite-3.3-8b-instruct](https://huggingface.co/ibm-granite/granite-3.3-8b-instruct) | No | Apache-2.0 | 8.17B | 4.49.0; `GraniteForCausalLM` native | Yes; with no system message it inserts a **date-dependent default** (`strftime_now`) | 12 languages; Hindi not listed |
| [ibm-granite/granite-3.3-2b-instruct](https://huggingface.co/ibm-granite/granite-3.3-2b-instruct) | No | Apache-2.0 | 2.53B | 4.49.0 | Same as 8B | Same as 8B |
| [allenai/OLMo-2-1124-7B-Instruct](https://huggingface.co/allenai/OLMo-2-1124-7B-Instruct) | No | Apache-2.0 | 7.30B | 4.47.0.dev0; `Olmo2ForCausalLM` | Yes (`<\|system\|>`) | `en` only |
| [mistralai/Mistral-7B-Instruct-v0.3](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3) | No | Apache-2.0 | 7.25B | 4.42.0.dev0; `MistralForCausalLM` | Accepted, but folded into a user turn (no separate role)** | None stated; older (2024) model |
| [google/gemma-3-4b-it](https://huggingface.co/google/gemma-3-4b-it) | **Yes (manual)** | Gemma terms | 4.30B | `Gemma3ForConditionalGeneration` (multimodal) | n/a | Excluded: gated |
| [meta-llama/Llama-3.2-3B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct) | **Yes (manual)** | Llama 3.2 | 3.21B | `LlamaForCausalLM` | n/a | Card claims Hindi, but excluded: gated |
| [sarvamai/sarvam-1](https://huggingface.co/sarvamai/sarvam-1) | No | Not set in card metadata (check card text) | 2.53B | 4.45.2; Llama arch | Template present, but this is a **base model** | 10 Indic languages + en (hi included) |
| [sarvamai/sarvam-m](https://huggingface.co/sarvamai/sarvam-m) | No | Apache-2.0 | 23.6B | Mistral arch | Yes | Indic; **too large for T4** |
| [ai4bharat/Airavata](https://huggingface.co/ai4bharat/Airavata) | **Yes (auto)** | Llama 2 | 6.87B | Llama arch | No chat template in tokenizer_config | Hindi instruction-tuned; excluded: gated, no template |
| Reference: [Qwen/Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B) | No | Apache-2.0 | 4.02B | `Qwen3ForCausalLM` | Yes | (current model) |

\* Phi-4-mini's config has an `auto_map` to remote code. That mapping is only used when `trust_remote_code=True`; without it, transformers uses its native Phi3 class, which supports Phi-4-mini from 4.49. **Unverified on 4.51.3 + bitsandbytes NF4; smoke-test it first.**
\*\* Inferred from reading the template's first lines (`messages[0]` is captured as `system_message` and then merged). Confirm by rendering it with `apply_chat_template`.

## T4 / NF4 fit (estimates, unverified)

NF4 weights take roughly 0.55–0.6 GB per billion parameters: Phi-4-mini about 2.5 GB, Granite-8B / OLMo-2-7B / Mistral-7B about 4.5–5 GB. All of these fit the T4's 15 GB alongside the KV cache for short math answers. The 7–8B models will run roughly 2× slower per token than the 4B model. Use FP16 compute; the T4 has no BF16 support.

## Pre-run checklist for the chosen model(s)

- Pin the `revision=` commit hash. Log the transformers, bitsandbytes and torch versions.
- Load with `AutoModelForCausalLM.from_pretrained(..., quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16))` and **no** `trust_remote_code`.
- Render one E, one R and one C prompt with `apply_chat_template(add_generation_prompt=True)` and archive the exact strings. Check that no default system prompt or date has been injected.
- Use the same decoding settings, scorer and answer-extraction rule as Qwen3-4B. Report per-model results; do not pool across models.
- Paper framing: Qwen3-4B (multilingual, Hindi listed among Qwen3's 119 languages; that number is from memory, so verify it) vs Phi-4-mini (math-strong, Hindi not listed). This contrast is itself informative for the E→R/C gap.
