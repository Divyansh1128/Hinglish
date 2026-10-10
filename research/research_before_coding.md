# Research before coding: continuation and decision gates

Date: 10 October 2026. Planning only; no new code, dataset, inference, or training.

Follow-up: [Closest-work comparison and publication decision](closest_work_comparison_2026-10-10.md) audits the core training controls, extends the comparison to XCOT, LinguaLIFT, MathOctopus and Nanda, and records remaining evidence gaps. Its narrower novelty assessment supersedes the preliminary closest-work check below.

## Recovered project status

The 8 October model-selection plan proposes Qwen3-4B as the primary training candidate, with several other families for unchanged-model evaluation. The pilot packet specifies 30 independent E/R/C evaluation families and 16 separate hardware-test families. E = English; R = Romanized Hindi; C = Roman-script Hinglish. Existing scorer and protocol-validation code are preparatory software, not experimental evidence. The latest local documents record human review, inference, and GPU feasibility as pending. This continuation does not independently establish that no work occurred elsewhere.

## Recommendation

Complete a bounded literature review and an implementation-ready protocol first. Then use a minimal pilot to resolve empirical uncertainties before committing to full implementation and training. Research includes experiments: reading cannot establish GPU fit, attainable accuracy, annotation quality, runtime, or statistical power under the eventual data distribution.

The pre-code phase is complete when every design-changing question below has a recorded decision or an explicit pilot decision rule. A growing bibliography alone is not a completion criterion.

## Closest-work check

1. [Anand et al., Multilingual Mathematical Reasoning](https://arxiv.org/html/2412.18415v1): Hindi/English mathematical evaluation and bilingual training are already studied. Bilingual math fine-tuning alone is insufficient differentiation.
2. [CodeMixBench, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.109/): broad code-mixed evaluation includes mathematics. A generic code-mixed math benchmark is insufficient differentiation. Do not confuse this paper with the separate code-generation paper bearing the same short name.
3. [Indi-RomCoM, v1](https://arxiv.org/html/2606.30790v1): includes Romanized Indic-English evaluation and fine-tuning ablations. Inspect Appendix C.1 and Table 14 before claiming a new training comparison. These sections describe differing split configurations; reconcile them with released artifacts before borrowing their recipe. This is an audit question, not proof of invalid experiments.
4. [CodeMixTax repository](https://github.com/sthanika-ai/CodeMixTax): describes five aligned language/script conditions, including Romanized Hindi and Romanized Hinglish. It states that raw runs/results are not committed. Treat headline findings as author-reported, not independently reproduced. A paired E/R/C diagnostic alone is not sufficient differentiation.

This is a targeted continuation, not an exhaustive novelty clearance or independent reproduction.

## Candidate directions

| Direction | Central question | Value | Limitation | Recommendation |
| --- | --- | --- | --- | --- |
| Controlled adaptation | Does E+C training outperform E+R on held-out C under matched mathematical supervision? | Tests a specific training decision with an explicit counterfactual | Requires GPU feasibility, reviewed data, and adequate independent families | Provisional primary direction |
| Translation-based inference | How well does translating C into E before solving compare with direct solving? | Establishes a practical alternative and exposes translation errors | Additional latency; broad novelty is weak without a sharper question | Required practical baseline if affordable; optional focused extension |

Candidate contribution: estimate the incremental benefit of code-mixed training over Romanized-Hindi training while matching families, English completion targets, example exposure, and training schedules, then test unseen families and reviewed spelling variants. Novelty remains provisional pending a full comparison of closest experimental controls.

## Finish before substantial coding

| Deliverable | Completion criterion |
| --- | --- |
| Literature comparison | For each closest paper: exact task, script, data origin, supervision, training comparator, split unit, output language, metrics, and remaining difference from our proposal; attach section/table references. |
| Research question | One primary estimand: held-out C accuracy difference between E+C and E+R. Document what each possible outcome would mean. |
| Language definition | Freeze borrowing policy and naturalness rubric. Specify English output targets. Do not equate English-word percentage with naturalness. |
| Data and licensing plan | Decide authoring/source strategy, permissions, provenance, independent bilingual review, adjudication, family boundaries, and permanent pilot/smoke exclusions. |
| Experiment matrix | Fix unchanged model, E+R, E+C, English-only matched-exposure control, and translation baseline roles. Make any omission conditional on a stated resource rule before final outcomes. |
| Evaluation specification | Freeze answer equivalence, units, invalid/truncated outputs, infrastructure failures, manual scoring audit, paired analysis, seed handling, and multiplicity policy. |
| Meaningful effects | Choose the smallest practically meaningful C gain and tolerable English loss based on project goals; justify sample size through sensitivity analysis and later pilot information. |
| Model policy | Recheck shortlist suitability and access before pinning revisions. Specify reasoning mode, output budget, quantization, and model-specific prompt wrappers. No model card establishes local training fit. |
| Feasibility protocol | Define bounded GPU tests, runtime budget, save/reload integrity checks, and go/revise/stop decisions. |

## Two design issues to resolve explicitly

E/R/C all use Roman script. They support comparisons among those input forms, but do not isolate the effect of romanization against native-script Hindi. If script-level claims are essential, add a reviewed Devanagari-Hindi diagnostic condition; otherwise limit the claim accordingly.

Matching examples and optimizer updates does not match input-token counts. Preserve identical supervised targets and family exposure for the primary comparison, record actual tokens and compute, and acknowledge that lexical/length differences are part of the intervention. Consider a token-budget sensitivity analysis only if resources permit; do not claim all factors are independently controlled.

## Staged execution after the review

1. Finish the comparison matrix, annotation rules, and experiment specification. Suggested planning budget: 5–7 focused working days, adjusted to availability.
2. Prepare and independently review pilot and smoke inputs under the existing packet. Annotation effort is a separate dependency, not assumed to fit that reading budget.
3. Implement only validation, inference, scoring reports, and the bounded hardware runner needed for feasibility. Preserve existing useful code.
4. Use the pilot to assess parsing, difficulty, naturalness, runtime, and floor/ceiling effects. Do not choose a direction solely because a 30-family accuracy gap is statistically significant.
5. Revise and freeze the confirmatory protocol, sample size, model choice, resource allocation, and untouched test procedure before full training and final evaluation.

## Immediate priorities

First complete the closest-work matrix, especially the exact training controls in Indi-RomCoM. Next settle data provenance and reviewer responsibilities. Then consolidate the protocol into one authoritative experiment specification, with unresolved hardware questions explicitly delegated to the future pilot.

No positive result, publication acceptance, or superiority of Hinglish training is assumed. A small or uncertain difference must be reported as such, rather than interpreted as equivalence.
