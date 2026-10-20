# Build: EACL 2027 SRW short paper (review version)

## Rebuild
From the project root:

    tectonic paper/latex/main.tex

This writes `paper/latex/main.pdf`. Tectonic runs BibTeX itself and downloads any missing packages, including `tfrupee`, which provides the rupee sign. The build had no errors and no overfull boxes (checked 2026-10-20). The only remaining warnings are underfull boxes, mostly in the reference list.

## Files
- `main.tex`: the paper, built with `\usepackage[review]{acl}` (anonymous, with line numbers).
- `references.bib`: each entry has a comment naming the primary source it was checked against.
- `acl.sty`, `acl_natbib.bst`, `acl_latex.tex`: official ACL files, not modified. Their source and commit are in `TEMPLATE_SOURCE.txt`. `acl_latex.tex` is kept as a reference and is not built.
- `figures/accuracy_by_form.pdf`: a copy of `paper/figures/accuracy_by_form.pdf`. If you regenerate the figure, copy it here again.

## Page count
The PDF has 6 pages. The main text, Abstract through Section 7 Conclusion, ends on page 4. Limitations, the Ethics Statement and the start of the References are on page 5, and the References end on page 6. The SRW short-paper limit is 4 content pages plus unlimited references. Under ARR rules, Limitations and Ethics do not count toward the limit.

Space is tight: page 4 is full. Any text added to Sections 1 to 7 must be balanced by a cut. Resolving the TODO markers removes their text and frees a few lines.

## Open TODOs (red `\todo{}` markers; 16 in total)
1. §3: GPT model version, and which model drafted the original 30.
2. §3: completion status of the R01/R02 review and the A01 adjudication.
3. §3: whether the FINAL_TEST reviewer is the same person as the Pilot-B reviewer.
4. §3: the share of REVISE decisions that targeted R.
5. §3: definition of EDIT/MINE (53 OK, 30 EDIT, 5 MINE).
6. §3: the keep/switch counts for FINAL_TEST and DEV are first-version tags. Recount on the accepted text with the frozen matcher.
7. §4: quote the exact prompt text in an appendix. No appendix exists yet.
8. §4: who audited and who spot-checked for Pilot-B.
9. §5: confirm that the two fixture R renderings were judged correct by an AI assistant, not by independent bilingual validation.
10. §6: R01/R02/A01 status for the original 30-family pilot.
11. §6: English-compliance audit results (the planned Table 5) from the verified audit sidecar.
12. Ethics: signed consent and exposure records for every reviewer; their roles; any compensation.
13. Ethics: each reviewer's preference for credit (acknowledgment or authorship).
14. Ethics: which model drafted the original 30 (same question as item 1).
15. Ethics: name the AI assistant systems as the venue policy requires.
16. Ethics: names/PII check before release.

## References
Every reference was checked against a primary source: ACL Anthology .bib exports, the arXiv API, Crossref/DOI, the NeurIPS 2023 and ICLR 2025 proceedings listings, OpenReview, or the publisher's own page. All [VERIFY] items in the draft's reference list are resolved:
- Bali et al. 2014: the full title is "I am borrowing ya mixing?" An Analysis of English-Hindi Code Mixing in Facebook. The authors are Bali, Sharma, Choudhury and Vyas.
- XCOT: Chai, Yang, Sun, Guo, Liu, Wang, Liang, Bai, Li, Peng and Li, *AAAI* 39(22), pp. 23550–23558.
- Anand et al.: DOI 10.1609/aaai.v39i22.34509. The draft did not give one.
- MathOctopus: Chen et al. 2024, "Breaking Language Barriers in Multilingual Mathematical Reasoning: Insights and Observations", *Findings of EMNLP 2024*.
- GSM8K: Cobbe et al., "Training Verifiers to Solve Math Word Problems", arXiv:2110.14168.
- GSM8K-Hi: Kamath et al. 2025, "Benchmarking Hindi LLMs: A New Suite of Datasets and a Comparative Analysis", arXiv:2508.19831, preprint.
- Khullar et al. 2025, "Script Gap: Evaluating LLM Triage on Indian Languages in Native vs Romanized Scripts in a Real World Setting", arXiv:2512.10780, preprint.
- mCoT: "mCoT: Multilingual Instruction Tuning for Reasoning Consistency in Language Models", *ACL 2024*.
- GSM-Symbolic: "...Understanding the Limitations of Mathematical Reasoning in Large Language Models", *ICLR 2025*.
- SVAMP: "Are NLP Models really able to Solve Simple Math Word Problems?", *NAACL 2021*.
- Petrov et al.: "Language Model Tokenizers Introduce Unfairness Between Languages", *NeurIPS 2023*.
- Dakshina: "Processing South Asian Languages Written in the Latin Script: the Dakshina Dataset", *LREC 2020*.
- HAWP: Harshita Sharma, Pruthwik Mishra and Dipti Sharma, "HAWP: a Dataset for Hindi Arithmetic Word Problem Solving", *LREC 2022*.

No entry is marked UNVERIFIED. Points to note:
- **Sthānika report:** it is dated 9 Sep 2026 and names no individual author. The name "CodeMixTax" does not appear on the page, so the paper calls it "an author report".
- **Sarvam-M:** only the blog's metadata (title, date) was checked. The page does mention a romanized GSM-8K benchmark. The claim that accuracy falls for every listed model was not re-checked against its table.
- **Model cards:** the draft's model-card references (pinned revisions in an appendix) are not cited, because there is no appendix yet.

## Anonymity
The .tex, the .bib and the PDF text were searched for DTU, Delhi Technological, divyansh, github.com/Divyansh, email addresses and the user's name. There were no hits. The only hit for "Harshit" is the cited HAWP author Harshita Sharma. The PDF metadata has empty author and title fields.
