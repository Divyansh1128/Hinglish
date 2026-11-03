# Phase-2 training study (E+E / E+R / E+C): pre-registered analysis plan

Written 3 November 2026, **before any Phase-2 training run, any trained adapter and any FINAL_TEST output exists**. FINAL_TEST has never been given to a model; for this document only its file hash was computed. This file is committed to git before the first Phase-2 training run, so the commit time proves the order. It is the binding plan; where it differs from `research/phase2_protocol_v1_2026-10-27.md` (a proposal), this file governs. Basis: D021, D033, D040, D041, D042, D043; style model `pilot_b/PREREGISTRATION.md`.

E = English, R = Romanized Hindi (frozen borrowing list, D033), C = Roman-script Hinglish (insertional definition, D033). All forms use Latin script.

## 1. Data (frozen; SHA-256 re-verified with `shasum -a 256` on 3 November 2026)

| Role | File | Families | SHA-256 |
|---|---|---:|---|
| TRAIN | `phase2/train_A.v2.json` | 80 | `b9656a8c41af2a795bce9c131efc6a5efc652df78368d14fb7720fd985883666` |
| TRAIN | `phase2/train_B.v2.json` | 80 | `c975fe12459df6160effc5aeb0087f94666ba0b49778c3d827a67bb923ff35bd` |
| DEV (sanity only) | `phase2/dev.v2.json` | 40 | `e741c1652f5b3dcaebc78d9dd9d7c31fdf4417306fbb2f0862149f27f858f28b` |
| FINAL_TEST | `phase2/final_test.v3.json` | 100 | `da89dd9a626e438dffca39e3a74c4c8abac6bb57501495723b87e6ee143f3d46` |

- Every script checks these hashes and stops on mismatch. Any data change needs a new version, a new hash and an amendment (§12) before use.
- TRAIN was drafted by Claude; DEV and FINAL_TEST by GPT (author/style shift is part of the test). FINAL_TEST: single-reviewer ACCEPT; TRAIN/DEV: sample-based review (D027). Reported as limitations.
- One frozen rendering per family and form. Pilot, Pilot-B and FMT2 families are never trained or tested on here. The D041 smoke adapters were discarded and are never used; their 16 families remain ordinary TRAIN families.

## 2. Backbone and stack

- **Qwen3-4B** (`Qwen/Qwen3-4B`), model and tokenizer revision `1cfa9a7208912126459214e8b04321603b3df60c` (D042). The SHA-256 of the downloaded weight shards is recorded in every run manifest.
- Stack (D021, verified by the smoke test): torch 2.11.0+cu130, transformers 4.51.3, bitsandbytes 0.50.2, PEFT 0.15.2, accelerate 1.6.0; no TRL. Single Colab T4 per run.

## 3. Training recipe (D021 + D043; identical for all arms and seeds)

- **Arms.** For each of the 160 TRAIN families, two examples, both supervising the identical full English solution (`reference_solution_en`) plus `<|im_end|>`: E+E = (E, T), (E, T); E+R = (E, T), (R, T); E+C = (E, T), (C, T). 320 examples per arm. The user turn is the frozen prompt `test1-english-final-v2` wrapped around the rendering, with the empty think block (non-thinking), exactly as at evaluation.
- **Labels.** Completion-only, self-built: prompt and empty think block masked; target token IDs asserted identical across E/R/C for every family before training. No packing, no truncation; every example must fit 1,024 tokens or training does not start.
- **Adapter.** LoRA r 16, α 32, dropout 0.05, on q/k/v/o/gate/up/down projections; fp32 adapter on an NF4 (double-quantized) base with FP16 compute; SDPA math attention; non-reentrant gradient checkpointing; `use_cache=False`.
- **Optimizer.** torch AdamW, betas (0.9, 0.999), eps 1e-8, weight decay 0, gradient clip 1.0, GradScaler initial scale 65,536. Microbatch 1, accumulation 16 (16 examples per update); loss = mean over each example's supervised tokens, divided by 16 (examples weighted equally).
- **Schedule (D043).** 3 passes × 20 updates = **60 updates**. Peak lr 1e-4. For update u = 1…60: lr(u) = 1e-4 · u/6 for u ≤ 6; otherwise lr(u) = 1e-4 · [0.1 + 0.9 · ½(1 + cos(π(u − 6)/54))], so lr(60) = 1e-5.
- **Seeds and pairing.** Seeds **11, 22, 33**. Before adapter creation `random`, `torch` and CUDA are seeded with the run seed, so LoRA initialisation is identical across the three arms of a seed. Data order for seed s, pass p ∈ {1,2,3}: families sorted by SHA-256 hex of `"phase2-D043:{s}:{p}:{family_id}"` ascending; each family contributes its E example then its arm-specific second example, consecutively; updates take the next 16 examples (8 families). The order therefore differs between seeds and passes but is identical across arms within a seed.
- **Checkpoint.** The adapter after update 60 is the evaluated checkpoint. No early stopping, no DEV-based selection, no intermediate checkpoint is ever evaluated.
- **Logged per run:** per-update loss, gradient norm, lr, scaler skips, input and supervised tokens, s/update, peak and free memory, stack versions, and SHA-256 of `adapter_model.safetensors` and `adapter_config.json`.

## 4. Evaluation protocol (identical to Pilot-B)

- Engine `test1_pilot/hinglish_pilot` with prompt `test1-english-final-v2`; scorer v1.0.0 (`scorer_v1.py` SHA-256 `c48f9d12e733eb1bfe5af5b1fece6e3ff69cb2342a97fe3ba8ac9f01f68dbbbc`). Greedy one-beam, non-thinking, NF4 + FP16, SDPA math, batch 1, context cap 2,048, **output cap 1,024 tokens**, fresh context per prompt, engine seed 11 for the evaluation order, at most one unchanged-configuration infrastructure retry per prompt, no answer-dependent retries.
- Trained checkpoints are evaluated as the unmerged LoRA adapter on the same NF4 base used in training (no merge, no re-quantisation).
- Invalid, missing, refused, ambiguous or truncated outputs score 0. No prompt, decoding or scorer change after any Phase-2 output.
- **Checkpoints evaluated:** 9 adapters (3 arms × 3 seeds) + the unchanged model = 10. FINAL_TEST: 10 × 3 forms × 100 = **3,000 generations**.
- **Endpoints.** Primary: strict accuracy, scorer v1.0.0. Secondary: `numeric_literal_v1` (D018, `secondary_analysis/numeric_endpoint.py` SHA-256 `ce70aefd1f4c03ffe80bbd06d4df025abe92fc0865732b6d2e6db13504ed883f`) and `numeric_literal_v2` (below). Secondary endpoints never change the primary score or the decision label.

**`numeric_literal_v2` (D040), exact rule.** v2 is v1 unchanged except for one rupee rule. "Gold is rupees" means the casefolded gold `unit` is one of `rupees`, `rupee`, `inr`, `rs`, `rs.`, `₹`. Extraction (still gold-blind) additionally accepts, after the scalar or its wrapper, an optional-whitespace **trailing `₹`** as the final token, and a **leading `rupees` or `rupee`** (case-insensitive, optional whitespace) in the position where v1 accepts `₹/INR/Rs./Rs`; at most one currency marker per answer (two → `unsupported_answer`, as v1). The marker is recorded in `extraction_path` (`currency_suffix_symbol` / `currency_prefix_word`) and stripped before the numeric comparison. In evaluation, an answer extracted *only* through one of these two new paths counts as correct only if gold is rupees and the value matches; otherwise it scores as v1 would (`unsupported_answer`, incorrect). Every other v1 behaviour is unchanged (v1 already accepts leading `₹/INR/Rs./Rs` and trailing word suffixes such as `Rs`, `INR`, `rupees`; no unit conversion). Consequently v2 can differ from v1 only on rupee-gold items. Implementation: versioned `ENDPOINT_VERSION = "numeric_literal_v2"`, unit tests covering each new path and the non-rupee negative case, re-scored on stored Pilot-B outputs (planning proxy, lower bound: Qwen3-4B E/R/C 69/61/67 vs v1 51/58/58), and its file hash recorded in a commit **before any trained-adapter output and before FINAL_TEST access**.

## 5. Unchanged-model DEV check and ceiling flag (before training)

- After this file is committed and **before the first training run**, the unchanged Qwen3-4B is run once on DEV E/R/C (120 generations) with the §4 protocol.
- **Ceiling flag:** fires if unchanged DEV C strict accuracy ≥ 95% (≥ 38/40). If it fires: Δ_C is pre-declared ceiling-limited; the report gives the headroom, leads with the precision statement and S2, and the power script is rerun with the DEV value of p0 for the record. Design, data and labels do not change.
- **Optional second backbone (only if the flag fires):** Llama-3.2-3B-Instruct (D032; revision and chat-template date to be pinned) may be added with the identical recipe, schedule, seeds and analysis, after its own D021-style smoke test. The decision is recorded in DECISIONS.md before any Qwen3-4B Phase-2 training output; its results are secondary and never replace the Qwen3-4B primary.
- After training, all 9 adapters are also run on DEV (1,080 generations) as a **sanity report only** (FINAL-line validity, format, Devanagari/English compliance). DEV results never select checkpoints, hyperparameters, arms or reruns.

## 6. Estimands

y(i,s,a,l) ∈ {0,1}: strict correctness for FINAL_TEST family i (N = 100), seed s (S = 3), arm a ∈ {EE, ER, EC}, form l ∈ {E, R, C}; u(i,l) for the unchanged model. Families and seeds get equal weight; arm effects are seed-averaged per family first, d_i = (1/3) Σ_s [·].

- **Primary:** Δ_C = mean_i (1/3) Σ_s [y(i,s,EC,C) − y(i,s,ER,C)].
- **S1 English retention:** Ret_E = EC − EE on E (seed-averaged, paired by family). Also reported, with the same margin labels: EC − unchanged on E; ER − EE and ER − unchanged on E; EE − unchanged on E.
- **S2 R transfer:** T_R = ER − EE on R. Also Δ_R = EC − ER on R.
- **S3 specificity:** Δ_C − Δ_R, computed per family before averaging.
- **Descriptive:** operation-word strata (R uses a Hindi operation word and C keeps it / C switches it to English / no operation word; tags read from the frozen FINAL_TEST provenance) for Δ_C and C accuracy by arm, counts and percentages only. Absolute E/R/C accuracy of all 10 checkpoints with Wilson 95% intervals; strict-invalid reason counts; tokens and latency per form.

## 7. Inference

- **Interval:** paired family bootstrap, **10,000 resamples, seed 101**, conditional on the 9 trained checkpoints and the unchanged model. Each resample draws 100 family indices with replacement (Python `random.Random(101)`, one index sequence shared by all estimands) and keeps each family's whole record (all arms × forms × seeds). 95% percentile interval. It is an approximate conditional interval: it does not cover training-seed variance. Also reported: the Wald interval on d_i, the Hoeffding bounded interval (radius ≈ 27.2 pp at N = 100), the number of distinct d_i values and degeneracy.
- **Per seed:** Δ_C, Ret_E, T_R and Δ_R for each seed with its own paired bootstrap (same settings) and exact McNemar counts (first-only/second-only) and two-sided exact p; the range across seeds; sign consistency described, never used as a test. Crossed family × seed resampling only as a labelled sensitivity analysis. Family-seed rows are never treated as independent.
- **Multiplicity:** Δ_C is the only confirmatory quantity. S1–S3 are reported with unadjusted 95% intervals labelled descriptive. If any secondary is claimed inferentially, Holm at α = .05 applies across {S1 (EC − EE vs −2 pp, one-sided), S2 (T_R vs 0), S3 (vs 0)} using bootstrap p-values: one-sided p = #{θ* ≤ −2 pp}/10,000 for S1, two-sided p = min(1, 2·min(#{θ* ≤ 0}, #{θ* ≥ 0})/10,000) for S2 and S3.
- All endpoints (strict, v1, v2) get the same analysis; decision labels use strict only. Decisions use unrounded bounds.

## 8. Decision labels (primary Δ_C, strict, 95% bootstrap interval [L, U], in pp)

| Label | Rule |
|---|---|
| **Useful support** | L > +5 |
| **Support** | 0 < L ≤ +5 |
| **Informative null** | L ≤ 0 ≤ U and U < +5 (rules out the useful gain) |
| **Harm** | U < 0 |
| **Inconclusive** | L ≤ 0 and U ≥ +5 |

The labels are exhaustive and exclusive. If the ceiling flag fired, the label is printed with "(ceiling-limited)". **English retention (S1, margin −2 pp, never widened):** "retained" only if L(Ret_E) > −2; "degraded" if U(Ret_E) < 0; "retention trade-off" if Δ_C is Support/Useful support and U(Ret_E) < −2; otherwise "retention not established", with the interval. The same rule is applied to EC − unchanged on E.

## 9. Power and precision (planning only; `research/phase2_power/`, script SHA-256 `7620f4db…0803`)

Simulated from real Pilot-B outcomes of the unchanged models, N = 100, S = 3, under gain-only effects (no offsetting losses), so **optimistic**. Trained-arm seed discordance q0 is unobserved and varied.

- Pilot-B Qwen3-4B (unchanged): E 66/70, R 60/70, C 66/70 → C headroom 5.7 pp; a +10 pp gain is impossible if E+R stays at the pilot C level.
- P(L > 0): +3 pp → 0.51–0.56 at the pilot ceiling (p0 0.943), 0.21–0.58 across all scenarios; +5 pp → 0.89–0.96 at the ceiling, 0.45–0.96 overall; +10 pp → 0.95–1.00 where headroom exists. False support at δ = 0: 0.016–0.028.
- Median 95% half-width ≈ 2.0–5.0 pp (2.1–2.9 at the ceiling). Approximate 80%-power MDE ≈ 3–7 pp.
- "Useful support" (L > +5) is essentially unreachable: ≤ 0.025 at true +5 pp, 0.41–0.60 at true +10 pp.
- Single seed pair, exact McNemar: 0.13–0.37 at +5 pp. All three seeds positive: 0.05–0.09 under the null.
- Retention (true difference 0, margin −2 pp): P(L > −2) = 0.52 / 0.29 (q0 0.035 / 0.071). Non-inferiority will usually not be shown even when nothing is lost.
- S3 null half-width ≈ 2.9–4.3 pp.
- **Honest statement:** the study is **underpowered for a +3 pp effect** and cannot establish a useful (≥ 5 pp) gain or 2 pp English non-inferiority. Its value is a pre-registered estimate of Δ_C with ±2–5 pp precision. Only 100 FINAL_TEST families exist; DEV is not added and extra seeds add no families.

## 10. Failed or incomplete runs

- **Training failure** = infrastructure failure only: runtime disconnect or crash, OOM, failed save or reload, non-finite loss, hash or label-assertion failure. The run is discarded and **rerun once from scratch with the identical seed and configuration** (no resume from partial state). If the rerun also fails, that seed is replaced by reserve seed **44**, then **55**, **for all three arms** (successful arms of the failed seed are retrained too, keeping the pairing); the original seed's adapters are not evaluated. If no complete triplet can be obtained, the study is reported with the completed seeds and S stated.
- Reruns are never triggered by training loss level (other than non-finite), DEV accuracy or any FINAL_TEST output. Every attempted run, failed or not, is logged and reported.
- **Evaluation:** the engine's one unchanged-configuration retry per prompt; an interrupted evaluation run is resumed with its stored attempts (generated outputs are never regenerated). A checkpoint whose FINAL_TEST run stays incomplete has its headline numbers suppressed (engine rule) and the primary analysis is reported as incomplete; no complete-case removal, no best-seed selection.

## 11. FINAL_TEST access rule

1. FINAL_TEST is read by no model and inspected by no person before all 9 adapters are trained and the **freeze manifest** (`phase2/ADAPTERS_FROZEN.md`: adapter and config SHA-256 for each arm × seed, the unchanged base revision and shard hashes, training logs' hashes) is committed, together with the `numeric_literal_v2` code and the analysis script (tested on DEV outputs only).
2. Each of the 10 checkpoints is then evaluated on FINAL_TEST **exactly once**. Only completeness and checksum checks are run until all 10 runs are complete; the analysis script is then run unchanged.
3. No training, tuning, prompt change or re-evaluation happens after FINAL_TEST access. Any later model on FINAL_TEST (e.g. the optional self-translate control) is a separate, labelled post-hoc analysis unless pre-registered by an amendment committed before step 2.

## 12. Reported regardless of outcome

The decision label and Δ_C with intervals; all secondary estimands; per-seed results; every checkpoint's E/R/C accuracy (strict, v1, v2); the unchanged-model FINAL_TEST and DEV results; the ceiling-flag outcome; DEV sanity; training curves and compute (tokens, s/update, memory); all failed or replaced runs; a two-AI-tagger audit plus human check of all E+R and E+C failures on C (format-only vs substantive; descriptive, never overwriting strict scores); limitations (single reviewer, sample-based TRAIN/DEV review, GPT vs Claude author shift, three seeds, conditional intervals, ceiling). Null, harmful and inconclusive results are reported in the same detail.

## 13. Deviations

Any change to this plan is a dated amendment appended here and recorded in `docs/DECISIONS.md`, stating what changed, why, and whether any Phase-2 output (training logs, DEV, FINAL_TEST) existed at the time. Changes made after FINAL_TEST access are labelled post hoc, and the pre-registered analysis is still reported in full alongside them. Thresholds (+5 pp useful, −2 pp retention, 95% ceiling) are never changed after the corresponding output exists.
