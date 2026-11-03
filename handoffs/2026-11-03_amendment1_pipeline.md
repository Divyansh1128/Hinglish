# Phase-2 pipeline aligned with Amendment 1 (3 Nov 2026)

**Author:** a Claude Opus subagent, working under D017.

**What this is:** the training and evaluation pipeline from commit 60bcd99 (`handoffs/2026-11-03_phase2_pipeline.md`), changed to follow Amendment 1 of `phase2/PREREGISTRATION.md` (commit b4fb956, D045). The current pre-registration SHA-256 is `37ef68bf…9ada`, which replaces `74be2328…2840`.

**Items covered:** 7, 9, 10, 11, 12, 13, 14 and 15. The other items belong to `phase2_analysis/` and `secondary_analysis/` (another agent).

**Not changed:**
- `phase2_analysis/` and `secondary_analysis/`;
- any data or frozen file;
- every Pilot-B, original-pilot, format and smoke notebook. They are byte-identical, and `git status` shows only the two Phase-2 `.ipynb` files.

**No commits were made.**

## Before the first DEV generation

1. Wait for the other agent's analysis changes to land.
2. Run `python3 -B phase2/build_implementation_manifest.py`, then `python3 -B colab_notebooks/build_phase2_notebooks.py`. The notebooks embed the manifest, so they have to be rebuilt after it.
3. Check both with `--check`.
4. Commit `phase2/EXPOSURE_ORDER.json`, `phase2/IMPLEMENTATION_MANIFEST.md` and the rebuilt notebooks. Then push.

**Current state:**
- The manifest in the working tree (`16efb5a2…`) hashes the analysis files **as they are now**. It is not committed, as instructed.
- Until it is regenerated, the notebook tests catch any change to a hashed file: they fail with "stale".

## Files

| File | Change |
|---|---|
| `t4_smoke/train_phase2.py` | <ul><li>**Item 9.** `order_input` takes the exact UTF-8 bytes with decimal s and p and rejects non-int values. Hash ties are broken by family ID. New commands `exposure-order` (write) and `--check`. Training requires `--exposure-order` and checks this seed's list against the recomputed order; a mismatch is a protocol failure.</li><li>**Item 10.** `Phase2Trainer` (subclass; `train_smoke.py` is untouched) works as follows:<ul><li>GradScaler pinned to 65536 / 2.0 / 0.5 / 2000.</li><li>lr(u) is set inside `update` before the step, and gradients are unscaled before clipping.</li><li>Any non-finite loss (checked before backward), non-finite gradient norm (checked before the step) or scale change after the step raises `NumericalFailure`.</li><li>There is no cursor wrap, and no update is replayed or skipped.</li><li>Steps are counted (attempted vs successful), and cursors are logged for each update.</li><li>Non-finite parameters are checked at checkpoints and in the saved final adapter.</li><li>A valid run must end with windows/attempted/successful = 60/60/60 and cursor 960, or it is a protocol failure.</li></ul></li><li>**Item 11.** Two parts:<ul><li>`classify_failure` assigns infrastructure, numerical or protocol by exception type and stage. The run report records `failure_class`, `failure_stage` and `study_halt`. Exit codes: 1 infrastructure, 3 numerical, 4 protocol.</li><li>`ATTEMPT_LOG.jsonl` is append-only and hash-chained (an edited, reordered or deleted line is refused). `plan()` applies the retry, reserve and halt rules; `next_action()`, `reconcile()` and `describe_plan()` work on top of it. `--slot` is recorded. Attempt 3 is refused.</li></ul></li></ul> |
| `t4_smoke/phase2_eval.py` | <ul><li>**Item 7.** `ceiling_flag` gives the proxy name, k/n, Wilson 95% (from the engine's `wilson`) and the DEV headroom. `ceiling_line` prints it.</li><li>**Item 12.** Freeze schema `phase2-adapters-frozen-2` records `retained_seeds`, `S`, `confirmatory`/`descriptive_only`, and the hashes of the attempt log, the implementation manifest and the exposure file. S = 1–2 must carry `descriptive_only: true`; S = 0 is refused. `freeze_manifest(train_root)` is built from the attempt log. It refuses while the study is halted or any slot is open.</li><li>**Gate.** It checks, for each adapter:<ul><li>a valid run (60/60 steps, finite, not resumed);</li><li>the implementation manifest, the exposure file and the base shards;</li><li>the attempt log is unchanged since the freeze and still gives the frozen retained seeds.</li></ul></li><li>**Items 13–14.** `evaluate` is always sealed for `final_test` (and with `--sealed`): stdout shows only `<run>: k/N generated` and a status JSON (completion, unresolved, attempts, infrastructure failures, ZIP and checksum SHA-256s). `summary.md` is not printed and the ceiling flag is not written.</li><li>**Item 15.** `config_for` allows Qwen3-4B only.</li></ul> |
| `test1_pilot/hinglish_pilot/engine.py` | **Item 15.** The Phase-2 modes refuse any model other than `Qwen/Qwen3-4B`. The v1 modes are unchanged; the frozen v1 snapshot is untouched. The engine already never retries a generated response; a test now covers this. |
| `phase2/build_implementation_manifest.py` (new) | **Item 14.** Writes `phase2/IMPLEMENTATION_MANIFEST.md`; `--check` reports it missing or stale and lists the changed files. Details below. |
| `phase2/EXPOSURE_ORDER.json` (new, SHA-256 `adf43e50…afb6`) | Item 9. Exposure lists for seeds 11/22/33 and reserves 44/55, three passes of 160 family IDs each. Each seed has `order_sha256` (equal to the run's `order_sha256`). It is tied to the TRAIN `families_sha256`. |
| `colab_notebooks/build_phase2_notebooks.py` | <ul><li>`PREREGISTRATION_SHA256` is now the current hash.</li><li>Every notebook embeds the manifest text and its SHA-256. The setup cell refuses to run if the manifest text, the notebook payload digest or any embedded code/data file (`payload_sources`) differs.</li><li>The GPU cell re-downloads the pinned Hub files and checks them against the manifest. It also exposes `STACK_MISMATCHES`.</li><li>The Train notebook uses `SLOT`, not `SEED`; the attempt-log flow is described below.</li><li>The FinalTest notebook is sealed, gates on S with a confirmatory or descriptive-only mode, and checks that the adapters were frozen under the embedded manifest.</li><li>No Llama text and no model option.</li></ul> |
| `colab_notebooks/phase2/*.ipynb` | Rebuilt. |
| `colab_notebooks/README.md` | Phase-2 section rewritten for SLOT, the attempt log, the manifest, freeze S and sealing. This is a doc-only edit outside the listed scope; the old text told the operator to switch reserves by hand. |
| Tests | `t4_smoke/test_train_phase2.py`, `test_phase2_eval.py` and `test_phase2_notebooks.py` were extended or rewritten. `test1_pilot/tests/test_phase2_compat.py` has one new test. |

### The implementation manifest

It hashes the following files by path:
- the trainer (`train_phase2.py`, `train_smoke.py`);
- the label builder, the prompt module and the eval driver;
- all engine files and scorer v1;
- `numeric_endpoint.py` (v1) and `numeric_literal_v2.py`;
- the secondary report modules;
- `phase2_analysis/*.py` plus its dependency `paper_analysis/safezip.py`;
- both builders, `EXPOSURE_ORDER.json`, and the TRAIN and DEV data.

It also records:
- the payload SHA-256s of the Baseline and Train notebooks;
- the prompt version and instruction hash;
- the model ID and revision, with SHA-256s of 7 Hub files (`config.json`, `generation_config.json`, the tokenizer files, the weight index) and the chat-template digest;
- the engine config digests and decoding settings;
- EOS and stopping (ids 151645/151643, 1,024-token cap, truncation rule);
- train and evaluation dtype preparation;
- the GradScaler settings and recipe hash;
- the pinned dependencies.

It refuses to write if scorer v1 or numeric v1 differs from its pre-registered hash, if the data hashes differ, if the prompt texts differ, or if `EXPOSURE_ORDER.json` is stale.

### The Train-notebook attempt flow

1. Close any open attempts from their own reports (`reconcile`).
2. Print the plan.
3. `next_action` decides whether to train, to stop because the arm is done, or to refuse (study halted, or slot exhausted).
4. Check the stack before any attempt is opened.
5. Log `start`, train, classify the result, log `finish`.
6. On a numerical or protocol failure, print a banner: "THE STUDY HALTS … no retry, no reserve".

An existing attempt folder is never reused. The Download cell also works after a refusal: it adds a snapshot of the attempt log.

## Interpretations (items not implemented literally)

1. **Reserve order (item 11).** A reserve that already has a logged attempt stays with its slot. Unlogged reserves go to retired slots in slot order 11, 22, 33. Example: if 22 retires first and gets 44 but nothing has been trained on 44 yet, and 11 then retires, 11 gets 44 and 22 gets 55. A seed is retired as soon as any of its arms has two failed attempts without a valid one. Starting an arm on a retired seed is a protocol error in the log.
2. **Failure classes.** Infrastructure covers:
   - errors in setup (no T4, stack mismatch), tokenizer download, checkpoint, reload and final save;
   - OOM and CUDA errors during training;
   - an attempt left open by a disconnect or a Ctrl-C.

   A plain assertion in the data, label, model-load or training stage is a protocol failure, because those are deterministic. So is a step-count mismatch. A stack mismatch is caught in the notebook **before** an attempt is opened, so it does not use up an attempt.
3. **Resume.** It is kept as an engineering-only option (`--resume` / `RESUME_AFTER_DISCONNECT`). It is logged as `resume_start`/`resume_finish`, can never make an arm valid, and the gate refuses it. The attempt still counts as failed.
4. **Notebook hashing (item 14).** The manifest hashes the notebook **payloads** and the builder, not the `.ipynb` files, because each `.ipynb` embeds the manifest (that would be a cycle). The FinalTest notebook is built after the freeze, so the manifest cannot contain its payload. Instead it checks every code member against the manifest and requires `ADAPTERS_FROZEN.md` to record the same manifest SHA-256.
5. **Tokenizer, config and chat template.** These are pinned by revision, with constant SHA-256s measured from the Hub at `1cfa9a72…` today. The four tokenizer files match the local Hub cache, and the builder rechecks them whenever the cache exists. They are verified byte-for-byte on Colab before any run. The trainer still only *records* the chat-template digest; it does not assert it. The check on `tokenizer_config.json` bytes covers it.
6. **Sealing (items 13–14).** Sealed output allows a count every 25 generations. Rendering IDs and latencies are not printed. The tests check that the sealed stdout contains no "accuracy", "correct", "FINAL:", "%", rendering IDs or summaries.

## Tests (all pass)

| Suite | Result |
|---|---|
| `python3 -B -m unittest discover -s t4_smoke -p 'test_*.py'` | Ran 145, OK (103 before) |
| `PYTHONPATH=test1_pilot python3 -B -m unittest discover -s test1_pilot/tests -p 'test_*.py'` | Ran 31, OK (30 before) |
| `python3 -B -m unittest discover -s secondary_analysis/tests -p 'test_*.py'` | Ran 81, OK (73 before; the increase is the other agent's) |

These `--check` runs report current: `build_implementation_manifest.py`, `build_phase2_notebooks.py`, `build_training_smoke_notebook.py` and `train_phase2.py exposure-order`.

Coverage by item, all without a GPU:

- **Item 9:**
  - exact bytes, decimal and type rejection;
  - tie-break;
  - the committed file is current, and every pass is recomputed independently;
  - the run refuses a tampered or missing list.
- **Item 10** (fake torch):
  - GradScaler kwargs;
  - 60/60 steps, cursor 960, and no 61st window;
  - lr(u) is seen at step u;
  - each window runs backward×16, then unscale, clip, step;
  - a skip, NaN/inf loss or NaN/inf gradient raises NumericalFailure with nothing replayed;
  - non-finite tensors are detected.
- **Item 11:**
  - the classification matrix and outcomes from folders;
  - `run_train` end to end with mocks: valid, numerical (exit 3, "THE STUDY HALTS"), step mismatch (protocol), tampered exposure (protocol);
  - log chain tampering;
  - retry then reserve, slot-order assignment, a reserve kept for a later slot, exhaustion, halt without reserve, resume never valid, reconcile;
  - the Train notebook's control cell run in a subprocess with a stub training step (retry → reserve 44 → numerical → refuses everything).
- **Item 12:**
  - freeze S = 3, S = 2 (descriptive-only, gate returns 6), a reserve replacing a slot;
  - S = 0, open slot or halted study is refused;
  - a missing or contradictory `descriptive_only` is refused;
  - the FinalTest gate cell, run in a subprocess, passes in CONFIRMATORY or DESCRIPTIVE-ONLY mode.
- **Items 13–14:**
  - a sealed `final_test` run prints nothing that leaks (DEV bytes under the FINAL_TEST name, so no FINAL_TEST content is read), and a rerun regenerates nothing;
  - the engine never retries a generated response;
  - setup cells, run in a subprocess, refuse a tampered file hash, a tampered payload digest or a mismatched manifest SHA;
  - the manifest covers every listed component, and `--check` detects stale or missing;
  - FinalTest embeds the current pre-registration hash and refuses 74be… or other values, and refuses adapters frozen under another manifest.
- **Item 15:** the engine refuses non-Qwen models in Phase-2 modes for every registered model, and no Phase-2 notebook mentions Llama.
- **Item 7:** k/40 and Wilson interval values, the printed line, and the Baseline cell run against a flag file.

## Still unverified (GPU only)

Nothing new has run on a GPU. Three things are untested there:
- the `Phase2Trainer.update` path on real tensors (`float(loss.detach())` sync, scaler state after a skip);
- the Hub-file download check on Colab;
- the non-finite check on the safetensors load.

The earlier handoff's GPU caveats still apply. The recommendation is unchanged: run the Baseline first, then one Train run, and check the ZIP.
