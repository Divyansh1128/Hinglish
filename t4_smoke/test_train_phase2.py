"""Model-free tests of the Phase-2 training module (PREREGISTRATION §3 with Amendment 1 items 9-11)."""
import copy
import hashlib
import io
import json
import math
import tempfile
import types
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
        self.assertEqual(recipe["content_batch_families"], 8)
        self.assertEqual(recipe["grad_scaler"], {"init_scale": 65536.0, "growth_factor": 2.0, "backoff_factor": 0.5,
                                                 "growth_interval": 2000})
        self.assertIn("not dropout", recipe["pairing_scope"])


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
        self.exposure = ROOT / tp.EXPOSURE_ORDER_PATH

    def tearDown(self):
        self.folder.cleanup()

    def args(self, *extra):
        return ["train", "--arm", "EC", "--seed", "11", "--slot", "11", "--attempt", "1", "--data", str(self.data),
                "--exposure-order", str(self.exposure), "--out", str(self.out), *extra]

    def test_started_attempt_is_not_resumed_silently(self):
        self.out.mkdir(parents=True)
        (self.out / "train_report.json").write_text(json.dumps({"status": "FAILED"}))
        with mock.patch("sys.stderr", io.StringIO()) as err, mock.patch.object(ts, "gpu_setup") as setup:
            self.assertEqual(tp.main(self.args()), 2)
        setup.assert_not_called()
        self.assertIn("item 11", err.getvalue())
        self.assertIn("never valid", err.getvalue())

    def test_completed_attempt_is_not_retrained(self):
        self.out.mkdir(parents=True)
        (self.out / "train_report.json").write_text(json.dumps({"status": "COMPLETE"}))
        with mock.patch.object(ts, "gpu_setup") as setup, mock.patch("sys.stdout", io.StringIO()):
            self.assertEqual(tp.main(self.args()), 0)
        setup.assert_not_called()

    def test_unknown_seed_is_refused(self):
        with self.assertRaises(SystemExit), mock.patch("sys.stderr", io.StringIO()):
            tp.main(["train", "--arm", "EC", "--seed", "12", "--slot", "11", "--attempt", "1", "--data", str(self.data),
                     "--exposure-order", str(self.exposure), "--out", str(self.out)])

    def test_setup_failure_is_reported(self):
        def failing(allow):
            raise ValueError("D021 stack mismatch: torch expected")

        with mock.patch.object(ts, "gpu_setup", failing), mock.patch("sys.stderr", io.StringIO()):
            self.assertEqual(tp.main(self.args()), 1)
        report = json.loads((self.out / "train_report.json").read_text())
        self.assertEqual(report["status"], "FAILED")
        self.assertIn("stack mismatch", report["error"])
        self.assertEqual(report["recipe_sha256"], ts.digest(tp.RECIPE))
        self.assertEqual(report["failure_class"], "infrastructure")
        self.assertEqual(tp.attempt_outcome(self.out)[0], "infrastructure")

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
        self.assertEqual(set(opened), {self.data.resolve()})  # the exposure order is read as bytes
        report = json.loads((self.out / "train_report.json").read_text())
        self.assertEqual(report["order_sha256"], tp.order_sha256(tp.phase2_dataset(ROOT)["families"], 11))
        self.assertIn("stop before the model", report["error"])


# ---------------------------------------------------------------- Amendment 1 item 9: exposure order

class ExposureOrderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = tp.phase2_dataset(ROOT)
        cls.families = tp.validate_phase2_data(cls.data)
        cls.document = json.loads((ROOT / tp.EXPOSURE_ORDER_PATH).read_text(encoding="utf-8"))

    def test_hash_input_is_exact_utf8_with_decimal_seed_and_pass(self):
        self.assertEqual(tp.order_input(44, 3, "TR-A-001"), b"phase2-D043:44:3:TR-A-001")
        self.assertEqual(tp.order_key(11, 2, "x"), hashlib.sha256("phase2-D043:11:2:x".encode("utf-8")).hexdigest())
        self.assertEqual(tp.order_input(11, 1, "ü"), "phase2-D043:11:1:ü".encode("utf-8"))
        for bad in ((True, 1), ("11", 1), (11.0, 1), (11, 0), (11, "1"), (-1, 1)):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                tp.order_input(*bad, "F1")

    def test_ties_are_broken_by_family_id(self):
        with mock.patch.object(tp, "order_key", return_value="0" * 64):
            self.assertEqual(tp.pass_order(["F3", "F1", "F2"], 11, 1), ["F1", "F2", "F3"])
        keys = {"A": "b", "B": "a", "C": "a"}
        with mock.patch.object(tp, "order_key", side_effect=lambda s, p, f: keys[f]):
            self.assertEqual(tp.pass_order(["A", "C", "B"], 11, 1), ["B", "C", "A"])

    def test_committed_exposure_order_is_current_and_complete(self):
        text = (ROOT / tp.EXPOSURE_ORDER_PATH).read_text(encoding="utf-8")
        self.assertEqual(text, tp.exposure_text(self.data), "Regenerate: python3 -B t4_smoke/train_phase2.py exposure-order")
        ids = sorted(f["family_id"] for f in self.families)
        self.assertEqual(sorted(self.document["seeds"]), ["11", "22", "33", "44", "55"])
        self.assertEqual(self.document["families_sha256"], self.data["families_sha256"])
        self.assertEqual(self.document["content_batch_families"], 8)
        for seed, entry in self.document["seeds"].items():
            self.assertEqual(entry["role"], "original" if int(seed) in tp.SLOTS else "reserve")
            self.assertEqual(len(entry["passes"]), 3)
            for number, ordered in enumerate(entry["passes"], 1):
                self.assertEqual(sorted(ordered), ids)
                expected = sorted(ids, key=lambda fid: (hashlib.sha256(f"phase2-D043:{seed}:{number}:{fid}".encode()).hexdigest(), fid))
                self.assertEqual(ordered, expected)
            self.assertEqual(entry["order_sha256"], tp.order_sha256(self.families, int(seed)))
            self.assertEqual(entry["order_sha256"], ts.digest(entry["passes"]))
        with mock.patch("sys.stdout", io.StringIO()):
            self.assertEqual(tp.main(["exposure-order", "--root", str(ROOT), "--check"]), 0)

    def test_training_checks_the_frozen_list(self):
        self.assertEqual(tp.check_exposure(self.document, self.data, 33), tp.order_sha256(self.families, 33))
        swapped = copy.deepcopy(self.document)
        first = swapped["seeds"]["22"]["passes"][1]
        first[0], first[1] = first[1], first[0]
        with self.assertRaisesRegex(tp.ProtocolFailure, "seed 22 differs"):
            tp.check_exposure(swapped, self.data, 22)
        missing = copy.deepcopy(self.document)
        del missing["seeds"]["55"]
        with self.assertRaisesRegex(tp.ProtocolFailure, "no list for seed 55"):
            tp.check_exposure(missing, self.data, 55)
        other = copy.deepcopy(self.data)
        other["families_sha256"] = "0" * 64
        with self.assertRaisesRegex(tp.ProtocolFailure, "other TRAIN data"):
            tp.check_exposure(self.document, other, 11)


# ---------------------------------------------------------------- Amendment 1 item 10: numerics (fake torch)

class FakeLoss:
    def __init__(self, value):
        self.value = value

    def detach(self):
        return self

    def __float__(self):
        return self.value

    def __truediv__(self, other):
        return self


class FakeScaler:
    def __init__(self, log, skip_at=None):
        self.log, self.skip_at, self.current, self.updates = log, skip_at, 65536.0, 0

    def get_scale(self):
        return self.current

    def scale(self, loss):
        return types.SimpleNamespace(backward=lambda: self.log.append(("backward", float(loss))))

    def unscale_(self, optimizer):
        self.log.append(("unscale",))

    def step(self, optimizer):
        self.log.append(("step", optimizer.param_groups[0]["lr"]))

    def update(self):
        self.updates += 1
        if self.updates == self.skip_at:
            self.current *= 0.5


def fake_trainer(*, losses=None, grad_norms=None, skip_at=None):
    log = []
    torch = types.SimpleNamespace(
        cuda=types.SimpleNamespace(synchronize=lambda: None, reset_peak_memory_stats=lambda: None, mem_get_info=lambda: (10, 20),
                                   max_memory_allocated=lambda: 1, max_memory_reserved=lambda: 2))
    norms = dict(grad_norms or {})

    def clip(parameters, clip_value):
        log.append(("clip", clip_value))
        return norms.get(len([e for e in log if e[0] == "clip"]), 0.5)

    torch.nn = types.SimpleNamespace(utils=types.SimpleNamespace(clip_grad_norm_=clip))
    trainer = tp.Phase2Trainer.__new__(tp.Phase2Trainer)
    trainer.torch, trainer.parameters, trainer.cursor = torch, [], 0
    trainer.attempted_steps = trainer.successful_steps = 0
    trainer.sequence = [{"family_id": f"F{i // 2:03d}", "form": "EC"[i % 2], "input_ids": [1, 2, 3, 4], "boundary_index": 1}
                        for i in range(960)]
    trainer.sampler = types.SimpleNamespace(take=lambda: None)
    trainer.scaler = FakeScaler(log, skip_at)
    trainer.optimizer = types.SimpleNamespace(param_groups=[{"lr": 0.0}], zero_grad=lambda set_to_none: log.append(("zero",)))
    values = dict(losses or {})
    counter = {"n": 0}

    def loss(example):
        counter["n"] += 1
        return FakeLoss(values.get(counter["n"], 1.0))

    trainer.loss = loss
    return trainer, log


class NumericsTests(unittest.TestCase):
    def test_scaler_is_pinned(self):
        torch = mock.MagicMock()
        tp.make_scaler(torch)
        torch.amp.GradScaler.assert_called_once_with("cuda", init_scale=65536.0, growth_factor=2.0, backoff_factor=0.5,
                                                     growth_interval=2000)
        sequence = [{}] * 960
        trainer = tp.Phase2Trainer(torch, mock.MagicMock(), [], True, sequence, mock.MagicMock())
        self.assertEqual(torch.amp.GradScaler.call_args_list[-1], mock.call("cuda", **tp.SCALER))
        self.assertIs(trainer.scaler, torch.amp.GradScaler.return_value)
        self.assertEqual(trainer.steps(), {"windows": 60, "attempted": 0, "successful": 0, "cursor": 0})
        with self.assertRaises(ValueError):
            tp.Phase2Trainer(torch, mock.MagicMock(), [], True, sequence[:-1], mock.MagicMock())

    def test_sixty_windows_sixty_successful_steps_lr_before_step_unscale_before_clip(self):
        trainer, log = fake_trainer()
        with mock.patch("sys.stdout", io.StringIO()):
            records = [trainer.update(u) for u in range(1, 61)]
        self.assertEqual(trainer.steps(), {"windows": 60, "attempted": 60, "successful": 60, "cursor": 960})
        steps = [entry for entry in log if entry[0] == "step"]
        self.assertEqual(len(steps), 60)
        for u, (_, lr) in enumerate(steps, 1):
            self.assertEqual(lr, tp.lr_at(u))  # lr(u) was set before step u
        kinds = [entry[0] for entry in log]
        for u in range(60):
            window = kinds[u * 20:(u + 1) * 20]  # 16 backward, unscale, clip, step, zero
            self.assertEqual(window, ["backward"] * 16 + ["unscale", "clip", "step", "zero"])
        for u, record in enumerate(records, 1):
            self.assertEqual((record["attempted_step"], record["successful_step"]), (u, u))
            self.assertEqual((record["cursor_before"], record["cursor_after"]), ((u - 1) * 16, u * 16))
            self.assertEqual(record["pass_number"], (u - 1) // 20 + 1)
            self.assertFalse(record["skipped"])
        self.assertEqual(ts.summarize_updates(records, warmup=0, resume_after=0)["scaler_skips"], 0)
        with self.assertRaises(ValueError):  # no 61st window
            trainer.update(61)

    def test_scaler_skip_is_a_numerical_failure_and_nothing_continues(self):
        trainer, log = fake_trainer(skip_at=5)
        with mock.patch("sys.stdout", io.StringIO()):
            for u in range(1, 5):
                trainer.update(u)
            with self.assertRaisesRegex(tp.NumericalFailure, "GradScaler skipped") as caught:
                trainer.update(5)
        self.assertEqual(caught.exception.record["reason"].split(" (")[0], "GradScaler skipped the step")
        self.assertEqual(trainer.steps(), {"windows": 60, "attempted": 5, "successful": 4, "cursor": 80})
        with self.assertRaises(ValueError):  # neither replayed nor skipped: the run cannot continue
            trainer.update(6)
        with self.assertRaises(ValueError):
            trainer.update(5)

    def test_non_finite_loss_stops_before_backward_and_step(self):
        trainer, log = fake_trainer(losses={3: float("nan")})
        with self.assertRaisesRegex(tp.NumericalFailure, "non-finite loss") as caught:
            trainer.update(1)
        self.assertEqual([entry[0] for entry in log], ["backward", "backward"])
        self.assertEqual(caught.exception.record["cursor_at_failure"], 3)
        self.assertEqual(caught.exception.record["microbatch_losses"][-1], "nan")
        self.assertEqual(trainer.steps()["successful"], 0)

    def test_non_finite_gradient_stops_before_the_step(self):
        for value in (float("inf"), float("nan")):
            trainer, log = fake_trainer(grad_norms={1: value})
            with self.subTest(value=value), self.assertRaisesRegex(tp.NumericalFailure, "non-finite gradient"):
                trainer.update(1)
            self.assertNotIn("step", [entry[0] for entry in log])
            self.assertEqual(log[16:18], [("unscale",), ("clip", 1.0)])

    def test_non_finite_saved_parameters_are_detected(self):
        class Flag:
            def __init__(self, ok):
                self.ok = ok

            def all(self):
                return self.ok

        torch = types.SimpleNamespace(isfinite=lambda tensor: Flag(tensor != "bad"))
        self.assertEqual(tp.nonfinite_tensors(torch, [("a", "ok"), ("b", "bad")]), ["b"])
        self.assertEqual(tp.nonfinite_tensors(torch, [("a", "ok")]), [])


# ---------------------------------------------------------------- Amendment 1 item 11: failure classes

def write_attempt(folder, *, status="COMPLETE", failure_class=None, **final_changes):
    folder.mkdir(parents=True, exist_ok=True)
    report = {"status": status, "failure_class": failure_class, "error": "Traceback\nValueError: boom"}
    (folder / "train_report.json").write_text(json.dumps(report))
    if status == "COMPLETE":
        final = {"status": "COMPLETE", "updates": 60, "steps": {"windows": 60, "attempted": 60, "successful": 60, "cursor": 960},
                 "scaler_skips": 0, "saved_parameters_finite": True, "resumed": False, "valid_for_gate": True}
        final.update(final_changes)
        (folder / "final_adapter.json").write_text(json.dumps(final))


class FailureClassTests(unittest.TestCase):
    def test_classification(self):
        cases = [(tp.NumericalFailure("x"), "training", "numerical"), (tp.ProtocolFailure("x"), "final", "protocol"),
                 (ValueError("hash"), "data", "protocol"), (AssertionError("targets"), "labels", "protocol"),
                 (ValueError("cursor"), "training", "protocol"), (ValueError("252 modules"), "model", "protocol"),
                 (RuntimeError("CUDA error"), "training", "infrastructure"), (MemoryError("OOM"), "training", "infrastructure"),
                 (OSError("download"), "model", "infrastructure"), (OSError("x"), "tokenizer", "infrastructure"),
                 (ValueError("stack mismatch"), "setup", "infrastructure"), (ValueError("save differs"), "final", "infrastructure"),
                 (ValueError("reload differs"), "reload", "infrastructure"), (OSError("drive"), "checkpoint", "infrastructure")]
        for error, stage, expected in cases:
            with self.subTest(error=error, stage=stage):
                self.assertEqual(tp.classify_failure(error, stage), expected)

    def test_attempt_outcomes_from_folders(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(tp.attempt_outcome(root / "none")[0], "infrastructure")
            write_attempt(root / "started", status="STARTED")
            self.assertEqual(tp.attempt_outcome(root / "started"), ("infrastructure", "run did not finish (status STARTED): runtime disconnect or crash"))
            for cls in tp.FAILURE_CLASSES:
                write_attempt(root / cls, status="FAILED", failure_class=cls)
                self.assertEqual(tp.attempt_outcome(root / cls), (cls, "ValueError: boom"))
            write_attempt(root / "valid")
            self.assertEqual(tp.attempt_outcome(root / "valid")[0], "valid")
            write_attempt(root / "resumed", resumed=True, valid_for_gate=False)
            self.assertEqual(tp.attempt_outcome(root / "resumed")[0], "resumed_invalid")
            write_attempt(root / "short", steps={"windows": 60, "attempted": 60, "successful": 59, "cursor": 960})
            self.assertEqual(tp.attempt_outcome(root / "short")[0], "protocol")
            write_attempt(root / "nosave")
            (root / "nosave" / "final_adapter.json").unlink()
            self.assertEqual(tp.attempt_outcome(root / "nosave")[0], "infrastructure")


class FakeRunTrainer:
    """Stands in for Phase2Trainer inside run_train; ``fail_at`` raises a NumericalFailure there."""
    fail_at, short = None, False

    def __init__(self, torch, model, trainable, keep, sequence, sampler):
        self.scaler = types.SimpleNamespace(state_dict=lambda: {"scale": 65536.0})
        self.attempted = self.successful = 0

    def steps(self):
        successful = self.successful - (1 if self.short and self.successful == 60 else 0)
        return {"windows": 60, "attempted": self.attempted, "successful": successful, "cursor": self.successful * 16}

    def update(self, number):
        self.attempted += 1
        if number == self.fail_at:
            raise tp.NumericalFailure(f"NUMERICAL FAILURE at update {number}: GradScaler skipped the step",
                                      {"update": number, "reason": "GradScaler skipped the step"})
        self.successful += 1
        return {"update": number, "seconds": 1.0, "microbatch_losses": [1.0], "skipped": False, "grad_norm": 0.5,
                "min_free_bytes": 1, "peak_allocated_bytes": 1, "peak_reserved_bytes": 1, "input_tokens": 1, "supervised_tokens": 1}


class RunClassificationTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.out = self.root / "EC-s11" / "attempt-01"
        self.data = self.root / "phase2_train.json"
        self.data.write_text(json.dumps(tp.phase2_dataset(ROOT)))
        self.exposure = self.root / "EXPOSURE_ORDER.json"
        self.exposure.write_bytes((ROOT / tp.EXPOSURE_ORDER_PATH).read_bytes())

    def tearDown(self):
        self.folder.cleanup()

    def run_with(self, trainer_class):
        torch = mock.MagicMock()
        torch.cuda.OutOfMemoryError = MemoryError
        torch.cuda.mem_get_info.return_value = (1, 2)
        sampler = mock.MagicMock()
        sampler.return_value.start.return_value.error = None
        sampler.return_value.start.return_value.take.return_value = None
        audit = {"passed": True, "arms": {}, "max_input_tokens": 5, "last_target_is_im_end": True}
        err, out = io.StringIO(), io.StringIO()
        with mock.patch.object(ts, "gpu_setup", return_value=(torch, [])), mock.patch.object(ts, "environment", return_value={}), \
                mock.patch.object(ts, "MemorySampler", sampler), mock.patch.object(ts, "load_tokenizer", return_value=mock.MagicMock(chat_template="t")), \
                mock.patch.object(tp, "prepare_examples", return_value=({}, audit)), \
                mock.patch.object(tp, "run_examples", return_value=[{"family_id": "F", "form": "E"}] * 960), \
                mock.patch.object(tp, "load_model", return_value=("model", [], True, {})), \
                mock.patch.object(tp, "weight_shard_hashes", return_value={"model.safetensors": "h"}), \
                mock.patch.object(ts, "tensors_digest", return_value="init"), mock.patch.object(tp, "Phase2Trainer", trainer_class), \
                mock.patch.object(tp, "save_checkpoint"), \
                mock.patch.object(tp, "save_final_adapter", return_value={"adapter_model_sha256": "a" * 64, "adapter_config_sha256": "b" * 64,
                                                                           "saved_parameters_finite": True}), \
                mock.patch("sys.stderr", err), mock.patch("sys.stdout", out):
            code = tp.main(["train", "--arm", "EC", "--seed", "11", "--slot", "11", "--attempt", "1", "--data", str(self.data),
                            "--exposure-order", str(self.exposure), "--out", str(self.out), "--implementation-manifest-sha256", "m" * 64])
        return code, json.loads((self.out / "train_report.json").read_text()), err.getvalue()

    def test_valid_run(self):
        code, report, _ = self.run_with(type("T", (FakeRunTrainer,), {}))
        self.assertEqual((code, report["status"], report["valid_for_gate"]), (0, "COMPLETE", True))
        final = json.loads((self.out / "final_adapter.json").read_text())
        self.assertEqual(final["steps"], {"windows": 60, "attempted": 60, "successful": 60, "cursor": 960})
        self.assertEqual((final["implementation_manifest_sha256"], final["slot"]), ("m" * 64, 11))
        self.assertEqual(final["exposure_order_file_sha256"], hashlib.sha256(self.exposure.read_bytes()).hexdigest())
        self.assertEqual(final["order_sha256"], json.loads(self.exposure.read_text())["seeds"]["11"]["order_sha256"])
        self.assertEqual(tp.valid_run_problems(final), [])
        self.assertEqual(tp.attempt_outcome(self.out)[0], "valid")

    def test_numerical_failure_halts_the_study(self):
        code, report, err = self.run_with(type("T", (FakeRunTrainer,), {"fail_at": 3}))
        self.assertEqual(code, tp.EXIT_CODES["numerical"])
        self.assertEqual((report["status"], report["failure_class"], report["study_halt"], report["valid_for_gate"]),
                         ("FAILED", "numerical", True, False))
        self.assertEqual(report["failed_update"]["update"], 3)
        self.assertEqual(report["steps"], {"windows": 60, "attempted": 3, "successful": 2, "cursor": 32})
        self.assertEqual(len(report["updates"]), 2)
        self.assertIn("THE STUDY HALTS", err)
        self.assertFalse((self.out / "final_adapter.json").exists())
        self.assertEqual(tp.attempt_outcome(self.out)[0], "numerical")

    def test_step_count_mismatch_is_a_protocol_failure(self):
        code, report, err = self.run_with(type("T", (FakeRunTrainer,), {"short": True}))
        self.assertEqual((code, report["failure_class"]), (tp.EXIT_CODES["protocol"], "protocol"))
        self.assertIn("60 successful steps", report["error"])
        self.assertIn("THE STUDY HALTS", err)

    def test_tampered_exposure_order_is_a_protocol_failure(self):
        document = json.loads(self.exposure.read_text())
        passes = document["seeds"]["11"]["passes"][0]
        passes[0], passes[1] = passes[1], passes[0]
        self.exposure.write_text(json.dumps(document))
        code, report, _ = self.run_with(type("T", (FakeRunTrainer,), {}))
        self.assertEqual((code, report["failure_class"], report["failure_stage"]), (tp.EXIT_CODES["protocol"], "protocol", "data"))

    def test_attempt_three_or_wrong_slot_refused(self):
        for extra in (["--attempt", "3"], ["--seed", "22"]):
            argv = ["train", "--arm", "EC", "--seed", "11", "--slot", "11", "--attempt", "1", "--data", str(self.data),
                    "--exposure-order", str(self.exposure), "--out", str(self.root / ("x" + extra[1]))]
            index = argv.index(extra[0])
            argv[index + 1] = extra[1]
            with mock.patch.object(ts, "gpu_setup") as setup, mock.patch("sys.stderr", io.StringIO()):
                self.assertEqual(tp.main(argv), tp.EXIT_CODES["protocol"])
            setup.assert_not_called()


# ---------------------------------------------------------------- Amendment 1 item 11: attempt log and seed plan

class AttemptLogTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.log = self.root / tp.ATTEMPT_LOG

    def tearDown(self):
        self.folder.cleanup()

    def attempt(self, arm, seed, slot, outcome):
        current = tp.plan(tp.read_log(self.log))
        action = tp.next_action(current, arm, slot)
        self.assertEqual((action["kind"], action["seed"]), ("train", seed))
        tp.log_event(self.log, "start", arm=arm, seed=seed, slot=slot, attempt=action["attempt"])
        tp.log_event(self.log, "finish", arm=arm, seed=seed, slot=slot, attempt=action["attempt"], outcome=outcome)
        return action["attempt"]

    def plan(self):
        return tp.plan(tp.read_log(self.log))

    def test_log_is_append_only_and_hash_chained(self):
        tp.log_event(self.log, "start", arm="EE", seed=11, slot=11, attempt=1)
        tp.log_event(self.log, "finish", arm="EE", seed=11, slot=11, attempt=1, outcome="valid")
        first = self.log.read_text().splitlines()
        tp.log_event(self.log, "start", arm="ER", seed=11, slot=11, attempt=1)
        self.assertEqual(self.log.read_text().splitlines()[:2], first)  # earlier lines never rewritten
        self.assertEqual([e["n"] for e in tp.read_log(self.log)], [1, 2, 3])
        lines = self.log.read_text().splitlines()
        edited = json.loads(lines[1])
        edited["outcome"] = "infrastructure"
        self.log.write_text("\n".join([lines[0], json.dumps(edited), lines[2]]) + "\n")
        with self.assertRaisesRegex(tp.ProtocolFailure, "edited"):
            tp.read_log(self.log)
        self.log.write_text("\n".join([lines[0], lines[2]]) + "\n")
        with self.assertRaisesRegex(tp.ProtocolFailure, "broken"):
            tp.read_log(self.log)

    def test_one_from_scratch_retry_then_whole_triplet_goes_to_the_next_reserve(self):
        self.assertEqual(self.attempt("EE", 11, 11, "valid"), 1)
        self.assertEqual(self.attempt("EC", 11, 11, "infrastructure"), 1)
        action = tp.next_action(self.plan(), "EC", 11)
        self.assertEqual((action["seed"], action["attempt"], action["retry"]), (11, 2, True))
        self.attempt("EC", 11, 11, "infrastructure")
        current = self.plan()
        self.assertEqual(current["slots"][11]["chain"], [11, 44])
        for arm in tp.ARMS:  # successful EE of seed 11 is retrained on the reserve too
            action = tp.next_action(current, arm, 11)
            self.assertEqual((action["kind"], action["seed"], action["attempt"], action["reserve"]), ("train", 44, 1, True))
        with self.assertRaisesRegex(tp.ProtocolFailure, "retired"):
            tp.plan(tp.read_log(self.log) + [{"n": 99, "event": "start", "arm": "ER", "seed": 11, "slot": 11, "attempt": 1}])
        # The reserve has the same two-attempt limit; the next reserve then takes over; reserves are never reused.
        self.attempt("ER", 44, 11, "infrastructure")
        self.attempt("ER", 44, 11, "infrastructure")
        self.assertEqual(self.plan()["slots"][11]["chain"], [11, 44, 55])
        self.attempt("EE", 55, 11, "infrastructure")
        self.attempt("EE", 55, 11, "infrastructure")
        current = self.plan()
        self.assertEqual(current["slots"][11]["status"], "exhausted")
        with self.assertRaisesRegex(tp.Refused, "no reserve is left"):
            tp.next_action(current, "EE", 11)
        self.assertEqual(tp.next_action(current, "EE", 22)["seed"], 22)  # other slots unaffected

    def test_reserves_fill_slots_in_order_and_are_never_reused(self):
        for _ in range(2):
            self.attempt("ER", 22, 22, "infrastructure")
        self.assertEqual(self.plan()["slots"][22]["chain"], [22, 44])
        for _ in range(2):
            self.attempt("EE", 11, 11, "infrastructure")
        current = self.plan()  # nothing trained on 44 yet: slot order decides (11 first)
        self.assertEqual((current["slots"][11]["chain"], current["slots"][22]["chain"]), ([11, 44], [22, 55]))
        self.attempt("EE", 44, 11, "valid")
        self.assertEqual(self.plan()["reserves_assigned"], {44: 11, 55: 22})
        with self.assertRaisesRegex(tp.ProtocolFailure, "reused"):
            tp.plan(tp.read_log(self.log) + [{"n": 99, "event": "start", "arm": "ER", "seed": 44, "slot": 22, "attempt": 1}])

    def test_reserve_already_trained_for_a_later_slot_is_kept(self):
        for _ in range(2):
            self.attempt("ER", 22, 22, "infrastructure")
        self.attempt("EE", 44, 22, "valid")
        for _ in range(2):
            self.attempt("EC", 11, 11, "infrastructure")
        current = self.plan()
        self.assertEqual((current["slots"][11]["chain"], current["slots"][22]["chain"]), ([11, 55], [22, 44]))

    def test_numerical_or_protocol_failure_halts_without_reserve(self):
        for outcome in ("numerical", "protocol"):
            with self.subTest(outcome=outcome):
                self.log.unlink(missing_ok=True)
                self.attempt("EC", 11, 11, outcome)
                current = self.plan()
                self.assertTrue(current["halted"])
                self.assertEqual(current["slots"][11]["chain"], [11])
                self.assertEqual(current["reserves_assigned"], {})
                for arm in tp.ARMS:
                    for slot in tp.SLOTS:
                        with self.assertRaisesRegex(tp.StudyHalted, "THE STUDY HALTS"):
                            tp.next_action(current, arm, slot)
                self.assertIn("STUDY HALTED", tp.describe_plan(current))

    def test_resumed_run_is_never_valid(self):
        self.attempt("EC", 11, 11, "infrastructure")
        tp.log_event(self.log, "resume_start", arm="EC", seed=11, slot=11, attempt=1)
        tp.log_event(self.log, "resume_finish", arm="EC", seed=11, slot=11, attempt=1, outcome="valid")
        current = self.plan()
        self.assertEqual(current["slots"][11]["arms"]["EC"]["valid_attempt"], None)
        self.assertEqual(current["attempts"]["EC-s11"][0]["resume_outcome"], "resumed_invalid")
        self.assertEqual(tp.next_action(current, "EC", 11)["attempt"], 2)
        with self.assertRaisesRegex(tp.ProtocolFailure, "bad resume"):  # one resume per attempt
            tp.plan(tp.read_log(self.log) + [{"n": 99, "event": "resume_start", "arm": "EC", "seed": 11, "slot": 11, "attempt": 1}])

    def test_attempt_numbers_cannot_skip_or_exceed_two(self):
        bad = [{"n": 1, "event": "start", "arm": "EE", "seed": 11, "slot": 11, "attempt": 2}]
        with self.assertRaisesRegex(tp.ProtocolFailure, "next allowed"):
            tp.plan(bad)
        self.attempt("EE", 11, 11, "infrastructure")
        self.attempt("EE", 11, 11, "valid")
        with self.assertRaisesRegex(tp.ProtocolFailure, "next allowed|already valid"):
            tp.plan(tp.read_log(self.log) + [{"n": 99, "event": "start", "arm": "EE", "seed": 11, "slot": 11, "attempt": 3}])

    def test_reconcile_closes_attempts_left_open_by_a_disconnect(self):
        tp.log_event(self.log, "start", arm="EE", seed=11, slot=11, attempt=1)
        with self.assertRaisesRegex(tp.Refused, "reconcile"):
            tp.next_action(self.plan(), "EE", 11)
        write_attempt(tp.attempt_dir(self.root, "EE", 11, 1), status="STARTED")
        tp.log_event(self.log, "start", arm="ER", seed=11, slot=11, attempt=1)
        write_attempt(tp.attempt_dir(self.root, "ER", 11, 1))  # finished training, disconnect during DEV sanity
        closed = tp.reconcile(self.root)
        self.assertEqual([(e["arm"], e["outcome"]) for e in closed], [("EE", "infrastructure"), ("ER", "valid")])
        self.assertEqual(tp.reconcile(self.root), [])
        self.assertEqual(tp.next_action(self.plan(), "EE", 11)["attempt"], 2)

    def test_all_slots_complete(self):
        for slot in tp.SLOTS:
            for arm in tp.ARMS:
                self.attempt(arm, slot, slot, "valid")
        current = self.plan()
        self.assertTrue(current["final"])
        self.assertEqual((current["S"], current["retained"]), (3, [(11, 11), (22, 22), (33, 33)]))
        self.assertEqual(tp.next_action(current, "EC", 33), {"kind": "done", "seed": 33, "attempt": 1})
        with mock.patch("sys.stdout", io.StringIO()) as out:
            tp.main(["plan", "--train-root", str(self.root)])
        self.assertIn("S = 3", out.getvalue())


if __name__ == "__main__":
    unittest.main()
