# Phase-3 design: explanation-preserving targets for E+E / E+R / E+C

11 November 2026. Owner: **Astra (research)**. Deliverables: this design and the pre-registration draft (archived at `research/phase3_prereg_astra_draft_2026-11-11.md`; adopted with changes as `PREREGISTRATION.md`). **Core design decided by Claude under the user's delegation D017**, as conveyed in the task; this is not a claim of human adjudication. The companion registration completes operational details for adoption before generation. No execution, freeze, independent review or commit is claimed by these drafts.

## 1. Motivation and question

Phase 2 estimated strict Δ_C (E+C minus E+R on C) at **−4.33 pp [−8.00, −0.67], Harm**. Every trained arm lost English accuracy against unchanged: EE −23.67 pp, ER −25.67 pp, EC −26.33 pp. Pooled median output length fell from 113 to 42 tokens. All arms supervised the terse `reference_solution_en`; D050 noted the shortening already on DEV and correctly kept the registered recipe unchanged.

The follow-up asks: **with English solution targets drawn from the unchanged model's own visible explanation style, does E+C training beat E+R on held-out C?** Preserving explanation style is the intervention rationale. Phase-2 length associations and failure tags do not prove a causal explanation for its loss. Neither this follow-up nor a cross-phase comparison isolates style from all other changes.

Source basis: `phase2/PREREGISTRATION.md` with Amendments 1–3; `docs/DECISIONS.md` D040–D052 (and delegation D017); `results/phase2/final_test/README.md` and `phase2_analysis.md`; `analysis/phase2_exploratory/README.md`; `results/phase2/audit/README.md`; `report/phase2_chapter.tex`. The final audit section records human checks of all 331 failures; earlier “65 only” statements surviving in the chapter are stale. The drafts use the completed full-check account and do not modify the chapter.

## 2. What changes and what stays fixed

| Component | Phase-3 choice |
|---|---|
| Targets | One greedy unchanged-Qwen E output per TRAIN family; exact accepted text plus `<|im_end|>` |
| Admission | Strict correct, English (Devanagari → reject; fixed Romanized-Hindi word list → human check of flagged rows only), terminal FINAL, nontruncated, all form-specific sequences ≤1,024 tokens |
| Minimum | Q ≥120: retain qualifying families only. Q <120: halt before training; continuation needs a dated amendment (no fallback teacher) |
| Arms | EE, ER, EC; two examples/family, identical target tokens across forms, equal inclusion and exposure across arms |
| Training | Same pinned base, D021 stack/T4, optimizer, NF4/LoRA, LR schedule, paired seeds 11/22/33, exactly 60 updates |
| Filtered-set order | Same SHA-256 pass ordering; concatenate passes and take 480 family visits = 960 examples. Exactly three passes only when N_train =160 |
| Evaluation | Same 100 FINAL_TEST families and hash; nine new adapters evaluated once after new freeze; unchanged outputs reused |
| Primary | Strict Δ_C; same analysis code, bootstrap and amended decision rules |
| Descriptive | English retention (−2 pp), S2/S3, numeric endpoints, length, audit and each arm's cross-phase changes |

The registration supplies complete rules for language review, length failures, the Q ≥ 120 halt, exposure, degeneracy, seed attrition and infrastructure recovery. An overlength self-target is ineligible across every arm; it is never truncated or edited. Generation/selection sees only TRAIN, never DEV or FINAL_TEST.

## 3. Test reuse and baseline identity

FINAL_TEST stays `phase2/final_test.v3.json`, SHA-256 `da89dd9a626e438dffca39e3a74c4c8abac6bb57501495723b87e6ee143f3d46`. It is disjoint from training but was already evaluated and audited in Phase 2. Phase 3 is designed in light of those findings. No fresh-test independence is claimed, and historical item-level audit exposure is acknowledged. The rule now is no item-level tuning, no gold/alias repair and no new semantic inspection before adapter freeze.

Reuse gives a matched, affordable comparison on the same benchmark, provided the Phase-3 recipe is fixed prospectively and all outcomes are reported. It is weaker than a fresh holdout: design adaptation can exploit benchmark characteristics even without individual-item tuning, and nominal intervals do not include that selection uncertainty.

The current engine, prompt and analysis source hashes were checked against `phase2/IMPLEMENTATION_MANIFEST.md` and match. The intended generation configuration is unchanged (prompt v2, greedy/non-thinking, pinned Qwen revision, NF4/FP16, SDPA math, output cap 1,024, context 2,048). Therefore the planned baseline is the **existing 300 unchanged FINAL_TEST outputs**, not a rerun. A future gate must bind the archived baseline to its original manifest and verify equivalence with the Phase-3 execution configuration. New training/target code requires a new manifest, so pretending that the whole old manifest hash still applies would be incorrect. If inference configuration actually changes, halt and amend before evaluation, then obtain one baseline under that configuration after freeze. The same equivalence bridge supports reuse of the 120-output unchanged DEV archive.

## 4. Interpretation and precision

Strict Δ_C is the sole pre-specified primary contrast, seed-averaged within each of 100 paired families. Reuse `phase2_analysis/analyze.py` for the statistical calculations; add reviewed Phase-3 provenance plumbing without changing its statistical mechanics. Bootstrap: 10,000 samples, `random.Random(101)`, sorted IDs, shared matrix and linear quantiles h =9999p. Preserve the degenerate override, exact label boundaries, reduced-S restrictions and independent English flags introduced by the amendments.

D040's practical expectation is about ±3–4 pp; the corrected scenario range is 1.97–5.64 pp half-width, not guaranteed. Phase 2 realized 3.67 pp. Small effects (+3 pp), Useful support (lower bound >5 pp), and English retention within −2 pp remain poorly powered. No new simulation is necessary. Intervals condition on the trained checkpoints and target set and omit training-seed uncertainty and adaptive test reuse.

Cross-phase reporting compares each arm's accuracy and output length with its Phase-2 counterpart, **descriptive only, different training data**. Even with the same underlying candidate families, targets differ; filtering also changes membership/repetitions and longer outputs change supervised-token volume. A rise across all arms would be compatible with a better recipe but would not prove that explanation length caused recovery.

## 5. Execution, cost and review gates

1. Adopt and archive the plan; Sol reviews the generator, filtering/fallback, provenance bridge and enforcement code. Freeze target-generation implementation and E-only TRAIN payload before its first output.
2. Generate ~160 unchanged E outputs, score/review, apply the fixed fallback if triggered, and freeze exact targets, source/rejection ledger and all-form token checks.
3. Freeze training code, five seed exposure lists (including reserves), attempt plan, analysis wrapper/core and reused DEV evidence. Execute nine runs in slots 11/22/33, EC→ER→EE, with the same locks and typed recovery rules as amended Phase 2. Record DEV sanity only.
4. Sol verifies the new adapter freeze, all hashes, retained seeds and archived unchanged-model compatibility. Freeze evaluation payload. Evaluate once, suppressing previews until all required records are complete.
5. Run frozen analysis and an independent Sol recomputation. Two independent AI taggers review every ER/EC strict failure on C; humans check **every audited output**, preserving disagreements and unresolved judgments. Report every outcome and deviation.

The detailed before-step hash checklist is in registration §11: plan; data; generator/config/model/tokenizer/shards; raw target archive and exact texts/token IDs; inclusion/exposure lists; trainer/labels/attempt/locks; analysis/scorers/notebooks; baseline evidence; adapter/config/log/DEV archives; final journals; verification/audit outputs. Hashes of future artifacts remain pending, not invented.

Nominal work is 160 teacher generations, 9 ×60 =540 updates, **2,700 new FINAL_TEST generations** (3,000 analysis records minus 300 reused unchanged), and separately 1,080 DEV sanity generations. Total new generations including DEV: 3,940. At ~12 s/output, generation is ~13.1 T4 hours; Phase-2-like training adds ~3.1 hours, with longer targets potentially increasing it. Allow roughly 16–23 T4 hours plus setup/recovery uncertainty; this is a planning estimate, not a measured cap. Claude fallback and human target/audit review require additional non-GPU effort. Any allowed changed-config baseline branch adds 300 final-test generations.

## 6. Design issues raised by Astra, and Claude's resolutions at adoption (12 Nov 2026, D053)

Resolutions: (1) the treatment is redefined as *own-style* targets; no richness gate; explanation status descriptive only. (2) Fallback removed; Q < 120 halts. (3) The filtered-exposure extension is accepted; it is never described as identical dose across phases. (4) Test reuse accepted and disclosed; a fresh holdout remains future work. The original issue text follows.


- **Does the admission rule deliver the intended treatment?** A strict-correct, English, terminal-FINAL output can still be a short answer or labelled equations. The fixed prompt cannot guarantee rich explanations. The draft records explanation status without introducing an unrequested eligibility threshold. If explanation-rich supervision is essential, add an explicit explanatory-proposition gate before generating anything, and specify how it affects Q/fallback.
- **Fallback changes the intervention.** Q=120 yields pure self-distillation on 120 families, whereas Q=119 can yield mixed Qwen/Claude targets on all 160. This abrupt change affects teacher, difficulty and token exposure. A halt-only minimum or separately named mixed-target study would be easier to interpret; the draft nevertheless implements the requested fallback prospectively and discloses it.
- **Filtering and 60 updates cannot preserve exactly three passes.** The draft prioritizes the decided 60 updates and paired exposure, extending the original permutation stream deterministically. This increases repeat exposure on selected families; it must not be described as identical training data/dose across phases.
- **Reused test evidence has a ceiling on its strength.** No item-level tuning is allowed, but Phase-2 audit observations already exist and the intervention responds to this benchmark's results. A fresh held-out replication would support stronger generalization claims. The present draft does not add data collection or alter the decided test set.

The next gate is adoption and Sol's implementation verification, not training authorization inferred from a draft. No Phase-2 file, result or decision is changed by these deliverables.
