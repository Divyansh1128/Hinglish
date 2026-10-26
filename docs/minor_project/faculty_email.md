Subject: Major Project update: Hinglish maths reasoning in LLMs (results, and a request for co-authorship before 6 Nov)

Dear Prof. ____,

I am writing with an update on my Major Project, "Hinglish Mathematical Reasoning in Large Language Models", and to request your guidance and support on a paper submission.

**What we study.** We test whether the language of an otherwise identical maths word problem changes whether a small open AI model solves it. Each problem is written three ways: English (E), Romanized Hindi (R) and Hinglish code-mixed (C). The mathematics and the answer stay the same.

**What is done.**
- A reproducible evaluation pipeline (Google Colab T4, 4-bit models, frozen prompt and scorer, checksum-verified results, analysis plans pre-registered before each run).
- 370 newly written problem families, frozen with SHA-256 hashes. Answers are computed in code, every item is checked independently by two AI solvers, and the Hindi/Hinglish wording was reviewed by a bilingual reviewer.
- A second, original set of 24 families, solved independently by two human reviewers and finalised by an adjudicator.
- Evaluation of three models on both sets:

| Model | Set 1 (70 families) E / R / C | Set 2 (24 families) E / R / C |
|---|---|---|
| Qwen3-4B | 94.3 / 85.7 / 94.3 % | 100 / 91.7 / 100 % |
| Qwen3-8B | 98.6 / 91.4 / 98.6 % | 100 / 95.8 / 100 % |
| Llama-3.2-3B | 94.3 / 57.1 / 70.0 % | 87.5 / 62.5 / 91.7 % |

**Main findings.** In both sets and for every model, Romanized Hindi is the hardest form, while Hinglish scores at or near English. The gap is small for Qwen (about 4–9 points) and large for Llama (25–37 points). We also found that the answer-format instruction itself can distort scores, and we corrected this before the main runs. One hypothesis, that misreading Hindi maths words such as *bhaag* and *bhinn* drives the errors, was not supported, and we report that honestly. Earlier work (CodeMixTax) has reported a similar Romanized-Hindi gap, so we position the paper as a careful, reproducible audit on new human-reviewed problems rather than a first discovery.

**Requests.**
1. **Paper and co-authorship:** we have a 4-page short-paper draft in the official ACL format, titled "Romanized Hindi Is Harder Than Hinglish: A Scoring-Aware Audit of Small LLMs", for the **EACL 2027 Student Research Workshop**. The optional mentorship draft is due **6 November 2026** and submission is due **15 December 2026**. Would you be willing to review it and join as co-author and supervising author? The review system also requires one author who qualifies as a reviewer.
2. **A short meeting** to discuss the results and the plan for the next phase (a controlled fine-tuning comparison, December to March).
3. **The minor-project evaluation:** please let me know the exact date and format.

For transparency: AI assistants (Claude and GPT) helped with drafting problem items, coding and analysis, and this is fully disclosed in the paper. The data will be released under CC BY 4.0 and the code under MIT. I can share the draft PDF and the results whenever convenient.

Thank you for your time.

With regards,
____
____ (Roll No. ____)
