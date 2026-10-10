# Hinglish Mathematical Reasoning in LLMs
## A teammate's guide from the beginning

Delhi Technological University | Final-year BTech research project

Project snapshot: 10 October 2026

> CURRENT STATUS: Pilot software built. A short real-model T4 inference check passed. Thirty mathematical families are AI-authored DRAFTS awaiting human review. No reviewed research pilot or training experiment has been completed.

### What are we trying to find out?

We want to know whether training a language model on Hindi-English mixed mathematical questions gives an advantage over training on Hindi questions written in Roman letters. The comparison should hold the underlying mathematics and English solution supervision fixed. A defensible research paper needs this controlled comparison, reliable data and honest reporting.

The immediate work is smaller: prepare and test an unchanged-model pilot. It will show whether our data, GPU setup, prompting, answer scorer and reports are ready before we spend time on training.

### What has happened so far?

| Milestone | Evidence and current status |
| --- | --- |
| Research design | A targeted closest-work comparison refined the question and its controls. Novelty is provisional. |
| Evaluation software | A complete Colab notebook, maintained Python helpers, templates, demo fixtures and tests are implemented. |
| Software demo | A fake backend exercised the pipeline and result export. Its answers are not model evidence. |
| Real-model engineering check | Qwen3-4B loaded and generated short responses on a Tesla T4. Scoring-format defects were documented. |
| Candidate data | 30 AI-authored families, 90 E/R/C renderings and independent-review packets were prepared. All remain DRAFT. |
| Actual research | Human acceptance, the 90-item reviewed pilot, training feasibility and controlled training are still pending. |

### How to read this guide

Pages 2-4 explain the scientific question. Pages 5-6 explain the software and what actually ran. Pages 7-9 explain data review, scoring and analysis. Pages 10-12 give the Colab workflow, team tasks and file map.

> REVIEWER NOTICE: This guide uses only an excluded software example. Reviewers must avoid A01's answer key and coordinator gold fields until their independent stage1 solutions have been submitted.

<!-- PAGEBREAK -->
# 1. The language forms: E, R and C

All three forms should ask the same mathematical question. Only the language form changes. Roman script means the Latin letters used here; it does not mean English.

| Code | Meaning | What counts |
| --- | --- | --- |
| E | English | The question is written in English. |
| R | Romanized Hindi | Hindi phrasing in Roman letters, under a documented common-borrowing policy. |
| C | Roman-script Hinglish | Hindi and English are mixed; a productive English clause, predicate or mathematical relation is required. |

### One excluded software example

The following is the existing demo-1 fixture. It is permanently outside research and confirmatory evaluation. It is not human-validated natural Hinglish.

**E:** There are 2 red and 3 blue counters. How many counters?

**R:** 2 laal aur 3 neele ginte ke tukde hain. Kul kitne tukde hain?

**C:** 2 red aur 3 blue counters hain. How many counters in total?

The same calculation is 2 + 3 = 5. An illustrative response ends with `FINAL: 5 counters`. C contains an English requested-answer clause; merely inserting an English object noun would not satisfy our C definition.

### Why review is necessary

A translation may accidentally reverse a comparison, change the requested unknown or lose a condition. For example, "five fewer than" and "five more than" are different mathematics. Numeric equality alone cannot establish equivalent questions. Reviewers inspect quantities, entities, units, comparison/rate direction, time conditions, requested unknown and assumptions.

A borrowing policy prevents an artificial R condition. Digits, symbols, variable names, common units and some established loanwords may be shared. Their historical origin alone does not make a sentence code-mixed. The proposed borrowing list still needs human review and freezing before research generation.

### What is a mathematical family?

A family is the underlying problem plus its translations, paraphrases, spelling variants and numerical siblings. Changing numbers in a template does not automatically make a new independent family. Sharing a broad skill, such as subtraction, also does not automatically make two genuinely different problems duplicates. Both provenance and human inspection matter.

Our proposed sample is 30 families with three forms each. It yields 90 prompts, but only 30 independent mathematical units for paired analysis.

<!-- PAGEBREAK -->
# 2. The eventual controlled training question

### The proposed three arms

Start each arm from the same initial checkpoint. An arm is one training condition, not a different model family. These arms are planned; they have not been trained.

| Arm | Input exposure for a matched family | Purpose |
| --- | --- | --- |
| E+E | Two English exposures | Controls for additional mathematical practice under matched example exposure. |
| E+R | One English and one Romanized-Hindi exposure | Tests Hindi phrasing in Roman script. |
| E+C | One English and one Roman-script Hinglish exposure | Tests mixed-language phrasing beyond the R condition. |

The English solution completion must be identical across matched renderings of a family, including its explanation. Having only the same final number is a weaker control.

### What must be held fixed?

- Initial checkpoint, architecture and adapter settings.
- Underlying mathematical families, shared English questions and exact English solution targets.
- Language-mixture proportions, example exposure, updates, checkpoint selection and paired training seeds.
- The held-out evaluation families and common scoring policy.
- Family-level separation of every translation, paraphrase and numerical sibling.

Match examples and exposure transparently. E, R and C can have different token lengths, so example matching is not token matching. We must report token counts and compute costs. A result would concern these training renderings under the specified recipe, not an isolated causal effect of switching independent of vocabulary and length.

### The main future comparison

Primary contrast: accuracy of E+C training on C test questions minus accuracy of E+R training on those same C families. Evaluate E and R too: C gains could come with English loss or reflect specialization in one register.

A future practical baseline is translating C into English and then solving. It must perform the translation itself; it cannot receive our human reference E question as a free oracle. Both stages' costs and errors need reporting.

### What Test 1 can answer

Test 1 uses one unchanged checkpoint for E/R/C. It can check language quality, inference feasibility, output validity, paired differences, cost and difficulty floor/ceiling effects. It cannot establish any training benefit, internal reasoning mechanism or general LLM claim. Full tuning and reinforcement learning are outside the implemented pilot.

<!-- PAGEBREAK -->
# 3. Why the literature comparison matters

A paper needs a useful scientific comparison, not simply a new project name. Code-mixed evaluation, bilingual mathematical training and English reasoning targets already have precedents.

The targeted audit dated 10 October 2026 did not locate our exact matched E+C versus E+R mathematical training control in the inspected sources. That supports proceeding provisionally. It is not proof of a worldwide first, a complete systematic review or a publication guarantee.

| Closest work | What it already covers | Boundary relevant to our question |
| --- | --- | --- |
| Multilingual Mathematical Reasoning | English/Hindi maths and bilingual curriculum training | A matched R-versus-C arm with shared English completions was not located. |
| Indi-RomCoM | Romanized Indic-English tasks, including maths, and fine-tuning | Closest application overlap. An R-only matched comparator was not located. |
| CodeMixBench | Code-mixed evaluation, including mathematical questions | Existing-model and prompt comparisons differ from controlled R/C training. |
| CodeMixTax | Paired inference across language/script forms | E/R/C evaluation alone overlaps; no separate matched training intervention was located. |
| XCOT | Code switching and cross-lingual mathematical tuning | Strong methodological overlap; extra modules and context treatments differ. |
| LinguaLIFT | Code-switched alignment plus English task supervision | Different stages/objectives, not the direct matched R/C mathematical arms. |
| MathOctopus | Multilingual mathematical training and language-pair strategies | Its mixture strategies are not automatically within-question Hinglish mixing. |
| Nanda Family | Native, Romanized and mixed Hindi training | Combined exposure does not isolate the R/C mathematical effect. |

### What would make our evidence more useful?

Use independently authored or reviewed test phrasings and spelling variants, with families kept out of training. Report English retention and R/C transfer. Include the E+E exposure control. A second trained backbone may strengthen replication if resources permit; several unchanged models alone cannot replicate a training effect.

A small or uncertain difference must be reported honestly. A wide interval around zero is inconclusive, not proof of equivalence. A gain limited to the training generator's style is weaker evidence of broad transfer.

The full linked matrix, source locators, discrepancies and artifact gaps are in `research/closest_work_comparison_2026-10-10.md`. Repeat the novelty search near submission. Older research and model-selection documents remain proposals; later decisions narrow Test 1 to one primary model and make E+E part of the eventual essential controls.

<!-- PAGEBREAK -->
# 4. What software has been built?

### A complete pilot package

`test1_pilot/` contains the self-contained Colab notebook, maintained helper modules, dependency specification, templates, synthetic fixtures, tests and a portable archive. The notebook embeds a checksummed helper bundle: it does not rely on the author's Mac or an unpublished repository.

| Component | What it does |
| --- | --- |
| data.py | Validates the exact JSON contract, human-review attestations, hashes and split exclusions. |
| hf_backend.py | Loads the explicit Qwen configuration, applies its chat template and records actual runtime facts. |
| engine.py | Saves attempt journals, verifies resumes, limits retries and records inference telemetry. |
| scorer_v1.py | Preserves the existing strict numeric/unit scorer, version 1.0.0. |
| report.py | Produces paired-family summaries, audit tables, plots and a checksummed export. |
| Main Colab notebook | Guides setup, input validation, demo checks, real loading, pilot execution, analysis and download. |
| GPU-smoke notebook | Runs excluded short software fixtures with the actual model; no reviewed dataset upload is needed. |

### Two deliberately separate modes

**DEMO / SOFTWARE CHECK:** synthetic fixtures, separate run names and folders, prominent labels and no human-validation claim. A fake backend returns canned responses to exercise the pipeline. A real-model demo remains a software check.

**REVIEWED PILOT:** requires the 30 accepted families, review/adjudication metadata and a human split audit. Missing or invalid required fields stop execution with an actionable error. The current DRAFT data cannot pass this gate.

### What local verification established

Twenty-two new model-free test methods passed. The existing scorer's three methods, including 60 balanced answer cases, and the training-smoke protocol's four methods/self-check passed. No training runner executed.

Tests cover rejection cases, exact scoring, family-level bootstrap/pairing, bounded retries, interruptions, stale-lock recovery, incompatible resumes, corruption, manual overlays, secret patterns and ZIP checksums. Notebook JSON/Python syntax checks passed; the fake demo also ran in a fresh Jupyter kernel. These checks do not establish GPU execution or human validity.

The new annotation packet was separately checked for 30 families/90 forms, preserved initial texts, randomized coverage, exact reference calculations/conversions, empty judgments, archive separation and deliberate reviewed-mode rejection. Browser import/export logic was tested with a stub DOM; a complete real-browser annotation workflow remains unverified.

<!-- PAGEBREAK -->
# 5. What actually ran on the GPU?

> REAL-MODEL SOFTWARE SMOKE ONLY. The returned run used two toy families, not the 30 research candidates. Its score cannot be treated as Hinglish research accuracy.

The user returned `demo-qwen-gpu-v1_results.zip`. Its 25 file checksums and configuration/data/split/source/environment fingerprints passed; six attempt-record hashes were checked. The original archive remains unchanged.

| Observation | Returned evidence |
| --- | --- |
| Actual GPU | Tesla T4 |
| Model | Qwen/Qwen3-4B, unchanged and quantized |
| Actual stack | Transformers 4.51.3; bitsandbytes 0.50.2; torch 2.11.0+cu130; Python 3.13.15 |
| Scored demo prompts | Six completions: two toy families times E/R/C; zero unresolved failures or truncations |
| Separate format fixture | One additional short format-only output; excluded from scored research |
| Load time | 224.75 seconds, including any possible weight download |
| Six generation latencies | 33.79 seconds total; 5.36 seconds median |
| Peak PyTorch reserved memory | Maximum reported generation peak: 4.19 GiB, including loaded-model baseline |
| Device free memory | Lowest endpoint sample: 10.21 GiB; not a continuously measured minimum |

Model/tokenizer revision: `1cfa9a7208912126459214e8b04321603b3df60c`.

### Why the original score was 0/6

All six outputs were automatically marked invalid_unit. Inspection found the final numeric values correct, but that technical check is not a revised research accuracy result.

The count fixture mistakenly had a blank canonical unit although it asked for counters. Demo-v2 corrects that metadata and declares equivalent count aliases. Three fraction responses appended words such as whole, fraction or part; the strict dimensionless suffix policy continues to reject them. We did not silently widen the scorer to accept arbitrary trailing nouns. One R explanation also used Hindi despite the English explanation instruction.

Original automatic scores, raw generations and the archive are preserved. The diagnostic CSV is a post-hoc engineering inspection, not a human review or confirmatory finding. New demo data use new run names; old v1 runs cannot be resumed with v2 data.

### What is still unknown?

This establishes short-input inference feasibility on the observed T4 stack. It does not establish the full 90-item workload, training memory, optimizer/save-reload behavior, research-data quality or a training effect. No further smoke rerun is needed simply to repeat this limited conclusion.

<!-- PAGEBREAK -->
# 6. The 30-family review packet

Thirty candidate families have been drafted: five in each topic below. Each has E/R/C renderings. PIL001-PIL005 preserve the original five illustrative question texts; the other 25 are newly AI-authored drafts.

| Topic key | Plain-language topic | Candidate families |
| --- | --- | --- |
| comparison_remaining | Comparisons and quantities remaining | 5 |
| two_step_money | Two-step money problems | 5 |
| fractions_percentages | Fractions and percentages | 5 |
| ratios | Ratios | 5 |
| rates_units | Rates and unit relationships | 5 |
| elementary_algebra | Elementary algebra | 5 |

All 30 remain DRAFT. Human equivalence, naturalness, classification, difficulty and independence have not been certified. Different IDs cannot certify independence. The coordinator packet identifies specific overlap priorities, including PIL002/PIL010 and PIL005/PIL021, and requires inspection beyond those pairs.

### The independent-review workflow

1. R01 and R02 each receive only their separate reviewer archive. They work independently without the other reviewer's answers, model outputs, reference key or translation tools.
2. In stage1.html, each solves all randomized renderings and records equation, reasoning, exact answer and unit. Save/download progress; unsaved browser-tab edits can be lost. Submit the independent solves before opening stage2.
3. In stage2.html, import the saved stage1 file. Original answers stay read-only. Compare each E/R/C triplet, record semantic checks, classification, ambiguity, naturalness/readability, borrowings and issues. Explain later answer corrections without erasing first-pass work.
4. Each reviewer returns two JSONs. A01 receives both reviewers' records and the proposed key, records decisions/reasons, and resolves disagreements. Repaired text needs a new version/hash and both independent re-reviews.
5. Acceptance and split audit are recorded only after the real process. Convert the accepted version to the pilot input contract, preserve the raw annotation trail, freeze policy/text/gold and validate before Colab.

ACCEPT requires equivalent content, correct treatment classification, no unresolved ambiguity and naturalness/readability ratings of at least 4 from each reviewer. R01, R02 and A01 are pseudonymous role placeholders, not invented people or completed approvals.

> Keep gold private during independent solves. A GitHub repository can contain coordinator/A01 files for reproducibility; assigned reviewers must still avoid them. Review archives intentionally contain no reference gold.

All pilot, smoke, rejected draft families and their descendants are permanently excluded from future confirmatory training and final tests. The separate 16-family training-smoke data and future confirmatory sets have not been authored.

<!-- PAGEBREAK -->
# 7. The frozen inference and scoring rules

### One common evaluation condition

Test 1 uses the same unchanged checkpoint, fixed English task instruction and common scorer for every rendering. The instruction requests an English explanation and a clearly marked final numeric answer. Each rendering starts a fresh model context; answers do not accumulate in one conversation.

The current candidate is Qwen3-4B, NF4 4-bit quantization with double quantization, FP16 computation, one CUDA device and SDPA math kernel. Thinking is explicitly disabled. Decoding is greedy, batch size 1; generation seed 11, output limit 1,024 new tokens and total context preflight cap 2,048. Model/tokenizer immutable revisions and actual package/hardware versions are saved. Greedy settings are our explicit policy, not a claim that they reproduce the model card's recommended sampling.

Evaluation order is seeded and saved. The complete prompt is checked before inference; question text is never silently truncated. A failure cannot silently trigger a model substitution, shorter question, lower cap, changed precision or different thinking mode. Deterministic settings do not guarantee bitwise equality across every hardware/library combination.

### Numeric correctness is strict and transparent

- Parse only the designated final-answer format, never a convenient intermediate number in the reasoning.
- Use safe exact integer, decimal and rational arithmetic. Numerically equivalent values such as 1/2 and 0.5 can match.
- Apply only predefined unit aliases/conversions. Unit omission is permitted only where the item policy allows it. An explicitly wrong unit remains wrong.
- No arbitrary floating tolerance and no LLM judge replace the numeric rule.
- Missing finals, duplicate/conflicting finals, ambiguous output, refusal and output truncation count incorrect.
- For explicit rounding questions, author the exact predetermined rounded target and policy before generation; otherwise use exact-answer questions.

A format failure can hide correct arithmetic, as the GPU demo showed. Preserve this distinction through diagnostic categories and manual audit, without silently changing automatic scores.

### Attempts and failures

After each generation, save raw text, exact prompt/reconstruction, IDs, extraction/normalization, score/status, tokens, timing, truncation and memory telemetry. One documented infrastructure retry is permitted with unchanged settings; attempts and reasons remain visible. A wrong or invalid completed answer is not retried for a better result.

OOM stops immediately. Exhausted infrastructure failures make the run incomplete; they are not dropped from the denominator. A transparent scoring attempt is designated rather than choosing the best retry.

<!-- PAGEBREAK -->
# 8. How results become a defensible report

### Completeness comes first

The report records expected, attempted, completed and unresolved items. A complete reviewed pilot expects all 90 renderings. If an infrastructure failure remains unresolved, headline accuracy comparisons are suppressed and the run is unmistakably incomplete. A useful troubleshooting archive is not a completed experiment.

| Report element | Why it matters |
| --- | --- |
| E/R/C correct counts and denominators | Makes the sample and missingness explicit. Each complete form has 30 items. |
| 95% Wilson intervals | Describes uncertainty around each small-sample accuracy. |
| E-C, E-R and R-C paired differences | Compares forms on the same mathematical families. |
| Both correct, both wrong, discordant counts | Reveals which families drive a difference. |
| 10,000 paired bootstrap resamples | Resamples whole families, preserving E/R/C pairing; seed 101 is recorded. |
| Invalid/refusal/truncation rates | Separates output-format reliability from numeric success. |
| Tokens, latency and memory | Exposes resource cost and feasibility. |
| Topic breakdowns | Descriptive only: five families per topic is a very small sample. |

Do not treat 90 renderings as 90 independent problems. Descriptive intervals and patterns do not establish statistical significance, internal mechanisms or training benefits. Near-perfect or near-zero accuracy can indicate a difficulty ceiling or floor; inspect it before planning a larger study.

### A separate manual audit

Independently inspect all raw generations and original automatic scores. Review decisions belong in a separate overlay with pseudonymous reviewer ID, decision, reason, category and timestamp. Original automatic scores remain intact. Revised analysis is versioned and archived; nobody silently edits a prediction CSV to improve a headline.

Any real scorer correction must be documented, versioned and consistently applied to stored outputs. Scoring rules must not be tuned to favor a language form or model.

### The one results ZIP

The export contains run_manifest.json, environment.json, experiment_config.json, dataset_snapshot.jsonl, split_manifest.json, generation_attempts.jsonl, predictions.csv, family_comparisons.csv, metrics.json, summary.md, manual_audit.csv, errors.jsonl and checksums.sha256. It includes code/input/config hashes, UTC times, model/tokenizer revisions, actual dependencies, warnings, scorer version and completion/demo status.

The executed notebook can be included if uploaded reliably; otherwise download it separately. Credentials and personal reviewer mappings stay outside exports. An allowlist and pattern checks help, but a person must still inspect arbitrary free text before sharing.

<!-- PAGEBREAK -->
# 9. Running the right notebook in Colab

### What should the team run now?

The next research action is human review, not another accuracy run. The GPU engineering check is already complete. The main reviewed pilot awaits accepted inputs. Anyone wanting to learn the interface can run the default fake demo; its ZIP must remain labeled SOFTWARE DEMO.

### When the reviewed data are ready

1. Open `test1_pilot/Hinglish_Math_Test1_Pilot_Colab.ipynb` in Colab using File > Upload notebook. The notebook is self-contained; the portable ZIP is for source archival and does not need uploading.
2. Select Runtime > Change runtime type > T4 GPU. In the single central configuration cell set MODE='reviewed', BACKEND='huggingface' and a unique RUN_NAME, for example 'pilot-reviewed-v1'. Keep the frozen protocol settings.
3. Set USE_DRIVE=True if persistent storage is desired; mounting Drive is a user-controlled step. Run setup/environment checks and dependency installation. If conflicting libraries were already imported, restart the session and rerun as instructed.
4. Upload the accepted `pilot_dataset.json` and audited `split_manifest.json` when prompted. Raw stage1/stage2/adjudication JSONs and DRAFT coordinator files are not runnable accepted inputs.
5. Run validation, inspect the excluded format-only smoke output, load the explicit model and execute the 90-item pilot. Read warnings; do not fix an OOM by silently editing scientific settings.
6. Inspect completeness, raw responses, scoring-audit material and plots. Complete the manual review workflow. Download the final reviewed run's `*_results.zip` and use File > Download > Download .ipynb for the executed notebook.
7. Return that ZIP and executed notebook to the research assistant. An incomplete ZIP is still useful for diagnosing failures, provided its status is preserved.

### Disconnect and resume

Use the same run name, persistent folder, input snapshots, code/config and actual environment. Resume rejects incompatible fingerprints and skips all committed completions, including incorrect or invalid answers. Interrupted in-flight work is recorded and consumes the defined retry allowance.

Only after confirming no notebook is still writing may you recover a stale lock using RECOVER_STALE_LOCK=True; set it back to False afterward. Never use two writers in the same run directory. Drive is useful persistence, not a transactional database: keep downloaded backups.

The separate `Hinglish_Math_Qwen_GPU_Smoke_Colab.ipynb` needs no dataset upload and is only a bounded engineering demo. Do not mistake its short synthetic inputs for the reviewed pilot.

<!-- PAGEBREAK -->
# 10. Team tasks and the next decision gates

The role descriptions below are suggested responsibilities. They do not assert that anyone has completed a review or approved a dataset.

| Role | Concrete responsibility |
| --- | --- |
| Coordinator | Assign pseudonymous roles, keep gold separate during solves, preserve raw submissions/version history and track pending repairs. |
| R01 and R02 | Independently solve and review all forms; record disagreements and naturalness/classification issues honestly. |
| A01 adjudicator | Resolve disagreement after independent submissions, document reasons and require re-review after repairs. |
| Data/split auditor | Check provenance, source/license records, borrowing policy and mathematical family relationships/exclusions. |
| Colab operator | Run only frozen accepted inputs; preserve logs, attempts, manifests and complete result downloads. |
| Scoring auditor | Inspect every response, retain originals and propose documented overlays or genuine scorer corrections. |
| Research lead | Keep the literature matrix/current protocol aligned; design the later training study and bounded claims. |

### Roadmap with evidence required

**Gate 1 - Data readiness:** collect the four reviewer JSONs and A01's completed adjudication JSON. Resolve repairs and re-review, finalize provenance/release terms, freeze the borrowing policy, and complete a genuine human split audit. The current source release terms for candidate data are not yet assigned.

**Gate 2 - Unchanged-model pilot:** freeze all accepted renderings, reference answers, settings, scorer and hashes. Complete 90 outputs; inspect manual scoring, validity/truncation rates, difficulty and costs. This is a development pilot, not confirmatory evidence.

**Gate 3 - Training feasibility:** separately prepare the planned 16 training-only smoke families and implement/execute the bounded optimizer/save-reload test. Short inference fit cannot establish training fit. Existing protocol code is preparation, not a completed training test.

**Gate 4 - Confirmatory design:** choose a smallest useful gain and English-retention tolerance, plan enough independent families, resolve budget/replication and freeze training arms, seed aggregation and analysis. Author/select independent confirmatory data with permanent development exclusions.

**Gate 5 - Controlled training and paper:** only after the earlier gates, execute the matched E+E/E+R/E+C study, report uncertainty/costs/tradeoffs and update the closest-work search. Publication depends on useful evidence and execution, not the absence of one located comparison.

We should not repeatedly optimize prompts on pilot accuracy. Format-only fixtures remain excluded from all future confirmatory splits. Any later pilot repeats after protocol changes are documented development runs.

<!-- PAGEBREAK -->
# 11. File map, terms and source trail

### Start here in the shared repository

| Relative path | What a teammate will find |
| --- | --- |
| research/closest_work_comparison_2026-10-10.md | Linked comparison matrix, claim limits and source/artifact gaps. |
| research/research_before_coding.md | Historical research decisions and pilot gates. |
| research/model_selection_plan.md | Historical broader model proposal; Test 1 later narrowed to Qwen. |
| pilot_review_packet.md | Governing review rubric, five initial illustrations and planned hardware protocol. Some historical status statements are superseded. |
| test1_pilot/README.md and DATA_CONTRACT.md | Exact Colab instructions and accepted dataset/split requirements. |
| test1_pilot/VERIFICATION.md | Local test evidence and later returned GPU check, distinguished. |
| research/test1_gpu_smoke_audit_2026-10-10/ | Actual returned T4 audit, preserved score interpretation and diagnostics. |
| pilot/annotation_draft_v1/README.md | Current draft review handoff and input-schema mapping. |
| pilot/annotation_draft_v1/R01/ and R02/ | Gold-free stage1/stage2 forms for independent review. |
| pilot/annotation_draft_v1/A01/ and coordinator/ | Proposed gold and pending decisions/data; restricted by review procedure until independent solves finish. |
| research/pilot_annotation_handoff_2026-10-10.md | Candidate status and annotation software checks/limitations. |
| docs/teammate_guide.md | Editable source of this guide. |

### A few terms in plain language

**Checkpoint:** a particular saved set of model weights. **Immutable revision:** the exact version identifier needed to reload those weights/tokenizer. **Quantization:** storing model weights at lower precision to reduce memory. **Fine-tuning:** updating model parameters with task examples; it has not happened here. **Gold:** the reference answer and policy established before model generation. **Bootstrap:** repeatedly resampling families to describe uncertainty while retaining paired forms. **Smoke test:** a small engineering check, not a research experiment.

### Technical sources already checked in the project

Qwen model card: https://huggingface.co/Qwen/Qwen3-4B

Hugging Face quantization: https://huggingface.co/docs/transformers/quantization/bitsandbytes

Chat templates: https://huggingface.co/docs/transformers/main/en/chat_templating

bitsandbytes 0.50.2 installation: https://huggingface.co/docs/bitsandbytes/v0.50.2/en/installation

This guide summarizes local source artifacts as of 10 October 2026. It introduces no new literature reproduction or GPU experiment. Historical proposals, implemented software and actually executed checks are explicitly distinguished. Review metadata can enforce a contract; it cannot prove truthful human review or certify every hidden family overlap.
