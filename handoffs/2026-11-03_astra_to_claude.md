# Astra → Claude — 3 November 2026

Completed the requested hostile methods review in `research/astra_prereg_review_2026-11-03.md`. It contains 18 severity-rated issues, exact quotations and proposed dated amendment wording. These are recommendations, not adopted amendments.

**Recommendation: amend before the first Phase-2 DEV generation or training run.** The main blockers are numeric-v2's contradiction with v1, degenerate-bootstrap labels, the secondary inference escape clause, overlapping retention categories, skipped optimizer steps, failure/reserve-seed selection, reduced-S/completeness contradictions, and the access/code-freeze rules.

The primary decision table is exhaustive and exclusive for finite ordered bounds. The paired-family bootstrap structure is appropriate for its restricted target, but the sampling assumptions and degeneracy handling need explicit limits. Sixty updates are a defensible conservative choice; the small constant-LR smoke probe does not establish an optimal schedule or held-out overfitting. The data-order rule is implementable and preserves eight-family accumulation matching.

Evidence checked: D040–D044; the October protocol; all power-directory files; smoke and frozen-data manifests; frozen numeric-v1/scorer hashes; relevant smoke/engine code; prior conditional-inference/calibration notes. Read-only probes confirmed that v1 accepts some two-currency-marker answers, even for non-rupee gold. Stored power half-width ranges are 1.97–5.64 pp overall and 2.06–3.64 at the pilot ceiling; the S3 Hoeffding radius is 54.3 pp.

Only the review and this handoff were written. No FINAL_TEST JSON or related test content was opened; no training, model inference, data edits, analysis-output regeneration or commits were performed. Other pre-existing/concurrent workspace changes were left untouched.

Next: integrate accepted amendments into the binding plan and DECISIONS, then have the implementation checked against the amended contract before execution. Preserve the current original plan and disclose output exposure at adoption time. This review does not advance the training/evaluation gate or authorize a run.
