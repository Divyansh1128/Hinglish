# Astra → Claude, 27 Oct 2026: Phase-2 confirmatory protocol v1 + real-data power

**Provenance:** this task was done by a **Claude Opus research subagent in place of Astra (GPT)**, because Codex authentication had expired. It replaces an older, unrelated handoff with the same filename (the novelty-refresh handoff; that content lives on in `research/novelty_refresh_2026-10-27.md`). No commits. No other files were touched. No training, no new inference, and FINAL_TEST was not read.

## Delivered
- `research/phase2_protocol_v1_2026-10-27.md` (202 lines): estimands, design, power, analysis plan, optional controls with costs, threats to validity, and the D021 fallback.
- `research/phase2_power/phase2_power.py`: standard library only, deterministic (byte-identical outputs on rerun, checked twice), about 30 s. Run it with `python3 research/phase2_power/phase2_power.py`.
  - Inputs: `results/pilot_b/{qwen3-4b,qwen3-8b,llama-3.2-3b}/per_rendering.csv` (SHA-256s recorded).
  - Outputs: `pilot_estimates.json`, `power_grid_n100.csv`, `n_scaling.csv`, `secondary_and_validation.json`, `manifest.json`.

## Key numbers (N = 100 families, 3 paired seeds; family-bootstrap-equivalent 95% interval)
- **Pilot inputs.** Qwen3-4B C accuracy is 66/70 = 94.3%. Discordance proxies:
  - 0.071 for C across checkpoints (4B vs 8B);
  - 0.114 for C vs R within Qwen3-4B;
  - 0.200 for R across checkpoints.
- **Ceiling.** If the E+R arm's C accuracy stays at about 94%, the headroom is 5.7 pp, so **+10 pp is impossible** and discordance above about 0.114 is infeasible.
- **Precision.** Δ_C half-width is about 2–5 pp. The false "support" rate is 1.6–2.8%.
- **Power, P(lower bound > 0).**
  - +3 pp: 0.21–0.58.
  - +5 pp: 0.45–0.96 (0.67 in the central case p0 = 0.857, q0 = 0.114).
  - +10 pp: 0.95–1.00 where it is feasible.
- **"Useful ≥5 pp" claim** (lower bound > 5 pp): ≤0.025 at true +5, and 0.41–0.60 at true +10.
- **Per-seed McNemar** at +5: 0.13–0.37. **All 3 seeds positive** under the null: 0.05–0.10.
- **English non-inferiority** (−2 pp margin) when the true loss is zero: shown only 29–52% of the time. **Not establishable.**
- **Δ_C − Δ_R** null half-width: about 2.9–4.3 pp.
- **Hoeffding reference interval** radius: 27.2 pp (uninformative).
- **Larger N, central case:** +3 pp needs about 600 families for 96% power; +5 pp reaches 92% at N = 200. Only 100 FINAL_TEST families exist.
- **Check of the Wald shortcut** against the real percentile bootstrap: decisions agree 98.7–100%.

## Recommended claims
1. Present Δ_C as a **pre-registered estimate with about ±3–4 pp precision**, conditional on the checkpoints.
2. Decision rules:
   - **support:** lower bound > 0;
   - **useful support:** lower bound > 5;
   - **informative null:** the interval contains 0 and the upper bound is < 5, which rules out the useful gain;
   - **harm:** upper bound < 0;
   - **inconclusive:** anything else.
3. Keep English retention, R transfer and specificity descriptive (Holm across them if any is ever tested). Say "retention not established" unless the lower bound is > −2 pp.
4. Flag the ceiling openly. Also flag that E+R shares Hindi with C, so a small Δ_C is expected a priori.

## Decisions needed (proposals, not adopted)
- **Margins.** Adopt +5 pp useful gain and −2 pp retention.
- **128-update timing rule.** Use 128 updates if 2,304 updates are infeasible (decided on timing only). 256 updates over 160 families is about 13 passes.
- **Amend D021's fallback.** Switch to Llama-3.2-3B instead of Qwen3-1.7B, which failed the format rule (D029).
- **Ceiling flag.** Check unchanged-model DEV difficulty before training; flag the ceiling if DEV C ≥ 95%.
- **Numeric endpoint.** Pre-register `numeric_literal_v2`, which accepts a ₹/Rs/INR/rupees affix when the gold unit is rupees, as a secondary only. On Pilot-B it gives Qwen3-4B E/R/C 69/61/67 vs v1 51/58/58.
- **Optional controls.** Recommended: self-translate (400 generations) and the operation-word analysis (free). Llama-3.2-3B second backbone only if the ceiling flag fires (doubles cost). Devanagari arm not recommended (about +33% training plus new reviewed renderings and a new FINAL_TEST version).

## Caveats
- The trained-arm seed-to-seed discordance is unobserved; the grid uses unchanged-model proxies.
- The effect model assumes proportional gains with no offsetting losses, which is optimistic; heterogeneous effects mean lower power.
- C/R independence for specificity is an assumption.
