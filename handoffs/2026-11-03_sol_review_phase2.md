# Sol independent Phase-2 review — 3 November 2026

**Verdict: NO, the pipeline is not ready to freeze.** Five groups of clear bugs were repaired with regression coverage. The remaining findings below need resolution before the implementation manifest is committed and used for the first DEV generation. Passing the suites does not close those findings.

Reviewed the scope in `handoffs/2026-11-03_claude_to_sol.md` against `phase2/PREREGISTRATION.md`, including Amendment 1, and `research/astra_prereg_review_2026-11-03.md`. The working checkout reports HEAD `ba67b03`; the handoff identifies `535b1e9` as its reference. No commits were made. No pre-registration, dataset, recipe, schedule, scorer-v1 file, numeric-v1 file, or threshold was changed. `train_smoke.py` was left unchanged. No real training or evaluation-backbone inference was run; this machine has no installed CUDA training stack.

## Access incident discovered in the existing tests

**P1 — fixed prospectively; historical exposure must still be recorded.** The initial required `t4_smoke` suite passed 145 tests, but subsequent inspection showed that `InputTests.test_final_test_mode_validates_structure` decoded the actual FINAL_TEST JSON and passed it to semantic validation/scoring. `FinalTestGateNotebookTests` also repeatedly embedded the actual test bytes in synthetic gate notebooks. That suite was run before I noticed these paths. No test problem, gold answer, or rendering was displayed to or inspected by me, and no evaluation backbone generated an answer. Nevertheless, the automated parsing was beyond an isolated byte-hash check and contradicts Amendment 1 item 13; the review must not claim that only hashes were accessed throughout.

The structure test now constructs 100 synthetic families from DEV, with distinct fixture identities and rendering texts. The notebook gate tests substitute DEV bytes before the builder can read the real test file. The existing isolated SHA-256 assertion remains. These replacements pass the full suite. Record the incident in the access history and determine the registration consequence before proceeding; changing the tests does not erase the exposure.

## Remaining findings

### R1 — P1 — Analysis does not bind checkpoint labels or retained seeds to the freeze — NOT FIXED

**Evidence:** `phase2_analysis/analyze.py:265` accepts a caller-created mapping from `(arm, seed)` to a run. It checks distinct paths/run IDs, common snapshots, and some config fields, but never compares each mapping key with `config['adapter']`, its two hashes, or `ADAPTERS_FROZEN.md`. It has no frozen-manifest argument. `analyze()` decides confirmatory status solely from `S == 3`.

I generated ten synthetic engine runs on DEV, swapped only the EC:11 and ER:11 input paths, and `assemble()` accepted all ten. The loader also accepts the existing fixtures, which have **no loaded adapters at all**, under trained-arm labels. A second probe supplied DEV families through a mocked FINAL_TEST dataset loader (no test file access); the same swapped input mapping was accepted without a retained-seed manifest. Thus an arm swap can reverse the primary contrast, and omitting/substituting a frozen seed can silently become a reduced-S or different confirmatory analysis.

**Required:** for real FINAL_TEST, bind every run to the frozen checkpoint identity, adapter/config hashes, exact retained seed set, unchanged-model entry, implementation, and prescribed execution settings. Denominators must come from the freeze, rather than whichever runs the operator supplies. Keep the DEV fixture facility explicitly separate. This is an input-integrity defect, not a defect in the 1/S arithmetic.

### R2 — P1 — Analysis permits the excluded backbone and incompletely validates execution — NOT FIXED

**Evidence:** `check_config()` at `phase2_analysis/analyze.py:256` checks the Qwen revision only **if** the supplied model ID is Qwen. I called it with a Llama-3.2-3B config and revision `000…000` under role FINAL_TEST; it returned successfully. `assemble()` merely adds the old “secondary backbone, section 5” warning, then `analyze()` can issue an S=3 confirmatory label. Amendment 1 item 15 excludes that backbone.

The instruction string is only required to agree across runs, rather than equal the frozen instruction. The analysis checks the scorer source hash, but does not bind the remaining engine source/backend/environment to the implementation manifest. It validates attempt numbering but does not enforce the configured two-attempt budget. These omissions allow non-protocol archives to receive registered labels even though the normal engine is stricter.

**Required:** reject excluded models, wrong modes/instructions, execution/source mismatches and excess attempts in the FINAL_TEST input validator. A warning is insufficient.

### R3 — P1 — Failure classification is broader than documented transient infrastructure — NOT FIXED

**Evidence:** executable probes of `train_phase2.classify_failure()` returned:

| Exception and stage | Actual class | Problem |
|---|---|---|
| `TypeError('bug')`, training | infrastructure | A programming error receives retry/reserve eligibility |
| `OSError('Drive I/O')`, data | protocol | A transient read failure halts instead of receiving the permitted infrastructure retry |
| `AssertionError('hash mismatch')`, reload | infrastructure | A hash assertion does not halt |

The function at `t4_smoke/train_phase2.py:467` treats all otherwise-unrecognized exceptions as infrastructure, and all data/label-stage exceptions as protocol. `restore_checkpoint()` uses ordinary `require()`/ValueError for identity and digest assertions, so the reload case is reachable through real checks. The original handoff explicitly describes these stage-based interpretations, but they do not implement Amendment 1 item 11's exception for **documented transient** failures and its mandatory halt for hash/label assertions.

**Required:** distinguish typed protocol assertions from I/O failures at the point of detection; do not silently grant reserves for unknown deterministic errors. Preserve all attempt evidence. I did not redefine the failure policy during this review.

### R4 — P1 — The trainer and freeze accept asserted manifest identities without checking the actual implementation — NOT FIXED

**Evidence:** `run_train()` at `t4_smoke/train_phase2.py:733` records the optional `--implementation-manifest-sha256` string but neither reads that manifest nor verifies its code/data/Hub entries. It does not consult the attempt log before training. The log's start events record a manifest hash, but `plan()` does not enforce identical implementation/configuration between attempts. `freeze_manifest()` checks that retained records agree with each other, not that their claimed hash matches the current implementation or the start-event identity. Its fixture runs can be frozen with the arbitrary hash `eee…eee`, demonstrating that the function is not itself a manifest recheck.

Similarly, `validate_phase2_data()` checks a self-reported sources dictionary and a self-computed family hash. I changed a TRAIN completion in memory, recomputed `families_sha256`, regenerated an exposure document, and both `validate_phase2_data()` and `check_exposure()` accepted it. The ordinary builder's payload hash protects the unmodified notebook route, but the executable trainer does not authenticate its input against an authoritative frozen value. The notebook builder later checks manifest agreement for FINAL_TEST; that does not satisfy the earlier code freeze or identical-retry requirement.

**Required:** enforce the implementation manifest at the executable training boundary and adapter freeze, tie its authenticated data/exposure identity and actual execution configuration to each attempt, and prevent direct trainer invocation from bypassing the attempt plan. Do not treat shared opaque strings as proof that the same code ran.

### R5 — P1 — The pinned stack can be bypassed while retaining a valid run — NOT FIXED

**Evidence:** the Train notebook exposes `ALLOW_STACK_MISMATCH`, forwards it to `gpu_setup()`, and the trainer sets `valid_for_gate = not resumed` regardless of recorded stack mismatches. The final gate does not reject those mismatches. The shared GPU cell prints `STACK_MISMATCHES`, but Baseline and FinalTest do not assert that it is empty. `HFBackend.PINS` omits torch, and its own device checks require one CUDA GPU without requiring T4; only the notebook cell supplies the T4 assertion.

This conflicts with §2's frozen stack/single-T4 execution and item 11's unchanged configuration across infrastructure retries. Recording a change does not authorize it. The previous handoff's warning that torch is merely “recorded” is therefore an unresolved protocol deviation, not just a GPU caveat.

**Required:** refuse mismatched registered executions before outputs, or use a dated pre-output amendment. Engineering overrides must never produce gate-valid study runs.

### R6 — P1 — Reserve assignment depends on operator order — NOT FIXED; specification interpretation needs resolution

**Evidence:** I logged two infrastructure failures for seed 22, one valid arm on reserve 44 for slot 22, then two infrastructure failures for seed 11. `plan()` assigned `{44: 22, 55: 11}`. The existing `test_reserve_already_trained_for_a_later_slot_is_kept` explicitly codifies this behavior. The handoff calls it an interpretation.

Amendment 1 item 11 says to fill original slots in order `[11, 22, 33]`. The notebook lets the operator process slots in any order and commits a reserve to a later slot before earlier slots are settled. The output can therefore differ from processing the original slots in the registered order. Reassigning an already trained reserve would also violate the no-reuse rule.

**Required:** settle the earlier slots before allocating reserves to later slots, or obtain a pre-output clarification/amendment authorizing the alternative. I did not silently choose a new allocation rule.

### R7 — P1 — Runtime-kill evaluation resume is blocked by a stale lock — NOT FIXED

**Evidence:** `hinglish_pilot.engine.lock()` leaves `RUNNING.lock` on Drive if the runtime/process is killed without running `finally`. The engine correctly requires `recover_lock(..., confirmed_no_active_writer=True)` before reuse. Neither `phase2_eval.run_evaluate()` nor the notebook cells invoke a recovery path. I created a stale lock on a synthetic run and re-entered the real engine; it refused with “Run lock exists … use recover_lock”.

The notebook tells the operator simply to re-run all after a disconnect, so this path repeatedly refuses instead of resuming the stored journal. No outputs need regeneration; the problem is writer ownership and recovery.

**Required:** provide an explicit safe recovery procedure or an orchestration-owned single-writer recovery path. Do not unconditionally unlink a lock that may belong to an active writer.

### R8 — P2 — The required unchanged-DEV-before-training sequence is only prose — NOT FIXED

**Evidence:** the Train notebook starts its attempt flow without verifying a complete unchanged-DEV run or its implementation identity. `freeze_manifest()` also has no baseline prerequisite. The analysis accepts a manually supplied ceiling count without linking it to the actual baseline artifact. §5 requires the baseline before the first training run.

**Required:** make the baseline artifact and order auditable, preferably as a checked prerequisite to the first training attempt. The docs instruct the right order, but the current artifacts cannot establish that it was followed. No baseline was run during this review.

### R9 — P2 — Item 7's versioned DEV planning rerun is not implemented, including the 40/40 boundary — NOT FIXED

**Evidence:** the baseline computes the renamed flag, k/40, Wilson interval and headroom correctly. However, none of the reviewed baseline/eval/analysis paths invokes or emits the adopted planning rerun. The existing `research/phase2_power/phase2_power.py` still rejects `p0 = 1`; I imported it read-only and `mixture(1, 0)` returned `None`. Item 7 adopts the review's requirement that `(p0=1, q0=0, delta=0)` be reported as the admissible degenerate zero-headroom cell, with other cells explicitly infeasible.

**Required:** supply a versioned planning-only rerun using observed k/40 and the original grid, including this boundary. Do not change design, labels or thresholds. The interval-calibration program is a different simulation and does not discharge this requirement.

### R10 — P2 — Calibration's “baseline 0.943” description refers to a latent state — NOT FIXED; wording/calibration-coverage concern

**Evidence:** `calibrate.py` correctly documents a latent Bernoulli state followed by independent seed flips, and correctly computes the contrast target. But `null_ceiling` calls 0.943 the C baseline while using `q=.035`. Its actual expected second-arm accuracy is `.035 + (1 - 2*.035)*.943 = .91199`. Therefore this is not calibration at an observed 94.3% comparator accuracy. The arithmetic probe returned `0.91199`.

**Required:** label latent and observed accuracies accurately; if calibration specifically at an observed 94.3% baseline is intended, archive an additional explicitly described scenario before outputs. This does not invalidate the reported coverage for the simulation actually run, nor justify changing the prescribed interval method. The archived unfavorable sparse coverage is appropriately retained.

## Repairs made and regression evidence

### F1 — P1 — Pre-freeze tests accessed real test content — FIXED PROSPECTIVELY

Replaced the real-data structure test and the gate-notebook payloads with DEV-derived fixtures as described above. The structure test still exercises the real 100-family/300-prompt FINAL_TEST schema, overlap refusal and missing-family refusal. The gate notebook cells still execute in subprocesses. Isolated real-file hashing is retained. The historical incident remains disclosed.

### F2 — P1 — Direct FINAL_TEST evaluation bypassed the notebook gate — FIXED

Previously `phase2_eval.py evaluate --split final_test` loaded the dataset/model without ever calling `gate()`. Added `authorize_final_test()` at the executable entry point, before test bytes are read. It requires `--train-root`, the registered plan hash, the implementation-manifest hash, the complete freeze gate, and membership/path equality for the chosen adapter. The notebook now passes `--train-root`. The loaded base-shard hashes are compared with the freeze before generation; a nonempty shard-hash mapping is mandatory in the freeze schema.

Regression tests: `GateTests.test_driver_requires_the_full_gate_before_reading_test_data` and `test_driver_authorizes_only_frozen_adapters`. They test refusal before input loading, authorized base/adapter paths, and an unauthorized adapter path without reading FINAL_TEST. Existing sealing tests use an explicit mocked authorization boundary over DEV fixtures. R4's broader implementation-authentication gap remains.

### F3 — P1 — Training logs could change after freeze without refusal — FIXED

Before the fix I froze nine synthetic adapters, changed EC-s11's training report to a numerical failure, and the gate still returned all nine. The freeze carried no training-log hashes.

The freeze now includes `training_logs_sha256` for every retained training report and, where present, the notebook's stdout and invocation logs. It refuses a retained run whose training report does not confirm validity. The gate verifies these hashes, mandatory report coverage, that all slots are settled, and that each adapter attempt is the log's valid attempt. Manifests missing log hashes are rejected. No real adapter-freeze manifest exists, so no existing real freeze was rewritten.

Regression tests: `GateTests.test_training_reports_are_frozen_and_checked` and `test_freeze_without_training_log_hashes_is_refused`, plus the existing full/reduced-S and notebook gate tests. Failed-attempt files remain in their original folders and their attempt-log records are retained; this repair does not implement R4's full provenance validation.

### F4 — P1 — Completed-run shortcut ignored requested identity — FIXED

Previously the wrapper skipped the engine's normal resume-identity validation whenever it found a COMPLETE manifest. A changed requested checkpoint/config could therefore reuse a different complete run and rewrite reporting around it. The shortcut now checks dataset, split, config and engine-code digests before exporting, while still never regenerating completed outputs.

Regression: `EngineTests.test_evaluate_command_with_mocked_backend` now changes the requested seed after completion and requires refusal without backend loading. Its unchanged-config case still succeeds without loading/regenerating the model. Existing sealed complete-run checks pass.

### F5 — P2 — Attempt parser accepted training starts after a halt; protocol reports lacked the halt flag — FIXED

A probe appended a new start after a protocol finish; the old parser accepted the history and merely marked the resulting plan halted. It now rejects subsequent starts following numerical/protocol failures, including failures during engineering resumes. `fail_report()` now writes `study_halt: true` for protocol failures as well as numerical failures.

Regressions: `AttemptLogTests.test_log_rejects_new_attempt_after_a_halt` covers both classes; `RunClassificationTests.test_step_count_mismatch_is_a_protocol_failure` checks the report flag. This improves log validation but does not make the direct trainer consult the log before execution (R4).

## Checks that agree with the registration

- Data/exposure mechanics: all 160 TRAIN families, exact UTF-8 decimal seed/pass hash input and tie break, three 160-family passes, consecutive E/second pairs, eight families per update, and arm-independent exposure hashes. Exposure lists for 11/22/33/44/55 recompute exactly. The ordinary trainer source never reads DEV or FINAL_TEST; the notebooks contain DEV for a separate sanity-evaluation subprocess.
- Labels/recipe: shared English completion plus im_end, matched E/R/C targets, completion-only causal loss, equal-example weighting, no truncation/packing, seeded adapter creation, and the smoke model/optimizer recipe. The LR formula and boundaries at 1, 6, 7 and 60 match. Fake-torch tests exercise 60 windows/60 successful steps/cursor 960, unscale-before-clip, pinned scaler settings, and numerical-failure stops without replay.
- Adapter loading: both adapter files are checked before and after `PeftModel.from_pretrained`, `is_trainable=False`, with no merge path. The NF4/FP16 evaluation preparation and its fixed difference from training preparation are recorded. Actual GPU loading and save-key mapping remain unverified here.
- Statistical mechanics: lexicographically sorted families; one reused `random.Random(101)` row-major randrange matrix; exact linear quantiles; sample-SD Wald; correctly clipped Hoeffding widths for differences and S3; checkpoint-specific N-outcome Wilson intervals. An independent recomputation produced matrix hash `33f4920eab5738cf29b346be8d63a15115f9fcbda58699ee9fc44b031e46e6a1`.
- Label mechanics: unrounded strict-only boundaries, local degeneracy overrides, nonzero/distinct contrast counts, bootstrap tails, five independent retention flag sets, correct trade-off eligibility, descriptive secondaries/McNemar values, and no Holm or crossed resampling. The 1/S arithmetic and unresolved-item suppression are implemented correctly; R1 concerns which S/checkpoints get admitted.
- Ceiling/reporting: renamed unchanged-DEV risk proxy, k/40 and Wilson, primary Δ_C first, and actual ER C headroom beside it. Numeric-v2 runs v1 first, preserves all non-unsupported results and old multiple-marker successes, uses the two gold-blind extension paths, and falls back to v1 for non-rupee gold. Its boundary/negative fixtures and Pilot-B fixture checks pass.
- Sealing: normal FINAL_TEST driver output is completion/checksum/infrastructure status; summary/answer previews are suppressed. Completed generated attempts are retained, including wrong/truncated answers. Exhausted/absent generations remain unresolved. No actual FINAL_TEST generation was performed to establish this; tests use DEV.

## Verification and artifact state

Executed the requested builders in order:

1. `python3 -B phase2/build_implementation_manifest.py`
2. `python3 -B colab_notebooks/build_phase2_notebooks.py`

The implementation-manifest SHA-256 is `6a6370cf9bb8dec6d31a020031bb3ec389c5d5ae4b89fcece465b2464918ab19`. Baseline and Train notebooks were rebuilt. FinalTest was correctly skipped because `phase2/ADAPTERS_FROZEN.md` does not exist. Its rendered fixture cells compile and its gate tests run without real test bytes.

| Required command | Final result |
|---|---|
| `python3 -B -m unittest discover -s t4_smoke -p 'test_*.py'` | 150 tests, OK |
| `PYTHONPATH=test1_pilot python3 -B -m unittest discover -s test1_pilot/tests -p 'test_*.py'` | 31 tests, OK |
| `python3 -B -m unittest discover -s secondary_analysis/tests -p 'test_*.py'` | 81 tests, OK |
| `python3 -B -m unittest discover -s phase2_analysis/tests -p 'test_*.py'` | 42 tests, OK |

One intermediate version of the replacement structure fixture had only 40 families and correctly failed the fixed 100-family validator; it was corrected to 100 distinct DEV-derived fixtures and the entire t4 suite rerun successfully. The original suites' success did not detect the open findings; those were checked with the targeted executable probes described above.

Both requested builders' `--check` commands pass, as do `train_phase2.py exposure-order --check`, `build_training_smoke_notebook.py --check`, and `git diff --check`. The archived interval calibration still matches the unchanged analysis-code hash, uses 1,000 datasets per scenario and 10,000 resamples, and retains its unfavorable results; the calibration suite checks its numerical implementation. I did not rerun all 16,000 archived simulated datasets or claim a new calibration archive.

The first two handoffs contain historical implementation claims superseded by Amendment 1 and this review. In particular, their reserve-order interpretation, stack override, automatic disconnect-resume promise, and earlier claim that training logs could be added as prose must not be treated as resolved evidence. Nothing in these CPU checks demonstrates T4 timing/headroom, Drive rename durability, actual Phase2Trainer numerics, or PEFT save/load behavior. Those are remaining GPU validation limits, separate from the reproducible code defects above.

Before advancing the registration, resolve R1–R7, account for the exposure incident, complete the applicable R8–R10 requirements/clarifications, rebuild and recheck again, and preserve the required server-side precedence/archive evidence. The current manifest is reviewable output, **not a recommendation to commit it as the freeze**.

**Is the pipeline ready to freeze? No.**
