# Tokenization and question length vs the R deficit (POST-HOC EXPLORATORY)

**Status: POST-HOC EXPLORATORY.** This was written on 2026-10-27, after every Pilot-B and original-cohort output had been seen. It implements analyses A1/A2 of `research/claude_deep_research/mechanisms_tokenization_2026-10-15.md`, but it was not frozen before the outputs were seen. It is descriptive only: the cohorts are small (Pilot-B n = 70 families; original cohort n = 24), there is no multiplicity correction, and no causal claim is made. The two cohorts are reported separately and never pooled.

## Method
- **Tokenizer.** `Qwen/Qwen3-4B` `tokenizer.json` at revision `1cfa9a7208912126459214e8b04321603b3df60c` (sha256 `aeb13307…2dae4`, checked by the script), loaded with `tokenizers` 0.23.3 and `add_special_tokens=False`. Qwen3-8B uses the same tokenizer. Check: for both Qwen models, the stored whole-prompt `input_tokens` differences R−E and C−E equal our question-only differences in 70/70 and 24/24 families. The question counts therefore match the run.
- **Llama-3.2-3B.** Its tokenizer is gated and was not downloaded. For Llama we report (i) the Qwen3 question counts as a length proxy that is independent of the model, and (ii) the R−E differences of the stored whole-prompt `input_tokens`. The template is constant across forms, so (ii) is a question-level difference measured with Llama's own tokenizer. Question-only Llama counts and Llama piece counts are not available.
- **Texts.** The frozen `forms.*.text` of every ACCEPT family in `pilot_b/pilot_b_families.v2.json` (70) and `pilot_original/cohort_dataset.json` (24). Words are split on whitespace. Each token is assigned to the word that holds its last non-space character.
- **Operation words.** The lexicon is section 2 of `research/operation_vocabulary_2026-10-15.md`: each entry plus its listed variants, matched whole-word and case-insensitively, with the multi-word entries `mil kar` and `ek jais*` included. "Pieces" counts the tokens that overlap the alphabetic span of the word in context. E has 0 matches, as a sanity check.
- **Correctness.** The strict `correct` column of each `per_rendering.csv` (scorer v1.0.0).
- **Tests in (c).** Among families where E is correct: an exact two-sided permutation test of the difference in mean R−E tokens, computed by full enumeration, between "R wrong" and "R correct". A one-predictor logistic regression (R correct ~ R−E tokens) is fitted only when both classes have at least 5 families and there is no separation.
- **Reproduce.** `python -I analysis/tokenization/analyze.py --tokenizer <path>/tokenizer.json` writes `results.json`. The script is deterministic: two runs gave byte-identical output.

## A1. Tokenization per form (Qwen3 tokenizer, question text only)

| Cohort | Form | Median tokens | Median words | Median tokens/word | Alphabetic words with ≥3 pieces |
|---|---|---:|---:|---:|---:|
| Pilot-B | E | 35 | 24 | 1.45 | 1.4% |
| Pilot-B | R | 49 | 24 | 2.00 | 16.5% |
| Pilot-B | C | 45 | 24.5 | 1.78 | 9.4% |
| Original | E | 37.5 | 28.5 | 1.33 | 0.2% |
| Original | R | 59.5 | 30 | 1.96 | 15.0% |
| Original | C | 44 | 29.5 | 1.54 | 3.4% |

Paired differences per family (median [IQR]):

| Cohort | R−E tokens | R/E ratio | C−E tokens | C/E ratio | R−E tokens/word |
|---|---|---|---|---|---|
| Pilot-B | +15 [10.25, 18.75]; R longer in 70/70 | 1.42 | +8 [5, 12]; C longer in 67/70 | 1.24 | +0.60 |
| Original | +22.5 [12.75, 31.75]; R longer in 24/24 | 1.61 | +8 [3.75, 9]; C longer in 20/24 | 1.21 | +0.60 |

So R costs about 1.4–1.6x the question tokens of E, at roughly the same word count: the extra cost is in segmentation, not in more words. The earlier "~25% longer" whole-prompt figure understated the question-level ratio.

**Pieces per Hindi operation-word occurrence:**
- **Pilot-B R:** 54 occurrences in 37 families; median 2 pieces, mean 2.07; 27.8% have ≥3 pieces.
- **Pilot-B C:** 30 occurrences; mean 2.23.
- **Original R:** 63 occurrences in 21 families; mean 2.21; 39.7% have ≥3 pieces.
- **For comparison:** the average alphabetic R word has 1.76 pieces (Pilot-B) and 1.78 (original).

Some operation words split into 3 pieces in context: `bhaag`, `anupat`, `ghata*`, `pratishat`, `zyada`, `nikaal`. `ek jaisi` takes 4 pieces. `kul` and `har` take 1. Operation words are only slightly more fragmented than other R words.

## A2. Length vs correctness, per model

**(a) R accuracy by tercile of R question tokens.** Ranks are computed within each cohort.

| Cohort | Tercile range (tokens) | Qwen3-4B R | Qwen3-8B R | Llama-3.2-3B R |
|---|---|---|---|---|
| Pilot-B | T1 32–44 (n 23) | 82.6% | 87.0% | 60.9% |
| Pilot-B | T2 44–54 (n 24) | 87.5% | 95.8% | 66.7% |
| Pilot-B | T3 54–87 (n 23) | 87.0% | 91.3% | 43.5% |
| Original | T1 24–47 (n 8) | 75.0% | 100% | 75.0% |
| Original | T2 50–73 (n 8) | 100% | 100% | 50.0% |
| Original | T3 77–124 (n 8) | 100% | 87.5% | 62.5% |

Llama's E accuracy in the Pilot-B top tercile is 95.7%, so long E items there are not hard for Llama in English.

**(b) Families with E correct: R wrong vs R correct.** Values are R−E tokens (Qwen3 counts), median [IQR].

| Cohort / model | E✓R✗: n, R−E | E✓R✓: n, R−E | (c) exact p | (c) logistic OR per +10 tokens [Wald 95%] |
|---|---|---|---|---|
| Pilot-B Qwen3-4B | 9, 15 [9, 16] | 57, 14 [10, 19] | 0.17 | 2.49 [0.67, 9.22] |
| Pilot-B Qwen3-8B | 6, 13 [9.25, 19.75] | 63, 15 [11, 18.5] | 0.93 | 1.09 [0.31, 3.83] |
| Pilot-B Llama-3.2-3B | 28, 16.5 [13.25, 21] | 38, 13.5 [10, 16.75] | 0.073 | 0.48 [0.21, 1.09] |
| Original Qwen3-4B | 2, 10.5 | 22, 25.5 | 0.14 | not fitted (2 events) |
| Original Qwen3-8B | 1, 30 | 23, 21 | 0.83 | not fitted (1 event) |
| Original Llama-3.2-3B | 7, 24 [12, 31] | 14, 19 [12.25, 27.75] | 0.85 | 0.93 [0.46, 1.85] |

- **Llama with its own tokenizer.** Using the stored whole-prompt R−E counts gives the same picture. In Pilot-B the medians are 16 vs 13, with p = 0.074 and OR 0.48 [0.21, 1.09]. In the original cohort they are 24 vs 18.5, with p = 0.83.
- **Raw R length.** For Pilot-B Llama, raw R length gives exact p = 0.037 (median 53 vs 47). This is the only nominal p below 0.05 among the 14 post-hoc permutation tests (plus 6 logistic fits).
- **Qwen.** An OR above 1 means that longer R−E went with R being correct more often, not less.

**Output tokens** (median, E/R/C):
- **Pilot-B:** Qwen3-4B 104/98.5/93.5; Qwen3-8B 72.5/73.5/72.5; Llama 99/119.5/96.5.
- **Original:** Qwen3-4B 94.5/101.5/91.5; Qwen3-8B 72/75/69.5; Llama 97/128/105.

Only Llama writes noticeably longer answers on R.

## Limits
- **Post hoc, small samples, no correction for multiple tests.** There are only 1–9 R-wrong families per cohort for Qwen, so the Qwen tests have almost no power. A null result here is not evidence that length has no effect.
- **Confounds.** Length is confounded with item content, the number of quantities and the number of Hindi words. Fragmentation is confounded with how rare the Romanized register is in pretraining. The design cannot separate any of these.
- **Llama tokenizer.** Llama piece and fertility figures are not available, because the Llama tokenizer is gated.
- **Lexicon.** The lexicon is a bilingual-unconfirmed proposal (status P). Matching is surface-only and does not judge the sense of a word in context.
- **Outcome.** Only the strict endpoint was used.
- **Data provenance.** Pilot-B renderings are single-reviewer frozen data, and some Pilot-B renderings are v2.

## Conclusion (for the thesis Discussion)
In a post-hoc exploratory analysis with the pinned Qwen3 tokenizer, Romanized-Hindi (R) questions were consistently longer than their English (E) counterparts: a median of +15 tokens (ratio 1.42) in Pilot-B and +22.5 (ratio 1.61) in the original cohort, at nearly the same word count, because R words split into more pieces (2.0 vs 1.45 tokens per word). Hindi operation words were only slightly more fragmented than other R words. Length does not account for the R deficit in the Qwen models. Their R errors did not occur in longer or more fragmented items: the median R−E difference was 15 vs 14 tokens for Qwen3-4B and 13 vs 15 for Qwen3-8B. In addition, code-mixed (C) questions were also longer than E (median +8 tokens), yet Qwen's C accuracy equalled its E accuracy in both cohorts. For Llama-3.2-3B there was a weak association in Pilot-B: R-wrong families had larger R−E differences (16.5 vs 13.5 tokens; exact p = 0.07), and the longest tercile had the lowest R accuracy. This association did not appear in the original cohort and would not survive any correction for multiple testing. Given the small samples, the many post-hoc comparisons and the confounding of length with item content and register rarity, we treat tokenization length as at most a minor correlate. We interpret the R gap as a language-form effect, not a demonstrated tokenization effect. Interventions that hold the content fixed while changing the wording (A4 lexical swaps, A6 length padding) would be needed to test the mechanism.
