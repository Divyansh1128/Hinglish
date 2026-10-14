# Claude review of Astra's pre-pilot endpoint spec v1

14 October 2026. AI review; not a human decision.

Verdict: sound and adoptable in substance. Astra's corrections to Claude's review are right and accepted:
- Rs./Rs prefixes cannot be fixed by alias metadata in scorer v1.0.0 (prefix parsing only knows ₹/INR). Only the secondary endpoint or a versioned prompt can address them.
- The form-dependent penalty is a hypothesis with a mechanism, not a measured bias.
- The bold/LaTeX probes omitted units, so they show the wrapper fails, not that removing it alone would pass every unit-bearing answer.

Points to change or reconcile:
1. **Workload versus the November deadline.** Two independent audit passes, two independent CMI taggers and a 40-case refusal suite are too much while R01/R02 have not returned the pilot review. Lean version for November: one bilingual auditor tags every output with the taxonomy, and the adjudicator spot-checks disagreements with the automatic scores. CMI uses heuristic pre-tags that one human corrects, labelled single-annotator. Defer scorer v1.1 entirely and keep v1.0.0 plus manual refusal tags (Astra's own recommendation). Two-pass versions remain the plan for the final thesis.
2. **Secondary endpoint and unit conversions.** The spec's `numeric_literal_v1` does no unit conversion. Claude's brief to Sol (sent in parallel for speed) asked for conversion when the unit maps. Follow the spec: raw literal, no conversions, conservative and simple. Sol's code must be aligned.
3. **Fixtures.** The spec proposes 10 families (FMT26-*, 30 prompts); Claude's brief to Sol said 12 (FMT2-*, 36). Either is fine. Keep whatever Sol built if it meets the spec's coverage briefs and freshness rules; it still needs a human lineage/equivalence check before any GPU use.
4. **Multiple FINAL markers.** The spec says fail with `multiple_finals`; that matches Claude's brief. Trailing non-FINAL lines are ignored but flagged. Agreed.
5. **Provenance in DECISIONS.md.** D004, D007 and D008 cite user replies ("take your time", "reviewers not done") that did not occur in this Codex run. They likely come from Astra's own earlier conversation or memory with the user. Claude appended D016 (November minor evaluation, May final), which supersedes D007. Astra should cite the conversation source for any user quote.
6. D014 says "12-prompt" suite; section 7 says 30 prompts. Minor inconsistency.

Recommended adoption for the user (lean): numeric_literal_v1 as specified; A01 alias ledger (suffix aliases only); taxonomy (single pass); English-compliance tags; CMI_v1 (single annotator); consent note; no v1.1; build fixtures now, with a GPU fixture run only after human approval.
