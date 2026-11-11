# Current project status

Updated: **11 November 2026**. This replaces the obsolete 11 October status summary; earlier text remains in Git history. Evidence baseline: commit `89284ed` (10 November).

## Completed work

| Workstream | Verified/documented state | Evidence |
| --- | --- | --- |
| Pilot software | Resumable inference, exact strict scoring, diagnostic endpoints, paired analysis, audit/export | `test1_pilot/`, `secondary_analysis/` |
| Model screening | Seven candidates screened; three qualified under fixed rule | D028–D032 |
| Pilot-B | 70 families, three models, all complete | [summary](../results/pilot_b/SUMMARY.md) |
| Original pilot | 24 accepted families, three models, all complete; separate cohort | [summary](../results/pilot_original/SUMMARY.md) |
| Training feasibility | T4 smoke passed on 28 October; checkpoints reloaded; memorisation risk disclosed | [smoke](../results/training_smoke/README.md) |
| Main training | Nine Qwen3-4B QLoRA adapters, three arms × three seeds, 60 updates each, frozen | [training](../results/phase2/train/README.md), D043–D051 |
| Final evaluation | Ten checkpoints × 300 renderings = 3,000 completed outputs | [analysis](../results/phase2/final_test/phase2_analysis.md), D052 |
| Failure audit | Human labels recorded for all 331 incorrect C outputs from ER/EC | [final counts](../results/phase2/audit/final_audit_summary.json) |
| Writing | Paper and full report sources include Phase-2 results; PDFs exist | `paper/latex/`, `report/` |
| Publication | Mentorship draft submitted 26 October per D039; no acceptance or final-track submission claimed | D039 |

## Findings and limits

Pilot-B E/R/C strict accuracies: Qwen3-4B 94.3/85.7/94.3%; Qwen3-8B 98.6/91.4/98.6%; Llama-3.2-3B 94.3/57.1/70.0%. R is lowest in both pilot cohorts. Equal observed Qwen E/C accuracy does not prove equivalence, and does not generalise to all datasets: the unchanged Phase-2 model scores 85/63/66%.

The primary training contrast is **E+C − E+R on C = −4.33 pp [−8.00, −0.67]**, decision **Harm**, with negative contrasts in all three seeds. Numeric secondary endpoints give −5.67 pp [−11.00, −0.67]. All trained arms are below the unchanged model. The bootstrap is conditional on these checkpoints, not an estimate of all training-seed uncertainty. This is evidence against benefit for the tested recipe, not a universal negative statement about code-mixed training.

Human-audited C failures: ER 46 format-only + 113 substantive; EC 40 format-only + 132 substantive. Formatting does not explain away the relative EC deficit. The overall trained-model decline accompanies shorter outputs and more unit failures; the causal role of terse targets remains unisolated.

Review limitations remain: Pilot-B/FINAL_TEST rely on one primary bilingual reviewer, TRAIN/DEV were sample-reviewed, and author/template dependence limits generalisation. Original-pilot AI-prefilled judgments are not counted as human review. Prior work already reports the R<C ordering; novelty rests on the audit protocol, data and controlled follow-up rather than that ordering alone.

## Integrity and verification

The 10 November independent verification reproduced strict counts and the primary bootstrap exactly. The 11 November read-only exploratory checker validates all ten final archives, 3,000 outputs and all 60 published strict/numeric checkpoint × form counts. Two generation infrastructure failures were preserved; all final items resolved, with one committed response per rendering. Failed process launches and stale-lock recovery are disclosed in the final-results README.

No experiments or frozen artifacts were changed in this status update. Human review claims above describe the returned records, not independent verification that a human performed each judgment.

## Next gate

Move to submission/report consolidation, not tuning on the used FINAL_TEST. Follow [the next-step plan](NEXT_STEPS_2026-11-11.md). New target-design experiments require a separate protocol and genuinely fresh held-out evaluation. No new compute or experiment is authorised by this status document.

Historical `docs/minor_project/report_draft.md`, `paper/README.md`, older team-board rows and guide PDFs may contain obsolete pending claims. Use this status and the linked result artifacts for current facts; reconcile and verify generated documents before sharing.
