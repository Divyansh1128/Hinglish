# Phase-3 step 2: implementation and execution gates

No training or Phase-3 DEV/FINAL_TEST inference is performed by implementation or
CPU tests. `PREREGISTRATION.md` governs. The original engine, statistical core and
all files bound by the earlier manifests remain unchanged.

Before training, archive the adopted registration, target archive/freeze, this
implementation manifest and notebooks read-only on a server. Record hashes,
exposure/adoption timestamps and server-side evidence; local commit times alone
are insufficient. Obtain the independent implementation/execution review required
by §11. These events are not claimed by the manifest builder.

Build and verify, from the repository root:

```sh
python3 -B -m t4_smoke.train_phase3 exposure-lists
python3 -B colab_notebooks/build_phase3_step2_notebooks.py
python3 -B phase3/build_implementation_manifest.py
python3 -B phase3/build_implementation_manifest.py --check
```

The sibling notebook builder imports the frozen step-1 builder. The hard rule
forbids editing that builder or the already frozen Targets notebook. The training
payload embeds engine + TRAIN + DEV + exact targets, target journals/review archive,
original DEV evidence and the required runtime modules, never FINAL_TEST.
`step2_runtime_contract.json` binds every executable/input in that payload. The
outer implementation manifest binds the runtime contract, both notebooks, all
step-2 files, the earlier manifests, statistical core, frozen targets/exposures,
audit rubric and original baseline identities. Every runtime entry authenticates
its files against that contract and outer manifest; the local adapter freeze
additionally checks the complete file set and both earlier freezes.
Authentication also resolves imported Phase-3, Phase-2, engine and analysis modules'
actual `__file__` paths and hashes them, and requires the entire executing engine
source inventory to equal the runtime contract. `--root` must resolve to the
executing checkout; a pristine alternative checkout cannot authenticate modified
running code. Symlinks resolve before comparison. Data/code roots are deliberately
not split. Both DEV and FINAL_TEST preflights collect the engine's
`PHASE2_PACKAGES` environment (including PEFT), using the same mode selection as
the frozen engine; a missing/wrong PEFT refuses before generation.

Copy `phase3/IMPLEMENTATION_MANIFEST.md` to
`MyDrive/Hinglish_Phase3/IMPLEMENTATION_MANIFEST.md`, open Phase3_Train.ipynb in a
fresh T4 runtime. Paste the SHA-256 printed by the implementation manifest builder
from the archived release into `EXPECTED_IMPLEMENTATION_SHA256`. The manifest binds
the notebook, so embedding that same manifest hash in its notebook would create a
self-reference; this explicit operator setting is the independent expected hash.
Immediately after Drive mount, before the torch check, installs or GPU checks, the
launcher checks the companion's existence and exact hash, with its Drive path and
remediation on refusal. Run its cells. The launcher prints the pending ARM/SEED/attempt
and training/evaluation lock status, then defaults ARM/SEED to that plan (initially
EC/11); the operator may override them but the trainer's plan assertion remains. The planner requires EC→ER→EE per slot, slots 11→22→33; reserves 44 then
55 replace a whole triplet after the second infrastructure failure. Operator
settings assert that plan. Each launch drains pending DEV sanity, trains one run,
and completes its DEV sanity in a separate subprocess before another training
attempt is permitted. The same seed/config/code gets one from-scratch retry only
for typed infrastructure failures. A numerical/protocol error halts. No checkpoint
resume is available; retained checkpoints are diagnostic evidence.

The original unchanged-DEV export is validated with its genuine Phase-2 manifest,
engine source/config/environment and complete 120-generation coverage. The bridge
records both implementation identities and checks exact inference equivalence;
it does not pretend the training implementation is unchanged. Original DEV C
24/40 is carried forward. DEV results cannot select a checkpoint, alter targets or
authorize a retry. Successful runs in subsequently discarded triplets also get
DEV sanity. Logs retain token counts, visits/cursors, losses/norms/lr/scaler,
timings/memory, initialization, checkpoints, attempts, recoveries and weight hashes.

After a disconnect, inspect the plan and active locks. Only after confirming no
other trainer/evaluator is active set RECOVER_STALE_WRITER or RECOVER_STALE_LOCK
in the notebook. Recovery is logged; a writer recovery preserves a recorded
numerical/protocol failure. Stored generations never regenerate. Attempts and
exports stay on Drive and are included in the download ZIP.

Every evaluation uses `train/EVALUATION_REGISTRY.jsonl`, a hash-chained append-only
study registry under an OS advisory lock held through initialization, generation
and export. The lock fails closed if held or unsupported by the filesystem. DEV
uses its implementation/target freeze identity; FINAL_TEST uses the exact adapter
freeze SHA-256. Each adapter/split reservation binds that identity, full adapter
hashes and canonical study-relative run directory. The unchanged engine first
runs with `max_items=0`, creating its run ID and empty journal without generation;
the registry durably binds that ID before the scored run starts. A crash in that
initialization can adopt only a zero-generation history. A bound recovery must
reuse the same directory, engine ID and stored attempts; a second directory is
refused. Never delete/reset the registry, journals or lock while a writer is active.
The persistent registry lock file is harmless when its OS lock is released.

The authoritative study root is `TRAIN_ROOT.parent`, with training under `train/`
and FINAL_TEST under `final_test/`. Evaluation paths cannot be chosen elsewhere.
Canonical paths are relative to this root, allowing the complete tree to move from
Drive to local storage with its layout intact. Copy the entire training tree,
including all DEV histories, and merge the final download bundle into the same
study root: the bundle contains `final_test/` and the updated
`train/EVALUATION_REGISTRY.jsonl`. Keep download bundles outside this study root
when analyzing. The adapter freeze binds the DEV registry snapshot; the mutable
registry/OS lock files are excluded from generic training-log hashes so registering
FINAL_TEST does not invalidate the freeze. All registered histories, including
abandoned/incomplete reservations, must reconcile before outcome unsealing.

After all slots are settled and DEV sanity validates, bring the complete training
root back locally, preserving its directory structure and every attempt. Freeze:

```sh
python3 -B -m t4_smoke.phase3_eval freeze-manifest --train-root TRAIN_ROOT
python3 -B -m t4_smoke.phase3_eval gate --train-root TRAIN_ROOT
```

The first command writes `phase3/ADAPTERS_FROZEN.md`, binding actual retained
adapter/config bytes, base shards/revision, seed slots/S, target/exposure/
implementation identity, all training/attempt/recovery logs and DEV archives.
It hashes FINAL_TEST and the original Phase-2 archive/member bytes without decoding
responses, scores, journal, dataset or configuration. The second command verifies
the freeze, then semantically validates the unchanged baseline against the genuine
original manifest and run ID/config digest. No new FINAL_TEST generation can begin
if that bridge fails. Inability to validate never authorizes regeneration.

To avoid a circular notebook/implementation/adapter hash and keep FINAL_TEST out
of pre-freeze payload construction, Phase3_FinalTest.ipynb is a fixed launcher.
After the matching adapter gate succeeds, create and archive the final payload:

```sh
python3 -B colab_notebooks/build_phase3_step2_notebooks.py --finalize --train-root TRAIN_ROOT
```

This creates `phase3/FINAL_EVAL_PAYLOAD.zip` (includes FINAL_TEST, original Phase-2
baseline archive, runtime files, implementation and adapter freeze) and
`phase3/FINAL_EVAL_MANIFEST.md`, binding all of those plus the frozen launcher.
Copy both files into `MyDrive/Hinglish_Phase3/`. Run the fixed FinalTest notebook
in a fresh T4 runtime with the same complete Drive training root. It refuses a
missing/mismatching freeze; it evaluates only retained adapters, unmerged, and
never generates an unchanged baseline. At S=3 this is nine adapters and 2,700 new
generations. Registered S=1/2 attrition permits 3S adapters and descriptive reduced-S
reporting only; S=0 refuses test access. This exception follows §10, not an
operator choice to select seeds.

Every console remains sealed to completion/checksum/infrastructure status. All
required exports must have valid checksums, exact adapter/config/environment
identities, attempt budgets and complete coverage before outcome unsealing. The
primary wrapper discovers the exact retained archive set, records journal/export
hashes, validates provenance, then calls the unchanged Phase-2 statistical core:

```sh
python3 -B -m phase3_analysis.analyze --train-root TRAIN_ROOT --evaluations EVALUATIONS --out NEW_OUTPUT
```

Do not choose an output directory that already exists. Run the frozen primary
once, then independent recomputation under §11. `phase3_analysis.compare` is a
separate descriptive comparison, requires the complete primary report and matching
export receipts, validates original Phase-2 runs through their original assembly,
and reports phase-specific seed means without claiming seed pairing. It reports
accuracy and engine `output_tokens` mean/median/quartiles/IQR, with no new tests or
decision labels. See `python3 -B -m phase3_analysis.compare --help` for arguments.
Before loading analysis outcomes, the wrapper reconciles every registered DEV and
FINAL_TEST history, exact engine IDs, aggregate/atomic journals and checksummed
exports, and refuses unregistered/extra run directories, orphan journals or exports
anywhere under the study root. Missing/incomplete reservations refuse unsealing.
The wrapper labels Phase 3 as a pre-specified follow-up on a reused test set.
Only the Markdown report title and explicit study attribution change: references
to original Phase-2 baselines/methods in the unchanged core's prose are preserved.
The unchanged statistical implementation retains all bootstrap/quantile/label/
degeneracy/English-flag mechanics. Descriptive length quartiles stay outside it.

The audit contract is `AUDIT_RUBRIC.md`, binding Pilot-B's taxonomy and the Phase-3
full-human-review requirement. No audit packet/tagging is performed before the
complete evaluation and primary analysis. Release additionally requires the
independent recomputation, full audit, human returns and hashed analysis outputs.

All implementation judgments where operational details were unspecified are
listed verbatim in the implementation manifest's `judgments` array. No source
control commit, server-side exposure evidence or GPU validation is claimed here.


Step-2 review verification (synthetic/CPU only):

```sh
python3 -B -m unittest t4_smoke.test_phase3_eval t4_smoke.test_train_phase3 phase3_analysis.tests.test_analyze
python3 -B colab_notebooks/build_phase3_step2_notebooks.py --check
python3 -B phase3/build_implementation_manifest.py --check
python3 -B phase2/build_implementation_manifest.py --check
python3 -B phase3/build_target_gen_manifest.py --check
```

The regression tests cover real evaluation preflight construction for DEV and
FINAL_TEST with PEFT present/missing, modified executing checkout versus pristine
`--root`, foreign imported source and complete engine inventory, study-wide
uniqueness/locking/recovery, missing/substituted journals, abandoned registrations,
extra histories/exports/orphan journals and analysis integration, early companion
hash checking, pending-plan defaults, and preservation of Phase-2 report prose.
Run every repository Python test directory separately with `unittest discover`
(`authoring/tests`, `autoverify/tests`, `exploratory/tests`, `paper_analysis/tests`,
`phase2_analysis/tests`, `phase3_analysis/tests`, `secondary_analysis/tests`,
`t4_smoke`, `test1_pilot/tests`, `pilot/scripts`); include the repo, `test1_pilot`
and `pilot/scripts` in `PYTHONPATH`. Root-only discovery omits most suites.
No GPU training, new research inference or held-out outcome unsealing is claimed.
