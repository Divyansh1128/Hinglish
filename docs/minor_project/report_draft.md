# Hinglish Mathematical Reasoning in Large Language Models
## Minor Project Report — DRAFT

**Bachelor of Technology, Final Year · Delhi Technological University**

Student name: ____________ Roll number: ____________ Department: ____________ Faculty in charge: ____________

Draft updated 26 October 2026 for the November 2026 minor-project evaluation. Every result below is labelled by evidence type: *software verification*, *development run on excluded fixtures*, or *Pilot-B result*. The Pilot-B results (Section 7) come from three complete, checksum-verified runs on a frozen, human-reviewed 70-family set, analysed under a plan pre-registered before any output (`pilot_b/PREREGISTRATION.md`). The original 30-family pilot, now reduced to a 24-family cohort under two-reviewer adjudication, is being run; its results are **pending** and are never pooled with Pilot-B.

---

### Abstract

Indian users often ask mathematical questions in Hinglish: Hindi and English mixed within a sentence and written in Roman script. This project asks whether the language form of an otherwise identical mathematical problem changes whether a large language model solves it correctly. We also ask whether code-mixed training helps more than exposure to Romanized Hindi alone. We render each problem as three matched forms: English (E), Romanized Hindi (R) and Roman-script code-mixed Hinglish (C). Gold answers are computed in code, every rendering is solved blind by two LLMs, and bilingual humans review the families. We evaluate unchanged small models (4-bit NF4 on a Colab T4) with a fixed English instruction, greedy decoding and a strict pre-registered scorer.

This phase delivered four things: a reproducible, resumable evaluation pipeline; 370 frozen families for the pilot extension and the later training study; a development study on permanently excluded fixtures; and the first real evaluation. On the fixtures, the original prompt made 10 of 36 Qwen3-4B outputs fail strict scoring and pushed 8 of 12 Romanized-Hindi explanations into Devanagari. One disclosed prompt revision reduced both to zero. A screen of seven models showed that format compliance is strongly model-specific; three passed a pre-declared rule. On the 70-family Pilot-B set (210 prompts per model), Romanized Hindi is the weakest form for all three backbones: Qwen3-4B scores 94.3 / 85.7 / 94.3% on E / R / C, Qwen3-8B 98.6 / 91.4 / 98.6%, and Llama-3.2-3B 94.3 / 57.1 / 70.0%. Code-mixed input is as easy as English for both Qwen models. R errors are not concentrated in items with Hindi operation words, so the operation-word misreading hypothesis from the development study is not supported. Results from the 24-family two-reviewer cohort are pending. The controlled training comparison is planned for the major-project phase.

### 1. Introduction and motivation

A model that solves "How many marbles does Aman have?" may fail on "Aman ke paas kitne kanche hain?" even though the mathematics is identical. If accuracy drops, the cause could be Hindi vocabulary, Roman-script spelling, the mixing of languages within a sentence, harder wording, or the evaluation protocol itself. Comparing unrelated English and Hinglish questions cannot separate these. This project therefore holds the mathematics fixed and varies only the language form.

### 2. Research questions

- **RQ1 (this phase).** How does an unchanged model's correctness differ across mathematically equivalent E, R and C prompts?
- **RQ2 (major phase).** Does E+C fine-tuning improve held-out C accuracy over matched E+R fine-tuning?
- **RQ3 (major phase).** Do gains transfer to unseen phrasing and spellings, and what happens to English accuracy?

### 3. Related work and positioning

Multilingual mathematical reasoning is established: MGSM [1], Hindi-English bilingual fine-tuning [2], code-mixed benchmarks covering Hindi-English GSM8K [3, 4], and an aligned Romanized-Hindi/Hinglish inference study [5]. Lower accuracy on code-mixed or Romanized input has been reported before, so **an E/R/C accuracy gap on existing models is not by itself novel**. This phase's contributions are narrower: a measurement caution about answer formats, a paired and reviewed E/R/C resource in which C keeps or switches R's Hindi operation words in balanced proportions, and a frozen diagnostic pilot with strict and numeric endpoints. The project's main intended contribution remains a controlled E+E / E+R / E+C training comparison with matched mathematical content, identical English solution targets and matched exposure, evaluated on independently drafted held-out families. A bounded 14-work audit did not locate this exact comparison (`research/astra_closest_work_update_2026-10-10.md`); this is not a guarantee of novelty.

### 4. Method

**Language forms.** E is English. R is Hindi phrasing in Roman script, with a borrowing list for numbers, units and established loanwords. C is Roman-script Hindi with English lexical material beyond that list. Human review showed that natural Hinglish is mostly *insertional*: Hindi grammar with English nouns, conjunct verbs and relation words (*23 add karta hai*). Pilot-B and Phase 2 therefore define C as requiring English material beyond R's borrowing list but no full English clause (decision D033). The original 30 families keep the earlier clause-based definition, which is one reason the two cohorts are reported separately.

**Datasets.** A family is one problem with three renderings, so all analyses are paired at the family level. Six topics are covered: comparison, money, fractions/percentages, ratios, rates/units and algebra. All families were LLM-drafted, with gold computed in code; Claude and GPT each solved every rendering blind (no Qwen model drafted, solved or checked).

| Set | Families | Drafted by | Human review | Status |
|---|---:|---|---|---|
| Original pilot | 30 → **24-family cohort** | AI | Two independent bilingual reviewers (R01, R02) plus an adjudicator (A01) | Cohort fixed (D036); run in progress, results pending |
| Pilot-B | 70 | Claude | One bilingual reviewer, all families: 57 ACCEPT, 13 REVISE, 0 REJECT | Frozen 16 Oct (`pilot_b/FROZEN.md`); evaluated |
| Phase-2 FINAL_TEST | 100 | GPT | One bilingual reviewer, all families: 32 ACCEPT, 68 REVISE (fixes applied) | Frozen 16 Oct; untouched until the confirmatory evaluation |
| Phase-2 DEV | 40 | GPT | Seeded sample shared with TRAIN (45 families: 19 ACCEPT, 26 REVISE) | Frozen 16 Oct |
| Phase-2 TRAIN | 160 | Claude | Same sample-based review | Frozen 16 Oct |

Pilot-B and Phase 2 together give **370 frozen families**, each file with a recorded SHA-256 hash. Blind solving matched gold on 210/210 first-version and 15/15 revised Pilot-B renderings; on the 900 Phase-2 renderings Claude matched 900/900 and GPT 897/900 (all misses in one family, a GPT error). Solver agreement shows only that the text encodes the intended calculation; the solvers may share blind spots. Review found GPT-drafted Romanized Hindi systematically over-formal (68/100 FINAL_TEST families needed repair, against 13/70 for Claude-drafted Pilot-B); this is descriptive, since drafter is confounded with split and prompt.

**Operation-word balance.** Hindi operation words (e.g. *bhaag* "divide", *bhinn* "fraction"/"different") appear in 27 of 30 original R drafts but only 10 of 30 C drafts, so on the original set a C advantage could partly reflect easier vocabulary. Pilot-B counters this: C *keeps* R's Hindi operation word in 18 families, *switches* it to English in 17, and 35 are controls without one.

**Original-pilot human review.** Two independent bilingual reviewers solved all 90 renderings before seeing the reference answer (R01 83/90 and R02 87/90 matched the reference), then rated equivalence, ambiguity, classification and naturalness. A third independent person (A01) adjudicated all 30 families: 24 ACCEPT, 5 REVISE, 1 EXCLUDE (PIL010, a near-duplicate of PIL002). The two returned re-reviews of the 5 repaired families were byte-identical, so they were not treated as independent, and the cohort is the **24 families accepted without repair** (D036; `pilot/reviews_v2_round2/README.md`).

**Model screening (development evidence).** Seven models were run on the excluded fixtures (Section 6) under the frozen prompt v2. A rule declared before screening (D028) admitted a model only if at most 3/36 fixture outputs were strict-invalid, with no per-model prompt or scorer tuning.

| Model | Strict-invalid of 36 | Correct E / R / C of 12 | Decision |
|---|---:|---:|---|
| Qwen3-4B | 0 | 12 / 10 / 12 | Primary backbone |
| Qwen3-8B | 0 | 12 / 12 / 12 | Included (D030) |
| Llama-3.2-3B-Instruct | 2 | 12 / 9 / 9 | Included (D032) |
| Qwen3-1.7B | 36 | 0 / 0 / 0 | Excluded: echoes the instruction (D029) |
| Phi-4-mini-instruct | 14 | 6 / 4 / 11 | Excluded: inline FINAL, R repetition (D025) |
| Granite-3.3-2B-instruct | 36 | 0 / 0 / 0 | Excluded: commentary after FINAL (D026) |
| Gemma-3-4B-it | — | — | Excluded: CUDA error under FP16, no outputs (D031) |

Phi-4-mini and Granite were excluded before the ≤3/36 rule was formalized; both exceed it. The pilot therefore has **three backbones**: Qwen3-4B (primary), Qwen3-8B (within-family scaling) and Llama-3.2-3B (cross-family). The latter two are secondary, descriptive comparisons.

**Inference protocol.** Pinned immutable model revisions; NF4 double quantization, FP16 compute, SDPA math kernel; thinking disabled (Qwen); greedy decoding; batch 1; 1,024 output tokens; fresh context per prompt; seeded order; one infrastructure retry; no answer-dependent retries. Llama's chat-template date is pinned so prompts stay frozen. The single English instruction (`test1-english-final-v2`) is identical for all forms and models.

**Scoring.** The primary endpoint is a strict scorer (v1.0.0, frozen): exactly one terminal `FINAL:` line, an exact rational value, and validated units with pre-declared aliases and conversions. Missing, refused, ambiguous or truncated answers count as wrong. The secondary endpoint, pre-specified before the pilot, is `numeric_literal_v1`: the sole FINAL line's literal value equals the gold value. It is reported beside the primary endpoint and never replaces it. Wilson 95% intervals are reported per form, and paired E−R, E−C and R−C differences use 10,000 family-bootstrap resamples (seed 101), with discordant-family counts. A manual audit of every output with a fixed error taxonomy and an English-output tag is planned (not yet reported).

### 5. System implementation (software verification)

- Self-contained Colab notebooks. They cover strict input validation, an append-only attempt journal with resume, immutable model/tokenizer revisions, environment fingerprints, refusal to resume after any code/data/configuration change, checksummed result ZIPs and manual-audit overlays that never overwrite automatic scores. A `MODEL_ID` setting and a `pilot_b` mode (single-reviewer attestation) were added for the three-backbone Pilot-B runs; the two-reviewer `reviewed` mode is unchanged.
- A secondary-analysis module: the numeric endpoint, per-form cross-tabulation, a code-mixing index and heuristic pre-tagging for human correction.
- Test status on 15 October: 22 pipeline tests, 38 secondary-analysis tests, 3 scorer tests and 4 training-protocol tests, all passing. These verify software behaviour only.

### 6. Pre-pilot measurement study (development run on excluded fixtures)

Before spending the one-shot pilot, we ran 12 newly authored fixture families (36 prompts) through the identical pipeline on a Colab T4. The fixtures are permanently excluded from the pilot and from all later training and test data.

| Prompt version | Strict failures from formatting | Strict correct E / R / C | R explanations in Devanagari |
|---|---:|---:|---:|
| v1 (original) | 10/36 | 9 / 7 / 9 of 12 | 8/12 |
| v2 (revised before pilot) | **0/36** | 12 / 10 / 12 of 12 | **0/12** |

Findings:
1. **The original instruction confounded the measurement.** "`<unit when applicable>`" led the model to write `FINAL: 8 unitless` or `24 unit.` after dimensionless answers. That is a format failure on a mathematically correct answer, and it would have affected the original pilot's six dimensionless families in every form.
2. **The model ignored the English-output instruction for Romanized-Hindi input** under v1, writing Hindi, often in Devanagari. Prompt v2 states "in English, even if the question is not in English".
3. **The remaining errors looked like operation-word misreadings.** Under v2 both errors were R-only. *bhaag dekar* (divide) was treated as a difference, and *kitna bhinn* (what fraction) was answered as a remaining count; *bhinn* also means "different" in Hindi. Llama-3.2-3B gave the same wrong answer (20) on the *bhinn* item. With two unreviewed items this was only a hypothesis; it motivated the keep/switch design of Pilot-B and was then tested there (Section 7.3).
4. **Format compliance is model-specific** (screening table in Section 4). Within Qwen3, instruction following broke before mathematics did (36/36 invalid at 1.7B, 0/36 at 4B and 8B). Without a compliance check on excluded data, a multi-model comparison would mostly measure formatting.

The prompt revision is a disclosed, versioned protocol change (decision D020), made once on excluded data and frozen before any pilot generation. The fixtures also changed slightly between runs (one R rendering repaired, one alias added), so 10 → 0 is a development comparison, not an isolated prompt effect. With 12 items per form these are indications, not estimates.

### 7. Pilot-B results (70 families × E/R/C, strict scorer v1.0.0)

**Evidence type: Pilot-B result.** Pre-registered plan: `pilot_b/PREREGISTRATION.md`, committed before any Pilot-B output. Single-reviewer frozen data (D035). Each backbone ran once on a Colab T4 and completed 210/210 renderings; all checksums were verified and the tables reproduce the stored metrics exactly (`results/pilot_b/`). Seventy families is a diagnostic sample, so all comparisons are descriptive.

#### 7.1 Accuracy by form

Strict accuracy (%) with Wilson 95% intervals and counts. *invalid* = strict-invalid outputs (truncations in parentheses). No refusals occurred.

| Backbone | E | R | C |
|---|---|---|---|
| **Qwen3-4B** (primary) | 94.3 [86.2, 97.8] (66/70) | 85.7 [75.7, 92.1] (60/70) | 94.3 [86.2, 97.8] (66/70) |
| invalid | 3 | 2 | 1 |
| Qwen3-8B | 98.6 [92.3, 99.7] (69/70) | 91.4 [82.5, 96.0] (64/70) | 98.6 [92.3, 99.7] (69/70) |
| invalid | 1 | 1 | 0 |
| Llama-3.2-3B | 94.3 [86.2, 97.8] (66/70) | 57.1 [45.5, 68.1] (40/70) | 70.0 [58.5, 79.5] (49/70) |
| invalid | 1 | 6 (5) | 4 (2) |

Figure: `paper/figures/accuracy_by_form.png` (strict accuracy by form with Wilson intervals, 70 families per bar).

#### 7.2 Paired differences

Percentage points, with 95% intervals from 10,000 family-bootstrap resamples (seed 101). In parentheses: discordant families correct only in the first / only in the second form.

| Backbone | E−R | E−C | R−C |
|---|---|---|---|
| **Qwen3-4B** | +8.6 [−1.4, +18.6] (9/3) | 0.0 [−7.1, +7.1] (3/3) | **−8.6 [−15.7, −1.4]** (1/7) |
| Qwen3-8B | +7.1 [0.0, +14.3] (6/1) | 0.0 [−4.3, +4.3] (1/1) | −7.1 [−14.3, 0.0] (1/6) |
| Llama-3.2-3B | **+37.1 [+24.3, +50.0]** (28/2) | **+24.3 [+11.4, +37.1]** (21/4) | −12.9 [−27.1, +1.4] (10/19) |

Findings:
1. **Romanized Hindi is the weakest form for all three backbones.** The size of the deficit depends strongly on the model: modest for Qwen (8.6 and 7.1 points, intervals crossing or touching zero) and large for Llama (37.1 points, interval well above zero).
2. **Code-mixing is not the problem for Qwen.** For both Qwen models C matches E exactly (E−C = 0.0) and exceeds R; for Qwen3-4B the R−C interval excludes zero (C better in 7 families, R better in 1). For Llama, C lies between E and R.
3. **Scale helps within the Qwen family but leaves the R deficit.** 4B → 8B raises R from 85.7% to 91.4% and E/C from 94.3% to 98.6%; the E−R gap moves only from 8.6 to 7.1 points.

#### 7.3 Operation-word hypothesis: null result

In the pre-registered descriptive split by whether C keeps or switches R's Hindi operation word (or R has none), R accuracy is similar across strata for every model:

| Backbone | R: keep (18) | R: switch (17) | R: no op-word (35) |
|---|---:|---:|---:|
| Qwen3-4B | 89% | 82% | 86% |
| Qwen3-8B | 94% | 94% | 89% |
| Llama-3.2-3B | 67% | 59% | 51% |

The R deficit is therefore **not concentrated** in items with *bhaag*/*bhinn*-type vocabulary, so the misreading hypothesis suggested by the two development errors (Section 6) is not supported at this scale. Many Llama R errors are arithmetic slips on simple items (e.g. PB017: 1200 − 3×265 = 405, answered as 435).

#### 7.4 Residual format effects

- **Llama:** the secondary numeric endpoint agrees with strict scoring on all 210 renderings, so its gaps are not formatting artifacts.
- **Qwen3-4B:** all 6 strict-invalid outputs are `invalid_unit`. Three of E's four failures are numerically correct answers with English unit phrases outside the aliases (`11 years old`, `13 years old`, `4 bags of cement`), and one C failure is an unlisted spelling (`300 rupye`), the form-dependent alias penalty anticipated before the pilot. Together these cost Qwen3-4B 4 strict points.
- **Secondary-endpoint specification gap (Qwen):** the frozen numeric grammar does not accept a *trailing* rupee symbol (`FINAL: 1575 ₹`), which strict scoring accepts as a unit. This accounts for every strict-correct/numeric-fail case (30 for Qwen3-4B, 36 for Qwen3-8B), so numeric_literal_v1 falls below strict (Qwen3-4B: E 72.9 / R 82.9 / C 82.9%; Qwen3-8B: E 84.3 / R 74.3 / C 80.0%). The gap is in the endpoint's specification, not in the models. It is reported as pre-registered and not corrected post hoc; a post-hoc sensitivity check (not pre-registered) that allows the trailing symbol restores agreement with strict on all 36 Qwen3-8B cases.

#### 7.5 Exploratory note (not pre-registered; Llama)

Despite the English-explanation instruction, Llama explained 60/70 R and 27/70 C outputs in Romanized-Hindi prose (E: 0/70; no Devanagari; heuristic detection). On C, Hindi-prose explanations were correct 13/27 (48%) against 36/43 (84%) for English explanations; on R, 35/60 against 5/10. This is observational: harder items may both trigger Hindi explanations and cause errors. The planned English-compliance audit is needed before any claim.

#### 7.6 Original-pilot cohort (pending)

The 24-family original-pilot cohort (two independent bilingual reviewers plus an adjudicator; D036) is being run under the same frozen protocol. Its results are **pending** and will be reported separately from Pilot-B, never pooled, because the two cohorts differ in review depth and in the C definition.

### 8. Limitations

- **Diagnostic scale.** 70 families per backbone give a diagnostic pilot, not a confirmatory estimate; the operation-word strata (17–35 families) are sparse and descriptive. Model-free power calculations show that detecting a 5-point paired difference needs hundreds of families.
- **Single reviewer.** Pilot-B and FINAL_TEST were each reviewed by one bilingual team member; TRAIN/DEV received sample-based review only (45 families), so unsampled families may still contain stilted Romanized Hindi. Naturalness judgments reflect one speaker's register. Only the 24-family original cohort rests on two independent reviewers plus adjudication, and its results are pending.
- **AI-authored data.** Items share LLM drafting styles that independent authors may not; Claude both drafted and blind-solved Pilot-B. The GPT/Claude repair contrast is confounded with split and prompt.
- **Different C definitions.** The original 30 and Pilot-B define C differently, which prevents a pooled C estimate. The original 30 also have unbalanced operation words (27/30 R vs 10/30 C drafts; `research/operation_vocabulary_2026-10-15.md`).
- **Models.** All three backbones are small, 4-bit quantized, greedy and non-thinking; results are conditional on this configuration. Admitting models by format compliance excluded four of the seven screened models whose formatting the scorer does not accept.
- **Residual format effects.** Strict scoring still penalises some correct answers (unlisted English unit phrases, the spelling `rupye`), and the secondary endpoint has the trailing-₹ specification gap. Both are reported, not corrected post hoc.
- **Thin development evidence.** The prompt was revised after seeing outputs on 12 unreviewed fixture families; this is disclosed, and no pilot item was used to design the prompt.
- **No script control.** There is no Devanagari arm, so an E−R gap mixes script, language, register and spelling. C ≈ E with R < E suggests Hindi vocabulary rather than mixing, but does not identify the cause. Published work already reports drops from native script to Romanized input (e.g. Sarvam-M, CodeMixTax), so the R gap supports a language-form effect, not a novel discovery.
- **Contamination.** The items are new, but the models' pretraining data cannot be audited.
- **No training yet.** RQ2 and RQ3 are untested; the manual error-taxonomy and English-compliance audit of Pilot-B outputs is still to be done.

### 9. Plan for the major-project phase (to May 2027)

| Period | Milestone |
|---|---|
| Nov 2026 | Original-pilot (24-family) run and analysis; error-taxonomy and English-compliance audit of Pilot-B outputs; minor evaluation |
| Dec 2026 – Jan 2027 | Training feasibility smoke test on T4 (completion-only loss, memory, checkpoint reload); second-annotator sample on Pilot-B and FINAL_TEST |
| Feb – Mar 2027 | E+E / E+R / E+C fine-tuning with paired seeds on the frozen TRAIN/DEV; one confirmatory evaluation on the untouched FINAL_TEST, plus English retention |
| Apr 2027 | Analysis, thesis and paper draft |
| May 2027 | Final submission |

Publication plan (decision D023): a 4-page short paper on the pilot for the EACL 2027 Student Research Workshop (optional mentorship draft 6 Nov 2026, submission 15 Dec 2026; draft in `paper/latex/main.tex`), then the training study for the ARR May 2027 cycle (date unconfirmed). Training feasibility is planned on the inference-verified T4 stack, with pre-declared go/no-go thresholds (decision D021).

### References

[1] F. Shi et al. Language Models are Multilingual Chain-of-Thought Reasoners. arXiv:2210.03057, 2022.
[2] A. Anand et al. Multilingual Mathematical Reasoning: Advancing Open-Source LLMs in Hindi and English. AAAI 39(22), 2025.
[3] Y. Yang and Y. Chai. CodeMixBench: Evaluating Code-Mixing Capabilities of LLMs Across 18 Languages. EMNLP 2025.
[4] A. Das et al. Indi-RomCoM: Code-Mixed Benchmark for Evaluating LLMs on Romanized Indic-English Instructions. arXiv:2606.30790, 2026 (preprint).
[5] Sthanika. The code-mixing tax on romanized Hindi, measured. Research report, 2026.
[6] Qwen Team. Qwen3-4B model card. huggingface.co/Qwen/Qwen3-4B.
[7] T. Dettmers et al. QLoRA: Efficient Finetuning of Quantized LLMs. arXiv:2305.14314, 2023.
[8] A. Das and B. Gambäck. Code-Mixing Index, §3.3. ICON 2014. ACL Anthology W14-5152. (Verify title before submission.)

*Evidence sources:* `results/pilot_b/SUMMARY.md` and `results/pilot_b/*/RESULTS.md` (Pilot-B results), `pilot_b/PREREGISTRATION.md`, `pilot_b/FROZEN.md`, `phase2/FINAL_TEST_FROZEN.md`, `phase2/TRAIN_DEV_FROZEN.md`, `pilot/reviews_v2_round2/README.md`, `research/fmt2_format_test_2026-10-14/` and the other `research/fmt2_*` screening runs, `research/claude_review/`, `research/pre_pilot_endpoint_spec_v1.md`, `docs/DECISIONS.md` (D020, D025–D036), `test1_pilot/VERIFICATION.md`, `paper/latex/main.tex`.
