"""Independent CPU probes for the 4 November re-review; uses TRAIN/DEV and synthetic artifacts only.

Run from the repository root: python3 -B research/phase2_rereview_2026_11_04/probes.py
The emitted JSON contains identities/status only. Acceptance probes deliberately describe open defects;
they are evidence, not assertions that the accepted artifacts are protocol-valid.
"""
import contextlib
import copy
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "test1_pilot"), str(ROOT / "phase2_analysis/tests")]
import test_final_test_binding as binding
from phase2_analysis import analyze as A, calibrate as C
from t4_smoke import train_phase2 as T
from t4_smoke import phase2_eval as E
from t4_smoke import test_phase2_eval as gate_fixtures
from t4_smoke.test_train_phase2 import TrainerEntryTests, FakeRunTrainer, TrainerFixture, write_baseline
import test_power_dev_rerun as power


def attempt(call):
    try:
        value = call()
    except Exception as error:
        return {"accepted": False, "exception": type(error).__name__, "message": str(error)}
    return {"accepted": True, "value": value}


def main():
    result = {"reviewed_head": "86854bd", "data": "DEV/TRAIN and synthetic fixtures only"}
    quiet = io.StringIO()
    with contextlib.redirect_stdout(quiet), contextlib.redirect_stderr(quiet):
        binding.setUpModule()
        fixture = binding.Fixture()
        fixture.setUp()
        try:
            runs = binding.checkpoints()
            swapped = dict(runs)
            swapped[("EC", 11)], swapped[("ER", 11)] = swapped[("ER", 11)], swapped[("EC", 11)]
            result["R1_swapped_arms"] = attempt(lambda: fixture.assemble(swapped)["labels"])
            result["R1_substituted_seed"] = attempt(lambda: fixture.assemble(binding.checkpoints((11, 22, 44)))["labels"])
            result["R2_unverified_CPU_backend"] = attempt(lambda: fixture.assemble(runs)["labels"])
            loaded = A.load_run(binding.RUNS[(A.UNCHANGED, None)])
            manifest = copy.deepcopy(loaded["manifest"])
            manifest["backend"].update(hardware="NVIDIA A100", gpu_verified=False, capability=[8, 0])
            for session in manifest["sessions"]:
                session["backend"] = manifest["backend"]
                session["environment"]["packages"]["torch"] = "0.0.0"
            loaded["manifest"] = manifest
            result["R2_wrong_recorded_environment"] = attempt(lambda: A.check_final_test_run(
                (A.UNCHANGED, None), loaded, A.load_frozen(fixture.frozen), A.load_implementation_manifest(fixture.impl)))
            bad = binding.final_test_config(None)
            bad.update(model_id=binding.LLAMA, model_revision="0" * 40)
            result["R2_excluded_model"] = attempt(lambda: A.check_config(bad, "FINAL_TEST"))
            # No GPU, no matching dependency stack: these are exactly the existing binding fixtures.
            result["R2_fixture_metadata"] = binding.FinalTestFixtureBackend(("EC", 11), binding.adapter_entry("EC", 11)).metadata
        finally:
            fixture.doCleanups()
            binding.tearDownModule()

        result["R3_original_probes"] = {
            "TypeError_training": T.classify_failure(TypeError("bug"), "training"),
            "OSError_data": T.classify_failure(OSError("Drive I/O"), "data"),
            "AssertionError_reload": T.classify_failure(AssertionError("hash mismatch"), "reload"),
        }
        with tempfile.TemporaryDirectory() as temp:
            train = TrainerFixture(temp)
            # These fields are not checked by verify_implementation, despite governing tokenizer/model loading.
            doc = T.parse_manifest((train.inputs / T.MANIFEST_NAME).read_text())
            doc["model"].update(hub_files={"tokenizer.json": "0" * 64}, chat_template={"digest": "0" * 64})
            train.write_manifest("```json\n" + json.dumps(doc) + "\n```\n")
            result["R4_wrong_Hub_template_entries"] = attempt(lambda: T.verify_implementation(train.inputs)[1])
            # This ZIP contains only two tiny JSON metadata members: no dataset, journal, sources or generations.
            digest = write_baseline(train.baseline, train.manifest_sha)
            result["R8_two_metadata_files_as_baseline"] = attempt(lambda: T.verify_baseline(train.baseline, train.manifest_sha) == digest)
            T.log_event(train.log, "start", arm="EC", seed=11, slot=11, attempt=1,
                        identity=T.attempt_identity(train.inputs, digest))
            result["new_live_attempt_reconcile"] = [e["outcome"] for e in T.reconcile(train.train_root)]
            result["new_live_attempt_next_run"] = T.next_run(T.plan(T.read_log(train.log)))

        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            # Real current file digests, but wrong non-file execution settings.
            doc = T.parse_manifest((ROOT / "phase2/IMPLEMENTATION_MANIFEST.md").read_text())
            doc["dependencies"]["evaluation"]["torch"] = "0.0.0"
            manifest = temp / "IMPLEMENTATION_MANIFEST.md"
            manifest.write_text("```json\n" + json.dumps(doc) + "\n```\n")
            manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
            with mock.patch.object(gate_fixtures, "MANIFEST_SHA", manifest_sha):
                gate_fixtures.complete_slots(temp / "train")
            result["R4_freeze_wrong_non_file_stack"] = attempt(lambda: E.freeze_manifest(
                temp / "train", manifest_path=manifest, root=ROOT)["S"])

        # Capture a SystemExit from inside the opened trainer: before repair it escapes without a finish event.
        fixture = TrainerEntryTests()
        fixture.setUp()
        try:
            try:
                code, _, _ = fixture.train(type("ExitTrainer", (FakeRunTrainer,), {"fail_at": 2, "error": SystemExit(9)}))
                result["SystemExit_training"] = {"exit_code": code, "outcomes": fixture.outcomes()}
            except SystemExit as error:
                result["SystemExit_training"] = {"escaped": error.code, "outcomes": fixture.outcomes()}
        finally:
            fixture.tearDown()

        # Execute the actual adversarial regressions for R1-R8 (no model loading).
        names = [
            "t4_smoke.test_train_phase2.AttemptLogTests.test_sol_r6_sequence_is_refused",
            "t4_smoke.test_train_phase2.TrainerEntryTests.test_stack_mismatch_or_non_t4_refuses_before_the_attempt_opens",
            "t4_smoke.test_train_phase2.TrainerEntryTests.test_changed_configuration_or_implementation_is_refused",
            "t4_smoke.test_train_phase2.TrainerEntryTests.test_manifest_train_and_exposure_are_verified_inside_the_attempt",
            "t4_smoke.test_phase2_eval.BaselineRecordAndLockTests.test_stale_lock_is_recovered_only_when_requested_and_nothing_is_regenerated",
        ]
        suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names)
        checks = unittest.TextTestRunner(stream=quiet).run(suite)
        result["targeted_regressions"] = {"run": checks.testsRun, "failures": len(checks.failures), "errors": len(checks.errors)}

        R = power.R
        result["R9_boundaries"] = {str(k): R.summary(R.rerun_grid(k, reps=5)) for k in (38, 39, 40)}
        scenarios = {s[0]: s for s in C.SCENARIOS}
        result["R10_observed_accuracies"] = {n: C.observed_accuracy(scenarios[n][3]) for n in ("null_ceiling", "null_ceiling_observed")}
        archive = json.loads((ROOT / "phase2_analysis/calibration.json").read_text())
        result["R10_archive_analysis_hash_matches"] = archive["analyze_sha256"] == hashlib.sha256(Path(A.__file__).read_bytes()).hexdigest()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
