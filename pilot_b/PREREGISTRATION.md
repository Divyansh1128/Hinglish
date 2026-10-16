# Pilot-B evaluation: pre-registered analysis plan

Written 16 October 2026, **before any model output on Pilot-B exists**. Decision D035. Data: `pilot_b_families.v2.json` (hash in `FROZEN.md`). Committed to git before the notebooks are run, so the commit time proves the order.

## Design
- 70 families × 3 forms (E, R, C) = 210 prompts per model. Fresh context per prompt; seeded order.
- Backbones (unchanged, D030/D032): Qwen3-4B (**primary**), Qwen3-8B, Llama-3.2-3B-Instruct. Each runs once, with identical settings.
- Frozen protocol: prompt `test1-english-final-v2`; greedy, non-thinking decoding; NF4 + FP16 on a T4; 1,024-token output cap; scorer v1.0.0; one infrastructure retry; no answer-dependent retries; no prompt or scorer change after seeing outputs.

## Endpoints
1. **Primary:** strict accuracy (scorer v1.0.0) per form, Qwen3-4B.
2. **Secondary:** `numeric_literal_v1` per form (D018); strict-invalid reason counts.
3. **Paired:** E−R, E−C and R−C family-level differences, with 10,000 family bootstrap resamples (seed 101) and discordant counts.
4. **Descriptive, per model:** the same tables for Qwen3-8B and Llama-3.2-3B, and the 4B vs 8B scaling contrast.
5. **Descriptive operation-word strata:** accuracy on R and C by the drafting tag (Hindi operation word in R with C keeping it / switching it to English / no operation word). Counts and percentages only; tags are taken from family provenance as frozen.
6. **After the run:** English-compliance tags and an error taxonomy (D018 categories) from an AI pre-tag plus a human check of disagreements and a sample. Resources: tokens and latency per form.

## Interpretation rules
- 70 families is a diagnostic sample. Intervals are reported; no significance claims; topic and stratum results are descriptive.
- Pilot-B is single-reviewer data with an insertional C definition (D033). It is reported separately from the original 30-family pilot and never pooled with it.
- All results are reported whatever their direction, including null results and runs that fail.
- Incomplete runs: headline accuracy is suppressed, as the engine does.
- FINAL_TEST (`phase2/`) is never evaluated here.
