# Submission form text (copy and paste)

**Title:** Romanized Hindi Is Harder Than Hinglish: A Scoring-Aware Audit of Small LLMs

**Abstract (plain text):**
Prior work reports lower LLM accuracy on Romanized Hindi than on Romanized Hinglish versions of the same translated GSM8K questions, and shows that translation errors and answer extraction can skew multilingual math gaps. Building on this evidence, we audit small open LLMs on newly drafted, human-reviewed math triplets in English (E), Romanized Hindi (R) and Roman-script Hinglish (C), with code-computed gold and a frozen, scoring-aware protocol. On permanently excluded fixtures, a plausible answer-format instruction made 10/36 Qwen3-4B outputs fail strict scoring and pushed 8/12 R explanations into Devanagari; after one disclosed prompt revision both were zero, and format compliance across seven models was strongly model-specific. In two separately reviewed, pre-registered cohorts, never pooled, R is the lowest-scoring form for all three backbones. On the primary 70-family cohort, Qwen3-4B scores 94.3/85.7/94.3% on E/R/C, Qwen3-8B 98.6/91.4/98.6% and Llama-3.2-3B 94.3/57.1/70.0%; a 24-family cohort shows the same direction, with Qwen near ceiling. Both Qwen models have equal observed aggregate accuracy on E and C. R errors are not concentrated in items with Hindi operation words.

**Keywords:** code-mixing; Romanized Hindi; Hinglish; mathematical reasoning; multilingual evaluation; answer extraction; benchmark construction; small language models

**Paper type:** Short paper (4 pages + references, limitations, ethics, appendix)

**TL;DR:** On newly written, human-reviewed English/Romanized-Hindi/Hinglish maths triplets, small open LLMs are least accurate on Romanized Hindi, while Hinglish matches English for Qwen; answer-format checks on excluded data are needed before such comparisons.

**Authors:** enter every author, with affiliation and email, in the submission system only, never in the PDF.
