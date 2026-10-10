# Authoritative experiment specification v1

Dated 10 October 2026. **Design proposal, not a preregistration or experimental result.** This consolidates current requirements; historical plans remain intact. New recommendations below await human decisions and feasibility evidence. No training or new inference was performed in this research phase.

## Direction and next gate

Continue the matched **E+E / E+R / E+C** comparison provisionally. The bounded [updated literature audit](astra_closest_work_update_2026-10-10.md) did not locate the core matched E+R/E+C constant-English-target comparison. Missing seed replication or reporting detail alone would not make an existing core comparison novel. English solution supervision, bilingual mathematical adaptation and Romanized mathematical training have precedents. The contribution must be a useful estimate of transfer beyond the training author's style, with English retention and honest uncertainty. It cannot rest on a new backbone or a claim that code mixing itself is new.

The immediate gate is exposure disclosures, genuine independent human review, adjudication and accepted pilot inputs. Additional bibliography expansion should not indefinitely delay that gate. The 30-family pilot diagnoses the unchanged model and pipeline; it cannot estimate a training benefit.

## Status and decision authority

| Status | Content |
| --- | --- |
| Established requirements | Three trained arms; identical full English targets; matched families/exposure/update policy; separate family splits; original automatic scores preserved; no answer-dependent retries |
| Measured evidence | Model-free software verification and six synthetic T4 generations; original automatic 0/6 invalid-unit scores; no reviewed research accuracy |
| New recommendations | Independent-author held-out E/R/C; fixed-update checkpoint selection; three paired training seeds as an initial resource proposal; family-conditional uncertainty plus seed-specific effects |
| Human decisions pending | Borrowing policy, acceptance/lineage/exposure adjudication, useful effect and retention margins, annotation/GPU budget, final sample size, training stack and release permissions |

The [review-readiness audit](astra_review_readiness_v1.md) is automated research assistance, not human acceptance. Its companion JSON contains proposed gold and belongs with coordinator materials, not blind stage1 review.

## Intervention and estimands

E is English; R is Hindi phrasing in Roman script under the frozen borrowing policy; C is Roman-script Hindi-English mixing with productive English clauses or relations. All three use Roman script. There is no Devanagari contrast and no identification of romanization itself.

| Arm | One matched exposure cycle per family | Completion |
| --- | --- | --- |
| E+E | The same E rendering twice | The same complete English solution twice |
| E+R | E once, R once | The same complete English solution twice |
| E+C | E once, C once | The same complete English solution twice |

Do not supply extra English families or a second English paraphrase in E+E. Each paired seed starts from the same immutable base checkpoint, fresh adapter and optimizer. Match family order, exposure schedule, mixture proportions, effective batch, adapter settings, optimizer, learning-rate schedule, update count and checkpoint-selection rule. Pair seed values across arms; log actual initialization and data-order seeds. Equal examples and updates do not equalize input tokens, throughput or compute: measure all three.

Keep full target strings identical across renderings and verify target token IDs in the actual chat encoding. Use completion-only loss with prompt/padding labels ignored, and explicitly verify the causal-shift boundary and intended EOS supervision. Declare the loss reduction and accumulation weighting; identical targets alone do not prove identical weighting. Start without packing. Check every full input-plus-target sequence before training; no silent truncation of questions or targets. Resolve an overlength family jointly across arms before freeze, recording exclusion or versioned repair.

Primary estimand: mean C accuracy of E+C minus mean C accuracy of E+R, averaging families and paired seeds equally. Evaluate all arms on the same E/R/C held-out families. English retention compares E+C against E+E on E; also report E+R versus E+E. The secondary specificity contrast Delta_C minus Delta_R describes relative specialization, not an internal mechanism. The treatment includes vocabulary, tokenization, accessibility and length changes under a rendering policy; it does not isolate switching independently of those properties.

## Data and transfer

Maintain separate family ledgers for pilot/development exclusions, future training-smoke data, confirmatory TRAIN, checkpoint-selection DEV if used, and untouched FINAL_TEST. Translations, paraphrases, spelling variants and numerical siblings inherit family ancestry. Distinct IDs do not prove independence; sharing a broad mathematical skill does not automatically imply the same family. Human lineage adjudication must use construction history and mathematical structure.

All pilot candidates, rejected drafts, smoke fixtures and descendants remain excluded from confirmatory TRAIN and FINAL_TEST. Sixteen future training-smoke families still need to be constructed and reviewed; existing format fixtures do not constitute that set. No accepted confirmatory dataset exists.

Recommend authoring held-out mathematical specifications and E/R/C texts independently of the training author/generator, with reviewers blind to model outputs. Make one accepted triplet per family the primary test. Additional spelling/style variants are within-family secondary measurements, never extra independent problems. Freeze their weights and scoring before evaluation. If only familiar synthetic style improves, the conclusion is specialization; independent-author transfer is the stronger test of practical value.

Before pilot acceptance, prioritize PIL002/PIL010 and PIL005/PIL021 lineage review, while auditing all pairs. PIL026-C adds a verbal restatement of the equation absent in E/R: humans should resolve this possible scaffolding difference with a new version and independent re-review. Audit R naturalness/borrowings and scalar ratio conventions; do not adjust wording based on model success.

Collect actual gold-exposure disclosures. Repository access is not proof of exposure or a blind-review barrier. A reviewer who saw an item's gold before solving cannot attest solve-before-gold for that item. Use eligible unexposed reviewers or new independently reviewed candidates when needed; retain exposed responses with their true status. Collect R01 and R02 stage1/stage2 JSONs, A01 adjudication and repair/re-review records. Preserve pseudonymous attribution, raw first decisions and real timestamps. The existing strict validator must pass unchanged. Record source/license permissions before release.

## Frozen unchanged-model pilot

Use the working Test 1 notebook after all 30 families are accepted: five per specified topic, three renderings each, 90 prompts. Freeze dataset, borrowing/unit policies, splits, prompt, scorer and configuration before generation. Keep Qwen3-4B model/tokenizer revision `1cfa9a7208912126459214e8b04321603b3df60c`, NF4 double quantization, FP16, SDPA math, thinking disabled, greedy one-beam decoding, batch one, seed 11, context cap 2048 and output cap 1024 unless a **new explicitly versioned protocol** is adopted before the run. Preflight each prompt plus the full output allowance.

The [official Qwen model card](https://huggingface.co/Qwen/Qwen3-4B) recommends sampling settings for non-thinking operation; greedy decoding is our recorded protocol choice. Current documentation is not permission to silently upgrade a saved run's dependencies or configuration. Cross-stack bitwise determinism is not guaranteed.

Retain fresh context per rendering, saved seeded order, incremental attempts, immutable fingerprints and one unchanged-configuration infrastructure retry. Invalid/missing/refused/ambiguous/truncated outputs count incorrect. Unresolved infrastructure failures make the run incomplete; suppress headline comparisons. Preserve original automatic scores and version manual overlays. Diagnose mathematical content and English-explanation compliance separately; neither silently replaces the strict scoring endpoint.

Report E/R/C numerators/denominators and Wilson intervals; paired E-C, E-R and R-C differences with 10,000 family bootstrap draws, seed 101; discordant counts; invalid/refusal/truncation rates; tokens, latency and scoped memory measurements. Topic results are descriptive. Ninety renderings represent 30 families. Keep the implemented pooled-family pilot bootstrap unchanged.

Inspect all invalid answers, truncations and unexpectedly uniform performance before moving on. Any protocol repair requires a new version, explicit rationale and retention of the original run. Do not repeatedly optimize prompts on pilot accuracy. Pilot difficulty informs construction criteria for future data before final-test outcomes are seen; do not select final items by observed model correctness.

## Confirmatory uncertainty and sample planning

See [validity and power analysis](astra_validity_and_power_v1.md) and its reproducible [planning code](astra_power/README.md). All sensitivity scenarios are assumptions, not observations from our models.

For illustration, a single fixed checkpoint pair with 20% discordance and a true five-percentage-point gain has approximately 2.9%, 44.6% and 76.0% positive-direction exact-test power at 30, 300 and 600 families respectively. These calculations are not power for the proposed multiseed estimator. Thirty pilot families must not automatically become the final sample. Final sample/resource freeze needs realistic discordance, target effect, feasible annotation and a specified inferential procedure.

For confirmatory point estimates average seeds equally, retaining matched family vectors across all arms/forms/seeds. Recommend a family bootstrap conditional on the fitted checkpoints; if the target is an equal-topic population, resample within topic under frozen weights. This future recommendation does not change the pilot implementation. Report every paired seed's effect and range. Three seeds give weak information about training-process variation; family bootstrap intervals do not cover that source automatically. Crossed family/seed resampling is a sensitivity analysis with so few seeds. Do not pool seeds as independent families or apply ordinary Wilson intervals to fractional seed averages. Wilson intervals remain appropriate for each single-checkpoint binary family outcome.

Recommend one primary Delta_C comparison. Treat other comparisons as descriptive unless a multiplicity procedure is frozen in advance. Any formal test for the seed-averaged endpoint still needs explicit assumptions and calibration; the single-pair McNemar planning calculation does not supply that test. Do not increase samples until a desired significance result appears.

A useful C gain of +5 percentage points and tolerable English loss of 2 points are **proposed discussion values, not approved thresholds**. Detecting a gain above zero does not establish a gain above five points. Failure to detect English degradation does not establish retention/noninferiority. A tight two-point retention margin may require substantially more families than detecting a C gain; budget it before committing to the claim. A wide interval is inconclusive, not equivalence. A precise null, specialization, negative effect or retention tradeoff can be informative without guaranteeing publication.

## Training feasibility and resource gate — not launched

Successful T4 inference does not establish training fit. Retain the separate bounded six-update smoke concept: completion-only masks, adapter-only updates, optimizer allocation, finite loss/gradients, timings, memory and clean-process checkpoint/optimizer/scaler/RNG reload. Existing protocol code is preparatory, not an implemented successful training runner. Recommend covering E+E as well as E+R/E+C when operationalizing the three-arm recipe; otherwise document exactly which common operations are tested and what E+E checks remain.

The historical proposal uses two warm-up and four timed updates, checkpoint after update four and a clean-process reload for the last two; sequence cap 1024, microbatch one, accumulation 16, no packing, and six-update bounded runs. Its headroom/time thresholds are engineering proposals, not observed results. Monitor whole-device memory over time as well as PyTorch peaks; endpoint free-memory readings cannot certify a continuous minimum. Check restored states and a fixed probe under predefined numerical tolerances. Freeze and test a compatible training stack separately from the verified inference stack.

[PEFT quantization guidance](https://huggingface.co/docs/peft/developer_guides/quantization) documents preparation for quantized adapter training. [TRL SFT documentation](https://huggingface.co/docs/trl/sft_trainer) documents completion-only supervision and length handling; current API defaults and template behavior must be verified against the chosen pinned versions. A library option is not proof that our masks are correct. Neither source establishes our T4 feasibility.

Three arms × three seeds × a proposed 256 updates means **2304 updates**, superseding the old two-arm 1536 estimate. The 256-update schedule itself remains provisional. If measured per-update times are t_EE, t_ER and t_EC seconds, training time is approximately 3 × 256 × (t_EE+t_ER+t_EC)/3600 hours plus loading, validation, save/reload and interruption overhead. Do not extrapolate training cost from six toy inference outputs.

Nine trained checkpoints plus one unchanged baseline evaluated on three forms require **30N generations** for N canonical held-out families. One additional C variant across those ten checkpoints adds 10N. A single translate-then-solve baseline adds two calls per C item and must generate its own translation, never consume reference E as an oracle. These counts omit separate development/pilot runs. Translation and a second backbone are optional resource-dependent extensions; frozen-model sweeps do not replicate a training effect.

Prefer a fixed, common update checkpoint to avoid asymmetric selection. If validation-based selection is necessary, freeze the same criterion and independent DEV family set for all arms, with no final-test inspection. Record total example/target/input tokens, wall time, failures and all attempted seeds, including unsuccessful runs.

## Stage gates and outcome decisions

1. Exposure integrity, accepted human data and frozen pilot policies.
2. Complete unchanged-model pilot, audited scoring/failure/difficulty evidence.
3. Separate reviewed smoke data and bounded training feasibility, including reload correctness.
4. Confirmatory family/sample/seed/resource/analysis freeze and source permissions.
5. Controlled training under the common recipe.
6. Untouched held-out evaluation, versioned audits and paired analysis.
7. Paper with bounded novelty claims, failures, limitations and reproducible artifacts.

If the exact comparison is later found, revise the question around a substantive missing transfer/control condition; changing only the backbone is insufficient. If annotation/compute cannot support the intended effect/retention claim, narrow the claim and declare a descriptive study before outcomes. No gate is satisfied by AI agreement or a draft's intended `kind='reviewed'` flag.

**Next concrete human action:** establish each reviewer's gold exposure, then complete independent review and adjudication of the draft families, including the flagged wording/lineage issues. Return the four reviewer JSONs plus adjudication and repair records. Full training remains outside this phase.
