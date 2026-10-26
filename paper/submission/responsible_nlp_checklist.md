# Responsible NLP checklist: draft answers

Copy these into the submission form. Section numbers refer to the PDF. Items marked **CONFIRM** need a fact only you have; answer them truthfully, since wrong answers can lead to desk rejection.

**A. For every submission**
- A1 Limitations discussed? **Yes**: the Limitations section (after the Conclusion).
- A2 Potential risks discussed? **Yes**: the Ethics Statement (misreading results as general claims about Hindi speakers; the small samples; the AI-drafted items).
- A3 Do the abstract and introduction summarise the claims? **Yes**: Abstract and §1.

**B. Scientific artifacts used or created**
- B1 Cite the creators of the artifacts used? **Yes**: §2 and §4 (Qwen3, Llama 3.2 and the related benchmarks are cited).
- B2 Licence or terms discussed? **Yes**: Ethics Statement. Data CC BY 4.0, code MIT; models used under their licences (Llama 3.2 Community Licence, accepted via Hugging Face).
- B3 Use consistent with intended use? **Yes**: models used for research evaluation only.
- B4 Steps to check for personal information or offensive content? **Yes**: Ethics Statement (invented first names; automated scan for contact details).
- B5 Documentation of artifacts (languages, domains)? **Yes**: §3 (English, Romanized Hindi, Hinglish; six school maths topics).
- B6 Statistics of the data (splits, sizes)? **Yes**: §3 and §6 (Pilot-B 70 families / 210 prompts; original cohort 24 / 72).

**C. Computational experiments**
- C1 Number of parameters, total compute, infrastructure? **Yes**: §4 (Qwen3-4B, Qwen3-8B and Llama-3.2-3B in 4-bit NF4 on one Colab T4; inference only, about 25–35 minutes per 210-prompt run).
- C2 Experimental set-up and hyperparameters? **Yes**: §4 and Appendix A (greedy, non-thinking, 1,024-token cap, frozen prompt).
- C3 Descriptive statistics (variance, intervals; single runs)? **Yes**: §6 (Wilson 95% intervals, 10,000-resample family bootstrap; each backbone run once per cohort under greedy decoding).
- C4 Packages used (versions)? **Yes**: §4 and the supplement (transformers 4.51.3, bitsandbytes 0.50.2, torch 2.11.0+cu130, scorer v1.0.0).

**D. Human annotators**
- D1 Full instruction text given to annotators? **Yes**: in the supplement (review form README and audit instructions).
- D2 Recruitment and payment? **CONFIRM**: reviewers were team members or acquaintances; state whether anyone was paid. If unpaid, say "volunteers, unpaid".
- D3 Consent and data use explained? **Yes**: all reviewers consented to release under CC BY 4.0 (Ethics Statement).
- D4 Approved by an ethics review board? **CONFIRM**: probably "No; the review involved no personal data and only rating maths word problems". Ask your faculty whether DTU requires an IRB for this.
- D5 Annotator demographics reported? **CONFIRM**: probably "Partially: bilingual Hindi–English speakers; no further demographics collected."

**E. AI assistants**
- E1 Did you use AI assistants (writing, coding)? **Yes**, disclosed in the Ethics Statement: Claude Opus 5.5 (Anthropic) and GPT-6 Astra and GPT-6.1 Sol (OpenAI, via Codex) for coding, analysis, drafting problem items and translations, AI pre-tagging, and writing assistance. The authors reviewed all outputs.
