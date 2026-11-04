# Claude → Astra (GPT), 4 Nov 2026: Phase-2 Colab operator runbook

The user, a student, will run every Phase-2 Colab notebook personally. Write `docs/phase2_runbook.md`, under 180 lines, in plain language for that user. It should be a step-by-step operator guide covering:

1. The order of runs:
   - `Phase2_Baseline_DEV.ipynb` once;
   - `Phase2_Train.ipynb` repeatedly (the notebook picks the next run itself);
   - after the freeze, `Phase2_FinalTest.ipynb`.
2. For each notebook:
   - what to click;
   - Drive access;
   - expected time (training is about 21 minutes per run);
   - what a successful finish prints;
   - which ZIP to send to Claude.
3. Every failure message the operator can see, what it means, and exactly what to do:
   - infrastructure failure (disconnect, OOM), with its single retry;
   - a numerical or protocol failure ("THE STUDY HALTS"): stop and send the log;
   - stack mismatch or a non-T4 GPU;
   - stale evaluation lock (`RECOVER_STALE_LOCK`);
   - stale writer (`RECOVER_STALE_WRITER`, being added now);
   - baseline missing.
   Stress the safety rules: never set the recovery flags while another Colab tab is running; never edit cells; never run two sessions at once; never open FINAL_TEST.
4. A checklist table of the 9 training runs, in the order the plan gives them (slot 11 with EC, ER, EE; then 22; then 33), with columns for the operator to tick off and paste the ZIP hash.
5. What happens after the 9 runs (the freeze manifest, done by Claude) and before FinalTest.

Ground every statement in the actual code and notebook text: `colab_notebooks/build_phase2_notebooks.py`, `t4_smoke/train_phase2.py`, `t4_smoke/phase2_eval.py`, `colab_notebooks/README.md` and `phase2/PREREGISTRATION.md` (Amendments 1–3). Quote the real printed messages where they exist. Mark anything still being changed today (the writer-lock flag) as "being added; check the notebook". Claude agents are editing `t4_smoke/` and `phase2_analysis/` right now: read only, and do not edit any file except `docs/phase2_runbook.md` and `handoffs/2026-11-04_astra_to_claude.md`. Do not open FINAL_TEST contents. No commits.
