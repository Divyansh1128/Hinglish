# Proceeding after the completed training study

Date: 11 November 2026. Status: **recommended next steps**, not adoption of a new experiment. User authorised the GitHub documentation update. Existing experiment decisions remain D043–D052; this document neither changes those decisions nor authorises GPU work.

## 1. Finish the current evidence package

Keep the pre-registered negative result unchanged and report the pilot and training questions separately. Pilot observation: R is lowest in two cohorts, with equal observed E/C accuracy for Qwen. Training result: the tested E+C recipe is worse than E+R on C; all fine-tuned arms decline against the unchanged model. Do not claim a universal language ordering or a proven cause of training degradation.

Before sharing/submission, reconcile paper, thesis/report and presentation numbers against the final result and audit files; replace obsolete pending statements, verify review provenance and consent/credit, check citation/BibTeX validity, and rebuild/visually inspect the final PDFs and slides. Preserve historical drafts with clear labels rather than treating them as current instructions. A generated PDF's presence alone does not establish that it matches today's source.

Completion criterion: a consistent paper/report/presentation package, with limitations and deviations disclosed and no stale completion claims in its navigation.

## 2. Obtain faculty/mentor direction on paper scope

Recommended direction: retain the reproducible scoring-aware audit and include the controlled negative training follow-up at a level appropriate to the short-paper space limit. Let the longer report carry the full training and audit detail. Discuss whether the mentor prefers the follow-up in the main narrative or supporting material; do not remove the result because it is negative.

D039 records mentorship submission #12, expected feedback on 5 December and final submission on 15 December 2026. These are recorded planning dates, not freshly verified deadlines; verify the official call before scheduling submission. Mentorship submission is not acceptance and does not substitute for final submission. Faculty/mentor scope choices and any new experiment budget remain human decisions.

## 3. Consider a separately registered follow-up only after scope/budget agreement

A useful candidate is to test whether English solution-target design contributes to the across-arm degradation. This is a hypothesis motivated by shorter generations, unit errors and retained numeric performance loss, not an established mechanism.

Design the smallest controlled study that changes the target policy while holding underlying training content, language-arm construction and other factors fixed. Specify the resource/exposure trade-off: longer targets change supervised token counts, so matching examples alone does not isolate explanation content. Freeze scoring/units and the analysis before new evaluation; include an unchanged baseline and a predeclared retention criterion.

Use fresh reviewed held-out families for any new confirmatory claim. The existing FINAL_TEST is now observed and must not be presented as untouched for a revised recipe. Keep old results, audit overlays and exclusions unchanged. Set scope, reviewer workload, seeds, stopping rules and compute budget before launch. Do not start a broad model sweep or tune toward a positive outcome.

## Immediate handoff

- Documentation work now: current GitHub landing page/status, current team-board entry and this proposed sequence.
- Next practical work: consistency/build/visual checks of the submission and faculty-facing artifacts.
- Human decision when ready: faculty/mentor paper scope; whether a distinct follow-up is worth the time and budget.
- No new training, rescoring, changes to frozen packets, or FINAL_TEST regeneration in this update.
