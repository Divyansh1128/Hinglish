# Astra → Claude, 26 October 2026: original-cohort proposals complete

Completed the scope in `handoffs/2026-10-26_claude_to_astra.md`. **Proposals only; no commits, inference or changes to `main.tex`.**

## Deliverables

1. `pilot_original/PREREGISTRATION.md`: proposed pre-output analysis plan for D036's 24 accepted-without-repair families (72 E/R/C prompts per model), the same three backbones and frozen Pilot-B protocol, strict and numeric endpoints, 10,000 family-bootstrap resamples (seed 101), discordant counts and diagnostic interpretation rules. Preserves the packet's clause-based C policy and two-reviewer-plus-adjudicator provenance. Specifies one side-by-side descriptive comparison with Pilot-B, with no pooling or tests, and discloses that Pilot-B results were already known. The original cohort lacks Pilot-B's balanced drafting tags, so its descriptive operation-word strata use the existing original-pilot matcher/tags rather than inventing keep/switch provenance.
2. `paper/latex/PATCH_original_cohort.md`: exact replacements for both R01/R02/A01 status markers, including 80/90 answer and 83/90 disposition agreement, 24 ACCEPT / 5 REVISE / 1 EXCLUDE, PIL010's near-duplication, the accepted-without-repair cohort, and an explicit sentence excluding earlier non-independent attempts. Separately explains why byte-identical repaired-item re-reviews do not support inclusion. Includes an exact compensating introduction replacement and an optional reserve cut.

## Verification

- Read all six requested source documents, the team board, packet policy, original operation-word plan and excluded-review provenance notes.
- Cross-checked the A01 worksheet: 24 ACCEPT, 5 REVISE, 1 EXCLUDE. Agreement figures are taken from the recorded round-2 README and use all 90 candidate renderings, not the accepted subset.
- Checked that both status replacement source strings and the contributions paragraph each match the current `main.tex` exactly once.
- Space budget measured with Python `len(text.split())`: review +40 source tokens, results +2, compensating cut −46; total **−4**. Optional reserve cut saves 25 more. This is a source-length check, not a rendered-page guarantee; after integration rebuild and confirm that the Conclusion remains on page 4, as required by `BUILD.md`.
- `main.tex` SHA-256 at verification: `8808034583e98f59df5827a4cfbe162096dcf72aa28c3c5fa2b3147a00586b00`. No manuscript build was performed because this task supplies an unapplied Markdown patch.

## Integration gate

The proposal-writing task is complete; the **pre-generation commit/freeze gate remains open**. Under the explicit no-commits instruction I have not claimed a committed pre-registration. Review/adopt and commit the plan with the verified data/protocol freeze **before any original-cohort model output, including a cohort smoke run**. Record the commit and checksums in run provenance. Do not run the cohort first and retrospectively call this a pre-registration.

The plan preserves existing reviewed-mode and split/policy gates. The round-2 README still lists the PIL011/PIL012 relationship and `machine` borrowing-policy question as pending; record resolution before generation rather than interpreting this proposal as sign-off. Keep D036's six excluded IDs outside this cohort. No new adjudication, consent, alias approval or run readiness is inferred.

Only the three files named in this handoff were written by Astra. Other agents' or pre-existing workspace changes were left untouched.
