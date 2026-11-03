"""Model-free tests of Phase-2 evaluation inputs, the engine modes and the FINAL_TEST gate."""
import atexit
import copy
import hashlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from t4_smoke import phase2_eval as pe
from t4_smoke import train_phase2 as tp
from t4_smoke import train_smoke as ts
from t4_smoke.test_train_phase2 import IDENTITY, write_baseline
from hinglish_pilot import engine as live_engine
from hinglish_pilot import hf_backend
from hinglish_pilot.data import validate
from hinglish_pilot.engine import FakeBackend, default_config, run, validate_config
from hinglish_pilot.report import analyze, export, wilson

ROOT = Path(__file__).resolve().parents[1]
H = lambda text: hashlib.sha256(text.encode()).hexdigest()  # noqa: E731


def fake_backend(adapter):
    class LabelledFake(FakeBackend):  # engine forbids the 'fake' backend outside demo
        metadata = dict(FakeBackend.metadata, backend="huggingface", adapter=copy.deepcopy(adapter),
                        model_revision=pe.MODEL_REVISION, tokenizer_revision=pe.MODEL_REVISION)
        load_report = {"load_seconds": 0}

        def __init__(self, config=None, adapter_path=None):
            self.adapter_path = adapter_path
    return LabelledFake


class InputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.identities = pe.split_identities(ROOT)
        cls.dev = (ROOT / "phase2" / "dev.v2.json").read_bytes()

    def test_frozen_hashes_agree_with_the_frozen_notes_and_preregistration(self):
        prereg = (ROOT / "phase2" / "PREREGISTRATION.md").read_text()
        notes = (ROOT / "phase2" / "TRAIN_DEV_FROZEN.md").read_text() + (ROOT / "phase2" / "FINAL_TEST_FROZEN.md").read_text()
        for split, (path, digest, _, _) in pe.FROZEN.items():
            self.assertIn(digest, notes)
            self.assertIn(digest, prereg)
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest)

    def test_identities_hold_no_text_and_no_final_test(self):
        self.assertEqual(sorted(self.identities), ["CONFIRM_TRAIN", "DEV"])
        self.assertEqual((len(self.identities["CONFIRM_TRAIN"]), len(self.identities["DEV"])), (160, 40))
        text = json.dumps(self.identities)
        for marker in ("FT0", "forms", "gold", "text"):
            self.assertNotIn(marker, text)

    def test_dev_inputs_are_the_frozen_file_unchanged(self):
        dataset, splits = pe.inputs(self.dev, "dev", self.identities)
        self.assertEqual(dataset["families"], json.loads(self.dev))
        self.assertEqual(dataset["kind"], "phase2_dev")
        self.assertEqual(splits["FINAL_TEST"], [])
        self.assertEqual(validate(dataset, splits, "phase2_dev")["prompts"], 120)
        with self.assertRaises(ValueError):
            validate(dataset, splits, "pilot_b")

    def test_tampered_or_wrong_split_bytes_are_refused(self):
        with self.assertRaisesRegex(ValueError, "frozen SHA-256"):
            pe.inputs(self.dev.replace(b"FINAL", b"Final", 1), "dev", self.identities)
        with self.assertRaisesRegex(ValueError, "frozen SHA-256"):
            pe.inputs(self.dev, "final_test", self.identities)
        with self.assertRaisesRegex(ValueError, "frozen SHA-256"):
            pe.inputs((ROOT / "phase2" / "dev.DRAFT.json").read_bytes(), "dev", self.identities)

    def test_final_test_mode_validates_structure(self):
        # Exercise FINAL_TEST validation with DEV content, never the sealed test set.
        dev = json.loads(self.dev)
        families = [copy.deepcopy(dev[i % len(dev)]) for i in range(100)]
        for i, family in enumerate(families):
            family["split_role"] = "FINAL_TEST"
            for key in pe.IDENTITY:
                family[key] = f"fixture-{key}-{i}"
            for form, rendering in family["forms"].items():
                rendering["rendering_id"] = f"fixture-{i}-{form}"
                rendering["text"] += f" Fixture {i}."
        raw = json.dumps(families).encode()
        identities = dict(self.identities, DEV=[])
        fixture = ("phase2/final_test.fixture.json", hashlib.sha256(raw).hexdigest(), "FINAL_TEST", 100)
        with mock.patch.dict(pe.FROZEN, final_test=fixture):
            dataset, splits = pe.inputs(raw, "final_test", identities)
        self.assertEqual(validate(dataset, splits, "phase2_final_test")["prompts"], 300)
        overlap = copy.deepcopy(splits)
        overlap["development_exclusion_ids"].append(splits["FINAL_TEST"][0]["family_id"])
        with self.assertRaises(ValueError):
            validate(dataset, overlap, "phase2_final_test")
        missing = copy.deepcopy(splits)
        missing["FINAL_TEST"].pop()
        with self.assertRaises(ValueError):
            validate(dataset, missing, "phase2_final_test")

    def test_dev_cannot_overlap_train(self):
        dataset, splits = pe.inputs(self.dev, "dev", self.identities)
        bad = copy.deepcopy(splits)
        bad["CONFIRM_TRAIN"].append({k: dataset["families"][0][k] for k in pe.IDENTITY})
        with self.assertRaises(ValueError):
            validate(dataset, bad, "phase2_dev")

    def test_config_and_ceiling_flag(self):
        config = pe.config_for("dev")
        self.assertEqual((config["seed"], config["model_revision"], config["adapter"], config["max_new_tokens"]),
                         (11, ts.MODEL_REVISION, None, 1024))
        metrics = lambda c: {"accuracy": {"C": {"correct": c, "denominator": 40}}}  # noqa: E731
        self.assertTrue(pe.ceiling_flag(metrics(38))["flag"])
        self.assertTrue(pe.ceiling_flag(metrics(40))["flag"])
        self.assertFalse(pe.ceiling_flag(metrics(37))["flag"])

    def test_ceiling_risk_proxy_reports_k_of_40_with_wilson_interval(self):
        """Amendment 1 item 7."""
        flag = pe.ceiling_flag({"accuracy": {"C": {"correct": 38, "denominator": 40}}})
        self.assertEqual(flag["name"], "high unchanged-DEV accuracy (ceiling-risk proxy)")
        self.assertEqual((flag["k"], flag["n"], flag["flag"]), (38, 40, True))
        self.assertEqual(flag["wilson95"], wilson(38, 40))
        self.assertAlmostEqual(flag["wilson95"][0], 0.8350, places=3)
        self.assertAlmostEqual(flag["observed_dev_headroom"], 0.05)
        line = pe.ceiling_line(flag)
        self.assertTrue(line.startswith("high unchanged-DEV accuracy (ceiling-risk proxy): FIRES — unchanged DEV C 38/40"))
        self.assertIn("Wilson 95% 83.5–98.6%", line)
        self.assertIn("does not fire — unchanged DEV C 37/40", pe.ceiling_line(pe.ceiling_flag({"accuracy": {"C": {"correct": 37, "denominator": 40}}})))


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.dataset, self.splits = pe.inputs((ROOT / "phase2" / "dev.v2.json").read_bytes(), "dev", pe.split_identities(ROOT))
        self.adapter = {"arm": "EC", "seed": 11, "attempt": 1, "adapter_model_sha256": "a" * 64, "adapter_config_sha256": "b" * 64}

    def tearDown(self):
        self.folder.cleanup()

    def test_adapter_run_end_to_end_with_fake_backend(self):
        config = pe.config_for("dev", self.adapter)
        manifest = run(self.root / "dev", self.dataset, self.splits, config, fake_backend(self.adapter)())
        self.assertEqual((manifest["status"], manifest["expected"]), ("COMPLETE", 120))
        self.assertTrue(manifest["label"].startswith("PHASE-2 DEV"))
        self.assertIn("adapter EC seed 11", manifest["warnings"][2])
        self.assertEqual(manifest["backend"]["adapter"], self.adapter)
        metrics, _ = analyze(self.root / "dev")
        self.assertEqual(metrics["accuracy"]["C"]["denominator"], 40)
        self.assertIn("Single checkpoint only", (self.root / "dev" / "summary.md").read_text())
        self.assertTrue(export(self.root / "dev").is_file())
        # Resume identity includes the adapter: another adapter cannot continue this run.
        other = dict(self.adapter, adapter_model_sha256="c" * 64)
        with self.assertRaisesRegex(ValueError, "Resume rejected"):
            run(self.root / "dev", self.dataset, self.splits, pe.config_for("dev", other), fake_backend(other)())

    def test_backend_must_have_loaded_the_configured_adapter(self):
        with self.assertRaisesRegex(ValueError, "did not load the adapter"):
            run(self.root / "x", self.dataset, self.splits, pe.config_for("dev", self.adapter), fake_backend(None)())
        with self.assertRaisesRegex(ValueError, "did not load the adapter"):
            run(self.root / "y", self.dataset, self.splits, pe.config_for("dev"), fake_backend(self.adapter)())

    def test_evaluate_command_with_mocked_backend(self):
        inputs = self.root / "inputs"
        inputs.mkdir()
        (inputs / "dev.v2.json").write_bytes((ROOT / "phase2" / "dev.v2.json").read_bytes())
        (inputs / "identities.json").write_text(json.dumps(pe.split_identities(ROOT)))
        with mock.patch.object(hf_backend, "HFBackend", fake_backend(None)), mock.patch("sys.stdout", io.StringIO()):
            code = pe.main(["evaluate", "--split", "dev", "--inputs", str(inputs), "--run-dir", str(self.root / "runs" / "base")])
            self.assertEqual(code, 0)
            flag = json.loads((self.root / "runs" / "base_ceiling_flag.json").read_text())
            self.assertEqual(flag["denominator"], 40)
            self.assertTrue((self.root / "runs" / "base_results.zip").is_file())
            # A completed run is never regenerated.
            with mock.patch.object(hf_backend, "HFBackend", side_effect=AssertionError("reloaded")):
                self.assertEqual(pe.main(["evaluate", "--split", "dev", "--inputs", str(inputs),
                                          "--run-dir", str(self.root / "runs" / "base")]), 0)
            changed = pe.config_for("dev")
            changed["seed"] = 22
            with mock.patch.object(pe, "config_for", return_value=changed), \
                    mock.patch.object(hf_backend, "HFBackend", side_effect=AssertionError("reloaded")):
                with self.assertRaisesRegex(ValueError, "Completed run identity differs"):
                    pe.main(["evaluate", "--split", "dev", "--inputs", str(inputs),
                             "--run-dir", str(self.root / "runs" / "base")])


class BaselineRecordAndLockTests(unittest.TestCase):
    """Amendment 2 items 5 (stale lock, Sol R7) and 6 (baseline first, Sol R8) through the evaluate command."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.inputs = self.root / "inputs"
        self.inputs.mkdir()
        (self.inputs / "dev.v2.json").write_bytes((ROOT / "phase2" / "dev.v2.json").read_bytes())
        (self.inputs / "identities.json").write_text(json.dumps(pe.split_identities(ROOT)))
        self.manifest = self.inputs / "IMPLEMENTATION_MANIFEST.md"
        self.manifest.write_text(FIXTURE_MANIFEST_TEXT)
        self.run_dir = self.root / "baseline_dev" / "base"

    def tearDown(self):
        self.folder.cleanup()

    def evaluate(self, *extra, backend=None):
        with mock.patch.object(hf_backend, "HFBackend", backend or fake_backend(None)), mock.patch("sys.stdout", io.StringIO()) as out:
            code = pe.main(["evaluate", "--split", "dev", "--inputs", str(self.inputs), "--run-dir", str(self.run_dir), *extra])
        return code, out.getvalue()

    def test_complete_baseline_is_recorded_once_and_accepted_by_the_trainer(self):
        code, out = self.evaluate("--implementation-manifest", str(self.manifest))
        self.assertEqual(code, 0)
        record = json.loads((self.run_dir.parent / tp.BASELINE_RECORD).read_text())
        archive = self.run_dir.parent / "base_results.zip"
        self.assertEqual((record["status"], record["completed"], record["unresolved"], record["adapter"], record["mode"]),
                         ("COMPLETE", 120, 0, None, "phase2_dev"))
        self.assertEqual(record["results_zip_sha256"], hashlib.sha256(archive.read_bytes()).hexdigest())
        self.assertEqual(record["implementation_manifest_sha256"], MANIFEST_SHA)
        self.assertIn("Unchanged-DEV baseline recorded", out)
        self.assertEqual(tp.verify_baseline(self.run_dir.parent, MANIFEST_SHA), record["results_zip_sha256"])
        with self.assertRaisesRegex(tp.Refused, "another implementation manifest|not"):
            tp.verify_baseline(self.run_dir.parent, "0" * 64)
        before = archive.read_bytes()
        code, out = self.evaluate("--implementation-manifest", str(self.manifest),
                                  backend=mock.MagicMock(side_effect=AssertionError("reloaded")))
        self.assertEqual(code, 0)
        self.assertIn("baseline record kept", out)
        self.assertEqual(archive.read_bytes(), before)  # the recorded ZIP is never rewritten
        other = self.inputs / "OTHER_MANIFEST.md"
        other.write_text(FIXTURE_MANIFEST_TEXT + "\n")
        with self.assertRaisesRegex(ValueError, "refusing to mix implementations"):
            self.evaluate("--implementation-manifest", str(other))

    def test_no_baseline_record_without_a_manifest_or_for_an_incomplete_run(self):
        dataset, splits = pe.inputs((ROOT / "phase2" / "dev.v2.json").read_bytes(), "dev", pe.split_identities(ROOT))
        self.assertEqual(self.evaluate()[0], 0)
        self.assertFalse((self.run_dir.parent / tp.BASELINE_RECORD).exists())
        with self.assertRaisesRegex(tp.Refused, "Phase2_Baseline_DEV"):
            tp.verify_baseline(self.run_dir.parent, MANIFEST_SHA)
        unbound = self.root / "unbound" / "base"  # started without a manifest: cannot become a baseline later
        run(unbound, dataset, splits, pe.config_for("dev"), fake_backend(None)(), max_items=5)
        self.run_dir = unbound
        with self.assertRaisesRegex(ValueError, "without a recorded implementation manifest"):
            self.evaluate("--implementation-manifest", str(self.manifest))
        self.run_dir = self.root / "partial" / "base"
        with mock.patch.object(pe, "run", side_effect=lambda *a, **k: run(*a, **dict(k, max_items=3))):
            self.assertEqual(self.evaluate("--implementation-manifest", str(self.manifest))[0], 1)
        self.assertFalse((self.run_dir.parent / tp.BASELINE_RECORD).exists())

    def test_stale_lock_is_recovered_only_when_requested_and_nothing_is_regenerated(self):
        dataset, splits = pe.inputs((ROOT / "phase2" / "dev.v2.json").read_bytes(), "dev", pe.split_identities(ROOT))
        run(self.run_dir, dataset, splits, pe.config_for("dev"), fake_backend(None)(), max_items=4)
        stored = {p.name: p.read_bytes() for p in (self.run_dir / "journal").glob("*.json")}
        (self.run_dir / "RUNNING.lock").write_text("2026-11-04T01:02:03+00:00")  # left by a killed runtime
        with self.assertRaisesRegex(ValueError, "Run lock exists"):
            self.evaluate()
        self.assertFalse((self.run_dir.parent / "base_lock_recoveries.jsonl").exists())
        code, out = self.evaluate("--recover-stale-lock")
        self.assertEqual(code, 0)
        self.assertIn("removed the stale RUNNING.lock", out)
        records = [json.loads(line) for line in (self.run_dir.parent / "base_lock_recoveries.jsonl").read_text().splitlines()]
        self.assertEqual(len(records), 1)
        self.assertEqual((records[0]["event"], records[0]["lock_created_at"], records[0]["journal_records_kept"],
                          records[0]["operator_confirmed_no_active_writer"]),
                         ("stale_lock_recovered", "2026-11-04T01:02:03+00:00", 4, True))
        self.assertRegex(records[0]["at"], r"^\d{4}-\d\d-\d\dT")
        for name, content in stored.items():  # stored outputs kept byte for byte, never regenerated
            self.assertEqual((self.run_dir / "journal" / name).read_bytes(), content)
        attempts = [json.loads(p.read_text()) for p in (self.run_dir / "journal").glob("*.json")]
        self.assertEqual((len(attempts), {a["attempt_number"] for a in attempts}), (120, {1}))
        self.assertFalse((self.run_dir / "RUNNING.lock").exists())
        code, out = self.evaluate("--recover-stale-lock")  # nothing to recover: no new record
        self.assertIn("nothing to recover", out)
        self.assertEqual(len((self.run_dir.parent / "base_lock_recoveries.jsonl").read_text().splitlines()), 1)

    def test_engine_recover_lock_still_requires_confirmation(self):
        (self.root / "RUNNING.lock").write_text("x")
        with self.assertRaises(ValueError):
            live_engine.recover_lock(self.root)
        self.assertTrue((self.root / "RUNNING.lock").exists())


# A fixture implementation manifest that is true of this repository (one hashed file), so freeze_manifest's recheck
# against the real implementation passes; the notebook tests swap in the real manifest.
FIXTURE_MANIFEST_TEXT = ("# Implementation manifest (TEST FIXTURE)\n\n```json\n" + json.dumps(
    {"schema": tp.MANIFEST_SCHEMA, "files": {tp.EXPOSURE_ORDER_PATH: tp.EXPOSURE_ORDER_SHA256}}) + "\n```\n")
_FIXTURE_DIR = tempfile.mkdtemp()
atexit.register(shutil.rmtree, _FIXTURE_DIR, True)
MANIFEST_PATH = Path(_FIXTURE_DIR) / "IMPLEMENTATION_MANIFEST.md"
MANIFEST_PATH.write_text(FIXTURE_MANIFEST_TEXT)
MANIFEST_SHA = H(FIXTURE_MANIFEST_TEXT)
BASELINE_SHA = "b" * 64  # results-ZIP SHA-256 of the unchanged-DEV run every attempt was started with
EXPOSURE_SHA = hashlib.sha256((ROOT / tp.EXPOSURE_ORDER_PATH).read_bytes()).hexdigest()
SHARDS = {"model-00001-of-00003.safetensors": "5" * 64}
DATA_SHA = "d"


def identity():
    return dict(IDENTITY, implementation_manifest_sha256=MANIFEST_SHA, baseline_dev_results_zip_sha256=BASELINE_SHA,
                exposure_order_file_sha256=EXPOSURE_SHA)


def freeze(train, **kwargs):
    """freeze_manifest against MANIFEST_PATH, rechecked against this repository."""
    return pe.freeze_manifest(train, manifest_path=MANIFEST_PATH, root=ROOT, **kwargs)


def make_run(train, arm, seed, slot, attempt=1, **changes):
    """A valid training attempt folder (final_adapter.json + adapter files) as train_phase2 writes it."""
    folder = pe.attempt_dir(train, arm, seed, attempt)
    (folder / "final_adapter").mkdir(parents=True, exist_ok=True)
    weights = f"weights {arm} {seed} {attempt}"
    settings = json.dumps({"peft_type": "LORA", "r": 16})
    (folder / "final_adapter" / "adapter_model.safetensors").write_text(weights)
    (folder / "final_adapter" / "adapter_config.json").write_text(settings)
    record = {"arm": arm, "seed": seed, "slot": slot, "attempt": attempt, "status": "COMPLETE", "updates": 60,
              "steps": {"windows": 60, "attempted": 60, "successful": 60, "cursor": 960}, "scaler_skips": 0,
              "saved_parameters_finite": True, "resumed": False, "valid_for_gate": True,
              "recipe_sha256": ts.digest(tp.RECIPE), "base_revision": pe.MODEL_REVISION,
              "adapter_model_sha256": H(weights), "adapter_config_sha256": H(settings),
              "initial_adapter_sha256": f"init-{seed}", "order_sha256": f"order-{seed}", "data_sha256": DATA_SHA,
              "implementation_manifest_sha256": MANIFEST_SHA, "exposure_order_file_sha256": EXPOSURE_SHA,
              "baseline_dev_results_zip_sha256": BASELINE_SHA, "base_weight_shards_sha256": SHARDS}
    record.update(changes)
    (folder / "final_adapter.json").write_text(json.dumps(record))
    (folder / "train_report.json").write_text(json.dumps({"status": "COMPLETE"}))
    return record


def log_attempt(train, arm, seed, slot, outcome):
    """Log the plan's next run (it must be arm/seed/slot) the way the trainer does; a valid one gets its run folder."""
    log = Path(train) / tp.ATTEMPT_LOG
    action = tp.next_run(tp.plan(tp.read_log(log)))
    assert (action["kind"], action["arm"], action["seed"], action["slot"]) == ("train", arm, seed, slot), action
    tp.log_event(log, "start", arm=arm, seed=seed, slot=slot, attempt=action["attempt"], identity=identity())
    if outcome == "valid":
        make_run(train, arm, seed, slot, action["attempt"])
    tp.log_event(log, "finish", arm=arm, seed=seed, slot=slot, attempt=action["attempt"], outcome=outcome)
    return action["attempt"]


def complete_slots(train, slots=(11, 22, 33)):
    for slot in slots:
        for arm in tp.ARM_ORDER:
            log_attempt(train, arm, slot, slot, "valid")


def exhaust_slot(train, slot):
    for seed in (slot, 44, 55):
        for _ in range(2):
            log_attempt(train, "EC", seed, slot, "infrastructure")


class GateTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.train = Path(self.folder.name) / "train"
        complete_slots(self.train)
        self.frozen = freeze(self.train)

    def tearDown(self):
        self.folder.cleanup()

    def test_freeze_manifest_and_gate_with_three_triplets(self):
        self.assertEqual((self.frozen["S"], self.frozen["confirmatory"], self.frozen["descriptive_only"]), (3, True, False))
        self.assertEqual(self.frozen["retained_seeds"], [{"slot": s, "seed": s} for s in (11, 22, 33)])
        self.assertEqual((self.frozen["implementation_manifest_sha256"], self.frozen["exposure_order_file_sha256"]), (MANIFEST_SHA, EXPOSURE_SHA))
        self.assertEqual(self.frozen["attempt_log_sha256"], ts.file_sha256(self.train / tp.ATTEMPT_LOG))
        result = pe.gate(self.frozen, self.train, expected_data_sha256="d")
        self.assertEqual(len(result), 9)
        self.assertEqual({(a["arm"], a["seed"]) for a, _ in result}, {(arm, s) for arm in tp.ARMS for s in (11, 22, 33)})
        text = "# Frozen\n\n```json\n" + json.dumps(self.frozen) + "\n```\n"
        self.assertEqual(pe.parse_frozen(text), self.frozen)

    def refuses(self, pattern, frozen=None):
        with self.assertRaisesRegex(ValueError, "REFUSED(.|\n)*" + pattern):
            pe.gate(frozen or self.frozen, self.train, expected_data_sha256="d")

    def test_missing_changed_or_misrecorded_adapters_are_refused(self):
        (pe.attempt_dir(self.train, "EC", 33, 1) / "final_adapter" / "adapter_model.safetensors").write_text("tampered")
        self.refuses("EC-s33 attempt 1: files match the frozen hashes")
        make_run(self.train, "EC", 33, 33)
        (pe.attempt_dir(self.train, "EE", 11, 1) / "final_adapter" / "adapter_config.json").unlink()
        self.refuses("EE-s11 attempt 1: files match the frozen hashes")
        make_run(self.train, "EE", 11, 11)
        frozen = copy.deepcopy(self.frozen)
        frozen["adapters"][0]["adapter_model_sha256"] = "0" * 64
        self.refuses("recorded hashes", frozen)
        (pe.attempt_dir(self.train, "ER", 22, 1) / "final_adapter.json").unlink()
        self.refuses("ER-s22 attempt 1: final_adapter.json not found")

    def test_invalid_runs_are_refused(self):
        for changes, pattern in (({"resumed": True}, "valid run"), ({"valid_for_gate": False}, "valid run"),
                                 ({"steps": {"windows": 60, "attempted": 61, "successful": 60, "cursor": 960}}, "valid run"),
                                 ({"scaler_skips": 1}, "valid run"), ({"saved_parameters_finite": False}, "valid run"),
                                 ({"recipe_sha256": "x"}, "recipe"), ({"implementation_manifest_sha256": "f" * 64}, "implementation manifest"),
                                 ({"exposure_order_file_sha256": "0" * 64}, "exposure order file"),
                                 ({"base_weight_shards_sha256": {}}, "base weight shards"), ({"data_sha256": "x"}, "TRAIN data"),
                                 ({"initial_adapter_sha256": "other"}, "seed 11: arms differ in initial_adapter_sha256")):
            with self.subTest(changes=changes):
                make_run(self.train, "ER", 11, 11, **changes)
                self.refuses(pattern)
                make_run(self.train, "ER", 11, 11)
        pe.gate(self.frozen, self.train, expected_data_sha256="d")

    def test_attempt_log_changed_after_the_freeze_is_refused(self):
        tp.log_event(self.train / tp.ATTEMPT_LOG, "start", arm="EE", seed=44, slot=11, attempt=1)
        self.refuses("attempt log")

    def test_training_reports_are_frozen_and_checked(self):
        path = pe.attempt_dir(self.train, "EC", 11, 1) / "train_report.json"
        name = str(path.relative_to(self.train))
        self.assertEqual(self.frozen["training_logs_sha256"][name], ts.file_sha256(path))
        path.write_text(json.dumps({"status": "FAILED", "failure_class": "numerical"}))
        self.refuses("training log")
        with self.assertRaisesRegex(ValueError, "training report"):
            freeze(self.train)

    def test_freeze_without_training_log_hashes_is_refused(self):
        frozen = copy.deepcopy(self.frozen)
        frozen.pop("training_logs_sha256")
        with self.assertRaisesRegex(ValueError, "training_logs_sha256"):
            pe.parse_frozen("```json\n" + json.dumps(frozen) + "\n```")

    def test_driver_requires_the_full_gate_before_reading_test_data(self):
        with mock.patch.object(pe, "inputs") as load_inputs:
            with self.assertRaisesRegex(ValueError, "--train-root"):
                pe.main(["evaluate", "--split", "final_test", "--inputs", "absent", "--run-dir", "absent"])
            load_inputs.assert_not_called()

    def test_driver_authorizes_only_frozen_adapters(self):
        inputs = Path(self.folder.name) / "inputs"
        inputs.mkdir()
        (inputs / "IMPLEMENTATION_MANIFEST.md").write_text(FIXTURE_MANIFEST_TEXT)
        (inputs / "PREREGISTRATION.md").write_bytes((ROOT / "phase2" / "PREREGISTRATION.md").read_bytes())
        baseline = Path(self.folder.name) / "baseline_dev"
        zip_sha = write_baseline(baseline, MANIFEST_SHA)
        frozen = dict(self.frozen, baseline_dev_results_zip_sha256=zip_sha)
        (inputs / "ADAPTERS_FROZEN.md").write_text("```json\n" + json.dumps(frozen) + "\n```")
        args = pe.argparse.Namespace(train_root=self.train, inputs=inputs, adapter_record=None, adapter_dir=None, baseline_dir=None)
        with self.assertRaisesRegex(ValueError, "--baseline-dir"):
            pe.authorize_final_test(args)
        args.baseline_dir = baseline
        with self.assertRaisesRegex(ValueError, "without the frozen unchanged-DEV baseline"):  # log records BASELINE_SHA
            pe.authorize_final_test(args)
        frozen = self.frozen
        (inputs / "ADAPTERS_FROZEN.md").write_text("```json\n" + json.dumps(frozen) + "\n```")
        with self.assertRaisesRegex(ValueError, "unchanged-DEV baseline: .*differs from the frozen"):
            pe.authorize_final_test(args)
        with mock.patch.object(tp, "verify_baseline", return_value=BASELINE_SHA):
            self.assertEqual(pe.authorize_final_test(args), frozen)
        folder = pe.attempt_dir(self.train, "EC", 11, 1)
        args.adapter_record, args.adapter_dir = folder / "final_adapter.json", folder / "final_adapter"
        with mock.patch.object(tp, "verify_baseline", return_value=BASELINE_SHA):
            self.assertEqual(pe.authorize_final_test(args), frozen)
            args.adapter_dir = inputs / "other_adapter"
            with self.assertRaisesRegex(ValueError, "outside the frozen set"):
                pe.authorize_final_test(args)

    def test_reduced_s_is_descriptive_only(self):
        folder = Path(self.folder.name) / "reduced"
        complete_slots(folder, slots=(11, 22))
        exhaust_slot(folder, 33)
        frozen = freeze(folder)
        self.assertEqual((frozen["S"], frozen["confirmatory"], frozen["descriptive_only"]), (2, False, True))
        self.assertEqual(len(pe.gate(frozen, folder)), 6)
        for change, pattern in ((lambda f: f.update(descriptive_only=False), "descriptive_only"),
                                (lambda f: f.update(confirmatory=True), "descriptive_only"),
                                (lambda f: f.pop("descriptive_only"), "descriptive_only")):
            broken = copy.deepcopy(frozen)
            change(broken)
            with self.subTest(pattern=pattern), self.assertRaisesRegex(ValueError, pattern):
                pe.parse_frozen("```json\n" + json.dumps(broken) + "\n```")

    def test_s_zero_or_open_or_halted_study_never_freezes(self):
        folder = Path(self.folder.name) / "zero"
        for slot in (11, 22):
            for seed in ((slot,) if slot == 22 else (11, 44, 55)):
                for _ in range(2):
                    log_attempt(folder, "EC", seed, slot, "infrastructure")
        with self.assertRaisesRegex(ValueError, "still open"):
            freeze(folder)
        zero = copy.deepcopy(self.frozen)
        zero.update(S=0, retained_seeds=[], adapters=[], confirmatory=False, descriptive_only=True)
        with self.assertRaisesRegex(ValueError, "S = 0"):
            pe.parse_frozen("```json\n" + json.dumps(zero) + "\n```")
        halted = Path(self.folder.name) / "halted"
        complete_slots(halted, slots=(11, 22))
        log_attempt(halted, "EC", 33, 33, "numerical")
        with self.assertRaisesRegex(ValueError, "halted"):
            freeze(halted)

    def test_manifest_parsing(self):
        for change in (lambda f: f["adapters"].pop(), lambda f: f.update(base_revision="0" * 40),
                       lambda f: f["adapters"][0].update(arm="ER"), lambda f: f["adapters"][0].update(seed=12),
                       lambda f: f["adapters"][0].update(attempt=3), lambda f: f.update(schema="phase2-adapters-frozen-1"),
                       lambda f: f.update(S=2), lambda f: f.update(descriptive_only=True),
                       lambda f: f["retained_seeds"][0].update(seed=22), lambda f: f["retained_seeds"][0].update(seed=55),
                       lambda f: f.update(implementation_manifest_sha256=None),
                       lambda f: f.pop("baseline_dev_results_zip_sha256"), lambda f: f.update(schema="phase2-adapters-frozen-2")):
            broken = copy.deepcopy(self.frozen)
            change(broken)
            with self.subTest(change=change), self.assertRaises(ValueError):
                pe.parse_frozen("```json\n" + json.dumps(broken) + "\n```")
        with self.assertRaises(ValueError):
            pe.parse_frozen("no block")

    def test_reserve_seed_triplet_replaces_a_slot(self):
        folder = Path(self.folder.name) / "reserve"
        log_attempt(folder, "EC", 11, 11, "valid")
        log_attempt(folder, "ER", 11, 11, "infrastructure")
        log_attempt(folder, "ER", 11, 11, "infrastructure")
        for arm in tp.ARM_ORDER:  # slot 11 is settled on reserve 44 before slot 22 starts (Amendment 2 item 4)
            log_attempt(folder, arm, 44, 11, "valid")
        complete_slots(folder, slots=(22, 33))
        frozen = freeze(folder)
        self.assertEqual(frozen["retained_seeds"], [{"slot": 11, "seed": 44}, {"slot": 22, "seed": 22}, {"slot": 33, "seed": 33}])
        self.assertEqual(sorted({a["seed"] for a in frozen["adapters"]}), [22, 33, 44])
        self.assertEqual(len(pe.gate(frozen, folder)), 9)

    def test_freeze_rechecks_the_manifest_against_the_real_files_and_the_start_events(self):
        """Amendment 2 item 7 (Sol R4): an asserted manifest hash is not enough to freeze."""
        stale = Path(self.folder.name) / "stale_manifest.md"
        stale.write_text(FIXTURE_MANIFEST_TEXT.replace(tp.EXPOSURE_ORDER_SHA256, "0" * 64))
        with self.assertRaisesRegex(ValueError, "differs from the real implementation: phase2/EXPOSURE_ORDER.json"):
            pe.freeze_manifest(self.train, manifest_path=stale, root=ROOT)
        other = Path(self.folder.name) / "other_manifest.md"  # true of the repository, but not what the attempts ran
        other.write_text(FIXTURE_MANIFEST_TEXT + "\n")
        with self.assertRaisesRegex(ValueError, "another implementation manifest"):
            pe.freeze_manifest(self.train, manifest_path=other, root=ROOT)
        arbitrary = Path(self.folder.name) / "arbitrary"  # Sol's probe: runs claiming eee...eee everywhere
        with mock.patch(__name__ + ".MANIFEST_SHA", "e" * 64):
            complete_slots(arbitrary)
        with self.assertRaisesRegex(ValueError, "another implementation manifest"):
            freeze(arbitrary)
        mixed = Path(self.folder.name) / "mixed"  # start events right, a retained record wrong
        complete_slots(mixed)
        make_run(mixed, "ER", 22, 22, implementation_manifest_sha256="e" * 64)
        with self.assertRaisesRegex(ValueError, "differ in"):
            freeze(mixed)

    def test_freeze_records_the_baseline_and_the_gate_requires_it(self):
        """Amendment 2 item 6 (Sol R8)."""
        self.assertEqual(self.frozen["baseline_dev_results_zip_sha256"], BASELINE_SHA)
        baseline = Path(self.folder.name) / "baseline_dev"
        zip_sha = write_baseline(baseline, MANIFEST_SHA)
        with self.assertRaisesRegex(ValueError, "Unchanged-DEV baseline: .*differs from the frozen"):
            freeze(self.train, baseline_dir=baseline)
        good = Path(self.folder.name) / "good"
        with mock.patch(__name__ + ".BASELINE_SHA", zip_sha):
            complete_slots(good)
            frozen = freeze(good, baseline_dir=baseline)
        self.assertEqual(frozen["baseline_dev_results_zip_sha256"], zip_sha)
        self.assertEqual(len(pe.gate(frozen, good, baseline_dir=baseline)), 9)
        (baseline / "base_results.zip").write_bytes(b"rerun")
        with self.assertRaisesRegex(ValueError, "REFUSED(.|\n)*unchanged-DEV baseline"):
            pe.gate(frozen, good, baseline_dir=baseline)
        with self.assertRaisesRegex(ValueError, "REFUSED(.|\n)*without the frozen unchanged-DEV baseline"):
            pe.gate(dict(frozen, baseline_dev_results_zip_sha256="0" * 64), good)
        no_baseline = Path(self.folder.name) / "no_baseline"
        with mock.patch(__name__ + ".BASELINE_SHA", None):
            complete_slots(no_baseline)
        with self.assertRaisesRegex(ValueError, "no unchanged-DEV baseline"):
            freeze(no_baseline)

    def test_preregistration_hash_check(self):
        text = (ROOT / "phase2" / "PREREGISTRATION.md").read_bytes()
        digest = hashlib.sha256(text).hexdigest()
        self.assertEqual(pe.check_preregistration(text, digest), digest)
        for expected in (None, "0" * 64):
            with self.assertRaisesRegex(ValueError, "FINAL_TEST refused"):
                pe.check_preregistration(text, expected)
        with self.assertRaisesRegex(ValueError, "FINAL_TEST refused"):
            pe.check_preregistration(text + b"\nedit", digest)


class SealedEvaluationTests(unittest.TestCase):
    """Amendment 1 item 14: FINAL_TEST runs print only completion, checksum and infrastructure status."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.inputs = self.root / "inputs"
        self.inputs.mkdir()
        self.dev = (ROOT / "phase2" / "dev.v2.json").read_bytes()
        (self.inputs / "identities.json").write_text(json.dumps(pe.split_identities(ROOT)))

    def tearDown(self):
        self.folder.cleanup()

    def assert_sealed(self, text):
        for leak in ("accuracy", "Accuracy", "FINAL:", "correct", "%", "rendering", "DV0", "summary", "Wilson"):
            self.assertNotIn(leak, text)
        self.assertIn("SEALED", text)

    def test_final_test_split_is_always_sealed_and_never_regenerated(self):
        # Uses DEV bytes under the FINAL_TEST file name (no FINAL_TEST content is read in this test).
        (self.inputs / "final_test.v3.json").write_bytes(self.dev)
        original_inputs, original_config = pe.inputs, pe.config_for
        run_dir = self.root / "runs" / "base"
        with mock.patch.object(pe, "inputs", lambda raw, split, ids: original_inputs(raw, "dev", ids)), \
                mock.patch.object(pe, "authorize_final_test", return_value=None), \
                mock.patch.object(pe, "config_for", lambda split, adapter=None: original_config("dev", adapter)), \
                mock.patch.object(hf_backend, "HFBackend", fake_backend(None)), mock.patch("sys.stdout", io.StringIO()) as out:
            self.assertEqual(pe.main(["evaluate", "--split", "final_test", "--inputs", str(self.inputs), "--run-dir", str(run_dir)]), 0)
        self.assert_sealed(out.getvalue())
        status = json.loads((self.root / "runs" / "base_status.json").read_text())
        self.assertEqual((status["status"], status["completed"], status["expected"], status["unresolved"], status["infrastructure_failures"]),
                         ("COMPLETE", 120, 120, 0, 0))
        archive = self.root / "runs" / "base_results.zip"
        self.assertEqual(status["results_zip_sha256"], hashlib.sha256(archive.read_bytes()).hexdigest())
        self.assertFalse((self.root / "runs" / "base_ceiling_flag.json").exists())
        journal = sorted(p.name for p in (run_dir / "journal").glob("*.json"))
        with mock.patch.object(pe, "inputs", lambda raw, split, ids: original_inputs(raw, "dev", ids)), \
                mock.patch.object(pe, "authorize_final_test", return_value=None), \
                mock.patch.object(pe, "config_for", lambda split, adapter=None: original_config("dev", adapter)), \
                mock.patch.object(hf_backend, "HFBackend", side_effect=AssertionError("regenerated")), mock.patch("sys.stdout", io.StringIO()) as out:
            self.assertEqual(pe.main(["evaluate", "--split", "final_test", "--inputs", str(self.inputs), "--run-dir", str(run_dir)]), 0)
        self.assert_sealed(out.getvalue())
        self.assertEqual(sorted(p.name for p in (run_dir / "journal").glob("*.json")), journal)

    def test_sealed_flag_and_unsealed_dev(self):
        (self.inputs / "dev.v2.json").write_bytes(self.dev)
        with mock.patch.object(hf_backend, "HFBackend", fake_backend(None)), mock.patch("sys.stdout", io.StringIO()) as out:
            pe.main(["evaluate", "--split", "dev", "--sealed", "--inputs", str(self.inputs), "--run-dir", str(self.root / "s" / "base")])
        self.assert_sealed(out.getvalue())
        with mock.patch.object(hf_backend, "HFBackend", fake_backend(None)), mock.patch("sys.stdout", io.StringIO()) as out:
            pe.main(["evaluate", "--split", "dev", "--inputs", str(self.inputs), "--run-dir", str(self.root / "u" / "base")])
        self.assertIn("ceiling-risk proxy", out.getvalue())
        self.assertIn("Accuracy", out.getvalue())

    def test_engine_never_retries_a_generated_response(self):
        dataset, splits = pe.inputs(self.dev, "dev", pe.split_identities(ROOT))
        run_dir = self.root / "r"
        run(run_dir, dataset, splits, pe.config_for("dev"), fake_backend(None)(), max_items=3)
        first = sorted(p.name for p in (run_dir / "journal").glob("*.json"))
        self.assertEqual(len(first), 3)
        run(run_dir, dataset, splits, pe.config_for("dev"), fake_backend(None)())
        attempts = [json.loads(p.read_text()) for p in (run_dir / "journal").glob("*.json")]
        self.assertTrue(all(a["attempt_number"] == 1 and a["status"] == "generated" for a in attempts))
        self.assertEqual(len(attempts), 120)


class SecondBackboneTests(unittest.TestCase):
    def test_phase2_modes_refuse_any_model_but_qwen3_4b(self):
        for mode in ("phase2_dev", "phase2_final_test"):
            config = default_config(mode, "meta-llama/Llama-3.2-3B-Instruct")
            config.update(model_revision="0" * 40, tokenizer_revision="0" * 40)
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "Amendment 1 item 15"):
                validate_config(config)
        self.assertEqual(pe.config_for("dev")["model_id"], "Qwen/Qwen3-4B")
        self.assertNotIn("llama", (ROOT / "t4_smoke" / "phase2_eval.py").read_text().lower().replace("llama-3.2-3b", ""))


if __name__ == "__main__":
    unittest.main()
