# Hinglish math: 30-family pilot review packet

Status: DRAFT FOR USER REVIEW. No human annotation, model generation, GPU measurement, or training has been performed. The five examples below are illustrative drafts, with mathematically checked reference answers; they are not validated research data.

Basis: the research report and draft preregistration in this conversation. The local project export contains the initial research brief, rather than separate copies of those two documents. Three subagents reviewed mathematical/language equivalence, evaluation/leakage, and T4 feasibility. Their reviews are technical advice and do not substitute for independent bilingual human validation.

The user has one Colab T4 with 16 GB nominal VRAM and no fixed deadline. GPU fit, speed, session length, and reviewer availability remain unmeasured. Assumption [R]: two independent Hindi-English bilingual reviewers and an adjudicator will be available before accepting pilot items. Assumption [G]: the actual Colab runtime supports the pinned quantization and training stack; verify this on the allocated GPU.

## 1. Purpose and scope

E denotes English input, R Romanized-Hindi input, and C Roman-script Hinglish input. E+R and E+C denote future training mixtures. The unchanged-model pilot evaluates E/R/C inputs and validates the data/scoring process. It cannot establish the E+C versus E+R training effect.

Plan 30 independent evaluation families: five each in comparison/remaining quantities, two-step money, fractions/percentages, ratios, rates/units, and elementary algebra. Select families before seeing model outputs. One family means an underlying authored/source problem and all its translations, paraphrases, spelling variants, and numerical siblings; sharing a common mathematical skill alone does not imply duplication. Do not manufacture 30 independent families by changing numbers in five templates.

After user review and bilingual adjudication, the five illustrations may occupy five of those 30 slots. Rejected drafts and revised descendants retain their provenance and remain reserved for development. The other 25 families have not been authored here.

## 2. Annotation rubric [R]

Both reviewers independently solve the problem before reading the proposed reference solution. Present forms in randomized order, without model outputs or the expected performance hypothesis. Language forms are visible, so reviewers are not blind to the register.

| Dimension | Required judgment | Acceptance rule |
|---|---|---|
| Mathematical content | Compare every quantity, entity, unit, rate, comparison direction, time condition, requested unknown, and explicit assumption across E/R/C. | All checks pass; fluency alone is insufficient. |
| Independent solution | Record an equation, reasoning, answer, and unit independently. Allow algebraically equivalent setups. | Both independently obtained answers match the adjudicated gold. |
| Ambiguity | Check pronouns, fraction base, ratio order, discount order, counts versus money, and omitted physical conditions. | No unresolved interpretation changes the answer. |
| R classification | Hindi phrasing in Roman script, without substantive English phrases/clauses. Use a frozen common-borrowing policy. | Pass; avoid forcing unnatural Sanskritized replacements merely to remove loanwords. |
| C classification | Contains a productive English predicate, clause, or mathematical relational phrase alongside Hindi, beyond names, units, and the permitted borrowing list. | Pass; English object nouns alone do not qualify. |
| Naturalness | 1 = difficult to understand; 2 = understandable with awkward translation; 3 = grammatical but conspicuously unnatural; 4 = plausible everyday educational wording; 5 = fluent and idiomatic. | Each reviewer rates each form at least 4 after any repair. |
| Roman readability | 1 = largely unreadable; 2 = substantial effort; 3 = understandable with repairs; 4 = readily readable; 5 = immediately clear. | Each reviewer rates R/C at least 4 after any repair. |
| Surface controls | Numerals, entities, units, punctuation conventions, and solution targets are documented. Record differences in phrasing and length. | Differences are intentional, recorded, and do not change the mathematics. |

Permitted shared symbols and conventional terms initially include Arabic digits, INR/rupee notation, L, m, minute, metre, and litre; review and freeze this list before classifying items. A borrowing's historical English origin is insufficient to label it a code switch. Record productive English spans and their roles: incidental object/entity, quantity, comparison, rate, operation, negation, or requested answer. Mixing percentage is descriptive and is not a naturalness criterion.

Review dispositions: ACCEPT, REVISE, EXCLUDE. Repaired items receive a new version and independent re-review. Freeze accepted text and reference answers before generation. Keep first-pass ratings and disagreements. Report raw agreement, adjudication counts, and rating distributions; 30 families are too few for stable agreement claims by topic. If reviewers are unavailable, retain DRAFT status and withhold data-validity approval for scaling.

## 3. Sheet schema

This specifies workbook tabs; no spreadsheet or 30-family dataset has been generated. Use stable IDs and controlled vocabularies, and do not overwrite earlier versions.

| Tab and row unit | Required fields |
|---|---|
| families: one row per family | family_id, source_family_id, template_group_id, split_role, topic, operation_count, authoring_origin, provenance, source_url_or_record, source_license, original_creation_date, version, reference_equation, reference_solution_en, gold_type, gold_exact, gold_unit, unit_omission_allowed, allowed_conversions, rounding_rule, status, exclusion_reason |
| renderings: one row per family x E/R/C x version | rendering_id, family_id, form, text, creator_type, generation_or_edit_history, Hindi_spans, English_spans, permitted_borrowings, switching_roles, romanization_notes, raw_character_count, formatted_prompt_tokens, formatted_training_tokens, supervised_target_tokens, text_hash |
| reviews: one row per reviewer x rendering version | reviewer_id, rendering_id, independent_equation, independent_answer, independent_unit, semantic_checks, ambiguity_flag, form_classification, naturalness_1_to_5, readability_1_to_5, disposition, issue_notes, adjudicator_id, adjudication, reviewed_at |
| leakage: one row per inspected cross-split match | family_id_a, family_id_b_or_external_source, match_method, normalized_exact_match, near_duplicate_evidence, mathematical_family_relationship, reviewer_decision, action, audit_version |
| baseline_runs: one row per generation attempt | run_id, rendering_id, model_revision, tokenizer_revision, prompt_version, quantization, attention_backend, thinking_mode, decoding_settings, output_cap, seed, attempt_id, retry_reason, raw_response, extracted_final, normalized_value, normalized_unit, correct, invalid_reason, refusal, truncated, infrastructure_failure, manual_score, scorer_version, input_tokens, output_tokens, latency_seconds, peak_GPU_allocated_GiB, peak_GPU_reserved_GiB, minimum_device_free_GiB |
| hardware_runs: one row per arm/test phase | hardware_run_id, arm, smoke_data_version, GPU_identity, total_device_GiB, software_versions, trainable_parameter_count, optimizer_parameter_count, adapter_dtype, quantization_config, sequence_length, effective_batch, successful_updates, attempted_updates, scaler_skips, phase, wall_seconds, load_seconds, update_durations_seconds, padded_positions, nonpadding_tokens, supervised_tokens, GPU_peak_allocated_GiB, GPU_peak_reserved_GiB, device_peak_used_GiB, device_min_free_GiB, host_RSS_peak_GiB, host_available_min_GiB, loss_and_gradient_checks, checkpoint_bytes, save_reload_seconds, resume_checks, OOM_or_failure, outcome |

split_role is PILOT_EVAL, SMOKE_TRAIN, or RETIRED_DRAFT. Keep future CONFIRM_TRAIN and FINAL_TEST IDs in separate manifests. creator_type must identify these five initial examples as AI_DRAFT, with subsequent human edits recorded. Human review does not erase their origin.

## 4. Five illustrative families for review

All wording remains provisional. Gold values below were calculated independently of any model output. Units omitted from a final answer may be accepted only when the question already fixes the requested quantity; an explicitly wrong unit is rejected.

### PIL001: comparison direction

- E: Riya has 36 marbles. Aman has 5 fewer marbles than Riya. How many marbles does Aman have?
- R: Riya ke paas 36 kanche hain. Aman ke paas Riya se 5 kam kanche hain. Aman ke paas kitne kanche hain?
- C: Riya ke paas 36 marbles hain. Aman has 5 fewer marbles than Riya. Aman ke paas kitne marbles hain?
- Equation/gold: 36 - 5 = 31 marbles.
- Shared English solution: Aman has 5 fewer marbles than Riya, so 36 - 5 = 31. FINAL: 31 marbles
- Review focus: preserve the comparison's subject and direction. The C English clause carries the mathematical relationship; mark that switching role.

### PIL002: unit price and change

- E: Meena buys 5 notebooks at INR 24 each. She pays the shopkeeper INR 150. How much change should she receive?
- R: Meena ne 5 kaapiyan khareedin. Har kaapi ki keemat INR 24 hai. Usne dukandaar ko INR 150 diye. Use kitne rupaye vaapas milne chahiye?
- C: Meena ne 5 notebooks khareedin; each costs INR 24. Usne shopkeeper ko INR 150 diye. Use kitna change milna chahiye?
- Equation/gold: 150 - (5 x 24) = INR 30.
- Shared English solution: The notebooks cost 5 x 24 = INR 120. The change is 150 - 120 = INR 30. FINAL: INR 30
- Review focus: each notebook costs INR 24, rather than all five together; requested answer is change, rather than purchase cost.

### PIL003: constant rate and initial amount

- E: A tank initially contains 20 L of water. Water is added at 3 L per minute for 4 minutes. No water leaves the tank, and it has enough capacity. How many litres of water are in the tank at the end?
- R: Ek tanki mein pehle se 20 L paani hai. Usmein 4 minute tak har minute 3 L paani dala jaata hai. Koi paani bahar nahi nikalta aur tanki mein is paani ke liye kaafi jagah hai. Aakhir mein tanki mein kul kitne litre paani hoga?
- C: Ek tank mein pehle se 20 L paani hai. Water is added at 3 L per minute for 4 minutes. Koi paani bahar nahi nikalta aur tank mein enough space hai. Aakhir mein total kitne litres paani hoga?
- Equation/gold: 20 + (3 x 4) = 32 L.
- Shared English solution: Adding water for 4 minutes adds 3 x 4 = 12 L. The total is 20 + 12 = 32 L. FINAL: 32 L
- Review focus: filling continues for the full interval; no outflow or overflow changes the result. Decide how minute/litre are treated in the borrowing policy.

### PIL004: fraction of the original length

- E: A ribbon is 24 m long. Three-eighths (3/8) of its original length is cut off. What length of ribbon remains, in metres?
- R: Ek feete ki lambai 24 m hai. Uski shuruaati lambai ka 3/8 hissa kaat diya gaya. Bache hue feete ki lambai kitne metre hai?
- C: Ek ribbon ki length 24 m hai. Uski original length ka 3/8 hissa cut kar diya gaya. Ribbon ki remaining length kitne metres hai?
- Equation/gold: 24 x (1 - 3/8) = 15 m.
- Shared English solution: The removed length is 24 x 3/8 = 9 m. The remaining length is 24 - 9 = 15 m. FINAL: 15 m
- Review focus: the removed fraction refers to original length, and the question asks for the remainder. Ask reviewers whether the final R/C sentences need a more natural phrasing.

### PIL005: ordered ratio

- E: A bag contains only red and blue marbles. The ratio of red marbles to blue marbles is 2:3. There are 30 marbles in total. How many red marbles are there?
- R: Ek thaili mein sirf laal aur neele kanche hain. Laal aur neele kanchon ki sankhya ka anupaat 2:3 hai. Kul 30 kanche hain. Laal kanche kitne hain?
- C: Ek bag mein sirf red aur blue marbles hain. Red to blue ratio 2:3 hai aur total 30 marbles hain. Red marbles kitne hain?
- Equation/gold: 30 x 2/(2 + 3) = 12 red marbles.
- Shared English solution: There are 2 + 3 = 5 ratio parts. Each part is 30/5 = 6 marbles, so there are 2 x 6 = 12 red marbles. FINAL: 12 marbles
- Review focus: red:blue order, exactly two colours, and naturalness of formal Hindi anupaat versus the English phrase.

These examples deliberately use different switching roles. They do not support an isolated causal conclusion about switching location. The AI equivalence review found the gold calculations correct and suggested explicit tank capacity and clearer ribbon wording; the revisions above still require human review.

## 5. Split firewall

Maintain a permanent development exclusion manifest covering these five drafts, all 30 PILOT_EVAL families, the separate SMOKE_TRAIN families, and every descendant or related version. Exclude these from future FINAL_TEST and CONFIRM_TRAIN. The final test will be authored/selected separately, without using observed pilot failures as test-selection criteria.

Use licensed, independently identified training-only sources for smoke records; do not source them from public benchmark test splits. Audit source IDs, normalized text, semantic near-matches, and mathematical-family relationships. This reduces observed overlap; it cannot certify that a pretrained model never saw a similar problem.

## 6. Unchanged-model baseline protocol [G, R]

Before generation, freeze 30 accepted families, all 90 E/R/C renderings, the reference answers, output rubric, prompt, scorer test cases, and hashes.

- Model: Qwen/Qwen3-4B, with exact immutable model/tokenizer revisions and software versions recorded. No LoRA adapters or weight updates. NF4 4-bit quantization, double quantization, FP16 computation; this is a fixed quantized baseline, not BF16 evaluation.
- Hardware: one T4, batch 1; record actual total/free memory and selected T4-compatible attention backend. Disable thinking through the chat template's enable_thinking=False setting. Disable sampling; fix seed 11, output cap 1,024 tokens, and EOS policy. Greedy decoding is the pilot's controlled choice.
- Instruction, unchanged across conditions: Solve the problem. Give a short explanation in English. End with exactly one line: FINAL: <number or fraction> <unit when applicable>.
- No demonstrations, translation pipeline, retrieval, tools, or sibling renderings in context. Fresh context for each input; interleave forms in a fixed seeded order. Keep the baseline checkpoint isolated from smoke checkpoints.
- Workload: exactly 30 families x 3 forms = 90 scored outputs. Record model-load time separately from generation latency. Record prompt tokens, generated tokens, finish reason, and per-generation memory peaks.
- Genuine infrastructure errors may be retried with the same configuration at most once, with both attempts logged. Wrong mathematics, refusal, malformed output, or model token-limit termination receive no answer-dependent retry. Unresolved infrastructure errors produce an incomplete run; preserve the denominator and report them explicitly.

Scoring: require one unambiguous FINAL field. Parse integers, fractions, and terminating decimals exactly as rationals; check valid units and predeclared conversions. No blanket epsilon. Missing, duplicate/contradictory, unparseable, refused, or token-limit-terminated answers count incorrect under the frozen pilot endpoint. Record human semantic correctness separately to diagnose formatting confounds; do not silently substitute it after looking at scores.

Before generation, specify at least 40 synthetic answer-only scorer cases, balanced between accepts and rejects. Include equivalent fractions/decimals, correct/incorrect units, permitted omitted units, wrong signs, wrong answers present only in reasoning, malformed numeric grouping, duplicate finals, missing finals, and refusals. Require zero false accepts/rejects on that fixed suite. Independently audit all 90 generated responses; resolve scorer bugs, version the scorer, and rescore stored responses consistently.

Report correct/n out of 30 for E/R/C with 95% Wilson intervals, invalid/refusal/truncation counts, and paired E-to-C and R-to-C correctness tables (both correct, E/R-only correct, C-only correct, neither). Use 10,000 paired family bootstrap resamples with seed 101 for descriptive intervals on accuracy differences. Pilot intervals and counts are descriptive; 30 families cannot establish the SFT effect or reliably determine final-study power. Low accuracy alone is not a stop condition.

## 7. Bounded QLoRA memory/time test [G]

This section specifies a future operational test; it does not launch it. Reserve 16 distinct SMOKE_TRAIN families outside PILOT_EVAL. Give each family one English and one R/C record per arm, with exactly the same English completion. Repeat the resulting 32 records three times per arm: 96 microsteps per arm.

Preflight: log GPU identity, actual VRAM, CPU RAM, CUDA/framework/Transformers/PEFT/quantization versions, attention backend, model/tokenizer revisions, quantized-module types, trainable adapter count, optimizer membership, parameter dtypes, and cache/checkpointing settings. A T4 lacks native BF16 support; do not assume the standard CUDA FlashAttention-2 backend works. Use a verified compatible backend identically in both arms.

Recipe: NF4 + double quantization, FP16 base computation, FP32 adapters/AdamW states where supported; LoRA rank 16, alpha 32, dropout .05 on q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj. Gradient checkpointing, training KV cache disabled, sequence 1,024, fixed right padding, no packing, microbatch 1, accumulation 16, completion-only loss. AdamW lr 1e-4, betas (.9,.999), epsilon 1e-8, weight decay 0, clip 1, dynamic FP16 loss scaling. For this short operational test use constant LR; its first two updates are measurement warm-up, not the future recipe's eight-step LR warm-up.

Verify identical supervised target token IDs including EOS policy for paired records. Prompts and padding must contribute zero loss after causal shifting; no target may be empty or truncated. Jointly reject or replace overlength families. Check every base parameter is frozen and every optimizer parameter is an adapter parameter. Use the same example order and initialization seed 11 in fresh processes for both arms.

Per arm: allow at most 30 minutes excluding dependency/model downloads but including loading, checks, save/reload, and training. Run two successful warm-up optimizer updates and four timed successful updates, each consisting of 16 microsteps. The first optimizer update must allocate optimizer states; a forward-only fit check is insufficient. Total per arm is six updates, 96 microsteps, and 98,304 padded token positions; the four timed updates cover 65,536 padded positions. Log attempted/skipped updates separately. Any OOM, nonfinite loss/gradient, or incomplete workload is a failed/unfinished test, not evidence of feasibility.

After timed update 2, save adapters, optimizer, scaler, RNG, data cursor, scheduler/test-config state, and successful-update count. End the process and reload a clean quantized base plus the saved training state. Complete timed updates 3 and 4. Record cold-resume duration separately, and include reload in the 30-minute cap. Check saved tensor/state equality and a fixed evaluation-mode probe before/after reload; prerecord atol=rtol=1e-3 for probe-loss agreement. Restore checkpoint RNG after the probe so it does not alter the resumed training stream.

Measure synchronized durations for every update, first-update overhead, median/range of timed updates, and resume-update time separately. Measure peak allocated and reserved GPU memory, device-wide maximum used/minimum free memory, host-process RSS peak, and minimum available host RAM. Report throughput separately for padded token positions, actual nonpadding tokens, and supervised completion tokens; record padding percentage. Include both arms, since their true token lengths can differ despite identical padded shapes.

Verify finite losses/gradients/weights, zero skipped timed updates, nonzero adapter updates, frozen base/optimizer membership, and successful checkpoint restore. Do not score the trained smoke adapters on PILOT_EVAL or compare six-update answer accuracy.

## 8. Measurements and decisions before scaling

| Gate | Required evidence | Decision rule |
|---|---|---|
| Human data validity [R] | 30 independent accepted families, 90 reviewed forms, independent gold solutions, treatment labels, naturalness/readability ratings and adjudication trail. | Zero unresolved math, treatment, or ambiguity defects; otherwise repair and re-review. |
| Split integrity | Source IDs, provenance and permanent development-exclusion manifest; resolved cross-split match audit. | Zero unresolved family overlaps with confirmatory data. |
| Scorer correctness | Fixed answer-only suite and independent review of all 90 responses; false-accept/reject and format-versus-semantic discrepancies. | Zero unresolved scorer defects; rescore stored outputs after versioned corrections. |
| Baseline completion | 90 generation records, all failure reasons, per-form correct/30, paired tables, invalid/refusal/truncation rates, token/memory/latency measurements. | Zero unresolved infrastructure failures. If more than 3/90 outputs are invalid or truncated, revise output handling/cap before a frozen study; label repeated pilot results as development. Accuracy is not a gate. |
| T4 memory [G] | Both full short-test runs including optimizer allocation and resume, maximum device use and minimum free memory, host RAM. | No OOM and at least 2 GiB device headroom throughout; this is a chosen engineering margin, not a hardware guarantee. |
| Training integrity [G] | Correct supervision masks, finite successful updates, adapter-only optimizer membership, checkpoint/reload and probe checks. | Both arms pass; any silent truncation, nonfinite timed step, or incorrect resume blocks scaling. |
| Time and session budget [G] | Update-time distributions, load/save/reload costs, downloads, wall times and actual interruption behavior. | Both tests finish within the bound. Decide whether the six-run budget is affordable and whether checkpoint/resume is practical before reserving training. |
| Scientific scaling | Reviewer capacity, revised item count/power design, frozen settings, confirmatory manifests. | Make and document the full-study decision without using the 30-family pilot as confirmatory evidence. |

For the draft full recipe, each arm/seed has 256 optimizer updates; two arms x three seeds require 1,536 updates. Forecast training hours as 3 x 256 x (median_C_update_seconds + median_R_update_seconds) / 3,600, plus measured loading/checkpoint costs and a declared safety margin. This is a projection from a short test; do not report it as a measured full-run duration. Add annotation and final-evaluation costs separately.

If 1,024-token tests fail, a 512-token test or smaller model is a new version of the design. Run the same changed configuration in both arms, confirm all complete targets still fit, and amend the preregistration before confirmatory training. Hardware adjustments must not be selected by comparing final-test accuracy.

User review now: wording/naturalness of these five families, the common-borrowing policy, and availability of independent bilingual reviewers. After that, complete/adjudicate the 30-family sheet, freeze it, run the unchanged-model baseline, and run the separate bounded hardware test. Full training remains outside this review packet's execution scope.

## Primary technical references

- Qwen3-4B official model card: https://huggingface.co/Qwen/Qwen3-4B
- NVIDIA T4 datasheet: https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/tesla-t4/t4-tensor-core-datasheet-951643.pdf
- Hugging Face bitsandbytes quantization documentation: https://huggingface.co/docs/transformers/quantization/bitsandbytes
- PyTorch CUDA memory/timing notes: https://docs.pytorch.org/docs/stable/notes/cuda.html

These references establish mechanisms and documented capabilities; no source guarantees the proposed workload will fit or meet the time limit on the user's runtime.
