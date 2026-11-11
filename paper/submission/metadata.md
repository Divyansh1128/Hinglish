# Submission form text — updated 11 November 2026

AUTHOR-ONLY: do not upload this file as anonymous supplementary material.

**Title:** Romanized Hindi Is Harder Than Hinglish: A Scoring-Aware Audit of Small LLMs

**Abstract:**
Prior work reports lower LLM accuracy on Romanized Hindi than on Romanized Hinglish versions of the same translated GSM8K questions, and shows that translation errors and answer extraction can skew multilingual math gaps. Building on this evidence, we audit small open LLMs on newly drafted, human-reviewed math triplets in English (E), Romanized Hindi (R) and Roman-script Hinglish (C), with code-computed gold and a frozen, scoring-aware protocol. On permanently excluded fixtures, a plausible answer-format instruction made 10/36 Qwen3-4B outputs fail strict scoring and pushed 8/12 R explanations into Devanagari; after one disclosed prompt revision both were zero, and format compliance across seven models was strongly model-specific. In two separately reviewed, pre-registered cohorts, never pooled, R is the lowest-scoring form for all three backbones. On the primary 70-family cohort, Qwen3-4B scores 94.3/85.7/94.3% on E/R/C, Qwen3-8B 98.6/91.4/98.6% and Llama-3.2-3B 94.3/57.1/70.0%; a 24-family cohort shows the same direction, with Qwen near ceiling. Both Qwen models have equal observed aggregate accuracy on E and C. R errors are not concentrated in items with Hindi operation words. In a pre-registered fine-tuning follow-up on 100 held-out families (Qwen3-4B QLoRA, three seeds), training on Hinglish rather than Romanized Hindi lowered Hinglish accuracy by 4.3 points [−8.0, −0.7], and every fine-tuned variant fell far below the unchanged model.

**TL;DR:** A scoring-aware audit finds Romanized Hindi weakest in two small-model math cohorts; a controlled three-seed follow-up finds Hinglish training worse than Romanized-Hindi training on Hinglish under the tested recipe.

**Keywords:** Romanized Hindi; Hinglish; code-mixing; mathematical reasoning; multilingual evaluation; answer extraction; negative results; controlled fine-tuning

**Track:** EACL 2027 Student Research Workshop, research paper, short paper, direct submission.

**Publication preference:** archival (user answered yes to the publication/approval question on 11 November; reconfirm the selected form option at upload).

**Author order, explicitly confirmed by the user on 11 November:**
1. Divyansh Raj
2. Ayush Kumar Singh
3. Divyanshu Mishra
4. Dr. Dinesh Udar (use the profile's name without honorific if the form requires it)

Affiliation from the project report: Department of Applied Mathematics, Delhi Technological University. Enter verified OpenReview profiles/emails directly in the form; do not invent contact details. The user answered yes to author approval; each co-author should review the final assembled version and its claims before actual submission.

**Prior mentorship:** project records say OpenReview #12, submitted 26 October. This requires a new final-track submission. No new submission has been made by this packaging task.

**Human review facts supplied today:** reviewers were teammates; all gave consent. Payment and institutional ethics determination were not specified by those replies. Do not infer either from consent.
