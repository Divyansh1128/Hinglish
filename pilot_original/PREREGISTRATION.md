# Original-pilot evaluation: proposed pre-registered analysis plan

Written 26 October 2026 for the **24-family original-pilot cohort** (D036), mirroring `pilot_b/PREREGISTRATION.md` (D035). **Proposal for Claude's review; not yet committed or an executed freeze.** Commit the adopted plan and the verified data/protocol freeze **before any evaluation-model output on this cohort is generated**, including smoke runs on cohort items. Record the commit identifier in the run provenance. This handoff authorizes no commits or inference. Pilot-B results already exist and were read when writing this plan; pre-registration here applies only to the original cohort, not retrospectively to Pilot-B.

## Design and cohort

- 24 families × 3 forms (E, R, C) = **72 prompts per model**. Fresh context per prompt; seeded order.
- Inclusion is fixed by A01 acceptance **without repair**, not model performance: PIL001–PIL030 except PIL009, PIL010, PIL015, PIL019, PIL020 and PIL024. PIL010 is excluded as a near-duplicate of PIL002. The other five received REVISE; their returned re-review files were byte-identical and do not establish independent re-review. They are not added to this cohort later.
- The original 30 families received round-2 reviews from two independent reviewers (R01/R02) and adjudication by a third person (A01), as recorded by the coordinator. Across all 90 candidate renderings, reviewer answer agreement was 80/90 and disposition agreement 83/90. A01 decided 24 ACCEPT, 5 REVISE and 1 EXCLUDE. These agreement denominators describe the full review round, not just the accepted cohort. Earlier non-independent review attempts and subsequent edited review copies are excluded from the evidence used for this cohort.
- Use the unchanged accepted packet-v2 texts and the packet's **clause-based C definition**: productive English predicate, clause or mathematical relation alongside Hindi; object nouns alone do not qualify. Do **not** substitute D033's insertional C definition or Pilot-B's expanded borrowing policy.
- Backbones (unchanged, D030/D032): **Qwen3-4B (primary)**, Qwen3-8B and Llama-3.2-3B-Instruct. Each runs once with the same settings used for Pilot-B.
- Frozen protocol: `test1-english-final-v2`; greedy, non-thinking decoding; NF4 + FP16 on a T4; 1,024-token output cap; strict scorer v1.0.0; one infrastructure retry; no answer-dependent retries. Preserve the pinned model revisions, chat templates (including Llama's fixed date), secondary endpoint and generation settings. No prompt, scorer, unit-alias or rendering changes after seeing outputs.
- Before generation, record SHA-256 hashes for the converted accepted dataset, split manifest, review/adjudication inputs, borrowing-policy and unit-alias decisions, prompt/configuration and scoring/analysis code. Verify the 24 IDs and 72 text hashes against the raw packet and complete the existing reviewed-mode validation and split/policy gates. D036's cohort decision does not itself certify those implementation gates or resolve the README's outstanding PIL011/PIL012 relationship and `machine` borrowing-policy questions. Record their resolution before generation; any cohort/text change requires an explicitly revised pre-output plan. No freeze or gate completion is claimed here.

## Endpoints

1. **Primary:** strict accuracy (scorer v1.0.0) per form for Qwen3-4B, with correct/24 counts, percentages and 95% Wilson intervals. Invalid, refused, ambiguous and truncated responses count as incorrect under the frozen scorer.
2. **Secondary:** `numeric_literal_v1` per form (D018), using the unchanged grammar; strict-invalid reason counts. Report strict and numeric endpoints side by side, including disagreements. Pilot-B's known trailing-rupee-symbol limitation does not authorize a parser change; any later sensitivity analysis must be labelled post hoc and must not replace this endpoint.
3. **Paired:** E−R, E−C and R−C family-level strict-accuracy differences in percentage points, with 95% percentile intervals from **10,000 family-bootstrap resamples (seed 101)** and discordant counts (correct only in the first / only in the second form). Resample complete families, retaining each E/R/C triplet together; never treat 72 renderings as 72 independent units.
4. **Descriptive, per model:** the same tables for Qwen3-8B and Llama-3.2-3B, and the 4B versus 8B scaling contrast, retaining matched family IDs. Primary inference remains Qwen3-4B.
5. **Descriptive operation-word strata:** counts and percentages only for R/C accuracy using input-only tags frozen before generation. The original cohort has no balanced Pilot-B drafting design: do not infer or import Pilot-B's keep/switch/control provenance labels. Use the existing `operation_vocab_draft_v1` matcher and accepted-ID subset of `research/operation_vocabulary_2026-10-15.md`: per-form lexically ambiguous-word presence (`A_present`) and the fixed `{bhaag, bhinn}` subset. Verify text hashes and record the subset tag freeze before generation. Report denominators and empty cells as NA; do not adapt words or strata to outputs or claim a causal operation-word effect.
6. **After the run:** English-compliance tags and the D018 error taxonomy, with AI pre-tags followed by the adopted bilingual human audit of every output and A01 spot-checking disagreements with automatic scores. Report audit coverage and unresolved cases; AI tags alone are not human findings. Report tokens and latency per form.

## One pre-specified descriptive comparison with Pilot-B

Produce **one side-by-side table**, for each of the three backbones, showing each cohort's N, strict E/R/C accuracy and paired E−R, E−C and R−C differences, retaining the separately computed within-cohort intervals. Original cohort N=24; Pilot-B N=70. Describe the directions and magnitudes of the form gaps, whether R is lowest, and C's position relative to E and R for every model, irrespective of agreement with Pilot-B. Pilot-B values come from its frozen runs summarized in `results/pilot_b/SUMMARY.md`.

**No pooling, cross-cohort hypothesis tests, combined intervals or cross-cohort pairing.** This is a descriptive comparison planned with Pilot-B results already known, not an independent confirmatory replication. Different families, sample sizes, topic/operation-word composition, review processes (two reviewers plus adjudicator versus one reviewer) and C definitions preclude attributing differences to any single factor.

## Interpretation rules

- 24 families is a diagnostic sample. Report intervals but make no significance claims; topic and stratum results are descriptive. Do not interpret an interval excluding zero as a confirmatory discovery.
- Report the original cohort separately from Pilot-B and **never pool them**, including E and R. Label the original clause-based and Pilot-B insertional C definitions explicitly.
- Report all results whatever their direction, including null results, invalid outputs and failed runs. Keep excluded/repaired families outside all cohort denominators; disclose later-discovered defects without silently dropping observations.
- Incomplete runs: suppress headline accuracy, as the engine does; report completion/failure counts and reasons. Do not compare a partial cohort with a complete Pilot-B run as if both were complete. Distinguish completed automatic scores from pending human audits.
- No training or model selection on this cohort. FINAL_TEST (`phase2/`) is never evaluated here. Excluded development fixtures remain outside the cohort.

## Source record

`docs/DECISIONS.md` (D018, D030, D032–D036); `pilot_b/PREREGISTRATION.md`; `pilot/reviews_v2_round2/README.md`; `pilot/annotation_draft_v2/R01/README.md`; `research/operation_vocabulary_2026-10-15.md`; `results/pilot_b/SUMMARY.md`. Acceptance and review facts are recorded evidence; this proposed analysis plan is not a new human adjudication.

## Amendment 1 (26 October 2026, before any model output on this cohort)

R01's official stage-2 file marks 70 of 90 renderings (52 of the cohort's 72) with `_annotation_provenance: {"source": "AI prefill suggestion", "human_verified": false}`, a field the review form never writes. R01's stage-1 solves and all of R02's files carry no such marking. The cohort is therefore described as: **mathematics independently solved by two humans (R01, R02 stage 1); language and equivalence review by one human reviewer (R02) plus the adjudicator (A01); R01's AI-prefilled stage-2 judgments are recorded (`judgment_source = ai_prefill_unverified`) and excluded from any human-review or agreement statistic.** Human inter-reviewer agreement is reported only for stage-1 answers (and for the 20 R01 renderings with human stage-2 judgments). Endpoints and analyses are otherwise unchanged. Decision D037.
