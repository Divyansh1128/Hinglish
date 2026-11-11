Prioritised fixes:

1. **Slide 13 — Correct the project’s current status.** Replace “The evaluation is complete, and the writing continues” with **“Phases 1–2 are complete; Phase 3 is underway.”** Use three sections: **Completed**, **In progress**, **Upcoming**. Put **“Phase 3: self-distilled explanation-rich targets”** under In progress and remove “optional.” Describe its purpose as testing whether richer solution targets reduce the Phase 2 degradation. Do not imply results already exist.

2. **Slide 10 — Remove the unsupported causal claim.** “Mainly by making it terse” is stronger than the displayed evidence. Accuracy and output length both declined; that alone does not establish why. Use **“All training arms lost accuracy and produced shorter answers.”** Label short targets as a proposed explanation, then connect that hypothesis to Phase 3.

3. **Slide 9 — State exactly what −4.33 measures.** The headline conflates adding Hinglish with the overall damage from fine-tuning. Write **“E+C scored 4.33 percentage points below E+R on Hinglish.”** Explain that this is the mean difference across three paired seeds. Keep the comparison against the unchanged model separate.

4. **Slides 8–9, 16 — Make the statistical uncertainty defensible.** An examiner will ask how the confidence interval handles repeated questions and three seeds. Add a readable description of the actual resampling unit and pairing method; put full details in backup. State that slide 6 shows individual accuracy intervals, whereas slide 16 shows intervals for paired differences. Do not infer significance from overlapping bar whiskers.

5. **Slide 7 — Withdraw the categorical exclusion of operation words.** The small, unequal strata and descriptive percentages do not establish that the gap “is not about” those words. Use **“This exploratory split does not clearly isolate an operation-word effect.”** Explain the strata with an actual example. Move this slide to backup unless it is central to the oral defence.

6. **Slides 2–3 — Define the language labels before using them.** Replace bare E/R/C labels on slide 2 with **English (E)**, **Romanized Hindi (R)** and **Hinglish/code-mixed (C)**. Explain that Romanized Hindi is Hindi written in Latin script. The chosen C example changes only the question sentence to English; identify it as an example, not a complete definition of all Hinglish.

7. **Slide 3 — Put the contribution on the slide.** CodeMixTax is buried in a microscopic footer, so the panel may think the language ranking itself is the novelty. Add one short statement: **“Prior work reports a similar language gap; we test it with controlled question families and compare training languages.”** Give the actual citation in readable form or notes.

8. **Slides 4, 6, 8–10 — Explain the different datasets and baselines.** Define one *family* as the same problem in three language forms. Show **70 pilot + 160 train + 40 dev + 100 test = 370 families**, with the separate 24-family cohort outside that total. Explicitly label slide 6 “70 pilot families” and slides 9–10 “100 Phase 2 test families.” Otherwise Qwen’s 94.3% versus 85% English baseline looks contradictory.

9. **Slide 8 — Make the training experiment understandable without the footer.** Move **Qwen3-4B** into the main content and explain QLoRA briefly as parameter-efficient fine-tuning. Show what is held constant: problem families, English targets, training settings and paired seeds. Clarify whether E+E duplicates each example and state the actual examples per arm. Equal update counts alone do not explain exposure or token differences.

10. **Slide 5 — Define the scoring rule and show the prompt intervention.** “Strict-invalid,” “fixture prompts” and “format failures” are unexplained. Include one real invalid response and the relevant v1/v2 instruction change. State whether a numerically correct answer in the wrong format counts as incorrect. Explain why Devanagari explanations matter under this rule.

11. **Slide 5 — Separate model screening from the main finding.** Two unrelated tables compete on a small slide. Keep the before/after prompt evidence in the main deck; move the seven-model screen to backup. Distinguish **format noncompliance** from **no outputs** rather than putting both under “Failed.” The current arrangement risks presenting an operational screen as a mathematical ability ranking.

12. **Slide 4 — Explain what validation actually established.** “Claude 900/900, GPT 897/900” needs a denominator and outcome label: 300 Phase 2 families × three forms, with what counted as success? Explain how the three disagreements were resolved. Replace “Frozen with SHA-256 hash” with **“Version locked after review”**, with hashing in notes. A hash demonstrates version integrity, not question validity.

13. **Slide 11 — Make the audit’s argument explicit.** State that the table covers **600 Hinglish responses across E+R and E+C: 100 questions × three seeds × two arms**. The useful result is **19 more real errors and six fewer format-only failures in E+C**. Define “real error” and “format only.” The current title “harm is substantive” sounds like a verdict without an immediately readable argument.

14. **Slide 11 — Replace vague assurance with the actual checks.** “Independent re-computation” should identify what was independent; the brief says a second agent recomputed results. Do not imply an external replication. Move interrupted-run recovery to a methods backup and state there that no answer was generated twice. Use the freed space to enlarge the audit table.

15. **Slides 6 and 14 — Bound the headline to the tested models.** Use **“Romanized Hindi had the lowest accuracy in all three tested models.”** On slide 6, replace “the same order” with **“Romanized Hindi was also lowest in the separate 24-family cohort”**: the full E/C ordering is not identical for Llama. On slide 14, restrict the training conclusion to Qwen3-4B and this recipe.

16. **All slides — Relax the template rules that are causing the template appearance.** The brief’s compulsory sentence titles and approximate 25-word limit produce oversized claims above underspecified evidence. Keep the restrained fonts and white background, but use short topic titles for methods and precise finding titles for results. Let examples, diagrams and charts occupy the space they need. Do not add decoration merely to make the deck look “human.”

17. **Slides 1, 3, 4, 8, 9, 10 — Fix headline wrapping deliberately.** Slide 1 strands “answer?”; slide 3 strands “languages”; slide 4 strands “review”; slide 10 strands “terse.” Slides 8–9 also have awkwardly short second lines. Shorten titles before reducing font size, then insert intentional line breaks. For example, slide 3 can simply be **“Research questions”** and slide 8 **“Phase 2: training comparison.”**

18. **All slides — Replace microscopic provenance with usable citations.** File paths, qualifiers and footer text are effectively unreadable in the sheets and will be weak on a projector. Move repository paths into notes. Keep only short, legible source labels on-slide. Promote essential information such as sample size, model name and interval type into the main visual. Check at actual projection scale before claiming a specific font-size violation.

19. **Slides 1 and 3 — Use the empty space to strengthen hierarchy.** Slide 1 compresses all identity information into the left portion; give the project title a clearer position and group authors, institution and supervisor into distinct blocks. Slide 3 spreads two questions across a large canvas while omitting the contribution. Align phase labels closely with their questions and add the contribution beneath them.

20. **Slide 2 — Make the linguistic comparison visually inspectable.** Use consistent line breaks across the three examples where possible, and bold or underline the changed question sentence. Replace “Gold: 405 rupees” with **“Correct answer: ₹405”** and show **₹1200 − 3 × ₹265 = ₹405**. This lets the panel understand the control immediately.

21. **Slides 4 and 8 — Give the diagrams enough visual weight.** Slide 4’s five identical narrow boxes force choppy three-line labels, while its arrows are barely visible. Widen or simplify the steps and place the dataset counts in one aligned block below. Slide 8’s faint branching connector adds little; use a large aligned table with **Training arm / Question languages / Solution language**.

22. **Slides 6 and 10 — Enlarge chart labels and standardise presentation.** Use full language names as panel headings on slide 10. Label the repeated bar groups clearly and use consistent decimal precision for averaged accuracies. Preserve common 0–100 scales. Brick currently means both Romanized Hindi and general emphasis throughout the deck; reserve language colours for language identity and use black bold text for unrelated conclusions.

23. **Slides 7 and 10 — Turn isolated wrong answers into evidence.** “435 instead of 405” lacks the model’s working; show the relevant actual response beside the correct calculation if available. On slide 10, the refund output and “Gold: 735” are separated across the slide, with no question context. Put a short prompt excerpt, actual output and correct answer together so the audience can inspect the error.

24. **Slides 12 and 14 — End with a specific scope and a readable conclusion.** Slide 12’s evenly spaced generic bullets feel boilerplate. Tie them to consequences: one backbone limits generalisation; one reviewer limits independent linguistic validation; no Devanagari arm leaves script effects unresolved. Slide 14 repeats its headline in a long paragraph and gives “Thank you” too much space. Keep two short findings, one Phase 3 sentence and a small “Questions?” line.

25. **Slides 13, 15 and 16 — Make status and backup slides functional.** Slide 13’s unequal table columns create empty cells that look unfinished; use separate aligned status lists and distinguish planned submission dates from completed work. Rename slide 15 **“Phase 2 accuracy by training arm and seed”** and decode `EE:11` into separate Arm and Seed columns. Rename slide 16 **“Pilot paired accuracy differences”**, define percentage points and contrast direction, and visibly separate the three model groups. Both backups need larger tables; the generic “Backup” heading wastes their best space.
tokens used
23,280
The deck looks orderly, but too mechanically composed: repeated sentence headlines, thin rules, small tables floating in large empty areas, and orange conclusions placed beneath them. A careful student’s deck would give more space to the actual experiment and use more cautious language around its conclusions.

I reviewed the contact sheets against :codex-file-citation{path="/Users/divyanshraj/Desktop/Major Project/docs/minor_project/deck/DECK_BRIEF.md" purpose="source"}. No files were edited. I see no obvious overlaps or clipping at contact-sheet resolution; the visible defects are mainly scale, wrapping, spacing and hierarchy.

Prioritised fixes:

1. **Slide 13 — Correct the project’s current status.** Replace “The evaluation is complete, and the writing continues” with **“Phases 1–2 are complete; Phase 3 is underway.”** Use three sections: **Completed**, **In progress**, **Upcoming**. Put **“Phase 3: self-distilled explanation-rich targets”** under In progress and remove “optional.” Describe its purpose as testing whether richer solution targets reduce the Phase 2 degradation. Do not imply results already exist.

2. **Slide 10 — Remove the unsupported causal claim.** “Mainly by making it terse” is stronger than the displayed evidence. Accuracy and output length both declined; that alone does not establish why. Use **“All training arms lost accuracy and produced shorter answers.”** Label short targets as a proposed explanation, then connect that hypothesis to Phase 3.

3. **Slide 9 — State exactly what −4.33 measures.** The headline conflates adding Hinglish with the overall damage from fine-tuning. Write **“E+C scored 4.33 percentage points below E+R on Hinglish.”** Explain that this is the mean difference across three paired seeds. Keep the comparison against the unchanged model separate.

4. **Slides 8–9, 16 — Make the statistical uncertainty defensible.** An examiner will ask how the confidence interval handles repeated questions and three seeds. Add a readable description of the actual resampling unit and pairing method; put full details in backup. State that slide 6 shows individual accuracy intervals, whereas slide 16 shows intervals for paired differences. Do not infer significance from overlapping bar whiskers.

5. **Slide 7 — Withdraw the categorical exclusion of operation words.** The small, unequal strata and descriptive percentages do not establish that the gap “is not about” those words. Use **“This exploratory split does not clearly isolate an operation-word effect.”** Explain the strata with an actual example. Move this slide to backup unless it is central to the oral defence.

6. **Slides 2–3 — Define the language labels before using them.** Replace bare E/R/C labels on slide 2 with **English (E)**, **Romanized Hindi (R)** and **Hinglish/code-mixed (C)**. Explain that Romanized Hindi is Hindi written in Latin script. The chosen C example changes only the question sentence to English; identify it as an example, not a complete definition of all Hinglish.

7. **Slide 3 — Put the contribution on the slide.** CodeMixTax is buried in a microscopic footer, so the panel may think the language ranking itself is the novelty. Add one short statement: **“Prior work reports a similar language gap; we test it with controlled question families and compare training languages.”** Give the actual citation in readable form or notes.

8. **Slides 4, 6, 8–10 — Explain the different datasets and baselines.** Define one *family* as the same problem in three language forms. Show **70 pilot + 160 train + 40 dev + 100 test = 370 families**, with the separate 24-family cohort outside that total. Explicitly label slide 6 “70 pilot families” and slides 9–10 “100 Phase 2 test families.” Otherwise Qwen’s 94.3% versus 85% English baseline looks contradictory.

9. **Slide 8 — Make the training experiment understandable without the footer.** Move **Qwen3-4B** into the main content and explain QLoRA briefly as parameter-efficient fine-tuning. Show what is held constant: problem families, English targets, training settings and paired seeds. Clarify whether E+E duplicates each example and state the actual examples per arm. Equal update counts alone do not explain exposure or token differences.

10. **Slide 5 — Define the scoring rule and show the prompt intervention.** “Strict-invalid,” “fixture prompts” and “format failures” are unexplained. Include one real invalid response and the relevant v1/v2 instruction change. State whether a numerically correct answer in the wrong format counts as incorrect. Explain why Devanagari explanations matter under this rule.

11. **Slide 5 — Separate model screening from the main finding.** Two unrelated tables compete on a small slide. Keep the before/after prompt evidence in the main deck; move the seven-model screen to backup. Distinguish **format noncompliance** from **no outputs** rather than putting both under “Failed.” The current arrangement risks presenting an operational screen as a mathematical ability ranking.

12. **Slide 4 — Explain what validation actually established.** “Claude 900/900, GPT 897/900” needs a denominator and outcome label: 300 Phase 2 families × three forms, with what counted as success? Explain how the three disagreements were resolved. Replace “Frozen with SHA-256 hash” with **“Version locked after review”**, with hashing in notes. A hash demonstrates version integrity, not question validity.

13. **Slide 11 — Make the audit’s argument explicit.** State that the table covers **600 Hinglish responses across E+R and E+C: 100 questions × three seeds × two arms**. The useful result is **19 more real errors and six fewer format-only failures in E+C**. Define “real error” and “format only.” The current title “harm is substantive” sounds like a verdict without an immediately readable argument.

14. **Slide 11 — Replace vague assurance with the actual checks.** “Independent re-computation” should identify what was independent; the brief says a second agent recomputed results. Do not imply an external replication. Move interrupted-run recovery to a methods backup and state there that no answer was generated twice. Use the freed space to enlarge the audit table.

15. **Slides 6 and 14 — Bound the headline to the tested models.** Use **“Romanized Hindi had the lowest accuracy in all three tested models.”** On slide 6, replace “the same order” with **“Romanized Hindi was also lowest in the separate 24-family cohort”**: the full E/C ordering is not identical for Llama. On slide 14, restrict the training conclusion to Qwen3-4B and this recipe.

16. **All slides — Relax the template rules that are causing the template appearance.** The brief’s compulsory sentence titles and approximate 25-word limit produce oversized claims above underspecified evidence. Keep the restrained fonts and white background, but use short topic titles for methods and precise finding titles for results. Let examples, diagrams and charts occupy the space they need. Do not add decoration merely to make the deck look “human.”

17. **Slides 1, 3, 4, 8, 9, 10 — Fix headline wrapping deliberately.** Slide 1 strands “answer?”; slide 3 strands “languages”; slide 4 strands “review”; slide 10 strands “terse.” Slides 8–9 also have awkwardly short second lines. Shorten titles before reducing font size, then insert intentional line breaks. For example, slide 3 can simply be **“Research questions”** and slide 8 **“Phase 2: training comparison.”**

18. **All slides — Replace microscopic provenance with usable citations.** File paths, qualifiers and footer text are effectively unreadable in the sheets and will be weak on a projector. Move repository paths into notes. Keep only short, legible source labels on-slide. Promote essential information such as sample size, model name and interval type into the main visual. Check at actual projection scale before claiming a specific font-size violation.

19. **Slides 1 and 3 — Use the empty space to strengthen hierarchy.** Slide 1 compresses all identity information into the left portion; give the project title a clearer position and group authors, institution and supervisor into distinct blocks. Slide 3 spreads two questions across a large canvas while omitting the contribution. Align phase labels closely with their questions and add the contribution beneath them.

20. **Slide 2 — Make the linguistic comparison visually inspectable.** Use consistent line breaks across the three examples where possible, and bold or underline the changed question sentence. Replace “Gold: 405 rupees” with **“Correct answer: ₹405”** and show **₹1200 − 3 × ₹265 = ₹405**. This lets the panel understand the control immediately.

21. **Slides 4 and 8 — Give the diagrams enough visual weight.** Slide 4’s five identical narrow boxes force choppy three-line labels, while its arrows are barely visible. Widen or simplify the steps and place the dataset counts in one aligned block below. Slide 8’s faint branching connector adds little; use a large aligned table with **Training arm / Question languages / Solution language**.

22. **Slides 6 and 10 — Enlarge chart labels and standardise presentation.** Use full language names as panel headings on slide 10. Label the repeated bar groups clearly and use consistent decimal precision for averaged accuracies. Preserve common 0–100 scales. Brick currently means both Romanized Hindi and general emphasis throughout the deck; reserve language colours for language identity and use black bold text for unrelated conclusions.

23. **Slides 7 and 10 — Turn isolated wrong answers into evidence.** “435 instead of 405” lacks the model’s working; show the relevant actual response beside the correct calculation if available. On slide 10, the refund output and “Gold: 735” are separated across the slide, with no question context. Put a short prompt excerpt, actual output and correct answer together so the audience can inspect the error.

24. **Slides 12 and 14 — End with a specific scope and a readable conclusion.** Slide 12’s evenly spaced generic bullets feel boilerplate. Tie them to consequences: one backbone limits generalisation; one reviewer limits independent linguistic validation; no Devanagari arm leaves script effects unresolved. Slide 14 repeats its headline in a long paragraph and gives “Thank you” too much space. Keep two short findings, one Phase 3 sentence and a small “Questions?” line.

25. **Slides 13, 15 and 16 — Make status and backup slides functional.** Slide 13’s unequal table columns create empty cells that look unfinished; use separate aligned status lists and distinguish planned submission dates from completed work. Rename slide 15 **“Phase 2 accuracy by training arm and seed”** and decode `EE:11` into separate Arm and Seed columns. Rename slide 16 **“Pilot paired accuracy differences”**, define percentage points and contrast direction, and visibly separate the three model groups. Both backups need larger tables; the generic “Backup” heading wastes their best space.
