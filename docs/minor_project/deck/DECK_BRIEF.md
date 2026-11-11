# Minor-evaluation deck v2 — brief

Audience: DTU faculty panel (Applied Mathematics), about 12 minutes plus questions. Presenters: Divyansh Raj (23/MC/195), Ayush Kumar Singh (23/MC/194), Divyanshu Mishra (23/MC/196). Supervisor: Dr. Dinesh Udar, Assistant Professor, Department of Applied Mathematics, DTU. Replaces `../minor_evaluation_presentation.pptx` (26 Oct, pre-Phase-2).

## Design: it must not look AI-generated

Aim for a careful student research talk, the way a good lab group's slides look.

- **Do**
  - Use a white background and a thin rule under the title.
  - Write every title as a full sentence that states the finding, e.g. "Romanized Hindi is the hardest form for every model".
  - Keep slides mostly empty. Put the detail in speaker notes.
  - Use real artefacts from the project: actual question text, actual model output, actual numbers.
  - Use one consistent colour per form, everywhere:
    - E: slate `3B4A5A`
    - R: brick `B5532F`
    - C: teal `2E7D74`
  - Use grey `8A8F96` for secondary text.
  - Use one accent, R's brick, for the key number on a slide.
- **Charts:**
  - Draw them yourself with shapes (bars plus thin CI whiskers, a dot plot for seeds) or use native pptxgenjs charts.
  - Label axes and values directly. Use no legends where direct labels work.
- **Fonts:** Georgia for titles and Calibri for body. Both are installed on any college PC. Body text at least 16 pt, titles 26–30 pt.
- **Footer:** slide number at the bottom right, and "DTU · Applied Mathematics · Minor project evaluation" in small grey at the bottom left. Leave the footer off the title slide.
- **Don't** use any of these:
  - emoji or icons
  - gradients
  - rounded "pill" badges or evidence-tag boxes
  - grids of three coloured cards
  - "Key takeaways" or "Key insights" boxes
  - bullet points that each start with a bolded phrase and a colon
  - stock phrases ("delve", "leverage", "robust", "seamless", "unlock", "landscape", "journey")
  - more than about 25 words of on-slide text, except where a slide shows quoted question or output text
  - drop shadows
- Keep bullets plain: at most 4 per slide, sentence case. Use real minus signs (−).

## Slides (numbers are verified; copy exactly)

1. **Title.** "Does the language of a maths problem change the answer? Hinglish, Romanized Hindi and small LLMs". Below it: the three names with roll numbers; B.Tech. Mathematics and Computing, Department of Applied Mathematics, Delhi Technological University; Supervisor: Dr. Dinesh Udar; "Minor project evaluation, November 2026".
2. **One problem, three forms.** Show the three PB017 renderings verbatim, each labelled in its colour:
   - E: "Imran had ₹1200. He bought 3 shirts at ₹265 each. How much money did he have left?"
   - R: "Imran ke paas ₹1200 the. Usne ₹265 waali 3 kameezein khareedin. Uske paas kitne rupaye bache?"
   - C: "Imran ke paas ₹1200 the. Usne ₹265 waali 3 kameezein khareedin. How much money did he have left?"

   Gold: 405 rupees. Line: "Only the language changes. The maths, numbers and answer are identical."
3. **Two questions.**
   - Phase 1: do unchanged models answer the three forms equally well?
   - Phase 2: does training on Hinglish (E+C) help on Hinglish more than training on Romanized Hindi (E+R)?

   Note that prior work (CodeMixTax) already reports R below Hinglish on translated GSM8K. Our contribution is a controlled, scoring-aware replication and the training comparison.
4. **How the data was built.** Draw it as a left-to-right flow of plain boxes with thin arrows:

   AI-drafted family → gold answer computed in code → solved blind by two different LLMs (Claude, GPT) → bilingual human review → frozen with SHA-256 hash.

   Counts: 370 frozen families (Pilot-B 70; Phase 2: 160 train, 40 dev, 100 test), plus a 24-family original cohort. Phase-2 blind solving: Claude 900/900, GPT 897/900.
5. **The answer format can fake a language gap.** This is development evidence on 36 excluded fixture prompts (Qwen3-4B). Show it as a two-column before/after table:

   | | Prompt v1 | Prompt v2 |
   |---|---|---|
   | Format failures | 10/36 | 0/36 |
   | R explanations in Devanagari | 8/12 | 0/12 |

   Then a second mini table, the 7-model screen. Rule: ≤ 3/36 strict-invalid. Passed: Qwen3-4B (0), Qwen3-8B (0), Llama-3.2-3B (2). Failed: Qwen3-1.7B (36), Phi-4-mini (14), Granite-3.3-2B (36), Gemma-3-4B (no outputs).
6. **Romanized Hindi is the hardest form for every model** (Pilot-B, 70 families). Grouped bars by model, E/R/C, with Wilson 95% whiskers:
   - Qwen3-4B 94.3 [86.2, 97.8] / 85.7 [75.7, 92.1] / 94.3 [86.2, 97.8]
   - Qwen3-8B 98.6 [92.3, 99.7] / 91.4 [82.5, 96.0] / 98.6 [92.3, 99.7]
   - Llama-3.2-3B 94.3 [86.2, 97.8] / 57.1 [45.5, 68.1] / 70.0 [58.5, 79.5]

   Note under the chart: "The separate 24-family original cohort shows the same order."
   - Qwen3-4B 100 / 91.7 / 100
   - Qwen3-8B 100 / 95.8 / 100
   - Llama 87.5 / 62.5 / 91.7
7. **The gap is not about Hindi operation words.** R accuracy by stratum (C keeps R's Hindi operation word: 18 families / C switches it: 17 / no operation word: 35):
   - Qwen3-4B 89 / 82 / 86%
   - Qwen3-8B 94 / 94 / 89%
   - Llama 67 / 59 / 51%

   Errors are spread evenly, so the development hypothesis (bhaag, bhinn) is not supported. Real example: Llama on PB017 R answered 435 instead of 405, a plain arithmetic slip.
8. **Phase 2 design: a controlled training comparison.** A diagram of three arms, all fine-tuning Qwen3-4B (QLoRA, free Colab T4) on the same 160 problems with identical English solutions. Only the question language differs:
   - E+E: English question twice
   - E+R: English + Romanized Hindi
   - E+C: English + Hinglish

   3 paired seeds; 60 updates each. Pre-registered with 3 amendments before any output. One evaluation on 100 untouched test families. Primary measure: Δ_C = (E+C) − (E+R) accuracy on Hinglish questions.
9. **Hinglish training did not help on Hinglish questions; it hurt.** Big number in the accent colour:

   Δ_C = −4.33 points, 95% CI [−8.00, −0.67] → pre-registered label: Harm.

   A small dot plot of the per-seed values: −3, −1, −9, all below zero, with a zero line. Arm accuracy on C:
   - unchanged 66
   - E+E 43.0
   - E+R 47.0
   - E+C 42.7
10. **Training made every arm worse, mainly by making it terse.** A chart of accuracy on E/R/C:
    - unchanged 85 / 63 / 66
    - E+E 61.3 / 40.3 / 43.0
    - E+R 59.3 / 38.0 / 47.0
    - E+C 58.7 / 41.3 / 42.7

    Median output length 113 → 42 tokens. Real trained output shown in monospace: "Refund = 120 + 45 = 165 rupees. FINAL: 165 rupees" (gold 735). Our training targets were short English solutions; the model copied that style and lost its step-by-step reasoning.
11. **We checked the result three ways.**
    1. An independent re-computation from the raw predictions by a second agent matches exactly.
    2. A human-checked audit of all 331 E+R/E+C failures on C. E+C has 132 real errors vs 113 for E+R, and fewer format-only failures (40 vs 46), so the harm is not a scoring artefact.
    3. Two interrupted evaluation runs were recovered under a pre-registered rule and are disclosed; no answer was generated twice.
12. **Limitations.** One backbone and one recipe in Phase 2. 100 test families. A single bilingual reviewer for most sets. AI-drafted items. No Devanagari arm. Results hold for this recipe, not for Hinglish training in general.
13. **Where the project stands.** A simple two-column done / remaining table, or a horizontal timeline.
    - Done (Oct–Nov 2026):
      - data (370 + 24 families)
      - pipeline (161 tests)
      - Phase 1 on 3 models
      - Phase-2 training (9/9 runs valid first time)
      - test evaluation and analysis
      - full human audit
      - EACL SRW paper draft (mentorship submission 26 Oct)
    - Remaining:
      - mentor feedback 5 Dec, final SRW submission 15 Dec
      - optional follow-up with explanation-rich training targets
      - thesis and training paper (ARR, May 2027)
      - final evaluation May 2027
14. **Thank you / questions.** Repeat the one-sentence headline: "Small models struggle most with Romanized Hindi, and adding Hinglish to a short-target fine-tune did not fix it; it made Hinglish answers worse."

Backup slides after 14, titled "Backup":

- B1, the full Phase-2 accuracy table with seeds:
  - EE:11 62/41/44
  - EE:22 63/41/41
  - EE:33 59/39/44
  - ER:11 61/42/44
  - ER:22 56/35/47
  - ER:33 61/37/50
  - EC:11 64/43/41
  - EC:22 58/41/46
  - EC:33 54/40/41
  - unchanged 85/63/66
- B2, Pilot-B paired differences (pp, 95% bootstrap):
  - Qwen3-4B: E−R +8.6 [−1.4, +18.6]; E−C 0.0 [−7.1, +7.1]; R−C −8.6 [−15.7, −1.4]
  - Qwen3-8B: E−R +7.1 [0.0, +14.3]; E−C 0.0 [−4.3, +4.3]; R−C −7.1 [−14.3, 0.0]
  - Llama: E−R +37.1 [+24.3, +50.0]; E−C +24.3 [+11.4, +37.1]; R−C −12.9 [−27.1, +1.4]

## Speaker notes

Each slide gets 2–4 sentences of plain spoken English that one of the three presenters can read naturally. Suggested split: slides 1–4 Divyansh, 5–8 Ayush, 9–14 Divyanshu. Mark the presenter at the start of the notes.

## Sources to verify against

- `paper/latex/main.tex`
- `report/final_report.tex`
- `report/phase2_chapter.tex`
- `results/pilot_b/*/RESULTS.md`
- `results/phase2/final_test/phase2_analysis.md`
- `results/phase2/audit/README.md`
- `analysis/phase2_exploratory/README.md`
