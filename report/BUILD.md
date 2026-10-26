# Final BTech report: build notes

## Files

| File | What it is |
|---|---|
| `final_report.tex` | Report source (`report` class, 12pt, A4, 1.5 spacing) |
| `references.bib` | Copy of `paper/latex/references.bib` (the verified citations). Only change: a stray `}` after the `khullar-etal-2026-script` entry was removed. Note that the same stray brace is still in `paper/latex/references.bib`. |
| `figures/accuracy_by_form.pdf` | Copied unchanged from `paper/figures/` (Pilot-B accuracy, Figure 6.1) |
| `figures/original_cohort_accuracy.pdf` | Regenerated from `results/pilot_original/*/per_rendering.csv` (Figure 6.3) |
| `figures/pilotb_r_by_stratum.pdf` | Regenerated from `results/pilot_b/*/per_rendering.csv`, using the stratum rule in `results/pilot_b/strata.py` (Figure 6.2) |
| `figures/make_figures.py` | Script that regenerates the two figures above from stored scores only (no rescoring) |
| `final_report.pdf` | Built output: 60 pages (12 front-matter pages i–xii, then 48 numbered pages; Chapters 1–9 run from page 1 to page 37) |

## Rebuild

```sh
cd "report"
/opt/homebrew/bin/tectonic final_report.tex        # runs XeTeX + BibTeX as many times as needed
```

Tectonic downloads the packages it needs on the first run, so it needs network access then. The fonts are TeX Gyre Termes and Latin Modern Mono, loaded by file name. The rupee sign comes from `tfrupee`. The last build finished with 0 errors, 0 undefined references and 0 overfull boxes; it reports only underfull-box warnings and harmless hyperref annotation notes.

To regenerate the two derived figures, run this from the repository root (matplotlib required):

```sh
python3 -B report/figures/make_figures.py
```

## Placeholders the student must fill

Placeholders appear as red bracketed italics (`\placeholder{...}` in the source). Search the source for `\placeholder`.

- **Title page:** department/branch name (twice), student name(s) and roll number(s), supervisor name and designation, optional DTU logo. The date is already set to November 2026.
- **Certificate:** student name(s), roll number(s), department, date, supervisor signature, name, designation and department.
- **Candidate's Declaration:** student name(s), roll number(s), branch, department, date, signature(s).
- **Acknowledgements:** supervisor, Head of Department and department, and any other thanks. Reviewers are deliberately not named because the adjudicator declined credit. Name a reviewer only if that reviewer has agreed in writing.
- **Appendix D:** an optional screenshot of the review forms. Take it from a copy of the packet filled with artificial answers, never from a real reviewer's file.
- **Declaration wording:** change "I/We" to the right form.

## Checks before submission

- Confirm DTU's required format (margins, title-page layout, whether a plagiarism certificate page is needed). The layout here is a generic B.Tech. layout: 3.5 cm left margin and 2.5 cm on the other sides.
- The report describes some items as planned or unconfirmed: the ARR May 2027 date, the training recipe (D015, not approved) and the second-annotator sample. Update these if their status changes.
- Numbers come from the files listed in the task brief. The only values computed for this report are the two regenerated figures and the Llama invalid-reason breakdown in Section 6.4, both read from `per_rendering.csv`. The test counts (161) are from re-running all seven suites on 26 October 2026.
