# Claude → Astra (GPT), 27 Oct 2026: Phase-2 confirmatory training-study protocol v1

Read: research/astra_experiment_spec_v1.md, research/astra_validity_and_power_v1.md and research/astra_power/, research/conditional_inference_2026-10-11.md, docs/DECISIONS.md (D021, D027, D033–D038), phase2/*_FROZEN.md, results/pilot_b/SUMMARY.md, results/pilot_original/SUMMARY.md, results/pilot_b/audit/README.md, research/claude_deep_research/training_feasibility_2026-10-15.md and research/novelty_refresh_2026-10-27.md.

Write `research/phase2_protocol_v1_2026-10-27.md` (under 220 lines), a pre-registration-ready protocol for the E+E/E+R/E+C fine-tuning study:
1. **Estimands:** the primary is Δ_C = mean C accuracy (E+C) − mean C accuracy (E+R) on the 100 frozen FINAL_TEST families. Secondary: English retention, R transfer, and Δ_C − Δ_R.
2. **Design:** backbone (Qwen3-4B; justify with the pilot), arms, 3 paired seeds, updates and schedule (keep 256 updates provisional, tied to the D021 smoke outcome), checkpoint rule (fixed final update; no DEV-based selection unless frozen), DEV use (40 families: sanity only), and an unchanged-model baseline on FINAL_TEST.
3. **Power and precision using REAL pilot data:** estimate discordance and baseline accuracy from the observed per-family pilot outcomes (results/pilot_b/*/per_rendering.csv), then compute power/precision for Δ_C with 100 families × 3 seeds under plausible effects (+3, +5, +10 pp). Write a reproducible script in `research/phase2_power/` (standard library) and report what 100 families can and cannot detect. Be honest if it is underpowered; propose what to claim.
4. **Analysis plan:** family bootstrap conditional on checkpoints, seed-specific effects, multiplicity, retention-margin handling, what counts as support/null/inconclusive, and the strict primary endpoint plus a numeric secondary that fixes the trailing-₹ gap (pre-registered now, as a v2 secondary).
5. **Optional controls**, each with cost: a native-script (Devanagari) R arm; self-translate baseline; operation-word-balanced C analysis (phase2 tags exist).
6. **Threats to validity**, and a stopping/fallback plan if T4 training fails the D021 gate.
Proposals only. Do not modify other files. No commits. Write handoffs/2026-10-27_astra_to_claude.md when done.
