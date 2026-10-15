# Mechanisms behind R/C gaps, and controls to add

Claude deep-research note, 15 October 2026. **Literature and design advice only.** No model runs and no paid APIs. Only the local FMT2 CSVs were read; no file was modified. Sources were accessed 15 Oct 2026 through web search and abstract or HTML pages. Unless a row says otherwise, numbers come from abstracts or HTML text, not from a full-PDF reading. **[U]** marks a claim that is unverified or secondary. The operation-word lexicon belongs to Astra ([operation_vocabulary_2026-10-15.md](../operation_vocabulary_2026-10-15.md)) and is not repeated here.

## 0. Local fact check (FMT2 development fixtures, n=12 families, excluded data)

`input_tokens` in the FMT2 CSVs counts the **whole prompt**: chat template, the fixed English instruction and the question.

| Prompt | Median E | Median R | Median C | Paired R−E per family | Paired C−E per family |
|---|---:|---:|---:|---|---|
| v1 (`per_rendering.csv`) | 77 | 99.5 | 82 | — | — |
| v2 (`per_rendering_prompt_v2.csv`) | 104 | 126.5 | 109 | +10 to +47 (median ≈ +22.5) | −5 to +11 (median ≈ +6) |

Implications:
- The quoted "~25% longer" figure is a whole-prompt ratio. The template is constant across forms, so the **question-only** R/E ratio must be larger. It has not been computed yet; see A1.
- C costs almost no extra tokens. Any C gap therefore cannot easily be blamed on length, which makes C a useful internal control.
- R outputs were also longer under v1 (median 107 vs 82 output tokens). Output length should be tracked per form.

## 1. Tokenization of Romanized Hindi and code-mixed text

| Source | What it shows | Relevance / caveat |
|---|---|---|
| Petrov et al., NeurIPS 2023, [arXiv 2305.15425](https://arxiv.org/abs/2305.15425) | Parallel text differs up to 15x in tokenized length across languages. The disparity holds across 17 tokenizers. | Establishes the "token tax". It concerns cost and context, and does not show an accuracy effect. |
| Srivastava 2026, "The Tokenizer Tax", [arXiv 2607.24276](https://arxiv.org/abs/2607.24276) | FLORES-200, 6 tokenizers, 14 Indian languages. Indian languages average an 8.0x tax under cl100k_base; o200k_base and XLM-R cut it by 73%. The apparent link between fertility and Belebele accuracy is **largely explained by language resource availability**. | Single-author preprint covering native scripts only. Directly relevant caution: fertility can be a proxy for low resources, not a cause. |
| Ali et al., "Tokenizer Choice for LLM Training", [arXiv 2310.08754](https://arxiv.org/abs/2310.08754) | 24 models at 2.6B parameters. Fertility and parity are "not always predictive" of downstream performance, and the non-English correlations are noisy. | Argues against treating token count as a mechanism by itself. |
| TokLens, ACL 2026 SRW, [aclanthology 2026.acl-srw.18](https://aclanthology.org/2026.acl-srw.18.pdf) | Tokenizer metrics predict per-language multilingual performance, but the authors call this correlational and confounded with pretraining data. | Same caution as above. [U: read via snippet] |
| Husain et al., RomanSetu, ACL 2024, [arXiv 2401.14280](https://arxiv.org/abs/2401.14280) | Romanized Indic text has 2–4x lower fertility than native script on Llama 2. | Romanized Hindi is *cheaper* than Devanagari. R's extra cost here is relative to English only. |
| Brahma et al., ACL 2026 Findings, [arXiv 2506.17789](https://arxiv.org/abs/2506.17789) | Indic tokenization study (17 languages): script normalization, BPE vs Unigram. | Native script only; no Romanized-text or Qwen results. |
| Qwen3 Technical Report, [arXiv 2505.09388](https://arxiv.org/html/2505.09388v1) | "byte-level byte-pair encoding (BBPE) with a vocabulary size of 151,669"; 119 languages and dialects in pretraining. | Hindi is named only in the multilingual benchmark lists. Romanized text is not discussed. |
| IndicSuperTokenizer, [arXiv 2511.03237](https://arxiv.org/html/2511.03237v1), Table 22 | Qwen3-32B tokenizer Hindi (Devanagari) fertility **4.86** vs 1.23 for their tokenizer. | This is the only Qwen-specific Indic number found. It is Devanagari, not Roman script. Qwen3 dense models share one tokenizer per the report, so this likely applies to Qwen3-4B [U: inference]. |

**Qwen-specific gap:** I found no published fertility or segmentation measurement of Romanized Hindi or Hinglish for any Qwen tokenizer. A secondary source (a [conference talk page](https://events.canonical.com/event/154/contributions/1005/)) cites a GPT-2-class tokenizer at about 7.71 tokens/word for Devanagari vs 2.36 for Romanized Hindi **[U: venue and peer review unknown; do not cite]**. The paper should measure its own numbers (A1) rather than borrow one.

**Mechanism verdict:** the length change is tiny. The extra ~20–25 tokens sit on a ~100-token prompt. Levy et al. ([ACL 2024, arXiv 2402.14848](https://arxiv.org/abs/2402.14848)) found reasoning degrades with input length, but at padding lengths far beyond this. "R is longer" is therefore a weak explanation for a gap. **Segmentation of specific content words** is more plausible: a rare Romanized word split into opaque pieces gets a poor representation, and this interacts with how rare the Romanized math register is in pretraining. These cannot be separated observationally.

## 2. Spelling variation in Romanized Hindi

- **No standard orthography.** Dakshina ([Roark et al., LREC 2020](https://aclanthology.org/2020.lrec-1.294), [arXiv 2007.01176](https://arxiv.org/abs/2007.01176)) collected about 1.7–4.2 attested romanizations per native word type across 12 languages [U: per-language figure from table snippet]. A single R rendering is therefore one sample from a distribution of spellings.
- **Normalization work**, all pre-LLM, for classifiers and parsers:
  - Bhat et al. 2016, shallow-parsing pipeline with a noisy-channel normalizer ([arXiv 1604.03136](https://arxiv.org/abs/1604.03136));
  - embedding-based variant clustering ([arXiv 1804.00804](https://arxiv.org/abs/1804.00804));
  - phonetic normalization that improved intent and slot NLU ([ICON 2022](https://aclanthology.org/2022.icon-main.33)).
- **LLM robustness evidence is thin.**
  - "Script Gap" ([Khullar et al., arXiv 2512.10780](https://arxiv.org/abs/2512.10780), preprint): on real health-triage queries in 5 Indian languages plus Nepali, **Romanized input scores 5–12 F1 points below native script**. A HealthBench control with identical messages still showed about a 5.4-point drop, which the authors attribute to orthography. Models often inferred the intent but produced brittle final labels. **Code-mixed Romanized messages did better than non-code-mixed ones.** [U: last two points from a secondary summary]
  - "Beyond Specialization" ([arXiv 2505.19851](https://arxiv.org/abs/2505.19851)) adds spelling and case noise to romanized words for transliteration.
  - A Bangla study tests realistic and adversarial script mixing ([BLP 2025](https://aclanthology.org/2025.banglalp-1.27)); its abstract reports no numbers.
- **No published spelling-variant robustness test for math word problems in Romanized Hindi was found.** This is a retrieval limit, not a novelty claim. A small probe (A3) would therefore add something.

## 3. Romanized vs native script: what an R gap means

- RomanSetu: romanization helps an English-centric model **after continued pretraining on romanized text**. Their mixed-script prompting results are task-dependent.
- Ma et al. ([MRL 2025, arXiv 2407.02320](https://arxiv.org/abs/2407.02320)): adding transliteration helps sequence labeling (up to +25%) but is "less effective" on other tasks. The benefit depends on task and model size.
- Sarvam-M author blog ([sarvam.ai/blogs/sarvam-m](https://www.sarvam.ai/blogs/sarvam-m)): on GSM-8K across Indic languages, every model drops from native script to romanized. Examples: Mistral Small 0.82 → 0.44, Llama 3.3 0.86 → 0.51, Gemma 3 0.89 → 0.63. Caveats: author technical report; the benchmark was machine-translated and transliterated; scores are aggregated over languages, not Hindi only. **This is the closest published evidence that an unadapted model's Romanized math accuracy falls well below its English accuracy.** The pilot can cite it as the prior expectation for an R gap.
- CodeMixBench ([EMNLP 2025, arXiv 2507.18791](https://arxiv.org/abs/2507.18791)) includes CM-GSM8K with hi-en and reports code-mixed underperformance. Indi-RomCoM ([arXiv 2606.30790](https://arxiv.org/abs/2606.30790), June 2026) finds that performance worsens as Romanized code-mixing density rises; GSM8K is not named on its abstract page [U].
- **What this means for interpretation:** an E–R gap combines at least four things:
  1. script: Roman vs Devanagari;
  2. language: Hindi vs English;
  3. register: how rare the Romanized math vocabulary is in pretraining;
  4. orthographic noise: the particular spelling chosen.

  The design cannot separate these, so the paper should claim a **language-form effect, not a tokenization or script effect**. C is the internal contrast: it matches R's script while keeping English relations, and Script Gap found code-mixed text more robust. If C ≈ E and R < E, that points to Hindi operation and relation vocabulary rather than Roman script as such. This would still be an inference, not an identification.
- A Devanagari arm (D) would separate script from language. It would need new human-reviewed renderings, and machine back-transliteration is lossy (Dakshina §3.3). **Do not add D to the pilot.** Name it as future work.

## 4. Translate-then-solve and "think in English" baselines

- MGSM ([Shi et al., ICLR 2023, arXiv 2210.03057](https://arxiv.org/abs/2210.03057)) defines Translate-EN (Google Translate, then English chain of thought) alongside native and English CoT. This is a standard comparison, but it relies on an external MT system.
- Self-translate ([Etxaniz et al., NAACL 2024](https://aclanthology.org/2024.naacl-short.46), [arXiv 2308.01223](https://arxiv.org/abs/2308.01223)): the *same* model translates its input to English few-shot, then solves it. This beat direct inference across 5 tasks. **This is the fair, oracle-free design**: no external system, and the model's own comprehension is what is tested.
- XLT prompting ([Huang et al., Findings EMNLP 2023, arXiv 2305.07004](https://arxiv.org/abs/2305.07004)) asks the model to restate the problem in English inside one prompt and reports large MGSM gains for GPT-3.5 [U: table values via snippet]. Note: [arXiv 2505.22888](https://arxiv.org/abs/2505.22888) reports that forcing reasoning in the user's language costs accuracy.
- **Current design status:** prompt v2 already asks for an English explanation, so the primary condition is already "reason in English, read in R or C". A translate-then-solve arm tests something different: does making the **reading** step explicit, as a separate English rewrite, recover R accuracy?
- **Fair implementation (no oracle):**
  1. Fresh context per question, with Qwen3-4B, the same pinned revision and greedy decoding. Use one fixed translation instruction: "Translate this math problem into English. Keep every number. Do not solve it." It should be zero-shot, or few-shot using only **excluded FMT2 fixtures**, never pilot items.
  2. Feed the translation, unedited, to the frozen E pipeline (prompt v2) in a new context. Score with the same scorer.
  3. Report three numbers per form: direct R/C; self-translate R/C; and E. E serves as the *human-oracle translation* upper bound.
     - (E − self-translate) estimates loss in the reading/translation step.
     - (self-translate − direct) shows whether separating reading from reasoning helps.
  4. Save every translation. Have a bilingual reviewer tag only whether the operation or quantity was preserved, without seeing model correctness. Translation errors are then evidence for the comprehension mechanism (e.g. "bhinn" rendered as "different").

  Cost: 60 translations plus 60 solves for R and C on 30 families. Inference only.

## 5. Recommended analyses

"Pre" means define and freeze before the pilot, in the endpoint spec as descriptive or secondary. "Post" means exploratory and labelled so. None changes the primary endpoint.

| ID | Analysis | Type | When | Notes |
|---|---|---|---|---|
| A1 | Token count and fertility per form: question-only tokens, tokens per whitespace word, % words split into ≥3 pieces, and pieces per *operation-word occurrence* (lexicon from Astra) | Model-free (pinned Qwen3 tokenizer on CPU) | **Pre** (freeze script and definitions; run on accepted data before outputs are seen) | Report paired R−E and C−E per family. The tokenizer revision must match the run manifest. |
| A2 | Length as covariate: correlate per-family ΔTokens(R−E) with discordance (E correct, R wrong), descriptive only; plus output-token medians per form | Analysis of pilot outputs | **Pre** (as descriptive) | With 30 families this is underpowered; state "no causal claim". Do not subset into "length-matched" pairs; too few remain. |
| A3 | Spelling-variant probe: for R items, regenerate with 1–2 alternative attested spellings of content and operation words (e.g. bhaag/bhag), checked by a bilingual reviewer; measure answer flips | Inference only | **Post** (method freezable pre-pilot) | Report flip rate, not accuracy. Variants must keep the meaning; record each one. |
| A4 | Lexical minimal pair: in R items, replace *only* the operation word with its English gloss ("bhinn" → "fraction"); does accuracy recover? | Inference only | **Post** | Most direct test of the bhaag/bhinn mechanism. The result is C-like text; describe it as an intervention, not a new form. |
| A5 | Self-translate baseline (§4) | Inference only | **Post**, or **Pre** as a named secondary if frozen now | If pre-registered, freeze the translation prompt now and never tune it on pilot items. |
| A6 | Length-only control: pad E prompts with neutral, irrelevant English text to R's token count | Inference only | **Post**, low priority | GSM-IC ([Shi et al., ICML 2023, arXiv 2302.00093](https://arxiv.org/abs/2302.00093)) shows irrelevant text itself hurts, so padding is not neutral. Run only if A2 suggests length matters. |
| A7 | Error taxonomy split by mechanism: `wrong_relation_operation`, `misread_quantity`, item non-equivalence, output-language drift | Manual audit | **Pre** (labels already planned) | Coders blind to form where feasible (show the English gloss of the model's reasoning). |
| A8 | English-compliance tag and output length per form | Model-free | **Pre** (already recommended in FMT2) | v2 removed Devanagari output, but drift remains a mediator to monitor. |

**Priority under the time budget:** A1, A2, A7 and A8 cost nothing and should be frozen now. A4 and A5 are the two most informative post-pilot experiments, about 120–200 extra generations on a T4. A3 and A6 come after those.

## 6. Interpretation guardrails for the paper

- Token count is a **correlate**, not a demonstrated cause. Two sources ([2607.24276](https://arxiv.org/abs/2607.24276), [2310.08754](https://arxiv.org/abs/2310.08754)) warn that fertility effects confound with resource level.
- The two FMT2 R errors are n=2 on excluded fixtures. Say "consistent with" an operation-word misreading. Also note that "bhinn" is ambiguous even in Devanagari (Astra's note), so the ambiguity is lexical, not purely orthographic.
- Interventions A4 and A5 are post hoc and use pilot items. Label them exploratory, and do not let them alter the frozen items or prompt.

## Unverified / not found

- No Romanized-Hindi fertility figures for Qwen were found.
- No study of spelling-variant robustness for Romanized-Hindi math was found.
- Per-language Hinglish CM-GSM8K numbers in CodeMixBench were not read (Astra reports hi-en is lower than English in Table 2).
- Indi-RomCoM math-task details were not confirmed.
- The XLT and Dakshina table values come from snippets.
