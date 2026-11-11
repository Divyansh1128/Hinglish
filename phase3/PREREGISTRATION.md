# Phase-3 self-distilled-target study (E+E / E+R / E+C): pre-registered analysis plan

Drafted 11 November 2026 by **Astra (research)**, after Phase-2 results and its exploratory analysis and failure audit. **Adopted 12 November 2026 by Claude under the user's delegation D017 (decision D053), with the changes listed in "Adoption changes" below, before any Phase-3 output exists** (no target generation, training, DEV or FINAL_TEST generation). The user instructed "go ahead with phase 3". This is an AI design decision under delegation, not human adjudication. Hashes of future artifacts are not claimed. Later changes before the relevant outputs exist are dated amendments; changes after are post hoc.

**Adoption changes (Claude, 12 Nov 2026), resolving the four issues raised in `DESIGN.md` §6:**
1. *Intervention definition.* The treatment is **targets in the unchanged model's own visible style** (self-distillation), not "explanation-rich" targets. No explanation-richness or length gate is added; explanation status is recorded descriptively only (§3). If the accepted targets turn out terse, that is reported as a property of the treatment, not repaired.
2. *No fallback teacher.* The Claude-written fallback is removed. If fewer than 120 families qualify, the study **halts before training** and any continuation requires a dated amendment (§3.6). Mixed-teacher targets are therefore impossible under this registration.
3. *Language gate.* Human review of all 160 candidates is replaced by a fixed automatic rule with human review of flagged candidates only (§3.3).
4. *Filtered exposure* (§4) and *test reuse* (§1) are adopted as drafted.

Basis: `phase2/PREREGISTRATION.md`, **including Amendments 1–3**, D040–D052, the Phase-2 final-test report, exploratory README, audit README and report chapter. This is a separate follow-up, not a repair or re-analysis of Phase 2. Its Harm result, −4.33 pp [−8.00, −0.67], remains unchanged. The new question is whether E+C beats E+R on held-out C under a recipe using the unchanged model's own English solution outputs as targets. “Own reasoning style” refers to visible, non-thinking explanations, not access to latent reasoning.

E = English; R = Romanized Hindi with the frozen borrowing list; C = insertional Roman-script Hinglish (D033). All question renderings remain frozen.

## 1. Data and prior exposure

| Role | File | Families | SHA-256 |
|---|---|---:|---|
| TRAIN | `phase2/train_A.v2.json` | 80 | `b9656a8c41af2a795bce9c131efc6a5efc652df78368d14fb7720fd985883666` |
| TRAIN | `phase2/train_B.v2.json` | 80 | `c975fe12459df6160effc5aeb0087f94666ba0b49778c3d827a67bb923ff35bd` |
| DEV (sanity only) | `phase2/dev.v2.json` | 40 | `e741c1652f5b3dcaebc78d9dd9d7c31fdf4417306fbb2f0862149f27f858f28b` |
| FINAL_TEST (reused) | `phase2/final_test.v3.json` | 100 | `da89dd9a626e438dffca39e3a74c4c8abac6bb57501495723b87e6ee143f3d46` |

Every entry point verifies its authorized inputs and stops on mismatch. TRAIN alone supplies targets and family selection; DEV and FINAL_TEST never enter target-generation inputs, language review or target-selection code. Pilot, Pilot-B and FMT2 remain excluded from study training/evaluation. Disjointness checks use the existing split identities; development fixtures must not parse or embed FINAL_TEST.

FINAL_TEST was already used once in Phase 2 (ten checkpoints, 3,000 outputs), and its aggregate results, exploratory summaries and item-level audit observations already exist. The Phase-3 design is motivated by those results. It is held out from **training**, not a fresh, unseen confirmatory set. Existing construction exposure, the FT057 exception and the unattended CPU-test access deviation in Phase-2 Amendments 2–3 remain disclosed. No new semantic inspection of FINAL_TEST or its item-level outputs is permitted from adoption until the new adapter freeze; isolated byte hashing is allowed. This draft used the requested reports, including their already published audit observations, rather than reopening the test JSON semantically.

Reuse is acceptable for a resource-constrained, prospectively fixed follow-up on this benchmark: training families are disjoint; no item-specific fixes, gold/alias changes or selection by test items are allowed; all arms receive matched content and targets. It does **not** restore independence from design selection based on Phase 2. Report the primary as a pre-specified follow-up on a reused test set; its intervals do not account for that adaptive design choice. Fresh held-out replication would be stronger evidence.

## 2. Backbone and execution stack

- Qwen/Qwen3-4B; model and tokenizer revision `1cfa9a7208912126459214e8b04321603b3df60c`. Start every training run from the unchanged base, never a Phase-2 adapter.
- Single Colab T4; D021/D048 stack: torch 2.11.0+cu130, transformers 4.51.3, bitsandbytes 0.50.2, PEFT 0.15.2, accelerate 1.6.0; no TRL. Also retain the manifest's huggingface-hub 0.30.2, tokenizers 0.21.1 and safetensors 0.5.3 pins and all execution settings. Record Python and remaining package versions.
- Preserve Phase-2 training/evaluation dtype preparation, deterministic settings, tokenizer, chat template and empty think block. Model shard hashes and all runtime identities are checked and recorded. A different Colab default image is refused before opening an attempt; no automatic backbone or stack fallback.

## 3. Target generation and eligibility (TRAIN only)

1. After the target-generation implementation freeze (§11), generate exactly one unchanged-model response to the **E rendering of each of the 160 TRAIN families**, fresh context, using the Phase-2 prompt `test1-english-final-v2`, pinned revision and §5 generation settings. Use the engine's deterministic seed-11 order construction restricted to these E inputs. Preserve the engine's decoded response text and raw token record. No answer-dependent retries, prompt improvements, R/C teacher generation or candidate sampling. An infrastructure retry follows §10; an unresolved generation halts completion of target construction, rather than being silently counted as a poor target.
2. A self-generated candidate qualifies only if scorer v1.0.0 marks it strict-correct, it is not truncated, its final nonblank line is the valid terminal FINAL line, it is fully English, and all three form-specific training sequences fit the cap below. Strict correctness uses the existing TRAIN gold and metadata unchanged.
3. Language gate (fixed rule): (a) any Devanagari character (Unicode blocks U+0900–097F, U+A8E0–A8FF, U+11B00–11B5F) → ineligible, automatically. (b) Otherwise, a candidate is **flagged** if, after lower-casing and splitting on non-letters, it contains any of these Romanized-Hindi words: hai, hain, ka, ki, ke, ko, mein, aur, se, kitne, kitna, kitni, bacha, bache, liye, paas, waala, waali, wale, nahi, kya, toh, yeh, woh, usne, uske, unke, isliye, kul, rupaye, rupye. (c) Unflagged candidates pass the language gate. (d) Flagged candidates go to a bilingual human (team member), who sees only that TRAIN family's E text and the candidate, and records pass (fully English; the hit is a name, unit or English use) / fail (non-English explanatory prose) / uncertain, with a reason; uncertain is ineligible. Mathematical notation, numerals, names and English units are permitted. Do not edit a candidate to make it pass. The word list and rule are frozen in the target-generation manifest.
4. For each accepted candidate, the training target is **that exact decoded output text plus `<|im_end|>`**, without stripping whitespace, rewriting steps or normalizing the FINAL line. Append the marker once to the stored decoded text (the engine decodes with `skip_special_tokens=True`); assert the last supervised ID is 151645. Prompt and target are encoded separately as in Phase 2; assert identical target IDs for E/R/C and both E+E copies.
5. **Sequence cap:** 1,024 total input tokens, including the full wrapped prompt, empty think block, output text and terminal marker, on **every** E/R/C form. No packing, truncation, shortening or per-arm dropping. An overlength candidate fails family eligibility in all arms. Report length failures separately even when other rules fail. Perform this check before counting qualifying families.
6. Let Q be the count passing all rules. **If Q ≥ 120**, train on exactly these Q families and exclude the other 160 − Q from every arm. **If Q < 120, halt before training.** No fallback targets, re-generation, sampling or rule change is permitted under this registration; any continuation requires a dated amendment written with knowledge of Q and the failure reasons, and is reported as such. Report Q, all overlapping failure reasons, exclusions and the branch regardless of outcome.
7. (Removed at adoption: no fallback teacher. Section numbering of later items is unchanged.)
8. Accepted self-targets are frozen verbatim plus the terminal marker, identical across arms, with per-family text and token-ID hashes.

Self-generated candidates need not be long: correctness/English/FINAL/fit do not guarantee rich explanations or sound intermediate steps. Record target tokens and a descriptive explanation status (`explanatory proposition`, `labelled equations only`, `answer only`) for every candidate, assigned by a fixed automatic heuristic frozen with the generator; never use these counts for selection. The treatment is the model's own style (adoption change 1); if it is terse, report that, with no repair.

## 4. Training recipe and exposure

- For each retained family with target T: EE = (E,T),(E,T); ER = (E,T),(R,T); EC = (E,T),(C,T). There are 2N_train distinct example slots per arm. Content, target text/token IDs and exposure counts match across arms.
- Completion-only labels mask the prompt and empty think block. LoRA r 16, alpha 32, dropout 0.05 on q/k/v/o/gate/up/down projections; fp32 adapter, double-quantized NF4 base, FP16 compute, SDPA math attention, non-reentrant gradient checkpointing, `use_cache=False`.
- AdamW: betas (0.9,0.999), eps 1e-8, weight decay 0; unscale before gradient clipping at 1.0. Microbatch 1, accumulation 16; mean loss over each example's supervised tokens divided by 16, equally weighted examples. GradScaler init 65,536, growth 2.0, backoff 0.5, interval 2,000.
- Exactly **60 accumulation windows and 60 successful optimizer steps**, 960 example exposures = 480 family visits per run. For u = 1…60, set lr before step u: `1e-4*u/6` for u ≤ 6; otherwise `1e-4*(0.1 + 0.9*0.5*(1 + cos(pi*(u-6)/54)))`. Update 60 is the only evaluated checkpoint. No early stopping or schedule optimization.
- Seeds 11/22/33. Seed Python, torch and CUDA before adapter creation; initial tensors match within each seed triplet. Pairing controls initialization and exposure order, not dropout draws.
- **Adaptation to filtering:** for each seed s, concatenate full family permutations for passes p = 1,2,…, sorting retained IDs by SHA-256 of UTF-8 `phase2-D043:{s}:{p}:{family_id}` (decimal s,p; ID tie-break). Take the first **480 family visits**, then emit E followed by the arm's second example for each visit. Carry the stream across pass boundaries without padding or dropping partial batches. Each update consumes eight visits. For N_train = 160 this exactly reproduces three Phase-2 passes; for 120 it gives four; otherwise it includes a partial last pass. Thus exactly three passes is **not** retained after filtering. Counts differ by at most one visit across families, and are identical across arms. Freeze lists for seeds 11/22/33 and reserves 44/55 before training.
- Run slot 11 (EC, ER, EE), then slot 22, then slot 33; settle a slot and any reserve before proceeding. Log every attempt, input/supervised tokens, data cursor, attempted/successful steps, losses, gradient norms, lr, scaler events, timing, memory, initial tensor identities and saved adapter/config hashes.

## 5. Generation protocol and unchanged-model reuse

Engine `test1_pilot/hinglish_pilot`; strict scorer v1.0.0, SHA-256 `c48f9d12e733eb1bfe5af5b1fece6e3ff69cb2342a97fe3ba8ac9f01f68dbbbc`. Frozen prompt v2; greedy one-beam, non-thinking, NF4 double quantization + FP16, SDPA math, batch 1, fresh context, engine seed 11, context cap 2,048, output cap 1,024. Preserve EOS IDs [151645,151643], pad 151643, stopping at first EOS or output cap, and all Phase-2 generation settings. Trained adapters are unmerged on the same base; no re-quantization. The training cap of 1,024 total tokens is distinct from these generation caps.

**Configuration check made for this draft:** current engine-group, prompt-source and analysis-group file hashes match `phase2/IMPLEMENTATION_MANIFEST.md`. Its FINAL_TEST engine configuration digest is `91a0cf80d989a9ff5cb1aec15207a4298c2b0c7422d9304b70a4b56dcab6c915`; DEV digest is `ef75d11575fb2b609fb81023b186c7f6f4038346d53e8a0e81146c12e16d8b85`. The Phase-2 analysis reports validated archives at that configuration. **No inference configuration difference is planned: reuse the unchanged model's 300 Phase-2 FINAL_TEST outputs; do not re-run it.** New Phase-3 runtime equivalence remains a future gate, not a completed check.

Bind the original unchanged run `phase2_final_test-627d68ad676f426c8c698c0258d433d6`, its inner archive/journal/config/environment/checksum hashes and the containing archive (`fb4a71ccb22d8d4f274ec3c94c0b7455f870aebe7fcc673d18e47632a0024f9a`) in the Phase-3 manifest. Preserve its original provenance; do not relabel it as newly generated. New adapter paths and study bookkeeping can differ; these do not excuse inference-setting differences. A loader must validate old baseline evidence against its original manifest and the explicit equivalence bridge to Phase 3.

If actual engine/config/backend identity differs, stop before evaluation and amend the registration before any new FINAL_TEST generation. If a changed inference configuration is then adopted, run a new unchanged baseline once on all 300 test renderings after freeze; do not choose between old/new baselines by outcomes. This is the sole conditional rerun branch and raises new final-test generations to 3,000. Mere inability to validate an archive is not permission to regenerate it.

Nine adapters × 100 families × three forms = **2,700 new FINAL_TEST generations**; with reused unchanged outputs the analysis has 3,000 records. Generated invalid, missing-answer, refused, ambiguous or truncated responses score 0. An absent/unresolved generation is not a scored zero (§10).

## 6. DEV prerequisite and sanity report

Reuse the validated complete Phase-2 unchanged-DEV archive (120 outputs; SHA-256 `a8194ac29cb17711d8e8e526835daacc368fdc4b5265f51d41f96edff347171a`) after checking its original implementation manifest (`726241c5726aaba2c51fc027866dd572abfc13d02ef9235d1901af87a9f5b43d`) and inference-equivalence bridge. The first training attempt is refused without this evidence. An unchanged manifest hash cannot be asserted across changed training/target code: both manifest hashes and the equivalence checks must be explicit.

The existing high unchanged-DEV accuracy proxy is C 24/40, Wilson 95% 44.6–73.7%, below 38/40. Carry this forward; no new ceiling-driven backbone, planning simulation or target choice. After training, each of the nine adapters gets DEV E/R/C once (1,080 generations) for format, language and completeness sanity reporting only. DEV never selects a checkpoint, changes targets or authorizes a retry. Target-generation execution is isolated from DEV; later DEV evaluation is a separate step.

## 7. Estimands

For family i (N = 100), retained seed s (S = 3), arm a and form l, y(i,s,a,l) is strict correctness and u(i,l) the reused unchanged outcome. Average paired seed contrasts within family first; families receive equal weight.

- **Primary:** Δ_C = mean_i (1/3) Σ_s [y(i,s,EC,C) − y(i,s,ER,C)].
- **S1 English retention, descriptive:** EC − EE, EC − unchanged, ER − EE, ER − unchanged and EE − unchanged on E. Lead practical retention reporting with all three arms versus unchanged; the margin remains −2 pp.
- **S2, descriptive:** T_R = ER − EE on R; Δ_R = EC − ER on R.
- **S3, descriptive:** Δ_C − Δ_R, constructed per family before averaging.
- **Other descriptive reporting:** per-checkpoint E/R/C accuracy with Wilson intervals, numeric_literal_v1/v2 using Phase-2 amended rules, operation-word strata, strict-invalid reasons, truncation, output-token median/mean/IQR and latency per checkpoint/form; target lengths/source composition and training-token counts. Output length uses the same engine token field as Phase 2. Pooled summaries are labelled as repeated family/seed observations.
- **Cross-phase, descriptive only:** for each arm and form, seed-mean Phase-3 accuracy minus seed-mean Phase-2 accuracy on the same 100 families; show both levels, pp change and output-length summaries. No new hypothesis test or decision label; no causal attribution to richer targets. Training targets, potentially family membership, passes and total supervised tokens differ. If reserves differ, compare phase-specific seed averages without claiming seed pairing. This comparison does not replace Δ_C.

## 8. Inference and decision labels

Reuse the statistical implementation in `phase2_analysis/analyze.py`, SHA-256 `11d6f1c837ff05d8de7ef96732ddca023f1f4b8faa4762b25747f7a49749150f`, rather than rewriting bootstrap/quantiles/labels. A Phase-3 input/provenance wrapper is needed to bind the new freeze and reused baseline and to label reports correctly; it must preserve all validation and be independently reviewed and frozen before outputs. Do not bypass validators, forge a Phase-2 manifest or import old adapters under new names. Test plumbing on synthetic/TRAIN/DEV fixtures only; keep cross-phase descriptive reporting separate from the primary core.

- Sort families by ID. Fresh `random.Random(101)` draws a 10,000 × 100 index matrix with `rng.randrange(100)` in row-major order; reuse it for every endpoint, contrast and per-seed interval. Retain the whole family record. Linear percentile quantiles use h = 9999p at p = .025/.975. Record Python version and matrix SHA-256 (expected `33f4920eab5738cf29b346be8d63a15115f9fcbda58699ee9fc44b031e46e6a1` using the existing serialization).
- Report Wald (sample SD, ddof 1, z = 1.959963984540054), bounded Hoeffding radius `(b-a)*sqrt(log(40)/(2N))`, clipped to [a,b], with [−1,1] for differences and [−2,2] for S3; nonzero/distinct family contrasts, degeneracy and bootstrap tails. Wilson intervals use N = 100 per checkpoint, never 300 pooled seed rows.
- Per-seed Δ_C, Ret_E, T_R and Δ_R intervals, exact McNemar discordance counts/two-sided p, ranges and signs are descriptive. No crossed family × seed resampling. Only strict Δ_C is the pre-specified primary; no inferential secondaries or Holm procedure.
- Intervals are approximate, conditional on these checkpoints; they do not include training-seed variance, target-generation/selection variance or adaptive benchmark reuse. The finite 100-family mean is descriptive; generalization assumes independent families from this authoring/review process. Δ_C measures the complete rendering-training recipe, not code-switching in isolation.

For unrounded strict 95% bounds [L,U] in pp:

| Label | Rule |
|---|---|
| Useful support | L > +5 |
| Support | 0 < L ≤ +5 |
| Informative null | L ≤ 0 ≤ U and U < +5 |
| Harm | U < 0 |
| Inconclusive | L ≤ 0 and U ≥ +5 |

**Override:** identical family contrasts or zero-width percentile interval → `inconclusive—degenerate empirical interval`; no support, null or retention claim. Still report the raw interval, point, Hoeffding interval, nonzero count and both tails. Informative null rules out ≥5 pp gains under the approximate model; it does not establish equivalence or exclude harm.

For each English contrast, independent descriptive flags: `within-margin criterion met` iff L > −2; `loss detected` iff U < 0; `loss beyond margin` iff U < −2. For EC − EE and EC − unchanged only, `retention trade-off` additionally requires primary Support/Useful support and U < −2. Degeneracy overrides these flags. Never widen the margin.

## 9. Power and precision

Reuse D040 and the amended Phase-2 planning reasoning; no new simulation is required. With N = 100 and three paired seeds, plan for approximately ±3–4 pp, with the previous scenario range **1.97–5.64 pp** median 95% half-width (2.06–3.64 at the pilot ceiling). Phase 2 realized 3.67 pp for Δ_C; that is context, not a guarantee for different targets. The planning simulations assumed gain-only effects and were optimistic; new trained-arm discordance is unknown. Approximate 80%-power MDE was 3–7 pp; +3 pp effects, L > +5 “Useful support”, and a −2 pp retention criterion are not reliably powered. More seeds do not create new families. Report E+R C headroom beside Δ_C, regardless of outcome. The bootstrap's approximate precision does not solve benchmark-reuse bias.

## 10. Failures, ownership and recovery

Retain Phase-2 Amendments 1–3, with precedence over the original unamended rules:

- Exact stack/hardware/config checks occur before an attempt opens. One writer per training root, session ID and heartbeat; never automatically abandon an open attempt. Stale-writer recovery requires explicit operator confirmation `RECOVER_STALE_WRITER = True` that no other session is running, logs the event and closes the open attempt as infrastructure failure. Separate Phase-3 roots; preserve all prior attempts.
- Typed training infrastructure failures only: runtime disconnect/kill, CUDA OOM, Drive/filesystem OSError, network/Hub download error, failed checkpoint write. At most one from-scratch retry with identical seed/config/code. No partial training resume. Second infrastructure failure replaces the whole triplet with the next unused reserve [44,55], assigned to original slots [11,22,33] in order; retrain successful arms of the replaced seed too. Each reserve gets the same attempt budget, never reused.
- Any scaler skip, nonfinite loss/gradient/saved parameter is numerical failure; any hash/identity/label/data assertion, programming error or unknown exception is protocol failure. Halt for diagnosis, no seed substitution; repair requires dated amendment before further training. Ordinary finite loss, short outputs, DEV accuracy or later test results never trigger retries.
- Target generation/evaluation use the engine's at most one unchanged-configuration infrastructure retry per prompt; OOM is not retried by the generation engine. No successfully generated output is regenerated. Interrupted evaluation resumes the journal. Stale evaluation lock recovery requires `RECOVER_STALE_LOCK = True` after confirming no other evaluator is active, with a timestamped log. Count process launches separately from generation attempts.
- Freeze retained seeds and S before new FINAL_TEST access. Three complete paired triplets are required for the primary decision label; S = 1 or 2 allows descriptive reduced-S reporting only, averaging by 1/S; S = 0 means no new FINAL_TEST evaluation. Any unresolved required evaluation item suppresses the primary analysis/label; do not remove incomplete families or choose best seeds.

## 11. Freeze gates and runbook

All named Phase-3 manifests below are **future required artifacts**, not files created or hashes supplied by this draft. Record SHA-256 values, adoption/exposure timestamps and server-side push/read-only archive evidence; a local commit time alone does not prove order. No gate advances merely because this draft exists. Sol independently verifies implementation, target identities, attempt policy, baseline equivalence and gate checks before execution; review is not claimed completed here.

| Before step | Freeze and hash requirements |
|---|---|
| **Any target generation** | Adopted plan/design; target-generation manifest; TRAIN bytes and authorized E-only input/order list; language word list and flag rule, explanation-status heuristic, length rules; generator, eligibility/scoring/label code and notebook payload; engine sources/config, prompt/template/tokenizer files, revision/config/weight shards, EOS/stopping/dtype/stack. Record source Phase-2 manifests, scorer and numeric endpoint hashes. Target runtime has no DEV/FINAL_TEST payload. |
| **Any training attempt** | Target archive and journals/attempts; per-family exact text/token hashes and source; selection/review/failure ledger, Q, final inclusion list and all-form length/identity checks; target freeze manifest; all five seed exposure lists and counts; trainer/label builder/schedule/attempt plan/lock code; implementation manifest and training notebooks; validated unchanged-DEV archive and old/new manifest equivalence bridge; frozen analysis core, Phase-3 input wrapper and descriptive reporting code; audit rubric. Recheck generator pins and frozen source data. |
| **Any Phase-3 DEV evaluation** | Frozen evaluation driver/notebook and engine settings already in implementation manifest; complete update-60 adapter/config identity for that run. No DEV-driven change thereafter. |
| **New FINAL_TEST access/generation** | `phase3/ADAPTERS_FROZEN.md`: all retained adapter weights/config hashes, base shard/revision hashes, seed-slot mapping/S, training logs and every attempt/recovery, target/exposure/implementation identities, DEV sanity archives, validated original unchanged DEV and FINAL_TEST archive/journal/config/environment identities. Hash the test bytes only. Sol checks adapter freeze and baseline reuse bridge. Freeze final-evaluation notebook/payload before launch, referencing this manifest. |
| **Outcome unsealing/analysis** | All required evaluation archives complete, checksums/coverage/attempt budgets/config identities valid; hash journals and sealed exports. Until then operators see only completion, checksum and infrastructure status, with response/accuracy previews suppressed. Run the frozen primary analysis once, then separate descriptive comparison/audit. |
| **Release/reporting** | Hash analysis outputs, independent Sol recomputation, audit packet, both tag sets, every human return and final audit. Preserve all failures/deviations and source identities. |

Runbook outline: (1) adopt plan and obtain Sol's implementation review; (2) freeze generator and produce 160 E teacher outputs; (3) apply the eligibility gates (halt if Q < 120) and freeze targets; (4) freeze exposure/training/analysis implementation and validate reused DEV prerequisite; (5) execute nine training runs in plan order and DEV sanity, settling retries/reserves; (6) freeze adapters and baseline reuse evidence; (7) evaluate nine adapters once on FINAL_TEST, sealed; (8) verify completeness, unseal, run analysis and obtain independent Sol recomputation; (9) complete audit and report everything. No further training, target changes, tuning or reevaluation after step 7 begins.

## 12. Compute and reporting

Nominal GPU work: **160 target generations + nine training runs (540 successful updates) + 1,080 DEV sanity generations + 2,700 new FINAL_TEST generations**. Thus 3,940 new generations including DEV, with the 300 unchanged FINAL_TEST and 120 unchanged DEV outputs reused. Retries/reserves are additional and reported.

Phase-2 training was about 20–21 s/update (~3.1 hours for 540 updates), and unchanged-model evaluation medians were about 11–12 s/output. Planning at 12 s/output gives ~0.53 h target generation, 3.6 h DEV and 9 h FINAL_TEST, plus training, loading/export and disconnect overhead. Budget roughly **16–23 T4 hours** as a planning allowance (e.g. 20–60 s/update for longer targets), not a measured Phase-3 throughput promise or cap. Near-cap targets could exceed it; timing never changes the recipe. Record actual input/target/generated tokens, GPU time, peak memory, all attempts and human review effort. Q < 120 halts rather than consuming further compute.

Report all primary and secondary results, null/harm/inconclusive outcomes, seed attrition, target exclusions/source counts, target and output lengths, training curves, English flags, baseline reuse and test-exposure history. Failure audit covers **every strict-incorrect C output of every retained ER and EC seed**: independent Claude Opus and GPT taggers, blind to each other's tags and arm/seed where feasible, followed by **human check of every audited output**, not a sample or propagation of an adjudicated rule. Use the frozen Pilot-B rubric; explicitly clarify before tagging that labelled equations without an English explanatory proposition are `no_explanation`. Retain tagger labels, agreement, human decisions and unresolved rows. Denominators are all C generations per arm; audit labels never replace strict scores or establish mechanisms.

## 13. Threats, deviations and scope

Correct-output filtering selects easier/model-compatible TRAIN families; fixed updates increase repeat exposure after exclusion. The Q ≥ 120 rule can halt the study. Exact self-target copying preserves errors in intermediate reasoning and does not guarantee explanation richness. Longer targets change supervised-token volume despite equal example/update counts. Cross-phase improvements cannot isolate target style from selection, repetition, teacher, or token-budget changes. One model, three seeds, shared author/templates, GPT-versus-Claude author shift, single-reviewer test acceptance, sample-based TRAIN review, frozen scoring limitations and old test exposure constrain generalization. Loss of English accuracy remains a substantive concern even if Δ_C is positive.

Any change is a dated amendment stating why, what outputs already existed and the affected hashes/gates; record adoption under D017 in the decision log during later integration. Do not edit Phase-2 artifacts. Changes after new FINAL_TEST access are post hoc, with the original pre-specified analysis retained in full. No second backbone, self-translation arm, new scorer, target-length optimization or checkpoint search is included.
