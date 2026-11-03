# Sol independent Phase-2 re-review — 4 November 2026

**The pipeline is not ready to freeze.** R1, R3, R6, R7, R9 and R10 are closed within the CPU-verifiable scope. R2, R4 and R8 remain partially fixed; R5's ordinary runtime enforcement is repaired, but its analysis-side enforcement remains part of R2. A newly exercised training-writer ownership risk also remains. All four required suites pass; that does not discharge the input-integrity findings below.

Owner: Sol. Reviewed HEAD `86854bd`, its parent Amendment-2 decisions, the original review, both amendments, and the working-tree implementation manifest. Write scope: two trainer fixes and their regressions, regenerated manifest/notebooks, this handoff and reproducible CPU probe evidence. No commits, pushes, data changes, pre-registration edits, recipe changes or threshold changes. No actual model inference or GPU training was performed. No FINAL_TEST content was decoded, displayed or semantically inspected in this review. The real file was accessed only by isolated byte hashing, including the already audited hash-only unit test. Its SHA-256 remains `da89dd9a626e438dffca39e3a74c4c8abac6bb57501495723b87e6ee143f3d46`.

## Executed evidence

The executable probe is `research/phase2_rereview_2026_11_04/probes.py`; run it from the repository root with `python3 -B research/phase2_rereview_2026_11_04/probes.py`. `probes_before.json` records the initial probes, plus an executed copy of `86854bd`'s original `preflight()` for the optional-argument defect. `probes_after.json` records the working implementation after repairs. They contain synthetic identities and status, not FINAL_TEST content. The before and after sets differ: the later set also includes the explicit wrong-environment and freeze non-file-setting probes.

FINAL_TEST-route analysis probes use the actual engine on DEV fixtures, mocking the dataset loader and the engine's 100-family validation boundary. The real FINAL_TEST path supplied to the analysis does not exist. Those probes test authorization/validation, not statistical conclusions about the sealed dataset. TRAIN probes use only the registered TRAIN files. GPU operations are mocked.

## R1–R10 disposition

| Finding | Disposition | Executed evidence |
| --- | --- | --- |
| R1 — checkpoint and retained-seed binding | **Fixed** | Swapping EC:11/ER:11 paths is refused by adapter identity. Substituting seed 44 for 33 is refused against the frozen checkpoint set. The full binding suite also checks absent adapters, changed model/config hashes or attempt IDs, omitted/extra seeds, reserve mapping, S=0 refusal, reduced-S denominators and suppression of labels. DEV is a separate fixture route. |
| R2 — excluded model and execution validation | **Partial; still open** | The original Llama/revision probe now raises `AnalysisError`. Wrong instruction/mode, changed engine source/config and three attempts under a two-attempt budget are rejected by executed tests. However, the analysis still accepts an explicitly unverified CPU backend and a recorded A100/torch-0.0.0 environment; see B1. |
| R3 — failure classes | **Fixed, with a logging repair here** | `TypeError('bug')` at training → protocol; `OSError('Drive I/O')` at data → infrastructure; `AssertionError('hash mismatch')` at reload → protocol. Entry-point tests exercise data I/O, programming errors, CUDA-OOM-shaped exceptions, checkpoint writes, numerical failure and halt persistence. A catchable `SystemExit` previously escaped the opened attempt; fixed below. Genuine process kills still require later reconciliation. |
| R4 — executable implementation/data/attempt authentication | **Partial; still open** | Changed TRAIN bytes, recomputed family hashes, changed exposure bytes, stale trainer code and changed retry identity are refused in executed tests. The trainer now derives TRAIN from authenticated raw bytes and consults the plan. Nevertheless, unchecked Hub/template entries pass its verification, and a manifest with wrong non-file stack settings passes adapter freeze; see B2. |
| R5 — pinned stack/T4 and overrides | **Runtime fix verified on CPU; analysis acceptance remains open** | Stack-mismatch and non-T4 preflight tests refuse before opening an attempt. Notebook cells have no engineering override and assert a matching stack. The HF backend tests check the exact torch pin and T4. This does not close B1: recorded noncompliant execution still receives analysis acceptance. No claim of actual T4 compatibility is made. |
| R6 — reserve order | **Fixed** | The original out-of-order seed-22 start is rejected before any reserve can be allocated. Executed plan and notebook-flow tests cover EC→ER→EE, slots 11→22→33, whole-triplet replacement, ordered consumption of 44/55 and exhaustion. The notebook supplies no operator arm/seed selection. |
| R7 — stale evaluation lock | **Fixed** | The real engine refuses an existing lock without confirmation. With the explicit recovery flag, the test resumes a DEV-backed journal, records recovery and checks that stored journal bytes are unchanged; a completed run does not reload/regenerate the model. Notebook controls and recovery instructions are present. Training ownership is a separate unresolved risk, B4. |
| R8 — baseline before training | **Partial; still open** | A missing, incomplete or different-manifest baseline record is refused, its ZIP digest enters attempt/freeze identities, and the gate checks the stored artifact. But a ZIP containing just two metadata JSON files, without a single generation, is accepted as the required complete baseline; see B3. The analysis ceiling count remains caller-supplied. |
| R9 — versioned DEV planning rerun | **Fixed as Amendment 2 specifies** | Executed k=38/39/40 probes produce respectively 6/1/0 ordinary feasible cells. k=40 has the additional single admissible degenerate `(p0=1,q0=0,delta=0)` cell and explicitly marks all 16 original-grid cells infeasible. Tests compare feasible cells against the unchanged original simulator and exercise the non-overwriting CLI. |
| R10 — latent/observed calibration wording | **Fixed** | Arithmetic gives `0.91199` for the old latent-ceiling comparator and `0.943` for the added observed-ceiling scenario. Executed tests check the generating formula against simulation, archived scenario fields, current analysis hash and unchanged scenario ordering/seeds. The archive includes the extra 1,000-dataset/10,000-resample scenario and keeps unfavorable coverage. I did not rerun the full archived simulation. |

## Remaining blockers and risks

### B1 — P1 — R2/R5: analysis ignores recorded hardware and dependency environment

`phase2_analysis/analyze.py:429` checks model/config/source identity and selected backend fields, but `parse_implementation_manifest()` does not return dependency pins for validation. `check_final_test_run()` never requires T4 hardware/capability, `gpu_verified=True`, the prescribed attention/dtype/quantization metadata, matching package versions or a valid execution digest. Session checks compare only backend dictionaries; missing sessions also pass the vacuous `all()` check.

**Executed:** the existing binding fixtures say `hardware='none: scripted test fixture on DEV families'` and `gpu_verified=False`, yet `assemble()` returns `labels=True`. A further probe loads an otherwise accepted run, records hardware A100/capability `[8,0]`, sets session torch to `0.0.0`, keeps session/backend agreement, and `check_final_test_run()` returns successfully. This is an explicit noncompliance signal, not merely the possibility of fabricating perfectly compliant metadata.

**Required before freeze:** bind recorded execution facts and every session to the manifest and §2/§4. Phase-2 archives must record enough environment information to check the adapter stack too: the engine's current `PACKAGES` list does not include PEFT. Keep synthetic fixtures clearly identified while testing the same validator with simulated compliant and deliberately noncompliant metadata. Do not weaken the study validator to accommodate CPU fixtures.

### B2 — P1 — R4: manifest verification is incomplete at trainer entry and adapter freeze

`train_phase2.verify_implementation()` authenticates four source files, TRAIN/exposure identity, the recipe/GradScaler, model ID/revision and training dependency constants. It does not authenticate the actual downloaded Hub files or compare the loaded chat template with the manifest. The notebook GPU cell performs Hub-byte checks, so the ordinary notebook route has additional protection; the direct executable does not have that same boundary.

**Executed:** a trainer manifest with zero-filled `tokenizer.json` and chat-template hashes passes `verify_implementation()`. Separately, I retained all real current file digests, changed only `dependencies.evaluation.torch` to `0.0.0`, built synthetic completed triplets that consistently named that manifest, and `freeze_manifest()` returned S=3. `phase2_eval.verify_manifest_against():202` rechecks listed file bytes but does not rederive the non-file choices. A shared manifest digest alone does not establish that those choices were checked.

**Required before freeze:** verify the relevant loaded Hub/template/config identities at the executable boundary, and perform the complete manifest-currency check at freeze, including derived non-file entries and the expected required file set. Preserve the now-working authoritative TRAIN/exposure and identical-attempt checks. No recipe or dependency-policy decision is needed to enforce the already registered values.

### B3 — P1 — R8: baseline metadata is mistaken for evidence of a complete registered run

`train_phase2.verify_baseline():336` verifies the record/ZIP hash and a few self-reported fields. It reads only `run_manifest.json` and `experiment_config.json` from the ZIP. It does not recompute the config digest, validate the frozen DEV dataset/source snapshots, verify generated records/completeness, check execution settings/environment, or bind the archive's actual engine identity to the implementation manifest.

**Executed:** the existing `write_baseline()` fixture produces a ZIP with only those two JSON members. Its config omits the model revision, prompt and decoding settings; it has no dataset, source or generation journal. The real `verify_baseline()` nevertheless returns its ZIP hash as a valid complete 120-generation baseline. In addition, `phase2_eval.bind_implementation()` records a supplied manifest's hash without verifying the running code, so a record bearing the desired hash is not by itself proof of the declared implementation.

The new prerequisite and recorded order are useful, but the original requirement is an actual complete unchanged-model DEV run. The analysis also accepts `ceiling_proxy_k` from the caller without deriving it from the frozen baseline ZIP.

**Required before freeze:** validate the actual baseline archive against frozen DEV, registered execution/config/source identities and exactly 120 resolved generations. Authenticate the baseline's implementation when it is created. Derive/check k against this same artifact during analysis. A byte-hash match to a shallow metadata record is insufficient.

### B4 — P1 — automatic training reconciliation has no writer-ownership check

`train_phase2.preflight()` calls `reconcile()` automatically, and the notebook does the same. `reconcile():977` treats every open attempt as abandoned without checking whether another session is still loading/training. There is no training-root writer lock. In particular, the trainer does not persist its initial STARTED report before model loading, leaving a realistic interval with a start event and no report.

**Executed:** I appended a valid start event for EC/11, invoked `reconcile()` immediately without asserting that the writer was dead, and it appended an infrastructure finish. `next_run()` then authorized attempt 2. The probe does not launch two GPUs; it demonstrates that there is no liveness/ownership condition between a potentially active start and consuming its retry. A second Colab session can therefore run alongside the original or prematurely spend retries/reserves. If the original later appends its finish, the log can become inconsistent.

**Required before freeze:** enforce one writer per training root and provide an explicit safe stale-writer recovery procedure. An open event must not automatically count as a dead process. This concerns execution ownership, not a change to the registered retry or reserve policy.

## Clear bugs repaired in this re-review

1. **Catchable runtime exits were not recorded.** `classify_failure(SystemExit(...))` already classified the exception as infrastructure, but neither training catch clause caught it. The initial executable probe escaped with code 9 and left only a start event. Both setup and training now catch it, write the classified failure report and append a finish event; the after-probe returns infrastructure exit 1 with one permitted retry. Regression: `TrainerEntryTests.test_system_exit_records_infrastructure_at_setup_and_during_training`. Uncatchable process termination still uses reconciliation; this repair does not solve B4.
2. **Individually optional CLI assertions were effectively all-or-none.** On the original source, `--arm EC` alone refused the plan's EC/11/11/1 run because unspecified fields were compared as `None`. Supplied fields now independently assert the plan's choice. A wrong supplied field still refuses without opening an attempt. Regression: `TrainerEntryTests.test_each_optional_run_assertion_can_be_supplied_independently` covers each option and an incorrect arm. The notebook continues to run the plan's choice.

The repairs change neither failure policy nor run selection. No statistical implementation was edited; the archived calibration's analysis hash remains valid.

## Amendments and access-incident disclosure

The original ten items are assessed above. The existing F1–F5 repairs remain covered by the passing suites: DEV fixtures replace semantic FINAL_TEST test access; direct FINAL_TEST evaluation requires the gate before input loading; frozen retained training reports are checked; completed-run identity cannot be relabelled; starts after a halt are rejected. The numerical/step-count, data-order, bootstrap/interval, degeneracy, retention and reduced-S tests continue to pass. These CPU checks provide no evidence of a change to the registered estimands, thresholds or recipe.

**Disclosure assessment: substantively accurate about the code paths found, with limits on what this review can independently certify.** I inspected the historical *test source*, not historical or current FINAL_TEST contents:

- In `60bcd99`, `InputTests.test_final_test_mode_validates_structure` read the real file and called `inputs()`/`validate()`; the latter invokes `validate_gold()` and `score_response('FINAL: 0', gold)`. This is schema/gold processing and scoring of a fixed dummy string, not evaluation-backbone inference.
- In `535b1e9`, `FinalTestGateNotebookTests` built notebooks carrying the real bytes and executed setup plus gate cells in subprocesses. Setup extracts the payload to disk before the gate. For completeness, the disclosure should explicitly mention **extraction into temporary test workspaces**, in addition to embedding. Neither operation is an isolated byte-hash check.
- The 3 November Sol review explicitly records running the suite before discovering these paths. The disclosure must continue to cover that run as well as the implementers' runs; it is not just a code-author incident.
- Current tests substitute DEV bytes before synthetic FINAL_TEST notebook construction and use DEV-derived 100-family schema fixtures. I inspected those substitutions before executing the suites. The remaining real-file unit-test access computes SHA-256 only.

The repository supports that these test paths produce pass/fail/status output and contain no evaluation-backbone generation. It cannot independently prove the universal historical statements that no human/model ever saw content, the exact number/timing of unattended runs, or that no other access occurred. Those remain participant/access-log attestations. Likewise, “no information reached any analysis choice” is a provenance claim, not something a passing suite proves. I found no contrary evidence in the reviewed paths. The adopted amendment already acknowledges the rule violation; I made no new registration decision and did not edit its disclosure.

The normal Baseline notebook currently does not automatically invoke the new planning script. R9 is closed because Amendment 2 explicitly requires the versioned script, which is supplied and tested; the operator still must archive its run after obtaining observed k/40. This review cannot perform that future rerun without an actual baseline. No baseline or adapter-freeze artifact exists in this checkout. The implementation manifest also remains uncommitted, so Amendment 1 item 14's commit/push/archive precedence requirement has not yet been satisfied. No commits were authorized in this task.

## T4 crash, hang and memory assessment

No real T4 load/save/reload or 60-update run was performed. CPU tests exercise the numerical stop paths, adapter-file checks, run-order orchestration, stale evaluation-lock recovery and simulated training failures. I found no newly demonstrated tensor-memory leak or infinite loop in the repaired code. That is not a hardware feasibility result. Exact pinned-package importability, real CUDA/Hub/Drive exception behavior, actual peak VRAM/host RAM, PEFT save-key equality and runtime duration remain unverified here. B4 is a concrete overlapping-run/attempt-log risk on Colab; B1–B3 are acceptance/provenance defects even if a T4 run happens to finish.

## Final verification and artifacts

After the trainer repairs I rebuilt **in the required order**:

1. `python3 -B phase2/build_implementation_manifest.py`
2. `python3 -B colab_notebooks/build_phase2_notebooks.py`

Manifest SHA-256: `1a471b2ec2dbe10bdfafc02044316aeb680ee7b2dd3ad2a268238181c083bd78`. Baseline and Train notebooks were rebuilt. FinalTest was correctly skipped because `phase2/ADAPTERS_FROZEN.md` does not exist; the executable gate-notebook tests still run with synthetic freezes/DEV payloads.

| Required suite, after rebuild | Result |
| --- | --- |
| `python3 -B -m unittest discover -s t4_smoke -p 'test_*.py'` | **174 passed** |
| `PYTHONPATH=test1_pilot python3 -B -m unittest discover -s test1_pilot/tests` | **32 passed** |
| `python3 -B -m unittest discover -s secondary_analysis/tests` | **81 passed** |
| `python3 -B -m unittest discover -s phase2_analysis/tests` | **73 passed** |

Both builders' `--check` commands, the exposure-order `--check` and `git diff --check` pass. The initial pre-repair suites also passed (172/32/81/73). The original scorer/numeric-v1 source, pre-registration, data and exposure-order file were not modified. Only the two Phase-2 notebooks changed; older notebooks remain untouched. The initially untracked request handoff was preserved, and the initially untracked manifest was regenerated, not committed.

The review is complete; the freeze gate has **not** advanced. Address B1–B4 and re-review the resulting executable checks before committing the implementation freeze or generating study outputs.

**Ready to freeze: NO.**
