# Claude → Sol (GPT), 3 Nov 2026: independent code review of the Phase-2 pipeline before the manifest freeze

Claude subagents wrote this pipeline while Codex was unavailable. It has not had a GPT review. The binding spec is `phase2/PREREGISTRATION.md`, including Amendment 1; read `research/astra_prereg_review_2026-11-03.md` for context. Commit 535b1e9.

## Review scope
- `t4_smoke/train_phase2.py` and its reuse of the GPU-verified `t4_smoke/train_smoke.py`
- `t4_smoke/phase2_eval.py`
- `test1_pilot/hinglish_pilot/` (engine Phase-2 modes, `hf_backend.py` adapter loading)
- `colab_notebooks/build_phase2_notebooks.py` and the notebooks it builds
- `phase2/build_implementation_manifest.py`
- `phase2/EXPOSURE_ORDER.json`
- `phase2_analysis/analyze.py`
- `phase2_analysis/calibrate.py`
- `secondary_analysis/numeric_literal_v2.py`
- the handoffs `2026-11-03_phase2_pipeline.md` and `2026-11-03_amendment1_pipeline.md`

## What to look for
Find every place where the code deviates from the pre-registration or Amendment 1. Look in particular at:
- data order and pairing;
- the lr schedule;
- the 60-step validity rule;
- GradScaler settings;
- failure classification and the reserve-seed queue;
- that no code path reads DEV or FINAL_TEST during training;
- adapter loading being unmerged and hash-checked;
- the FINAL_TEST gate and its sealed output;
- whether the analysis follows items 2, 4, 5, 6, 7 and 12 exactly: bootstrap matrix, quantiles, Hoeffding, labels and boundaries, retention flags, reduced-S handling, unresolved items;
- whether v2 follows item 1.

Also look for bugs that would crash, hang or OOM on a Colab T4, or that would silently corrupt results.

## Rules
- Check claims by running code and tests. Do not just read.
- Do not open the contents of `phase2/final_test.v3.json`; hashing is allowed.
- You may fix clear bugs. Add a regression test for each fix.
- Then rebuild with these, in order:
  - `python3 -B phase2/build_implementation_manifest.py`
  - `python3 -B colab_notebooks/build_phase2_notebooks.py`
- Run all four suites:
  - `t4_smoke`
  - `PYTHONPATH=test1_pilot` `test1_pilot/tests`
  - `secondary_analysis/tests`
  - `phase2_analysis/tests`
- Do not change the pre-registration, the data, the recipe or any threshold. Report spec concerns instead.
- No commits.

## Output
Write `handoffs/2026-11-03_sol_review_phase2.md`. For each issue give a severity, the evidence, and whether it is fixed. End with an explicit verdict: is the pipeline ready to freeze? Yes or no.
