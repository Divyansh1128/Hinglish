# Hinglish Mathematical Reasoning in Large Language Models
## A Controlled Study of Code Mixing and Romanized Hindi

**Major Project Synopsis | Bachelor of Technology | Final Year**

**Delhi Technological University**

Student name: ____________________    Roll number: ____________________

Department: ______________________    Faculty in charge: _______________

Date: 7 October 2026

### 1 Abstract

This project proposes a controlled study of mathematical reasoning in English, Romanized Hindi, and Hinglish. It will investigate whether changing the language of an otherwise equivalent mathematical problem affects answer correctness, and whether code-mixed training offers benefits beyond exposure to Hindi written in Roman script. The study will use matched problem families, independent bilingual review, and a reproducible evaluation pipeline. An unchanged-model pilot will precede a comparison of English plus Romanized-Hindi training with English plus Hinglish training. English-only training and translation-based inference are proposed controls, subject to a measured compute budget. Parameter-efficient fine-tuning will be assessed on the available Colab T4 before larger experiments. Expected deliverables are reviewed data, reproducible software, and an empirical analysis of language robustness. The project seeks approval for this investigation; it does not assume improved accuracy, established novelty, or publication acceptance.

### 2 Problem Statement and Scope

The central problem is to distinguish sensitivity to code mixing from sensitivity to Hindi vocabulary, Roman script, or mathematical difficulty. Comparing unrelated English and Hinglish questions would confound these factors. We therefore propose equivalent renderings of each problem: English (E), Romanized Hindi (R), and Roman-script Hinglish (C). R will avoid substantive English clauses, while C will include productive English phrases or clauses alongside Hindi. A documented policy will distinguish common borrowings from code switches.

The study will cover numerical word problems in comparisons, money, fractions and percentages, ratios, rates and units, and elementary algebra. Solution explanations will remain in English across conditions to control output language. The scope excludes training a foundation model from scratch, unrestricted symbolic mathematics, and deployment as a classroom decision system.

### 3 Objectives

- Measure paired differences in mathematical correctness across E, R, and C inputs.
- Test whether E+C training improves held-out Hinglish accuracy relative to matched E+R training.
- Examine generalization to unseen problem families and reviewed spelling or phrasing variants, while monitoring English performance.
- Produce an auditable dataset and evaluation pipeline, including uncertainty estimates and descriptive error analysis.

<!-- pagebreak -->

### 4 Related Work and Proposed Contribution

MGSM evaluates multilingual mathematical reasoning using translated grade-school problems [1]. Anand et al. investigate mathematical reasoning and bilingual supervised fine-tuning in Hindi and English [2]. CodeMixBench evaluates code mixing across multiple languages and tasks [3]. Indi-RomCoM extends evaluation to Romanized Indic-English instructions [4]. Sthanika's CodeMixTax report also examines Romanized-Hindi and code-mixed mathematical performance [5]; it is treated as a research report rather than a verified peer-reviewed publication.

These works preclude claiming that multilingual mathematics, code-mixed evaluation, or Hinglish fine-tuning alone is new. The proposed contribution is a narrowly controlled training comparison with matched mathematical content and solution supervision, followed by evaluation on independent families and language variants. A detailed comparison of prior controls, datasets, and training experiments will precede protocol finalization. If the proposed comparison substantially duplicates prior work, the scope will be revised with the faculty before full training.

### 5 Research Questions

**RQ1** How does the unchanged model's correctness differ across mathematically equivalent E, R, and C prompts?

**RQ2** Does E+C training improve held-out C accuracy over E+R training when problem families, targets, and training schedules are matched?

**RQ3** Do any gains extend to unseen phrasing and Romanized spellings, and what tradeoffs occur on E and R inputs?

### 6 Dataset and Human Validation

The pilot will contain 30 independent families, five per topic, with three renderings each: 90 evaluation prompts. Five illustrative families exist as drafts; they are not validated data. Bilingual reviewers are available. The protocol will use two independent reviews of each rendering, covering the equation, answer, units, ambiguity, naturalness, and language classification. Reviewers will solve problems before seeing the proposed gold answer. Disagreements will be adjudicated before acceptance, with reviewer and adjudicator roles finalized in advance.

A separate set of 16 families will support hardware testing. Pilot and hardware-test families, including translations, paraphrases, and numerical siblings, will be excluded permanently from confirmatory training and final testing. Sources, licenses, AI assistance, edits, and review decisions will be recorded. Automated matching and human inspection will audit cross-split overlaps; they cannot guarantee absence from model pretraining.

The larger study will use distinct training, development, and final-test families. Its size will be justified through annotation capacity, compute measurements, and a sensitivity or power analysis before final-test generation. The 30-family pilot will not establish the training effect. Any spelling-variant analysis will be specified in advance and grouped by underlying family.

<!-- pagebreak -->

### 7 Experimental Method and Implementation

**Baseline.** Run the unchanged model on the frozen pilot with a fixed prompt, decoding policy, output limit, and fresh context per input. Store raw responses, token counts, latency, and failure reasons. A translate-to-English-then-solve baseline will assess a simpler alternative; translation settings and both stages' costs will be recorded.

**Training comparison.** The primary conditions will use English plus Romanized Hindi (E+R) and English plus Hinglish (E+C). Each family will have identical English completion targets in both conditions. Model initialization, data order, example exposure, optimizer updates, and adapter settings will be matched; actual input and supervised token counts will be reported. An English-only condition will use matched example exposure, repeating the English rendering rather than adding new problems. Its inclusion will be decided before confirmatory runs, not after observing outcomes.

**Resources.** The provisional candidate is Qwen3-4B [6], using QLoRA-style quantized adapter training [7]. One Colab T4 with nominal 16 GB VRAM is available. Neither stack compatibility nor workload fit has been established. A separate bounded smoke test will attempt six updates per primary condition, with memory monitoring, completion-only loss checks, and a clean-process checkpoint reload. Larger training requires successful integrity checks and an affordable measured runtime. Hardware changes will apply to both conditions and be documented before final evaluation.

**Implementation sequence.** Extend the existing scorer and input checks into a dataset validator, baseline inference runner, reporting pipeline, training runner, and checkpoint/resume verifier. Use Python, PyTorch, Transformers, PEFT, and bitsandbytes with pinned versions and immutable model revisions. The target is three seeds per primary training condition; a second-model replication is an extension if resources permit.

### 8 Evaluation and Analysis

The primary outcome will be the paired difference in held-out C accuracy between E+C and E+R training. Accuracy will count exact numeric or rationally equivalent final answers, with predefined unit conversions and omission rules. Missing or ambiguous final answers, refusals, and truncated outputs will count incorrect; unresolved infrastructure errors will make the run incomplete rather than silently reduce its denominator.

Secondary outcomes will include E and R accuracy, E-to-C and R-to-C accuracy gaps, and correctness changes under reviewed spelling variants. The pilot will use Wilson accuracy intervals and 10,000 paired family bootstrap resamples for descriptive difference intervals. The final analysis will report seed-specific effects and an across-seed summary, clustering uncertainty by family and accounting for seed variation rather than treating repeated predictions as independent questions. A meaningful-effect threshold and English-retention tolerance will be specified before confirmatory runs.

Independent review will examine pilot scoring discrepancies and a predefined sample of final errors. Categories will include apparent language interpretation, mathematical setup, calculation, and output-format errors. These are descriptive annotations, not proof of internal model mechanisms. Inconclusive differences will not be interpreted as equivalence.

<!-- pagebreak -->

### 9 Work Plan and Expected Outcomes

The following 12-week schedule is provisional from faculty approval and depends on reviewer and GPU availability.

| Period | Planned work and completion milestone |
| --- | --- |
| Weeks 1 and 2 | Audit novelty, finalize scope and review rubric, approve the pilot protocol. |
| Weeks 3 and 4 | Review and adjudicate pilot/smoke data; implement baseline inference and reports. |
| Weeks 5 and 6 | Run the baseline and hardware tests; decide feasibility and freeze the full-study design. |
| Weeks 7 and 8 | Prepare and audit larger splits; finalize sample-size and statistical-analysis plans. |
| Weeks 9 and 10 | Run controlled training and final evaluation under the frozen protocol. |
| Weeks 11 and 12 | Analyze errors and uncertainty; prepare the report, reproducibility package, and paper draft. |

Expected outputs are a documented evaluation resource, a tested inference and training pipeline, saved configurations and outputs, and a research report. A paper submission will be considered if the completed work establishes a distinct contribution with adequate evidence; positive results and acceptance are not promised. Release of data and adapters will respect source and model licenses. Reviewer participation, attribution, and any institutional requirements will be agreed before annotation; personal identifiers will not be included in released review records.

### 10 Present Status and Approval Sought

The pilot design, answer scorer, and model-free input checks are prepared; seven software test methods and a protocol self-check passed in the latest local verification. Human reviewers are available, but annotation and adjudication remain pending. No model inference, GPU measurement, or training experiment has been completed. Approval is requested for the research scope, review process, staged feasibility tests, and provisional work plan. The untouched final-test set will not be used for development or model selection.

### 11 References

[1] F. Shi et al. Language Models are Multilingual Chain-of-Thought Reasoners. arXiv:2210.03057, 2022.

[2] A. Anand et al. Multilingual Mathematical Reasoning: Advancing Open-Source LLMs in Hindi and English. AAAI, 39(22), 23415-23423, 2025. DOI: 10.1609/aaai.v39i22.34509.

[3] Y. Yang and Y. Chai. CodeMixBench: Evaluating Code-Mixing Capabilities of LLMs Across 18 Languages. EMNLP, 2139-2169, 2025. DOI: 10.18653/v1/2025.emnlp-main.109.

[4] A. Das, M. Parmar, M. Ramnath, and P. Verma. Indi-RomCoM: Code-Mixed Benchmark for Evaluating LLMs on Romanized Indic-English Instructions. arXiv:2606.30790, 2026. Preprint.

[5] Sthanika. The code-mixing tax on romanized Hindi, measured. Research report, 2026. sthanika.ai/research/codemix-tax-2026.

[6] Qwen Team. Qwen3-4B official model card. huggingface.co/Qwen/Qwen3-4B. Accessed 7 October 2026.

[7] T. Dettmers et al. QLoRA: Efficient Finetuning of Quantized LLMs. arXiv:2305.14314, 2023.
