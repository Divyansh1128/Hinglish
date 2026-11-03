"""Model-free tests of Phase-2 evaluation inputs, the engine modes and the FINAL_TEST gate."""
import copy
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from t4_smoke import phase2_eval as pe
from t4_smoke import train_phase2 as tp
from t4_smoke import train_smoke as ts
from hinglish_pilot import hf_backend
from hinglish_pilot.data import validate
from hinglish_pilot.engine import FakeBackend, default_config, run
from hinglish_pilot.report import analyze, export

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
        dataset, splits = pe.inputs((ROOT / "phase2" / "final_test.v3.json").read_bytes(), "final_test", self.identities)
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


class GateTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.train = Path(self.folder.name) / "train"
        self.entries = []
        for seed in (11, 22, 33):
            for arm in tp.ARMS:
                self.entries.append(self.make(arm, seed))
        self.frozen = {"schema": pe.FROZEN_SCHEMA, "base_model": pe.MODEL_ID, "base_revision": pe.MODEL_REVISION,
                       "adapters": self.entries}

    def tearDown(self):
        self.folder.cleanup()

    def make(self, arm, seed, attempt=1, **changes):
        folder = pe.attempt_dir(self.train, arm, seed, attempt)
        (folder / "final_adapter").mkdir(parents=True, exist_ok=True)
        weights = f"weights {arm} {seed} {attempt}"
        settings = json.dumps({"peft_type": "LORA", "r": 16})
        (folder / "final_adapter" / "adapter_model.safetensors").write_text(weights)
        (folder / "final_adapter" / "adapter_config.json").write_text(settings)
        record = {"arm": arm, "seed": seed, "attempt": attempt, "status": "COMPLETE", "updates": 60, "resumed": False,
                  "recipe_sha256": ts.digest(tp.RECIPE), "base_revision": pe.MODEL_REVISION,
                  "adapter_model_sha256": H(weights), "adapter_config_sha256": H(settings),
                  "initial_adapter_sha256": f"init-{seed}", "order_sha256": f"order-{seed}", "data_sha256": "d"}
        record.update(changes)
        (folder / "final_adapter.json").write_text(json.dumps(record))
        return pe.adapter_record(record)

    def test_gate_passes_with_all_nine(self):
        result = pe.gate(self.frozen, self.train, expected_data_sha256="d")
        self.assertEqual(len(result), 9)
        self.assertEqual({(a["arm"], a["seed"]) for a, _ in result}, {(arm, s) for arm in tp.ARMS for s in (11, 22, 33)})

    def refuses(self, pattern):
        with self.assertRaisesRegex(ValueError, "REFUSED(.|\n)*" + pattern):
            pe.gate(self.frozen, self.train, expected_data_sha256="d")

    def test_missing_adapter_is_refused(self):
        (pe.attempt_dir(self.train, "ER", 22, 1) / "final_adapter.json").unlink()
        self.refuses("ER-s22 attempt 1: final_adapter.json not found")

    def test_changed_weights_are_refused(self):
        (pe.attempt_dir(self.train, "EC", 33, 1) / "final_adapter" / "adapter_model.safetensors").write_text("tampered")
        self.refuses("EC-s33 attempt 1: files match the frozen hashes")

    def test_missing_weights_are_refused(self):
        (pe.attempt_dir(self.train, "EE", 11, 1) / "final_adapter" / "adapter_config.json").unlink()
        self.refuses("EE-s11 attempt 1: files match the frozen hashes")

    def test_manifest_hash_mismatch_is_refused(self):
        self.frozen["adapters"][0] = dict(self.frozen["adapters"][0], adapter_model_sha256="0" * 64)
        self.refuses("recorded hashes")

    def test_resumed_incomplete_or_unpaired_runs_are_refused(self):
        self.make("ER", 11, resumed=True)
        self.refuses("not resumed")
        self.make("ER", 11)
        self.make("EC", 11, updates=50, status="FAILED")
        self.refuses("EC-s11 attempt 1: complete")
        self.make("EC", 11, initial_adapter_sha256="other")
        self.refuses("seed 11: arms differ in initial_adapter_sha256")
        self.make("EC", 11, recipe_sha256="x")
        self.refuses("recipe")

    def test_manifest_parsing(self):
        text = "# Frozen\n\n```json\n" + json.dumps(self.frozen) + "\n```\n"
        self.assertEqual(pe.parse_frozen(text), self.frozen)
        for change in (lambda f: f["adapters"].pop(), lambda f: f.update(base_revision="0" * 40),
                       lambda f: f["adapters"][0].update(arm="ER"), lambda f: f["adapters"][0].update(seed=12),
                       lambda f: f.update(schema="other")):
            broken = copy.deepcopy(self.frozen)
            change(broken)
            with self.subTest(change=change), self.assertRaises(ValueError):
                pe.parse_frozen("```json\n" + json.dumps(broken) + "\n```")
        with self.assertRaises(ValueError):
            pe.parse_frozen("no block")

    def test_freeze_manifest_from_records_and_reserve_seeds(self):
        records = [json.loads(p.read_text()) for p in sorted(self.train.rglob("final_adapter.json"))]
        self.assertEqual(pe.freeze_manifest(records)["adapters"], sorted(self.entries, key=lambda a: (a["seed"], a["arm"])))
        for arm in tp.ARMS:
            self.make(arm, 44, attempt=1)
        records = [json.loads(p.read_text()) for p in sorted(self.train.rglob("final_adapter.json")) if "-s22" not in str(p)]
        frozen = pe.freeze_manifest(records)
        self.assertEqual(sorted({a["seed"] for a in frozen["adapters"]}), [11, 33, 44])
        self.assertEqual(len(pe.gate(frozen, self.train)), 9)

    def test_preregistration_hash_check(self):
        text = (ROOT / "phase2" / "PREREGISTRATION.md").read_bytes()
        digest = hashlib.sha256(text).hexdigest()
        self.assertEqual(pe.check_preregistration(text, digest), digest)
        for expected in (None, "0" * 64):
            with self.assertRaisesRegex(ValueError, "FINAL_TEST refused"):
                pe.check_preregistration(text, expected)
        with self.assertRaisesRegex(ValueError, "FINAL_TEST refused"):
            pe.check_preregistration(text + b"\nedit", digest)


if __name__ == "__main__":
    unittest.main()
