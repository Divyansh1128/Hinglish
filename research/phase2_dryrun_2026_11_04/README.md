# Phase-2 round-3 CPU rehearsal — synthetic software checks only

Run from the repository root:

```sh
python3 -B phase2/build_implementation_manifest.py
python3 -B colab_notebooks/build_phase2_notebooks.py
python3 -B research/phase2_dryrun_2026_11_04/dryrun.py
python3 -B research/phase2_b2_b3_b4_2026_11_04/probes.py > research/phase2_dryrun_2026_11_04/b2_b3_b4_probes.json
```

`summary.json` records the successful flow, refusal probes and hashes. `before_config_digest_fix.json` preserves the
first run's genuine training-to-analysis failure: the builder hashed engine configurations with spaced JSON while
analysis used the engine's compact JSON. `dryrun.log`, `synthetic_freeze.md` and `synthetic_analysis.json` are generated
by the rehearsal. They are **synthetic software fixtures**, including every apparent decision label or accuracy.
They contain no model output and are not study results. Timestamps and random run/session IDs make their hashes
vary between rehearsals. The implementation hash is stable while the implementation is unchanged.

The actual trainer validates TRAIN bytes, builds and audits labels with a mock character tokenizer, executes its
registered exposure order and all 60 update windows using mock tensor/model operations, saves mock adapters and
checkpoints through the real filesystem functions, and logs real plan outcomes. The model/tokenizer, GPU tensor
operations, package/hardware observations, and Hub identities are mocked. Hub-byte/template refusal behavior is
separately covered by the B2 probes and regression suite. The first attempt fails during training; its fresh retry
succeeds. Another attempt is left STARTED with its writer lock, then explicitly recovered before its retry.

The baseline and nine adapter DEV reports use the real 40-family DEV data and engine. FINAL_TEST uses 100
DEV-derived fixture families with distinct synthetic identities, under mocked evaluation and analysis dataset
loaders. Engine schema validation stays active; no real FINAL_TEST content is loaded. The real gate, sealed exports,
freeze-manifest CLI, source/config/environment validation, paired analysis and 10,000-resample calculation execute.
Baseline k is derived from its frozen archive, and a caller-supplied k is refused. The rehearsal's fixed backend
produces k=0, which says nothing about model accuracy.

Regression tests in `t4_smoke/test_phase2_eval.py` additionally interrupt DEV after seven generations, require
explicit stale-lock recovery, preserve all seven journal files byte-for-byte, complete 120 generations, avoid
reloading a complete report, refuse freezing without adapter nine's report and check frozen DEV-export hashes.
Notebook tests verify that an unfinished DEV check blocks the next training attempt and that the evaluation runs
through the existing subprocess helper. Training-writer tests confirm that both recorded halting failure classes
survive recovery.

See `handoffs/2026-11-04_sol_round3.md` for the review and final verification results.
