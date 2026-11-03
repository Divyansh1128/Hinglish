"""Model-free tests of the Phase-2 training module (PREREGISTRATION §3, §10)."""
import copy
import hashlib
import io
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from t4_smoke import train_phase2 as tp
from t4_smoke import train_smoke as ts
from t4_smoke.test_labels import FakeTokenizer

ROOT = Path(__file__).resolve().parents[1]


class ScheduleTests(unittest.TestCase):
    def test_lr_at_the_preregistered_points(self):
        self.assertAlmostEqual(tp.lr_at(1), 1e-4 / 6, places=15)
        self.assertAlmostEqual(tp.lr_at(6), 1e-4, places=15)
        self.assertAlmostEqual(tp.lr_at(7), 1e-4 * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi / 54))), places=15)
        self.assertAlmostEqual(tp.lr_at(7), 9.9923867e-5, places=12)
        self.assertAlmostEqual(tp.lr_at(60), 1e-5, places=15)

    def test_warmup_linear_then_monotone_cosine(self):
        warm = [tp.lr_at(u) for u in range(1, 7)]
        for u, value in enumerate(warm, 1):
            self.assertAlmostEqual(value, 1e-4 * u / 6, places=15)
        decay = [tp.lr_at(u) for u in range(6, 61)]
        self.assertTrue(all(a > b for a, b in zip(decay, decay[1:])))
        self.assertAlmostEqual(tp.lr_at(33), 1e-4 * 0.55, places=15)  # cosine midpoint
        for bad in (0, 61):
            with self.assertRaises(ValueError):
                tp.lr_at(bad)

    def test_recipe_keeps_the_d021_recipe_and_d043_counts(self):
        for key, value in tp.RECIPE.items():
            if key in ts.RECIPE and key not in ("families", "updates", "lr_schedule", "data_order"):
                self.assertEqual(value, ts.RECIPE[key], key)
        recipe = tp.RECIPE
        self.assertEqual((recipe["families"], recipe["examples_per_arm"], recipe["passes"], recipe["updates_per_pass"],
                          recipe["updates"], recipe["accumulation"], recipe["lr"]), (160, 320, 3, 20, 60, 16, 1e-4))
        self.assertEqual(recipe["examples_per_arm"] * recipe["passes"], recipe["updates"] * recipe["accumulation"])
        self.assertEqual((tp.SEEDS, tp.RESERVE_SEEDS, recipe["checkpoint_every"]), ((11, 22, 33), (44, 55), 10))
        self.assertNotIn("seed", recipe)  # the run seed is a run argument, never a recipe constant


class DataTests(unittest.TestCase):
    def test_all_160_frozen_train_families_and_only_the_train_files_are_read(self):
        read = []
        original = Path.read_bytes

        def spy(path):
            read.append(path.resolve())
            return original(path)

        with mock.patch.object(Path, "read_bytes", spy):
            data = tp.phase2_dataset(ROOT)
        self.assertEqual(sorted(read), sorted((ROOT / name).resolve() for name in ts.TRAIN_FILES))
        families = tp.validate_phase2_data(data)
        self.assertEqual(len(families), 160)
        self.assertEqual(sum(f["source_file"] == "phase2/train_A.v2.json" for f in families), 80)
        self.assertTrue(all(f["split_role"] == "CONFIRM_TRAIN" for f in families))
        self.assertEqual(data["sources"], ts.TRAIN_FILES)
        embedded = json.dumps(data)
        for marker in ("DV0", "FT0", '"gold"', "reference_equation"):
            self.assertNotIn(marker, embedded)

    def test_frozen_hashes_agree_with_the_frozen_notes(self):
        notes = (ROOT / "phase2" / "TRAIN_DEV_FROZEN.md").read_text()
        for name, digest in ts.TRAIN_FILES.items():
            self.assertIn(digest, notes)
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest)

    def test_hash_mismatch_and_tampering_are_refused(self):
        sources = ts.load_train_sources(ROOT)
        tampered = [(sources[0][0], sources[0][1].replace(b"FINAL", b"Final", 1)), sources[1]]
        with mock.patch.object(ts, "load_train_sources", return_value=tampered), \
                self.assertRaisesRegex(ValueError, "frozen SHA-256"):
            tp.phase2_dataset(ROOT)
        data = tp.phase2_dataset(ROOT)
        altered = copy.deepcopy(data)
        altered["families"][5]["completion"] += " "
        with self.assertRaisesRegex(ValueError, "changed"):
            tp.validate_phase2_data(altered)
        altered = copy.deepcopy(data)
        altered["families"].pop()
        with self.assertRaisesRegex(ValueError, "160"):
            tp.validate_phase2_data(altered)
        altered = copy.deepcopy(data)
        altered["sources"] = {"phase2/dev.v2.json": "0" * 64}
        with self.assertRaisesRegex(ValueError, "frozen TRAIN"):
            tp.validate_phase2_data(altered)

    def test_training_code_names_no_dev_or_final_test_file(self):
        for name in ("train_phase2.py", "train_smoke.py", "labels.py"):
            source = (ROOT / "t4_smoke" / name).read_text()
            for marker in ("dev.v2", "final_test.v", "dev.DRAFT", "final_test.DRAFT"):
                self.assertNotIn(marker, source, name)


class OrderAndPairingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.families = tp.validate_phase2_data(tp.phase2_dataset(ROOT))

    def test_order_follows_the_preregistered_rule(self):
        for seed in (11, 22, 33, 44, 55):
            for number in (1, 2, 3):
                expected = sorted((hashlib.sha256(f"phase2-D043:{seed}:{number}:{f['family_id']}".encode()).hexdigest(),
                                   f["family_id"]) for f in self.families)
                self.assertEqual(tp.pass_order(self.families, seed, number), [fid for _, fid in expected])

    def test_sequence_structure(self):
        sequence = tp.run_sequence(self.families, "EC", 11)
        self.assertEqual(len(sequence), 960)
        for number in range(3):
            block = sequence[number * 320:(number + 1) * 320]
            self.assertEqual(block[0::2], [(fid, "E") for fid in tp.pass_order(self.families, 11, number + 1)])
            self.assertEqual(block[1::2], [(fid, "C") for fid in tp.pass_order(self.families, 11, number + 1)])
        for update in range(1, 61):
            items = [sequence[c] for c in ts.update_cursors(update)]
            self.assertEqual(len({fid for fid, _ in items}), 8)
            self.assertEqual(tp.pass_of(update), (update - 1) // 20 + 1)

    def test_identical_order_across_arms_within_a_seed(self):
        for seed in tp.SEEDS + tp.RESERVE_SEEDS:
            sequences = {arm: tp.run_sequence(self.families, arm, seed) for arm in tp.ARMS}
            ids = {arm: [fid for fid, _ in seq] for arm, seq in sequences.items()}
            self.assertEqual(ids["EE"], ids["ER"])
            self.assertEqual(ids["EE"], ids["EC"])
            for arm, second in tp.ARMS.items():
                self.assertEqual([form for _, form in sequences[arm]], ["E", second] * 480)
            self.assertEqual(len({tp.order_sha256(self.families, seed)}), 1)
        self.assertNotEqual(tp.pass_order(self.families, 11, 1), tp.pass_order(self.families, 22, 1))
        self.assertNotEqual(tp.pass_order(self.families, 11, 1), tp.pass_order(self.families, 11, 2))
        self.assertNotEqual(tp.order_sha256(self.families, 11), tp.order_sha256(self.families, 22))

    def test_arms_share_targets_position_by_position(self):
        tokenizer = FakeTokenizer()
        examples = ts.build_examples(tokenizer, self.families)
        runs = {arm: tp.run_examples(examples, self.families, arm, 22) for arm in tp.ARMS}
        for index in range(0, 960, 7):
            targets = {arm: run[index]["input_ids"][run[index]["boundary_index"]:] for arm, run in runs.items()}
            self.assertEqual(targets["EE"], targets["ER"])
            self.assertEqual(targets["EE"], targets["EC"])
        self.assertEqual(runs["EE"][0]["input_ids"], runs["ER"][0]["input_ids"])  # probe example: E, identical
        self.assertNotEqual(runs["ER"][1]["input_ids"], runs["EC"][1]["input_ids"])

    def test_lora_initialisation_uses_the_run_seed_not_the_arm(self):
        seen = []

        def fake_smoke_load(torch):
            ts.seed_everything(torch, ts.RECIPE["seed"])  # what train_smoke.load_model does before get_peft_model
            return "model", [], True, {}

        with mock.patch.object(ts, "load_model", fake_smoke_load), \
                mock.patch.object(ts, "random") as fake_random:
            fake_random.seed.side_effect = seen.append
            torch = mock.MagicMock()
            for seed in (22, 22, 33):
                tp.load_model(torch, seed)
            self.assertEqual(seen, [22, 22, 33])
            torch.manual_seed.assert_called_with(33)
            torch.cuda.manual_seed_all.assert_called_with(33)
        self.assertEqual(ts.seed_everything.__name__, "seed_everything")  # restored

        def failing(torch):
            raise RuntimeError("load failed")

        with mock.patch.object(ts, "load_model", failing), self.assertRaises(RuntimeError):
            tp.load_model(mock.MagicMock(), 11)
        self.assertEqual(ts.seed_everything.__name__, "seed_everything")

    def test_pairing_report(self):
        base = {"order_sha256": "o", "initial_adapter_sha256": "i"}
        records = [dict(base, seed=11, arm=arm) for arm in tp.ARMS]
        self.assertEqual(tp.pairing(records)[11], {"arms": ["EC", "EE", "ER"], "same_order": True, "same_initial_adapter": True})
        records[1]["initial_adapter_sha256"] = "j"
        self.assertFalse(tp.pairing(records)[11]["same_initial_adapter"])


class RunTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.out = Path(self.folder.name) / "EC-s11" / "attempt-01"
        self.data = Path(self.folder.name) / "phase2_train.json"
        self.data.write_text(json.dumps(tp.phase2_dataset(ROOT)))

    def tearDown(self):
        self.folder.cleanup()

    def args(self, *extra):
        return ["train", "--arm", "EC", "--seed", "11", "--attempt", "1", "--data", str(self.data), "--out", str(self.out), *extra]

    def test_started_attempt_is_not_resumed_silently(self):
        self.out.mkdir(parents=True)
        (self.out / "train_report.json").write_text(json.dumps({"status": "FAILED"}))
        with mock.patch("sys.stderr", io.StringIO()) as err, mock.patch.object(ts, "gpu_setup") as setup:
            self.assertEqual(tp.main(self.args()), 2)
        setup.assert_not_called()
        self.assertIn("§10", err.getvalue())

    def test_completed_attempt_is_not_retrained(self):
        self.out.mkdir(parents=True)
        (self.out / "train_report.json").write_text(json.dumps({"status": "COMPLETE"}))
        with mock.patch.object(ts, "gpu_setup") as setup, mock.patch("sys.stdout", io.StringIO()):
            self.assertEqual(tp.main(self.args()), 0)
        setup.assert_not_called()

    def test_unknown_seed_is_refused(self):
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", io.StringIO()):
            tp.main(["train", "--arm", "EC", "--seed", "12", "--attempt", "1", "--data", str(self.data), "--out", str(self.out)])

    def test_setup_failure_is_reported(self):
        def failing(allow):
            raise ValueError("D021 stack mismatch: torch expected")

        with mock.patch.object(ts, "gpu_setup", failing), mock.patch("sys.stderr", io.StringIO()):
            self.assertEqual(tp.main(self.args()), 1)
        report = json.loads((self.out / "train_report.json").read_text())
        self.assertEqual(report["status"], "FAILED")
        self.assertIn("stack mismatch", report["error"])
        self.assertEqual(report["recipe_sha256"], ts.digest(tp.RECIPE))

    def test_training_reads_only_its_data_file(self):
        """Up to the tokenizer, the run reads the embedded TRAIN data file and nothing else."""
        opened = []
        original = Path.read_text

        def spy(path, *args, **kwargs):
            opened.append(Path(path).resolve())
            return original(path, *args, **kwargs)

        torch = mock.MagicMock()
        torch.cuda.OutOfMemoryError = MemoryError
        with mock.patch.object(Path, "read_text", spy), \
                mock.patch.object(ts, "gpu_setup", return_value=(torch, [])), \
                mock.patch.object(ts, "environment", return_value={}), \
                mock.patch.object(ts, "MemorySampler") as sampler, \
                mock.patch.object(ts, "load_tokenizer", side_effect=RuntimeError("stop before the model")), \
                mock.patch("sys.stderr", io.StringIO()), mock.patch("sys.stdout", io.StringIO()):
            sampler.return_value.start.return_value.error = None
            sampler.return_value.start.return_value.samples = 0
            self.assertEqual(tp.main(self.args()), 1)
        self.assertEqual(set(opened), {self.data.resolve()})
        report = json.loads((self.out / "train_report.json").read_text())
        self.assertEqual(report["order_sha256"], tp.order_sha256(tp.phase2_dataset(ROOT)["families"], 11))
        self.assertIn("stop before the model", report["error"])


if __name__ == "__main__":
    unittest.main()
