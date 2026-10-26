# Build: EACL 2027 SRW short paper (review version)

## Rebuild
From `paper/latex/`:

    tectonic main.tex

This writes `main.pdf`. Tectonic runs BibTeX itself and downloads any missing packages, including `tfrupee`, which provides the rupee sign. The build had no errors and no overfull boxes (last checked 2026-10-26, after the update below). The only remaining warnings are underfull boxes, mostly in the reference list.

## Files
- `main.tex`: the paper, built with `\usepackage[review]{acl}` (anonymous, with line numbers).
- `references.bib`: each entry has a comment naming the primary source it was checked against.
- `acl.sty`, `acl_natbib.bst`, `acl_latex.tex`: official ACL files, not modified. Their source and commit are in `TEMPLATE_SOURCE.txt`. `acl_latex.tex` is kept as a reference and is not built.
- `figures/accuracy_by_form.pdf`: a copy of `paper/figures/accuracy_by_form.pdf`. It is **no longer included** in `main.tex` (removed 2026-10-26 to fit four pages; it duplicated Table 2's Pilot-B numbers). Kept for a camera-ready or appendix version.
- `PATCH_original_cohort.md`: Astra's earlier proposal. **Superseded and not applied**: it predates D037 and wrongly describes two independent language reviewers.

## Page count
The PDF has 6 pages. The main text, Abstract through Section 7 Conclusion, ends on page 4 (the Conclusion closes the right column). Limitations, the Ethics Statement and the start of the References are on page 5, and the References end on page 6. The SRW short-paper limit is 4 content pages plus unlimited references. Under ARR rules, Limitations and Ethics do not count toward the limit.

Space is very tight: page 4 has no spare lines. Any text added to Sections 1 to 7 must be balanced by a cut. Resolving TODO markers frees a few lines.

## Changes on 2026-10-26 (original cohort, positioning)
- Title changed to "Romanized Hindi Is Harder Than Hinglish: A Scoring-Aware Audit of Small LLMs".
- Abstract and Introduction rewritten as building on prior evidence: CodeMixTax (Sth\=anika 2026) cited as direct prior evidence for R below Romanized Hinglish; Peter et al. 2026 (GEM) added on translation errors and answer extraction; Astra's positioning sentence (novelty memo, line 11) used in close paraphrase. Contributions are the new triplets, the scoring-aware frozen protocol, and two separately reviewed cohorts. "Equal observed aggregate accuracy" replaces C-as-easy-as-E wording. No "first", no "not code-mixing".
- §3: original-cohort review described per D037 (two independent human solvers; stage-1 answers agreed on 65/72 cohort renderings, R02 matched gold on 72/72, from `pilot_original/independent_expected.json`; language review by R02 plus A01; R01's 52 AI-prefilled stage-2 judgments excluded; earlier rounds discarded; A01 24/5/1). Disposition agreement is not reported, because R01's stage-2 dispositions are mostly AI-prefilled.
- §3 cuts: Phase-2 development details removed (900-rendering solver check, EDIT/MINE counts, FINAL_TEST/DEV keep/switch tags). The GPT over-formality observation (68/100 vs 13/70) is kept.
- §4: the strict/numeric agreement caveat added (agreement does not rule out failures both endpoints reject). The audit sentence now states only the AI pre-tag status.
- §6: original-cohort rows added to Tables 2 and 3 (exact values from `results/pilot_original/SUMMARY.md` and the per-model RESULTS.md files). Text added: the direction replicates for every model; Qwen is near ceiling; zero-width intervals are not evidence of equivalence; the cohort plan was written with Pilot-B known; never pooled. The PIL001-R isolated *kam* misreading was added. The incorrect claim that Llama's gaps "are not formatting artifacts" was removed.
- Figure 1 removed (it duplicated Table 2). Small cuts in §1 and §5 and a shorter Conclusion.
- Limitations and Ethics updated for the two cohorts and the excluded AI-prefilled judgments.
- references.bib: added `peter-etal-2026-mind`; replaced the `khullar-etal-2025-script` arXiv entry with `khullar-etal-2026-script` (EMNLP 2026 Industry, pp. 2414--2429).

## Open TODOs (red `\todo{}` markers; 12 in total)
1. §3: which model drafted the original 30.
2. §3: whether the test-set reviewer is the same person as the Pilot-B reviewer.
3. §3: GPT model version.
4. §3: the share of REVISE decisions that targeted R.
5. §4: quote the exact prompt text in an appendix. No appendix exists yet.
6. §5: confirm that the two fixture R renderings were judged correct by an AI assistant, not by independent bilingual validation.
7. §6: Pilot-B English-compliance/error audit. AI pre-tags exist (two models, κ = 0.94 category, 0.96 English, Qwen3-4B outputs); the human check (`results/pilot_b/audit/human_check_sheet.csv`) is pending. Report results only after it is done.
8. Ethics: signed consent and exposure records for every reviewer; their roles; any compensation.
9. Ethics: each reviewer's preference for credit (acknowledgment or authorship).
10. Ethics: which model drafted the original 30 (same as item 1).
11. Ethics: name the AI assistant systems as the venue policy requires.
12. Ethics: names/PII check before release.

Resolved on 2026-10-26: R01/R02/A01 status (two markers, now facts per D037); EDIT/MINE definition and the FINAL_TEST/DEV keep/switch recount (text removed); Pilot-B auditor assignment (replaced by item 7).

## References
Every reference was checked against a primary source: ACL Anthology .bib exports, the arXiv API, Crossref/DOI, the NeurIPS 2023 and ICLR 2025 proceedings listings, OpenReview, or the publisher's own page. All [VERIFY] items in the draft's reference list are resolved:
- Bali et al. 2014: the full title is "I am borrowing ya mixing?" An Analysis of English-Hindi Code Mixing in Facebook. The authors are Bali, Sharma, Choudhury and Vyas.
- XCOT: Chai, Yang, Sun, Guo, Liu, Wang, Liang, Bai, Li, Peng and Li, *AAAI* 39(22), pp. 23550–23558.
- Anand et al.: DOI 10.1609/aaai.v39i22.34509. The draft did not give one.
- MathOctopus: Chen et al. 2024, "Breaking Language Barriers in Multilingual Mathematical Reasoning: Insights and Observations", *Findings of EMNLP 2024*.
- GSM8K: Cobbe et al., "Training Verifiers to Solve Math Word Problems", arXiv:2110.14168.
- GSM8K-Hi: Kamath et al. 2025, "Benchmarking Hindi LLMs: A New Suite of Datasets and a Comparative Analysis", arXiv:2508.19831, preprint.
- Khullar et al. 2026, "Script Gap: Evaluating LLM Triage on Indian Languages in Native vs Romanized Scripts in a Real-World Setting", *Proceedings of EMNLP 2026: Industry Track*, pp. 2414–2429 (https://aclanthology.org/2026.emnlp-industry.144/; no DOI shown). It replaces the earlier arXiv:2512.10780 preprint entry.
- Peter et al. 2026, "Mind the Gap... or Not? How Translation Errors and Evaluation Details Skew Multilingual Results", *GEM 2026*, pp. 191–204, DOI 10.18653/v1/2026.gem-main.22. Verified by Astra (novelty refresh) and independently confirmed by the user.
- mCoT: "mCoT: Multilingual Instruction Tuning for Reasoning Consistency in Language Models", *ACL 2024*.
- GSM-Symbolic: "...Understanding the Limitations of Mathematical Reasoning in Large Language Models", *ICLR 2025*.
- SVAMP: "Are NLP Models really able to Solve Simple Math Word Problems?", *NAACL 2021*.
- Petrov et al.: "Language Model Tokenizers Introduce Unfairness Between Languages", *NeurIPS 2023*.
- Dakshina: "Processing South Asian Languages Written in the Latin Script: the Dakshina Dataset", *LREC 2020*.
- HAWP: Harshita Sharma, Pruthwik Mishra and Dipti Sharma, "HAWP: a Dataset for Hindi Arithmetic Word Problem Solving", *LREC 2022*.

No entry is marked UNVERIFIED. Points to note:
- **Sthānika report:** it is dated 9 Sep 2026 and names no individual author. The paper now calls it CodeMixTax, the name of its repository according to the 2026-10-26 novelty refresh. The "955 questions" and "five forms" details come from that refresh.
- **Sarvam-M:** only the blog's metadata (title, date) was checked. The page does mention a romanized GSM-8K benchmark. The paper no longer claims that accuracy falls for every listed model.
- **Model cards:** the draft's model-card references (pinned revisions in an appendix) are not cited, because there is no appendix yet.

## Anonymity
Checked 2026-10-26. The .tex, the .bib and the PDF text were searched for DTU, Delhi, Technological, divyansh, GitHub, "@", Astra and the user's name. There were no hits in the PDF apart from cited authors (HAWP's Harshita Sharma; Raj Jaiswal in Anand et al.). The .bib comments no longer name team agents. The PDF metadata has empty author and title fields. Item IDs (PIL001-R) and reviewer codes (R01, R02, A01) are pseudonymous.
