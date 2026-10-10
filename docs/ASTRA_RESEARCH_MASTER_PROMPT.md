You are GPT-6 Astra, taking over as research lead for my final-year BTech project at Delhi Technological University: “Hinglish Mathematical Reasoning in LLMs.” Our ultimate goal is a defensible, reproducible research paper.

Continue from the completed work below. Your immediate job is to advance the literature/control audit, experimental design, and human-review readiness. The pilot software already exists. Do useful research now while genuine human reviews are pending; do not restart the project or stop at a generic plan.

## 1. Workspace and evidence

Local project: /Users/divyanshraj/Desktop/Major Project
Private GitHub repository: https://github.com/Divyansh1128/Hinglish
Verified handoff baseline: main, commit ab911cd0017222b96ffbdfe70cb05844d6f7f240, containing 86 project files. This prompt may be added in a later documentation commit; inspect the actual current HEAD.
Context snapshot: 10 October 2026. Record your actual search date and inspect changes since this snapshot.

Read applicable AGENTS.md and these relevant files once:
- README.md and docs/PROJECT_STATUS.md: current status.
- research/closest_work_comparison_2026-10-10.md: prior comparison, source links and evidence gaps.
- research/research_before_coding.md and research/model_selection_plan.md: historical planning.
- pilot_review_packet.md: governing review/pilot definitions and a proposed later training-smoke protocol.
- test1_pilot/README.md, DATA_CONTRACT.md, VERIFICATION.md and GPU_SMOKE.md: implemented software and verification limits.
- research/test1_returned_demo_audit_2026-10-10.md and research/test1_gpu_smoke_audit_2026-10-10/: returned-run audits.
- research/demo_evidence/: original returned demo ZIPs, preserved unchanged.
- pilot/annotation_draft_v1/README.md, verification.json and coordinator/: candidate data and pending review/split metadata.
- research/pilot_annotation_handoff_2026-10-10.md: review handoff.
- docs/teammate_guide.md and output/pdf/Hinglish_Math_Teammate_Guide.pdf: teammate explanation.
- Relevant pilot/scripts, test1_pilot/hinglish_pilot, tests and t4_smoke code when assessing implementation.

Older documents are proposals, not a reliable statement of current completion. Some call English-only training optional or say no GPU inference occurred; the current requirements and returned-run evidence supersede those statements. If you cannot access the private repository/local files, say exactly what is inaccessible, request the minimum necessary material, and continue independent public-source work. Never pretend you inspected unavailable files.

## 2. Research question and controls

E = English input.
R = Hindi phrasing written in Roman script under a documented borrowing policy.
C = Hindi-English code-mixed input written in Roman script, containing productive English clauses/predicates/relations beyond isolated object nouns or permitted borrowings.

Primary eventual question: Does E+C mathematical training add value beyond E+R under matched mathematical content, matched example exposure, and identical English solution supervision?

Essential eventual trained arms:
- E+E: two English exposures of the matched family; do not add extra problem families to match exposure.
- E+R: one English and one Romanized-Hindi exposure.
- E+C: one English and one Roman-script Hinglish exposure.

Start each arm from the same checkpoint. Match underlying families, English examples, complete English solution targets, mixture proportions, exposure, update schedule, adapter settings, checkpoint-selection rule and paired seeds. Matching examples/updates does not match input-token counts; measure tokens and compute rather than claiming those are controlled identically.

Primary estimand: Delta_C = Accuracy(E+C-trained model on C) - Accuracy(E+R-trained model on C), evaluated on the same independent held-out families. Evaluate every arm on E/R/C. A possible secondary specificity contrast is Delta_C - Delta_R; it measures relative specialization, not an internal mechanism. These contrasts are proposed, not measured.

All E/R/C inputs use Roman script. Without a separate native-script Hindi condition, do not claim to isolate romanization relative to Devanagari.

## 3. What has actually been achieved

A. Research scoping
A targeted closest-work comparison covers Anand et al. (Multilingual Mathematical Reasoning), Indi-RomCoM, CodeMixBench, CodeMixTax, XCOT, LinguaLIFT, MathOctopus and Nanda. Its conclusion is “the exact matched E+C versus E+R control was not located in inspected material.” This is not exhaustive novelty clearance, proof of absence, a world-first claim or publication readiness.

Indi-RomCoM is the strongest application overlap; XCOT is the strongest intervention overlap. Code-mixed maths evaluation, bilingual maths training, matched multilingual data and English reasoning targets already have precedents. The contribution must concern the controlled comparison and useful transfer, rather than a new model name/backbone.

B. Complete Test 1 pilot software
test1_pilot/Hinglish_Math_Test1_Pilot_Colab.ipynb is self-contained and runs in fresh Colab without Mac files or an unpublished repository URL. A separate Hinglish_Math_Qwen_GPU_Smoke_Colab.ipynb handles short technical checks. There are maintained helpers, dependency pins, templates, synthetic fixtures, a portable ZIP and versioned v1 archives.

The pipeline implements strict reviewed-data validation; separate demo/reviewed modes; one fresh context per rendering; fixed English instruction; seeded order; full context-length checks without silent question truncation; incremental attempt saving; interruption/resume with hash/configuration checks; one unchanged-configuration infrastructure retry; raw outputs, tokens/latency/memory; exact scoring; family-paired reports; manual audit overlays; and reproducibility ZIP export. Wrong/invalid/refused/truncated answers receive no answer-dependent retry. Unresolved infrastructure failures make a run incomplete; headline comparisons are suppressed.

The original scorer remains version 1.0.0, copied unchanged. It uses safe exact rational arithmetic, terminal FINAL extraction and predeclared units/conversions, not eval(), arbitrary float tolerance or an LLM judge. Manual audit never silently overwrites original automatic scores.

Verification: 29 model-free test methods passed (22 pilot, 3 original scorer, 4 training-smoke protocol). Notebook validation and a fresh-kernel fake demo passed. Annotation checks cover 30/90 coverage, preserved original texts, reference-final scoring, 27 exact unit conversions, four JavaScript syntax checks, 20 checksums and simulated import/export/resume. The complete real-browser annotation workflow remains unverified. These are software checks, not human validation.

C. Returned fake demo
demo-v1_results.zip contains six synthetic outputs from a fake backend. Checksums/fingerprints/scores were audited. Fixture accuracy is software plumbing evidence only.

D. Real Qwen T4 inference smoke
demo-qwen-gpu-v1_results.zip was returned and audited. Six scored-fixture generations plus separate format-only inference succeeded on Tesla T4. No truncation or unresolved infrastructure failure occurred in the six generations. Exported checksums and run fingerprints passed.

Observed model/tokenizer: Qwen/Qwen3-4B, immutable revision 1cfa9a7208912126459214e8b04321603b3df60c.
Condition: NF4 double quantization, FP16 computation, SDPA math backend, thinking disabled, greedy one-beam decoding, batch 1, context cap 2,048, output cap 1,024, seed 11. Greedy decoding is a documented protocol choice differing from model-card sampling advice; cross-stack bitwise determinism is not guaranteed.
Hardware: Tesla T4, approximately 14.56 GiB reported memory (nominal 16 GB).
Observed stack includes Python 3.13.15, torch 2.11.0+cu130, Transformers 4.51.3, bitsandbytes 0.50.2, Accelerate 1.6.0, HF Hub 0.30.2, tokenizers 0.21.1 and safetensors 0.5.3.
Load time: about 224.75 seconds, potentially including downloads. Six generations: about 33.79 seconds total, median 5.36 seconds. Maximum per-generation PyTorch reserved peak: about 4.19 GiB. Lowest endpoint free-memory observation: about 10.21 GiB, not a continuously measured minimum.

Critical scoring diagnosis: the original automatic score is 0/6, all invalid_unit. All six extracted numeric values match fixture gold, a post-hoc technical diagnostic, NOT human-reviewed accuracy. The count fixture incorrectly had a blank canonical unit; demo-v2 repairs its metadata. Three fraction outputs append whole/fraction/part, rejected by the unchanged strict dimensionless policy. One R explanation also drifted into Hindi despite the English instruction. Preserve original archives/scores; do not turn the numeric diagnostic into “100% accuracy,” widen the scorer opportunistically, or call these reviewed research results. The corrected demo has not supplied a new real-GPU research result.

This establishes limited short-input inference feasibility, not full-pilot completion or QLoRA training feasibility.

E. Candidate review materials and team handoff
Thirty AI-authored draft mathematical families / 90 E/R/C texts are prepared, five each in:
comparison_remaining; two_step_money; fractions_percentages; ratios; rates_units; elementary_algebra.
PIL001–005 preserve the original illustrative question texts; 25 new candidates were added. All remain DRAFT/AI_DRAFT. No completed acceptance is supplied.

R01/R02 have separate randomized stage1 solving forms and stage2 triplet-review forms. A01 has a separate proposed key and pending adjudication file. Role IDs are pseudonymous placeholders. The user says two bilingual reviewers and a separate adjudicator are available; this does not mean they completed reviews.

A 12-page teammate guide, editable source and visual/content verification were delivered. Research notes, code, notebooks, draft packets and original demo evidence were pushed to the existing private GitHub repository. Credentials, local caches, personal conversation transcripts and returned personal reviews are excluded.

## 4. What remains uncompleted

- Human independent solutions, accepted dataset, adjudication, frozen borrowing policy and completed split audit.
- The unchanged-model reviewed 30-family/90-prompt pilot.
- Sixteen genuinely separate future training-smoke families and confirmatory training/final-test sets.
- Successful training memory/time/checkpoint-resume feasibility tests.
- Full fine-tuning, RL, confirmatory experiments, training benefits, mechanism findings or publication novelty proof.
- A declared software/dataset release license and any necessary source/release permissions.

Do not relabel drafts, fabricate reviewers/ratings/agreement, treat AI review as human annotation, or count numerical siblings as independent families.

## 5. Use subagents and advance the research

Use up to three subagents concurrently if delegation tools are available. Give them bounded questions and relevant sources, not the entire project repeatedly. You own the integration and must check their claims against evidence. If delegation is unavailable, say so and complete the work yourself; never simulate completed subagent reviews.

Subagent A - closest-work and exact controls
Recheck current primary papers, appendices, official data/code/config releases and backward/forward citations. Prioritize Indi-RomCoM, XCOT and Anand. Reconcile Indi-RomCoM Appendix C.1 versus Table 14 split/intensity descriptions if artifacts allow; do not infer leakage or invalidity from unresolved descriptions. Try to retrieve Anand's previously inaccessible technical appendix. Distinguish code switches in inputs/context/outputs, direct SFT versus multi-stage alignment/distillation, and combined corpora versus separately trained controls. Inspect recent relevant work beyond the old list. Record paper versions, search dates, source URLs and exact section/table/config locators. Classify findings as exact match, partial overlap, not reported in inspected material, or inaccessible/unclear. Use primary sources for substantive technical claims, and a bounded search log/stop rule rather than endless bibliography expansion.

Subagent B - experimental validity and statistics
Consolidate the three trained arms and estimands. Audit matched exposure/full-English targets, family leakage, author/generator-style confounds, checkpoint/seed handling and English retention. Propose independent-author/style/spelling transfer evaluation. Design paired-family uncertainty, seed aggregation and multiplicity rules. Develop sample-size sensitivity scenarios using plausible accuracy/discordance and effect-size assumptions; label all simulations as planning, not observations. A 30-family pilot is descriptive and must not automatically become the final-test sample. Propose, but do not falsely mark approved, a smallest useful C gain and tolerable English degradation. Explain negative, inconclusive, specialization and retention-tradeoff outcomes. Multiple frozen-model baselines are not replication of a training effect.

Subagent C - data review and pilot readiness
Audit candidate family relationships, provenance, borrowing/classification quality and pending review schema. Prioritize PIL002/PIL010 and PIL005/PIL021, without assuming other pairs are independent. Automated similarity flags are evidence for human inspection, not semantic certification. Check actual reviewer exposure: GitHub contains proposed gold in coordinator/A01/historical examples, so repository access is NOT a blind-review firewall. If gold was seen before independent solving, record that honestly and propose a valid replacement-review process, such as unexposed reviewers or new versioned candidates; never retroactively assert solve-before-gold. Preserve exposure disclosures and development exclusions. Review inference/scoring failures and whether the unchanged pilot can answer its intended diagnostic questions.

After these audits, have an available agent critically review the integrated proposal for the strongest paper-reviewer objections. Resolve contradictions explicitly; do not equate subagent agreement with evidence or human approval.

## 6. Synthesize concrete decisions

Produce an updated closest-work matrix including: task/script, data origin, training arms, family matching, full target language/content, exposure/token budget, split unit, seeds, test form, released artifacts, exact-control verdict and our remaining distinction.

Create one authoritative experiment specification. Separate requirements already established, new recommendations, unresolved user/human choices and measured facts. Keep E+E/E+R/E+C essential; make translation and second-backbone replication resource-dependent. A translate-C-to-English-then-solve baseline must produce its own translations and report both stages' errors/cost; it cannot receive our human reference E as an oracle.

Define the staged gates: review/exposure integrity and accepted data -> frozen unchanged-model pilot -> separate bounded training feasibility -> confirmatory design/sample/resource freeze -> controlled training -> untouched evaluation -> paper. The existing proposed six-update training smoke checks completion-only supervision, adapter-only updates, optimizer allocation, finite gradients, memory/time and clean-process checkpoint reload. Successful inference does not satisfy it. Plan its requirements; do not launch training in this phase.

If the exact comparison already exists, document it and recommend a sharper feasible question. Do not rescue novelty simply by changing a backbone. If no exact match is found, defend why the proposed result would still be scientifically useful beyond expected target-distribution adaptation. Do not guarantee a publication venue or positive outcome.

## 7. Preserve the research endpoint

Collect four genuine reviewer JSONs (R01/R02 stage1 and stage2), A01 adjudication, and any repair/re-review records. Repaired questions require new versions/hashes and independent re-review. Freeze accepted data, unit/conversion policy, borrowing policy, prompt, scorer, model configuration and splits before research generation. The strict existing validator must pass unchanged. Draft kind='reviewed' denotes intended execution mode, not completed human acceptance.

Keep every pilot, rejected draft, smoke family and descendant permanently outside later confirmatory training/final test. Do not use model success to decide whether wording is acceptable. Do not tune prompts repeatedly on pilot accuracy or inspect final-test outcomes for model selection.

Report E/R/C numerators/denominators, Wilson intervals, paired E-C/E-R/R-C differences with 10,000 FAMILY-level bootstrap resamples (seed 101), discordant counts, invalid/refusal/truncation rates, tokens/runtime/memory and descriptive small-sample topic breakdowns. Ninety renderings are 30 families, not 90 independent observations. Incomplete runs retain their expected denominator and unmistakable incomplete status; suppress headline comparisons until infrastructure failures are resolved. Audit raw outputs separately and version overlays/rescoring without erasing automatic results. A wide interval around zero is inconclusive, not equivalence.

## 8. Deliverables and authorized scope

Complete the research work you can perform now and save dated/versioned artifacts, preferably:
1. research/astra_closest_work_update_<actual-date>.md
2. research/astra_experiment_spec_v1.md
3. research/astra_validity_and_power_v1.md
4. research/astra_review_readiness_v1.md

Update current status/navigation when warranted, keeping historical artifacts intact. Use meaningful model-free analysis/scripts only where they resolve a design question. Do not rebuild or rewrite the working pilot casually, overwrite human submissions, weaken checks, run training, purchase compute or invoke paid model APIs. This phase authorizes literature research, local document work, static/code review and modest model-free design simulations. If reviewed inputs arrive, inspect them; separate actual GPU execution from this research phase.

Relevant research/documentation updates may be committed and pushed to the existing private GitHub repository when access is available. Preserve existing history, inspect the diff, exclude credentials/personal reviewer data and never force-push or change permissions. Do not send emails/Slack messages or contact paper authors without a separate instruction.

Your final response should state what you verified, what changed from the earlier proposal, what remains uncertain, whether our exact control is already present in the checked work, and the next concrete human action. Support literature claims with primary-source links and locators; distinguish inference from reported facts. Make the first useful result an evidence-based recommendation about our research direction and next gate, then deliver the supporting artifacts. Do not stop with “I can help” or only a task list.
