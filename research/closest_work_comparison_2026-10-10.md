# Closest-work comparison and publication decision

Audit date: 10 October 2026. Research only; no experiments conducted.

## Decision

No exact E+C versus E+R matched mathematical training comparison was located in the inspected sources. This supports proceeding with a narrowly framed empirical study, but does not establish a worldwide first or guarantee publication. The strongest overlap comes from Indi-RomCoM for the application and XCOT for the intervention. Code mixing, bilingual maths training, matched multilingual evaluation, and English reasoning targets each have precedents.

Recommended framing: **Does Code-Mixed Training Add Value Beyond Romanized Hindi for Mathematical Reasoning?**

Treat this as a controlled empirical question about training-data choice. A new model name or a different backbone is not the contribution.

## What qualifies as our exact control?

E = English input; R = predominantly Hindi in Roman script under a borrowing policy; C = Hindi-English code-mixed input in Roman script; H = Hindi in Devanagari.

An exact training comparison must include all of the following:

1. Two separately trained copies of the same initial checkpoint: E+R and E+C.
2. The same underlying mathematical families and the same English examples in both arms.
3. Identical English solution completions for every matched family, not merely identical final numerical answers.
4. The same language-mixture proportions, family exposure, update schedule, adapter settings, checkpoint-selection rule, and paired training seeds.
5. Evaluation of both arms on the same held-out C families, with all translations, paraphrases, and numerical siblings kept within their assigned split.

Token counts need not be identical merely because examples are matched. Report them and compute costs; describe the estimand as the effect of these training renderings under matched exposure, not a pure causal effect of switching independent of vocabulary and length.

## Matrix A: substantive overlap

“Not located” means not reported in the inspected material, not proof that no unpublished or uninspected experiment exists. Locators refer to the linked versions.

| Work and evidence | Task/data and actual comparison | Supervision/script relevance | Exact E+C versus E+R? | Consequence for our paper |
| --- | --- | --- | --- | --- |
| [Anand et al., Multilingual Mathematical Reasoning](https://arxiv.org/html/2412.18415v1), sections “Curriculum Learning based Fine-Tuning” and “Bilingual Combined Training”; Tables 2–4 | IndiMathQA, GSM8K/MATH-related training; separate English/Hindi training versus combined bilingual curriculum training | Parallel English/Hindi question-answer pairs; structured solutions and translations. No R-versus-C training arm located | **Not located** | Bilingual mathematical adaptation and paired content are prior art; our comparison must concern the incremental value of C over R |
| [Indi-RomCoM v1](https://arxiv.org/html/2606.30790v1), Appendix C.1, D.2, Table 14 | Seven tasks including GSM8K; Romanized code-mixed fine-tuning compared with untuned models | Multiple Indic languages and mixing levels; Table 14 describes Romanized CM instruction pairs, not a shared-English-target R control | **Not located** | Closest application overlap; “Hinglish fine-tuning improves maths” is insufficient differentiation |
| [CodeMixBench](https://aclanthology.org/2025.emnlp-main.109.pdf), experimental setup and Table 2 | CM-GSM8K and other tasks; model and prompting comparisons, including existing base/instruct checkpoints | Hindi-English mixed inputs; comparison of pre-existing checkpoints is not a controlled R-versus-C training intervention | **Not located** | Neither code-mixed maths evaluation nor base-versus-instruct improvement is our novelty |
| [CodeMixTax](https://github.com/sthanika-ai/CodeMixTax), “five language forms” and reproduction sections; [author report](https://sthanika.ai/research/codemix-tax-2026) | Paired inference on English, native Hindi, mixed-script Hinglish, Romanized Hindi and Romanized Hinglish; GSM8K/MMLU | Changes evaluation input form; no separate controlled training arms described | **Not located; inference study** | E/R/C evaluation alone overlaps. The report also acknowledges romanization quality limitations; our human-reviewed spelling evaluation must be explicit |
| [XCOT, AAAI 2025](https://ojs.aaai.org/index.php/AAAI/article/download/34524/36679), xICL section, experiments, Tables 4 and 6 | Multilingual mathematical instruction tuning; module ablations and English/native/code-switched context comparisons | Code switching in contextual examples, with cross-lingual reasoning/distillation components; no Hindi R-versus-C arm located | **Not located** | Strong methodological overlap: do not claim code-switched training for mathematical transfer is new |
| [LinguaLIFT](https://arxiv.org/html/2412.12499), §§3.1–3.2, 6.1–6.8 | Code-switched translation alignment followed by English task instruction tuning; stage/module/ratio ablations | English translation targets in alignment stage, a multilingual encoder and alignment layer; not matched R/C mathematical SFT arms | **Not located** | Code-switched inputs plus English supervision are already explored; our value must be the controlled scientific comparison |
| [MathOctopus, Findings EMNLP 2024](https://aclanthology.org/2024.findings-emnlp.411.pdf), training strategies, Tables 4–7, Appendix D.2 | GSM8K-derived multilingual training; parallel, cross, and mixture strategies; MGSM/MSVAMP evaluation | Parallel = same-language question/answer; cross = English question with another-language answer. Its “mix” denotes combinations of training pairs, not necessarily within-question code mixing | **Not located** | Matching translated mathematical content and studying training-language composition are established methods |
| [Nanda Family, EACL 2026](https://aclanthology.org/2026.eacl-long.288.pdf), §§2–4, Table 3 | Broad bilingual pretraining and instruction tuning; model evaluations | Training covers native-script, Romanized and code-mixed Hindi; no separate matched mathematical R/C intervention located | **Not located** | Exposure to both Romanized Hindi and Hinglish is not a new model capability claim |

## Matrix B: what is verified versus unresolved

| Work | Artifact depth in this audit | Split / output / exposure issue relevant to an exact match |
| --- | --- | --- |
| Anand et al. | Paper sections, repository listing and training-file page | Bilingual pairs are documented. Identical English completions across R/C arms and a family-level R/C split manifest were not located. Technical appendix link was found, but its PDF content could not be retrieved in this audit |
| Indi-RomCoM | HTML and PDF text | C.1 describes 80% training across three intensities; Table 14 describes 90/10 at 50% CM. These require reconciliation. Family-grouped splitting and an R-only training comparator were not located |
| CodeMixBench | Paper experiment and appendix material; official dataset card | Existing checkpoint/prompt comparisons do not establish equal training exposure. Its GSM8K-derived test material should not become our training data |
| CodeMixTax | Repository README and author report | Aligned inference families are documented. Repository states raw runs/results are not committed; no independent reproduction performed here |
| XCOT | Paper methods and ablation descriptions/tables | Context-switching and additional training components differ from our direct input-form comparison. Identical English-only completions for matched Hindi R/C arms were not located |
| LinguaLIFT | HTML methods and ablations | Alignment and task training are different stages/objectives. No family-matched Hindi R/C contrast located |
| MathOctopus | Paper training settings and appendix | Explicit question/answer language variation differs from our fixed completion language. “Mix-All” also changes data volume |
| Nanda | Official proceedings paper, instruction-data and evaluation descriptions | A combined corpus containing R and C does not isolate their respective effects; an R/C mathematical intervention is not reported in inspected sections |

The discrepancy also appears in PDF text (pages 18 and 21); screenshots failed. No project-specific training repository was located. Implementation details remain unresolved; this is not evidence of leakage or invalidity.

## Additional screening

- [mCoT, ACL 2024](https://aclanthology.org/2024.acl-long.649/) and its [author repository](https://github.com/laihuiyuan/mCoT): multilingual mathematical instruction tuning and consistency are established. Screened at abstract/repository level; not a full appendix audit.
- [MathMist, Findings EACL 2026](https://aclanthology.org/2026.findings-eacl.131.pdf): parallel mathematical evaluation and code-switching reasoning prompts; limitations describe frozen-model prompting and identify fine-tuning as future work. Relevant evaluation precedent, not an exact training match.
- [AdaMame](https://arxiv.org/abs/2606.15080): abstract describes multilingual SFT/RL targeting reasoning-language fidelity. Adjacent output-language work; full control audit not performed.
- [Korean self-correction study](https://arxiv.org/abs/2601.05459): abstract describes code-switching data and reasoning alignment. Adjacent methodological precedent; not evidence of a Hindi R/C control.
- [Hinglish-Assistant](https://github.com/Muskan910/hinglish-assistant): public conversational QLoRA project. Application overlap does not establish mathematical matched-control overlap.

Screened sources are not counted as fully audited negative results.

## Publication assessment: the main risk is incremental value

The absence of an exact match is necessary evidence for our chosen framing, but is not sufficient evidence of a strong contribution. A reviewer could reasonably say that training on the target input distribution should help. A comparison on synthetic test text produced by the same generator/style as training would leave that objection largely unanswered.

Strengthen the study around **transfer and specificity**:

- Evaluate both E+R and E+C on E, R and C, not only C. If each arm mainly helps its own register, report specialization rather than universal reasoning improvement.
- Reserve independently authored/reviewed C phrasings and spelling variants from training. Group uncertainty by underlying family. A variant does not create a new independent mathematical example.
- Include an exposure-matched English-only arm (E+E). It tests whether extra mathematical practice can explain improvements over an unchanged checkpoint.
- Include translate-to-English-then-solve as a practical baseline with both stages' cost and translation errors recorded. Do not give this baseline the human reference E text as if it had translated C itself.
- Seek a second-backbone training replication if the measured budget permits. Multiple unchanged-model baselines do not establish that a training effect generalizes across models.
- Keep human acceptance of mathematical equivalence and naturalness independent of model success. Freeze items before generation and preserve rejected items as development exclusions.

Do not inflate scope solely to accumulate conditions. The essential trained arms are E+E, E+R, E+C; a native-script E+H arm is useful only if script-level training claims become central. E/R/C alone cannot identify the effect of romanization relative to Devanagari.

## Concrete contrast and interpretation

For family i, let c(i, arm, form) be numeric-answer correctness. The primary effect is the family-averaged difference:

    Delta_C = Accuracy(E+C training, C test) - Accuracy(E+R training, C test)

Prespecify seed aggregation, uncertainty and the practically meaningful threshold before confirmatory runs. Report absolute accuracies alongside differences.

A useful secondary contrast is:

    Specificity = Delta_C - Delta_R

where Delta_R compares the same trained arms on R test items. This measures relative specialization across the two test forms; it does not prove an internal language-understanding mechanism. Preserve the paired-family structure when estimating uncertainty.

| Possible finding | Defensible interpretation |
| --- | --- |
| C advantage survives independent phrasings/spellings and replication | Evidence for transferable value of C training under the tested recipe |
| C advantage only on familiar generation style | Distribution-specific adaptation; inadequate support for broad robustness |
| R training performs similarly, with a sufficiently narrow interval relative to a prespecified margin | Potential evidence that C-specific data offer limited extra value in this setting; formal equivalence needs its own prespecified test |
| Wide interval around zero | Inconclusive; not proof that R and C training are equivalent |
| Translation baseline is competitive at acceptable cost | A useful practical result; contextualize whether adaptation is worth its data/training expense |
| C improves while English worsens materially | A measurable tradeoff, not an unqualified improvement |

## Claims we can and cannot write now

Safe proposal wording:

> We propose a controlled comparison of code-mixed and Romanized-Hindi mathematical adaptation with matched problem families and English solution supervision. The study will measure transfer to independent Hinglish renderings and retention on English and Romanized Hindi. Our targeted review did not locate this exact comparison in the inspected literature.

Do not write: first Hinglish maths model; first use of code mixing for reasoning; first matched multilingual mathematics evaluation; code mixing inherently harms reasoning; or our method improves performance. None is established by this audit.

For the eventual paper, replace proposal language with the actual protocol and results, and repeat the novelty search near submission. Publication suitability depends on the evidence and execution; a control combination alone does not justify a venue claim.

## Search record and remaining uncertainty

Primary sources were prioritized: ACL Anthology, AAAI proceedings, arXiv manuscripts, author repositories and reports. Discovery included exact-title searches and the following query families:

- Hinglish + Romanized Hindi + fine tuning + math
- code-mixed / code-switched + mathematical reasoning + training
- Romanized Hindi + ablation / matched / control
- Indi-RomCoM + GitHub / dataset / training
- multilingual mathematics + parallel / cross-lingual instruction tuning

Backward follow-up expanded the audit to XCOT, LinguaLIFT, MathOctopus and Nanda. Sentiment, speech recognition, unrelated code-generation benchmarks, education courses, and secondary summaries were excluded as evidence for the exact mathematical training control.

This is a targeted literature audit, not a systematic review with complete database coverage. Some full implementation artifacts were unavailable, and no third-party runs were reproduced. “Not located” must remain the conclusion until stronger evidence supports an absence claim.

## Recommendation for the next research milestone

Proceed with this question provisionally. Before implementation, finalize a one-page experiment specification: three trained arms; exact matching rules; independent-style test construction; primary and secondary contrasts; annotation capacity; and resource-dependent replication. Set an explicit smallest useful gain and English-retention tolerance, then plan sample size around them rather than selecting a convenient small final-test set.

The closest-work comparison has enough evidence to refine the question. The unresolved artifact details should remain documented limitations; they do not justify indefinitely postponing a carefully scoped pilot.
