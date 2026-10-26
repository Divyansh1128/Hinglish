# Pre-submission novelty and related-work refresh

**Filename date requested: 27 October 2026. Actual search and verification date: 26 October 2026 (UTC and Asia/Kolkata).** Coverage ends on the actual search date, not the future filename date. Main window: 26 October 2025–26 October 2026; older directly relevant precedents are identified below. This is a bounded primary-source audit, not exhaustive novelty clearance or a venue-acceptance prediction.

## Decision and proposed Introduction sentence

**Verdict: the broad R-harder-than-C framing is already present in prior work; the project remains distinguishable as a focused replication/extension and evaluation audit, not as the first discovery of that ordering.** The precise Qwen3-4B/8B result on these reviewed cohorts was not located in the inspected sources. That narrow observation does not establish population equivalence or make changing the backbone a scientific novelty claim.

Proposed exact one-sentence positioning:

> Building on prior evidence of Romanized-language degradation, we provide a reproducible, scoring-aware audit of small open LLMs on newly drafted, human-reviewed English/Romanized-Hindi/Hinglish math triplets, finding lower observed accuracy for Romanized Hindi across the tested models and equal aggregate English–Hinglish accuracy for Qwen3-4B and Qwen3-8B in two separately reported cohorts.

Attach the existing Sthānika and Indi-RomCoM citations and the new Peter et al. citation to the surrounding Introduction discussion. Avoid “first,” “code-mixing is harmless,” or an unqualified “not code-mixing.” A more defensible title proposal is **“Romanized Hindi Is Harder Than Hinglish: A Scoring-Aware Audit of Small LLMs.”** This is a proposal; no manuscript text was changed.

## What our evidence actually establishes

Read: README.md; DECISIONS D030–D037; Pilot-B SUMMARY; both original-cohort RESULTS files; the complete main.tex and references.bib; team board and latest 26 October handoffs. The README's 10 October status and the manuscript's original-review TODOs are stale relative to D036/D037 and the supplied results. Results were read, not regenerated or independently re-scored in this task.

| Cohort/model | E | R | C | Interpretation |
|---|---:|---:|---:|---|
| Pilot-B, Qwen3-4B, 70 families | 94.3% | 85.7% | 94.3% | R−C −8.6 pp, family-bootstrap interval [−15.7, −1.4]; E−C 0.0 [−7.1, +7.1]. |
| Pilot-B, Qwen3-8B, 70 | 98.6% | 91.4% | 98.6% | R−C −7.1 [−14.3, 0.0]; E−C 0.0 [−4.3, +4.3]. |
| Pilot-B, Llama-3.2-3B, 70 | 94.3% | 57.1% | 70.0% | R lowest, but C also substantially below E. R−C interval includes zero. |
| Original cohort, Qwen3-4B, 24 | 100% | 91.7% | 100% | Same direction; no strict-invalid output; descriptive near-ceiling cohort. |
| Original cohort, Qwen3-8B, 24 | 100% | 95.8% | 100% | Same direction; no strict-invalid output; descriptive near-ceiling cohort. |

Sources: [Pilot-B](../results/pilot_b/SUMMARY.md), [original 4B](../results/pilot_original/qwen3-4b/RESULTS.md), [original 8B](../results/pilot_original/qwen3-8b/RESULTS.md).

Equal aggregate accuracy is not itemwise identity: Pilot-B E/C discordances are 3/3 for Qwen3-4B and 1/1 for Qwen3-8B. No equivalence margin/test was established. The original cohort's zero empirical E/C bootstrap width at ceiling does not prove population equality. Keep the two cohorts separate: their C definitions, authoring and review processes differ. Under D037, the original cohort has two independent human **solvers**, but language review by R02 plus A01; R01's unverified AI-prefill judgments cannot support human-review or agreement claims.

All E/R/C conditions use Latin script, so the study does not identify a causal romanization penalty relative to Devanagari. R/C also differ in vocabulary and register. “R is the lowest-scoring form here” is supported; a universal statement about small LLMs or a mechanism is not. A nonsignificant or sparse lexical-stratum comparison does not refute every vocabulary mechanism.

## Verified comparison matrix

“No” below means no matched monolingual-R versus C condition reported in the inspected material, not proof that no related artifact exists. **Supports** concerns direction or methodological rationale, not direct replication; **contradicts** is explicitly qualified when populations/protocols differ. Citation details and primary locators follow the matrix.

| ID | What was measured | Matched R vs C? | Relation to our claim and action |
|---|---|---|---|
| S1 CodeMixTax | Same GSM8K and MMLU questions in E, native Hindi, mixed-script Hinglish, Romanized Hinglish and Romanized Hindi; 16 models. | **Yes.** 955 paired maths questions per form. | **Supports + directly overlaps.** R below Romanized C already reported. Qwen absent from the displayed model list. Must acknowledge as direct precedent, despite being an author report rather than a peer-reviewed paper. |
| S2 Indi-RomCoM | Seven tasks including GSM8K; four Indic languages; English and 25/50/75% mixing conditions, including Romanization. | **No separate monolingual-R endpoint found.** Mixing intensities are not an R baseline. | **Overlaps.** Roman-script code-mixed math evaluation and small-model comparisons already exist. Its same-register output instruction differs from our English-output policy. |
| S3 CodeMixBench | Eight tasks across 18 languages, including synthetic Hindi–English CM-GSM8K versus English. | **No.** Hindi–English examples use mixed Devanagari/Latin scripts. | **Overlaps; contradicts a universal C≈E claim**, not our checkpoint/cohort-specific observation. Retain citation and distinguish script/register. |
| S4 Mind the Gap | MGSM translation/ambiguity audit and alternative answer extraction, with corrected MGSM-Rev2. | **No.** MGSM is not an R/C Hindi experiment. | **Overlaps + supports measurement caution.** Most apparent language gaps can disappear after repairs; our format-confound contribution must explicitly build on it. Highest-priority missing citation. |
| S5 TeluguEval | English/Telugu reasoning across GSM8K, ARC, Winogrande, law and ethics; includes Romanized Telugu probes and output failures. | **No.** Native/Romanized Telugu is not Hindi R/C. | **Supports analogous difficulty; overlaps** Indic script-sensitive reasoning and repetition/answer failures. Add as recent Indic precedent. |
| S6 Scaling Synthetic Pre-training Data and Evaluation for Indic LLMs | Indic synthetic pretraining and evaluation suite; native/romanized resources; Romanized Malayalam GSM8K recipe comparison; benchmark-aware quality controls. | **No matched Hindi R/C condition located.** | **Overlaps** Romanized Indic reasoning and human-in-the-loop quality assurance. New 19 October preprint; important freshness addition, not evidence for our R/C ordering. |
| S7 IRIS | Curriculum SFT/RL with step-level CL-Math in English, Hindi and Marathi; multilingual and bilingual training. | **No R/C condition located** in paper/setup. | **Neutral to R<C; overlaps** Hindi math resources/training. “Bilingual” training must not be misreported as code-mixed input comparison. |
| S8 Script Gap | Real-world healthcare triage in native versus Romanized Indian-language messages; selective routing. | **No C arm.** | **Supports adjacent script vulnerability; neutral** on matched math R/C. Update existing preprint citation to the verified 2026 industry paper. |
| S9 Why Do Multilingual Reasoning Gaps Emerge? | Reasoning-stage interventions and selective translation, including Qwen3-4B, PolyMath and MMLU-ProX-Lite. | **No matched Hindi R/C comparison found.** | **Supports an understanding hypothesis, not our mechanism.** Its interventions are stronger evidence about its setting than our observational lexical strata. Cite if discussing causes/translation. |
| S10 MathIF | Mathematical correctness alongside instruction adherence, including verifiable format/language constraints. | **No.** | **Overlaps** separating solving from compliance; supports reporting both. Not a replication of our frozen FINAL/unit scorer. |
| S11 Recovered in Translation | Automated benchmark translation/refinement for eight European languages, evaluated using reference metrics and model judges. | **No.** | **Overlaps** LLM benchmark construction and semantic-quality checks. Automated judging is not a substitute for our disclosed human review. |
| S12 mmPISA-bench | 25 reasoning questions in 43 official human translations plus machine translations, two proprietary models; accuracy and token cost. | **No Hindi R/C manipulation.** | **Neutral** on R<C; challenges a blanket claim that machine translation necessarily damages evaluation. Optional balancing citation. |
| S13 Bridging the Culture Gap | LLM localization of math names, organizations and currencies; robustness comparisons and human verification. | **No R/C arm.** | **Overlaps** AI-assisted multilingual math construction and meaning-preserving perturbations. Useful data-quality citation; local names alone are not a novel resource method. |
| S14 Large Reasoning Models Struggle to Transfer Parametric Knowledge Across Scripts | Cross-script factual transfer on ECLeKTic/MultiLoKo, entity hints and post-training interventions. | **No math R/C comparison.** | **Supports adjacent script sensitivity; neutral** on our fixed-Latin-script comparison. Optional, not a causal explanation of our results. |
| S15 Sarvam-M | Native and Romanized Indic GSM8K evaluation/training in an author model report. | **No matched monolingual-R/C arm found.** | **Supports older Romanized-math precedent.** Retain existing citation; outside the main 12-month window. |

## Full citations, verification and exact locators

### S1 — direct headline precedent; already cited

Sthānika. 2026. **The code-mixing tax on romanized Hindi, measured.** Author research report, dated 9 September 2026. [Primary report](https://sthanika.ai/research/codemix-tax-2026); [author repository](https://github.com/sthanika-ai/CodeMixTax).

Verified: five-form definition; §5 maths table; appendix “Where each form came from” and translation-quality limitations. Example E/C-ROM/R: Gemma-3-4B 90.26/66.18/40.63; Llama-3.1-8B 88.27/55.81/36.75. The C counterpart is **Romanized Hinglish**, not the report's mixed-script “Hinglish” column. The report acknowledges semantic translation drift. Repository extraction/retry policies differ from ours. No independent rerun or peer-review status is claimed. Existing key `sthanika-2026-codemix` can remain.

### S2 — Romanized code-mixed math; already cited

Avisha Das, Mihir Parmar, Mohana Ramnath, and Pulkit Verma. 2026. **Indi-RomCoM: Code-Mixed Benchmark for Evaluating LLMs on Romanized Indic-English Instructions.** arXiv:2606.30790v1, submitted 29 June. [Primary record](https://arxiv.org/abs/2606.30790); [full text](https://arxiv.org/html/2606.30790v1).

Verified: §§3.1–3.3, §4, Appendix C.2. Conditions explicitly list English and three CM levels; C.2 asks output in the input language/script. Do not convert the highest mixing level into a pure-R control. Retain `das-etal-2026-indiromcom` as a preprint; no newer proceedings version verified here.

### S3 — mixed-script GSM8K; already cited

Yilun Yang and Yekun Chai. 2025. **CodeMixBench: Evaluating Code-Mixing Capabilities of LLMs Across 18 Languages.** Proceedings of EMNLP 2025, pp. 2139–2169. ACL. DOI: 10.18653/v1/2025.emnlp-main.109. [Primary record](https://aclanthology.org/2025.emnlp-main.109/); [paper](https://aclanthology.org/2025.emnlp-main.109.pdf).

Verified: §§3–4, mathematical-reasoning comparison/Table 2 and dataset examples. Its synthetic construction already combines word substitution and GPT prompting. Retain `yang-chai-2025-codemixbench`; do not characterize it as only code generation or as a pure Latin-script R/C experiment.

### S4 — essential missing measurement reference

Jan-Thorsten Peter, David Vilar, Tobias Domhan, Dan Malkin, and Markus Freitag. 2026. **Mind the Gap... or Not? How Translation Errors and Evaluation Details Skew Multilingual Results.** Proceedings of the Fifth Workshop on Generation, Evaluation and Metrics (GEM), pp. 191–204. ACL. DOI: 10.18653/v1/2026.gem-main.22. [Primary proceedings record](https://aclanthology.org/2026.gem-main.22/); [arXiv v2](https://arxiv.org/html/2511.05162v2).

First arXiv version 7 November 2025; v2 22 June 2026. Verified §§5.1–5.3 (translation, ambiguous source questions, extraction including Bengali numerals), §6 and Appendix C. Their repair-based analysis does not license changing our frozen endpoints after seeing results. Cite as methodological predecessor, not as proof that our specific R deficit is spurious.

### S5 — recent Indic math/script comparison

Revanth Kumar Gundam and Radhika Mamidi. 2026. **TeluguEval: A Comprehensive Benchmark for Evaluating LLM Capabilities in Telugu.** Proceedings of the Second Workshop on Language Models for Low-Resource Languages (LoResLM 2026), pp. 212–224. ACL. DOI: 10.18653/v1/2026.loreslm-1.20. [Primary record](https://aclanthology.org/2026.loreslm-1.20/); [paper](https://aclanthology.org/2026.loreslm-1.20.pdf).

Verified abstract, Table 1, §6.2 maths and §6.3 science discussion. Includes failure to produce numerical answers on Romanized input. These findings are analogous, not evidence about the relative difficulty of Hindi R and C.

### S6 — newest directly relevant addition

Abhinav Khattar, Aishwarya Chhabra, Ameya Velingker, Anusha Kamath, Brandon Norick, Kanishk Singla, Kiran Praveen, Markus Kliegl, Mohammad Qazim Bhat, Mostofa Patwary, Niket Agarwal, Rajpreet Thethy, Ramani Akkati, Raviraj Joshi, Sai Nishanth Padala, Shuoyang Ding, Sriharsha Niverty, Utkarsh Vaidya, Vitaly Lavrukhin, Yev Meyer, Anoop Kunchukuttan, Mitesh Khapra, Mohammed Safi Ur Rahman Khan, Rudra Murthy, Sumanth Doddapaneni, Thanmay Jayakumar, and Ujjwal Sharma. 2026. **Scaling Synthetic Pre-training Data and Evaluation for Indic LLMs.** arXiv:2610.26006v1, submitted 19 October. [Primary record](https://arxiv.org/abs/2610.26006); [full text](https://arxiv.org/html/2610.26006v1).

Verified author list; §4.4 Romanization; §5.4.4/Table 5.6 Romanized Malayalam evaluation; §§6.1–6.4 benchmark-aware translation, correction and human checks. The authors explicitly qualify the recipe comparison as not isolating script alone. Do not cite the Romanized Malayalam experiment as a Hindi/Hinglish comparison.

### S7 — Hindi math resource/training update

Navya Gupta, Rishitej Reddy Vyalla, Avinash Anand, Chhavi Kirtani, Erik Cambria, Zhengchen Zhang, Zhengkui Wang, Timothy Liu, Aik Beng Ng, Simon See, and Rajiv Ratn Shah. 2026. **IRIS: Interleaved Reinforcement with Incremental Staged Curriculum for Cross-Lingual Mathematical Reasoning.** Proceedings of ACL 2026, Volume 1: Long Papers, pp. 22216–22248. ACL. DOI: 10.18653/v1/2026.acl-long.1017. [Primary record](https://aclanthology.org/2026.acl-long.1017/); [paper](https://aclanthology.org/2026.acl-long.1017.pdf).

Verified abstract, introduction and CL-Math/training setup. No Romanized condition located in the inspected paper. Relevant to the broader Hindi-math paragraph; optional for a short paper centered on evaluation rather than training.

### S8 — update existing preprint citation

Manurag Khullar, Utkarsh Desai, Poorva Malviya, Aman Dalmia, and Zheyuan Ryan Shi. 2026. **Script Gap: Evaluating LLM Triage on Indian Languages in Native vs Romanized Scripts in a Real-World Setting.** Proceedings of EMNLP 2026: Industry Track, pp. 2414–2429. ACL. [Primary record](https://aclanthology.org/2026.emnlp-industry.144/).

Verified proceedings metadata and abstract. This supersedes the manuscript's “preprint” label for `khullar-etal-2025-script`; supplied new key `khullar-etal-2026-script`. No DOI was displayed, so none is invented. Native/Romanized clinical comparison does not establish C/E equivalence or a math mechanism.

### S9 — understanding versus reasoning

Deokhyung Kang, Seonjeong Hwang, Daehui Kim, Hyounghun Kim, and Gary Lee. 2026. **Why Do Multilingual Reasoning Gaps Emerge in Reasoning Language Models?** Findings of ACL 2026, pp. 31684–31716. ACL. DOI: 10.18653/v1/2026.findings-acl.1586. [Primary record](https://aclanthology.org/2026.findings-acl.1586/); [arXiv](https://arxiv.org/abs/2510.27269); [OpenReview paper](https://openreview.net/pdf/ad62adf2177bd5916cb337fb9f1b2eea25f15192.pdf).

Verified proceedings metadata, abstract and evaluation Appendix D.2. Uses a model-assisted fallback after regex extraction; our numeric scorer must not be equated with this protocol. Use proceedings author name “Gary Lee”; the arXiv record uses “Gary Geunbae Lee.” Mechanistic results belong to their intervention setting, not ours.

### S10 — mathematical instruction-following

Tingchen Fu, Yafu Li, Jiawei Gu, Xiaoye Qu, and Yu Cheng. 2026. **Scaling Reasoning, Losing Control: Evaluating Instruction Following in Large Reasoning Models.** Proceedings of ACL 2026, Volume 1: Long Papers, pp. 40445–40463. ACL. DOI: 10.18653/v1/2026.acl-long.1878. [Primary record](https://aclanthology.org/2026.acl-long.1878/); [paper](https://aclanthology.org/2026.acl-long.1878.pdf).

Verified proceedings author order and MathIF description; §3 and Table 10. First preprint is May 2025, outside the main window, but this proceedings version is July 2026. Do not copy the older arXiv author order into the proceedings entry. Citation supports compliance/accuracy separation; it does not establish our form-dependent failure rates.

### S11 — synthetic benchmark quality

Hanna Yukhymenko, Anton Alexandrov, and Martin Vechev. 2026. **Recovered in Translation: Efficient Pipeline for Automated Translation of Benchmarks and Datasets.** arXiv:2602.22207v1, 25 February. [Primary record](https://arxiv.org/abs/2602.22207); [full text](https://arxiv.org/html/2602.22207v1).

Verified §§1, 3 and 4.2: benchmark-structure preservation, candidate refinement/ranking and translation-quality evaluation. This concerns translation of existing benchmarks, not newly authored Hindi mathematical families. Label as preprint; acceptance elsewhere was not verified.

### S12 — balancing evidence about machine translation

Yerzhan Sapenov and Jaromir Savelka. 2026. **mmPISA-bench: Do LLMs Reason Equally Well Across 43 Languages?** Proceedings of the 1st Workshop on Multilinguality in the Era of Large Language Models (MeLLM 2026), pp. 170–180. ACL. DOI: 10.18653/v1/2026.mellm-1.16. [Primary record](https://aclanthology.org/2026.mellm-1.16/); [arXiv](https://arxiv.org/abs/2606.07069).

Verified metadata and abstract-level design/results. Evidence is limited to their small multiple-choice benchmark and tested systems. It neither validates our AI drafts nor supports dismissing synthetic resources categorically.

### S13 — LLM-assisted multilingual math quality

Israel Abebe Azime, Tadesse Destaw Belay, Dietrich Klakow, Philipp Slusallek, and Anshuman Chhabra. 2026. **Bridging the Culture Gap: A Framework for LLM-Driven Socio-Cultural Localization of Math Word Problems in Low-Resource Languages.** Findings of ACL 2026, pp. 855–870. ACL. DOI: 10.18653/v1/2026.findings-acl.42. [Primary record](https://aclanthology.org/2026.findings-acl.42/); [paper](https://aclanthology.org/2026.findings-acl.42.pdf).

Verified introduction and Table 1: automatic localization plus full human test-set verification and sampled training verification. The distinction between numerical gold, semantic preservation and culturally natural language matters for our own resource claims. Not a matched Hindi R/C study.

### S14 — optional cross-script reasoning background

Lucas Bandarkar, Alan Ansell, and Trevor Cohn. 2026. **Large Reasoning Models Struggle to Transfer Parametric Knowledge Across Scripts.** Findings of EMNLP 2026, pp. 29519–29529. ACL. [Primary record](https://aclanthology.org/2026.findings-emnlp.1387/).

Verified metadata and abstract: script-match analysis, source-language entity hints and post-training. No DOI displayed. Its cross-script knowledge-transfer claim cannot be imported into our comparison, where R and C share a script. Optional background rather than essential short-paper citation.

### S15 — older indispensable precedent; already cited

Sarvam AI. 2025. **Sarvam-M.** Author technical blog report, 23 May 2025. [Primary report](https://www.sarvam.ai/blogs/sarvam-m).

Verified mathematics training/evaluation discussion and Indic Romanized GSM8K reporting. Explicitly predates the main search window. Retain `sarvam-2025-sarvamm`; this is not a peer-reviewed paper or a controlled R/C comparison.

## Submission-facing changes recommended to Claude

1. **Position as an audit/extension.** S1 has the direct R/C design; S4 already establishes multilingual math measurement confounds. Our contribution is the combined, transparent application to newly drafted matched families under a frozen small-model protocol, with explicit limits—not either idea in isolation.
2. **Replace equivalence language.** “Equal observed aggregate strict accuracy” is justified; “as easy as English,” “mixing does not hurt,” and C≈E without qualification imply more than the data show. Llama's substantial E/C deficit must be in the same discussion, not relegated to a footnote.
3. **Separate endpoint agreement from validity.** The manuscript says identical strict/numeric Llama scores mean its gaps “are not formatting artifacts.” Both endpoints can reject the same malformed/truncated response, so that inference is invalid. Report endpoint agreement and invalid/truncation counts, and await independent manual audit. Qwen's trailing-rupee grammar issue and alias failures also preclude describing the numeric endpoint as a definitive semantic oracle. Do not alter either frozen endpoint to improve the story.
4. **Respect current review provenance.** Replace old two-reviewer-language-validation implications using D037. Do not describe the 24-family cohort as all 30 accepted, pool it with Pilot-B, or treat the original cohort as untouched confirmation of a hypothesis selected without seeing Pilot-B.
5. **Keep developmental evidence separate.** The 10/36→0/36 comparison also changes fixtures/aliases; it is not an isolated causal prompt effect. The paper already discloses this later, but its abstract should not undo that qualification. Independent gold computation and two LLM solves do not certify naturalness, independence or freedom from shared drafting bias.
6. **Citations by priority.** Add S4 first; retain and explicitly discuss S1–S3; add S5 and S6 for current Indic coverage, S13 for AI-assisted math construction, S10 for compliance. Update S8's venue/year. S7/S9/S11/S12/S14 are verified optional additions depending on available space and claims. Do not add every reference merely to enlarge the bibliography.

The companion BibTeX file contains 11 verified new/replacement entries (S4–S14), with primary-source URLs and access-date comments. Existing S1/S2/S3/S15 keys are intentionally not duplicated. Proposed integration only; neither manuscript nor existing bibliography was modified.

## Search record, coverage and limitations

Actual search date: 26 October 2026. Search stopped after direct-precedent, extraction, Indic-script and benchmark-quality categories all had primary-source coverage, followed by a final recent-date pass and verification of the October 19 addition. This was targeted retrieval and one-hop follow-up, not a systematic review or exhaustive citation graph traversal.

Representative executed query groups:

- `"Romanized" "math" "2026" Hindi`; `"code-mixed" "Romanized" "reasoning" benchmark`; `"Hinglish" "GSM8K" after:2025-10-25 before:2026-10-27`; `"Romanized Hindi" "math" after:2026-09-01 before:2026-10-27`.
- `site:aclanthology.org 2026 romanized Hindi reasoning math`; `site:arxiv.org "Hinglish" "2026" benchmark math`; `site:openreview.net "Hindi" "romanized" math`.
- `site:arxiv.org multilingual math "extraction" evaluation`; `site:openreview.net "answer extraction" "multilingual" math`; exact-title follow-up for Peter, Kang and MathIF.
- `site:aclanthology.org "synthetic" "benchmark" "quality" "2026" multilingual`; `site:arxiv.org "synthetic" "multilingual" "benchmark quality"`; `site:openreview.net multilingual benchmark synthetic translation quality 2026`.
- `site:semanticscholar.org Hinglish math romanized benchmark`; `site:semanticscholar.org "Romanized" "mathematical"`; exact-title queries for Indi-RomCoM and Mind the Gap. These did not provide usable additional records; the arXiv-linked Semantic Scholar lookup also failed. **Semantic Scholar coverage is incomplete**, and it is an index, not a substitute for the primary paper.

ACL/arXiv metadata and full text were used for the substantive matrix. OpenReview searches yielded relevant PDFs, including S9, and an additional lead below. Publication dates come from paper metadata/history, not search-engine “months ago” labels. Newly indexed proceedings were cited only when primary metadata was available by the actual cutoff. No search or event on 27 October is claimed.

**UNVERIFIED lead, excluded from BibTeX and novelty verdict:** “Gold vs. Translation: Are We Measuring Language, Knowledge, or Locality in Translated Benchmarks?”, [OpenReview submission 2SI74SsSSq](https://openreview.net/forum?id=2SI74SsSSq). Search indexing displayed an anonymous ARR March 2026 submission, but direct retrieval hit a browser-verification page. Authorship, complete version and publication status were not verified; no author or venue is inferred. Broadly unrelated dialogue, speech, safety and RAG papers were screened out rather than padded into the matrix.

The novelty conclusion is therefore bounded: **a verified direct precedent exists, while the exact Qwen/cohort/protocol combination was not found**. Absence from this search is not evidence that no other paper exists. We did not reproduce external results or audit their complete released datasets.

## Write-scope verification and handoff

Only the two requested refresh files and the explicitly requested [handoff note](../handoffs/2026-10-27_astra_to_claude.md) were created. The 27 October names are retained as requested. No inference, installation, commit, push or branch change occurred. Pre-existing `paper/latex/PATCH_original_cohort.md` was left untouched.

Manuscript input SHA-256: `8808034583e98f59df5827a4cfbe162096dcf72aa28c3c5fa2b3147a00586b00`.
Existing bibliography input SHA-256: `67fa5f3121bdee4243e8934ce6df4fc6b2fd572493d6b282d047419596e8d063`.

Next action: Claude should review the proposed positioning, integrate selected verified citations, reconcile D037/results text, and finish the scoring/language audit before treating the submission as ready. No additional experiment or reviewer approval is inferred from this literature refresh.
