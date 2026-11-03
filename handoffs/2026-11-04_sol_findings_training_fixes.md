# Sol review: training- and evaluation-side fixes (4 Nov 2026)

**Author:** a Claude Opus subagent, working under D017.

**What this is:** the fixes for findings R3, R4 (trainer side), R5, R6, R7 and R8 from `handoffs/2026-11-03_sol_review_phase2.md`. They follow `phase2/PREREGISTRATION.md` Amendment 2, items 2–7 (commit 17986d4).

**Not touched:**
- `phase2_analysis/` and `research/` (another agent owns them);
- any data, frozen file or `train_smoke.py`;
- every pre-Phase-2 notebook. They are byte-identical: `git status` shows only the two Phase-2 `.ipynb` files.

**No commits were made.**

## Status by finding

| Finding | Status | What changed |
|---|---|---|
| **R3** failure classes | FIXED | <ul><li>`classify_failure` no longer uses the stage. **Infrastructure** comes only from the typed list (`INFRASTRUCTURE_KINDS`): runtime disconnect or kill, CUDA OOM, a Drive or filesystem `OSError`, a network or Hub download error, and a failed checkpoint write (`CheckpointWriteError`).</li><li>Every `ProtocolError`, and every other exception (`TypeError`, a plain `AssertionError`, an unlisted CUDA error), is **protocol** and halts the study.</li><li>`ProtocolError(ValueError)` is now raised at every hash, identity, label or data assertion. This includes all `restore_checkpoint` identity and digest checks, the saved-adapter equality checks, and the reused smoke-code checks (wrapped with `protocol_assertions`).</li><li>An `OSError` at the data stage is infrastructure.</li><li>If the report contains an unknown `failure_class`, `attempt_outcome` returns protocol, never infrastructure.</li></ul> |
| **R4** trainer entry point and freeze | FIXED (trainer side) | <ul><li>`train` now takes `--train-root --inputs --baseline-dir`. Before anything else it reconciles open attempts and reads the plan. It refuses any run the plan does not authorise. `--arm/--seed/--slot/--attempt` are optional and only assert the plan's choice.</li><li>It refuses an identity (manifest, trainer code, TRAIN and exposure files, recipe, model, stack, baseline ZIP) that differs from earlier attempts.</li><li>It logs `start` and `finish` itself, so the notebook no longer writes to the log.</li><li>Inside the attempt, `verify_implementation` checks `IMPLEMENTATION_MANIFEST.md` against the trainer's own source files, the frozen TRAIN and exposure hashes, the recipe, GradScaler, model and exact stack.</li><li>`load_verified_train` builds the families from the raw TRAIN bytes, checked against `TRAIN_FILES` and the new frozen `TRAIN_FAMILIES_SHA256`. The built `phase2_train.json` is gone from the payload.</li><li>`verify_exposure` checks the file against the new frozen `EXPOSURE_ORDER_SHA256` (`adf43e50…afb6`) and the recomputed per-seed list.</li><li>`plan()` rejects a log whose start events have no identity or differing identities.</li><li>`freeze_manifest` rechecks the manifest against the real files under the repo root and against every start event, then requires the retained records to match.</li></ul> |
| **R5** stack | FIXED | <ul><li>`ALLOW_STACK_MISMATCH` and `--allow-stack-mismatch` are removed everywhere.</li><li>`check_stack()` refuses a mismatch or a non-T4 GPU (name and capability 7.5) before the attempt opens. Nothing is logged.</li><li>`HFBackend.PINS` now includes `torch: 2.11.0+cu130`. HFBackend also requires a T4.</li><li>The shared GPU cell asserts `not STACK_MISMATCHES`, so Baseline, Train and FinalTest all refuse.</li></ul> |
| **R6** run order | FIXED | <ul><li>The Train notebook has no ARM, SEED or SLOT setting. `next_run(plan)` gives the next pending run: slots 11 → 22 → 33, arms EC → ER → EE within a slot. A slot is settled (complete, or exhausted after its reserves) before the next one starts.</li><li>Reserves are allocated from [44, 55] in slot order.</li><li>`plan()` replays the log and rejects any start that is not the run authorised at that point.</li><li>`next_action` is removed. The test `test_reserve_already_trained_for_a_later_slot_is_kept` is replaced by `test_reserves_are_taken_in_slot_order` and `test_sol_r6_sequence_is_refused`.</li></ul> |
| **R7** stale lock | FIXED | <ul><li>`RECOVER_STALE_LOCK = False` is in Baseline, FinalTest and Train (Train because of its DEV sanity evaluation).</li><li>When it is True, `evaluate --recover-stale-lock` calls the engine's `recover_lock(confirmed_no_active_writer=True)`. It appends a timestamped record (lock time, number of kept journal records and their hash) to `<run>_lock_recoveries.jsonl`, then resumes from the journal. Stored outputs are never regenerated.</li><li>Without the flag the engine still refuses.</li><li>The engine itself is unchanged.</li></ul> |
| **R8** baseline first | FIXED | <ul><li>`evaluate --implementation-manifest M` binds the manifest SHA at the run's first session. A later session under another manifest, or a run started unbound, is refused.</li><li>A complete unchanged DEV run writes `base_baseline_record.json` once, with the results-ZIP and manifest SHA-256s. That ZIP is never re-exported.</li><li>`verify_baseline` (trainer preflight) refuses every attempt without a complete 120/120 unchanged-model DEV run under the same manifest, with a matching ZIP.</li><li>The ZIP hash goes into every start event's identity, every `final_adapter.json`, and `ADAPTERS_FROZEN.md` (`baseline_dev_results_zip_sha256`, schema `phase2-adapters-frozen-3`).</li><li>The gate requires it: every start event must carry it, every retained record must match it, and with `--baseline-dir` the ZIP on Drive must match. The FINAL_TEST driver now requires `--baseline-dir`.</li></ul> |

## Rebuild and hashes

- The pre-registration SHA-256 is now `b2e6df8f552dfe5756cfde9308880f06de0685d7d1d40de57c5e71cc41260396`, computed from the committed file with Amendment 2 (identical to HEAD).
  - It is set in `build_phase2_notebooks.PREREGISTRATION_SHA256` and `phase2_eval.PREREGISTRATION_SHA256`.
  - A test checks both against the file.
  - The `37ef68bf…` and `74be2328…` values are asserted absent from the notebooks.
- `python3 -B phase2/build_implementation_manifest.py` produced manifest `414b67eb43db3d7bffd052452634e772e592d1de8e6741e65a73384700db5787`. It is uncommitted.
  - The manifest now records Amendments 1 and 2, `torch_build`, the stack policy, the failure classes, the run order, the baseline-first rule and `TRAIN_FAMILIES_SHA256`.
- `python3 -B colab_notebooks/build_phase2_notebooks.py` rebuilt Baseline and Train. FinalTest is skipped because `ADAPTERS_FROZEN.md` does not exist.
- All `--check` commands report current: both builders, `train_phase2.py exposure-order` and the training-smoke builder. `git diff --check` is clean.
- **The manifest hashes `phase2_analysis/*.py`.** If the other agent changes those files after this, rebuild the manifest and then the notebooks. The notebook tests will report "stale" until you do.

## Tests

| Suite | Result |
|---|---|
| `t4_smoke` | 172 OK (150 before) |
| `test1_pilot/tests` | 32 OK (31 before) |
| `secondary_analysis/tests` | 81 OK |
| `phase2_analysis/tests` | 73 OK (the other agent's suite; 42 before) |

No test reads FINAL_TEST contents. The FinalTest gate tests still swap in DEV bytes, and the freeze recheck hashes only manifest-listed files, which do not include FINAL_TEST.

New regression tests, by finding:
- **R3:** `FailureClassTests.*`, which includes Sol's three probes: `TypeError` → protocol, Drive `OSError` at data → infrastructure, hash assertion at reload → protocol. Also `TrainerEntryTests.test_drive_error_at_the_data_stage_is_infrastructure`, `test_programming_error_halts_the_study` and `test_cuda_oom_and_checkpoint_write_failure_are_infrastructure`.
- **R4:**
  - `AuthenticatedInputTests.*`, including Sol's probe of a changed completion with a recomputed hash;
  - `TrainerEntryTests.test_manifest_train_and_exposure_are_verified_inside_the_attempt`, `test_changed_configuration_or_implementation_is_refused` and `test_valid_run_logs_start_and_finish_with_the_identity`;
  - `AttemptLogTests.test_attempts_must_share_one_identity`;
  - `GateTests.test_freeze_rechecks_the_manifest_against_the_real_files_and_the_start_events`, which includes Sol's `eee…` probe.
- **R5:**
  - `TrainerEntryTests.test_stack_mismatch_or_non_t4_refuses_before_the_attempt_opens`;
  - `BuiltNotebookTests.test_gpu_cell_refuses_a_stack_mismatch` and `test_notebooks_check_t4_use_drive_and_zip_with_checksums`, which check that no override exists;
  - `test_phase2_compat.test_hf_backend_requires_the_pinned_torch_and_a_t4`.
- **R6:**
  - `AttemptLogTests.test_next_run_follows_the_registered_order`, `test_a_slot_is_fully_settled_before_the_next_starts`, `test_reserves_are_taken_in_slot_order` and `test_sol_r6_sequence_is_refused`;
  - `TrainerEntryTests.test_operator_cannot_choose_the_run`;
  - `BuiltNotebookTests.test_train_notebook_has_no_run_choice_and_follows_the_plan`;
  - `TrainNotebookFlowTests.*`, which runs the control cell in a subprocess.
- **R7:**
  - `BaselineRecordAndLockTests.test_stale_lock_is_recovered_only_when_requested_and_nothing_is_regenerated`, which uses a real engine journal and checks that stored records are byte-identical;
  - `test_engine_recover_lock_still_requires_confirmation`;
  - `BuiltNotebookTests.test_eval_notebooks_offer_logged_stale_lock_recovery`.
- **R8:**
  - `BaselineRecordAndLockTests.test_complete_baseline_is_recorded_once_and_accepted_by_the_trainer` and `test_no_baseline_record_without_a_manifest_or_for_an_incomplete_run`;
  - `TrainerEntryTests.test_no_baseline_or_a_baseline_under_another_manifest_refuses_before_any_attempt`;
  - `GateTests.test_freeze_records_the_baseline_and_the_gate_requires_it`;
  - `FinalTestGateNotebookTests.test_refuses_without_the_frozen_unchanged_dev_baseline`.

## Interpretations and deviations

1. **What counts as each typed infrastructure kind:**

   | Kind | What it covers |
   |---|---|
   | Disconnect or kill | `KeyboardInterrupt` or `SystemExit`. A killed process leaves its attempt open; `reconcile` later closes it as infrastructure. |
   | CUDA OOM | The `torch` `OutOfMemoryError` class only. A host `MemoryError` and other CUDA `RuntimeError`s are protocol. |
   | Network or Hub error | Any `OSError` (Hub HTTP errors subclass it) and exceptions from `requests`, `urllib3`, `httpx`, `http.client`, `socket` and `ssl`. |
   | Failed checkpoint write | Inside the write operations only: an `OSError`, a `SafetensorError` or a `torch.save` stream-writer `RuntimeError`. |

   A missing input file is an `OSError`, so it counts as infrastructure under the list.
2. **Preflight refusals open no attempt and log nothing.** These cover the plan, the baseline, identity consistency, the stack and T4 checks, and existing attempt evidence.
   - An `OSError` during preflight exits 1 with nothing logged.
   - A corrupt attempt log exits 4. Nothing can be logged in that case.
   - Hash and identity checks that must halt the study run inside the opened attempt, so they are logged as protocol failures.
3. **The baseline is required for every attempt, not only the first.** It is part of the identity, which must not change between attempts. The first attempt therefore cannot happen without it.
4. **The live engine's `HFBackend` requires a T4 and the torch pin in every mode.** Only the Phase-2 notebooks embed the live engine; v1 notebooks use `frozen_engine/v1`.
5. **The freeze recheck verifies every manifest-listed file under the repo root.** It does not re-derive the non-file entries (notebook payload hashes, Hub hashes). `build_implementation_manifest.py --check` remains the full currency check.
6. **Documentation outside the listed scope.** `colab_notebooks/README.md`'s Phase-2 operator section still told the operator to set `ARM`/`SLOT`, so I rewrote it to describe the new flow. It is a doc-only edit.
7. **Engineering resume is kept.** It is restricted to the infrastructure-failed attempt of the plan's pending run and is still never valid.

## Still unverified (GPU only)

Nothing ran on a GPU. These three behaviours have only been checked on CPU:
- the real `check_stack` and `gpu_setup` on Colab;
- the typed classification of real CUDA, Hub and Drive exceptions (CPU tests used class-shaped fakes);
- `CheckpointWriteError` on a real safetensors or `torch.save` failure.

## Before the first DEV generation

1. Wait for the `phase2_analysis/` work to land.
2. Rebuild the manifest, then the notebooks.
3. Run both `--check`s.
4. Commit and push `EXPOSURE_ORDER.json`, `IMPLEMENTATION_MANIFEST.md`, the rebuilt notebooks and this code.
5. Run `Phase2_Baseline_DEV` before any training. The trainer now enforces this.
