# Current project status

Updated: 11 October 2026. This file separates completed work from proposals.

| Workstream | Current evidence | Next step |
| --- | --- | --- |
| Literature and novelty | Expanded 14-work audit complete; exact matched E+C versus E+R control not located in inspected material | Proceed provisionally to human review; retain unresolved Indi-RomCoM artifact question and bounded novelty claim |
| Research design | E/R/C definitions, family-level analysis, exposure controls, draft review/scoring/split policies documented | Human-freeze borrowing policy and accepted data; refine later confirmatory sample/resource design |
| Pilot implementation | Self-contained Colab notebook, strict input validation, incremental inference/resume, common scorer, reports/audit/export and software tests implemented | Execute only after accepted inputs and freeze |
| Fake demo | Six synthetic outputs completed; exported checksums and original scores verified | Retain as software evidence only |
| Real Qwen GPU smoke | Six short scored-fixture generations plus one format-only inference on Tesla T4; model loading and generation succeeded | Treat as limited inference feasibility, not research accuracy or training fit |
| GPU smoke scoring diagnosis | Original automatic 0/6 invalid-unit scores preserved; all six extracted numeric values match fixture gold; count-fixture unit metadata repaired in demo-v2 | Keep strict dimensionless suffix policy; diagnose formatting separately without silently replacing original scores |
| Human dataset review | Thirty AI-authored candidate families / 90 renderings prepared; user reports reviewers available; randomized packets and blank decision forms delivered | Actual independent solves, equivalence/classification/naturalness review, adjudication and family/split audit |
| Training | Protocol/validation preparations only; no fine-tuning, RL or successful training hardware run | Separate bounded training feasibility test only after appropriate inputs and explicit scope |
| Research conclusions | No completed reviewed pilot or confirmatory results | Analyze frozen reviewed pilot before deciding the next experiment |

## What the real GPU smoke tells us

The returned run used Qwen3-4B, immutable model/tokenizer revision `1cfa9a7208912126459214e8b04321603b3df60c`, on a Tesla T4 with 14.56 GiB reported device memory. The stack included bitsandbytes 0.50.2, Transformers 4.51.3 and torch 2.11.0+cu130. The six scored-fixture generations took about 33.79 seconds in total; none were truncated and no infrastructure failures were recorded. Per-generation PyTorch reserved peak reached about 4.19 GiB. Device free-memory values are endpoint observations, not continuous minima. Model load took about 224.75 seconds and may include download overhead.

The original automatic score was 0/6, with all outputs failing unit validation. Three count outputs exposed a fixture-authoring error: blank canonical gold unit for a question asking for counters. The count fixture is repaired in a new demo version. Three fraction outputs appended words such as whole/fraction/part, rejected by the frozen strict dimensionless policy. Numeric-value checks diagnose these failures; they are not independently human-reviewed semantic scores. One R explanation also drifted into Hindi despite the English-output instruction. See the [full audit](../research/test1_gpu_smoke_audit_2026-10-10/README.md).

## Practical team handoff

The coordinator distributes the separated review packets, preserves submissions and versions, and manages the split-exclusion ledger. R01 and R02 independently solve before seeing gold, then review all triplets. A01 resolves documented disagreements, checks gold/units, and confirms real decisions. Code reviewers can inspect the model-free tests and notebook configuration. These are roles to assign, not claims that particular people completed work.

After review, return four stage1/stage2 reviewer JSONs and the adjudication JSON with any repair/re-review records. No local DRAFT input should be relabeled ACCEPT just to pass validation. Pilot families, rejected drafts, format fixtures and all descendants stay excluded from future confirmatory training and final test. Later training/final-test families and the 16 planned training-smoke families have not been fabricated.

The next research deliverable is a human-reviewed, versioned and frozen pilot dataset and split manifest. After that, run the main notebook's reviewed mode, return its results ZIP and executed notebook, and inspect failure modes, paired outcomes, uncertainty, tokens and memory. A descriptive gap from 30 families cannot demonstrate an E+C training benefit.

## Research audit update

The [updated literature matrix](../research/astra_closest_work_update_2026-10-10.md) recovered Anand’s official technical appendix and confirmed its Romanized-Hindi exclusion. XCOT already retains English responses for translated queries; Sarvam-M supplies a Romanized mathematical training precedent. These narrow the claim to the controlled comparison and useful independent-style transfer.

The [authoritative design proposal](../research/astra_experiment_spec_v1.md) keeps E+E/E+R/E+C essential and corrects the illustrative three-arm, three-seed, 256-update budget to 2304 updates. The schedule, final sample size and practical effect/retention margins remain unapproved. [Model-free power calculations](../research/astra_validity_and_power_v1.md) show why 30 families are a diagnostic pilot rather than a justified confirmatory sample; all seven planning-code validation categories passed. These calculations are not training results.

The [static review audit](../research/astra_review_readiness_v1.md) found no completed human acceptance. PIL026-C adds explanatory wording requiring review; candidate lineage, naturalness and reviewer gold exposure remain human decisions. The audit JSON contains proposed gold and should not be distributed as blind stage1 material. Software, original generations/scores and draft questions were not changed by this research phase.

## Current review distribution: draft v2

[Version 2](../pilot/annotation_draft_v2/README.md) applies eight AI wording repairs across six families after a three-agent pre-review. All 30 candidates remain DRAFT, with no human acceptance or ancestry certification. v1 and any v1 submissions must be preserved; new v2 forms reject mismatched versions. Gold, units, scorer and model settings are unchanged. Verification passes 30-family/90-rendering coverage, 27 conversions, four JavaScript syntax checks, simulated import/export/resume, 22 checksums, exact repair/version mapping and unchanged v1 fingerprints. A rebuild-overwrite guard was also verified. Full real-browser annotation behavior remains unverified. See [today’s progress](PROGRESS_2026-10-10.md).

## 11 October: analysis and annotation design

Completed a [conditional inference contract](../research/conditional_inference_2026-10-11.md), separating fixed-benchmark description, new-family inference, new-author inference and training-process uncertainty. A [model-free stress test](../research/conditional_calibration/README.md) ran 18 synthetic cases, with 250 datasets and 10,000 bootstrap draws per case. Five validation categories passed. Rare-event and broader-target failures prevent treating this as final calibration approval. The original pilot implementation was not changed.

A [sampling/annotation plan](../research/sampling_and_annotation_plan_2026-10-11.md) offers 100/300/600-family future scope options with explicitly hypothetical person-hour estimates and independent-author safeguards. No final sample, resource budget or practical effect margin has been approved. The immediate experimental gate remains actual v2 human review, exposure disclosures and adjudication. No new model inference or training took place.

User decision recorded 11 October: annotation budget remains undecided; retain multiple future scope options. The 30-family diagnostic pilot is unchanged.
