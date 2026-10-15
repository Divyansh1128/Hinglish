# Hinglish Mathematical Reasoning in Large Language Models
## Minor Project Report — DRAFT

**Bachelor of Technology, Final Year · Delhi Technological University**

Student name: ____________ Roll number: ____________ Department: ____________ Faculty in charge: ____________

Draft prepared 15 October 2026 for the November 2026 minor-project evaluation. Sections marked **[PENDING PILOT]** are filled only from the frozen, human-reviewed pilot run. Every result below is labelled by evidence type: *software verification*, *development run on excluded fixtures*, or *pilot result*. No pilot result exists yet.

---

### Abstract

Indian users often ask mathematical questions in Hinglish: Hindi and English mixed within a sentence and written in Roman script. This project asks whether the language form of an otherwise identical mathematical problem changes whether a large language model solves it correctly. We also ask whether code-mixed training helps more than exposure to Romanized Hindi alone. We render each problem as three matched forms: English (E), Romanized Hindi (R) and Roman-script code-mixed Hinglish (C). We evaluate one unchanged model, Qwen3-4B (4-bit NF4 on a Colab T4), with a fixed English instruction, greedy decoding and a strict pre-registered scorer. This minor-project phase delivered three things. The first is a reproducible, resumable evaluation pipeline with checksummed exports. The second is a 30-family, 90-prompt pilot set under independent bilingual review. The third is a pre-pilot measurement study on excluded fixtures. That study showed the original prompt caused 10 of 36 correct-looking answers to fail scoring and pushed Romanized-Hindi explanations into Devanagari. A versioned prompt revision removed both effects (0/36 format failures). The remaining errors were Romanized-Hindi-only misreadings of operation words such as *bhaag* (divide) and *bhinn* (fraction / "different"). The human-reviewed pilot result is **[PENDING PILOT]**. The controlled training comparison is planned for the major-project phase.

### 1. Introduction and motivation

A model that solves "How many marbles does Aman have?" may fail on "Aman ke paas kitne kanche hain?" even though the mathematics is identical. If accuracy drops, the cause could be Hindi vocabulary, Roman-script spelling, the mixing of languages within a sentence, or simply harder wording. Comparing unrelated English and Hinglish questions cannot separate these. This project therefore holds the mathematics fixed and varies only the language form.

### 2. Research questions

- **RQ1 (this phase).** How does an unchanged model's correctness differ across mathematically equivalent E, R and C prompts?
- **RQ2 (major phase).** Does E+C fine-tuning improve held-out C accuracy over matched E+R fine-tuning?
- **RQ3 (major phase).** Do gains transfer to unseen phrasing and spellings, and what happens to English accuracy?

### 3. Related work and positioning

Multilingual mathematical reasoning is established: MGSM [1], Hindi-English bilingual fine-tuning [2], code-mixed benchmarks covering Hindi-English GSM8K [3, 4], and an aligned Romanized-Hindi/Hinglish inference study [5]. These works mean that **measuring an E/R/C accuracy gap on existing models is not by itself novel**. The project's intended contribution is narrower. It is a controlled E+E / E+R / E+C training comparison with matched mathematical content, identical English solution targets and matched exposure, evaluated on independently authored held-out families. A bounded 14-work audit did not locate this exact comparison (`research/astra_closest_work_update_2026-10-10.md`); this is not a guarantee of novelty.

### 4. Method

**Language forms.** E is English. R is Hindi phrasing in Roman script, under a proposed borrowing policy for numbers, units and established loanwords. C is Roman-script Hindi with productive English clauses or relations, not just English nouns.

**Problem families.** There are 30 families, five in each of six topics: comparison and remaining quantity, two-step money, fractions and percentages, ratios, rates and units, and elementary algebra. Each family has three renderings, so the pilot has 90 prompts. Ninety prompts represent 30 families, not 90 independent problems, and all analyses are paired at the family level.

**Human review.** All drafts are AI-authored. Two independent bilingual reviewers solve each question before seeing the reference answer. They then check equivalence, ambiguity, language classification and naturalness, and a separate adjudicator resolves disagreements. Only accepted families enter the pilot. Status: v2 review packets distributed; **[PENDING: R01/R02 submissions, A01 adjudication]**.

**Inference protocol.** Qwen3-4B at a pinned immutable revision; NF4 double quantization, FP16 compute, SDPA math kernel; thinking disabled; greedy decoding; batch 1; 1,024 output tokens; fresh context per prompt; seeded order; one infrastructure retry; no answer-dependent retries.

**Scoring.** The primary endpoint is a strict scorer (v1.0.0, frozen): exactly one terminal `FINAL:` line, an exact rational value, and validated units with pre-declared aliases and conversions. Missing, refused, ambiguous or truncated answers count as wrong. The secondary endpoint, pre-specified before the pilot, is `numeric_literal_v1`: the sole FINAL line's literal value equals the gold value. It is reported beside the primary endpoint and never replaces it. Wilson intervals are reported per form, and paired E−C, E−R and R−C differences use 10,000 family-bootstrap resamples. Every output is manually audited with a fixed error taxonomy and an English-output tag.

### 5. System implementation (software verification)

- A self-contained Colab notebook. It covers strict input validation, an append-only attempt journal with resume, immutable model/tokenizer revisions, environment fingerprints, refusal to resume after any code/data/configuration change, checksummed result ZIPs and manual-audit overlays that never overwrite automatic scores.
- A secondary-analysis module: the numeric endpoint, per-form cross-tabulation, a code-mixing index and heuristic pre-tagging for human correction.
- Test status at the time of writing: 22 pipeline tests, 38 secondary-analysis tests, 3 scorer tests and 4 training-protocol tests, all passing. These verify software behaviour only.

### 6. Pre-pilot measurement study (development run on excluded fixtures)

Before spending the one-shot pilot, we ran 12 newly authored fixture families (36 prompts) through the identical pipeline on a Colab T4. The fixtures are permanently excluded from the pilot and from all later training and test data.

| Prompt version | Strict failures from formatting | Strict correct E / R / C | R explanations in Devanagari |
|---|---:|---:|---:|
| v1 (original) | 10/36 | 9 / 7 / 9 of 12 | 8/12 |
| v2 (revised before pilot) | **0/36** | 12 / 10 / 12 of 12 | **0/12** |

Findings:
1. **The original instruction confounded the measurement.** "`<unit when applicable>`" led the model to write `FINAL: 8 unitless` or `24 unit.` after dimensionless answers. That is a format failure on a mathematically correct answer, and it would have affected the pilot's six dimensionless families in every form.
2. **The model ignored the English-output instruction for Romanized-Hindi input** under v1, writing Hindi, often in Devanagari. Prompt v2 states "in English, even if the question is not in English".
3. **The remaining errors are language-form effects.** Under v2 both errors were R-only misreadings of operation words in correctly worded questions. *bhaag dekar* (divide) was treated as a difference, and *kitna bhinn* (what fraction) was answered as a remaining count; *bhinn* also means "different" in Hindi.

The prompt revision is a disclosed, versioned protocol change (decision D020), made once on excluded data and frozen before any pilot generation. With 12 items per form these are indications, not estimates.

### 7. Pilot results **[PENDING PILOT]**

To be filled from the reviewed pilot's results ZIP: per-form accuracy with Wilson intervals; paired E−R, E−C and R−C differences with bootstrap intervals and discordant counts; invalid, refusal and truncation rates; strict vs numeric endpoint cross-tabulation; error-taxonomy and English-compliance counts; operation-vocabulary covariate (descriptive); input/output tokens and latency per form.

### 8. Limitations

- 30 families give a diagnostic pilot, not a confirmatory estimate. Model-free power calculations show detecting a 5-point paired difference needs hundreds of families.
- One model, quantized, greedy, non-thinking: results are conditional on this configuration.
- AI-authored items, even after human review, may share an authoring style that independent authors would not.
- The development run informed the prompt; this is disclosed, and pilot items were never used for prompt design.
- No training has been performed; RQ2 and RQ3 are untested.

### 9. Plan for the major-project phase (to May 2027)

| Period | Milestone |
|---|---|
| Nov 2026 | Reviewed pilot run and analysis; minor evaluation |
| Dec 2026 – Jan 2027 | Training feasibility smoke test on T4 (completion-only loss, memory, checkpoint reload); scale data beyond 30 families with independent authors |
| Feb – Mar 2027 | E+E / E+R / E+C fine-tuning with paired seeds; held-out evaluation and English retention |
| Apr 2027 | Analysis, thesis and paper draft |
| May 2027 | Final submission |

### References

[1] F. Shi et al. Language Models are Multilingual Chain-of-Thought Reasoners. arXiv:2210.03057, 2022.
[2] A. Anand et al. Multilingual Mathematical Reasoning: Advancing Open-Source LLMs in Hindi and English. AAAI 39(22), 2025.
[3] Y. Yang and Y. Chai. CodeMixBench: Evaluating Code-Mixing Capabilities of LLMs Across 18 Languages. EMNLP 2025.
[4] A. Das et al. Indi-RomCoM: Code-Mixed Benchmark for Evaluating LLMs on Romanized Indic-English Instructions. arXiv:2606.30790, 2026 (preprint).
[5] Sthanika. The code-mixing tax on romanized Hindi, measured. Research report, 2026.
[6] Qwen Team. Qwen3-4B model card. huggingface.co/Qwen/Qwen3-4B.
[7] T. Dettmers et al. QLoRA: Efficient Finetuning of Quantized LLMs. arXiv:2305.14314, 2023.
[8] A. Das and B. Gambäck. Code-Mixing Index, §3.3. ICON 2014. ACL Anthology W14-5152. (Verify title before submission.)

*Evidence sources:* `research/fmt2_format_test_2026-10-14/`, `research/claude_review/`, `research/pre_pilot_endpoint_spec_v1.md`, `docs/DECISIONS.md`, `test1_pilot/VERIFICATION.md`.
