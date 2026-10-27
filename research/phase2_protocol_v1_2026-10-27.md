# Phase-2 confirmatory training-study protocol v1 (E+E / E+R / E+C)

27 October 2026. **Proposal for pre-registration; not adopted, not run.** Written by a Claude Opus research subagent standing in for Astra (Codex authentication had expired). No training, no new inference and no FINAL_TEST inspection were done. Power numbers come from `research/phase2_power/phase2_power.py`, which reads only the stored Pilot-B outcomes of the *unchanged* models. Builds on `astra_experiment_spec_v1.md`, `astra_validity_and_power_v1.md` and `conditional_inference_2026-10-11.md`. Where this note differs from them, it says so.

## 0. Bottom line

- With 100 FINAL_TEST families and 3 paired seeds, the primary Δ_C can be estimated to roughly **±2–5 pp** (95% half-width), conditional on the trained checkpoints. That precision is useful, but the **design is underpowered for small effects**: +3 pp is detected with about 21–58% probability, and a "useful gain ≥ +5 pp" claim (lower bound > 5 pp) is essentially unreachable unless the true gain is about +10 pp.
- **The ceiling is the main risk.** On Pilot-B, unchanged Qwen3-4B already scores 94.3% on C. If the E+R arm stays there, the largest possible gain is 5.7 pp, so +10 pp cannot happen. Several of those failures are formatting failures that training on English targets may fix in *every* arm, which shrinks the headroom further. E+R also trains on Romanized Hindi, so it may already lift C. Δ_C is therefore expected to be small.
- Recommended claim: frame the primary result as a **pre-registered estimate with a precision target**, not as a significance hunt. Report "support / informative null / inconclusive" using the rules in §4.4. Keep retention, R-transfer and specificity descriptive. English non-inferiority within 2 pp cannot be established reliably at N = 100.

## 1. Estimands

Notation: y(i,s,a,l) ∈ {0,1} is strict correctness (scorer v1.0.0) for FINAL_TEST family i (N = 100), paired seed s (S = 3), arm a ∈ {EE, ER, EC} and input form l ∈ {E, R, C}. One frozen rendering per family and form; no variants in the primary analysis.

- **Primary.** Δ_C = (1/N) Σ_i (1/S) Σ_s [y(i,s,EC,C) − y(i,s,ER,C)]. Families and seeds get equal weight.
- **Secondary S1, English retention.** Ret_E = mean y(EC,E) − mean y(EE,E). Also report ER − EE on E and every arm against the unchanged model.
- **Secondary S2, R transfer.** T_R = mean y(ER,R) − mean y(EE,R): does Romanized-Hindi training help R? Also report Δ_R = mean y(EC,R) − mean y(ER,R).
- **Secondary S3, specificity.** Δ_C − Δ_R, computed per family before averaging so that the pairing is kept. It describes relative specialization only, not a mechanism.
- **Context (not an estimand).** Absolute E/R/C accuracy of all 9 checkpoints and of the unchanged model.

The intervention is the training-data rendering under this recipe. Vocabulary, tokenization, length and switching change together, and all forms use Latin script. So there is no claim about romanization or switching in themselves (spec v1).

## 2. Design

**Backbone: Qwen3-4B** at the pinned revision `1cfa9a72…`, with the NF4/FP16 recipe. Reasons from the pilots:
- It follows prompt v2 cleanly: 6/210 strict-invalid on Pilot-B, all `invalid_unit`, and 0/72 on the original cohort.
- It shows the R deficit the study targets (Pilot-B E−R +8.6 pp; R−C −8.6 pp [−15.7, −1.4]).
- Its inference stack is verified on T4.
- It is the backbone of the submitted paper (D039).

Alternatives:
- Qwen3-1.7B failed the format rule (D029, 36/36 invalid).
- Qwen3-8B is closer to ceiling (C 98.6%) and costs about 2× to train.
- Llama-3.2-3B has more C headroom (70.0%) and would power Δ_C better. It is the strongest alternative, kept as an optional cost-bearing control (§5), not the primary.

**Arms.** Each matched exposure cycle per TRAIN family supervises the identical full English solution (+ `<|im_end|>`) twice:
- E+E: (E, T), (E, T)
- E+R: (E, T), (R, T)
- E+C: (E, T), (C, T)

Training data: the 160 frozen TRAIN families (`train_A.v2` ∪ `train_B.v2`, hashes in `TRAIN_DEV_FROZEN.md`). Completion-only labels are self-built per D021, with the target token IDs asserted identical across arms. No packing and no truncation.

**Seeds.** 3 paired seeds (proposed values 11, 23, 37). The family order and exposure schedule for seed s are identical across arms. Each run starts from a fresh adapter and optimizer on the same base checkpoint. Every attempted run is logged, including failed ones.

**Updates (provisional).** 256 optimizer updates (microbatch 1, accumulation 16), LoRA r16/α32 on all 7 linear projections, fixed LR schedule. Total: 3 arms × 3 seeds × 256 = 2,304 updates.
- 256 updates is about 12.8 passes over 320 examples per arm, so overfitting the English targets is a real risk.
- The count stays provisional until the D021 smoke test. **Pre-registered rule, set before any arm outcome:** if the measured median s/update makes 2,304 updates infeasible on the chosen platform, use 128 updates for all arms. This rule uses timing only, never accuracy.

**Checkpoint rule.** Evaluate the fixed final update (256, or 128 under the rule above) for every arm and seed. No DEV-based selection. If one is ever adopted, it needs the same frozen criterion for all arms, written down before training.

**DEV (40 families): sanity only.** Use it for:
- loss/NaN, format and template checks;
- confirming that every arm still emits a valid FINAL line;
- unchanged-model difficulty (§3.4).

DEV accuracy never chooses hyperparameters, checkpoints or arms.

**Baseline.** The unchanged Qwen3-4B on FINAL_TEST E/R/C, with the identical prompt v2, greedy decoding and scorer.

**Evaluation budget.** 10 checkpoints × 3 forms × 100 families = **3,000 generations**, plus at most one unchanged-configuration infrastructure retry each. At Pilot-B latency (about 7–8 s per generation) that is roughly 6–7 T4-hours. FINAL_TEST is evaluated **once**, only after all 9 checkpoints are frozen and hashed.

## 3. Power and precision from real pilot data

### 3.1 Observed pilot inputs (Pilot-B, 70 families, strict; `pilot_estimates.json`)

| Unchanged model | E | R | C | numeric v1 E/R/C | numeric v2 proxy E/R/C |
|---|---|---|---|---|---|
| Qwen3-4B | 66/70 (94.3%) | 60 (85.7%) | 66 (94.3%) | 51/58/58 | 69/61/67 |
| Qwen3-8B | 69 (98.6%) | 64 (91.4%) | 69 (98.6%) | 59/52/56 | 70/64/69 |
| Llama-3.2-3B | 66 (94.3%) | 40 (57.1%) | 49 (70.0%) | 66/40/49 | 66/40/49 |

The trained-arm seed-to-seed discordance is **not observable** yet. Family-level discordance proxies:

| Proxy | Value |
|---|---|
| Qwen3-4B vs Qwen3-8B on C (cross-checkpoint) | 5/70 = 0.071 |
| Same comparison on E | 3/70 = 0.043 |
| Same comparison on R | 14/70 = 0.200 |
| Within Qwen3-4B, C vs R | 8/70 = 0.114 (7 C-only, 1 R-only) |
| Within Qwen3-4B, C vs E | 6/70 = 0.086 |

Qwen3-4B fails at least one form in 14/70 families and all three in only 1/70. Difficulty is concentrated in a small set of fragile families.

### 3.2 Model

Each family is solid (π = 1), fragile (π = p_f) or hard (π = 0). The mixture is calibrated so the E+R arm's C accuracy is p0 and the discordance between two seeds of the same arm is q0. The E+C arm raises every family's π proportionally to its headroom by a mean of δ, with no offsetting losses, which is optimistic. Seeds are conditionally independent given the family.

Grid: p0 ∈ {0.943 (pilot C), 0.857 (pilot R level, i.e. a harder test or a degraded arm), 0.70 (Llama-like)}; q0 ∈ {0.035, 0.071, 0.114, 0.200}; δ ∈ {0, 3, 5, 10} pp. Each cell uses 4,000 Monte Carlo datasets.

The decision interval is Wald on the seed-averaged d_i. On 300 datasets per check it was validated against a 2,000-draw percentile family bootstrap: power 0.717 vs 0.710 (decision agreement 98.7%) and 0.967 vs 0.967 (100%). Rerunning reproduces every output byte-for-byte (output SHA-256s in `manifest.json`; script SHA-256 `7620f4db…`). Run time is about 30 s.

### 3.3 Results at N = 100, S = 3 (`power_grid_n100.csv`)

P(95% lower bound > 0) for each scenario. Numbers in brackets are the median 95% half-width in pp.

| p0 (E+R on C) | q0 | δ = 0 (false support) | +3 pp | +5 pp | +10 pp |
|---|---|---|---|---|---|
| 0.943 | 0.035 | 0.016 [2.1] | 0.56 | 0.89 | impossible (headroom 5.7) |
| 0.943 | 0.071 | 0.023 [2.9] | 0.51 | 0.96 | impossible |
| 0.943 | ≥ 0.114 | infeasible with p0 = 0.943 | – | – | – |
| 0.857 | 0.035 | 0.017 [2.0] | 0.56 | 0.87 | 1.00 |
| 0.857 | 0.071 | 0.025 [2.9] | 0.42 | 0.78 | 1.00 |
| 0.857 | 0.114 | 0.027 [3.8] | 0.31 | 0.67 | 1.00 |
| 0.857 | 0.200 | 0.023 [5.0] | 0.22 | 0.56 | 1.00 |
| 0.70 | 0.071 | 0.020 [3.0] | 0.41 | 0.74 | 0.995 |
| 0.70 | 0.200 | 0.025 [5.0] | 0.21 | 0.45 | 0.95 |

Other quantities in the same grid:
- **Useful-gain claim** (lower bound > +5 pp): ≤ 0.025 at true +5 and 0.41–0.60 at true +10.
- **Single seed pair, exact McNemar, positive direction:** 0.13–0.37 at +5 and 0.47–0.88 at +10. So individual seeds will usually be non-significant even when the effect is real.
- **All 3 seeds positive:** 0.05–0.10 under the null and 0.58–0.97 at +5. Sign consistency is weak evidence.
- **Approximate 80%-power MDE:** about 3–7 pp, depending on p0 and q0.
- **Hoeffding bounded reference interval** (conditional_inference note): radius 27.2 pp at N = 100. It is valid but uninformative, so it is reported but not used for decisions.

N scaling (`n_scaling.csv`):
- Central case p0 = 0.857, q0 = 0.114. +3 pp: 0.31 / 0.55 / 0.73 / 0.96 at N = 100/200/300/600. +5 pp: 0.67 / 0.92 / 0.99 / 1.00.
- Ceiling case p0 = 0.943, q0 = 0.071. +3 pp: 0.51 / 0.83 / 0.94 / 1.00.
- **Only 100 frozen FINAL_TEST families exist.** Adding the 40 DEV families would break the DEV firewall, and more seeds do not add independent families.

Secondaries:
- **English retention (margin −2 pp, true difference 0):** P(lower bound > −2 pp) = 0.52 (q0 0.035) or 0.29 (q0 0.071). **Non-inferiority usually cannot be shown even when nothing is lost.**
- **Δ_C − Δ_R** null half-width: 2.9–4.3 pp, assuming C and R outcomes are independent within a family. This is approximate.

### 3.4 What 100 families can and cannot support

**Can:**
- Estimate Δ_C to about ±2–5 pp (±3–4 pp in the central cases).
- Detect a gain of about +5 pp with 0.45–0.96 probability, *if* the E+R arm has room below the ceiling.
- Reliably detect +10 pp when headroom exists.
- Rule out gains ≥ +5 pp if the true effect is about 0 (the expected upper bound is about +2–5 pp).

**Cannot:**
- Reliably detect +3 pp.
- Establish that the gain is "useful" (≥ 5 pp).
- Show English non-inferiority within 2 pp.
- Make topic-level or seed-process (training-randomness) claims.
- Get a below-0.25 p-value from seed-flip tests with S = 3.

**Pre-registered difficulty check.** Before training, run the unchanged model once on DEV (sanity use). If DEV C accuracy is ≥ 95%, pre-declare that Δ_C is ceiling-limited, report the headroom, and lead the paper with S2 and the precision statement. Neither the design nor the test set changes. Rerun the power script with DEV p0 for the record.

## 4. Analysis plan

1. **Completeness.** All 3,000 items must resolve. Infrastructure failures make the run incomplete and suppress headline numbers. Invalid, refused or truncated answers count as 0. There is no complete-case removal and no best-seed selection.
2. **Interval.** Use a 10,000-draw paired **family bootstrap, seed 101, conditional on the 9 checkpoints**. Resample whole family records (all arms × forms × seeds together) and use 95% percentile endpoints. Label it as an approximate conditional interval. Report degeneracy (all-zero d_i) and the number of distinct d_i values. Pooled resampling, equal family weights. Also report the Hoeffding interval and the Wald interval (identical decisions in validation) as references.
3. **Seed-specific effects.** Report each seed's Δ_C with its own paired bootstrap and exact McNemar counts (first-only/second-only), plus the range. Crossed family × seed resampling is a sensitivity analysis only. Never treat 300 family-seed rows as independent.
4. **Decision rules (primary only).**
   - **Support:** 95% lower bound > 0.
   - **Useful support:** lower bound > +5 pp.
   - **Informative null:** the interval contains 0 and the upper bound is < +5 pp. This rules out the proposed useful gain.
   - **Harm:** upper bound < 0.
   - **Inconclusive:** anything else.
   - Seed signs are reported as consistency, not as a test.
5. **Multiplicity.** There is one confirmatory test, Δ_C. S1–S3 are reported with unadjusted 95% intervals labelled descriptive. If any secondary is claimed inferentially, Holm applies across {S1, S2, S3} at α = .05, fixed now. Topic, operation-word and numeric analyses are exploratory.
6. **Retention-margin handling.** The −2 pp margin (proposed, not approved) is fixed before training.
   - **English retained:** only if the Ret_E lower bound is > −2 pp.
   - **English degraded:** upper bound < 0.
   - **Retention tradeoff:** Δ_C supported but the Ret_E upper bound < −2 pp.
   - Otherwise: "retention not established", with the interval reported. The margin is never widened after results.
7. **Endpoints.**
   - The **strict** scorer v1.0.0 is primary, unchanged.
   - **`numeric_literal_v2` is pre-registered now as a secondary.** It is v1 plus one rule: when the gold unit is rupees, accept a numeric final answer with a leading or trailing `₹`, `Rs`, `Rs.`, `INR` or `rupees` (optional whitespace), stripped before the numeric match. Everything else is unchanged.
   - v2 is versioned, implemented and unit-tested on Pilot-B outputs (proxy: Qwen3-4B E/R/C 69/61/67 vs v1 51/58/58), and its code is hashed before any trained-arm or FINAL_TEST output. It is never applied to the primary endpoint.
8. **Audit.** Run a two-AI-tagger output audit plus human check (Pilot-B method) on all failures of the E+R and E+C arms for C, separating format_only from substantive errors. It is descriptive and does not overwrite strict scores.

## 5. Optional controls (each adds cost; adopt before training or not at all)

| Control | What it answers | Added cost |
|---|---|---|
| **Devanagari R arm (E+D)** | Whether the R effect depends on script | 768 updates (+33%); new Devanagari renderings of TRAIN (160) and FINAL_TEST (100), plus human review; eval +9N (new arm) +10N (D form on all checkpoints) ≈ 1,900 generations. Most expensive; changes the FINAL_TEST file (needs a new frozen version) |
| **Self-translate baseline** | Whether translating C/R to English and then solving with the unchanged model matches E+C | 2 calls × 100 × {C, R} = 400 generations (about 1 h); the model makes its own translation, with no reference E used as an oracle |
| **Operation-word-balanced C analysis** | Whether Δ_C differs when C kept vs switched the R focal operation word | Zero compute; strata come from existing Phase-2 provenance tags. Strata of about 30–50 families mean descriptive only |
| **Second backbone (Llama-3.2-3B)** | Δ_C with headroom (pilot C 70%) | 2,304 more updates + 3,000 generations; doubles cost. Strongest option if the ceiling flag fires and budget allows |

## 6. Threats to validity

- **Ceiling and format artefacts.** Strict failures for Qwen3-4B are partly format errors (3 of 4 E failures; `rupye`). Training may fix these in all arms, which compresses Δ_C. The audit and numeric v2 separate this from mathematics.
- **Author/style shift.** FINAL_TEST and DEV were drafted by GPT, TRAIN by Claude, and GPT-drafted R was over-formal (68/100 repaired). This is useful as a transfer test. But a gain may reflect Claude-style adaptation, and only one reviewer accepted FINAL_TEST, with a second-annotator sample still pending.
- **Overfitting and memorization.** About 13 passes over 160 families. Watch E+E English and DEV sanity, and report training loss curves.
- **Token and compute asymmetry.** R and C prompts tokenize longer. Record input tokens, s/update and padding per arm.
- **Seeds.** S = 3 says little about training-process variance. Claims are conditional on these checkpoints.
- **Comparator overlap.** E+R and E+C share Hindi grammar, so Δ_C isolates English lexical mixing, and a small effect is plausible a priori.
- **Single scorer and single prompt.** Prompt v2 is frozen and there is no prompt tuning on any test data.
- **Firewall.** Pilot, Pilot-B and FINAL_TEST are never trained on. FINAL_TEST is evaluated once, after freezing.

## 7. Stopping and fallback if the D021 gate fails

D021 sets the gate as follows: median ≤ 56 s/update stays on Colab; 56–150 s moves to Kaggle 2×T4; > 150 s falls back to Qwen3-1.7B. All of this is decided before any results.

- **Problem with the D021 fallback.** Qwen3-1.7B failed the format rule (D029). Training on the English targets might teach the FINAL format, but this is unverified. **Proposal (needs a decision):**
  1. Apply the 128-update rule first.
  2. If that is still > 150 s/update, switch to Llama-3.2-3B, which passed D032 and has headroom, instead of Qwen3-1.7B.
  3. If memory, NaN or reload checks fail, fix the stack once under a new version. If they fail again, stop training.
- **Fallback study if training is infeasible by the minor-evaluation deadline.** Run a frozen-model study on FINAL_TEST: unchanged Qwen3-4B / 8B / Llama E/R/C, plus the self-translate baseline. It is pre-registered as descriptive and replicates the Pilot-B R < C finding on 100 independent-author families.
- **Mid-study stops.** A run that diverges (NaN or loss explosion) is logged and repeated once with the same seed after an infrastructure fix. If that fails, the seed is replaced by the next pre-declared seed (41, 43) **for all arms**. There is no outcome-based early stopping and no interim look at FINAL_TEST.

## 8. Open decisions for the user

1. Adopt the +5 pp useful gain and −2 pp retention margin, or revise them.
2. Approve the 128-update timing rule and the Llama-3.2-3B fallback, which would amend D021.
3. Approve the DEV difficulty check and the ceiling-flag rule.
4. Choose which optional controls to fund (recommendation: self-translate and op-word analysis yes; Llama only if the ceiling flag fires; Devanagari no).
5. Freeze this protocol with hashes before any training output exists.
