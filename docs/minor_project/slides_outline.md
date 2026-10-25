# Minor evaluation — final slide outline (14 slides, about 10–12 minutes)

Updated 26 October 2026 with the verified Pilot-B results. Every number is traceable to `results/pilot_b/SUMMARY.md`, `results/pilot_b/*/RESULTS.md`, `docs/DECISIONS.md`, `pilot_b/FROZEN.md`, `phase2/*_FROZEN.md` or `pilot/reviews_v2_round2/README.md`, and matches `paper/latex/main.tex`. Label every slide with its evidence type: **development evidence** (excluded fixtures) or **Pilot-B result**. Never pool Pilot-B with the original pilot.

---

**1. Title**
- Hinglish Mathematical Reasoning in LLMs: does the language form of a maths problem change the answer?
- Student name / roll number / department / faculty in charge: ____________
- *Speaker note (20 s):* one sentence on the question: same maths, three language forms, does the answer change?

**2. Motivation**
- Same marbles question in three forms: E "How many marbles does Aman have?" / R "Aman ke paas kitne kanche hain?" / C (insertional Hinglish, e.g. "23 add karta hai").
- Indian users mix Hindi and English in Roman script; benchmarks are mostly English or Devanagari.
- *Speaker note (40 s):* read the three forms aloud; stress that only the language changes.

**3. The confound and our design**
- A drop could come from vocabulary, spelling, mixing, wording, or the evaluation protocol itself.
- Design: matched families (one problem, three renderings), gold computed in code, all analyses paired by family.
- *Speaker note (40 s):* unrelated English vs Hinglish questions cannot separate these causes; holding the maths fixed can.

**4. Research questions and related work**
- RQ1 (this phase): does an unchanged model's accuracy differ across E, R, C?
- RQ2/RQ3 (major phase): does E+C training beat matched E+R training on held-out C; transfer and English retention?
- Prior work (MGSM, Anand et al., CodeMixBench, Indi-RomCoM, Sarvam-M, CodeMixTax) already shows Romanized/code-mixed drops, so an E/R/C gap alone is not novel. Our contributions: a format-measurement caution, a paired reviewed E/R/C resource with operation-word balance, a pre-registered diagnostic pilot; the controlled training comparison comes next.
- *Speaker note (50 s):* be explicit that we do not claim the gap as a discovery.

**5. Data: 370 frozen families plus the original pilot**
- Table: Pilot-B 70 (Claude-drafted; one bilingual reviewer: 57 ACCEPT / 13 REVISE / 0 REJECT); Phase-2 FINAL_TEST 100 (GPT; one reviewer: 32 ACCEPT / 68 REVISE), DEV 40 (GPT), TRAIN 160 (Claude); TRAIN/DEV sample review of 45 families (19 ACCEPT / 26 REVISE). All frozen 16 Oct with SHA-256 hashes; FINAL_TEST untouched until the confirmatory evaluation.
- Blind dual-LLM solving: Pilot-B 210/210 (and 15/15 revised); Phase 2 Claude 900/900, GPT 897/900 (one family, GPT error). No Qwen model ever drafted, solved or checked.
- Original pilot: 30 families, two independent bilingual reviewers (R01, R02) plus adjudicator A01 → 24 ACCEPT / 5 REVISE / 1 EXCLUDE; cohort = 24 families accepted without repair (D036).
- *Speaker note (60 s):* review finding: GPT-drafted Romanized Hindi was over-formal (68/100 needed repair vs 13/70 Claude-drafted); descriptive, confounded with split. C was redefined as insertional Hinglish after review (D033).

**6. Pipeline and protocol**
- Diagram: frozen data → Colab T4 notebook (NF4 4-bit, FP16, greedy, thinking off, 1,024 tokens, fresh context) → append-only journal with resume → strict scorer v1.0.0 (primary) + numeric_literal_v1 (secondary) → checksummed results ZIP.
- One English instruction (prompt v2) for all forms and models; Wilson 95% intervals; paired differences with 10,000 family-bootstrap resamples.
- Analysis plan pre-registered (`pilot_b/PREREGISTRATION.md`) before any Pilot-B output.
- *Speaker note (40 s):* the pipeline refuses to resume after any code/data/config change; every run's ZIP hash is recorded.

**7. Development finding 1: the answer format confounds the measurement** *(development evidence, excluded fixtures)*
- Table: prompt v1 → v2 on 36 fixture prompts (Qwen3-4B): format failures 10/36 → 0/36; strict correct E/R/C 9/7/9 → 12/10/12 of 12; R explanations in Devanagari 8/12 → 0/12.
- Example: `FINAL: 8 unitless` after a correct dimensionless answer.
- *Speaker note (50 s):* one disclosed prompt revision (D020), frozen before any pilot output. The fixtures also changed slightly, so 10 → 0 is a development comparison, not an isolated prompt effect.

**8. Development finding 2: model screening (7 models)** *(development evidence)*
- Table: strict-invalid of 36 / correct E/R/C of 12: Qwen3-4B 0 (12/10/12, primary); Qwen3-8B 0 (12/12/12); Llama-3.2-3B 2 (12/9/9); Qwen3-1.7B 36 (instruction echo); Phi-4-mini 14 (inline FINAL, R repetition); Granite-3.3-2B 36 (commentary after FINAL); Gemma-3-4B no outputs (CUDA error under FP16).
- Pre-declared rule: ≤3/36 strict-invalid, no per-model tuning → three backbones.
- Development hypothesis: Qwen3-4B's two remaining errors were R misreadings of *bhaag* (divide) and *bhinn* (fraction / "different"); Llama gave the same wrong answer on the *bhinn* item.
- *Speaker note (50 s):* within Qwen3, instruction following broke before maths did. Without this screen, a multi-model comparison would mostly measure formatting. The *bhaag/bhinn* idea is a hypothesis from n = 2 unreviewed items; slide 11 tests it.

**9. Pilot-B result: accuracy by form** *(Pilot-B result)*
- **Figure: `paper/figures/accuracy_by_form.png`** (strict accuracy by form with 95% Wilson intervals, 70 families per bar).
- Numbers beside the figure (E / R / C, %): Qwen3-4B 94.3 [86.2, 97.8] / 85.7 [75.7, 92.1] / 94.3 [86.2, 97.8]; Qwen3-8B 98.6 [92.3, 99.7] / 91.4 [82.5, 96.0] / 98.6 [92.3, 99.7]; Llama-3.2-3B 94.3 [86.2, 97.8] / 57.1 [45.5, 68.1] / 70.0 [58.5, 79.5].
- *Speaker note (60 s):* 70 families × 3 forms = 210 prompts per model, all three runs complete (210/210) and checksum-verified; no refusals. R is the lowest bar for every model. Single-reviewer data (D035), diagnostic sample.

**10. Pilot-B result: paired differences** *(Pilot-B result)*
- Table (pp, 95% bootstrap interval, discordant first-only/second-only):
  - Qwen3-4B: E−R +8.6 [−1.4, +18.6] (9/3); E−C 0.0 [−7.1, +7.1] (3/3); R−C −8.6 [−15.7, −1.4] (1/7)
  - Qwen3-8B: E−R +7.1 [0.0, +14.3] (6/1); E−C 0.0 [−4.3, +4.3] (1/1); R−C −7.1 [−14.3, 0.0] (1/6)
  - Llama-3.2-3B: E−R +37.1 [+24.3, +50.0] (28/2); E−C +24.3 [+11.4, +37.1] (21/4); R−C −12.9 [−27.1, +1.4] (10/19)
- Takeaways: R deficit is model-dependent (about 7–9 points for Qwen, 37 for Llama); C = E for both Qwen models; 4B → 8B improves every form but the R deficit stays (8.6 → 7.1 pp).
- *Speaker note (60 s):* for Qwen the E−R intervals cross or touch zero, so call it modest; for Qwen3-4B the R−C interval excludes zero (C better in 7 families, R in 1). Headline: Romanized Hindi, not code-mixing, is the hard case.

**11. Pilot-B result: the operation-word hypothesis is not supported** *(Pilot-B result, descriptive stratum)*
- Table, R accuracy by stratum (C keeps R's Hindi op-word, 18 families / C switches it, 17 / no op-word, 35): Qwen3-4B 89 / 82 / 86%; Qwen3-8B 94 / 94 / 89%; Llama 67 / 59 / 51%.
- R errors are spread across families with and without Hindi operation words, for all models.
- *Speaker note (40 s):* an honest null: the development hypothesis from slide 8 does not explain the gap. Many Llama R errors are plain arithmetic slips (PB017: 1200 − 3×265 = 405, answered 435). Strata are small and descriptive.

**12. Residual format effects and an exploratory note**
- Llama: numeric endpoint agrees with strict on all 210, so its gaps are not formatting.
- Qwen3-4B: 3 of 4 E failures are correct values with unlisted unit phrases (`11 years old`, `13 years old`, `4 bags of cement`); 1 C failure is the spelling `300 rupye`; together 4 strict points.
- Secondary endpoint specification gap: trailing `₹` (`FINAL: 1575 ₹`) explains every strict-correct/numeric-fail case (30 for Qwen3-4B, 36 for Qwen3-8B); reported as pre-registered, not corrected post hoc.
- Exploratory, not pre-registered (Llama): Hindi-prose explanations on 60/70 R and 27/70 C outputs despite the English instruction; on C, Hindi-prose answers correct 13/27 (48%) vs 36/43 (84%) for English.
- *Speaker note (50 s):* format problems shrink but do not vanish after the fix. The Llama association is observational (harder items may trigger both); it needs the planned English-compliance audit.

**13. Limitations**
- Diagnostic scale: 70 families; strata of 17–35 families.
- Single bilingual reviewer for Pilot-B and FINAL_TEST; TRAIN/DEV sample-reviewed only.
- AI-drafted items; Claude drafted and solved Pilot-B; different C definitions in the original 30 vs Pilot-B.
- Small, 4-bit, greedy, non-thinking models; format screening excluded 4 of 7.
- No Devanagari arm, so the R gap mixes script, vocabulary, register and spelling; contamination cannot be audited.
- *Speaker note (40 s):* emphasise what the evidence does not show: no causal mechanism, no training result yet.

**14. Status and plan to May 2027**
- In progress: the 24-family original-pilot cohort (two independent reviewers plus adjudicator) is being run under the same frozen protocol; **results pending**, to be reported separately.
- Nov 2026: original-pilot analysis; error-taxonomy and English-compliance audit. Dec–Jan: T4 training feasibility smoke test; second-annotator sample. Feb–Mar: E+E / E+R / E+C fine-tuning on frozen TRAIN/DEV, one confirmatory run on FINAL_TEST. Apr–May: analysis, thesis, submission.
- Publication: EACL 2027 Student Research Workshop short paper (submission 15 Dec 2026); training study for ARR May 2027 (date unconfirmed).
- *Speaker note (40 s):* close on the headline: holding the maths fixed, small models lose accuracy on Romanized Hindi rather than on code-mixing, by a strongly model-specific amount, and answer formats must be checked on excluded data first.

---

Timing: about 11–12 minutes in total; to fit 10 minutes, merge slides 7 and 8 and shorten slide 12. Backup slides (optional): full screening table, per-model numeric-endpoint figures (Qwen3-4B E 72.9 / R 82.9 / C 82.9%; Qwen3-8B E 84.3 / R 74.3 / C 80.0%), the original-pilot review flow (R01 83/90 and R02 87/90 matched the reference before adjudication).
