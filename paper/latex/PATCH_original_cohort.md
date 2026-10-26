# Proposed original-cohort status patch

26 October 2026. **Proposal only: do not treat this file as an applied manuscript change.** Targets are the two R01/R02/A01 TODOs in `main.tex`. Review facts come from D036 and `pilot/reviews_v2_round2/README.md`; the excluded first round is documented in `pilot/reviews_v2_returned_2026-10-20/PROVENANCE.md`. The agreement counts cover all 90 round-2 renderings, whereas A01 dispositions count 30 families. This patch reports no original-cohort model results and makes no claim that its pre-registration has been committed.

Apply replacements 1–3 together. Replacement 3 pays for the added review detail in replacement 1; replacement 2 also saves space. Keep every unrelated TODO unchanged.

## 1. Section 3: completed independent review and exclusions

Replace this exact opening sentence of `\paragraph{Bilingual human review.}` (leave the paragraph heading and following Pilot-B/FINAL_TEST sentences in place):

```latex
Each of the original 30 families gets two independent blind solves and an adjudicator \todo{completion status of R01/R02 review and A01 adjudication}.
```

with:

```latex
Two independent round-2 reviewers (R01/R02) reviewed all 30 original families, agreeing on answers for 80/90 renderings and dispositions for 83/90. Independent adjudicator A01 accepted 24 families without repair, required five revisions and excluded PIL010 as a near-duplicate of PIL002. Earlier review attempts were non-independent and excluded. The five repaired families remain outside the cohort because their returned re-reviews were byte-identical, not independent.
```

The sentence about earlier attempts is the required disclosure; it does not describe the retained round-2 reviews as non-independent. The final sentence separately explains why the five repaired families are excluded. Do not replace either with a claim that all 30 families passed review.

## 2. Section 6: replace the stale cohort-status sentence

Replace:

```latex
The original 30-family pilot, under two-reviewer adjudication, will be reported separately \todo{R01/R02/A01 status} and is never pooled with Pilot-B.
```

with:

```latex
The original cohort comprises the 24 families accepted without repair (\S\ref{sec:data}); its evaluation will be reported separately, never pooled with Pilot-B.
```

This is prospective about evaluation, not review completion. It does not assert that any original-cohort generation or analysis has occurred.

## 3. Compensating cut: Section 1 contributions paragraph

Replace the entire paragraph beginning `Lower accuracy on code-mixed or Romanized math input` with the following shorter version. This retains the prior-work acknowledgment, all three contribution types and the fixture exclusion boundary (also stated in Section 5):

```latex
Prior work reports code-mixed and Romanized math gaps \citep{yang-chai-2025-codemixbench,sarvam-2025-sarvamm,sthanika-2026-codemix}. We contribute: (1)~\textbf{a measurement caution} about form-dependent scoring and output-language failures across models; (2)~\textbf{a reviewed E/R/C resource} with Pilot-B's balanced operation-word design; and (3)~\textbf{a frozen diagnostic pilot} with strict and numeric endpoints. Development evidence (\S\ref{sec:dev}) uses 12 fixture families permanently excluded from every split.
```

## Space budget and integration check

The word budget below uses whitespace-delimited LaTeX source tokens consistently, including the removed TODO text; it is a reproducible editing budget, not a claim about rendered line counts.

| Replacement | Before | After | Change |
| --- | ---: | ---: | ---: |
| 1: review status | 22 | 62 | +40 |
| 2: results status | 19 | 21 | +2 |
| 3: contributions cut | 99 | 53 | −46 |
| **Total** | **140** | **136** | **−4** |

Of the 46 tokens saved by replacement 3, allocate 40 to replacement 1 and two to replacement 2, leaving four spare. This supplies an equal-or-greater cut for each addition. Do not add the new review text without its compensating cut.

`BUILD.md` records that the current main text already fills four pages. After applying the whole proposal, rebuild with `tectonic paper/latex/main.tex` and verify that the Conclusion still ends on page 4 and there are no new overfull boxes. A non-increasing word budget alone cannot certify pagination. If line wrapping requires further space, remove this exact 25-token introductory sentence as a reserve cut:

```latex
A drop could come from vocabulary, spelling, mixing, wording or the evaluation protocol itself, so we hold the mathematics fixed and vary only the form.
```

Count the reserve sentence directly before applying it; it is optional and is not included in the base budget. No change to the build, figures, bibliography, model results, ethics TODOs or review records is proposed. The clause-based/insertional C distinction remains in the existing Section 3 paragraph.
