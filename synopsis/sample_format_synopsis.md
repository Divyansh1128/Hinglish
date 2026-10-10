# HINGLISH MATHEMATICAL REASONING IN LARGE LANGUAGE MODELS

### 1. INTRODUCTION

Mathematical questions can be expressed in English, Hindi, or Hinglish, where Hindi and English are mixed in the same sentence. In Roman-script Hinglish, Hindi words are also written using English letters. A model may therefore encounter several natural versions of the same problem. Evaluating these versions separately can help determine whether its mathematical answers remain reliable when the language changes.

Our project proposes a controlled study of this issue using an existing open-weight large language model. Each mathematical problem will have three equivalent forms: English (E), Romanized Hindi (R), and Hinglish (C). We will first evaluate the unchanged model and then compare training on English plus Romanized Hindi with training on English plus Hinglish. Mathematical content and solution targets will be matched so that the comparison is not driven simply by different questions or answers.

The project will produce reviewed data, reproducible implementation code, and an experimental report. It will investigate whether code-mixed training helps, rather than assume that fine-tuning must improve performance.

### 2. PROBLEM STATEMENT

Language variation can complicate the interpretation of mathematical word problems. A wrong final answer may reflect misunderstanding of a comparison, a unit, or a quantity, as well as an error in calculation. Comparing unrelated English and Hinglish questions would make these explanations difficult to separate.

- **Language effects:** Determine whether the same model answers equivalent E, R, and C questions differently.
- **Training effects:** Test whether E+C training improves held-out Hinglish accuracy beyond matched E+R training, while monitoring English performance.
- **Generalization:** Examine whether observed gains extend to independent problem families and reviewed spelling or phrasing variants rather than familiar templates.

The study will focus on numerical word problems involving comparisons, money, fractions and percentages, ratios, rates and units, and elementary algebra. It will not train a foundation model from scratch or claim to solve unrestricted mathematical reasoning.

### 3. MOTIVATION

We want to investigate mathematical reasoning under language conditions that include Hindi and English together, rather than treating English performance as sufficient evidence of robustness. The R condition is important because it provides a comparison with Hindi written in Roman script without substantive English clauses. This helps narrow the question to code mixing rather than script choice alone.

Bilingual reviewers are available to check mathematical equivalence and language quality. Together with a staged pilot and an available Colab T4, this makes a bounded student research project worth investigating. At present, the scorer and input checks are implemented, but human annotation and model experiments are pending.

<!-- pagebreak -->

### 4. LITERATURE REVIEW

The initial review covers multilingual mathematical reasoning, code-mixed evaluation, and parameter-efficient model adaptation. The following sources guide the proposed design; a detailed comparison of their datasets, controls, and training experiments will precede the full study.

**Multilingual Mathematical Reasoning**

Shi et al. introduced MGSM to evaluate mathematical reasoning through translated grade-school problems [1]. Their work motivates comparing language versions of common mathematical content. Anand et al. studied open-source mathematical reasoning in Hindi and English, including supervised fine-tuning and bilingual training [2]. Consequently, mathematical training in two languages is not by itself a new contribution.

**Code Mixing and Romanized Instructions**

Yang and Chai introduced CodeMixBench to evaluate code-mixing capabilities across languages and tasks [3]. Das et al. introduced Indi-RomCoM, a benchmark for Romanized Indic-English instructions [4]. These studies demonstrate that code-mixed and Romanized evaluation are already active research areas. Sthanika's CodeMixTax report also examines Romanized-Hindi and code-mixed mathematical performance [5]. We treat this last source as a research report, not as a verified peer-reviewed publication.

**Model Adaptation and Feasibility**

The provisional model is Qwen3-4B, described in its official model card [6]. QLoRA provides a method for fine-tuning low-rank adapters while using a quantized base model [7]. We propose this approach to investigate feasibility under limited GPU resources. The intended workload has not yet been verified on our allocated T4; successful memory, timing, and checkpoint tests will be required before scaling.

**Research Gap and Proposed Contribution**

Our proposed contribution is a controlled comparison of E+R and E+C training using the same mathematical families and identical English solution targets. Evaluation will use independently reviewed, held-out families and predefined language variants. This design seeks evidence about the incremental value of code-mixed training beyond Romanized-Hindi exposure, rather than presenting a new Hinglish model or a small benchmark as sufficient novelty.

The precise distinction from existing work remains a research milestone. If a detailed audit finds that the proposed comparison has already been adequately studied, we will revise the scope with our supervisor before full training. Positive, negative, and inconclusive outcomes will be reported without changing the final test to obtain a favorable result.

**Research Questions**

- How does unchanged-model correctness differ across equivalent E, R, and C inputs?
- Does matched E+C training improve held-out C accuracy over E+R training?
- Do any gains persist on unseen spellings and phrasing, and what happens to English and Romanized-Hindi accuracy?

<!-- pagebreak -->

### 5. PROPOSED METHODOLOGY AND ARCHITECTURE

**Data preparation.** The pilot will contain 30 independent problem families, with E, R, and C forms for 90 prompts. Two bilingual reviewers will independently solve and assess the renderings before seeing the proposed answers. Disagreements will be adjudicated. A borrowing policy will distinguish genuine code mixing from common loanwords. Source provenance, licenses, edits, and AI assistance will be recorded.

**Controlled experiments.** We will run an unchanged-model baseline and a separate six-update-per-condition hardware test on 16 other families. The main comparison will match E+R and E+C training families, solution targets, update counts, and adapter settings, with three seeds planned per condition. English-only training and translate-then-solve inference are proposed controls, subject to the measured budget. Their inclusion will be decided before confirmatory experiments. Python, PyTorch, Transformers, PEFT, and bitsandbytes will support the implementation.

**Evaluation and safeguards.** Final-test families and their derivatives will be excluded from training and development. Pilot and hardware-test families will also remain outside the confirmatory study. The primary outcome is the paired difference in held-out C accuracy between training conditions. Equivalent numeric answers and predefined unit conversions will be accepted; malformed, refused, or truncated answers will count incorrect. We will report E/R/C results, family-based uncertainty, seed variation, and descriptive error categories. Dataset size and analysis rules will be finalized before final-test generation. Pretraining contamination cannot be ruled out completely.

<!-- workflow -->

### 6. EXPECTED GOALS

We propose a 12-week schedule from faculty approval, subject to reviewer and GPU availability. The next page shows the planned activities and outputs. Full training will proceed only after data review, novelty assessment, and hardware checks. Expected deliverables are reviewed data, reproducible code, an empirical report, and a paper draft if the completed evidence supports a distinct contribution; improved accuracy and publication acceptance are not guaranteed.

<!-- pagebreak -->

<!-- gantt -->

### 7. REFERENCES

[1] F. Shi et al. Language Models are Multilingual Chain-of-Thought Reasoners. arXiv:2210.03057, 2022.

[2] A. Anand et al. Multilingual Mathematical Reasoning: Advancing Open-Source LLMs in Hindi and English. AAAI, 39(22), 23415-23423, 2025. DOI: 10.1609/aaai.v39i22.34509.

[3] Y. Yang and Y. Chai. CodeMixBench: Evaluating Code-Mixing Capabilities of LLMs Across 18 Languages. EMNLP, 2139-2169, 2025. DOI: 10.18653/v1/2025.emnlp-main.109.

[4] A. Das, M. Parmar, M. Ramnath, and P. Verma. Indi-RomCoM: Code-Mixed Benchmark for Evaluating LLMs on Romanized Indic-English Instructions. arXiv:2606.30790, 2026. Preprint.

[5] Sthanika. The code-mixing tax on romanized Hindi, measured. Research report, 2026. sthanika.ai/research/codemix-tax-2026.

[6] Qwen Team. Qwen3-4B official model card. huggingface.co/Qwen/Qwen3-4B. Accessed 7 October 2026.

[7] T. Dettmers et al. QLoRA: Efficient Finetuning of Quantized LLMs. arXiv:2305.14314, 2023.

### 8. SIGNATURES

<!-- signatures -->

<!-- covers -->
