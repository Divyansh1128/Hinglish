# Updated closest-work and exact-control audit

Access date: 10 October 2026. Research audit only; no training, reproduction, accepted annotation or new model evaluation. Prepared from current primary sources and the existing project comparison. Earlier documents remain historical. UTC clock checked during this audit: 2026-10-10 08:26:09 UTC.

## Recommendation and verdict

Proceed provisionally with **“Does code-mixed mathematical adaptation add transferable value beyond Romanized Hindi under matched exposure and English solution supervision?”** The next gate is valid human review, an accepted/frozen dataset and the unchanged-model pilot. Do not begin full training or add many model conditions merely to compensate for an uncertain contribution.

**No exact E+R versus E+C comparison was located in the inspected material.** This is a bounded retrieval result, not proof of worldwide absence. There are strong partial precedents for every broad ingredient, including Romanized mathematical training and code-switched inputs with retained English responses. Publication value therefore depends on the controlled estimate, useful independent-style transfer, English retention and uncertainty, rather than being the first Hinglish maths model.

What changed in this audit:

- Recovered the official standalone Anand technical appendix, previously inaccessible locally; its exclusion of Romanized Hindi agrees with the paper's Appendix G.
- Made XCOT's retained English-response supervision explicit. That supervision is prior art.
- Added Sarvam-M as a concrete Romanized mathematical post-training precedent.
- Added the latest **Think Multilingual, Not Harder v3**, which directly trains alternative reasoning-output policies, including Hindi. It addresses a different intervention from our fixed-English-target input-form comparison.
- Upgraded mCoT, MathMist, AdaMame and the Korean self-correction study from abstract-level screening to targeted method/appendix inspection. This is still not an exhaustive code audit of every experiment.
- Could not reconcile Indi-RomCoM's two split/intensity descriptions with an attributable released training artifact. Keep that uncertainty open without accusing the study of leakage.

## Exact-match test and interpretation

E is English input, R is Hindi phrasing in Roman script under a frozen borrowing policy, and C is productive Hindi-English mixing in Roman script. A shared alphabet does not equate R with English, or isolated borrowed nouns with C.

The core comparator is separately trained E+R and E+C conditions from the same checkpoint, using matched mathematical content and constant complete English solution supervision, evaluated on common held-out C questions. Audit exposure/budget matching, family splits, adapters, checkpoint selection and paired seeds as separate validity/reporting dimensions. Missing paired seeds or an undocumented family ledger alone does not make an existing core comparison novel. No core comparator was located in the inspected methods; this conclusion is not based merely on failure to satisfy every preferred rigor criterion. Our essential E+E arm further controls additional mathematical exposure. Numerical siblings, translations and paraphrases must stay together in our splits.

Two evidence axes are kept separate below: **partial overlap** describes the intervention's relevance; **not reported** describes failure to locate the exact control. **Inaccessible/unclear** identifies a particular unresolved artifact/field. None implies that an unreported experiment never happened.

Matching example exposure does not equalize input tokens. Our eventual estimand is the effect of the complete R/C rendering policy under matched exposure; vocabulary, tokenization, lexical accessibility and length change together. It cannot identify a pure internal effect of switching independent of those properties. No E/R/C-only experiment identifies Romanization versus Devanagari.

## Matrix A: intervention, supervision and substantive overlap

The source key links to inspected primary versions and precise locators below. All rows are **partial overlap; exact control not reported in inspected material**, except where the extra artifact caveat is stated. Research-run claims remain author-reported and were not independently reproduced.

| Work | Task/data origin and script | Training or inference comparison | Full target / switching location | Remaining distinction |
| --- | --- | --- | --- | --- |
| [A: Anand](https://arxiv.org/html/2412.18415v1) | Hindi/English mathematics; IndiMathQA, HAWP and established maths corpora; translated/augmented questions | Separate language tuning and bilingual combined curriculum | English/Hindi question-answer versions; not constant-English-target R/C arms | R/C input-form effect rather than generic bilingual maths adaptation |
| [B: Indi-RomCoM](https://arxiv.org/html/2606.30790v1) | Seven tasks including GSM8K; four Indic languages; Romanized mixtures | CM-tuned versus untuned models | Register-matching output instructions; Table 14 refers to Roman CM targets | Active R-only matched training comparator; artifact ambiguity remains |
| [C: CodeMixBench](https://aclanthology.org/2025.emnlp-main.109.pdf) | Synthetic code-mixed evaluation, including Hindi-English GSM8K | Existing checkpoint/few-shot comparisons | Mixed inputs; CoT maths output scored using answer extraction | A controlled training intervention, rather than evaluating existing models |
| [D: CodeMixTax](https://github.com/sthanika-ai/CodeMixTax) | Aligned GSM8K/MMLU in five script/register forms | Paired inference across existing models | Includes both Romanized Hindi and Romanized Hinglish inputs | E/R/C diagnostics already overlap; incremental training value is the question |
| [E: XCOT](https://ojs.aaai.org/index.php/AAAI/article/download/34524/36679) | GSM8K translated into ten other languages; MGSM/MSVAMP tests | Multilingual tuning, code-switched context, Random-CoT and distillation ablations | Translated queries retain English responses; switching in contextual demonstration queries | No Hindi Romanized-R/C direct-input arms with all other components fixed |
| [F: LinguaLIFT](https://arxiv.org/html/2412.12499v2) | English corpora/lexicon-generated mixtures; multilingual reasoning tests | Encoder/alignment layer followed by English task tuning; stage/ratio ablations | Stage 1 code-switched-input to English translation; stage 2 English maths | Direct matched R/C maths SFT is different from two-stage representation bridging |
| [G: MathOctopus](https://aclanthology.org/2024.findings-emnlp.411.pdf) | Translated GSM8K question-answer pairs | Parallel, cross, mixture and rejection-sampling strategies | Parallel uses same-language Q/A; cross uses English Q/native answer | “Mix” is corpus-pair composition, not our within-question C condition |
| [H: Nanda](https://aclanthology.org/2026.eacl-long.288.pdf) | Broad Hindi-English pretraining/instruction corpora; native, Romanized and mixed forms | Combined corpus/model development and benchmark evaluations | Diverse casual/formal Hindi instructions/outputs | Corpus coverage does not isolate R versus C mathematical adaptation |
| [I: mCoT](https://aclanthology.org/2024.acl-long.649.pdf) | MetaMathQA/MathInstruct translated across eleven languages | Multilingual maths SFT and consistency evaluation | Translated questions and same-language reasoning; not fixed English targets | Paired evaluation and multilingual SFT are precedents, but not Hindi R/C arms |
| [J: MathMist](https://aclanthology.org/2026.findings-eacl.131.pdf) | Parallel multilingual mathematical benchmark | Frozen-model prompting, reasoning perturbations and Q/CoT language policies | Its “code-switching” analysis includes question/CoT language mismatch | Output-policy evaluation is distinct from within-input Hinglish training |
| [K: Sarvam-M](https://www.sarvam.ai/blogs/sarvam-m) | GSM8K/MATH plus other tasks; native and Romanized Indic inputs | SFT/RLVR curriculum, combined-language recipe | Romanized/native/English questions enter maths training; output matching not established | Romanized maths adaptation already exists; isolated E+R/E+C comparator absent from report |
| [L: Think Multilingual, Not Harder](https://arxiv.org/html/2604.15490v3) | Global MMLU reasoning subjects, NLLB and Global PIQA; seven languages including Hindi | Six SFT intervention types on three reasoners | Native prompts with native/English/strategic or synthetic mixed reasoning targets; translation tasks | Varies completions/objectives; our intervention varies Romanized R/C questions with constant English solutions |
| [M: AdaMame](https://arxiv.org/html/2606.15080v2) | Translated DAPO-MATH-17K, generated query-language traces | SFT then adaptive-reward GRPO; accuracy/fidelity/efficiency ablations | Query-language reasoning fidelity, rather than constant English completions | Reasoning-language alignment is a different outcome/intervention |
| [N: Korean self-correction](https://arxiv.org/html/2601.05459v1) | MathDial-generated correction traces; Korean mathematical evaluation | Language-specific neuron tuning, training-method/data-order comparisons and RL | English/mixed/Korean stages inside self-correction solutions | Mixed-output supervision and neuron targeting, not Hindi R/C input rendering |

## Matrix B: matching, budget, split, seeds and inspectable artifacts

**NR** = required property not located in the inspected method/artifact; **NA** = the exact trained-arm control does not apply to the frozen-model study. Split descriptions below are reported policies, not an audit proving family independence or excluding pretraining contamination. Seed documentation does not establish paired independent training replication.

| Key | Mathematical-content matching / budget | Split and paired-seed evidence | Artifacts inspected / limitation |
| --- | --- | --- | --- |
| A | Parallel English/Hindi content; curriculum exposure; R/C matching NR | R/C family ledger NR; reproducibility checklist flags seed documentation absent | Official paper, seven-page technical appendix and `train.py`; release directory inspected, data not exhaustively audited |
| B | CM corpus; C.1/Table 14 disagree on split/intensity | Family grouping and paired training seeds NR | Paper/appendices; no attributable project training repository found in bounded search |
| C | Paired English/CM evaluation; matched training budget NA | Evaluation/prompt settings; exact-arm seed design NA | Proceedings §§3–4/appendices, official README; no independent run |
| D | Item alignment documented; training budget NA | Existing-model paired evaluation; training seeds NA | README and author report; raw runs/results deliberately absent |
| E | Translated question content and retained responses; extra contexts/objectives | Benchmark splits described; R/C grouping/paired seeds NR | AAAI methods/ablation tables plus arXiv v1; dedicated training-release link not located |
| F | Alignment/task stages differ in data and updated modules | Benchmark construction; R/C grouped splits/paired seeds NR | v2 methods and Appendices A/D; a generic framework link is not a verified project release |
| G | Parallel/cross share translated problem origin; mixtures expand volume | Benchmark splits; official launch seed 1234, paired-seed replication NR | Paper Appendix D.2 and official repository README/training command |
| H | Combined broad corpora, not matched maths arms | Some evaluation decontamination documented; exact-arm seeds NA | Proceedings §§2–4 and evaluation appendix; official repo/model links |
| I | Translated common sources; full multilingual corpus | MGSM/MSVAMP evaluation; paired R/C training seeds NR | Paper §§3–4 and Appendix A; official repository/data/model links |
| J | Parallel content and multiple output-policy evaluations | Frozen-model comparisons; training seed control NA | Proceedings §5.4/Limitations, official repository listing |
| K | Reported maths mixture 40% English/40% native Indic/20% Romanized Indic | Exact-arm family split/seed/exposure ledger NR | Official technical blog §§2.1/3 and model card; recipe not reproduced |
| L | One-million-token SFT budget per model/language/task; example counts vary | Reported 500-item validation/test sets; family grouping and paired seeds NR | v3 §§4.1/A.14/A.16/A.18; no project repository link located in inspected paper |
| M | Five in-domain languages; SFT/RL stages and filtered traces | Benchmark/held-out-language design; exact R/C split/paired seeds NR | v2 §§3–4 and appendices; official released repository README |
| N | Generated correction traces; sample-size/order manipulations | Korean benchmark evaluation; exact R/C design NR | v1 §§2.3/3/4.1 and Appendices B/D |

## Resolved and unresolved closest-work questions

### Anand: standalone appendix recovered

The official [Technical_Appendix.pdf](https://raw.githubusercontent.com/midas-research/Multilingual-Mathematical-Reasoning/master/Technical_Appendix.pdf) was retrieved and all seven pages read. Page 7, “Limitations,” excludes Romanized Hindi; page 1 flags missing seed-setting, infrastructure and variation documentation. That is a documentation statement, not evidence that no seeds were used. [Paper Appendix G](https://arxiv.org/html/2412.18415v1) independently supports the Romanization exclusion. The generic [`train.py`](https://github.com/midas-research/Multilingual-Mathematical-Reasoning/blob/master/train.py) supplies LoRA/SFT settings and validation-based checkpoint selection, not a matched R/C recipe.

PDF bytes: 228,523; SHA-256 `26b971de2cc9d381ab9008b50536aba9db76fe0bf03040de270ebed3dbbdeaae`. Retrieval used the public `master` URL. The content hash fixes the inspected PDF; the repository commit could not be resolved through the browsing tool. Do not claim an immutable code checkout. The downloaded third-party PDF is a temporary reading artifact, not redistributed in this project.

### Indi-RomCoM: discrepancy remains open

[Appendix C.1 and Table 14](https://arxiv.org/html/2606.30790v1) respectively report 395,076 training instances/three intensities/80% versus 50%-CM/90–10/14,848 evaluation items. Their model coverage also differs. No inspected artifact reconciles these protocols or generated-variant splitting. Do not borrow either recipe as resolved fact. This does not establish leakage, invalidity or undisclosed R-only arms.

### XCOT: strongest supervision/intervention overlap

The [AAAI paper](https://ojs.aaai.org/index.php/AAAI/article/download/34524/36679), PDF p. 3/published p. 23552, “Data Construction,” retains English responses for translated queries. Figure 2 and the tuning section distinguish switched contextual demonstrations from current queries; Table 6 compares context policies. Our missing comparator concerns Romanized-Hindi/Hinglish direct inputs with ancillary mechanisms fixed.

### Current additions do not justify mechanism claims

Sarvam-M prevents a claim that Romanized mathematical post-training itself is new. Lin and Jurgens v3 prevents a broad claim that alternative code-switched reasoning training controls are new. Neither report identifies the exact primary intervention specified above. Their target/objective differences motivate keeping our full English completion byte-identical, rather than attributing a gain to altered reasoning supervision. These are design inferences, not results about our models.

## Primary source and version ledger

Every source below was accessed 10 October 2026. Stable proceedings PDFs are identified by Anthology/DOI record; repository branches/blogs are mutable access-date snapshots unless a content hash is supplied. No reproduction, exhaustive repository checkout, or release-license conclusion is implied.

| Key | Inspected version and precise locators | Primary artifacts |
| --- | --- | --- |
| A | arXiv 2412.18415v1, 24 Dec 2024; “Bilingual Combined Training,” Tables 2–4, Appendices A/G; standalone appendix pp. 1–7 | [Paper](https://arxiv.org/html/2412.18415v1), [official repository](https://github.com/midas-research/Multilingual-Mathematical-Reasoning), [appendix](https://github.com/midas-research/Multilingual-Mathematical-Reasoning/blob/master/Technical_Appendix.pdf), [training file](https://github.com/midas-research/Multilingual-Mathematical-Reasoning/blob/master/train.py) |
| B | arXiv 2606.30790v1, 29 Jun 2026; §§3.1/4.2/5.2, Appendices A.1/C.1/C.2/D.2, Tables 12/14 | [Versioned paper](https://arxiv.org/html/2606.30790v1), [submission record](https://arxiv.org/abs/2606.30790) |
| C | EMNLP 2025, Anthology 2025.emnlp-main.109; §§3–4, Table 2, prompting appendices | [Proceedings PDF](https://aclanthology.org/2025.emnlp-main.109.pdf), [official repository](https://github.com/Jeromeyluck/CodeMixBench) |
| D | Mutable author repository/report; “five language forms,” reproduction/material availability and limitations | [Official README](https://github.com/sthanika-ai/CodeMixTax), [author report](https://sthanika.ai/research/codemix-tax-2026) |
| E | AAAI 2025 DOI 10.1609/aaai.v39i22.34524, PDF pp. 2–4/7, Tables 4/6; arXiv 2401.07037v1, 13 Jan 2024 §§3.2–3.5 | [Proceedings PDF](https://ojs.aaai.org/index.php/AAAI/article/download/34524/36679), [versioned arXiv](https://arxiv.org/html/2401.07037v1) |
| F | arXiv 2412.12499v2, 17 Feb 2025; §§3.1–3.2/6.1–6.8, Appendices A.4/D | [Versioned paper](https://arxiv.org/html/2412.12499v2) |
| G | Findings EMNLP 2024, Anthology 2024.findings-emnlp.411; §2.3, Appendix D.2; official README “Fine-tuning” | [Proceedings PDF](https://aclanthology.org/2024.findings-emnlp.411.pdf), [official repository](https://github.com/microsoft/MathOctopus) |
| H | EACL 2026, Anthology 2026.eacl-long.288; §§2–4, Table 3, evaluation Appendix C | [Proceedings PDF](https://aclanthology.org/2026.eacl-long.288.pdf), [official repository](https://github.com/MBZUAI-IFM/Nanda-Family) |
| I | ACL 2024, Anthology 2024.acl-long.649; §§3/4.1–4.3, Appendix A | [Proceedings PDF](https://aclanthology.org/2024.acl-long.649.pdf), [official repository](https://github.com/laihuiyuan/mCoT) |
| J | Findings EACL 2026, Anthology 2026.findings-eacl.131; §5.4, Figure 3, Limitations | [Proceedings PDF](https://aclanthology.org/2026.findings-eacl.131.pdf), [official repository](https://github.com/mahbubhimel/MathMist) |
| K | Sarvam AI technical blog dated 23 May 2025; §2.1 “Math skills,” §3 “Evaluation”; model-card training description | [Official report](https://www.sarvam.ai/blogs/sarvam-m), [official model card](https://huggingface.co/sarvamai/sarvam-m) |
| L | arXiv 2604.15490v3, 3 Oct 2026 (updated title); §4.1, Appendices A.14/A.16–A.18 | [Versioned paper](https://arxiv.org/html/2604.15490v3), [version history](https://arxiv.org/abs/2604.15490) |
| M | arXiv 2606.15080v2, 20 Sep 2026; §§3.1–3.3/4, Appendices B/C | [Versioned paper](https://arxiv.org/html/2606.15080v2), [official repository](https://github.com/dayeonki/adamame) |
| N | arXiv 2601.05459v1, 9 Jan 2026; §§2.3/3/4.1, Appendices B/D | [Versioned paper](https://arxiv.org/html/2601.05459v1) |

## Bounded search log and stopping rule

Scope: recheck the eight existing main works; resolve the two closest artifact questions; inspect relevant cited/citing primary work that changes the exact-control interpretation; screen recent mathematical code-mixing/romanization training. Technical conclusions rely on primary papers or author artifacts, not search snippets/third-party summaries.

Queries issued in this audit included:

- `Indi-RomCoM github dataset fine tuning`
- `XCOT cross lingual instruction tuning github`
- `Romanized Hindi code mixed mathematical reasoning training 2026`
- `"Indi-RomCoM" "github"`
- `"XCOT" "Chai" "github"`
- `"Hinglish" "Romanized" mathematical fine-tuning control 2026`
- `"code-mixed" "mathematical" training ablation 2026`
- `"Indi-RomCoM" training romanized Hindi`
- `"XCOT" code mixed Romanized Hindi mathematics`
- `"Romanized Hindi" "mathematical reasoning" training control`
- `"Think Multilingual, Not Harder" "Romanized"`
- `"Indi-RomCoM" dataset release`
- `"Hinglish" "math" "fine-tuning" "Romanized Hindi"`
- `"code-mixed" "math" "matched" "training"`
- `MathOctopus official Github MGSM8KInstruct`
- `"Think Multilingual, Not Harder" "github" "Lin"`
- `"XCOT" "Romanized" "training"`
- `"Hinglish" "E+R" "E+C" mathematical reasoning`

Backward/forward follow-up: XCOT/MathOctopus precedents in mCoT and LinguaLIFT; XCOT cited by AdaMame; AdaMame's citation to Lin and Jurgens led to the current v3; exact-title/author artifact discovery checked those papers. This is citation-following, not a complete citation-index enumeration.

Additional primary screens: [UL-XCoT](https://arxiv.org/abs/2604.20090) and its [official repository](https://github.com/chenyuanTKCY/UL-XCoT) describe multilingual inference routing/pruning, not the requested training control. [Akshar](https://huggingface.co/Sujalvc/akshar-qwen2.5-1.5b-instruct) and [Bharat-Tiny v3](https://huggingface.co/eulogik/Bharat-Tiny-LLM-v3) author model cards describe adjacent Hinglish/Hindi adaptation; they were screened only, not fully audited negative results. Speech/sentiment/code-generation studies and secondary summaries were excluded as evidence for our exact mathematical intervention.

Stopping rule used: finish the eight-work recheck and six targeted method additions; attempt official resolution of the named appendix/split issues; stop after the follow-up query batches yield no new plausible exact-comparator primary paper requiring a design change. Broad query results became dominated by speech, sentiment, unrelated software code, tutoring and model cards. This supports stopping this phase, not an exhaustive novelty certificate. Repeat the bounded search near confirmatory freeze and submission, and reopen immediately if a closer control is supplied.

## Paper value and next decision

The strongest reviewer objection is expected target-distribution adaptation: a model trained on our synthetic C style may simply learn that style. Our recommendation is therefore conditional on a useful test of **transfer beyond the training author/generator**, with family-level exclusions and independent spellings/phrasings, and explicit evaluation on E/R/C. Those variants are repeated measurements of a family, not extra independent maths problems.

Keep the smallest essential trained matrix E+E/E+R/E+C. Prespecify the C effect, English-loss tolerance, held-out author/style construction, paired seeds, checkpoint-selection rule and sample-size sensitivity before confirmatory data/outcomes. Translation and second-backbone replication are resource-dependent extensions; multiple unchanged-model evaluations do not replicate a training effect. A translation baseline must translate C itself, with both stages' cost/error recorded, rather than receive our reference E.

A narrow, well-estimated null can be useful evidence about data choice. A wide interval is inconclusive; familiar-style-only gains support specialization; a C gain with English loss is a tradeoff. No outcome is assumed or guarantees publication.

**Next human action:** before independent solving, collect honest gold-exposure disclosures and resolve candidate family relationships; then collect genuine independent solves/review/adjudication, freeze accepted texts/units/borrowing/splits and run the unchanged-model pilot. Reading cannot settle attainable accuracy, difficulty, formatting or training memory fit. Missing third-party artifacts should remain documented limitations, rather than indefinitely delaying that valid gate.
