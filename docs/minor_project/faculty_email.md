# Email to the faculty coordinator (draft — edit names and send yourself)

**Subject:** Major Project update — Hinglish math reasoning in LLMs: first results, and three requests

Dear Prof. ____,

I am writing with an update on my Major Project, "Hinglish Mathematical Reasoning in Large Language Models", and to ask for your guidance on three points.

**What we studied.** We test whether the language of an otherwise identical math word problem changes whether a language model solves it. Each problem is written three ways: English (E), Romanized Hindi (R) and Hinglish code-mixed (C). The mathematics and the expected answer stay the same.

**What is done.**
- A reproducible evaluation pipeline (Colab T4, 4-bit models, frozen prompt and scorer, checksummed results).
- A dataset of 370 newly written problem families. Answers are computed in code, every item is checked independently by two AI solvers, and the Hindi/Hinglish wording was reviewed by a bilingual reviewer.
- A first pre-registered evaluation on 70 reviewed families with three models:

| Model | English | Romanized Hindi | Hinglish |
|---|---|---|---|
| Qwen3-4B | 94.3% | 85.7% | 94.3% |
| Qwen3-8B | 98.6% | 91.4% | 98.6% |
| Llama-3.2-3B | 94.3% | 57.1% | 70.0% |

**Main findings so far.** Romanized Hindi is consistently the hardest form, with a gap of about 8 points for Qwen and 37 for Llama. Hinglish is as easy as English for Qwen. One of our hypotheses, that misreading Hindi math words such as *bhaag* and *bhinn* drives the errors, was not supported, and we report that honestly. We also found that the answer-format instruction itself can distort scores, and fixed this before the main run.

**Requests.**
1. **Co-authorship and paper:** we plan a 4-page short paper for the **EACL 2027 Student Research Workshop**. The optional mentorship draft is due **6 November 2026** and submission is **15 December 2026**. Would you be willing to be a co-author and supervising author? The review system (ARR) also needs one author who qualifies as a reviewer, which we expect a faculty co-author to satisfy.
2. **Feedback on scope:** could we have a short meeting to discuss the results and the plan for the major phase (fine-tuning comparison, December–March)?
3. **Minor-project evaluation:** please let me know the exact date and format of the November evaluation.

For transparency, AI assistants (Claude and GPT) helped with drafting problem items, coding and analysis. All of this is disclosed in the paper, and human review covers the data. The data will be released under CC BY 4.0 and the code under MIT. The report draft and results tables are ready whenever you would like to see them.

Thank you for your time.

Regards,
____ (Roll no. ____)
