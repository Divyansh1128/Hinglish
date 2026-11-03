# Phase-2 training and evaluation pipeline (3 Nov 2026)

**Author:** a Claude Opus subagent, working under D017.

**Governing documents:** D043 and `phase2/PREREGISTRATION.md` (SHA-256 `74be2328…2840`, commit 58d330d). The pipeline follows §3–§5, §10 and §11.

**Not changed:** the recipe, the schedule, any data, any frozen file, `paper/`, `report/`, `results/`, numeric_literal_v2 and `phase2_analysis/`. No commits were made.

## Files

| File | What it does |
|---|---|
| `t4_smoke/train_phase2.py` | Full training. It reuses the GPU-verified `train_smoke.py` (labels, model load, `Trainer`, digests, memory sampler, stack checks) without modifying it. New in this file: <ul><li>data from all 160 TRAIN families, through `select_families` with hash checks;</li><li>the §3 order `phase2-D043:{s}:{p}:{family_id}`, with E then the second example;</li><li>the lr schedule `lr_at`;</li><li>run-seeded LoRA initialisation;</li><li>a checkpoint every 10 updates (atomic, latest only, exact-digest and probe reload check);</li><li>the final adapter after update 60, checked tensor by tensor against memory, with the SHA-256 of `adapter_model.safetensors` and `adapter_config.json`;</li><li>a per-update log of loss, grad norm, lr, scaler skip, tokens, s/update and memory;</li><li>base weight-shard hashes;</li><li>a `pairing` check.</li></ul> |
| `t4_smoke/phase2_eval.py` | <ul><li>`evaluate`: DEV or FINAL_TEST through the engine, for the unchanged model or one unmerged adapter, with engine seed 11. For the unchanged-model DEV run it writes the ceiling flag (≥ 38/40).</li><li>`gate`: the §11 FINAL_TEST gate.</li><li>`freeze-manifest`: builds the ```json block for `phase2/ADAPTERS_FROZEN.md` from the 9 `final_adapter.json` files.</li></ul> |
| `test1_pilot/hinglish_pilot/{engine,data,hf_backend,report}.py` | Backward-compatible additions: <ul><li>modes `phase2_dev` and `phase2_final_test`, which take the frozen files unchanged, with split roles DEV/FINAL_TEST and fixed counts 40/100;</li><li>a config field `adapter` (arm, seed, attempt, both SHA-256s), present only in the Phase-2 modes and therefore part of `config_sha256`, the resume identity;</li><li>`HFBackend(config, adapter_path=None)`, which verifies both hashes, requires peft 0.15.2 and loads the adapter with `PeftModel.from_pretrained`, unmerged;</li><li>backend metadata records the adapter and the base weight-shard hashes (Phase-2 modes only);</li><li>the engine refuses a backend whose loaded adapter differs from the config.</li></ul> |
| `test1_pilot/frozen_engine/v1/` | Byte-identical snapshot of the pre-Phase-2 engine, with `SHA256SUMS`. |
| `test1_pilot/build_notebook.py` | Now embeds the `frozen_engine/v1/` snapshot (see Design notes). |
| `colab_notebooks/build_phase2_notebooks.py` | Builds `colab_notebooks/phase2/Phase2_Baseline_DEV.ipynb` and `Phase2_Train.ipynb`. The FinalTest notebook is built only once the pre-registration matches `PREREGISTRATION_SHA256` and `phase2/ADAPTERS_FROZEN.md` exists. |
| `colab_notebooks/build_pilot_b_notebooks.py`, `build_pilot_original_notebooks.py`, `secondary_analysis/build_format_notebook.py` | Embed an explicit list of the four v1 secondary modules instead of a glob. |
| Tests | `t4_smoke/test_train_phase2.py` (18), `t4_smoke/test_phase2_eval.py` (19), `t4_smoke/test_phase2_notebooks.py` (11), `test1_pilot/tests/test_phase2_compat.py` (7). |
| Docs | Phase-2 sections in `colab_notebooks/README.md` and `t4_smoke/README.md`. |

## Design notes

**1. Freezing the old notebooks.**
- The existing builders embedded `hinglish_pilot/*.py` and `secondary_analysis/*.py` live from disk. Any engine edit would therefore have made the Pilot-B, original-pilot and format notebooks stale.
- They now embed the frozen v1 engine and a fixed list of the v1 secondary modules.
- All existing notebooks are byte-identical (`git diff` shows no `.ipynb` change).
- During this work the separate agent's new `secondary_analysis/numeric_literal_v2.py` and `rescore_pilot_b_v2.py` had broken 13 currency tests through those globs. The fixed list repairs that. That agent's files were not touched.

**2. Backward compatibility.** `test_phase2_compat.py` checks the following:
- the v1 modes run identically on the live engine and on the snapshot (same manifest, predictions and summary);
- `default_config` is identical in every v1 mode and model;
- v1 modes reject an `adapter` field;
- `adapter_path` defaults to `None` and is checked before any GPU import.

**3. Disconnects (§10).**
- Re-running the Train notebook after a failure creates a new `attempt-NN` folder and trains from scratch.
- A third attempt is refused, with the instruction to switch to reserve seed 44, then 55, for all three arms.
- `RESUME_AFTER_DISCONNECT = True` uses the checkpoint, and the reload is checked exactly. It records `resumes` in `train_report.json` and `resumed: true` in `final_adapter.json`, and the FinalTest gate then refuses that adapter.

**4. FinalTest gate.** The notebook refuses to run unless all of the following hold:
- the embedded PREREGISTRATION.md hash equals the recorded constant;
- the embedded freeze manifest is intact;
- for every one of the 9 frozen adapters on Drive, `final_adapter.json` is present and records COMPLETE, 60 updates, not resumed, the same recipe, the same TRAIN data and the same base revision;
- the files on disk match the manifest hashes;
- within each seed, the arms share the initial adapter and the order hash.

The evaluation cell also asserts `GATE_PASSED`.

**5. Data separation.**
- Training reads only the embedded TRAIN data file; a test spies on file reads.
- The Baseline and Train payloads contain no FINAL_TEST bytes.
- The split manifests use identity triples only.

**6. Phase-2 notebooks embed only the four v1 secondary modules.** numeric_literal_v1 runs in the notebook. numeric_literal_v2 and the pre-registered analysis run offline on the exported results (`phase2_analysis/`, owned by the other agent).

## FinalTest notebook not built yet

`phase2/ADAPTERS_FROZEN.md` does not exist, so the builder skips `Phase2_FinalTest.ipynb` and prints why. The pre-registration hash already matches the recorded constant.

After the 9 runs:
1. Write `ADAPTERS_FROZEN.md`. The `freeze-manifest` command produces its ```json block; the §11 shard and log hashes are added as prose.
2. Commit it.
3. Run `python3 -B colab_notebooks/build_phase2_notebooks.py`.

The gate path is tested with a fixture manifest: the cells run in a subprocess and both refusals and a pass are checked.

## Tests (all pass)

| Suite | Result |
|---|---|
| `python3 -B -m unittest discover -s t4_smoke -p 'test_*.py'` | Ran 103, OK (55 before) |
| `PYTHONPATH=test1_pilot python3 -B -m unittest discover -s test1_pilot/tests -p 'test_*.py'` | Ran 30, OK (23 before) |
| `python3 -B -m unittest discover -s secondary_analysis/tests -p 'test_*.py'` | Ran 73, OK (includes the other agent's v2 tests) |

The `--check` runs of `build_phase2_notebooks.py` and `build_training_smoke_notebook.py` both report their notebooks current.

The required tests are covered:
- the schedule at updates 1, 6, 7 and 60, plus monotonicity;
- the order rule recomputed independently, and pairing across arms (IDs, forms, targets position by position, order hash);
- the run-seeded LoRA initialisation (seed passed through, restored after a failure);
- data hashes and tampering;
- no DEV or FINAL_TEST access by training;
- adapter-path backward compatibility;
- the notebooks compile and are current;
- the FinalTest gate refuses when adapters or hashes are missing or wrong, when a run was resumed or incomplete, and when the pre-registration hash differs.

## Still unverified (GPU only)

- **Not run on a GPU.** Nothing in `train_phase2.py` or the adapter path has run on a GPU: the `seed_everything` swap around `train_smoke.load_model`, the generalised save/restore, and `save_final_adapter`'s key mapping (`.default.` removed, as PEFT 0.15.2 does in `get_peft_model_state_dict`).
- **Timing and Drive I/O.** Expect about 21 min for 60 updates (D042 rate), plus the Drive write of five checkpoints of about 400 MB each, plus the base-shard hashing (about 8 GB, roughly 30 s) in training and in every evaluation load. The atomic directory rename on the Drive mount is also untested.
- **Loading the adapter for evaluation.** Not yet run: `PeftModel.from_pretrained` on the NF4 base under transformers 4.51.3 and PEFT 0.15.2, unmerged, with fp32 adapter weights (`autocast_adapter_dtype`), and generation latency with the adapter.
- **Train/eval numerics mismatch.** Training uses `prepare_model_for_kbit_training`, which upcasts the norms and the tied embedding/lm_head to fp32, under fp16 autocast. Evaluation uses the frozen engine's fp16 base. This is standard QLoRA practice and is not a recipe change, but numerics differ slightly between training and evaluation.
- **Colab stack.** Whether Colab still ships torch 2.11.0+cu130. `ALLOW_STACK_MISMATCH` records a mismatch but does not stop the run.

**Recommendation:** run `Phase2_Baseline_DEV` first (inference only), then one `Phase2_Train` run (for example EC, seed 11), and check its ZIP before the other 8.
