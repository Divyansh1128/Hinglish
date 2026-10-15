# Minor evaluation — slide outline (DRAFT, about 12 slides, 10 minutes)

Build the final deck from this after the pilot. Keep every number traceable to a results file.

1. **Title**: Hinglish Mathematical Reasoning in LLMs: does the language form of a maths problem change the answer?
2. **Motivation**: the same marbles question in E, R and C; Indian users mix Hindi and English in Roman script.
3. **The confound**: vocabulary vs script vs mixing vs difficulty. Solution: matched families, three renderings, same maths.
4. **Research questions**: RQ1 now (unchanged model); RQ2 and RQ3 in the major phase (E+C vs E+R training).
5. **Related work and gap**: MGSM, Anand et al., CodeMixBench, Indi-RomCoM, CodeMixTax. Inference gaps are known; the controlled training comparison is the contribution.
6. **Dataset and human review**: 30 families × 3 forms; two blind bilingual reviewers plus an adjudicator; review status.
7. **Pipeline**: diagram of notebook → journal/resume → strict scorer + secondary endpoint → audited export. Reproducibility features.
8. **Pre-pilot finding 1**: the v1 vs v2 table. The original prompt failed 10/36 correct-looking answers; after the fix, 0/36.
9. **Pre-pilot finding 2**: R input made the model answer in Hindi/Devanagari (8/12 → 0/12 after the fix).
10. **Pre-pilot finding 3**: *bhaag* / *bhinn* misreadings, a concrete example of a language-form effect.
11. **Pilot results** [PENDING]: per-form accuracy with intervals, paired differences, error taxonomy.
12. **Limitations and plan to May**: 30 families is diagnostic; training feasibility, data scale-up, three-arm training.

Speaker note: label slides 8–10 as development evidence on excluded fixtures, not results.
