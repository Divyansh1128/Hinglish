# FMT2 format-compliance test — returned T4 run, 14 October 2026

**Development evidence only.** These are 36 outputs on 12 AI-authored, unreviewed, permanently excluded fixture families. They are not pilot data, not human-validated, and not a measure of Hinglish mathematical ability. With 12 prompts per form, every rate below is a rough indication.

Run: `secondary_analysis/Hinglish_FMT2_Format_Test_Colab.ipynb`, user-executed on a Colab Tesla T4, 17:34–17:41 UTC. Returned ZIP SHA-256 `c21741273a1f1c825bc141957a30439b95d567f456e9fc68da0f83e0a004e84f`. Both parts COMPLETE: 36/36 generated, 36 attempts, no infrastructure retries, no truncation, 0 checksum mismatches. Stack: Qwen3-4B with the pinned revision, transformers 4.51.3, bitsandbytes 0.50.2, torch 2.11.0+cu130. Model load took 114 s. Prompt `test1-english-final-v1`, unchanged. Per-rendering data: `per_rendering.csv`.

## Results

| Form | Strict v1.0.0 correct | numeric_literal_v1 match | Strict invalid (all `invalid_unit`) | Output contains Devanagari | Median output tokens |
|---|---:|---:|---:|---:|---:|
| E | 9/12 | 12/12 | 3 | 0/12 | 82 |
| R | 7/12 | 10/12 | 4 | 8/12 | 107 |
| C | 9/12 | 11/12 | 3 | 0/12 | 86 |

Every strict failure was `invalid_unit`. There were no missing, multiple or non-terminal FINAL lines, and no refusal hits.

## What actually broke

1. **The prompt causes unit words on dimensionless answers.** This affected 8 of 36 outputs, about equally across E/R/C. The instruction `FINAL: <number or fraction> <unit when applicable>` led the model to write `8 unitless`, `24 unit.`, `8 unit (no unit specified, so just the number)` and `7/27 positions.`. The earlier GPU smoke showed the same mechanism (`whole`, `fraction`, `part`). The pilot has 6 dimensionless families out of 30, so the frozen v1 prompt would likely fail many correct answers on them in every form. This is the main finding.
2. **Hindi unit words in R outputs.** In 1 case (`109 moti.`, FMT2-012-R) the model echoed the R question's noun, which was not in that fixture's aliases. This is the form-dependent mechanism predicted in Claude's review. It appeared only in R, but one case is too few to estimate a rate. Pilot gold for beads already lists `moti`; fixture metadata lacked it.
3. **English-output instruction largely ignored for R inputs.** 8 of 12 R outputs contain Devanagari script, and about 10 of 12 contain romanized-Hindi prose, despite "Give a short explanation in English". E: 0/12; C: about 2/12 romanized only (heuristic marker count, not a validated language tag). This does not affect either scoring endpoint, but it is substantial evidence that output-language following degrades on Romanized-Hindi input. It is worth reporting in its own right and makes the planned English-compliance tag essential.
4. **Two R-only value errors, both pointing to item quality.** FMT2-001-R answered 504: the R text "Har thaali ka kiraya 43 rupaye hai aur sambhalne ka shulk 29 rupaye hai" can be read as a per-plate fee, unlike E/C. This is a non-equivalent AI-authored rendering, not clearly a model error. FMT2-006-R answered the remaining positions (20) instead of the used fraction, which is a misread of "kitna bhinn istemaal hua hai". These two cases support the protocol's insistence on human E/R/C equivalence review.

## Risks predicted in Claude's review that did not occur here

There were no Markdown-bold FINAL markers, no `\boxed{}` or `$…$` on the FINAL line, no `x = v`, no `Rs.` prefix, and no incidental "I cannot" in 36 outputs. The model did use `$$…$$` LaTeX in explanations, but not on the FINAL line. These remain possible but appear uncommon under this prompt. The actual dominant failure is item 1, which the review did not predict.

## Recommendations (pre-pilot; the pilot itself is untouched)

- **Prompt v2 before the pilot**, as a new explicitly versioned protocol (allowed by the experiment spec). Tell the model to write nothing after a pure number, to use English unit words, and to explain in English even when the question is not in English. Then rerun FMT2 once with v2 to confirm. Disclose that v2 was revised after this development run. Do not iterate the prompt repeatedly on the fixtures.
- **Fixtures:** version FMT2 to repair FMT2-001-R's ambiguity and add `moti` to FMT2-012 aliases; do not reuse the repaired items as evidence of model ability.
- **Pilot data:** A01 should still check Hindi count/unit aliases (the `moti` mechanism is real). The English-compliance tag should be applied to every pilot output.
- Keep numeric_literal_v1 as the secondary endpoint. It behaved as specified: it matched every correct dimensionless answer, and it rejected the two wrong values and the misread.

## Prompt v2 confirmation run (decision D020)

Same notebook rebuilt with prompt `test1-english-final-v2` and fixtures FMT2-0.2.0. User-executed on Colab T4. Returned ZIP SHA-256 `28794810b54579a6b78f61b36b9354d02eb338cf481dede5869791e7c5cb36d6`. Both parts COMPLETE, 36/36, no retries, 0 checksum mismatches. Per-rendering data: `per_rendering_prompt_v2.csv`.

| Form | Strict v1.0.0 correct | numeric_literal_v1 match | Strict invalid | Output contains Devanagari |
|---|---:|---:|---:|---:|
| E | 12/12 | 12/12 | 0 | 0/12 |
| R | 10/12 | 10/12 | 0 | 0/12 |
| C | 12/12 | 12/12 | 0 | 0/12 |

- **Format failures went from 10/36 to 0/36.** Dimensionless answers are now bare (`FINAL: 8`), and units are English (`330 rupees`, `59 minutes`). Strict and secondary endpoints agree on all 36 outputs.
- **Explanations are now English.** Devanagari dropped from 8/12 to 0/12 R outputs; a heuristic marker found romanized-Hindi prose in 1/12 R outputs.
- **The repaired FMT2-001-R is now answered correctly** (330), consistent with the 0.1.0 error being item ambiguity.
- **Both remaining errors are R-only comprehension failures on Romanized-Hindi operation words. The renderings are correct.** FMT2-005-R: "bhaag dekar bhinn likho" (divide, write a fraction) was treated as a difference (answer 6). Under v1 this item was answered correctly with a Hindi explanation; with n=1 that is anecdote, not evidence that English reasoning hurts R. FMT2-006-R: "kitna bhinn istemaal hua" (what fraction was used) was answered as the remaining count (20) in both runs. *Bhinn* also means "different" in Hindi, a plausible source of the misreading.

Interpretation, development evidence only: v2 removes the format and output-language confounds without changing E or C correctness. The surviving errors are the kind of language-form effect the study is designed to measure. Mathematical-operation vocabulary in R (bhaag, bhinn, anupat) should be a deliberate, balanced feature of the pilot and later datasets, and the error taxonomy should record it (`misread_quantity` / `wrong_relation_operation`). Prompt iteration on these fixtures stops here, as committed in D020.
